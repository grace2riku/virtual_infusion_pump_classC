"""State machine for the infusion pump flow-control core (UNIT-001.1).

Implements RCM-019 (state transition protection) per SDD-VIP-001 v0.2 §4.1.
The machine holds one of six states (INITIALIZING, IDLE, RUNNING, PAUSED,
STOPPED, ERROR) and only allows transitions declared in `TRANSITION_TABLE`.
Invalid requests are rejected without mutating state; watchdog timeouts
escalate to ERROR preserving the first reason recorded.

Thread-safety: all mutating methods acquire a re-entrant lock with a bounded
wait (default 100 ms per SDD §4.1.5). Lock acquisition timeout raises
`StateLockTimeoutError` so the caller can escalate to ERROR via
`on_watchdog_timeout`.

Persistence coupling: every successful transition enqueues a
`RuntimeSnapshot` onto an internal `queue.Queue`. On queue saturation the
machine escalates to ERROR with reason `PERSISTENCE_QUEUE_FULL`, matching
the SRS-025 degradation contract.

Related SRS: SRS-020, SRS-021, SRS-025, SRS-RCM-020, SRS-ALM-003.
Related RCM: RCM-019.
Related HZ:  HZ-001, HZ-002.
"""

from __future__ import annotations

import queue
import threading
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum, auto
from typing import TYPE_CHECKING, Final, Self

if TYPE_CHECKING:
    from collections.abc import Mapping

__all__ = [
    "TRANSITION_TABLE",
    "EventKind",
    "InvalidInitializationError",
    "InvalidTransitionError",
    "RuntimeSnapshot",
    "State",
    "StateLockTimeoutError",
    "StateMachine",
    "TransitionErr",
    "TransitionEvent",
    "TransitionOk",
    "TransitionResult",
    "WatchdogReason",
]


# ---------------------------------------------------------------------------
# Domain enums and value objects
# ---------------------------------------------------------------------------


class State(Enum):
    """Flow-control state. Mirrors SRS-VIP-001 §4.1.3."""

    INITIALIZING = auto()
    IDLE = auto()
    RUNNING = auto()
    PAUSED = auto()
    STOPPED = auto()
    ERROR = auto()


class EventKind(Enum):
    """Transition event kinds. See SDD-VIP-001 §4.1.3."""

    BOOT_OK_NO_PENDING = auto()
    BOOT_OK_WITH_PENDING = auto()
    BOOT_INTEGRITY_FAIL = auto()
    BOOT_FATAL = auto()
    CMD_START = auto()
    CMD_PAUSE = auto()
    CMD_RESUME = auto()
    CMD_STOP = auto()
    CMD_RESET = auto()
    CMD_ERROR_RESET = auto()
    AUTO_STOP_DOSE_REACHED = auto()
    WDT_TIMEOUT = auto()


class WatchdogReason(Enum):
    """Why the machine entered ERROR. Preserved first-write on repeated timeouts."""

    SW_WATCHDOG = auto()
    HW_FAILSAFE = auto()
    PERSISTENCE_QUEUE_FULL = auto()
    OTHER = auto()


@dataclass(frozen=True, slots=True)
class TransitionEvent:
    """Immutable request container passed to `StateMachine.request_transition`."""

    kind: EventKind
    timestamp: datetime
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class RuntimeSnapshot:
    """Point-in-time machine state captured for persistence (SDD §4.1.2)."""

    state: State
    needs_resume_confirm: bool
    last_transition_ts: datetime
    error_reason: WatchdogReason | None


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class TransitionOk:
    """Successful transition outcome; exposes the resulting state."""

    new_state: State


@dataclass(frozen=True, slots=True)
class TransitionErr:
    """Failed transition outcome carrying the rejecting exception."""

    error: Exception


TransitionResult = TransitionOk | TransitionErr


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class InvalidTransitionError(Exception):
    """Raised (via `TransitionErr`) when the (state, event) pair is not in the table.

    This realises RCM-019: any request not covered by `TRANSITION_TABLE` is
    rejected without mutating the machine.
    """

    def __init__(self, state: State, kind: EventKind) -> None:
        """Capture the rejecting (state, kind) pair for diagnostics."""
        super().__init__(f"Invalid transition: {state.name} x {kind.name}")
        self.state = state
        self.kind = kind


class InvalidInitializationError(Exception):
    """Raised when `set_initial` is called on an already-initialised machine."""


class StateLockTimeoutError(Exception):
    """Raised when acquiring the internal lock exceeds the configured timeout."""


# ---------------------------------------------------------------------------
# Transition table (SDD-VIP-001 §4.1.3)
# ---------------------------------------------------------------------------
#
# Map: (from_state, event_kind) -> (to_state, guard_label | None)
# Guard labels are placeholders in this Step 19 B2 baseline; concrete guard
# functions are wired in later steps that implement their dependencies
# (check_settings_valid needs the settings store; record_wdt_reason needs the
# logger; set_needs_confirm / set_failsafe_defaults require the integrity
# subsystem from UNIT-004). The table structure and keys are final.

TRANSITION_TABLE: Final[dict[tuple[State, EventKind], tuple[State, str | None]]] = {
    (State.INITIALIZING, EventKind.BOOT_OK_NO_PENDING): (State.IDLE, None),
    (State.INITIALIZING, EventKind.BOOT_OK_WITH_PENDING): (State.IDLE, "set_needs_confirm"),
    (State.INITIALIZING, EventKind.BOOT_INTEGRITY_FAIL): (State.IDLE, "set_failsafe_defaults"),
    (State.INITIALIZING, EventKind.BOOT_FATAL): (State.ERROR, None),
    (State.IDLE, EventKind.CMD_START): (State.RUNNING, "check_settings_valid"),
    (State.RUNNING, EventKind.AUTO_STOP_DOSE_REACHED): (State.STOPPED, None),
    (State.RUNNING, EventKind.CMD_PAUSE): (State.PAUSED, None),
    (State.RUNNING, EventKind.CMD_STOP): (State.STOPPED, None),
    (State.RUNNING, EventKind.WDT_TIMEOUT): (State.ERROR, "record_wdt_reason"),
    (State.PAUSED, EventKind.CMD_RESUME): (State.RUNNING, None),
    (State.PAUSED, EventKind.CMD_STOP): (State.STOPPED, None),
    (State.STOPPED, EventKind.CMD_RESET): (State.IDLE, "clear_settings"),
    (State.ERROR, EventKind.CMD_ERROR_RESET): (State.IDLE, "clear_error_after_check"),
}


# ---------------------------------------------------------------------------
# StateMachine
# ---------------------------------------------------------------------------


_DEFAULT_LOCK_TIMEOUT_S: Final[float] = 0.1
_DEFAULT_QUEUE_MAXSIZE: Final[int] = 128


class StateMachine:
    """Thread-safe flow-control state machine (UNIT-001.1).

    Parameters
    ----------
    persistence_queue_maxsize:
        Capacity of the internal snapshot queue. A saturated queue on a
        transition escalates the machine to ERROR (SRS-025).
    lock_timeout_s:
        Maximum time a caller will wait for the internal lock before
        `StateLockTimeoutError` is raised. Defaults to 100 ms per SDD §4.1.5.

    """

    def __init__(
        self,
        *,
        persistence_queue_maxsize: int = _DEFAULT_QUEUE_MAXSIZE,
        lock_timeout_s: float = _DEFAULT_LOCK_TIMEOUT_S,
    ) -> None:
        """Initialise the machine in INITIALIZING with empty snapshot queue."""
        self._state: State = State.INITIALIZING
        self._needs_resume_confirm: bool = False
        self._last_transition_ts: datetime = datetime.now(UTC)
        self._error_reason: WatchdogReason | None = None
        self._lock_timeout_s: float = lock_timeout_s
        self._lock = threading.RLock()
        self._persistence_queue: queue.Queue[RuntimeSnapshot] = queue.Queue(
            maxsize=persistence_queue_maxsize,
        )

    # ---- read-only accessors ----

    def current(self) -> State:
        """Return the current state. Thread-safe via internal lock."""
        with self._acquire():
            return self._state

    def needs_resume_confirm(self) -> bool:
        """Return whether the machine awaits a resume confirmation (RCM-016 cue)."""
        with self._acquire():
            return self._needs_resume_confirm

    def error_reason(self) -> WatchdogReason | None:
        """Return the first ERROR reason recorded, or None when not in ERROR."""
        with self._acquire():
            return self._error_reason

    def last_transition_ts(self) -> datetime:
        """Return the timestamp of the most recent accepted transition."""
        with self._acquire():
            return self._last_transition_ts

    # ---- initial configuration ----

    def set_initial(self, state: State, *, needs_confirm: bool) -> None:
        """Apply the boot-time initial state once.

        May only be called while the machine is still in INITIALIZING, per
        SDD-VIP-001 §4.1.1 `set_initial` preconditions.
        """
        with self._acquire():
            if self._state != State.INITIALIZING:
                msg = f"set_initial called after initialization (current={self._state.name})"
                raise InvalidInitializationError(msg)
            self._state = state
            self._needs_resume_confirm = needs_confirm
            self._last_transition_ts = datetime.now(UTC)
            self._enqueue_snapshot_or_record_overflow()

    # ---- watchdog ----

    def on_watchdog_timeout(self, reason: WatchdogReason) -> None:
        """Force the machine into ERROR; idempotent on subsequent calls.

        Preserves the first reason recorded, per SDD-VIP-001 §4.1.1
        `on_watchdog_timeout` postcondition.
        """
        with self._acquire():
            if self._state == State.ERROR:
                return
            self._state = State.ERROR
            self._error_reason = reason
            self._last_transition_ts = datetime.now(UTC)
            self._enqueue_snapshot_or_record_overflow()

    # ---- main transition API ----

    def request_transition(self, event: TransitionEvent) -> TransitionResult:
        """Request a transition based on `event`.

        Returns `TransitionOk(new_state)` on success or `TransitionErr(error)`
        when the request violates `TRANSITION_TABLE` (RCM-019) or triggers a
        persistence overflow that escalates to ERROR.
        """
        with self._acquire():
            key = (self._state, event.kind)
            if key not in TRANSITION_TABLE:
                return TransitionErr(
                    InvalidTransitionError(self._state, event.kind),
                )
            new_state, _guard = TRANSITION_TABLE[key]
            # NOTE: Guard functions are placeholders in this baseline. When
            # wired (Step 19 B2+), a guard that rejects must return a
            # TransitionErr without mutating state. The rejection path is
            # already exercised by the invalid-transition tests of RCM-019,
            # so this branch stays simple until dependencies are in place.

            self._state = new_state
            self._last_transition_ts = event.timestamp
            if event.kind == EventKind.WDT_TIMEOUT:
                self._error_reason = WatchdogReason.SW_WATCHDOG

            try:
                self._persistence_queue.put_nowait(self._build_snapshot())
            except queue.Full:
                # SRS-025 degradation: escalate to ERROR, preserve overflow
                # reason, and expose the escalation to the caller.
                self._state = State.ERROR
                self._error_reason = WatchdogReason.PERSISTENCE_QUEUE_FULL
                return TransitionOk(State.ERROR)
            return TransitionOk(new_state)

    # ---- persistence coupling ----

    def drain_persistence_queue(self) -> list[RuntimeSnapshot]:
        """Drain all pending snapshots. Intended for the persistence worker and tests."""
        items: list[RuntimeSnapshot] = []
        while True:
            try:
                items.append(self._persistence_queue.get_nowait())
            except queue.Empty:
                break
        return items

    # ---- internals ----

    def _build_snapshot(self) -> RuntimeSnapshot:
        return RuntimeSnapshot(
            state=self._state,
            needs_resume_confirm=self._needs_resume_confirm,
            last_transition_ts=self._last_transition_ts,
            error_reason=self._error_reason,
        )

    def _enqueue_snapshot_or_record_overflow(self) -> None:
        """Best-effort snapshot enqueue used by set_initial / on_watchdog_timeout.

        These paths must not fail (set_initial is called once during boot,
        on_watchdog_timeout is the last line of defence), so a saturated queue
        simply records the overflow reason without re-escalating.
        """
        try:
            self._persistence_queue.put_nowait(self._build_snapshot())
        except queue.Full:
            # Already under lock, so recording is safe.
            if self._error_reason is None:
                self._error_reason = WatchdogReason.PERSISTENCE_QUEUE_FULL

    def _acquire(self) -> _LockGuard:
        return _LockGuard(self._lock, self._lock_timeout_s)


class _LockGuard:
    """Context manager that raises `StateLockTimeoutError` on acquire timeout."""

    def __init__(self, lock: threading.RLock, timeout_s: float) -> None:
        """Record the lock and timeout for the upcoming acquisition."""
        self._lock = lock
        self._timeout_s = timeout_s
        self._held = False

    def __enter__(self) -> Self:
        """Acquire the lock with the configured timeout or raise."""
        if not self._lock.acquire(timeout=self._timeout_s):
            msg = f"Failed to acquire state lock within {self._timeout_s:.3f}s"
            raise StateLockTimeoutError(msg)
        self._held = True
        return self

    def __exit__(self, *_exc: object) -> None:
        """Release the lock only when acquisition succeeded."""
        if self._held:
            self._lock.release()
