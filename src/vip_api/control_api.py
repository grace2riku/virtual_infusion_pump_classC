"""Control API (UNIT-005.1) per SDD-VIP-001 v0.2 §4.15.

Thin Facade over Command Handler (UNIT-001.3), Resume Confirmation Gate
(UNIT-004.2), and Validation API (UNIT-005.3 — accepted via the local
`ValidationApi` Protocol so this module never imports `vip_api_b`,
preserving the SEP-001 architectural separation between Class C and
Class B subsystems).

Realises SRS-IF-002 (external command interface) and SRS-010〜014
(start/stop/pause/resume/error_reset semantics). The 8 public methods
all return their result via `ApiResult` and never raise — every
unexpected exception is captured and surfaced as
`ApiRejected(InternalError.UNEXPECTED_EXCEPTION)` (SDD §4.15.E).

Step 19 B16 design judgments (recorded in DEVELOPMENT_STEPS.md):

* `Settings.model_dump()` converts pydantic to `Mapping[str, object]` so
  `Command(payload=...)` (whose contract is `Mapping[str, object] | None`)
  is satisfied without leaking pydantic into the Command Handler.
* `ValidationApi` is a `Protocol` (`validate_settings(settings) ->
  list[ValidationError]`) — UNIT-005.3 will satisfy it later via
  structural typing without breaking the SEP-001 import boundary.
* The `drug_name` field from SDD §4.15.B is intentionally NOT consumed
  here — Inc.1 `vip_persist.records.Settings` lacks it and the ripple
  through B6/B7 tests is deferred to Inc.4 UI work (B15 hand-off
  continued).
* `Confirmed` / `WrongToken` / `Expired` / `NotPending` are re-exported
  from `vip_integrity.resume_gate` rather than redefined: the gate's
  own value objects already model the same outcomes, so introducing
  parallel API-side classes would force a useless mapping layer.

Related SRS: SRS-IF-002, SRS-010〜014.
Related RCM: — (delegation only).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum, auto
from typing import TYPE_CHECKING, Protocol

from vip_ctrl.command_handler import (
    Accepted,
    Command,
    CommandKind,
)
from vip_integrity.resume_gate import (
    Confirmed,
    Expired,
    NotPending,
    WrongToken,
)

if TYPE_CHECKING:
    from vip_ctrl.command_handler import (
        CommandHandler,
        CompletionResult,
        RejectReason,
    )
    from vip_integrity.resume_gate import ResumeConfirmationGate
    from vip_persist.records import Settings

__all__ = [
    "ApiRejected",
    "ApiResult",
    "Confirmed",
    "ControlApi",
    "Expired",
    "InternalError",
    "NotPending",
    "Ok",
    "ValidationApi",
    "ValidationError",
    "ValidationFailed",
    "WrongToken",
]


_logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Internal-error reason (SDD §4.15.E "予期せぬ例外 → Rejected(INTERNAL_ERROR)")
# ---------------------------------------------------------------------------


class InternalError(Enum):
    """Reason carried by ApiRejected when an unexpected exception is caught."""

    UNEXPECTED_EXCEPTION = auto()


# ---------------------------------------------------------------------------
# Result value objects (SDD §4.15.A / §4.15.B)
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ValidationError:
    """A single semantic validation problem reported by `ValidationApi`."""

    field: str
    message: str


@dataclass(frozen=True, slots=True)
class Ok:
    """Successful command acceptance; carries the Command Handler token."""

    token: str


@dataclass(frozen=True, slots=True)
class ValidationFailed:
    """`start` rejected by `ValidationApi`. Carries every detected problem."""

    errors: list[ValidationError]


@dataclass(frozen=True, slots=True)
class ApiRejected:
    """Command Handler rejected (or unexpected internal exception caught)."""

    reason: RejectReason | InternalError


ApiResult = Ok | ValidationFailed | ApiRejected | Confirmed | WrongToken | Expired | NotPending


# ---------------------------------------------------------------------------
# Validation API protocol (UNIT-005.3 will satisfy it; tests Mock it)
# ---------------------------------------------------------------------------


class ValidationApi(Protocol):
    """Structural contract for the Class B Validation API (UNIT-005.3)."""

    def validate_settings(self, settings: Settings) -> list[ValidationError]:
        """Return zero or more semantic validation problems for `settings`."""
        ...


# ---------------------------------------------------------------------------
# Control API
# ---------------------------------------------------------------------------


class ControlApi:
    """Thin Facade publishing 7 commands + `await_command` (SDD §4.15)."""

    def __init__(
        self,
        *,
        command_handler: CommandHandler,
        resume_gate: ResumeConfirmationGate,
        validation_api: ValidationApi,
    ) -> None:
        """Inject the three delegated subsystems (Class C + Class B Validation)."""
        self._command_handler = command_handler
        self._resume_gate = resume_gate
        self._validation_api = validation_api

    # ---- start (settings + validation) ----

    def start(self, settings: Settings) -> ApiResult:
        """Validate settings then enqueue START. Never raises."""
        try:
            errors = self._validation_api.validate_settings(settings)
            if errors:
                return ValidationFailed(errors=list(errors))
            payload: dict[str, object] = dict(settings.model_dump())
            return self._enqueue(CommandKind.START, payload=payload)
        except Exception:
            _logger.exception("ControlApi.start: unexpected exception")
            return ApiRejected(reason=InternalError.UNEXPECTED_EXCEPTION)

    # ---- simple commands (no payload) ----

    def stop(self) -> ApiResult:
        """Enqueue STOP (Command Handler routes via STOP fast-path)."""
        return self._safe_enqueue(CommandKind.STOP)

    def pause(self) -> ApiResult:
        """Enqueue PAUSE."""
        return self._safe_enqueue(CommandKind.PAUSE)

    def resume(self) -> ApiResult:
        """Enqueue RESUME (Command Handler enforces State Machine pre-cond)."""
        return self._safe_enqueue(CommandKind.RESUME)

    def reset(self) -> ApiResult:
        """Enqueue RESET (valid only from STOPPED, Command Handler verifies)."""
        return self._safe_enqueue(CommandKind.RESET)

    def error_reset(self) -> ApiResult:
        """Enqueue ERROR_RESET (Command Handler routes via fast-path)."""
        return self._safe_enqueue(CommandKind.ERROR_RESET)

    # ---- resume confirmation (Resume Gate delegation) ----

    def confirm_resume(self, token: str) -> ApiResult:
        """Forward `token` to Resume Gate; map `Confirmed` to `Ok(token)`."""
        try:
            outcome = self._resume_gate.confirm(token)
        except Exception:
            _logger.exception("ControlApi.confirm_resume: unexpected exception")
            return ApiRejected(reason=InternalError.UNEXPECTED_EXCEPTION)
        if isinstance(outcome, Confirmed):
            return Ok(token=token)
        return outcome

    # ---- await (thin pass-through to Command Handler) ----

    def await_command(self, token: str, timeout_ms: int = 200) -> CompletionResult:
        """Pass-through to `CommandHandler.await_completion` (SDD §4.15.A)."""
        return self._command_handler.await_completion(token, timeout_ms=timeout_ms)

    # ---- internal helpers ----

    def _safe_enqueue(self, kind: CommandKind) -> ApiResult:
        try:
            return self._enqueue(kind, payload=None)
        except Exception:
            _logger.exception("ControlApi.%s: unexpected exception", kind.name.lower())
            return ApiRejected(reason=InternalError.UNEXPECTED_EXCEPTION)

    def _enqueue(self, kind: CommandKind, *, payload: dict[str, object] | None) -> ApiResult:
        cmd = Command(kind=kind, payload=payload)
        outcome = self._command_handler.enqueue(cmd)
        if isinstance(outcome, Accepted):
            return Ok(token=outcome.token)
        return ApiRejected(reason=outcome.reason)
