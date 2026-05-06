"""Integration test — IT-PWR(SRS-DATA-002 / 003 / SRS-RCM-015 電源断耐性).

ITPR-VIP-001 §6.9 の詳細化(Step 19 F6、IT 6 観点目)。SDD §4.4.E「原理的に
検知不可能 / load 側で担保」の前提で、永続化パイプラインの **真の電源断
シミュレーション**(`subprocess.Popen` で書込中プロセスを生成 →
`os.kill(pid, signal.SIGKILL)`)に対して、SDD §4.4.B 不変条件
**「target か bak のいずれか常在」** が成立し、再起動後の read 経路で
`Integrity Validator`(UNIT-004.1)が破損 / 中間状態を検出して
`FailsafeRecommended` を返すか、または `rollback()` API で原本を復元できる
ことを検証する。

設計判断(Step 19 F6、ITPR §6.9.4 と二重記録):

* **subprocess + SIGKILL の精密同期:** monkey-patch によって `os.replace` /
  `_try_fsync_directory` の **指定フェーズ突入直前** で signal-file を作成 +
  `time.sleep(60)` する子プロセスを介して、親が SIGKILL を送る瞬間の
  ファイル状態を **決定論的** に作る(`tests/integration/_pwr_child_helper.py`、
  underscore 接頭辞で pytest collection を回避)。乱数的に SIGKILL を打つ
  fuzz 方式と異なり、**SDD §4.4.B 不変条件の各フェーズ** を 1:1 で網羅できる
  利点が大きい(SDD 監査トレーサビリティ確保、回帰時の再現性)。
* **Linux 限定 + nightly schedule:** `pytestmark` に `integration + nightly +
  linux_only` を付与。Step 19 F5 で先取り実装した `tests/conftest.py` の
  `linux_only` auto-skip hook により macOS / Windows ではテスト本体が
  collection 直後に skip 化され、`subprocess.Popen` + `os.kill(SIGKILL)` の
  プラットフォーム差異を回避(macOS は SIGKILL 動作差異、Windows は
  POSIX signal 非対応)。**F5 教訓「ITPR §8.1 規定の機械化を先取り実装」の
  最初の再利用事例** — F5 で導入した hook を新規追加なしで再利用できる。
* **本物 SUT 比率最大化:** F5 の延長で本物 atomic_writer + 本物 serializer +
  本物 integrity validator を主体に、Mock は使用しない(子プロセスでの
  monkey-patch は **試験 scaffolding** であって SUT を Mock 化したものでは
  ない)。
* **試験ケース構成(SDD §4.4.B 不変条件の各フェーズを 1 ケース):**
  * IT-PWR.1-01 — phase `temp_write`(after temp fsync, before 1st os.replace)
    で SIGKILL → target=原本 holds(.bak 不在)
  * IT-PWR.1-02 — phase `between_replaces`(after target→bak, before
    temp→target)で SIGKILL → target 不在、.bak=原本 holds(critical race)
  * IT-PWR.1-03 — phase `before_dir_fsync`(after temp→target, before
    fsync directory)で SIGKILL → target=新, .bak=旧 両者 holds
  * IT-PWR.1-04 — IT-PWR.1-02 同条件で SIGKILL 後に `atomic_writer.rollback()`
    を呼出し → target=原本に復元(SRS-DATA-003 1 世代 backup の正式運用)

関連 SRS: SRS-DATA-002(atomic write)、SRS-DATA-003(1 世代 backup)、
SRS-RCM-015(起動時整合性検証)。
関連 IF-U: IF-U-009(永続化 Saver/Loader)、IF-E-001(プロセス境界、subprocess)。
関連 RCM: RCM-015(起動時状態検証 — load 側で破損検知)。
関連 HZ:  HZ-007(persisted-data corruption)。
関連 UT 申し送り: UT-003.3-10(UTPR §7.3.4 v0.5 Step 19 B5 申し送り、
SDD §4.4.E「原理的に検知不可能 / load 側で担保」整合)。
"""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import pytest

from vip_integrity.validator import FailsafeRecommended, Ok, validate
from vip_persist import atomic_writer
from vip_persist.serializer import from_json

# 本ファイル全体に integration + nightly + linux_only マーカー付与
# (§8.1 規定:IT-PERF / IT-PWR / IT-SIDE は Linux runner 限定 + nightly schedule)
# `linux_only` は `tests/conftest.py` の hook で macOS / Windows では auto-skip
# される(Step 19 F5 で先取り実装、本 F6 が最初の再利用事例)。
pytestmark = [
    pytest.mark.integration,
    pytest.mark.nightly,
    pytest.mark.linux_only,
]

# 子プロセスヘルパへの絶対パス(`tests/integration/_pwr_child_helper.py`)
_HELPER_PATH = Path(__file__).parent / "_pwr_child_helper.py"

# 親が子のシグナルファイル出現を待つ最大時間(子の起動 + 1 回目書込 +
# monkey-patch 仕込み + 2 回目書込開始まで通常 1 秒以内、余裕を見て 10 秒)
_SIGNAL_WAIT_TIMEOUT_SEC = 10.0
# 親が SIGKILL 送信後に子の終了を待つ最大時間(SIGKILL は即時、念のため 5 秒)
_SIGKILL_WAIT_TIMEOUT_SEC = 5.0
# 子のシグナルファイル出現を polling する間隔
_POLL_INTERVAL_SEC = 0.02


def _spawn_child_and_kill_at_phase(
    target: Path,
    signal_file: Path,
    kill_phase: str,
) -> None:
    """子ヘルパを起動し、`signal_file` 出現を検知したら SIGKILL を送る.

    子プロセスは `kill_phase` で指定したフェーズで `time.sleep(60)` 中に親の
    SIGKILL で消滅する。本関数は子の終了 (negative returncode = signal kill)
    を確認するまでブロックする。

    Args:
        target:       永続レコードの書き込み先(temporary file path)
        signal_file:  子が「kill して安全な瞬間」を通知するためのファイル
        kill_phase:   `_pwr_child_helper.py` の `--kill-phase` 引数値

    Raises:
        AssertionError: signal_file 出現がタイムアウト、または子が SIGKILL
                       以外の理由で終了した場合(monkey-patch が機能していない、
                       環境異常など)。

    """
    proc = subprocess.Popen(  # noqa: S603 — Linux 限定 + 引数固定 + helper 信頼
        [
            sys.executable,
            str(_HELPER_PATH),
            "--target",
            str(target),
            "--signal-file",
            str(signal_file),
            "--kill-phase",
            kill_phase,
        ],
    )
    try:
        # 子が指定フェーズに到達して signal_file を作成するまで poll
        deadline = time.monotonic() + _SIGNAL_WAIT_TIMEOUT_SEC
        while time.monotonic() < deadline:
            if signal_file.exists():
                break
            # 子が早期終了していないか確認(monkey-patch エラー等)
            ret = proc.poll()
            if ret is not None:
                pytest.fail(
                    f"child exited prematurely (returncode={ret}) before reaching phase "
                    f"{kill_phase!r}"
                )
            time.sleep(_POLL_INTERVAL_SEC)
        else:
            # ループが break せず deadline 到達 = signal_file 不出現
            proc.kill()
            proc.wait(timeout=_SIGKILL_WAIT_TIMEOUT_SEC)
            pytest.fail(
                f"child did not reach phase {kill_phase!r} within "
                f"{_SIGNAL_WAIT_TIMEOUT_SEC} sec (signal_file={signal_file})"
            )

        # SIGKILL を送信 — 子は monkey-patch 仕込み点の sleep 中
        os.kill(proc.pid, signal.SIGKILL)
        try:
            ret = proc.wait(timeout=_SIGKILL_WAIT_TIMEOUT_SEC)
        except subprocess.TimeoutExpired:
            pytest.fail(f"child did not exit within {_SIGKILL_WAIT_TIMEOUT_SEC} sec after SIGKILL")
        # POSIX で SIGKILL を受けたプロセスの returncode は -SIGKILL (= -9)
        assert ret == -signal.SIGKILL, (
            f"unexpected child returncode {ret} (expected -SIGKILL = {-signal.SIGKILL})"
        )
    finally:
        if proc.poll() is None:
            # 念のため親 cleanup(到達しないはずだが、test failure path で確実に解放)
            proc.kill()
            proc.wait(timeout=_SIGKILL_WAIT_TIMEOUT_SEC)


def _validate_record_at(path: Path) -> Ok | FailsafeRecommended:
    """与えた path のバイト列を deserialize + 整合性検証して結果を返す.

    本関数は IT-PWR の事後観測で「target / .bak から原本が復元可能」を判定する
    ための薄いラッパ(本物 `atomic_writer.read` + 本物 `from_json` + 本物
    `validate` を組み合わせた load 側経路を再現)。
    """
    read_result = atomic_writer.read(path)
    assert isinstance(read_result, atomic_writer.ReadOk), f"read failed at {path}: {read_result!r}"
    raw = from_json(read_result.data)
    return validate(raw)


def _bak_path_for(target: Path) -> Path:
    """`atomic_writer` の `.bak` 命名規則と同じ(suffix への文字列追加)."""
    return target.with_suffix(target.suffix + ".bak")


# ---------------------------------------------------------------------------
# IT-PWR.1-01 — phase `temp_write` で SIGKILL(target=原本 holds)
# ---------------------------------------------------------------------------
def test_it_pwr_1_01_kill_during_temp_write(tmp_path: Path) -> None:
    """SDD §4.4.B 不変条件: temp 書込中に SIGKILL されても target は原本を保持.

    シーケンス:
    1. 子プロセスが原本を target に書き込む(monkey-patch 前、通常書込)
    2. monkey-patch 仕込み:1 回目 `os.replace`(target → bak)突入直前で停止
    3. 子が新データで 2 回目の `atomic_writer.write` を開始 → temp 書込 +
       fsync 完了直後、1 回目 `os.replace` 直前で signal-file を作成 + sleep
    4. 親が signal-file を検知して SIGKILL → 子消滅
    5. 期待:target は原本のまま、.bak は不在、temp はオーファン残り得るが
       検証対象外(SDD §4.4.A best-effort cleanup の意図に反しないが必須でない)
    """
    target = tmp_path / "persist.json"
    signal_file = tmp_path / "ready.flag"

    _spawn_child_and_kill_at_phase(target, signal_file, kill_phase="temp_write")

    # target は原本のまま(SDD §4.4.B 不変条件: target が previous-gen を保持)
    assert target.exists(), "target file unexpectedly absent after temp_write SIGKILL"
    result = _validate_record_at(target)
    assert isinstance(result, Ok), f"target should be valid (original), got {result!r}"
    # 原本書込時点では .bak は生成されない(target が事前不存在 → bak 移動なし)
    assert not _bak_path_for(target).exists(), ".bak should not exist after first-write SIGKILL"


# ---------------------------------------------------------------------------
# IT-PWR.1-02 — phase `between_replaces` で SIGKILL(target 不在、.bak=原本 holds)
# ---------------------------------------------------------------------------
def test_it_pwr_1_02_kill_between_target_bak_and_temp_target(tmp_path: Path) -> None:
    """SDD §4.4.B 不変条件: 2 段 rename の中間で SIGKILL されても .bak が原本を保持.

    シーケンス:
    1. 子プロセスが原本を target に書き込む(target = 原本)
    2. monkey-patch 仕込み:2 回目 `os.replace`(temp → target)突入直前で停止
    3. 子が新データで 2 回目の `atomic_writer.write` を開始 →
       1 回目 `os.replace`(target → bak)完了 → 2 回目突入直前で停止 + sleep
    4. 親が signal-file を検知して SIGKILL → 子消滅
    5. 期待:target は不在、.bak が原本を保持(critical race window)
       — SRS-DATA-003 1 世代 backup により load 側で復元可能
    """
    target = tmp_path / "persist.json"
    signal_file = tmp_path / "ready.flag"

    _spawn_child_and_kill_at_phase(target, signal_file, kill_phase="between_replaces")

    # target は不在(2 回目 rename 直前で kill されたため)
    assert not target.exists(), "target should be absent in between_replaces window"
    # .bak が原本を保持(SDD §4.4.B 不変条件)
    bak = _bak_path_for(target)
    assert bak.exists(), ".bak should hold the original record"
    result = _validate_record_at(bak)
    assert isinstance(result, Ok), f".bak should be valid (original), got {result!r}"


# ---------------------------------------------------------------------------
# IT-PWR.1-03 — phase `before_dir_fsync` で SIGKILL(target=新, .bak=旧 両者 holds)
# ---------------------------------------------------------------------------
def test_it_pwr_1_03_kill_before_directory_fsync(tmp_path: Path) -> None:
    """SDD §4.4.B 不変条件: rename 完了後 dir fsync 前の SIGKILL でも両世代が残る.

    シーケンス:
    1. 子プロセスが原本を target に書き込む(target = 原本)
    2. monkey-patch 仕込み:`_try_fsync_directory` 突入直前で停止
    3. 子が新データで 2 回目の `atomic_writer.write` を開始 →
       1 回目 `os.replace`(target → bak)+ 2 回目 `os.replace`(temp → target)
       完了 → dir fsync 直前で停止 + sleep
    4. 親が signal-file を検知して SIGKILL → 子消滅
    5. 期待:target = 新(整合)、.bak = 旧(整合)— SRS-DATA-003 の 1 世代
       保持原則どおり

    注: ディレクトリ fsync が実施されない場合、ext4 / xfs では rename が OS
    クラッシュ時に巻き戻る理論的可能性があるが、ファイルシステム自身の整合性
    は本テストの範囲外(SDD §4.4.E「原理的に検知不可能」整合) — 本テストは
    プロセス kill 後の **ユーザー空間から見える** 整合性のみを検証する。
    """
    target = tmp_path / "persist.json"
    signal_file = tmp_path / "ready.flag"

    _spawn_child_and_kill_at_phase(target, signal_file, kill_phase="before_dir_fsync")

    # target = 新データ(整合性 Ok)、.bak = 旧データ(整合性 Ok)
    assert target.exists(), "target should hold the new record after rename"
    target_result = _validate_record_at(target)
    assert isinstance(target_result, Ok), (
        f"target should be valid (new record), got {target_result!r}"
    )
    bak = _bak_path_for(target)
    assert bak.exists(), ".bak should hold the previous-generation record"
    bak_result = _validate_record_at(bak)
    assert isinstance(bak_result, Ok), f".bak should be valid (original), got {bak_result!r}"
    # 念のため target と .bak が異なる内容(=新と旧)であることを確認
    assert target.read_bytes() != bak.read_bytes(), (
        "target and .bak should hold different generations"
    )


# ---------------------------------------------------------------------------
# IT-PWR.1-04 — IT-PWR.1-02 と同条件で SIGKILL 後に `rollback()` で復旧
# ---------------------------------------------------------------------------
def test_it_pwr_1_04_rollback_recovers_from_bak(tmp_path: Path) -> None:
    """SRS-DATA-003: target 不在 + .bak 残存状態から rollback() が原本を復元する.

    シーケンス:
    1〜4. IT-PWR.1-02 と同一(phase=between_replaces で SIGKILL → target 不在、
       .bak = 原本 holds)
    5. 親プロセスで `atomic_writer.rollback(target)` を呼び出す
    6. 期待:target = 原本(復元成功)、.bak = 不在(消費)
       — SRS-DATA-003 の 1 世代 backup が想定どおり再起動後の load 経路で
       使われたことを実証
    """
    target = tmp_path / "persist.json"
    signal_file = tmp_path / "ready.flag"

    _spawn_child_and_kill_at_phase(target, signal_file, kill_phase="between_replaces")

    # 前提確認(IT-PWR.1-02 と同条件)
    assert not target.exists()
    assert _bak_path_for(target).exists()

    # 親プロセスで rollback API を呼出
    rollback_result = atomic_writer.rollback(target)
    assert isinstance(rollback_result, atomic_writer.RollbackOk), (
        f"rollback failed: {rollback_result!r}"
    )

    # rollback 後:target = 原本(復元成功)、.bak = 消費されて不在
    assert target.exists(), "target should be restored from .bak"
    assert not _bak_path_for(target).exists(), ".bak should be consumed by rollback"
    result = _validate_record_at(target)
    assert isinstance(result, Ok), f"restored target should be valid (original), got {result!r}"
