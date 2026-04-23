"""Atomic file writer (UNIT-003.3) per SDD-VIP-001 v0.2 §4.4.

Implements RCM-015 prerequisite: never leave the persisted file in a
half-written state, so the Integrity Validator (UNIT-004.1) at boot can
trust what it reads.

Algorithm (SDD §4.4.B, temp → rename pattern with one-generation backup):

1. Write `data` to a fresh temporary file in the same directory and
   `fsync(fd)` to flush kernel/disk caches.
2. If `target_path` already exists, `os.replace(target, bak)` so the
   previous generation is preserved on `target_path.bak`.
3. `os.replace(temp, target)` — atomic on POSIX and on Windows for
   same-volume renames in Python 3.8+.
4. On POSIX, also `fsync` the parent directory so the rename itself is
   durable.

On any `OSError` the function attempts a best-effort cleanup of the temp
file and returns `WriteErr(error)`. The target is either left at its
previous state (if the failure happened during temp write) or resides at
the `.bak` (if the failure happened between step 2 and step 3) — never
both gone, never half-written, per SDD §4.4.B invariant.

This module is stateless. Concurrent writes against the same
`target_path` are the **caller's** responsibility (SDD §4.4.C); the
writer does not lock. Calls against different `target_path` values are
fully independent.

Related SRS: SRS-DATA-002 (atomic write), SRS-DATA-003 (1-generation backup).
Related RCM: RCM-015 (prerequisite).
Related HZ:  HZ-007 (persisted-data corruption).
"""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from pathlib import Path

__all__ = [
    "NoBackupError",
    "ReadErr",
    "ReadOk",
    "ReadResult",
    "RollbackErr",
    "RollbackOk",
    "RollbackResult",
    "WriteErr",
    "WriteOk",
    "WriteResult",
    "read",
    "rollback",
    "write",
]


_BAK_SUFFIX: Final[str] = ".bak"
_TMP_SUFFIX_PREFIX: Final[str] = ".tmp."

_logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class NoBackupError(Exception):
    """Raised (via `RollbackErr`) when `rollback` finds no `.bak` file."""


# ---------------------------------------------------------------------------
# Result types (Result-style unions, mirrors UNIT-001.1 / UNIT-001.4)
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class WriteOk:
    """Successful write outcome carrying the byte count."""

    bytes_written: int


@dataclass(frozen=True, slots=True)
class WriteErr:
    """Failed write outcome carrying the underlying OSError."""

    error: OSError


WriteResult = WriteOk | WriteErr


@dataclass(frozen=True, slots=True)
class ReadOk:
    """Successful read outcome carrying the file content."""

    data: bytes


@dataclass(frozen=True, slots=True)
class ReadErr:
    """Failed read outcome carrying the underlying OSError."""

    error: OSError


ReadResult = ReadOk | ReadErr


@dataclass(frozen=True, slots=True)
class RollbackOk:
    """Successful rollback outcome (no payload)."""


@dataclass(frozen=True, slots=True)
class RollbackErr:
    """Failed rollback outcome carrying the underlying error."""

    error: OSError | NoBackupError


RollbackResult = RollbackOk | RollbackErr


# ---------------------------------------------------------------------------
# Path helpers
# ---------------------------------------------------------------------------


def _bak_path_for(target: Path) -> Path:
    return target.with_suffix(target.suffix + _BAK_SUFFIX)


def _temp_path_for(target: Path) -> Path:
    suffix = f"{_TMP_SUFFIX_PREFIX}{os.getpid()}.{int(time.time() * 1000)}"
    return target.with_suffix(target.suffix + suffix)


def _best_effort_unlink(path: Path) -> None:
    try:
        path.unlink(missing_ok=True)
    except OSError:
        _logger.exception("best-effort unlink failed for %s", path)


def _try_fsync_directory(target: Path) -> None:
    """Fsync the parent directory on POSIX so the rename is durable."""
    if not hasattr(os, "O_DIRECTORY"):
        return
    dir_fd = os.open(target.parent, os.O_DIRECTORY)
    try:
        os.fsync(dir_fd)
    finally:
        os.close(dir_fd)


# ---------------------------------------------------------------------------
# Public API (SDD §4.4.A)
# ---------------------------------------------------------------------------


def write(data: bytes, target_path: Path) -> WriteResult:
    """Write `data` to `target_path` atomically with a 1-generation backup.

    See module docstring for the algorithm and invariants.
    """
    temp_path = _temp_path_for(target_path)
    bak_path = _bak_path_for(target_path)
    try:
        with temp_path.open("wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())

        # SDD §4.4.B の擬似コードどおり `os.replace` を使用(POSIX/Windows で
        # 単一ボリューム上の atomic rename が保証される)。テスト側からの
        # モンキーパッチ互換性も `os.replace` 参照で確保している。
        if target_path.exists():
            os.replace(target_path, bak_path)  # noqa: PTH105
        os.replace(temp_path, target_path)  # noqa: PTH105

        _try_fsync_directory(target_path)
    except OSError as e:
        _best_effort_unlink(temp_path)
        return WriteErr(e)
    return WriteOk(bytes_written=len(data))


def read(target_path: Path) -> ReadResult:
    """Return the bytes at `target_path`, or `ReadErr` on any OS error."""
    try:
        return ReadOk(data=target_path.read_bytes())
    except OSError as e:
        return ReadErr(e)


def rollback(target_path: Path) -> RollbackResult:
    """Restore `target_path` from its `.bak` companion.

    Returns `RollbackErr(NoBackupError)` if no `.bak` exists, or
    `RollbackErr(OSError)` if the rename itself fails. On success the
    `.bak` file is consumed (it becomes the new target).
    """
    bak_path = _bak_path_for(target_path)
    if not bak_path.exists():
        return RollbackErr(NoBackupError(f"no backup at {bak_path}"))
    try:
        os.replace(bak_path, target_path)  # noqa: PTH105  # SDD §4.4.B 整合
    except OSError as e:
        return RollbackErr(e)
    return RollbackOk()
