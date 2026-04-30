"""Resume confirmation gate (UNIT-004.2) per SDD-VIP-001 v0.2 §4.14.

Realises RCM-016 (resume confirmation, HZ-007 protective measure) and
SRS-028 (no auto-resume of interrupted infusions). The gate holds at most
one `PendingResume`, issues a 128-bit `secrets.token_hex(16)` confirmation
token, and forwards the operator-confirmed `CMD_RESUME` to the State
Machine via `request_transition`. SDD §4.14.C is the authoritative
reference; the implementation here is its line-by-line realisation.

Step 19 B15 design judgments (recorded in DEVELOPMENT_STEPS.md):

* `ResumeDetail` is defined inside this module (concern locality —
  Inc.1 has only one consumer; promotion to `vip_persist.records` is an
  Inc.4 task once the integrity-validator → resume-gate path is wired).
* `StateMachine` is constructor-injected; `_state_machine.request_transition`
  is invoked **outside** `_lock` to avoid potential deadlock if a future
  reverse path calls back into the gate (SDD §4.14 design judgment).
* `clock: Callable[[], float]` is constructor-injected (B4/B9 watchdog
  pattern) so UT can advance fake time past `EXPIRY_SEC` deterministically;
  default `time.monotonic` provides clock-rewind resistance.
* Token comparison uses `hmac.compare_digest` for constant-time matching
  to mitigate theoretical timing attacks on the token (SDD §4.14 design
  judgment).
* All value objects (`PendingResume`, `ResumeDetail`, `Confirmed`,
  `WrongToken`, `NotPending`, `Expired`) are `frozen=True, slots=True`
  (B11/B12/B13/B14 pattern); the frozen contract is exercised by
  UT-004.2-12.
* MC/DC 100% target — RCM-016 unit; every branch of `confirm` (not
  pending / wrong token / expired / ok), `set_pending` (already pending /
  fresh), and `check_expiry` (none / expired / fresh) is covered by
  UT-004.2-01 .. UT-004.2-15 design.

Related SRS: SRS-028, SRS-RCM-016.
Related RCM: RCM-016.
Related HZ:  HZ-007.
"""

from __future__ import annotations

import hmac
import logging
import secrets
import threading
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Final

from vip_ctrl.state_machine import EventKind, State, TransitionEvent

if TYPE_CHECKING:
    from collections.abc import Callable
    from decimal import Decimal

    from vip_ctrl.state_machine import StateMachine
    from vip_persist.records import Settings

__all__ = [
    "EXPIRY_SEC",
    "ConfirmResult",
    "Confirmed",
    "Expired",
    "NotPending",
    "PendingResume",
    "ResumeConfirmationGate",
    "ResumeDetail",
    "WrongToken",
]


EXPIRY_SEC: Final[int] = 3600
"""Pending-resume expiry per SDD §4.14 (60 minutes; SRS-028 operational reading)."""


_logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Value objects (SDD §4.14.A / §4.14.B)
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ResumeDetail:
    """Restored runtime context awaiting operator confirmation."""

    settings: Settings
    state: State
    accumulated_volume: Decimal


@dataclass(frozen=True, slots=True)
class PendingResume:
    """Single in-flight pending-resume record (SDD §4.14.B)."""

    token: str
    detail: ResumeDetail
    set_at: float
    set_at_wall: datetime


@dataclass(frozen=True, slots=True)
class Confirmed:
    """Result: operator-confirmed resume (SDD §4.14.A)."""

    detail: ResumeDetail


@dataclass(frozen=True, slots=True)
class WrongToken:
    """Result: token mismatch (constant-time compared)."""


@dataclass(frozen=True, slots=True)
class NotPending:
    """Result: confirm called when no pending resume exists."""


@dataclass(frozen=True, slots=True)
class Expired:
    """Result: pending older than `EXPIRY_SEC` at the moment of confirm."""


ConfirmResult = Confirmed | WrongToken | NotPending | Expired


# ---------------------------------------------------------------------------
# Gate
# ---------------------------------------------------------------------------


class ResumeConfirmationGate:
    """Resume confirmation gate (UNIT-004.2).

    Thread safety: a non-reentrant `threading.Lock` guards `_pending`. The
    `request_transition` call to the State Machine is performed outside
    the lock so a future reverse path cannot deadlock on `_lock`.
    """

    def __init__(
        self,
        *,
        state_machine: StateMachine,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        """Inject the State Machine and (optionally) a fake clock for UT."""
        self._state_machine = state_machine
        self._clock = clock
        self._lock = threading.Lock()
        self._pending: PendingResume | None = None

    # ---- queries ----

    def is_pending(self) -> bool:
        """Return whether a pending-resume token is currently issued."""
        with self._lock:
            return self._pending is not None

    def pending_detail(self) -> ResumeDetail | None:
        """Return the pending detail (read-only) or None."""
        with self._lock:
            return self._pending.detail if self._pending is not None else None

    # ---- mutating API ----

    def set_pending(self, detail: ResumeDetail) -> str:
        """Register a pending resume and return its 128-bit hex token."""
        with self._lock:
            if self._pending is not None:
                msg = "ResumeGate already pending"
                raise RuntimeError(msg)
            token = secrets.token_hex(16)
            self._pending = PendingResume(
                token=token,
                detail=detail,
                set_at=self._clock(),
                set_at_wall=datetime.now(UTC),
            )
        _logger.info(
            "resume_pending: state=%s accumulated=%s",
            detail.state.name,
            detail.accumulated_volume,
        )
        return token

    def confirm(self, token: str) -> ConfirmResult:
        """Validate `token` against the pending entry and forward CMD_RESUME."""
        with self._lock:
            pending = self._pending
            if pending is None:
                return NotPending()
            if not hmac.compare_digest(token, pending.token):
                return WrongToken()
            if (self._clock() - pending.set_at) > EXPIRY_SEC:
                self._pending = None
                _logger.warning(
                    "resume_expired: token age exceeded EXPIRY_SEC=%d",
                    EXPIRY_SEC,
                )
                return Expired()
            self._pending = None
        # Outside the lock — see module docstring (deadlock prevention).
        self._state_machine.request_transition(
            TransitionEvent(
                kind=EventKind.CMD_RESUME,
                timestamp=datetime.now(UTC),
                metadata={"resume_token": token},
            ),
        )
        return Confirmed(detail=pending.detail)

    def cancel(self) -> None:
        """Discard any pending resume; idempotent when none is pending."""
        with self._lock:
            self._pending = None

    def check_expiry(self) -> None:
        """Emit a warning when the pending resume has aged past EXPIRY_SEC."""
        with self._lock:
            pending = self._pending
            if pending is None:
                return
            if (self._clock() - pending.set_at) > EXPIRY_SEC:
                _logger.warning(
                    "resume_expiry_warning: pending older than EXPIRY_SEC=%d",
                    EXPIRY_SEC,
                )
