"""Flow command validator (UNIT-001.4) per SDD-VIP-001 v0.2 §4.2.

Implements RCM-001 (flow command range and settings consistency check).
The validator is a pure function: it receives an immutable `FlowCommand`
plus a `ControlContext` snapshot and returns a `ValidationResult` union.
No side effects, no shared state, fully thread-safe.

Algorithm (SDD §4.2.C):
1. Reject NaN / Infinite values (`NAN_OR_INFINITE`).
2. Reject negative rates (`NEGATIVE`).
3. Reject rates above `MAX_FLOW` (`OUT_OF_RANGE`).
4. When `current_state == State.RUNNING`, compare against
   `current_settings.flow_rate`:
   - if expected is zero, the command must also be zero,
     otherwise `MISMATCH_WITH_SETTINGS`,
   - else if `|rate - expected| / expected > TOLERANCE` (5%),
     `MISMATCH_WITH_SETTINGS`.
5. Otherwise return `ValidationOk(ValidatedFlowCommand)`.

Related SRS: SRS-O-001, SRS-RCM-001, SRS-005.
Related RCM: RCM-001.
Related HZ:  HZ-001 (over-delivery), HZ-002 (under-delivery).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime  # noqa: TC003  (runtime use in dataclass field types)
from decimal import Decimal
from enum import Enum, auto
from typing import Final

from vip_ctrl.state_machine import State

__all__ = [
    "MAX_FLOW",
    "MIN_FLOW",
    "TOLERANCE",
    "ControlContext",
    "FlowCommand",
    "Settings",
    "ValidatedFlowCommand",
    "ValidationErr",
    "ValidationOk",
    "ValidationReason",
    "ValidationResult",
    "validate",
]


# ---------------------------------------------------------------------------
# Domain constants (SDD §4.2.C)
# ---------------------------------------------------------------------------

MIN_FLOW: Final[Decimal] = Decimal("0.0")
MAX_FLOW: Final[Decimal] = Decimal("1200.0")
TOLERANCE: Final[Decimal] = Decimal("0.05")  # ±5% per SRS-005

_ZERO: Final[Decimal] = Decimal("0.0")


# ---------------------------------------------------------------------------
# Value objects
# ---------------------------------------------------------------------------


class ValidationReason(Enum):
    """Why a flow command was rejected (SDD §4.2.B)."""

    OUT_OF_RANGE = auto()
    MISMATCH_WITH_SETTINGS = auto()
    NEGATIVE = auto()
    NAN_OR_INFINITE = auto()


@dataclass(frozen=True, slots=True)
class FlowCommand:
    """Immutable input to `validate`. SDD §4.2.B."""

    flow_rate: Decimal
    timestamp: datetime


@dataclass(frozen=True, slots=True)
class ValidatedFlowCommand:
    """Immutable output of a successful validation. SDD §4.2.B."""

    flow_rate: Decimal
    approved_at: datetime


@dataclass(frozen=True, slots=True)
class Settings:
    """Subset of operator-configured settings used by the validator.

    UNIT-001.2 SettingsStore owns the full `Settings` aggregate; the validator
    consumes only the `flow_rate` field through this minimal projection so that
    UNIT-001.4 stays decoupled from settings persistence.
    """

    flow_rate: Decimal


@dataclass(frozen=True, slots=True)
class ControlContext:
    """Snapshot of the control loop context required for validation.

    Carries the latest committed `Settings` and the current `State`. Both are
    captured by the caller before invoking `validate` so the validator never
    observes a partially updated context.
    """

    current_settings: Settings
    current_state: State


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ValidationOk:
    """Successful validation outcome carrying the approved command."""

    validated: ValidatedFlowCommand


@dataclass(frozen=True, slots=True)
class ValidationErr:
    """Failed validation outcome carrying the rejection reason."""

    reason: ValidationReason


ValidationResult = ValidationOk | ValidationErr


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def validate(command: FlowCommand, context: ControlContext) -> ValidationResult:
    """Validate a flow command against range and (when RUNNING) settings.

    Pure function — no side effects. See module docstring for the algorithm.
    """
    rate = command.flow_rate

    # Step 1: NaN / Infinity must be rejected before any comparison since
    # `Decimal('NaN') < x` raises `InvalidOperation`.
    if rate.is_nan() or rate.is_infinite():
        return ValidationErr(ValidationReason.NAN_OR_INFINITE)

    # Step 2/3: range
    if rate < MIN_FLOW:
        return ValidationErr(ValidationReason.NEGATIVE)
    if rate > MAX_FLOW:
        return ValidationErr(ValidationReason.OUT_OF_RANGE)

    # Step 4: settings consistency only matters during active infusion.
    if context.current_state is State.RUNNING:
        expected = context.current_settings.flow_rate
        if expected == _ZERO:
            if rate != _ZERO:
                return ValidationErr(ValidationReason.MISMATCH_WITH_SETTINGS)
        else:
            diff_ratio = abs(rate - expected) / expected
            if diff_ratio > TOLERANCE:
                return ValidationErr(ValidationReason.MISMATCH_WITH_SETTINGS)

    # Step 5: accepted — preserve the caller's Decimal precision.
    return ValidationOk(
        ValidatedFlowCommand(flow_rate=rate, approved_at=command.timestamp),
    )
