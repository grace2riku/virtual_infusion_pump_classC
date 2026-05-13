"""UNIT-006.2 Air-Bubble Detector (SDD-VIP-001 v0.6 §4.20, RCM-010).

Multi-stage air-bubble detection using two physically independent sensor
channels (``AIR_BUBBLE_WARN`` and ``AIR_BUBBLE_CRITICAL``):

* On warning-threshold exceedance with critical still below: emit an
  audit-only record via :class:`~vip_detection.protocols.WarningLogger`
  (no alarm, no transition). Inc.4 is expected to wire a UI surface into
  the same Protocol.
* On critical-threshold exceedance: emit ``SRS-ALM-005`` (HIGH /
  TECHNICAL) and request an ERROR transition. The critical stage is
  evaluated independently from warning — a noisy warning sensor cannot
  mask or fabricate a critical decision (SDD §4.20).
* On both-channel sensor failure: request ERROR with no alarm payload
  (safe side, same pattern as UNIT-006.1).
* On single-channel failure: return ``Degraded`` and continue
  monitoring; alarms / warnings are quiet until the surviving channel
  observes an actual exceedance.

Step 20 X4 scope (this commit, Inc.2 TDD seed for UNIT-006.2):

* Pure threshold logic in :func:`_evaluate` (UT-006.2-01..10).
* ``tick`` orchestration: alarm-before-transition ordering on Detected
  (UT-006.2-12), warning-only logging (UT-006.2-13), idempotency over
  both severity stages (UT-006.2-17..19), sensor-exception suppression
  (UT-006.2-20).
* All collaborators injected (sensor reader, alarm reporter, warning
  logger, state machine, clock) so unit tests run hermetically.

Out of scope for Step 20 X4 (deferred to SDD v0.7 / later Step):

* Continuous-warning-to-critical hold time — SDD v0.7 §4.20.G.x.
* Per-channel fault-detection internals — UNIT-002.3 extension.
* Concurrent-``tick`` resilience — UT-006.2-21+.
* Final threshold values against bench data — :data:`AIR_BUBBLE_WARN_THRESHOLD`
  and :data:`AIR_BUBBLE_CRITICAL_THRESHOLD` are placeholder scales
  pending SDD v0.7 confirmation.

Related SRS: SRS-041, SRS-RCM-010, SRS-ALM-005, SRS-IF-010.
Related RCM: RCM-010 (multi-stage air-bubble detection).
Related HZ:  HZ-004 (detection-failure -> alarm-failure chain).
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
        WarningLogger,
    )

__all__ = [
    "AIR_BUBBLE_CRITICAL_THRESHOLD",
    "AIR_BUBBLE_WARN_THRESHOLD",
    "AirBubbleDetector",
    "Degraded",
    "Detected",
    "DetectionResult",
    "Failed",
    "Healthy",
    "Warning",
]


# ---------------------------------------------------------------------------
# Constants (placeholder values — confirmation in SDD v0.7).
# ---------------------------------------------------------------------------


AIR_BUBBLE_WARN_THRESHOLD: Final[Decimal] = Decimal(50)
"""Sensor reading at or above which the warning stage records a hit.

Placeholder scale pending SDD v0.7 bench confirmation. The unit is
intentionally left dimensionless here so the value can be re-projected
once the bench data fixes the sensor's transfer function (e.g. mm^3 of
entrained air, or the pump's normalised reading scale).
"""

AIR_BUBBLE_CRITICAL_THRESHOLD: Final[Decimal] = Decimal(150)
"""Sensor reading at or above which the critical stage emits an alarm.

Strictly greater than :data:`AIR_BUBBLE_WARN_THRESHOLD` by construction;
SDD v0.7 must re-validate this ordering against the bench data before
the constant is published in the released device.
"""


_DETECTOR_ID: Final[str] = "UNIT-006.2"
_ALARM_ID_AIR_BUBBLE: Final[str] = "ALM-AIR"
_CAUSE_CODE_AIR_BUBBLE: Final[str] = "air_bubble"
_REASON_DETECTED: Final[str] = "air_bubble_detected"
_REASON_UNAVAILABLE: Final[str] = "air_bubble_detection_unavailable"


_logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Sealed DetectionResult hierarchy (5 variants — adds Warning to the
# UNIT-006.1 quartet to encode the multi-stage outcome explicitly).
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Healthy:
    """Both channels healthy and below the warning threshold."""


@dataclass(frozen=True, slots=True)
class Warning:  # noqa: A001 — SDD §4.20 names this stage "Warning"; shadow is deliberate
    """Warning channel exceeded its threshold, critical still below.

    ``triggering_value`` carries the warning-channel reading so the
    audit record produced by :class:`~vip_detection.protocols.WarningLogger`
    can include the offending value.
    """

    triggering_value: Decimal


@dataclass(frozen=True, slots=True)
class Detected:
    """Critical channel exceeded its threshold (SRS-041, SRS-ALM-005).

    ``triggering_value`` is the critical channel's reading, not the
    warning channel's — even when both stages are over their respective
    thresholds, the alarm payload reflects the more severe input.
    """

    triggering_value: Decimal


@dataclass(frozen=True, slots=True)
class Degraded:
    """One channel unhealthy; the surviving channel was below threshold.

    Monitoring continues on the surviving channel until it either
    recovers (Healthy / Warning / Detected) or the other channel also
    fails (Failed).
    """

    failed_channel: SensorKind


@dataclass(frozen=True, slots=True)
class Failed:
    """Both channels unhealthy — detection is unavailable (safe-side).

    Triggers an ``ERROR`` transition request without an alarm payload.
    """


DetectionResult = Healthy | Warning | Detected | Degraded | Failed
"""Sealed result of one multi-stage evaluation."""


# ---------------------------------------------------------------------------
# Detector unit (UNIT-006.2).
# ---------------------------------------------------------------------------


class AirBubbleDetector:
    """Multi-stage air-bubble detector (UNIT-006.2).

    The detector keeps two armed flags so that:

    * Continuous Detected ticks collapse to one alarm event and one
      transition request (``_alarm_armed``, UT-006.2-17).
    * Continuous Warning ticks collapse to one logger record
      (``_warning_armed``, UT-006.2-18).

    A return to Healthy / Degraded re-arms both stages, so a recurring
    bubble is reported afresh (UT-006.2-19).
    """

    def __init__(  # noqa: PLR0913 — DI-driven detector; all kwargs are deliberate
        self,
        *,
        sensor_reader: SensorReader,
        alarm_reporter: AlarmReporter,
        warning_logger: WarningLogger,
        state_machine: StateTransitionRequester,
        clock: Callable[[], float] = time.monotonic,
        warn_threshold: Decimal = AIR_BUBBLE_WARN_THRESHOLD,
        critical_threshold: Decimal = AIR_BUBBLE_CRITICAL_THRESHOLD,
    ) -> None:
        """Wire the detector to its collaborators.

        Args:
            sensor_reader: IF-U-015 pull provider for the two
                air-bubble channels.
            alarm_reporter: IF-U-007 / IF-U-012 alarm sink (SEP-003,
                exception-suppressed by the detector).
            warning_logger: Sub-alarm record sink for warning-stage
                exceedances (SEP-003, exception-suppressed).
            state_machine: IF-U-013 transition-request sink.
            clock: Monotonic seconds source for ``AlarmEvent.occurred_at``
                and warning-record timestamps.
            warn_threshold: Per-channel warning threshold. Defaults to
                :data:`AIR_BUBBLE_WARN_THRESHOLD`.
            critical_threshold: Per-channel critical threshold. Defaults
                to :data:`AIR_BUBBLE_CRITICAL_THRESHOLD`.

        """
        self._sensor_reader = sensor_reader
        self._alarm_reporter = alarm_reporter
        self._warning_logger = warning_logger
        self._state_machine = state_machine
        self._clock = clock
        self._warn_threshold = warn_threshold
        self._critical_threshold = critical_threshold
        self._alarm_armed = True
        self._warning_armed = True

    # ------------------------------------------------------------------
    # Public entry point — periodic tick driven by the control loop.
    # ------------------------------------------------------------------

    def tick(self) -> None:
        """Perform one detection cycle.

        Outline:

        1. Read both channels (guarding against sensor faults).
        2. Evaluate the multi-stage threshold logic (pure
           :func:`_evaluate`).
        3. Drive side effects per result type, preserving the
           alarm-before-transition order on Detected.
        """
        warn = self._safe_read(SensorKind.AIR_BUBBLE_WARN)
        critical = self._safe_read(SensorKind.AIR_BUBBLE_CRITICAL)
        result = self._evaluate(warn, critical)
        self._apply(result)

    # ------------------------------------------------------------------
    # Pure decision logic (testable in isolation).
    # ------------------------------------------------------------------

    def _evaluate(
        self,
        warn: SensorReading,
        critical: SensorReading,
    ) -> DetectionResult:
        """Multi-stage threshold evaluation (no side effects).

        Decision order:

        1. Both unhealthy -> ``Failed``.
        2. Critical unhealthy (warn either way) -> ``Degraded(CRITICAL)``.
        3. Warn unhealthy (critical healthy, below) -> ``Degraded(WARN)``.
        4. Critical healthy, value >= critical threshold -> ``Detected``.
        5. Warn healthy, value >= warn threshold (critical below) ->
           ``Warning``.
        6. Otherwise -> ``Healthy``.
        """
        warn_ok = warn.healthy
        critical_ok = critical.healthy

        if not warn_ok and not critical_ok:
            return Failed()

        if critical_ok and critical.value >= self._critical_threshold:
            return Detected(triggering_value=critical.value)

        if not critical_ok:
            return Degraded(failed_channel=SensorKind.AIR_BUBBLE_CRITICAL)
        if not warn_ok:
            return Degraded(failed_channel=SensorKind.AIR_BUBBLE_WARN)

        if warn.value >= self._warn_threshold:
            return Warning(triggering_value=warn.value)

        return Healthy()

    # ------------------------------------------------------------------
    # Internals.
    # ------------------------------------------------------------------

    def _safe_read(self, kind: SensorKind) -> SensorReading:
        """Read a channel, converting raised exceptions to ``healthy=False``.

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
        if isinstance(result, Detected):
            self._on_detected(result)
            return
        if isinstance(result, Warning):
            self._on_warning(result)
            return
        if isinstance(result, Failed):
            self._on_failed()
            return
        # Healthy and Degraded re-arm both severity stages so a
        # subsequent recurrence triggers fresh emissions (UT-006.2-19).
        self._alarm_armed = True
        self._warning_armed = True

    def _on_detected(self, result: Detected) -> None:
        """Emit alarm and request the ERROR transition (idempotent while armed).

        Continuous detection collapses to one alarm event and one
        transition request per UT-006.2-17. The warning-armed flag is
        also cleared here so a Warning result observed *after* Detected
        (without an intervening Healthy / Degraded) does not produce a
        spurious warning record while we are already escalating.
        """
        if not self._alarm_armed:
            return
        event = AlarmEvent(
            alarm_id=_ALARM_ID_AIR_BUBBLE,
            priority=AlarmPriority.HIGH,
            category=AlarmCategory.TECHNICAL,
            occurred_at=self._clock(),
            cause_code=_CAUSE_CODE_AIR_BUBBLE,
            metadata={"triggering_value": result.triggering_value},
        )
        try:
            self._alarm_reporter.report_alarm(event)
        except Exception:  # noqa: BLE001 — SEP-003 catch-all
            _logger.warning(
                "alarm reporter raised; continuing to state-transition request",
                exc_info=True,
            )
        self._alarm_armed = False
        self._warning_armed = False
        self._state_machine.request_state_transition(
            TargetState.ERROR,
            reason=_REASON_DETECTED,
        )

    def _on_warning(self, result: Warning) -> None:
        """Record one warning entry while warning-armed.

        No alarm, no state transition — the warning stage is informational
        only (SDD §4.20). The alarm-armed flag is preserved so an
        immediately-following Detected tick (without an intervening
        Healthy) still escalates.
        """
        if not self._warning_armed:
            return
        try:
            self._warning_logger.log_warning(
                _DETECTOR_ID,
                threshold_value=self._warn_threshold,
                observed_value=result.triggering_value,
                occurred_at=self._clock(),
            )
        except Exception:  # noqa: BLE001 — SEP-003 catch-all
            _logger.warning("warning logger raised; continuing", exc_info=True)
        self._warning_armed = False

    def _on_failed(self) -> None:
        """Both channels lost — escalate without an alarm payload."""
        self._state_machine.request_state_transition(
            TargetState.ERROR,
            reason=_REASON_UNAVAILABLE,
        )
        # Re-arm both stages so that, on recovery, the next true
        # exceedance is reported.
        self._alarm_armed = True
        self._warning_armed = True
