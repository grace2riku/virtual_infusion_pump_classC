"""Pump observer (UNIT-002.2) per SDD-VIP-001 v0.2 §4.10.

Read-only observer that builds frozen `PumpSnapshot` values from
`PumpSimulator` state. Realises SRS-031 (state observability) and
SRS-I-020 (internal observation interface). Consumed by the Control
Loop (UNIT-001.2 auto-stop check) and the future State Observer API
(UNIT-005.2).

Step 19 B12 design judgments (recorded in DEVELOPMENT_STEPS.md):

* `observe` borrows the Pump Simulator's `_lock` (SDD §4.10.C) so all
  six fields land in a single critical section. Borrowing the lock is
  intentional — having Observer hold its own lock would either race
  with the pump or require a second-level lock that complicates the
  failsafe path. The private access is annotated with `# noqa: SLF001`.
* `PumpSnapshot` is `frozen=True, slots=True`; this makes
  `FrozenInstanceError` on attribute assignment a contract test (B12).
* `observed_at` is `time.monotonic()` so consecutive observes form a
  non-decreasing sequence regardless of system clock changes.
* Observer is stateless: only the `_pump` reference is retained.

Related SRS: SRS-031, SRS-I-020.
Related HZ:  — (observation only, no RCM).
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from decimal import Decimal  # noqa: TC003 (runtime use in dataclass field types)
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from vip_sim.pump_simulator import PumpSimulator

__all__ = [
    "PumpObserver",
    "PumpSnapshot",
]


@dataclass(frozen=True, slots=True)
class PumpSnapshot:
    """Immutable observation of pump state (SDD §4.10.B).

    Fields mirror SDD §4.10.B exactly. The structural shape satisfies the
    Control Loop's `PumpSnapshot` Protocol (which requires `current_flow`,
    `accumulated_volume`, `elapsed_min`).
    """

    current_flow: Decimal
    target_flow: Decimal
    accumulated_volume: Decimal
    elapsed_min: Decimal
    failsafe_active: bool
    observed_at: float


class PumpObserver:
    """Stateless adapter exposing `PumpSimulator` state as frozen snapshots."""

    def __init__(self, *, pump: PumpSimulator) -> None:
        """Capture the pump under observation; no other state is retained."""
        self._pump = pump

    def observe(self) -> PumpSnapshot:
        """Return an atomic 6-field snapshot of pump state (SDD §4.10.C).

        Borrows `pump._lock` to read all fields in one critical section,
        avoiding tearing across `current_flow` / `accumulated_volume` /
        `elapsed_min` / etc. The private access is by design (SDD §4.10.C
        explicitly chose lock borrowing over an Observer-owned lock).
        """
        with self._pump._lock:  # noqa: SLF001 — see module docstring + SDD §4.10.C
            return PumpSnapshot(
                current_flow=self._pump._current_flow,  # noqa: SLF001
                target_flow=self._pump._target_flow,  # noqa: SLF001
                accumulated_volume=self._pump._accumulated_volume,  # noqa: SLF001
                elapsed_min=self._pump._elapsed_min,  # noqa: SLF001
                failsafe_active=self._pump._failsafe_active,  # noqa: SLF001
                observed_at=time.monotonic(),
            )
