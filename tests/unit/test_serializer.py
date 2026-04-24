"""Unit tests for UNIT-003.1 Serializer (SDD §4.12).

Cross-reviewed against SDD §4.12 / SRS-DATA-001/004 / UTPR §7.3.6 (skeleton)
before Red (Step 19 B7 pre-implementation review). Seven논점 were resolved
with the user's consent on the recommended default; all changes are
MINOR-class (no SRS/SDD/RMF/SAD body change):

1. PersistedRecord and RawPersistedRecord are distinct pydantic models
   sharing the same field layout, per SDD §4.12.B.
2. `build_persisted_record` factory computes payload_bytes and checksum
   inside the Serializer module (generation responsibility).
3. `State` enum is serialised **by name** (tagged object), never by
   `auto()` numeric value, to survive future enum insertions.
4. `from_json` keeps the existing `RawPersistedRecord.model_validate`
   call -- records.py is NOT modified in Step 19 B7.
5. hypothesis drives round-trip and determinism at `max_examples=200`.
6. `current_schema_version()` is a function, not a constant re-export.
7. MC/DC target raised to 100 % (B5 Atomic Writer precedent for
   RCM-015 prerequisites).

An 8th point was resolved during implementation: `payload_bytes: bytes`
has no entry in the SDD §4.12.C pseudocode `_default` hook. We adopted
the tagged-object pattern `{"__bytes__": "<base64>"}` consistent with
the existing Decimal tag -- SDD pseudocode extension, MINOR.
"""

from __future__ import annotations

import json
from decimal import Decimal
from typing import Final

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from pydantic import ValidationError

from vip_ctrl.state_machine import State
from vip_integrity.validator import Ok, validate
from vip_persist.records import (
    CURRENT_SCHEMA_VERSION,
    PersistedRecord,
    RawPersistedRecord,
    RuntimeState,
    Settings,
)
from vip_persist.serializer import (
    _default,
    _hook,
    build_persisted_record,
    compute_payload_checksum,
    current_schema_version,
    from_json,
    to_json,
)

# ---------------------------------------------------------------------------
# Fixtures and helpers
# ---------------------------------------------------------------------------

_DEFAULT_SAVED_AT: Final[str] = "2026-04-24T10:00:00Z"


def make_settings(
    flow_rate: Decimal = Decimal("100.0"),
    dose_volume: Decimal = Decimal("1000.0"),
    duration_min: int = 600,
) -> Settings:
    return Settings(flow_rate=flow_rate, dose_volume=dose_volume, duration_min=duration_min)


def make_runtime_state(
    state: State = State.IDLE,
    current_flow: Decimal = Decimal("0.0"),
    accumulated_volume: Decimal = Decimal("0.0"),
) -> RuntimeState:
    return RuntimeState(
        state=state,
        current_flow=current_flow,
        accumulated_volume=accumulated_volume,
    )


def make_record(
    settings: Settings | None = None,
    runtime_state: RuntimeState | None = None,
    saved_at: str = _DEFAULT_SAVED_AT,
) -> PersistedRecord:
    return build_persisted_record(
        settings=settings or make_settings(),
        runtime_state=runtime_state or make_runtime_state(),
        saved_at=saved_at,
    )


# ---------------------------------------------------------------------------
# UT-003.1-01: build_persisted_record + to_json 正常
# ---------------------------------------------------------------------------


def test_ut_003_1_01_build_and_to_json_produces_utf8_bytes() -> None:
    """build_persisted_record + to_json returns valid UTF-8 JSON bytes."""
    record = make_record()
    data = to_json(record)
    assert isinstance(data, bytes)
    # Must decode as UTF-8
    decoded = data.decode("utf-8")
    # Must be valid JSON (tags included)
    parsed = json.loads(decoded)
    assert isinstance(parsed, dict)
    assert parsed["schema_version"] == CURRENT_SCHEMA_VERSION


# ---------------------------------------------------------------------------
# UT-003.1-02: from_json 正常 — 復元が RawPersistedRecord を返す
# ---------------------------------------------------------------------------


def test_ut_003_1_02_from_json_returns_raw_persisted_record() -> None:
    """from_json on valid payload returns a RawPersistedRecord."""
    record = make_record()
    data = to_json(record)
    raw = from_json(data)
    assert isinstance(raw, RawPersistedRecord)
    assert raw.schema_version == record.schema_version
    assert raw.settings == record.settings
    assert raw.runtime_state == record.runtime_state
    assert raw.payload_bytes == record.payload_bytes
    assert raw.checksum == record.checksum
    assert raw.saved_at == record.saved_at


# ---------------------------------------------------------------------------
# UT-003.1-03: 決定論性 — 同じレコードを N 回 to_json で全バイト列同一
# ---------------------------------------------------------------------------


def test_ut_003_1_03_to_json_is_deterministic() -> None:
    """Serialising the same record N times yields identical bytes each time."""
    record = make_record()
    baseline = to_json(record)
    for _ in range(20):
        assert to_json(record) == baseline


# ---------------------------------------------------------------------------
# UT-003.1-04: Decimal 精度保持 — 0.1 + 0.2 → 0.3 が復元後も等価
# ---------------------------------------------------------------------------


def test_ut_003_1_04_decimal_precision_preserved_across_roundtrip() -> None:
    """Decimal('0.1') + Decimal('0.2') survives round-trip as Decimal('0.3')."""
    tricky = Decimal("0.1") + Decimal("0.2")  # Decimal('0.3')
    settings = make_settings(flow_rate=tricky)
    # SRS-004 consistency: dose = flow * duration / 60
    # tricky * 600 / 60 = tricky * 10 = Decimal('3.0')
    settings = Settings(
        flow_rate=tricky,
        dose_volume=tricky * Decimal(10),
        duration_min=600,
    )
    record = make_record(settings=settings)
    raw = from_json(to_json(record))
    assert raw.settings.flow_rate == Decimal("0.3")
    assert isinstance(raw.settings.flow_rate, Decimal)


# ---------------------------------------------------------------------------
# UT-003.1-05: 不正 JSON → JSONDecodeError
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "bad_payload",
    [
        b"{not json",
        b"",
        b"[]",  # JSON array, not an object the model expects
        b"null",
    ],
)
def test_ut_003_1_05_malformed_json_raises(bad_payload: bytes) -> None:
    """Truncated or invalid JSON raises JSONDecodeError or ValidationError."""
    with pytest.raises((json.JSONDecodeError, ValidationError)):
        from_json(bad_payload)


def test_ut_003_1_05b_invalid_utf8_raises() -> None:
    """Invalid UTF-8 bytes raise UnicodeDecodeError."""
    with pytest.raises(UnicodeDecodeError):
        from_json(b"\xff\xfe\xfd")


# ---------------------------------------------------------------------------
# UT-003.1-06: 必須フィールド欠落 → pydantic ValidationError
# ---------------------------------------------------------------------------


def test_ut_003_1_06_missing_required_field_raises_validation_error() -> None:
    """JSON missing a required field raises pydantic ValidationError."""
    data = json.dumps({"schema_version": 1}).encode("utf-8")
    with pytest.raises(ValidationError):
        from_json(data)


# ---------------------------------------------------------------------------
# UT-003.1-07: 未知 schema_version は Serializer は通過する
# ---------------------------------------------------------------------------


def test_ut_003_1_07_unknown_schema_version_passes_serializer() -> None:
    """schema_version=999 is accepted by Serializer; Integrity Validator rejects.

    Per SDD §4.12.E "未知 schema_version | pydantic + Integrity Validator |
    SchemaVersionUnsupported 失敗" -- the Serializer is a type guard only,
    schema acceptance is the validator's job.
    """
    record = build_persisted_record(
        settings=make_settings(),
        runtime_state=make_runtime_state(),
        saved_at=_DEFAULT_SAVED_AT,
        schema_version=999,
    )
    data = to_json(record)
    raw = from_json(data)
    assert raw.schema_version == 999


# ---------------------------------------------------------------------------
# UT-003.1-08: hypothesis round-trip プロパティ
# ---------------------------------------------------------------------------


@st.composite
def _srs004_consistent_settings(draw: st.DrawFn) -> Settings:
    """Settings strategy producing SRS-004 consistent records."""
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
    expected_dose = min(
        flow_rate * Decimal(duration_min) / Decimal(60),
        Decimal("9999.9"),
    )
    return Settings(
        flow_rate=flow_rate,
        dose_volume=expected_dose,
        duration_min=duration_min,
    )


_RUNTIME_STATES = st.sampled_from(
    [State.IDLE, State.RUNNING, State.PAUSED, State.STOPPED, State.ERROR],
)


@st.composite
def _arbitrary_runtime_state(draw: st.DrawFn) -> RuntimeState:
    state = draw(_RUNTIME_STATES)
    current_flow = draw(
        st.decimals(
            min_value=Decimal("0.0"),
            max_value=Decimal("1200.0"),
            places=2,
            allow_nan=False,
            allow_infinity=False,
        ),
    )
    accumulated_volume = draw(
        st.decimals(
            min_value=Decimal("0.0"),
            max_value=Decimal("9999.9"),
            places=2,
            allow_nan=False,
            allow_infinity=False,
        ),
    )
    return RuntimeState(
        state=state,
        current_flow=current_flow,
        accumulated_volume=accumulated_volume,
    )


@given(settings=_srs004_consistent_settings(), runtime_state=_arbitrary_runtime_state())
@settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
def test_ut_003_1_08_roundtrip_equals_input(
    settings: Settings,
    runtime_state: RuntimeState,
) -> None:
    """to_json then from_json yields a record equal to the input in every field."""
    record = build_persisted_record(
        settings=settings,
        runtime_state=runtime_state,
        saved_at=_DEFAULT_SAVED_AT,
    )
    raw = from_json(to_json(record))
    assert raw.schema_version == record.schema_version
    assert raw.settings == record.settings
    assert raw.runtime_state == record.runtime_state
    assert raw.payload_bytes == record.payload_bytes
    assert raw.checksum == record.checksum
    assert raw.saved_at == record.saved_at


# ---------------------------------------------------------------------------
# UT-003.1-09: State enum は名前でシリアライズ(auto() の値変動耐性)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("state", list(State))
def test_ut_003_1_09_state_serialised_by_name(state: State) -> None:
    """Every State member round-trips by its name, not its auto() numeric."""
    runtime_state = make_runtime_state(state=state)
    record = make_record(runtime_state=runtime_state)
    data = to_json(record)
    # The emitted JSON must contain the enum name somewhere
    assert state.name.encode("ascii") in data
    # And round-trip restores the same State member
    raw = from_json(data)
    assert raw.runtime_state.state is state


# ---------------------------------------------------------------------------
# UT-003.1-10: bytes 型(payload_bytes)は base64 タグで往復
# ---------------------------------------------------------------------------


def test_ut_003_1_10_payload_bytes_roundtrip() -> None:
    """payload_bytes is tagged with base64 and decodes identically on round-trip."""
    record = make_record()
    assert record.payload_bytes  # non-empty
    data = to_json(record)
    # Round-trip must preserve the exact bytes
    raw = from_json(data)
    assert raw.payload_bytes == record.payload_bytes
    # And the tag marker must appear in the serialised form
    assert b"__bytes__" in data


# ---------------------------------------------------------------------------
# UT-003.1-11: current_schema_version API
# ---------------------------------------------------------------------------


def test_ut_003_1_11_current_schema_version_returns_int() -> None:
    """current_schema_version() returns the constant as an int."""
    assert current_schema_version() == CURRENT_SCHEMA_VERSION
    assert isinstance(current_schema_version(), int)


# ---------------------------------------------------------------------------
# UT-003.1-12: 統合 — build → to_json → from_json → validate (Integrity)
# ---------------------------------------------------------------------------


def test_ut_003_1_12_integration_with_integrity_validator() -> None:
    """End-to-end: Serializer output feeds Integrity Validator and returns Ok."""
    record = make_record()
    raw = from_json(to_json(record))
    result = validate(raw)
    assert isinstance(result, Ok)


# ---------------------------------------------------------------------------
# UT-003.1-13: compute_payload_checksum は決定論的かつ SHA-256 で整合
# ---------------------------------------------------------------------------


def test_ut_003_1_13_compute_payload_checksum_is_deterministic() -> None:
    """compute_payload_checksum yields the same (bytes, digest) pair for same input."""
    settings = make_settings()
    runtime_state = make_runtime_state()
    p1, c1 = compute_payload_checksum(1, settings, runtime_state, _DEFAULT_SAVED_AT)
    p2, c2 = compute_payload_checksum(1, settings, runtime_state, _DEFAULT_SAVED_AT)
    assert p1 == p2
    assert c1 == c2
    # Checksum is a 64-char hex digest (SHA-256)
    assert len(c1) == 64
    assert all(ch in "0123456789abcdef" for ch in c1)


# ---------------------------------------------------------------------------
# UT-003.1-14: JSON 中のキーは sort_keys=True で辞書順
# ---------------------------------------------------------------------------


def test_ut_003_1_14_keys_are_sorted_for_determinism() -> None:
    """Top-level JSON keys appear in sorted order (enables stable checksum)."""
    record = make_record()
    data = to_json(record)
    parsed = json.loads(data.decode("utf-8"))
    # Top-level record fields must be in sorted order in the raw bytes
    decoded_text = data.decode("utf-8")
    top_keys = list(parsed.keys())
    assert top_keys == sorted(top_keys)
    # Confirmed by checking that the key positions in the raw string are sorted
    positions = [decoded_text.index(f'"{k}"') for k in sorted(top_keys)]
    assert positions == sorted(positions)


# ---------------------------------------------------------------------------
# UT-003.1-15: 不明 type を default で送ると TypeError
# ---------------------------------------------------------------------------


def test_ut_003_1_15_unsupported_type_raises_type_error() -> None:
    """Passing an unsupported object via the default hook raises TypeError.

    SDD §4.12.E "未知 type の encode | TypeError | プログラムバグ(到達不可、テストで予防)".
    """

    class _NotEncodable:
        pass

    with pytest.raises(TypeError):
        _default(_NotEncodable())


# ---------------------------------------------------------------------------
# UT-003.1-16: _hook のパススルー — タグなし dict は変形しない
# ---------------------------------------------------------------------------


def test_ut_003_1_16_hook_passes_through_plain_dicts() -> None:
    """_hook leaves non-tagged dicts unchanged."""
    plain = {"schema_version": 1, "other": "value"}
    result = _hook(plain)
    assert result == plain
    assert result is plain  # identity preserved


# ---------------------------------------------------------------------------
# UT-003.1-17: hypothesis 決定論性 — 任意の有効レコードで 5 回 to_json 全一致
# ---------------------------------------------------------------------------


@given(settings=_srs004_consistent_settings(), runtime_state=_arbitrary_runtime_state())
@settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
def test_ut_003_1_17_determinism_property(
    settings: Settings,
    runtime_state: RuntimeState,
) -> None:
    """For any valid record, 5 consecutive to_json calls produce identical bytes."""
    record = build_persisted_record(
        settings=settings,
        runtime_state=runtime_state,
        saved_at=_DEFAULT_SAVED_AT,
    )
    baseline = to_json(record)
    for _ in range(4):
        assert to_json(record) == baseline
