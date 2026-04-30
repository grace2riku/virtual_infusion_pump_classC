"""Command Handler (UNIT-001.3) per SDD-VIP-001 v0.2 §4.7.

Receives external commands (start/stop/pause/resume/reset/error_reset/
confirm_resume) from Control API (UNIT-005.1) and dispatches them to
the State Machine (UNIT-001.1) sequentially. STOP/ERROR_RESET commands
take a fast path that bypasses the FIFO queue so SRS-P04 (≤ 50 ms) can
be met even under load. Tokens identify each enqueued command for later
result retrieval via `await_completion`.

Step 19 B13 design judgments (recorded in DEVELOPMENT_STEPS.md):

* `Command` and `CommandKind` are owned by this module. UNIT-005.1
  Control API will import them in a later step.
* `_is_acceptable_in_state` consults `state_machine.TRANSITION_TABLE`
  directly so the state-machine table stays the single source of
  truth (DRY: no duplicated mapping).
* Command Handler treats `payload` as opaque; payload validation
  belongs to UNIT-005.1 Control API.
* SRS-P03/P04 statistical timing measurement is deferred to ITPR
  §5.6; this unit only exercises deterministic fast-path semantics
  under unit test (continuation of B4/B5/B8/B10 deferral pattern).

Related SRS: SRS-010, SRS-013, SRS-014, SRS-P03, SRS-P04.
Related RCM: — (collaborates with State Machine RCM-019).
Related HZ:  HZ-001, HZ-002.
"""

from __future__ import annotations

import logging
import queue
import threading
import time
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum, auto
from typing import TYPE_CHECKING, Final

from vip_ctrl.state_machine import (
    TRANSITION_TABLE,
    EventKind,
    TransitionEvent,
    TransitionOk,
)

if TYPE_CHECKING:
    from collections.abc import Mapping

    from vip_ctrl.state_machine import State, StateMachine

__all__ = [
    "MAX_QUEUE_SIZE",
    "STOP_KINDS",
    "AcceptResult",
    "Accepted",
    "Command",
    "CommandHandler",
    "CommandKind",
    "Completed",
    "CompletionResult",
    "Failed",
    "RejectReason",
    "Rejected",
    "SupersededByStopError",
    "TimedOut",
    "UnknownTokenError",
]


# ---------------------------------------------------------------------------
# Domain constants (SDD §4.7.B / §4.7.C)
# ---------------------------------------------------------------------------

MAX_QUEUE_SIZE: Final[int] = 16
_DISPATCH_GET_TIMEOUT_S: Final[float] = 0.05
_THREAD_JOIN_TIMEOUT: Final[float] = 2.0


# ---------------------------------------------------------------------------
# Domain enums
# ---------------------------------------------------------------------------


class CommandKind(Enum):
    """External command kinds (SRS-I-010). SDD §4.7.A."""

    START = auto()
    STOP = auto()
    PAUSE = auto()
    RESUME = auto()
    RESET = auto()
    ERROR_RESET = auto()
    CONFIRM_RESUME = auto()


STOP_KINDS: Final[frozenset[CommandKind]] = frozenset(
    {CommandKind.STOP, CommandKind.ERROR_RESET},
)


class RejectReason(Enum):
    """Why an enqueue was rejected. SDD §4.7.E."""

    INVALID_FOR_CURRENT_STATE = auto()
    QUEUE_FULL = auto()


# ---------------------------------------------------------------------------
# Value objects
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Command:
    """Immutable command request. Payload is opaque to this unit."""

    kind: CommandKind
    payload: Mapping[str, object] | None = None


@dataclass(frozen=True, slots=True)
class _CommandTask:
    """Internal task wrapper assigned a unique token at enqueue time."""

    token: str
    cmd: Command
    enqueued_at: float


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Accepted:
    """Successful enqueue. Carries the unique command token."""

    token: str


@dataclass(frozen=True, slots=True)
class Rejected:
    """Failed enqueue with a structured rejection reason."""

    reason: RejectReason


AcceptResult = Accepted | Rejected


@dataclass(frozen=True, slots=True)
class Completed:
    """Command completed successfully and the State Machine transitioned."""

    state: State


@dataclass(frozen=True, slots=True)
class TimedOut:
    """`await_completion` exceeded its timeout window."""

    elapsed_ms: int


@dataclass(frozen=True, slots=True)
class Failed:
    """Command failed; carries the underlying error."""

    error: Exception = field()


CompletionResult = Completed | TimedOut | Failed


# ---------------------------------------------------------------------------
# Custom errors (SDD §4.7.E)
# ---------------------------------------------------------------------------


class SupersededByStopError(Exception):
    """Raised on tasks discarded by a STOP/ERROR_RESET fast path."""


class UnknownTokenError(Exception):
    """Raised when `await_completion` receives a token that was never enqueued."""

    def __init__(self, token: str) -> None:
        """Capture the offending token for diagnostics."""
        super().__init__(f"Unknown token: {token}")
        self.token = token


# ---------------------------------------------------------------------------
# Command -> EventKind mapping
# ---------------------------------------------------------------------------


_CMD_TO_EVENT: Final[dict[CommandKind, EventKind]] = {
    CommandKind.START: EventKind.CMD_START,
    CommandKind.STOP: EventKind.CMD_STOP,
    CommandKind.PAUSE: EventKind.CMD_PAUSE,
    CommandKind.RESUME: EventKind.CMD_RESUME,
    CommandKind.RESET: EventKind.CMD_RESET,
    CommandKind.ERROR_RESET: EventKind.CMD_ERROR_RESET,
}


# ---------------------------------------------------------------------------
# CommandHandler
# ---------------------------------------------------------------------------


_logger = logging.getLogger(__name__)


class CommandHandler:
    """Sequentially dispatches external commands to the State Machine."""

    def __init__(self, *, state_machine: StateMachine) -> None:
        """Wire up the State Machine; the dispatch thread is not yet started."""
        self._state_machine = state_machine
        self._queue: queue.Queue[_CommandTask] = queue.Queue(maxsize=MAX_QUEUE_SIZE)
        self._pending_stop: _CommandTask | None = None
        self._completions: dict[str, threading.Event] = {}
        self._results: dict[str, CompletionResult] = {}
        self._lock = threading.Lock()
        self._wake_event = threading.Event()
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    # ------------------------------------------------------------------
    # Public API (SDD §4.7.A)
    # ------------------------------------------------------------------

    def enqueue(self, cmd: Command) -> AcceptResult:
        """Enqueue a command. STOP/ERROR_RESET take a fast path."""
        if not self._is_acceptable_in_state(cmd):
            return Rejected(RejectReason.INVALID_FOR_CURRENT_STATE)
        task = _CommandTask(
            token=str(uuid.uuid4()),
            cmd=cmd,
            enqueued_at=time.monotonic(),
        )
        if cmd.kind in STOP_KINDS:
            self._enqueue_fast_path(task)
            return Accepted(task.token)
        try:
            self._queue.put_nowait(task)
        except queue.Full:
            return Rejected(RejectReason.QUEUE_FULL)
        with self._lock:
            self._completions[task.token] = threading.Event()
        return Accepted(task.token)

    def await_completion(self, token: str, *, timeout_ms: int) -> CompletionResult:
        """Wait up to `timeout_ms` for the command identified by `token`.

        Removes the result+event pair on retrieval; subsequent calls with the
        same token return `Failed(UnknownTokenError(...))`.
        """
        with self._lock:
            ev = self._completions.get(token)
        if ev is None:
            return Failed(UnknownTokenError(token))
        if not ev.wait(timeout_ms / 1000.0):
            return TimedOut(elapsed_ms=timeout_ms)
        with self._lock:
            self._completions.pop(token, None)
            return self._results.pop(token, Failed(UnknownTokenError(token)))

    def is_running(self) -> bool:
        """Return True while the dispatch thread is alive."""
        with self._lock:
            t = self._thread
        return t is not None and t.is_alive()

    def start(self) -> None:
        """Launch the dispatch thread; raises if already started."""
        with self._lock:
            if self._thread is not None and self._thread.is_alive():
                msg = "CommandHandler already started"
                raise RuntimeError(msg)
            self._stop_event.clear()
            self._thread = threading.Thread(
                target=self._dispatch_loop,
                name="CommandHandler",
                daemon=True,
            )
            self._thread.start()

    def stop(self) -> None:
        """Signal the dispatch thread to stop and join it (no-op if not running)."""
        with self._lock:
            t = self._thread
        if t is None:
            return
        self._stop_event.set()
        self._wake_event.set()  # 起こして即座にループ終了させる
        t.join(timeout=_THREAD_JOIN_TIMEOUT)
        with self._lock:
            self._thread = None

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _is_acceptable_in_state(self, cmd: Command) -> bool:
        """Return True when (current_state, mapped EventKind) is in the table."""
        event_kind = _CMD_TO_EVENT.get(cmd.kind)
        if event_kind is None:
            return False
        return (self._state_machine.current(), event_kind) in TRANSITION_TABLE

    def _enqueue_fast_path(self, task: _CommandTask) -> None:
        """Stash STOP/ERROR_RESET task and discard everything in the queue."""
        with self._lock:
            self._pending_stop = task
            self._completions[task.token] = threading.Event()
            while not self._queue.empty():
                try:
                    discarded = self._queue.get_nowait()
                except queue.Empty:  # pragma: no cover -- race-window guard
                    break
                self._results[discarded.token] = Failed(SupersededByStopError())
                ev = self._completions.get(discarded.token)
                if ev is not None:  # pragma: no branch -- enqueue always sets event
                    ev.set()
        self._wake_event.set()

    def _dispatch_loop(self) -> None:
        while not self._stop_event.is_set():
            with self._lock:
                stop_task = self._pending_stop
                self._pending_stop = None
            if stop_task is not None:
                self._handle(stop_task)
                continue
            try:
                task = self._queue.get(timeout=_DISPATCH_GET_TIMEOUT_S)
            except queue.Empty:
                self._wake_event.wait(timeout=0.0)
                self._wake_event.clear()
                continue
            self._handle(task)

    def _handle(self, task: _CommandTask) -> None:
        """Translate command → transition event and record the completion."""
        completion: CompletionResult
        try:
            event_kind = _CMD_TO_EVENT[task.cmd.kind]
            event = TransitionEvent(kind=event_kind, timestamp=datetime.now(UTC))
            result = self._state_machine.request_transition(event)
            if isinstance(result, TransitionOk):
                completion = Completed(state=result.new_state)
            else:  # pragma: no cover -- guarded earlier by _is_acceptable_in_state
                completion = Failed(error=result.error)
        except Exception as exc:
            _logger.exception("dispatch task raised; recording Failed")
            completion = Failed(error=exc)
        with self._lock:
            self._results[task.token] = completion
            ev = self._completions.get(task.token)
        if ev is not None:  # pragma: no branch -- enqueue always sets event
            ev.set()
