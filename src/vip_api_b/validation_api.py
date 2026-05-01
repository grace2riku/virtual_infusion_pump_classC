"""Validation API (UNIT-005.3, class B) per SDD-VIP-001 v0.2 §4.17.

Pure-function semantic validation of `Settings` (SRS-004 consistency
constraint, SRS-005 range validation). Class B per SAD §9 SEP-001:
the implementation must not import any class-C unit (verified by the
AST-based test UT-005.3-13). Only `vip_persist.records.Settings` is
allowed because it is a frozen value object with no behaviour, and
treating it as a shared data type does not create the kind of
behavioural coupling SEP-001 prevents.

Step 19 B18 design judgments (recorded in DEVELOPMENT_STEPS.md):

* SDD §4.17.C ``drug_name`` validation is deferred to Inc.4 because
  ``vip_persist.records.Settings`` does not yet carry that field
  (B15/B16/B17 hand-off chain). The Inc.1 implementation includes the
  range and SRS-004 consistency checks; the ``drug_name`` rule will
  land alongside the Settings extension in Inc.4.
* The function never raises across the SEP-001 boundary: a top-level
  ``try / except`` wraps the whole body and returns
  ``Err([Inconsistency("internal: ...")])`` on any unexpected failure
  (SDD §4.17.E). This is the dual of UNIT-005.1's exception-swallow
  contract for class-C → class-B inputs.
* Result types use the same ``Ok`` / ``Err`` naming as
  ``vip_integrity.validator``; reusing the local module names keeps
  this file self-contained even though the type identities differ.
* All value objects are frozen+slots dataclasses (B11〜B17 pattern);
  UT-005.3-10 exercises the frozen contract.

Related SRS: SRS-UX-001, SRS-004, SRS-005.
Related RCM: — (class B side, separated).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from decimal import Decimal
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from vip_persist.records import Settings

__all__ = [
    "TOLERANCE",
    "Err",
    "Inconsistency",
    "MissingField",
    "Ok",
    "OutOfRange",
    "ValidationFailure",
    "ValidationResult",
    "validate_settings",
]


_logger = logging.getLogger(__name__)


TOLERANCE: Final[Decimal] = Decimal("0.01")
"""SRS-004 inclusive tolerance for the flow x duration / 60 ≈ dose check (1%)."""

_FLOW_RATE_MIN: Final[Decimal] = Decimal("0.0")
_FLOW_RATE_MAX: Final[Decimal] = Decimal("1200.0")
_DOSE_VOLUME_MIN: Final[Decimal] = Decimal("0.0")
_DOSE_VOLUME_MAX: Final[Decimal] = Decimal("9999.9")
_DURATION_MIN_LOWER: Final[int] = 1
_DURATION_MIN_UPPER: Final[int] = 5999
_SECONDS_PER_HOUR_DECIMAL: Final[Decimal] = Decimal("60.0")


# ---------------------------------------------------------------------------
# Failure value objects (SDD §4.17.B)
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class OutOfRange:
    """A field outside its declared inclusive range."""

    field: str
    actual: object
    allowed_range: str


@dataclass(frozen=True, slots=True)
class Inconsistency:
    """A cross-field invariant (e.g. SRS-004) was violated."""

    detail: str


@dataclass(frozen=True, slots=True)
class MissingField:
    """A required field was empty / missing."""

    field: str


ValidationFailure = OutOfRange | Inconsistency | MissingField


# ---------------------------------------------------------------------------
# Result value objects (SDD §4.17.A)
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Ok:
    """Validation passed; carries the validated Settings."""

    settings: Settings


@dataclass(frozen=True, slots=True)
class Err:
    """Validation failed; carries every detected failure."""

    failures: list[ValidationFailure]


ValidationResult = Ok | Err


# ---------------------------------------------------------------------------
# Validator
# ---------------------------------------------------------------------------


def validate_settings(settings: Settings) -> ValidationResult:
    """Validate Settings semantically (SDD §4.17.C; pure, never raises)."""
    try:
        failures: list[ValidationFailure] = []

        if not (_FLOW_RATE_MIN <= settings.flow_rate <= _FLOW_RATE_MAX):
            failures.append(
                OutOfRange(
                    field="flow_rate",
                    actual=settings.flow_rate,
                    allowed_range=f"{_FLOW_RATE_MIN}..{_FLOW_RATE_MAX}",
                ),
            )
        if not (_DOSE_VOLUME_MIN <= settings.dose_volume <= _DOSE_VOLUME_MAX):
            failures.append(
                OutOfRange(
                    field="dose_volume",
                    actual=settings.dose_volume,
                    allowed_range=f"{_DOSE_VOLUME_MIN}..{_DOSE_VOLUME_MAX}",
                ),
            )
        if not (_DURATION_MIN_LOWER <= settings.duration_min <= _DURATION_MIN_UPPER):
            failures.append(
                OutOfRange(
                    field="duration_min",
                    actual=settings.duration_min,
                    allowed_range=f"{_DURATION_MIN_LOWER}..{_DURATION_MIN_UPPER}",
                ),
            )

        if settings.flow_rate > _FLOW_RATE_MIN and settings.duration_min > 0:
            # flow_rate > 0 かつ duration_min > 0 のとき expected_dose > 0 が必ず成立。
            expected_dose = (
                settings.flow_rate * Decimal(settings.duration_min) / _SECONDS_PER_HOUR_DECIMAL
            )
            diff_ratio = abs(expected_dose - settings.dose_volume) / expected_dose
            if diff_ratio > TOLERANCE:
                failures.append(
                    Inconsistency(
                        detail=(
                            f"flow*duration/60={expected_dose}, "
                            f"dose={settings.dose_volume}, diff={diff_ratio:.4f}"
                        ),
                    ),
                )

        # Inc.1 では drug_name 検証を行わない(Inc.4 で Settings 拡張時に追加予定)。
        # SDD §4.17.C drug_name の MissingField チェックは UTPR §7.3.17 申し送り。

    except Exception as exc:  # SEP-001 boundary swallow per SDD §4.17.E
        _logger.exception("validate_settings: internal exception swallowed")
        return Err(
            failures=[Inconsistency(detail=f"internal: {exc.__class__.__name__}")],
        )

    if not failures:
        return Ok(settings=settings)
    return Err(failures=failures)
