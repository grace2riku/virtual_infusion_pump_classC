"""Shared protocols for the detection group (ARCH-006).

Defines the dependency boundary that every detector unit in Inc.2 talks to:

* :class:`SensorKind` / :class:`SensorReading` — IF-U-015 sensor pull I/F
  (SDD-VIP-001 v0.5 §5.1, SAD v0.2 §5 IF-U-015). The sealed ``SensorKind``
  enum names the six redundant channels available to the detection group;
  ``SensorReading.healthy`` represents per-channel fault detection so the
  detector logic can stay agnostic of the actual fault-detection mechanism
  (timeout / noise threshold / consecutive error count — all deferred to
  the SDD v0.6 / UNIT-002.3 extension).
* :class:`SensorReader` — pull I/F implemented by UNIT-002.1 PumpSimulator
  + UNIT-002.3 EventInjection extension (SAD v0.2 §11.3 SRS-RCM-009/010).
* :class:`AlarmPriority` / :class:`AlarmCategory` / :class:`AlarmEvent` —
  IF-U-007 alarm event contract (SDD v0.5 §5.1.A). ``AlarmEvent`` is
  ``frozen=True, slots=True`` to satisfy the immutability requirement
  recorded in SDD §5.1.A; the ``metadata`` mapping is wrapped in
  :class:`types.MappingProxyType` so callers cannot mutate it post-hoc.
* :class:`AlarmReporter` — IF-U-007 / IF-U-012 push contract implemented
  by UNIT-007.1 Alarm Reporter Core (planned). The contract forbids
  exceptions from propagating back to the detector (SEP-003).
* :class:`StateTransitionRequester` — IF-U-013 transition-request push
  contract implemented by UNIT-001.1 State Machine.

These protocols are intentionally placed in this module (rather than inside
``occlusion.py``) so UNIT-006.2 .. UNIT-006.6 can import them without
duplicating type definitions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from collections.abc import Mapping
    from decimal import Decimal

__all__ = [
    "AlarmCategory",
    "AlarmEvent",
    "AlarmPriority",
    "AlarmReporter",
    "SensorKind",
    "SensorReader",
    "SensorReading",
    "StateTransitionRequester",
    "TargetState",
]


class SensorKind(Enum):
    """Sealed catalogue of sensor channels (IF-U-015, SAD v0.2 §5).

    The two ``OCCLUSION_*`` channels back the redundant-pair contract in
    SRS-RCM-009; ``AIR_BUBBLE_WARN`` / ``AIR_BUBBLE_CRITICAL`` back the
    multi-stage contract in SRS-RCM-010. ``RESERVOIR`` and ``BATTERY``
    are single-channel inputs feeding UNIT-006.3 and UNIT-006.6.
    """

    OCCLUSION_PRIMARY = "occlusion_primary"
    OCCLUSION_SECONDARY = "occlusion_secondary"
    AIR_BUBBLE_WARN = "air_bubble_warn"
    AIR_BUBBLE_CRITICAL = "air_bubble_critical"
    RESERVOIR = "reservoir"
    BATTERY = "battery"


@dataclass(frozen=True, slots=True)
class SensorReading:
    """One sample from a sensor channel (IF-U-015).

    ``healthy=False`` indicates a per-channel fault (timeout / noise /
    out-of-range) detected upstream of the detection group. Detectors
    must treat unhealthy readings as unusable for the threshold decision
    but still consider the channel reachable for the next ``tick``.

    The concrete fault-detection rule lives in UNIT-002.3 EventInjection
    extension (Step 20 X+1 onward) per SDD §4.11.G; the detection group
    only consumes the boolean flag.
    """

    kind: SensorKind
    value: Decimal
    healthy: bool = True


@runtime_checkable
class SensorReader(Protocol):
    """IF-U-015 pull contract.

    Implemented by UNIT-002.1 PumpSimulator + UNIT-002.3 EventInjection
    extension (the latter currently no-op). The detection group calls
    :meth:`read_sensor` once per tick per channel.
    """

    def read_sensor(self, kind: SensorKind) -> SensorReading:
        """Return the most recent reading on ``kind``.

        Implementations may raise on truly catastrophic failures
        (e.g. corrupted hardware register). Detectors must guard the
        call so SEP-003 (alarm-path resilience) survives the exception.
        """
        ...


class AlarmPriority(Enum):
    """IEC 60601-1-8 §6.1 priority levels (SDD §5.1.A)."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class AlarmCategory(Enum):
    """IEC 60601-1-8 §5.1.4 alarm categories (SDD §5.1.A)."""

    TECHNICAL = "technical"
    PHYSIOLOGICAL = "physiological"


def _empty_metadata() -> Mapping[str, object]:
    """Return an empty immutable metadata mapping (factory for ``AlarmEvent``)."""
    return MappingProxyType({})


@dataclass(frozen=True, slots=True)
class AlarmEvent:
    """Immutable alarm event (IF-U-007, SDD v0.5 §5.1.A).

    The detection group constructs an ``AlarmEvent`` whenever a hazard
    becomes actionable, and hands it to :class:`AlarmReporter` for
    delivery. ``metadata`` is wrapped in :class:`types.MappingProxyType`
    at construction so downstream callers cannot mutate the snapshot.
    """

    alarm_id: str
    priority: AlarmPriority
    category: AlarmCategory
    occurred_at: float
    cause_code: str
    metadata: Mapping[str, object] = field(default_factory=_empty_metadata)


@runtime_checkable
class AlarmReporter(Protocol):
    """IF-U-007 / IF-U-012 push contract (planned UNIT-007.1).

    Implementations must never re-raise: SEP-003 (separation of alarm
    delivery from detection) requires the detector to continue running
    even if the reporter is unable to deliver.
    """

    def report_alarm(self, event: AlarmEvent) -> None:
        """Hand off ``event`` for delivery. Must not raise back to caller."""
        ...


class TargetState(Enum):
    """Sealed state-machine targets reachable from the detection group.

    Inc.2 detectors only request the two safe-side states defined by
    SAD v0.2 §11.1: ``ERROR`` (immediate stop) and ``PAUSED``
    (operator-recoverable pause, used by UNIT-006.3 reservoir-empty).
    """

    ERROR = "error"
    PAUSED = "paused"


@runtime_checkable
class StateTransitionRequester(Protocol):
    """IF-U-013 transition-request contract (UNIT-001.1 State Machine)."""

    def request_state_transition(self, target: TargetState, *, reason: str) -> None:
        """Request a transition to ``target``. Implementations should be idempotent."""
        ...
