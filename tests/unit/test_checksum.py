"""Unit tests for UNIT-003.2 Checksum Verifier (SDD §4.13).

Cross-reviewed against SDD §4.13 / SRS-SEC-001 / UTPR §7.3.7 (skeleton)
before Red. The review resolved 1 operational discussion point
(existing duplicate `compute_sha256` in vip_integrity.validator stays
unchanged; future refactor handled separately) plus four specialist
points accepted as recommended:

1. `compute` / `verify` per SDD §4.13.C, using `hmac.compare_digest`
   for constant-time comparison (timing-attack resistant).
2. Upper-case hex `expected` is normalised via `.lower()`.
3. Malformed `expected` (wrong length, non-hex) returns `False` with
   no exception.
4. MC/DC target raised from 95 % (UTPR v0.7 skeleton) to 100 %
   (B5/B6/B7 precedent for RCM-015-related units).

The §4.13.F "timing試験(参考)" is deferred to ITPR §5.6 per the
B4/B5 precedent (non-deterministic tests belong in IT, not UT).
"""

from __future__ import annotations

from typing import Final

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from vip_persist.checksum import compute, verify

# ---------------------------------------------------------------------------
# NIST known-answer vectors for SHA-256
# ---------------------------------------------------------------------------

_SHA256_EMPTY: Final[str] = (
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
)
_SHA256_ABC: Final[str] = (
    "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
)


# ---------------------------------------------------------------------------
# UT-003.2-01 / 02: Known-answer vectors
# ---------------------------------------------------------------------------


def test_ut_003_2_01_sha256_of_empty_bytes() -> None:
    """compute(b'') equals the NIST known answer for SHA-256 of empty input."""
    assert compute(b"") == _SHA256_EMPTY


def test_ut_003_2_02_sha256_of_abc() -> None:
    """compute(b'abc') equals the NIST known answer for SHA-256('abc')."""
    assert compute(b"abc") == _SHA256_ABC


# ---------------------------------------------------------------------------
# UT-003.2-03: Verify success — compute then verify returns True
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "payload",
    [
        b"",
        b"abc",
        b"The quick brown fox jumps over the lazy dog",
        b"\x00\x01\x02\xff\xfe\xfd",
        b"\x00" * 1000,
    ],
)
def test_ut_003_2_03_verify_success(payload: bytes) -> None:
    """verify(data, compute(data)) is True for arbitrary bytes."""
    assert verify(payload, compute(payload)) is True


# ---------------------------------------------------------------------------
# UT-003.2-04: Verify failure on any single-bit change
# ---------------------------------------------------------------------------


def test_ut_003_2_04_verify_fails_on_one_bit_change() -> None:
    """Flipping a single bit in `data` makes verify return False."""
    original = b"medical device payload"
    checksum = compute(original)
    tampered = bytearray(original)
    tampered[0] ^= 0x01
    assert verify(bytes(tampered), checksum) is False


# ---------------------------------------------------------------------------
# UT-003.2-05: Malformed expected length — returns False without raising
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "bad_expected",
    [
        "",  # empty
        "a" * 63,  # one short
        "a" * 65,  # one long
        "a" * 128,  # double length
    ],
)
def test_ut_003_2_05_verify_false_on_wrong_length(bad_expected: str) -> None:
    """verify returns False (no exception) when expected has wrong length."""
    assert verify(b"anything", bad_expected) is False


# ---------------------------------------------------------------------------
# UT-003.2-06: Non-hex characters in expected — returns False
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "bad_expected",
    [
        "g" + "0" * 63,  # leading 'g' is not hex
        "z" * 64,  # all non-hex
        "-" * 64,  # punctuation
        "0123456789abcdef" * 3 + "0123456789abcdeZ",  # last char non-hex
    ],
)
def test_ut_003_2_06_verify_false_on_non_hex(bad_expected: str) -> None:
    """verify returns False (no exception) when expected contains non-hex chars."""
    assert verify(b"anything", bad_expected) is False


# ---------------------------------------------------------------------------
# UT-003.2-07: Upper-case hex expected is normalised via .lower()
# ---------------------------------------------------------------------------


def test_ut_003_2_07_verify_accepts_uppercase_hex() -> None:
    """Upper-case hex `expected` matches when the lower-case hex would."""
    payload = b"abc"
    assert verify(payload, _SHA256_ABC.upper()) is True


def test_ut_003_2_07b_verify_accepts_mixed_case_hex() -> None:
    """Mixed-case hex `expected` still matches."""
    payload = b"abc"
    mixed = "".join(
        c.upper() if i % 2 == 0 else c.lower() for i, c in enumerate(_SHA256_ABC)
    )
    assert verify(payload, mixed) is True


# ---------------------------------------------------------------------------
# UT-003.2-08: Determinism — same input yields same checksum
# ---------------------------------------------------------------------------


def test_ut_003_2_08_determinism() -> None:
    """compute is deterministic: repeated calls yield identical digests."""
    payload = b"determinism check"
    baseline = compute(payload)
    for _ in range(100):
        assert compute(payload) == baseline


# ---------------------------------------------------------------------------
# UT-003.2-09: Large input (1 MB) succeeds within test timeout
# ---------------------------------------------------------------------------


def test_ut_003_2_09_large_payload() -> None:
    """compute handles a 1 MB payload and verify agrees."""
    payload = b"x" * (1024 * 1024)
    digest = compute(payload)
    assert len(digest) == 64
    assert verify(payload, digest) is True


# ---------------------------------------------------------------------------
# UT-003.2-10 / 11: Output contract — length 64, lower-case hex only
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "payload",
    [b"", b"abc", b"\x00\xff", b"\x00" * 10],
)
def test_ut_003_2_10_output_length_is_64(payload: bytes) -> None:
    """compute always returns exactly 64 hex characters."""
    assert len(compute(payload)) == 64


@pytest.mark.parametrize(
    "payload",
    [b"", b"abc", b"\x00\xff", b"\x00" * 10],
)
def test_ut_003_2_11_output_is_lowercase_hex(payload: bytes) -> None:
    """compute returns only [0-9a-f] characters — no upper case, no other."""
    digest = compute(payload)
    assert all(c in "0123456789abcdef" for c in digest)


# ---------------------------------------------------------------------------
# UT-003.2-12 / 13: hypothesis properties (roundtrip and collision resistance)
# ---------------------------------------------------------------------------


@given(payload=st.binary(max_size=4096))
@settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
def test_ut_003_2_12_property_roundtrip(payload: bytes) -> None:
    """For any bytes, verify(data, compute(data)) is True."""
    assert verify(payload, compute(payload)) is True


@given(p1=st.binary(min_size=1, max_size=64), p2=st.binary(min_size=1, max_size=64))
@settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
def test_ut_003_2_13_property_distinct_payloads_distinct_digests(
    p1: bytes,
    p2: bytes,
) -> None:
    """Distinct payloads produce distinct digests (no collisions at small sizes)."""
    if p1 == p2:
        assert compute(p1) == compute(p2)
    else:
        assert compute(p1) != compute(p2)


# ---------------------------------------------------------------------------
# UT-003.2-14: verify rejects a one-character-short expected of valid hex
# ---------------------------------------------------------------------------


def test_ut_003_2_14_verify_rejects_short_valid_hex() -> None:
    """Correct content but one char short — still False."""
    payload = b"abc"
    short = _SHA256_ABC[:-1]
    assert verify(payload, short) is False


# ---------------------------------------------------------------------------
# UT-003.2-15: verify accepts a Python-style extra whitespace? → False
# ---------------------------------------------------------------------------


def test_ut_003_2_15_verify_false_on_whitespace_contaminated_expected() -> None:
    """Whitespace-surrounded expected is rejected (length differs from 64)."""
    payload = b"abc"
    assert verify(payload, f" {_SHA256_ABC} ") is False
