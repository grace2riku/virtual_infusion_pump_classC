"""Control loop (UNIT-001.2) per SDD-VIP-001 v0.2 §4.6.

Implements RCM-004 SW-side: a 100 ms-period (SRS-P02) loop that
dispatches heartbeats to both watchdog layers, validates and forwards
flow commands to the pump, and emits AUTO_STOP_DOSE_REACHED events
when the dose threshold is met (SRS-012, SRS-031).

Step 19 B10 design judgments (recorded in DEVELOPMENT_STEPS.md):

* `clock` is injectable so deterministic tests can drive time without
  patching `time.monotonic` globally (B4/B9 pattern).
* `tick()` is exposed as a test-friendly single-tick entry point that
  bypasses the scheduling thread (B4/B9 `check_once` pattern).
* `WatchdogReason.OTHER` is used to escalate control-loop exceptions;
  the SDD §4.6.C pseudocode name `CONTROL_LOOP_EXCEPTION` is treated
  as informative because state_machine.py's enum is fixed in B2.
* `EventKind.AUTO_STOP_DURATION_REACHED` (SDD §4.6.C pseudocode) is
  intentionally not implemented — SRS-012/031 only mandate dose-based
  auto-stop. Adding a duration branch is deferred to a future CR.
* SRS-P02 ±10% real-time period jitter testing is deferred to
  ITPR §5.6 (B4/B5/B8 申し送り pattern continuation).
* Logger plumbing via `logging.getLogger(__name__)` (no `_logger`
  field per SDD §4.6.B; matches B4/B9 deferral).

Related SRS: SRS-011, SRS-012, SRS-031, SRS-P02, SRS-RCM-004.
Related RCM: RCM-004 (SW dispatch side).
Related HZ:  HZ-001, HZ-002.
"""

from __future__ import annotations

import logging
import threading
import time
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Final, Protocol

from vip_ctrl.flow_validator import (
    ControlContext,
    FlowCommand,
    ValidationOk,
    validate,
)
from vip_ctrl.flow_validator import (
    Settings as ValidatorSettings,
)
from vip_ctrl.state_machine import (
    EventKind,
    State,
    TransitionEvent,
    WatchdogReason,
)

if TYPE_CHECKING:
    from collections.abc import Callable
    from decimal import Decimal

    from vip_ctrl.state_machine import StateMachine
    from vip_persist.records import Settings as RecordSettings

__all__ = [
    "PERIOD_SEC",
    "PERIOD_TOLERANCE",
    "ControlLoop",
    "PumpFlowController",
    "PumpSnapshot",
    "PumpSnapshotObserver",
]


# ---------------------------------------------------------------------------
# Domain constants (SDD §4.6.C)
# ---------------------------------------------------------------------------

PERIOD_SEC: Final[float] = 0.1
PERIOD_TOLERANCE: Final[float] = 0.1  # ±10% (SRS-P02)
_THREAD_JOIN_TIMEOUT: Final[float] = 2.0


# ---------------------------------------------------------------------------
# Collaborator protocols
# ---------------------------------------------------------------------------


class PumpSnapshot(Protocol):
    """Read-only pump-state view consumed by the control loop (SRS-031).

    UNIT-002.2 Pump Observer (a future TDD step) will produce concrete
    instances; for now only the attributes needed by `_tick` are listed.
    """

    @property
    def accumulated_volume(self) -> Decimal:
        """Total volume infused so far (mL)."""

    @property
    def elapsed_min(self) -> Decimal:
        """Minutes since the most recent infusion start."""

    @property
    def current_flow(self) -> Decimal:
        """Current flow rate (mL/h)."""


class PumpFlowController(Protocol):
    """Subset of the pump API used by the control loop's command path."""

    def set_flow_rate(self, value: Decimal) -> None:
        """Forward a validated flow command to the pump."""


class PumpSnapshotObserver(Protocol):
    """Subset of the pump observer used by the control loop's auto-stop path."""

    def observe(self) -> PumpSnapshot:
        """Return an immutable snapshot of the pump state."""


# ---------------------------------------------------------------------------
# Watchdog protocol (heartbeat sink)
# ---------------------------------------------------------------------------


class _HeartbeatSink(Protocol):
    """Both SW and HW watchdogs accept `heartbeat(ts)` (SDD IF-U-010/011)."""

    def heartbeat(self, ts: float) -> None:
        """Refresh the watchdog's last-heartbeat timestamp."""


# ---------------------------------------------------------------------------
# ControlLoop
# ---------------------------------------------------------------------------


_logger = logging.getLogger(__name__)


class ControlLoop:
    """100 ms-period control loop (UNIT-001.2).

    Threading model: a single periodic thread (started via `start`) ticks
    at `period_sec` and calls `tick()`. Tests typically bypass the thread
    by calling `tick` directly with an injected fake clock.
    """

    def __init__(  # noqa: PLR0913 — collaborators are mandatory per SDD §4.6.B
        self,
        *,
        state_machine: StateMachine,
        pump: PumpFlowController,
        observer: PumpSnapshotObserver,
        sw_watchdog: _HeartbeatSink,
        hw_watchdog: _HeartbeatSink,
        settings_provider: Callable[[], RecordSettings],
        clock: Callable[[], float] | None = None,
        period_sec: float = PERIOD_SEC,
    ) -> None:
        """Wire up dependencies; construction does not start the periodic thread."""
        self._state_machine = state_machine
        self._pump = pump
        self._observer = observer
        self._sw_watchdog = sw_watchdog
        self._hw_watchdog = hw_watchdog
        self._settings_provider = settings_provider
        self._clock = clock if clock is not None else time.monotonic
        self._period_sec = period_sec
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    # ------------------------------------------------------------------
    # Public API (SDD §4.6.A)
    # ------------------------------------------------------------------

    def is_running(self) -> bool:
        """Return True while the periodic thread is alive."""
        with self._lock:
            t = self._thread
        return t is not None and t.is_alive()

    def start(self) -> None:
        """Launch the periodic thread; raises if already started."""
        with self._lock:
            if self._thread is not None and self._thread.is_alive():
                msg = "ControlLoop already started"
                raise RuntimeError(msg)
            self._stop_event.clear()
            self._thread = threading.Thread(
                target=self._loop,
                name="ControlLoop",
                daemon=True,
            )
            self._thread.start()

    def stop(self) -> None:
        """Signal the periodic thread to exit and join it (no-op if not running)."""
        with self._lock:
            t = self._thread
        if t is None:
            return
        self._stop_event.set()
        t.join(timeout=_THREAD_JOIN_TIMEOUT)
        with self._lock:
            self._thread = None

    # ------------------------------------------------------------------
    # Test-friendly single tick (SDD §4.6.C `_tick`)
    # ------------------------------------------------------------------

    def tick(self) -> bool:
        """Execute a single tick of the control loop.

        Returns True if the tick performed RUNNING-state work, False when
        skipped because the State Machine is not in RUNNING.
        """
        if self._state_machine.current() is not State.RUNNING:
            return False

        now = self._clock()
        # 1. Heartbeat both watchdogs FIRST so a downstream exception still
        # records "alive" (SDD §4.6 keypoint).
        self._sw_watchdog.heartbeat(now)
        self._hw_watchdog.heartbeat(now)

        # 2-4. Run the rest of the tick under exception guard.
        try:
            self._dispatch_command_and_check_auto_stop(now)
        except Exception:
            _logger.exception("control loop tick raised; escalating to ERROR")
            self._state_machine.on_watchdog_timeout(WatchdogReason.OTHER)
        return True

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _dispatch_command_and_check_auto_stop(self, now: float) -> None:
        settings = self._settings_provider()
        cmd = FlowCommand(flow_rate=settings.flow_rate, timestamp=datetime.now(UTC))
        context = ControlContext(
            current_settings=ValidatorSettings(flow_rate=settings.flow_rate),
            current_state=State.RUNNING,
        )
        result = validate(cmd, context)
        if not isinstance(result, ValidationOk):
            # Validator rejected the command — escalate via WDT_TIMEOUT,
            # matching SDD §4.6.C pseudocode "WDT_TIMEOUT with reason".
            self._state_machine.request_transition(
                TransitionEvent(
                    kind=EventKind.WDT_TIMEOUT,
                    timestamp=datetime.now(UTC),
                    metadata={
                        "reason": "validation_failed",
                        "detail": result.reason.name,
                        "tick_clock": now,
                    },
                ),
            )
            return
        self._pump.set_flow_rate(result.validated.flow_rate)

        # Auto-stop check (SRS-012, SRS-031). Duration-based stop is
        # intentionally omitted (no SRS backing; deferred to future CR).
        snap = self._observer.observe()
        if snap.accumulated_volume >= settings.dose_volume:
            self._state_machine.request_transition(
                TransitionEvent(
                    kind=EventKind.AUTO_STOP_DOSE_REACHED,
                    timestamp=datetime.now(UTC),
                ),
            )

    def _loop(self) -> None:
        next_deadline = self._clock() + self._period_sec
        while not self._stop_event.is_set():
            self.tick()
            sleep_sec = next_deadline - self._clock()
            if sleep_sec > 0:
                self._stop_event.wait(sleep_sec)
            else:
                _logger.warning(
                    "control loop overrun: %.4f s past deadline",
                    -sleep_sec,
                )
            next_deadline += self._period_sec
