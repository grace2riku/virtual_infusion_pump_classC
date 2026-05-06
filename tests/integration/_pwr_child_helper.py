"""IT-PWR 子プロセスヘルパ(ITPR-VIP-001 §6.9 / Step 19 F6).

`tests/integration/test_power_loss.py` から `subprocess.Popen` で起動され、
`vip_persist.atomic_writer.write` の実行中に **指定したフェーズ** で停止して
親プロセスからの `signal.SIGKILL` を待つ。停止時にシグナルファイル
(`--signal-file`)を作成して親に「kill して安全な瞬間」を通知する。

ファイル名先頭の `_` は **pytest collection 回避** のため(本ファイル自体は
試験ではなく試験対象を駆動する補助スクリプト)。

フェーズ仕様(SDD §4.4.B atomic write 擬似コードに対応):

* `temp_write`         : temp ファイル書込 + fsync 完了直後、1 回目 `os.replace`
                          (target → bak)直前で停止。target は原本 holds。
* `between_replaces`   : 1 回目 `os.replace`(target → bak)完了直後、2 回目
                          `os.replace`(temp → target)直前で停止。target 不在、
                          .bak が原本 holds。
* `before_dir_fsync`   : 2 回目 `os.replace` 完了直後、ディレクトリ fsync 直前で
                          停止。target = 新, .bak = 旧 の両者 holds。

CLI:

    python _pwr_child_helper.py \
        --target /tmp/persist.json \
        --signal-file /tmp/ready.flag \
        --kill-phase {temp_write,between_replaces,before_dir_fsync}

動作シーケンス:

1. 親と合意した「初回(原本)書き込み」を target に対して実施(monkey-patch
   なし、通常の atomic_writer.write)。
2. `os.replace` および `_try_fsync_directory` を monkey-patch して指定フェーズ
   での停止点を埋め込む。
3. 「2 回目の書き込み(新データ)」を atomic_writer.write で実行 — ここで
   monkey-patch がフェーズに到達した瞬間 `--signal-file` を作成して
   `time.sleep(無限大)` し親の `os.kill(SIGKILL)` を待つ。
4. 親が SIGKILL を送ると本プロセスは停止フェーズの直前のファイル状態のまま
   消える。親は target / .bak を観測して SDD §4.4.B 不変条件を検証する。

Linux 限定(`tests/conftest.py` の `linux_only` auto-skip hook により、本
ヘルパは Linux 以外では呼び出されない)。
"""

from __future__ import annotations

import argparse
import sys
import time
from decimal import Decimal
from pathlib import Path
from typing import Any

# `vip_persist` は `pip install -e ".[dev]"` 済を前提(CI / 開発用 venv)
from vip_ctrl.state_machine import State
from vip_persist import atomic_writer
from vip_persist.records import RuntimeState, Settings
from vip_persist.serializer import build_persisted_record, to_json

# 親が SIGKILL を送るまで子が確実に止まる十分長い秒数
_SLEEP_FOREVER_SEC = 60.0

_INITIAL_SAVED_AT = "2026-05-06T00:00:00Z"
_NEW_SAVED_AT = "2026-05-06T00:01:00Z"


def _build_initial_record() -> bytes:
    """原本(整合性検証 Ok を取れる代表値)レコードを JSON bytes で返す."""
    settings = Settings(
        flow_rate=Decimal("60.0"),
        dose_volume=Decimal("60.0"),
        duration_min=60,
    )
    runtime_state = RuntimeState(
        state=State.IDLE,
        current_flow=Decimal("0.0"),
        accumulated_volume=Decimal("0.0"),
    )
    return to_json(build_persisted_record(settings, runtime_state, _INITIAL_SAVED_AT))


def _build_new_record() -> bytes:
    """2 回目書き込み用レコード(原本と区別できる別の整合値)."""
    settings = Settings(
        flow_rate=Decimal("120.0"),
        dose_volume=Decimal("120.0"),
        duration_min=60,
    )
    runtime_state = RuntimeState(
        state=State.IDLE,
        current_flow=Decimal("0.0"),
        accumulated_volume=Decimal("0.0"),
    )
    return to_json(build_persisted_record(settings, runtime_state, _NEW_SAVED_AT))


def _signal_and_wait(signal_file: Path) -> None:
    """シグナルファイルを作成して親の SIGKILL を待つ.

    親は `signal_file.exists()` を polling して検知し即 SIGKILL する想定
    (`time.sleep` の経過秒数は意味を持たない — kill されるまでに上限を
    切るためだけの値)。親は **存在確認のみ** で内容は読まないため、
    `Path.write_bytes` の brief な空ファイル状態は無害。`os.replace` は
    monkey-patch 済の可能性があるため使用しない(self-recursion 回避)。
    """
    signal_file.write_bytes(b"READY")
    time.sleep(_SLEEP_FOREVER_SEC)


def _install_phase_pause(kill_phase: str, signal_file: Path) -> None:
    """指定フェーズ到達時に `signal_file` を作って sleep する monkey-patch を仕掛ける.

    `os.replace` を本物 `os` モジュールごと差し替える(`atomic_writer.write` 内の
    `os.replace(...)` 参照は singleton の `os` モジュールを引くため、ここでの
    差し替えがそのまま反映される)。`_try_fsync_directory` は `atomic_writer`
    モジュール属性として差し替える(`setattr` で mypy attribute 警告を回避)。
    """
    import os as _os  # noqa: PLC0415 — monkey-patch ローカル化のため遅延 import

    original_replace = _os.replace
    original_fsync_directory = atomic_writer._try_fsync_directory  # noqa: SLF001
    counter = {"replace": 0}

    def patched_replace(src: Any, dst: Any) -> None:
        counter["replace"] += 1
        if kill_phase == "temp_write" and counter["replace"] == 1:
            # 1 回目 os.replace は target → bak。これに突入する直前で停止。
            # target はまだ動いていない = 原本 holds。
            _signal_and_wait(signal_file)
        if kill_phase == "between_replaces" and counter["replace"] == 2:
            # 1 回目 os.replace(target → bak)が完了し、2 回目(temp → target)に
            # 突入する直前で停止。target は不在、.bak が原本 holds。
            _signal_and_wait(signal_file)
        original_replace(src, dst)

    def patched_fsync_directory(target: Path) -> None:
        if kill_phase == "before_dir_fsync":
            # 2 回目 os.replace 完了直後、ディレクトリ fsync 直前で停止。
            # target = 新, .bak = 旧 の両者 holds。
            _signal_and_wait(signal_file)
        original_fsync_directory(target)

    setattr(_os, "replace", patched_replace)  # noqa: B010
    setattr(atomic_writer, "_try_fsync_directory", patched_fsync_directory)  # noqa: B010


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="IT-PWR child helper (Step 19 F6)")
    parser.add_argument("--target", required=True, type=Path)
    parser.add_argument("--signal-file", required=True, type=Path)
    parser.add_argument(
        "--kill-phase",
        required=True,
        choices=("temp_write", "between_replaces", "before_dir_fsync"),
    )
    args = parser.parse_args(argv)

    # Step 1: 原本書き込み(monkey-patch なし、通常書き込み)
    initial_data = _build_initial_record()
    initial_result = atomic_writer.write(initial_data, args.target)
    if not isinstance(initial_result, atomic_writer.WriteOk):
        sys.stderr.write(f"initial write failed: {initial_result!r}\n")
        return 2

    # Step 2: monkey-patch を仕掛けて 2 回目書き込みを実行
    _install_phase_pause(args.kill_phase, args.signal_file)
    new_data = _build_new_record()
    atomic_writer.write(new_data, args.target)
    # 通常はここに到達しない(親の SIGKILL でプロセス消滅) — 到達した場合は
    # monkey-patch の停止点が正しく仕掛かっていないことを意味する。
    sys.stderr.write("ERROR: kill phase was not reached\n")
    return 3


if __name__ == "__main__":
    raise SystemExit(main())
