"""HW-side failsafe timer (UNIT-002.4) per SDD-VIP-001 v0.2 §4.3.

Implements RCM-004 HW-side: a watchdog living on the (virtual) pump side
that independently halts flow when the control task stops sending
heartbeats. Independent of the SW watchdog (UNIT-001.5) so a single
control-loop failure cannot disable both layers.

Step 19 B4 design judgments (recorded in DEVELOPMENT_STEPS.md):

* `clock` is injectable so deterministic tests can drive time without
  patching `time.monotonic` globally. Production callers pass nothing
  and get `time.monotonic`.
* The HW failsafe identifier is carried by the `reason="HEARTBEAT_TIMEOUT"`
  argument of `force_stop_failsafe`; an explicit logger wire-up is
  deferred to UNIT-004+ (SDD §4.3.B does not declare a `_logger` field).
* Clock regression (`now < last`) is treated as a safety-side trip
  even though SDD §4.3 leaves this case undefined; RCM-004 demands
  fail-safe and the State Machine baseline (UNIT-001.1) follows the
  same "unknown ⇒ safe" pattern.

Related SRS: SRS-RCM-004, SRS-032.
Related RCM: RCM-004 (HW side).
Related HZ:  HZ-001, HZ-002.
"""

from __future__ import annotations

import logging
import threading
import time
from typing import TYPE_CHECKING, Final, Protocol

if TYPE_CHECKING:
    from collections.abc import Callable

__all__ = [
    "HEARTBEAT_TIMEOUT",
    "MONITOR_INTERVAL",
    "HwFailsafeTimer",
    "PumpController",
]


# ---------------------------------------------------------------------------
# Domain constants (SDD §4.3.C)
# ---------------------------------------------------------------------------

HEARTBEAT_TIMEOUT: Final[float] = 0.5
MONITOR_INTERVAL: Final[float] = 0.1
_FAILSAFE_REASON: Final[str] = "HEARTBEAT_TIMEOUT"
_THREAD_JOIN_TIMEOUT: Final[float] = 2.0


# ---------------------------------------------------------------------------
# Collaborator protocol
# ---------------------------------------------------------------------------


class PumpController(Protocol):
    """Subset of the virtual pump API the timer uses."""

    def force_stop_failsafe(self, *, reason: str) -> None:
        """Stop the pump immediately for fail-safe reason `reason`."""


# ---------------------------------------------------------------------------
# Timer
# ---------------------------------------------------------------------------


_logger = logging.getLogger(__name__)


class HwFailsafeTimer:
    """Pump-side heartbeat watchdog (RCM-004 HW redundant layer).

    Threading model: a single monitor thread (started via `start`) ticks at
    `monitor_interval` and calls `force_stop_failsafe` when the gap since the
    last heartbeat exceeds `timeout`. All shared state is guarded by an
    internal `Lock`. Tests typically bypass the thread by calling
    `check_once` directly with an injected fake clock.
    """

    def __init__(
        self,
        pump: PumpController,
        *,
        clock: Callable[[], float] | None = None,
        timeout: float = HEARTBEAT_TIMEOUT,
        monitor_interval: float = MONITOR_INTERVAL,
    ) -> None:
        """Wire up dependencies; construction does not start the monitor thread."""
        self._pump = pump
        self._clock = clock if clock is not None else time.monotonic
        self._timeout = timeout
        self._monitor_interval = monitor_interval
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._last_heartbeat: float = self._clock()
        self._tripped: bool = False

    # ------------------------------------------------------------------
    # Public API (SDD §4.3.A)
    # ------------------------------------------------------------------

    def heartbeat(self) -> None:
        """Refresh the last-heartbeat timestamp (no-op once tripped)."""
        ts = self._clock()
        with self._lock:
            if not self._tripped:
                self._last_heartbeat = ts

    def is_tripped(self) -> bool:
        """Return True once the failsafe has fired."""
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
                msg = "HwFailsafeTimer already started"
                raise RuntimeError(msg)
            self._stop_event.clear()
            self._last_heartbeat = self._clock()
            self._thread = threading.Thread(
                target=self._monitor_loop,
                name="HwFailsafeTimer",
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

        Returns True if this call transitioned the timer to tripped. Calling
        after a trip is a no-op and returns False (idempotency).
        """
        now = self._clock()
        with self._lock:
            last = self._last_heartbeat
            already_tripped = self._tripped
        if already_tripped:
            return False

        elapsed = now - last
        # SDD §4.3.C: trip when elapsed > timeout.
        # Step 19 B4 design: clock regression (elapsed < 0) is treated as
        # safety-side trip even though SDD does not specify it.
        if not (elapsed < 0 or elapsed > self._timeout):
            return False

        try:
            self._pump.force_stop_failsafe(reason=_FAILSAFE_REASON)
        except Exception:
            # SDD §4.3.E: log and continue, do not crash the monitor.
            # We still mark _tripped so subsequent ticks are idempotent and
            # the operator-facing state observer can surface the trip.
            _logger.exception("force_stop_failsafe raised; marking tripped anyway")
        with self._lock:
            self._tripped = True
        return True

    # ------------------------------------------------------------------
    # Monitor loop (SDD §4.3.C)
    # ------------------------------------------------------------------

    def _monitor_loop(self) -> None:
        while not self._stop_event.is_set():
            self.check_once()
            self._stop_event.wait(self._monitor_interval)
