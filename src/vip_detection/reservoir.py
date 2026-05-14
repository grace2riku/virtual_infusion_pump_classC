"""UNIT-006.3 Reservoir Empty Detector (SDD-VIP-001 v0.7 §4.21, RCM-006).

Single-channel reservoir-empty detection over the ``RESERVOIR`` sensor:

* On the reservoir reading falling at or below the empty threshold:
  emit ``SRS-ALM-006`` (MEDIUM / TECHNICAL) and request a ``PAUSED``
  transition. PAUSED — not ERROR — is the safe side here: the device
  has not failed, it has run out of fluid, and an operator can resume
  after refilling (SAD v0.2 §11.1).
* On a healthy reading above the threshold: re-arm silently. The
  detector never requests RUNNING — recovery from PAUSED is an explicit
  operator action (IEC 60601-1-8 §6.4), so a refill only re-arms the
  detector for the next genuine empty condition.
* On a sensor failure (unhealthy reading or a raising reader): request
  ERROR with no alarm payload. A reservoir reading that cannot be
  trusted is a technical fault more severe than a known-empty
  reservoir, so it escalates to ERROR rather than PAUSED (same
  safe-side pattern as UNIT-006.1 / UNIT-006.2).

Step 20 X7 scope (this commit, Inc.2 TDD seed for UNIT-006.3):

* Pure threshold logic in :func:`_evaluate` (UT-006.3-01..03, 03b, 11).
* ``tick`` orchestration: alarm-before-transition ordering on Empty
  (UT-006.3-04), the AlarmEvent content contract (UT-006.3-05), the
  no-op Healthy path (UT-006.3-06), armed-idempotency (UT-006.3-07),
  re-arm after refill (UT-006.3-08), the no-auto-RUNNING contract
  (UT-006.3-09), and exception suppression (UT-006.3-10, 13).
* All collaborators injected (sensor reader, alarm reporter, state
  machine, clock) so unit tests run hermetically.

Out of scope for Step 20 X7 (deferred to SDD v0.8 / later Step):

* Hysteresis / chatter suppression (dual-threshold band) — SDD v0.8
  §4.21.G.x.
* Per-channel fault-detection internals — UNIT-002.3 extension.
* Concurrent-``tick`` resilience — UT-006.3-15+.
* Final threshold value against bench data — :data:`RESERVOIR_EMPTY_THRESHOLD`
  is a placeholder scale pending SDD v0.8 confirmation.

Related SRS: SRS-042, SRS-ALM-006, SRS-IF-010.
Related RCM: RCM-006 (alarm-delivery assurance).
Related HZ:  HZ-004 (detection-failure -> alarm-failure chain),
             HZ-002 (under-infusion on undetected reservoir-empty).
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from decimal import Decimal
from typing import TYPE_CHECKING, Final

from vip_detection.protocols import (
    AlarmCategory,
    AlarmEvent,
    AlarmPriority,
    SensorKind,
    SensorReading,
    TargetState,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from vip_detection.protocols import (
        AlarmReporter,
        SensorReader,
        StateTransitionRequester,
    )

__all__ = [
    "RESERVOIR_EMPTY_THRESHOLD",
    "DetectionResult",
    "Empty",
    "Failed",
    "Healthy",
    "ReservoirEmptyDetector",
]


# ---------------------------------------------------------------------------
# Constants (placeholder value — confirmation in SDD v0.8).
# ---------------------------------------------------------------------------


RESERVOIR_EMPTY_THRESHOLD: Final[Decimal] = Decimal(20)
"""Reservoir reading at or below which the reservoir is treated as empty.

Placeholder scale pending SDD v0.8 bench confirmation. The unit is
intentionally left dimensionless here so the value can be re-projected
once the bench data fixes the sensor's transfer function (e.g. mL of
remaining fluid, or the pump's normalised reading scale).
"""


_DETECTOR_ID: Final[str] = "UNIT-006.3"
_ALARM_ID_RESERVOIR: Final[str] = "ALM-RSV"
_CAUSE_CODE_RESERVOIR_EMPTY: Final[str] = "reservoir_empty"
_REASON_EMPTY: Final[str] = "reservoir_empty"
_REASON_UNAVAILABLE: Final[str] = "reservoir_detection_unavailable"


_logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Sealed DetectionResult hierarchy (3 variants — single-channel detector,
# so there is no Degraded; a sensor fault goes straight to Failed).
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Healthy:
    """Reservoir reading is healthy and above the empty threshold."""


@dataclass(frozen=True, slots=True)
class Empty:
    """Reservoir reading at or below the empty threshold (SRS-042, SRS-ALM-006).

    ``triggering_value`` carries the offending reservoir reading so the
    alarm payload can report the observed level.
    """

    triggering_value: Decimal


@dataclass(frozen=True, slots=True)
class Failed:
    """Reservoir channel unhealthy — detection is unavailable (safe-side).

    Triggers an ``ERROR`` transition request without an alarm payload.
    """


DetectionResult = Healthy | Empty | Failed
"""Sealed result of one reservoir evaluation."""


# ---------------------------------------------------------------------------
# Detector unit (UNIT-006.3).
# ---------------------------------------------------------------------------


class ReservoirEmptyDetector:
    """Single-channel reservoir-empty detector (UNIT-006.3).

    The detector keeps one armed flag so that continuous Empty ticks
    collapse to one alarm event and one PAUSED transition request
    (``_armed``, UT-006.3-07). A return to Healthy (a refill) or a
    sensor-failure tick re-arms the detector, so a recurring empty
    condition is reported afresh (UT-006.3-08, UT-006.3-14).
    """

    def __init__(
        self,
        *,
        sensor_reader: SensorReader,
        alarm_reporter: AlarmReporter,
        state_machine: StateTransitionRequester,
        clock: Callable[[], float] = time.monotonic,
        empty_threshold: Decimal = RESERVOIR_EMPTY_THRESHOLD,
    ) -> None:
        """Wire the detector to its collaborators.

        Args:
            sensor_reader: IF-U-015 pull provider for the ``RESERVOIR``
                channel.
            alarm_reporter: IF-U-007 / IF-U-012 alarm sink (SEP-003,
                exception-suppressed by the detector).
            state_machine: IF-U-013 transition-request sink.
            clock: Monotonic seconds source for ``AlarmEvent.occurred_at``.
            empty_threshold: Reservoir reading at or below which the
                reservoir is empty. Defaults to
                :data:`RESERVOIR_EMPTY_THRESHOLD`.

        """
        self._sensor_reader = sensor_reader
        self._alarm_reporter = alarm_reporter
        self._state_machine = state_machine
        self._clock = clock
        self._empty_threshold = empty_threshold
        self._armed = True

    # ------------------------------------------------------------------
    # Public entry point — periodic tick driven by the control loop.
    # ------------------------------------------------------------------

    def tick(self) -> None:
        """Perform one detection cycle.

        Outline:

        1. Read the reservoir channel (guarding against sensor faults).
        2. Evaluate the threshold logic (pure :func:`_evaluate`).
        3. Drive side effects per result type, preserving the
           alarm-before-transition order on Empty.
        """
        reading = self._safe_read(SensorKind.RESERVOIR)
        result = self._evaluate(reading)
        self._apply(result)

    # ------------------------------------------------------------------
    # Pure decision logic (testable in isolation).
    # ------------------------------------------------------------------

    def _evaluate(self, reading: SensorReading) -> DetectionResult:
        """Single-channel threshold evaluation (no side effects).

        Decision order:

        1. Unhealthy reading -> ``Failed``.
        2. Value <= empty threshold -> ``Empty`` (boundary inclusive).
        3. Otherwise -> ``Healthy``.
        """
        if not reading.healthy:
            return Failed()
        if reading.value <= self._empty_threshold:
            return Empty(triggering_value=reading.value)
        return Healthy()

    # ------------------------------------------------------------------
    # Internals.
    # ------------------------------------------------------------------

    def _safe_read(self, kind: SensorKind) -> SensorReading:
        """Read the channel, converting raised exceptions to ``healthy=False``.

        SEP-003 requires sensor faults to degrade detection rather than
        crash the periodic tick. The placeholder value handed to
        :func:`_evaluate` is :class:`Decimal` zero — it is ignored when
        ``healthy=False`` but must still satisfy the dataclass type
        constraint.
        """
        try:
            return self._sensor_reader.read_sensor(kind)
        except Exception:  # noqa: BLE001 — SEP-003 catch-all is intentional
            _logger.warning("sensor read failed: kind=%s", kind.value, exc_info=True)
            return SensorReading(kind=kind, value=Decimal(0), healthy=False)

    def _apply(self, result: DetectionResult) -> None:
        """Drive side effects for a decision result."""
        if isinstance(result, Empty):
            self._on_empty(result)
            return
        if isinstance(result, Failed):
            self._on_failed()
            return
        # Healthy (a refill) re-arms the detector so a subsequent empty
        # condition triggers a fresh alarm (UT-006.3-08). No transition
        # is requested — recovery from PAUSED is an operator action
        # (UT-006.3-09).
        self._armed = True

    def _on_empty(self, result: Empty) -> None:
        """Emit alarm and request the PAUSED transition (idempotent while armed).

        Continuous empty ticks collapse to one alarm event and one
        transition request per UT-006.3-07. The alarm is emitted before
        the transition request so the alarm path observes the event
        before the control loop pauses (UT-006.3-04).
        """
        if not self._armed:
            return
        event = AlarmEvent(
            alarm_id=_ALARM_ID_RESERVOIR,
            priority=AlarmPriority.MEDIUM,
            category=AlarmCategory.TECHNICAL,
            occurred_at=self._clock(),
            cause_code=_CAUSE_CODE_RESERVOIR_EMPTY,
            metadata={"triggering_value": result.triggering_value},
        )
        try:
            self._alarm_reporter.report_alarm(event)
        except Exception:  # noqa: BLE001 — SEP-003 catch-all
            _logger.warning(
                "alarm reporter raised; continuing to state-transition request",
                exc_info=True,
            )
        self._armed = False
        self._state_machine.request_state_transition(
            TargetState.PAUSED,
            reason=_REASON_EMPTY,
        )

    def _on_failed(self) -> None:
        """Reservoir channel lost — escalate to ERROR without an alarm payload."""
        self._state_machine.request_state_transition(
            TargetState.ERROR,
            reason=_REASON_UNAVAILABLE,
        )
        # Re-arm so that, on recovery, the next true empty condition is
        # reported (UT-006.3-14).
        self._armed = True
