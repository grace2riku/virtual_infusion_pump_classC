"""Validation API bridge (CR-0004 (b) per CRR-VIP-001).

Adapter that wraps `vip_api_b.validation_api.validate_settings`(class B,
returns `Ok(settings)` / `Err(failures=[...])`)so it satisfies the
`vip_api.control_api.ValidationApi` Protocol(returns
`list[ValidationError]`、空 list = OK).

Direction: class C → class B import (allowed by SAD §9 SEP-001;
class-B side never imports class-C, verified by UT-005.3-13).

Failure mapping(SDD §4.17.B → §4.15.B):

* `OutOfRange(field, actual, allowed_range)` → ValidationError(field, message=
    f"out_of_range: actual={actual}, allowed={allowed_range}")
* `Inconsistency(detail)` → ValidationError(field="settings_consistency",
    message=f"inconsistency: {detail}")
* `MissingField(field)` → ValidationError(field, message="missing_field")

Related CR: CR-0004 (Issue #32) — F1 着手時に発見した
ValidationApi Protocol(`-> list[ValidationError]`)と
`vip_api_b.validate_settings`(`-> ValidationResult`)の戻り値型不整合を、
クラス B の `Ok` / `Err` を境界仕様の主とした上で本 Adapter で吸収する。
"""

from __future__ import annotations

from typing import TYPE_CHECKING, assert_never

from vip_api.control_api import ValidationApi, ValidationError
from vip_api_b.validation_api import (
    Err,
    Inconsistency,
    MissingField,
    Ok,
    OutOfRange,
)
from vip_api_b.validation_api import (
    validate_settings as _validate_settings_b,
)

if TYPE_CHECKING:
    from vip_api_b.validation_api import ValidationFailure
    from vip_persist.records import Settings

__all__ = [
    "ClassBValidationApiAdapter",
    "make_validation_api",
]


_CONSISTENCY_FIELD = "settings_consistency"


def _failure_to_error(failure: ValidationFailure) -> ValidationError:
    """Map a class-B `ValidationFailure` to a class-C `ValidationError`."""
    if isinstance(failure, OutOfRange):
        return ValidationError(
            field=failure.field,
            message=f"out_of_range: actual={failure.actual}, allowed={failure.allowed_range}",
        )
    if isinstance(failure, Inconsistency):
        return ValidationError(
            field=_CONSISTENCY_FIELD,
            message=f"inconsistency: {failure.detail}",
        )
    if isinstance(failure, MissingField):
        return ValidationError(field=failure.field, message="missing_field")
    assert_never(failure)


class ClassBValidationApiAdapter:
    """`ValidationApi` Protocol を満たす Adapter(`vip_api_b` の `Ok` / `Err` 包み込み)."""

    def validate_settings(self, settings: Settings) -> list[ValidationError]:
        """Validate via class-B `validate_settings` and flatten to a list."""
        result = _validate_settings_b(settings)
        if isinstance(result, Ok):
            return []
        if isinstance(result, Err):
            return [_failure_to_error(f) for f in result.failures]
        assert_never(result)


def make_validation_api() -> ValidationApi:
    """Build a `ValidationApi`-compatible adapter wrapping `vip_api_b`."""
    return ClassBValidationApiAdapter()
