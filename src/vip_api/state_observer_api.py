"""State Observer API (UNIT-005.2) per SDD-VIP-001 v0.2 §4.16.

Read-only Facade aggregating snapshots from State Machine, Pump
Observer, and Resume Confirmation Gate into a single immutable
`StateSnapshot`. Realises SRS-IF-003 (read-only state observation),
SRS-O-010 (machine-state output), and SRS-UX-002 (no-side-effect /
idempotent).

Step 19 B17 design judgments (recorded in DEVELOPMENT_STEPS.md):

* `StateSnapshot` is `frozen=True, slots=True` (B11〜B16 pattern), not
  the `frozen pydantic` of SDD §4.16.B — the snapshot is an output
  value object that is always constructed by this module from already-
  validated data, so the runtime overhead of pydantic validation has
  no benefit.
* Each collaborator is queried independently; SDD §4.16 explicitly
  documents that the four atomic reads do NOT share a single
  transactional lock (acceptable micro-skew vs. blocking transitions).
* `error_reason` is stringified via `WatchdogReason.name`, keeping the
  internal enum off the API surface.
* SDD §4.16.E states "design goal: no exceptions; if a collaborator
  throws, that's the caller's responsibility." This module therefore
  does NOT wrap collaborator calls in try/except — that would mask
  bugs in collaborators and is the opposite of SDD's intent.
* Collaborators are constructor-injected (B9/B10/B15/B16 pattern).

Related SRS: SRS-IF-003, SRS-O-010, SRS-UX-002.
Related RCM: — (read-only observation).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from vip_ctrl.state_machine import State

if TYPE_CHECKING:
    from vip_ctrl.state_machine import StateMachine
    from vip_integrity.resume_gate import ResumeConfirmationGate
    from vip_sim.pump_observer import PumpObserver, PumpSnapshot

__all__ = [
    "StateObserverApi",
    "StateSnapshot",
]


@dataclass(frozen=True, slots=True)
class StateSnapshot:
    """Immutable aggregate of machine + pump + resume state (SDD §4.16.B)."""

    machine_state: State
    pump: PumpSnapshot
    resume_pending: bool
    resume_set_at: datetime | None
    error_reason: str | None
    observed_at: datetime


class StateObserverApi:
    """Read-only state observer (UNIT-005.2)."""

    def __init__(
        self,
        *,
        state_machine: StateMachine,
        pump_observer: PumpObserver,
        resume_gate: ResumeConfirmationGate,
    ) -> None:
        """Capture references to the three collaborators (no other state)."""
        self._state_machine = state_machine
        self._pump_observer = pump_observer
        self._resume_gate = resume_gate

    def observe_state(self) -> StateSnapshot:
        """Aggregate the current snapshot (SDD §4.16.C, idempotent)."""
        machine = self._state_machine.current()
        pump_snap = self._pump_observer.observe()
        resume_pending = self._resume_gate.is_pending()
        resume_detail = self._resume_gate.pending_detail()

        if machine is State.ERROR:
            reason = self._state_machine.error_reason()
            error_reason: str | None = reason.name if reason is not None else None
        else:
            error_reason = None

        # Inc.1 の ResumeDetail は set_at_wall を持たないため None 固定。
        # Inc.4 UI 着手時に Resume Gate API を拡張して set_at_wall を透過する予定
        # (DEVELOPMENT_STEPS.md Step 19 B17 申し送り)。SDD §4.16.B の
        # `Optional[datetime]` 仕様に合致する。
        _ = resume_detail  # 取得は SDD §4.16.C 擬似コードに従い継続(将来拡張点)
        return StateSnapshot(
            machine_state=machine,
            pump=pump_snap,
            resume_pending=resume_pending,
            resume_set_at=None,
            error_reason=error_reason,
            observed_at=datetime.now(UTC),
        )
