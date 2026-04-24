"""Unit tests for UNIT-004.1 Integrity Validator (SDD §4.5).

Cross-reviewed against SDD §4.5 / SRS-026/027/RCM-015 / UTPR §7.3.5 before
Red (Step 19 B6 pre-implementation review). Four inconsistencies were
harmonised as MINOR-class documentation updates (no SRS/SDD/RMF/SAD body
change):

1. Return types aligned with SDD §4.5.A: `Ok(TrustedRecord)` /
   `FailsafeRecommended(reasons=[...])` (instead of UTPR's `Err`).
2. UT-004.1-03/04/08 redirected from pydantic-guarded cases (record
   construction would raise `ValidationError` before validate runs) to the
   un-covered SDD §4.5.B checks: `SchemaVersionUnsupported` /
   `DoseVolumeOutOfRange` / `SettingsInconsistent`.
3. UT-004.1-09 redirected from `FutureTimestamp` (not in SDD §4.5.B) to
   `AccumulationExceedsDose` — a HZ-001 critical check previously untested.
4. UT-004.1-10 redirected from `ERROR ∧ error_reason==None` (not in SDD)
   to `StateContradiction("RUNNING but current_flow=0")` — the first
   state-combination check in the §4.5.B pseudocode.
"""

from __future__ import annotations

import hashlib
from dataclasses import FrozenInstanceError
from decimal import Decimal
from typing import Final

import pytest
from hypothesis import assume, given
from hypothesis import strategies as st

from vip_ctrl.state_machine import State
from vip_integrity.validator import (
    AccumulationExceedsDose,
    ChecksumMismatch,
    DoseVolumeOutOfRange,
    DurationOutOfRange,
    FailsafeRecommended,
    FlowRateOutOfRange,
    Ok,
    SchemaVersionUnsupported,
    SettingsInconsistent,
    StateContradiction,
    UnsavableState,
    check_settings_consistency,
    compute_sha256,
    validate,
)
from vip_persist.records import (
    CURRENT_SCHEMA_VERSION,
    SUPPORTED_SCHEMA_VERSIONS,
    RawPersistedRecord,
    RuntimeState,
    Settings,
    TrustedRecord,
)

# ---------------------------------------------------------------------------
# Test fixtures and helpers
# ---------------------------------------------------------------------------

_DEFAULT_PAYLOAD: Final[bytes] = b"payload-for-unit-tests-32bytes.."  # 32 bytes exactly
_DEFAULT_SAVED_AT: Final[str] = "2026-04-23T10:00:00Z"


def make_valid_settings(
    flow_rate: Decimal = Decimal("100.0"),
    dose_volume: Decimal = Decimal("1000.0"),
    duration_min: int = 600,
) -> Settings:
    """Build a Settings with SRS-004 consistent values by default.

    flow_rate=100 mL/h * duration_min=600 min / 60 = dose_volume=1000 mL.
    """
    return Settings(flow_rate=flow_rate, dose_volume=dose_volume, duration_min=duration_min)


def make_valid_runtime_state(
    state: State = State.IDLE,
    current_flow: Decimal = Decimal("0.0"),
    accumulated_volume: Decimal = Decimal("0.0"),
) -> RuntimeState:
    return RuntimeState(
        state=state,
        current_flow=current_flow,
        accumulated_volume=accumulated_volume,
    )


def make_raw_record(
    settings: Settings | None = None,
    runtime_state: RuntimeState | None = None,
    schema_version: int = CURRENT_SCHEMA_VERSION,
    payload_bytes: bytes = _DEFAULT_PAYLOAD,
    checksum: str | None = None,
    saved_at: str = _DEFAULT_SAVED_AT,
) -> RawPersistedRecord:
    settings = settings or make_valid_settings()
    runtime_state = runtime_state or make_valid_runtime_state()
    if checksum is None:
        checksum = compute_sha256(payload_bytes)
    return RawPersistedRecord(
        schema_version=schema_version,
        settings=settings,
        runtime_state=runtime_state,
        payload_bytes=payload_bytes,
        checksum=checksum,
        saved_at=saved_at,
    )


# ---------------------------------------------------------------------------
# UT-004.1-01: 正常系 → Ok(TrustedRecord)
# ---------------------------------------------------------------------------


def test_ut_004_1_01_valid_record_returns_ok() -> None:
    """Valid record with all nine §4.5.B checks satisfied → Ok(TrustedRecord)."""
    record = make_raw_record()
    result = validate(record)
    assert isinstance(result, Ok)
    assert isinstance(result.trusted, TrustedRecord)
    assert result.trusted.schema_version == record.schema_version
    assert result.trusted.settings == record.settings
    assert result.trusted.runtime_state == record.runtime_state
    assert result.trusted.checksum == record.checksum
    assert result.trusted.saved_at == record.saved_at


# ---------------------------------------------------------------------------
# UT-004.1-02: checksum 不一致 → FailsafeRecommended([ChecksumMismatch])
# ---------------------------------------------------------------------------


def test_ut_004_1_02_checksum_mismatch() -> None:
    """Altered checksum (payload unchanged) → ChecksumMismatch reason only."""
    valid = make_raw_record()
    corrupted = valid.model_copy(update={"checksum": "0" * 64})
    result = validate(corrupted)
    assert isinstance(result, FailsafeRecommended)
    assert len(result.reasons) == 1
    reason = result.reasons[0]
    assert isinstance(reason, ChecksumMismatch)
    assert reason.expected == "0" * 64
    assert reason.actual == compute_sha256(valid.payload_bytes)


# ---------------------------------------------------------------------------
# UT-004.1-03: schema_version 非対応 → SchemaVersionUnsupported
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "bad_version",
    [0, 2, 999, -1],
)
def test_ut_004_1_03_schema_version_unsupported(bad_version: int) -> None:
    """schema_version ∉ SUPPORTED_SCHEMA_VERSIONS → SchemaVersionUnsupported."""
    assert bad_version not in SUPPORTED_SCHEMA_VERSIONS
    record = make_raw_record(schema_version=bad_version)
    result = validate(record)
    assert isinstance(result, FailsafeRecommended)
    reasons_of_type = [r for r in result.reasons if isinstance(r, SchemaVersionUnsupported)]
    assert len(reasons_of_type) == 1
    assert reasons_of_type[0].version == bad_version


# ---------------------------------------------------------------------------
# UT-004.1-04: dose_volume / duration_min 境界値外
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("dose", "duration", "failure_type"),
    [
        # dose_volume < 0.0 (boundary below min)
        (Decimal("-0.1"), 600, DoseVolumeOutOfRange),
        # dose_volume > 9999.9 (boundary above max)
        (Decimal("10000.0"), 600, DoseVolumeOutOfRange),
        # duration_min < 1
        (Decimal("0.0"), 0, DurationOutOfRange),
        # duration_min > 5999
        (Decimal("99983.333"), 6000, DurationOutOfRange),
    ],
)
def test_ut_004_1_04_dose_or_duration_out_of_range(
    dose: Decimal,
    duration: int,
    failure_type: type,
) -> None:
    """dose_volume or duration_min outside SRS-I-001 range → matching failure."""
    settings = Settings(flow_rate=Decimal("10.0"), dose_volume=dose, duration_min=duration)
    record = make_raw_record(settings=settings)
    result = validate(record)
    assert isinstance(result, FailsafeRecommended)
    matched = [r for r in result.reasons if isinstance(r, failure_type)]
    assert len(matched) == 1


# ---------------------------------------------------------------------------
# UT-004.1-05: flow_rate 値域外 → FlowRateOutOfRange
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "bad_flow",
    [
        Decimal("-0.1"),  # below SRS-O-001 min
        Decimal("-1.0"),
        Decimal("1200.1"),  # above SRS-O-001 max
        Decimal("2000.0"),
    ],
)
def test_ut_004_1_05_flow_rate_out_of_range(bad_flow: Decimal) -> None:
    """flow_rate outside [0.0, 1200.0] → FlowRateOutOfRange."""
    settings = Settings(
        flow_rate=bad_flow,
        dose_volume=Decimal("1000.0"),
        duration_min=600,
    )
    record = make_raw_record(settings=settings)
    result = validate(record)
    assert isinstance(result, FailsafeRecommended)
    matched = [r for r in result.reasons if isinstance(r, FlowRateOutOfRange)]
    assert len(matched) == 1
    assert matched[0].value == bad_flow


# ---------------------------------------------------------------------------
# UT-004.1-06: 複数エラーの列挙
# ---------------------------------------------------------------------------


def test_ut_004_1_06_multiple_failures_enumerated() -> None:
    """Multiple simultaneous violations → all reasons enumerated in a single result."""
    valid = make_raw_record()
    # checksum 改竄 + flow_rate 値域外(加えて SettingsInconsistent も自動的に発生)
    bad_settings = Settings(
        flow_rate=Decimal("2000.0"),
        dose_volume=Decimal("1000.0"),
        duration_min=600,
    )
    corrupted = valid.model_copy(
        update={
            "checksum": "bad" + "0" * 61,
            "settings": bad_settings,
        },
    )
    result = validate(corrupted)
    assert isinstance(result, FailsafeRecommended)
    reason_types = {type(r) for r in result.reasons}
    assert ChecksumMismatch in reason_types
    assert FlowRateOutOfRange in reason_types
    assert len(result.reasons) >= 2


# ---------------------------------------------------------------------------
# UT-004.1-07: hypothesis — 1 bit 反転 → 必ず ChecksumMismatch
# ---------------------------------------------------------------------------


@given(bit_position=st.integers(min_value=0, max_value=len(_DEFAULT_PAYLOAD) * 8 - 1))
def test_ut_004_1_07_bit_flip_detected_as_checksum_mismatch(bit_position: int) -> None:
    """Flipping any single bit in payload_bytes → ChecksumMismatch always reported."""
    valid = make_raw_record(payload_bytes=_DEFAULT_PAYLOAD)
    byte_idx, bit_idx = divmod(bit_position, 8)
    flipped = bytearray(valid.payload_bytes)
    flipped[byte_idx] ^= 1 << bit_idx
    corrupted = valid.model_copy(update={"payload_bytes": bytes(flipped)})
    result = validate(corrupted)
    assert isinstance(result, FailsafeRecommended)
    assert any(isinstance(r, ChecksumMismatch) for r in result.reasons)


# ---------------------------------------------------------------------------
# UT-004.1-08: SettingsInconsistent(SRS-004 tolerance 外)
# ---------------------------------------------------------------------------


def test_ut_004_1_08_settings_inconsistent_above_tolerance() -> None:
    """flow * duration / 60 != dose_volume above tolerance -> SettingsInconsistent."""
    # expected_dose = 100 * 600 / 60 = 1000, actual dose=1100 -> 10% diff > 1% tolerance
    settings = Settings(
        flow_rate=Decimal("100.0"),
        dose_volume=Decimal("1100.0"),
        duration_min=600,
    )
    record = make_raw_record(settings=settings)
    result = validate(record)
    assert isinstance(result, FailsafeRecommended)
    matched = [r for r in result.reasons if isinstance(r, SettingsInconsistent)]
    assert len(matched) == 1


# ---------------------------------------------------------------------------
# UT-004.1-09: AccumulationExceedsDose(積算量 > 設定量)
# ---------------------------------------------------------------------------


def test_ut_004_1_09_accumulation_exceeds_dose() -> None:
    """accumulated_volume > dose_volume → AccumulationExceedsDose (HZ-001 critical)."""
    runtime_state = make_valid_runtime_state(accumulated_volume=Decimal("1000.1"))
    # dose_volume is 1000.0 in the default settings
    record = make_raw_record(runtime_state=runtime_state)
    result = validate(record)
    assert isinstance(result, FailsafeRecommended)
    matched = [r for r in result.reasons if isinstance(r, AccumulationExceedsDose)]
    assert len(matched) == 1
    assert matched[0].accumulated == Decimal("1000.1")
    assert matched[0].dose == Decimal("1000.0")


# ---------------------------------------------------------------------------
# UT-004.1-10: StateContradiction(RUNNING ∧ current_flow=0.0)
# ---------------------------------------------------------------------------


def test_ut_004_1_10_state_contradiction_running_with_zero_flow() -> None:
    """state=RUNNING with current_flow=0.0 → StateContradiction."""
    runtime_state = make_valid_runtime_state(
        state=State.RUNNING,
        current_flow=Decimal("0.0"),
    )
    record = make_raw_record(runtime_state=runtime_state)
    result = validate(record)
    assert isinstance(result, FailsafeRecommended)
    matched = [r for r in result.reasons if isinstance(r, StateContradiction)]
    assert len(matched) == 1
    assert "RUNNING" in matched[0].detail


# ---------------------------------------------------------------------------
# UT-004.1-11: hypothesis — 正常値範囲 → 常に Ok
# ---------------------------------------------------------------------------


@st.composite
def _consistent_valid_settings(draw: st.DrawFn) -> Settings:
    """Settings strategy that is guaranteed SRS-004 consistent and in range.

    dose_volume is set to the exact expected value (flow * duration / 60) so
    that `check_settings_consistency` sees zero diff regardless of precision.
    Rounding the dose would introduce a representation mismatch that the
    validator legitimately flags as `SettingsInconsistent`.
    """
    duration_min = draw(st.integers(min_value=1, max_value=5999))
    flow_rate = draw(
        st.decimals(
            min_value=Decimal("0.0"),
            max_value=Decimal("1200.0"),
            places=2,
            allow_nan=False,
            allow_infinity=False,
        ),
    )
    expected_dose = flow_rate * Decimal(duration_min) / Decimal(60)
    assume(Decimal("0.0") <= expected_dose <= Decimal("9999.9"))
    return Settings(
        flow_rate=flow_rate,
        dose_volume=expected_dose,
        duration_min=duration_min,
    )


@given(settings=_consistent_valid_settings())
def test_ut_004_1_11_property_valid_records_always_ok(settings: Settings) -> None:
    """Any in-range, SRS-004-consistent record → Ok (no false positives)."""
    record = make_raw_record(settings=settings)
    result = validate(record)
    assert isinstance(result, Ok)


# ---------------------------------------------------------------------------
# UT-004.1-12: hypothesis — 2+ 箇所破損 → 常に FailsafeRecommended、reasons ≥ 2
# ---------------------------------------------------------------------------


@given(
    bad_flow=st.decimals(
        min_value=Decimal("1200.01"),
        max_value=Decimal("9999.99"),
        places=2,
        allow_nan=False,
        allow_infinity=False,
    ),
    bad_dose=st.decimals(
        min_value=Decimal("10000.0"),
        max_value=Decimal("99999.9"),
        places=1,
        allow_nan=False,
        allow_infinity=False,
    ),
)
def test_ut_004_1_12_property_multi_damage_always_failsafe(
    bad_flow: Decimal,
    bad_dose: Decimal,
) -> None:
    """Two+ out-of-range fields → FailsafeRecommended with reasons ≥ 2."""
    settings = Settings(flow_rate=bad_flow, dose_volume=bad_dose, duration_min=600)
    record = make_raw_record(settings=settings)
    result = validate(record)
    assert isinstance(result, FailsafeRecommended)
    assert len(result.reasons) >= 2


# ---------------------------------------------------------------------------
# UT-004.1-13: UnsavableState(state == INITIALIZING)
# ---------------------------------------------------------------------------


def test_ut_004_1_13_unsavable_state_initializing() -> None:
    """Persisted state == INITIALIZING → UnsavableState (state should never be saved)."""
    runtime_state = make_valid_runtime_state(state=State.INITIALIZING)
    record = make_raw_record(runtime_state=runtime_state)
    result = validate(record)
    assert isinstance(result, FailsafeRecommended)
    matched = [r for r in result.reasons if isinstance(r, UnsavableState)]
    assert len(matched) == 1
    assert matched[0].state == State.INITIALIZING


# ---------------------------------------------------------------------------
# UT-004.1-14: 純粋関数(副作用なし)
# ---------------------------------------------------------------------------


def test_ut_004_1_14_validate_is_pure_function() -> None:
    """Calling validate twice on the same record yields equal results."""
    record = make_raw_record()
    r1 = validate(record)
    r2 = validate(record)
    assert isinstance(r1, Ok)
    assert isinstance(r2, Ok)
    assert r1.trusted == r2.trusted


# ---------------------------------------------------------------------------
# UT-004.1-15: TrustedRecord は frozen
# ---------------------------------------------------------------------------


def test_ut_004_1_15_trusted_record_is_frozen() -> None:
    """TrustedRecord is a frozen dataclass — attribute assignment raises."""
    record = make_raw_record()
    result = validate(record)
    assert isinstance(result, Ok)
    with pytest.raises(FrozenInstanceError):
        result.trusted.schema_version = 999  # type: ignore[misc]


# ---------------------------------------------------------------------------
# UT-004.1-16: SUPPORTED_SCHEMA_VERSIONS の内容
# ---------------------------------------------------------------------------


def test_ut_004_1_16_supported_schema_versions_contains_current() -> None:
    """SUPPORTED_SCHEMA_VERSIONS must contain CURRENT_SCHEMA_VERSION."""
    assert CURRENT_SCHEMA_VERSION in SUPPORTED_SCHEMA_VERSIONS
    assert isinstance(SUPPORTED_SCHEMA_VERSIONS, frozenset)


# ---------------------------------------------------------------------------
# UT-004.1-17: check_settings_consistency tolerance 境界
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("flow_rate", "duration", "dose", "tolerance", "expected"),
    [
        # 0% diff — perfectly consistent
        (Decimal(100), 600, Decimal("1000.0"), Decimal("0.01"), True),
        # exactly at tolerance boundary (1%)
        (Decimal(100), 600, Decimal("1010.0"), Decimal("0.01"), True),
        # just above tolerance (1.1%)
        (Decimal(100), 600, Decimal("1011.0"), Decimal("0.01"), False),
        # 2% diff with 5% tolerance — consistent
        (Decimal(100), 600, Decimal("1020.0"), Decimal("0.05"), True),
    ],
)
def test_ut_004_1_17_settings_consistency_tolerance_boundary(
    flow_rate: Decimal,
    duration: int,
    dose: Decimal,
    tolerance: Decimal,
    expected: bool,  # noqa: FBT001  (pytest.parametrize supplies positionally)
) -> None:
    """check_settings_consistency returns True at/under tolerance, False above."""
    settings = Settings(flow_rate=flow_rate, dose_volume=dose, duration_min=duration)
    assert check_settings_consistency(settings, tolerance) is expected


# ---------------------------------------------------------------------------
# UT-004.1-18: 複数 failure が SDD §4.5.B の順序で列挙される
# ---------------------------------------------------------------------------


def test_ut_004_1_18_failure_enumeration_follows_sdd_order() -> None:
    """Failures appear in SDD §4.5.B enumeration order: schema → checksum → flow …."""
    # Force violations of: schema, checksum, flow, dose, duration
    settings = Settings(
        flow_rate=Decimal("-1.0"),  # FlowRateOutOfRange
        dose_volume=Decimal("-1.0"),  # DoseVolumeOutOfRange
        duration_min=0,  # DurationOutOfRange
    )
    record = make_raw_record(
        schema_version=999,
        settings=settings,
        checksum="deadbeef" + "0" * 56,
    )
    result = validate(record)
    assert isinstance(result, FailsafeRecommended)
    types = [type(r) for r in result.reasons]
    # SchemaVersionUnsupported precedes ChecksumMismatch, which precedes range checks
    assert types.index(SchemaVersionUnsupported) < types.index(ChecksumMismatch)
    assert types.index(ChecksumMismatch) < types.index(FlowRateOutOfRange)
    assert types.index(FlowRateOutOfRange) < types.index(DoseVolumeOutOfRange)
    assert types.index(DoseVolumeOutOfRange) < types.index(DurationOutOfRange)


# ---------------------------------------------------------------------------
# UT-004.1-19: check_settings_consistency の dose == 0 分岐
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("flow_rate", "duration", "dose", "expected"),
    [
        # dose == 0, flow * duration == 0 → consistent
        (Decimal("0.0"), 1, Decimal("0.0"), True),
        # dose == 0, flow * duration != 0 → inconsistent
        (Decimal("100.0"), 60, Decimal("0.0"), False),
    ],
)
def test_ut_004_1_19_settings_consistency_zero_dose_branch(
    flow_rate: Decimal,
    duration: int,
    dose: Decimal,
    expected: bool,  # noqa: FBT001  (pytest.parametrize supplies positionally)
) -> None:
    """When dose_volume == 0, consistency requires expected_dose == 0."""
    settings = Settings(flow_rate=flow_rate, dose_volume=dose, duration_min=duration)
    assert check_settings_consistency(settings, Decimal("0.01")) is expected


# ---------------------------------------------------------------------------
# UT-004.1-20: compute_sha256 の契約
# ---------------------------------------------------------------------------


def test_ut_004_1_20_compute_sha256_matches_hashlib() -> None:
    """compute_sha256 delegates to hashlib.sha256 and returns hex digest."""
    payload = b"arbitrary-payload"
    expected = hashlib.sha256(payload).hexdigest()
    assert compute_sha256(payload) == expected
    # Deterministic
    assert compute_sha256(payload) == compute_sha256(payload)
    # Empty payload has a well-known SHA-256
    assert compute_sha256(b"") == (
        "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    )
