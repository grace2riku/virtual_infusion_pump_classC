"""SW-side watchdog (UNIT-001.5) per SDD-VIP-001 v0.2 §4.8.

Implements RCM-003 SW-side: a watchdog owned by the controller that
monitors heartbeats from the Control Loop (UNIT-001.2) and escalates
the State Machine (UNIT-001.1) to ERROR when heartbeats stall beyond
HEARTBEAT_TIMEOUT (300 ms). Independent of the HW failsafe timer
(UNIT-002.4, 500 ms) so a single control-loop failure cannot disable
both layers; by design the SW side trips first (300 < 500) to drive
ERROR state and block further commands, while the HW side acts as
the last-resort physical stop.

Step 19 B9 design judgments (recorded in DEVELOPMENT_STEPS.md):

* `clock` is injectable so deterministic tests can drive time without
  patching `time.monotonic` globally. Production callers pass nothing
  and get `time.monotonic`.
* The SW watchdog identifier is carried by
  `WatchdogReason.SW_WATCHDOG` (existing enum in
  `vip_ctrl.state_machine`); the SDD §4.8.C pseudocode name
  `SW_HEARTBEAT_TIMEOUT` is treated as informative — we keep the
  state_machine enum untouched (B7/B8 "add-only, existing artefacts
  unchanged" principle).
* Clock regression (`now < last`) is treated as a safety-side trip
  even though SDD §4.8 notes monotonic time; the injected clock may
  regress under faults, and RCM-003 demands fail-safe.
* State Machine exceptions during escalation are swallowed (logged)
  so the monitor thread survives and the trip flag still flips —
  subsequent ticks are then idempotent (SDD §4.8.E).
* Logger plumbing is deferred — an explicit `_logger` field is not
  declared in SDD §4.8.B, matching B4's decision for the HW side.

Related SRS: SRS-RCM-003.
Related RCM: RCM-003 (SW side).
Related HZ:  HZ-001, HZ-002.
"""

from __future__ import annotations

import logging
import threading
import time
from typing import TYPE_CHECKING, Final, Protocol

from vip_ctrl.state_machine import WatchdogReason

if TYPE_CHECKING:
    from collections.abc import Callable

__all__ = [
    "HEARTBEAT_TIMEOUT",
    "MONITOR_INTERVAL",
    "StateMachineLike",
    "SwWatchdog",
]


# ---------------------------------------------------------------------------
# Domain constants (SDD §4.8.C)
# ---------------------------------------------------------------------------

HEARTBEAT_TIMEOUT: Final[float] = 0.3
MONITOR_INTERVAL: Final[float] = 0.05
_THREAD_JOIN_TIMEOUT: Final[float] = 2.0


# ---------------------------------------------------------------------------
# Collaborator protocol
# ---------------------------------------------------------------------------


class StateMachineLike(Protocol):
    """Subset of the State Machine API the watchdog calls on trip."""

    def on_watchdog_timeout(self, reason: WatchdogReason) -> None:
        """Escalate to ERROR with the given reason; expected to be idempotent."""


# ---------------------------------------------------------------------------
# Watchdog
# ---------------------------------------------------------------------------


_logger = logging.getLogger(__name__)


class SwWatchdog:
    """Controller-side heartbeat watchdog (RCM-003 SW redundant layer).

    Threading model: a single monitor thread (started via `start`) ticks at
    `monitor_interval` and calls `state_machine.on_watchdog_timeout` when the
    gap since the last heartbeat exceeds `timeout`. All shared state is
    guarded by an internal `Lock`. Tests typically bypass the thread by
    calling `check_once` directly with an injected fake clock.
    """

    def __init__(
        self,
        state_machine: StateMachineLike,
        *,
        clock: Callable[[], float] | None = None,
        timeout: float = HEARTBEAT_TIMEOUT,
        monitor_interval: float = MONITOR_INTERVAL,
    ) -> None:
        """Wire up dependencies; construction does not start the monitor thread."""
        self._state_machine = state_machine
        self._clock = clock if clock is not None else time.monotonic
        self._timeout = timeout
        self._monitor_interval = monitor_interval
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._last_heartbeat: float = self._clock()
        self._tripped: bool = False

    # ------------------------------------------------------------------
    # Public API (SDD §4.8.A)
    # ------------------------------------------------------------------

    def heartbeat(self) -> None:
        """Refresh the last-heartbeat timestamp (no-op once tripped)."""
        ts = self._clock()
        with self._lock:
            if not self._tripped:
                self._last_heartbeat = ts

    def is_tripped(self) -> bool:
        """Return True once the watchdog has fired."""
        with self._lock:
            return self._tripped

    def is_running(self) -> bool:
        """Return True while the monitor thread is alive."""
        with self._lock:
            t = self._thread
        return t is not None and t.is_alive()

    def last_heartbeat(self) -> float:
        """Return the most recently recorded heartbeat timestamp."""
        with self._lock:
            return self._last_heartbeat

    def start(self) -> None:
        """Launch the monitor thread; raises if already started."""
        with self._lock:
            if self._thread is not None and self._thread.is_alive():
                msg = "SwWatchdog already started"
                raise RuntimeError(msg)
            self._stop_event.clear()
            self._last_heartbeat = self._clock()
            self._thread = threading.Thread(
                target=self._monitor_loop,
                name="SwWatchdog",
                daemon=True,
            )
            self._thread.start()

    def stop(self) -> None:
        """Signal the monitor thread to exit and join it (no-op if not running)."""
        with self._lock:
            t = self._thread
        if t is None:
            return
        self._stop_event.set()
        t.join(timeout=_THREAD_JOIN_TIMEOUT)
        with self._lock:
            self._thread = None

    # ------------------------------------------------------------------
    # Test-friendly tick
    # ------------------------------------------------------------------

    def check_once(self) -> bool:
        """Run a single tick of the monitor loop.

        Returns True if this call transitioned the watchdog to tripped.
        Calling after a trip is a no-op and returns False (idempotency).
        """
        now = self._clock()
        with self._lock:
            last = self._last_heartbeat
            already_tripped = self._tripped
        if already_tripped:
            return False

        elapsed = now - last
        # SDD §4.8.C: trip when elapsed > timeout.
        # Step 19 B9 design: clock regression (elapsed < 0) is treated as
        # safety-side trip even though SDD does not specify it (mirrors B4).
        if not (elapsed < 0 or elapsed > self._timeout):
            return False

        try:
            self._state_machine.on_watchdog_timeout(WatchdogReason.SW_WATCHDOG)
        except Exception:
            # SDD §4.8.E: log and continue, do not crash the monitor loop.
            # We still mark _tripped so subsequent ticks are idempotent and
            # the State Machine observer can surface the trip.
            _logger.exception("on_watchdog_timeout raised; marking tripped anyway")
        with self._lock:
            self._tripped = True
        return True

    # ------------------------------------------------------------------
    # Monitor loop (SDD §4.8.C)
    # ------------------------------------------------------------------

    def _monitor_loop(self) -> None:
        while not self._stop_event.is_set():
            self.check_once()
            self._stop_event.wait(self._monitor_interval)
