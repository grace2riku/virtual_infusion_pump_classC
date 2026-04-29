"""Virtual pump simulator (UNIT-002.1) per SDD-VIP-001 v0.2 §4.9.

Implements the virtual pump model that responds to flow commands and
accumulates dose, time, and current flow values. Realises SRS-030
(simulation), SRS-031 (state observability), and SRS-P01 (±5% steady-
state accuracy via a first-order lag with τ = 0.5 s). Receives
`force_stop_failsafe` from UNIT-002.4 (RCM-004 HW-side callee).

Step 19 B11 design judgments (recorded in DEVELOPMENT_STEPS.md):

* SRS-031 observation contract is exposed via thread-safe getters
  (`current_flow` / `accumulated_volume` / `elapsed_min` /
  `is_failsafe_active` / `failsafe_reason`). UNIT-002.2 Pump Observer
  will wrap these into a frozen `PumpSnapshot` (a future TDD step).
* Accumulation overflow (>`MAX_ACCUMULATED_VOLUME`) emits a
  `logger.warning` and continues — clamping is intentionally avoided
  so over-detection can be performed by upper layers (UI, Inc.4).
* `release_failsafe()` is public for unit testability; production
  wiring via UNIT-005.1 (CMD_ERROR_RESET) follows in a later step.
* `Decimal` arithmetic throughout to keep arithmetic deterministic;
  `math.exp` is the only float gateway and its result is converted
  to `Decimal` before any state mutation.

Related SRS: SRS-030, SRS-031, SRS-P01, SRS-RCM-004 (HW-side callee).
Related RCM: RCM-004 (HW-side callee via `force_stop_failsafe`).
Related HZ:  HZ-001 (over-delivery), HZ-002 (under-delivery).
"""

from __future__ import annotations

import logging
import math
import threading
from decimal import Decimal
from typing import Final

__all__ = [
    "MAX_ACCUMULATED_VOLUME",
    "TIME_CONSTANT_SEC",
    "PumpSimulator",
]


# ---------------------------------------------------------------------------
# Domain constants (SDD §4.9.B / SRS-I-020)
# ---------------------------------------------------------------------------

TIME_CONSTANT_SEC: Final[float] = 0.5
"""First-order lag time constant τ (SDD §4.9.C, SRS-P01 backing)."""

MAX_ACCUMULATED_VOLUME: Final[Decimal] = Decimal("9999.9")
"""SRS-I-020 accumulated-volume range upper bound (mL)."""

_SECONDS_PER_HOUR: Final[Decimal] = Decimal(3600)
_SECONDS_PER_MINUTE: Final[Decimal] = Decimal(60)
_ZERO: Final[Decimal] = Decimal(0)


_logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Pump simulator
# ---------------------------------------------------------------------------


class PumpSimulator:
    """Virtual infusion pump model (UNIT-002.1).

    Threading model: all mutating operations acquire an internal `RLock`
    so the Control Loop (UNIT-001.2, periodic thread) and the HW-side
    Failsafe Timer (UNIT-002.4, monitor thread) can call concurrently.
    Re-entrant because some helpers may need to call back into the same
    instance under lock.
    """

    def __init__(self) -> None:
        """Initialise all observable values to zero and failsafe inactive."""
        self._lock = threading.RLock()
        self._target_flow: Decimal = _ZERO
        self._current_flow: Decimal = _ZERO
        self._accumulated_volume: Decimal = _ZERO
        self._elapsed_min: Decimal = _ZERO
        self._failsafe_active: bool = False
        self._failsafe_reason: str | None = None
        self._overflow_logged: bool = False

    # ------------------------------------------------------------------
    # Public API (SDD §4.9.A)
    # ------------------------------------------------------------------

    def set_flow_rate(self, target: Decimal) -> None:
        """Update the target flow rate; ignored while failsafe is active."""
        with self._lock:
            if self._failsafe_active:
                _logger.info(
                    "set_flow_rate ignored: failsafe active (reason=%s)",
                    self._failsafe_reason,
                )
                return
            self._target_flow = target

    def advance_time(self, dt_sec: float) -> None:
        """Advance the model by `dt_sec` seconds.

        Updates `current_flow` via first-order lag, accumulates dose,
        and progresses elapsed time. While failsafe is active, only
        `elapsed_min` advances (flow stays 0, dose is not added).
        """
        if dt_sec <= 0:
            msg = "dt must be positive"
            raise ValueError(msg)
        with self._lock:
            dt = Decimal(str(dt_sec))
            if self._failsafe_active:
                # SDD §4.9.C: failsafe maintains zero flow; only time advances.
                self._elapsed_min += dt / _SECONDS_PER_MINUTE
                return
            # First-order lag: current += (target - current) * (1 - exp(-dt/τ))
            alpha = Decimal(str(1.0 - math.exp(-dt_sec / TIME_CONSTANT_SEC)))
            delta = (self._target_flow - self._current_flow) * alpha
            self._current_flow += delta
            # Accumulated dose: current_flow [mL/h] * dt [s] / 3600 -> mL
            increment = self._current_flow * dt / _SECONDS_PER_HOUR
            self._accumulated_volume += increment
            self._elapsed_min += dt / _SECONDS_PER_MINUTE
            self._maybe_warn_overflow()

    def reset(self) -> None:
        """Reset all state to initial values; ignored while failsafe is active."""
        with self._lock:
            if self._failsafe_active:
                _logger.info(
                    "reset ignored: failsafe active (reason=%s)",
                    self._failsafe_reason,
                )
                return
            self._target_flow = _ZERO
            self._current_flow = _ZERO
            self._accumulated_volume = _ZERO
            self._elapsed_min = _ZERO
            self._overflow_logged = False

    def force_stop_failsafe(self, *, reason: str) -> None:
        """Engage failsafe stop. Idempotent — first reason is preserved."""
        with self._lock:
            if not self._failsafe_active:
                self._failsafe_active = True
                self._failsafe_reason = reason
            self._target_flow = _ZERO
            self._current_flow = _ZERO

    def release_failsafe(self) -> None:
        """Clear the failsafe flag (no-op when not active)."""
        with self._lock:
            if not self._failsafe_active:
                return
            self._failsafe_active = False
            self._failsafe_reason = None

    # ------------------------------------------------------------------
    # SRS-031 observation contract (Step 19 B11 design judgment)
    # ------------------------------------------------------------------

    def current_flow(self) -> Decimal:
        """Return the current flow rate (mL/h)."""
        with self._lock:
            return self._current_flow

    def accumulated_volume(self) -> Decimal:
        """Return total volume infused (mL)."""
        with self._lock:
            return self._accumulated_volume

    def elapsed_min(self) -> Decimal:
        """Return elapsed time since last reset (minutes)."""
        with self._lock:
            return self._elapsed_min

    def is_failsafe_active(self) -> bool:
        """Return True while the failsafe stop is engaged."""
        with self._lock:
            return self._failsafe_active

    def failsafe_reason(self) -> str | None:
        """Return the first reason recorded when failsafe engaged, or None."""
        with self._lock:
            return self._failsafe_reason

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _maybe_warn_overflow(self) -> None:
        """Emit one warning when accumulated volume first exceeds the SRS-I-020 limit."""
        if self._accumulated_volume > MAX_ACCUMULATED_VOLUME and not self._overflow_logged:
            _logger.warning(
                "accumulated_volume overflow: %s mL exceeds SRS-I-020 limit %s mL",
                self._accumulated_volume,
                MAX_ACCUMULATED_VOLUME,
            )
            self._overflow_logged = True
