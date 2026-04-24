"""Checksum Verifier (UNIT-003.2) per SDD-VIP-001 v0.2 §4.13.

Two public, stateless, pure functions that guard against tampering and
accidental corruption of persisted payloads (RCM-015 building block):

* `compute(data) -> hex digest` -- SHA-256 hex digest (64 lower-case chars).
* `verify(data, expected) -> bool` -- recompute and compare in constant
  time via `hmac.compare_digest`; malformed `expected` returns `False`
  without raising.

`hmac.compare_digest` is used even though no secret key is involved so
the comparison step stays resistant to timing side-channels if the
persisted checksum is ever exposed to adversarial control (SDD §4.13
design note on future intentional-tampering).

Related SRS: SRS-SEC-001 (tamper detection with SHA-256).
Related RCM: RCM-015 (building block used by UNIT-004.1 Integrity Validator).
Related HZ:  HZ-007 (persisted-data corruption).
"""

from __future__ import annotations

import hashlib
import hmac
from typing import Final

__all__ = [
    "compute",
    "verify",
]


_HEX_DIGEST_LENGTH: Final[int] = 64
_HEX_ALPHABET: Final[frozenset[str]] = frozenset("0123456789abcdef")


def compute(data: bytes) -> str:
    """Return the SHA-256 hex digest of `data` (lower case, 64 chars)."""
    return hashlib.sha256(data).hexdigest()


def verify(data: bytes, expected: str) -> bool:
    """Return True iff SHA-256(data) matches `expected`.

    `expected` is normalised via `.lower()` so upper-case and mixed-case
    hex are accepted. Malformed `expected` (wrong length or non-hex
    characters) yields `False` without raising, per SDD §4.13.E.
    """
    if len(expected) != _HEX_DIGEST_LENGTH:
        return False
    normalised = expected.lower()
    if not all(c in _HEX_ALPHABET for c in normalised):
        return False
    actual = compute(data)
    return hmac.compare_digest(actual, normalised)
