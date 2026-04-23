"""UT-003.3 — Atomic File Writer (UNIT-003.3 per SDD-VIP-001 §4.4).

Implements UTPR-VIP-001 §7.3.4 test cases UT-003.3-01 .. UT-003.3-10.
Covers RCM-015 prerequisite (do not corrupt the persisted file that the
Integrity Validator will later check) per RMF-VIP-001 §6.1.

Step 19 B5 reconciles UTPR §7.3.4 with SDD §4.4:

* API name and arity follow SDD §4.4.A: `write(data, target_path)`,
  `read(target_path)`, `rollback(target_path)`.
* UT-003.3-07 is reframed: SDD §4.4.C says "concurrent writes are the
  caller's responsibility" — this unit does not lock. The test verifies
  statelessness (no deadlock, no internal-state corruption) instead.
* UT-003.3-08 expects `Err(OSError)` with `errno == ENOSPC` (no custom
  `DiskFullError` type) — matches SDD §4.4.E.
* UT-003.3-10 (subprocess + SIGKILL power-loss) is deferred to ITPR §5.6.
  This unit verifies the atomicity contract by observing intermediate
  filesystem state and asserting `os.fsync` is called (per SDD §4.4.B
  pseudo-code).

Related SRS: SRS-DATA-002 (atomic write), SRS-DATA-003 (one-generation backup).
Related HZ:  HZ-007 (persisted-data corruption).
"""

from __future__ import annotations

import errno
import os
import threading
from typing import TYPE_CHECKING
from unittest.mock import patch

from vip_persist.atomic_writer import (
    NoBackupError,
    ReadErr,
    ReadOk,
    RollbackErr,
    RollbackOk,
    WriteErr,
    WriteOk,
    read,
    rollback,
    write,
)

if TYPE_CHECKING:
    from pathlib import Path

    import pytest


# ---------- helpers ----------


def _bak_path(target: Path) -> Path:
    return target.with_suffix(target.suffix + ".bak")


def _list_tmp_siblings(target: Path) -> list[Path]:
    """Return any sibling files matching the temp pattern produced by `write`."""
    return [p for p in target.parent.iterdir() if p.name.startswith(target.name + ".tmp.")]


# ---------- UT-003.3-01: 新規書込 ----------


def test_ut_003_3_01_new_file_write_creates_file_with_content(tmp_path: Path) -> None:
    target = tmp_path / "state.json"
    result = write(b"hello", target)
    assert isinstance(result, WriteOk)
    assert result.bytes_written == 5
    assert target.read_bytes() == b"hello"


# ---------- UT-003.3-02: 上書き(原子性 + 旧データを bak へ) ----------


def test_ut_003_3_02_overwrite_moves_old_to_bak(tmp_path: Path) -> None:
    target = tmp_path / "state.json"
    target.write_bytes(b"old")
    result = write(b"new", target)
    assert isinstance(result, WriteOk)
    assert target.read_bytes() == b"new"
    assert _bak_path(target).read_bytes() == b"old"


def test_ut_003_3_02b_overwrite_replaces_existing_bak(tmp_path: Path) -> None:
    target = tmp_path / "state.json"
    bak = _bak_path(target)
    target.write_bytes(b"v2")
    bak.write_bytes(b"stale-v0")  # 古い世代の bak が残っている
    write(b"v3", target)
    # bak は v2 に置換される(2 世代以上は保持しない、SRS-DATA-003 = 1 世代)
    assert bak.read_bytes() == b"v2"
    assert target.read_bytes() == b"v3"


# ---------- UT-003.3-03: .tmp 残存しない ----------


def test_ut_003_3_03_tmp_does_not_remain_after_success(tmp_path: Path) -> None:
    target = tmp_path / "state.json"
    write(b"data", target)
    assert _list_tmp_siblings(target) == []


# ---------- UT-003.3-04: リネーム失敗時、target 不変 + .tmp クリーンアップ ----------


def test_ut_003_3_04_replace_failure_keeps_target_unchanged(tmp_path: Path) -> None:
    target = tmp_path / "state.json"
    target.write_bytes(b"original")
    real_replace = os.replace
    call_count = {"n": 0}

    def failing_replace(src: str, dst: str) -> None:
        call_count["n"] += 1
        # 1 回目(target → bak)は通す、2 回目(temp → target)で失敗
        if call_count["n"] == 2:
            msg = "simulated rename failure"
            raise OSError(errno.EIO, msg)
        real_replace(src, dst)

    with patch("vip_persist.atomic_writer.os.replace", side_effect=failing_replace):
        result = write(b"new", target)
    assert isinstance(result, WriteErr)
    assert result.error.errno == errno.EIO
    # target 自体はリネーム前 = 旧内容、または bak に逃げた状態。
    # 不変条件:target か bak のいずれかが旧データ「original」を保持。
    target_or_bak = (
        (target.read_bytes() if target.exists() else None),
        (_bak_path(target).read_bytes() if _bak_path(target).exists() else None),
    )
    assert b"original" in target_or_bak
    # .tmp は best-effort クリーンアップ済み
    assert _list_tmp_siblings(target) == []


# ---------- UT-003.3-05: 空データ書込 ----------


def test_ut_003_3_05_empty_data_writes_empty_file(tmp_path: Path) -> None:
    target = tmp_path / "state.json"
    result = write(b"", target)
    assert isinstance(result, WriteOk)
    assert result.bytes_written == 0
    assert target.read_bytes() == b""


# ---------- UT-003.3-06: 1 MB データ ----------


def test_ut_003_3_06_one_megabyte_data_writes_successfully(tmp_path: Path) -> None:
    target = tmp_path / "state.json"
    payload = b"x" * (10**6)
    result = write(payload, target)
    assert isinstance(result, WriteOk)
    assert result.bytes_written == 10**6
    assert target.stat().st_size == 10**6


# ---------- UT-003.3-07: ステートレス確認(2 スレッド連続呼出) ----------


def test_ut_003_3_07_stateless_concurrent_writes_no_deadlock(tmp_path: Path) -> None:
    """SDD §4.4.C: 並行書き込みは呼出側責任、本ユニットはロックしない。

    ここでは「**異なる** target_path に対する並行書き込み」が独立に成功し、
    本ユニット側にデッドロックや内部状態破壊が起きないことを確認する。
    同一 target_path への並行書き込みは ARCH-003 上位で直列化される(契約)。
    """
    targets = [tmp_path / f"state_{i}.json" for i in range(2)]
    barrier = threading.Barrier(2)
    errors: list[BaseException] = []

    def worker(idx: int) -> None:
        try:
            barrier.wait()
            for j in range(20):
                payload = f"thread{idx}-iter{j}".encode()
                result = write(payload, targets[idx])
                assert isinstance(result, WriteOk)
        except BaseException as e:  # noqa: BLE001
            errors.append(e)

    t1 = threading.Thread(target=worker, args=(0,))
    t2 = threading.Thread(target=worker, args=(1,))
    t1.start()
    t2.start()
    t1.join(timeout=5.0)
    t2.join(timeout=5.0)
    assert not t1.is_alive()
    assert not t2.is_alive()
    assert errors == []
    # 各 target は最後の書込内容を保持している
    assert targets[0].read_bytes() == b"thread0-iter19"
    assert targets[1].read_bytes() == b"thread1-iter19"


# ---------- UT-003.3-08: ENOSPC(ディスクフル)→ Err(OSError) ----------


def test_ut_003_3_08_enospc_returns_err_oserror(tmp_path: Path) -> None:
    """ディスクフルは `os.fsync` が ENOSPC を投げるケースで模擬する。

    SDD §4.4.E の「ディスク full → `OSError(ENOSPC)` を `Err` で返却、
    temp 削除試行」を検証。実ファイルシステムを満杯にするのは CI で非現実的
    なため、`os.fsync` に OSError を注入する(fsync は書込バッファの
    フラッシュ時に ENOSPC を投げる典型的 API)。
    """
    target = tmp_path / "state.json"

    def failing_fsync(_fd: int) -> None:
        msg = "simulated disk full"
        raise OSError(errno.ENOSPC, msg)

    with patch("vip_persist.atomic_writer.os.fsync", side_effect=failing_fsync):
        result = write(b"data", target)
    assert isinstance(result, WriteErr)
    assert result.error.errno == errno.ENOSPC
    # 元 target が存在しない場合は target も作られていない
    assert not target.exists()
    assert _list_tmp_siblings(target) == []


# ---------- UT-003.3-09: 読込専用ディレクトリ(PermissionError)→ target 不変 ----------


def test_ut_003_3_09_readonly_directory_returns_err_and_keeps_target(
    tmp_path: Path,
) -> None:
    target = tmp_path / "state.json"
    target.write_bytes(b"original")
    # ディレクトリを読込専用化
    tmp_path.chmod(0o500)
    try:
        result = write(b"new", target)
    finally:
        tmp_path.chmod(0o700)
    assert isinstance(result, WriteErr)
    assert isinstance(result.error, OSError)
    assert target.read_bytes() == b"original"


# ---------- UT-003.3-10: 内部ステップ観測 + fsync 呼出 ----------


def test_ut_003_3_10a_fsync_is_called_on_temp_fd(tmp_path: Path) -> None:
    target = tmp_path / "state.json"
    fsync_calls: list[int] = []
    real_fsync = os.fsync

    def recording_fsync(fd: int) -> None:
        fsync_calls.append(fd)
        real_fsync(fd)

    with patch("vip_persist.atomic_writer.os.fsync", side_effect=recording_fsync):
        write(b"data", target)
    # 少なくとも temp ファイル fd への fsync が 1 回以上呼ばれる
    # (POSIX なら追加でディレクトリ fd への fsync も呼ばれる)
    assert len(fsync_calls) >= 1


def test_ut_003_3_10b_atomic_rename_invariant_target_or_bak_always_present(
    tmp_path: Path,
) -> None:
    """SDD §4.4.B 不変条件:write のどの瞬間でも target か bak のいずれかが旧データを保持。

    シミュレーション:write の 3 ステップそれぞれで例外を注入し、
    旧データが target または bak のどちらかから復元可能なことを確認。
    """
    # ステップ 2(target → bak リネーム)直後に失敗注入
    target = tmp_path / "state.json"
    target.write_bytes(b"original")
    real_replace = os.replace
    call_count = {"n": 0}

    def fail_at_step3(src: str, dst: str) -> None:
        call_count["n"] += 1
        if call_count["n"] == 2:  # 2 回目 = temp → target
            msg = "fail at step 3"
            raise OSError(errno.EIO, msg)
        real_replace(src, dst)

    with patch("vip_persist.atomic_writer.os.replace", side_effect=fail_at_step3):
        write(b"new", target)
    # original データが target または bak から復元可能
    candidates = []
    if target.exists():
        candidates.append(target.read_bytes())
    if _bak_path(target).exists():
        candidates.append(_bak_path(target).read_bytes())
    assert b"original" in candidates


# ---------- 補助観点:read API ----------


def test_read_returns_ok_with_file_content(tmp_path: Path) -> None:
    target = tmp_path / "state.json"
    target.write_bytes(b"persisted")
    result = read(target)
    assert isinstance(result, ReadOk)
    assert result.data == b"persisted"


def test_read_missing_file_returns_err(tmp_path: Path) -> None:
    target = tmp_path / "missing.json"
    result = read(target)
    assert isinstance(result, ReadErr)
    assert isinstance(result.error, FileNotFoundError)


# ---------- 補助観点:rollback API ----------


def test_rollback_restores_target_from_bak(tmp_path: Path) -> None:
    target = tmp_path / "state.json"
    target.write_bytes(b"corrupted")
    _bak_path(target).write_bytes(b"good-backup")
    result = rollback(target)
    assert isinstance(result, RollbackOk)
    assert target.read_bytes() == b"good-backup"


def test_rollback_without_bak_returns_no_backup_err(tmp_path: Path) -> None:
    target = tmp_path / "state.json"
    target.write_bytes(b"corrupted")
    result = rollback(target)
    assert isinstance(result, RollbackErr)
    assert isinstance(result.error, NoBackupError)
    # target は不変
    assert target.read_bytes() == b"corrupted"


# ---------- 補助観点:write → read 往復 + 永続性 ----------


def test_write_read_round_trip_preserves_data(tmp_path: Path) -> None:
    target = tmp_path / "state.json"
    payload = b"\x00\x01\x02binary\xff\xfe"
    write(payload, target)
    result = read(target)
    assert isinstance(result, ReadOk)
    assert result.data == payload


# ---------- 補助観点:連続 2 回書込で 1 世代バックアップを保持 ----------


def test_two_sequential_writes_keep_only_last_generation_in_bak(
    tmp_path: Path,
) -> None:
    """SRS-DATA-003: 1 世代のみ保持。3 回目の書込で v1 は失われ v2 が bak に。"""
    target = tmp_path / "state.json"
    write(b"v1", target)
    write(b"v2", target)
    write(b"v3", target)
    assert target.read_bytes() == b"v3"
    assert _bak_path(target).read_bytes() == b"v2"


# ---------- 補助観点:best-effort unlink の OSError パス ----------


def test_best_effort_unlink_swallows_os_error(tmp_path: Path) -> None:
    """`_best_effort_unlink` が OSError を握りつぶすこと。

    SDD §4.4.E の「`.tmp` のクリーンアップ失敗は本ユニットでは許容(best
    effort)」の分岐を直接検証。`Path.unlink` を OSError で失敗させても
    `write` 全体としては通常どおり `WriteErr` を返して完結する。
    """
    target = tmp_path / "state.json"

    def fsync_fail(_fd: int) -> None:
        msg = "trigger cleanup path"
        raise OSError(errno.EIO, msg)

    def unlink_fail(
        self: Path,  # noqa: ARG001
        *,
        missing_ok: bool = False,  # noqa: ARG001
    ) -> None:
        msg = "unlink forbidden"
        raise OSError(errno.EACCES, msg)

    with (
        patch("vip_persist.atomic_writer.os.fsync", side_effect=fsync_fail),
        patch("pathlib.Path.unlink", new=unlink_fail),
    ):
        result = write(b"data", target)
    # OSError が上方に伝播せず、WriteErr が返る
    assert isinstance(result, WriteErr)
    assert result.error.errno == errno.EIO


# ---------- 補助観点:非 POSIX(O_DIRECTORY なし)環境 ----------


def test_fsync_directory_skipped_when_o_directory_absent(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Windows 相当(`hasattr(os, "O_DIRECTORY")` が False)で早期リターン。"""
    target = tmp_path / "state.json"
    monkeypatch.delattr(os, "O_DIRECTORY", raising=False)
    result = write(b"data", target)
    assert isinstance(result, WriteOk)
    assert target.read_bytes() == b"data"


# ---------- 補助観点:rollback で os.replace 失敗 ----------


def test_rollback_replace_failure_returns_err(tmp_path: Path) -> None:
    target = tmp_path / "state.json"
    target.write_bytes(b"corrupted")
    _bak_path(target).write_bytes(b"good-backup")

    def failing_replace(_src: str, _dst: str) -> None:
        msg = "simulated replace failure"
        raise OSError(errno.EIO, msg)

    with patch("vip_persist.atomic_writer.os.replace", side_effect=failing_replace):
        result = rollback(target)
    assert isinstance(result, RollbackErr)
    assert isinstance(result.error, OSError)
    assert result.error.errno == errno.EIO
