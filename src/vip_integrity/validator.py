"""Integrity validator (UNIT-004.1) per SDD-VIP-001 v0.2 §4.5.

Implements RCM-015 (boot-time state verification). Given a
`RawPersistedRecord` produced by UNIT-003.1 Serializer's `from_json`, the
validator performs the nine checks of §4.5.B and returns either
`Ok(TrustedRecord)` on full success or
`FailsafeRecommended(reasons=[...])` when at least one check fails,
triggering SRS-027 fail-safe boot.

The checks in §4.5.B enumeration order:

1. schema_version is in SUPPORTED_SCHEMA_VERSIONS (SRS-DATA-004)
2. recomputed SHA-256 of payload_bytes matches stored checksum
3. flow_rate is in [0.0, 1200.0] mL/h (SRS-O-001)
4. dose_volume is in [0.0, 9999.9] mL (SRS-I-001)
5. duration_min is in [1, 5999] min (SRS-I-001)
6. flow_rate * duration_min / 60 approximately equals dose_volume within
   +-1 % (SRS-004)
7. not (state == RUNNING and current_flow == 0) -- no drive-halted running
8. accumulated_volume <= dose_volume -- prevents over-delivery on restore
   (HZ-001 critical)
9. state != INITIALIZING -- INITIALIZING is never a saveable state

All failures are collected rather than short-circuited so the caller sees
every cause at once. The function is pure -- no I/O, no shared state,
trivially thread-safe.

Related SRS: SRS-026, SRS-027, SRS-RCM-015.
Related RCM: RCM-015.
Related HZ:  HZ-007 (persisted-data corruption), HZ-001 (over-delivery).
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from decimal import Decimal
from typing import Final

from vip_ctrl.state_machine import State
from vip_persist.records import (
    SUPPORTED_SCHEMA_VERSIONS,
    RawPersistedRecord,
    Settings,
    TrustedRecord,
)

__all__ = [
    "AccumulationExceedsDose",
    "ChecksumMismatch",
    "DoseVolumeOutOfRange",
    "DurationOutOfRange",
    "FailsafeRecommended",
    "FlowRateOutOfRange",
    "IntegrityFailure",
    "Ok",
    "SchemaVersionUnsupported",
    "SettingsInconsistent",
    "StateContradiction",
    "UnsavableState",
    "ValidationResult",
    "check_settings_consistency",
    "compute_sha256",
    "validate",
]


# ---------------------------------------------------------------------------
# Range constants (SDD §4.5.B)
# ---------------------------------------------------------------------------

_MIN_FLOW: Final[Decimal] = Decimal("0.0")
_MAX_FLOW: Final[Decimal] = Decimal("1200.0")
_MIN_DOSE: Final[Decimal] = Decimal("0.0")
_MAX_DOSE: Final[Decimal] = Decimal("9999.9")
_MIN_DURATION: Final[int] = 1
_MAX_DURATION: Final[int] = 5999
_SETTINGS_TOLERANCE: Final[Decimal] = Decimal("0.01")  # +-1 % per SRS-004
_MINUTES_PER_HOUR: Final[Decimal] = Decimal(60)
_ZERO: Final[Decimal] = Decimal("0.0")


# ---------------------------------------------------------------------------
# IntegrityFailure sealed hierarchy (SDD §4.5.C)
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class SchemaVersionUnsupported:
    """schema_version is not in SUPPORTED_SCHEMA_VERSIONS."""

    version: int


@dataclass(frozen=True, slots=True)
class ChecksumMismatch:
    """Recomputed SHA-256 does not match the stored checksum."""

    expected: str
    actual: str


@dataclass(frozen=True, slots=True)
class FlowRateOutOfRange:
    """Settings.flow_rate outside [0.0, 1200.0] mL/h."""

    value: Decimal


@dataclass(frozen=True, slots=True)
class DoseVolumeOutOfRange:
    """Settings.dose_volume outside [0.0, 9999.9] mL."""

    value: Decimal


@dataclass(frozen=True, slots=True)
class DurationOutOfRange:
    """Settings.duration_min outside [1, 5999] minutes."""

    value: int


@dataclass(frozen=True, slots=True)
class SettingsInconsistent:
    """flow_rate * duration_min / 60 differs from dose_volume beyond tolerance."""

    detail: str


@dataclass(frozen=True, slots=True)
class StateContradiction:
    """RuntimeState combination that cannot physically occur."""

    detail: str


@dataclass(frozen=True, slots=True)
class AccumulationExceedsDose:
    """accumulated_volume is greater than the configured dose_volume (HZ-001)."""

    accumulated: Decimal
    dose: Decimal


@dataclass(frozen=True, slots=True)
class UnsavableState:
    """A state that should never have been persisted (e.g. INITIALIZING)."""

    state: State


IntegrityFailure = (
    SchemaVersionUnsupported
    | ChecksumMismatch
    | FlowRateOutOfRange
    | DoseVolumeOutOfRange
    | DurationOutOfRange
    | SettingsInconsistent
    | StateContradiction
    | AccumulationExceedsDose
    | UnsavableState
)


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Ok:
    """Validation success carrying the trusted, frozen record."""

    trusted: TrustedRecord


@dataclass(frozen=True, slots=True)
class FailsafeRecommended:
    """Validation reported ≥ 1 failure; SRS-027 fail-safe boot is required."""

    reasons: list[IntegrityFailure]


ValidationResult = Ok | FailsafeRecommended


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def compute_sha256(payload: bytes) -> str:
    """Return the SHA-256 hex digest of `payload`."""
    return hashlib.sha256(payload).hexdigest()


def check_settings_consistency(settings: Settings, tolerance: Decimal) -> bool:
    """Verify flow_rate * duration_min / 60 approximates dose_volume within tolerance.

    When dose_volume == 0, the check requires expected_dose == 0 exactly;
    any non-zero flow_rate * duration_min would otherwise produce an
    undefined ratio.
    """
    expected_dose = settings.flow_rate * Decimal(settings.duration_min) / _MINUTES_PER_HOUR
    if settings.dose_volume == _MIN_DOSE:
        return expected_dose == _MIN_DOSE
    diff_ratio = abs(expected_dose - settings.dose_volume) / settings.dose_volume
    return diff_ratio <= tolerance


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def validate(record: RawPersistedRecord) -> ValidationResult:  # noqa: C901
    # The 9-check enumeration of SDD §4.5.B intentionally fans out to 9
    # branches here; splitting them into helpers would obscure the SDD
    # correspondence that auditors trace line-for-line.
    """Integrity-validate a deserialised persisted record.

    Returns `Ok(TrustedRecord)` when every SDD §4.5.B check passes;
    otherwise returns `FailsafeRecommended(reasons=[...])` enumerating all
    detected failures in §4.5.B order. Pure function -- no side effects.
    """
    failures: list[IntegrityFailure] = []
    settings = record.settings
    runtime_state = record.runtime_state

    # 1. Schema version
    if record.schema_version not in SUPPORTED_SCHEMA_VERSIONS:
        failures.append(SchemaVersionUnsupported(record.schema_version))

    # 2. Checksum
    recomputed = compute_sha256(record.payload_bytes)
    if recomputed != record.checksum:
        failures.append(ChecksumMismatch(expected=record.checksum, actual=recomputed))

    # 3. Flow-rate range
    if not (_MIN_FLOW <= settings.flow_rate <= _MAX_FLOW):
        failures.append(FlowRateOutOfRange(settings.flow_rate))

    # 4. Dose-volume range
    if not (_MIN_DOSE <= settings.dose_volume <= _MAX_DOSE):
        failures.append(DoseVolumeOutOfRange(settings.dose_volume))

    # 5. Duration range
    if not (_MIN_DURATION <= settings.duration_min <= _MAX_DURATION):
        failures.append(DurationOutOfRange(settings.duration_min))

    # 6. SRS-004 settings consistency
    if not check_settings_consistency(settings, _SETTINGS_TOLERANCE):
        failures.append(
            SettingsInconsistent(
                f"flow_rate={settings.flow_rate}, "
                f"duration_min={settings.duration_min}, "
                f"dose_volume={settings.dose_volume}",
            ),
        )

    # 7. State and current_flow contradiction
    if runtime_state.state == State.RUNNING and runtime_state.current_flow == _ZERO:
        failures.append(StateContradiction("RUNNING but current_flow=0"))

    # 8. Accumulated volume exceeds configured dose (HZ-001)
    if runtime_state.accumulated_volume > settings.dose_volume:
        failures.append(
            AccumulationExceedsDose(
                accumulated=runtime_state.accumulated_volume,
                dose=settings.dose_volume,
            ),
        )

    # 9. Unsavable state
    if runtime_state.state == State.INITIALIZING:
        failures.append(UnsavableState(runtime_state.state))

    if failures:
        return FailsafeRecommended(reasons=failures)
    return Ok(trusted=TrustedRecord.from_raw(record))
