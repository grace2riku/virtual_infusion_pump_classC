"""UNIT-006.1 Occlusion Detector (SDD-VIP-001 v0.5 §4.19, RCM-009).

Detects intravenous-line occlusion from two independent pressure sensor
channels (``OCCLUSION_PRIMARY`` / ``OCCLUSION_SECONDARY``). Whenever
either channel reports a healthy reading at or above the configured
threshold, the detector emits ``SRS-ALM-004`` (HIGH / TECHNICAL) via the
injected :class:`~vip_detection.protocols.AlarmReporter` and requests an
``ERROR`` state transition from the State Machine.

Step 20 X scope (this commit, Inc.2 TDD seed):

* Pure threshold logic in :func:`_evaluate` (UT-006.1-01..11).
* ``tick`` orchestration: alarm-before-transition ordering
  (UT-006.1-12..14), continuous-detection idempotency (UT-006.1-15..16),
  sensor-exception suppression (UT-006.1-17..18).
* All dependencies (sensor reader, alarm reporter, state machine, clock)
  are injected so unit tests run without the rest of Inc.2 yet wired in.

Out of scope for Step 20 X (deferred to SDD v0.6 / later Step):

* Per-channel fault-detection internals (timeout / noise / consecutive
  error counts) — currently encoded as a single boolean on
  :class:`~vip_detection.protocols.SensorReading.healthy`.
* Concurrent-``tick`` resilience (UT-006.1-19+).
* Tick-period validation against the SDD v0.6 final cadence.
* Final threshold value confirmation against bench data —
  :data:`OCCLUSION_PRESSURE_THRESHOLD_KPA` is a clinically representative
  placeholder pending SDD v0.6.

Related SRS: SRS-040, SRS-RCM-009, SRS-ALM-004, SRS-IF-010.
Related RCM: RCM-009 (occlusion-detection redundancy).
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
    )

__all__ = [
    "OCCLUSION_PRESSURE_THRESHOLD_KPA",
    "Degraded",
    "Detected",
    "DetectionResult",
    "Failed",
    "Healthy",
    "OcclusionDetector",
]


# ---------------------------------------------------------------------------
# Constants (placeholder values — confirmation in SDD v0.6).
# ---------------------------------------------------------------------------


OCCLUSION_PRESSURE_THRESHOLD_KPA: Final[Decimal] = Decimal(90)
"""Pressure threshold above which a channel is considered to indicate occlusion.

Placeholder value pending SDD v0.6 confirmation against bench data;
chosen as a clinically representative downstream-occlusion alarm
threshold for syringe / volumetric pumps. The unit is kPa to match the
SAD v0.2 §5 IF-U-015 convention.
"""


_ALARM_ID_OCCLUSION: Final[str] = "ALM-OCC"
_CAUSE_CODE_OCCLUSION: Final[str] = "occlusion"
_REASON_DETECTED: Final[str] = "occlusion_detected"
_REASON_UNAVAILABLE: Final[str] = "occlusion_detection_unavailable"


_logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Sealed DetectionResult hierarchy (4 variants).
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Healthy:
    """Both channels healthy and below threshold."""


@dataclass(frozen=True, slots=True)
class Detected:
    """At least one healthy channel exceeded the threshold (SRS-040)."""

    triggering_channels: frozenset[SensorKind]


@dataclass(frozen=True, slots=True)
class Degraded:
    """One channel unhealthy; the surviving channel reports below threshold.

    Monitoring continues on the surviving channel (RCM-009 redundancy).
    """

    failed_channel: SensorKind


@dataclass(frozen=True, slots=True)
class Failed:
    """Both channels unhealthy — detection cannot be performed (safe-side).

    Triggers an ``ERROR`` transition request without emitting an alarm,
    since a fabricated alarm without sensor evidence would be misleading.
    """


DetectionResult = Healthy | Detected | Degraded | Failed
"""Sealed result of one redundant-pair evaluation."""


# ---------------------------------------------------------------------------
# Detector unit (UNIT-006.1).
# ---------------------------------------------------------------------------


class OcclusionDetector:
    """Redundant-pair occlusion detector (UNIT-006.1).

    The detector owns no persistent sensor state; it relies on the
    injected :class:`SensorReader` for the per-tick snapshot. The only
    internal state is ``_alarm_armed`` which guarantees the idempotency
    contract documented in UTPR §7.3.19 UT-006.1-15/16.
    """

    def __init__(
        self,
        *,
        sensor_reader: SensorReader,
        alarm_reporter: AlarmReporter,
        state_machine: StateTransitionRequester,
        clock: Callable[[], float] = time.monotonic,
        threshold_kpa: Decimal = OCCLUSION_PRESSURE_THRESHOLD_KPA,
    ) -> None:
        """Wire the detector to its collaborators.

        Args:
            sensor_reader: IF-U-015 pull provider.
            alarm_reporter: IF-U-007 / IF-U-012 alarm sink.
            state_machine: IF-U-013 transition-request sink.
            clock: Monotonic seconds source used as ``AlarmEvent.occurred_at``.
            threshold_kpa: Per-channel pressure threshold. Defaults to
                :data:`OCCLUSION_PRESSURE_THRESHOLD_KPA`; tests pin a
                deterministic value via this argument.

        """
        self._sensor_reader = sensor_reader
        self._alarm_reporter = alarm_reporter
        self._state_machine = state_machine
        self._clock = clock
        self._threshold = threshold_kpa
        self._alarm_armed = True

    # ------------------------------------------------------------------
    # Public entry point — periodic tick driven by the control loop.
    # ------------------------------------------------------------------

    def tick(self) -> None:
        """Perform one detection cycle.

        Outline:

        1. Read both redundant channels (guarding against sensor faults).
        2. Evaluate the threshold logic (pure :func:`_evaluate`).
        3. Drive side effects per result type, preserving the
           alarm-before-transition order on Detected.
        """
        primary = self._safe_read(SensorKind.OCCLUSION_PRIMARY)
        secondary = self._safe_read(SensorKind.OCCLUSION_SECONDARY)
        result = self._evaluate(primary, secondary)
        self._apply(result)

    # ------------------------------------------------------------------
    # Pure decision logic (testable in isolation).
    # ------------------------------------------------------------------

    def _evaluate(
        self,
        primary: SensorReading,
        secondary: SensorReading,
    ) -> DetectionResult:
        """Threshold-evaluate one redundant pair (no side effects).

        Returns one of :class:`Healthy`, :class:`Detected`,
        :class:`Degraded`, :class:`Failed` per the RCM-009 redundancy
        contract.
        """
        primary_ok = primary.healthy
        secondary_ok = secondary.healthy

        if not primary_ok and not secondary_ok:
            return Failed()

        triggering: set[SensorKind] = set()
        if primary_ok and primary.value >= self._threshold:
            triggering.add(SensorKind.OCCLUSION_PRIMARY)
        if secondary_ok and secondary.value >= self._threshold:
            triggering.add(SensorKind.OCCLUSION_SECONDARY)

        if triggering:
            return Detected(triggering_channels=frozenset(triggering))

        if not primary_ok:
            return Degraded(failed_channel=SensorKind.OCCLUSION_PRIMARY)
        if not secondary_ok:
            return Degraded(failed_channel=SensorKind.OCCLUSION_SECONDARY)
        return Healthy()

    # ------------------------------------------------------------------
    # Internals.
    # ------------------------------------------------------------------

    def _safe_read(self, kind: SensorKind) -> SensorReading:
        """Read a channel, converting raised exceptions to ``healthy=False``.

        SEP-003 requires that sensor faults degrade detection rather than
        crash the periodic tick. The placeholder value handed to the
        :func:`_evaluate` decision logic is :class:`Decimal` zero — it is
        ignored when ``healthy=False`` but must still satisfy the dataclass
        type constraint.
        """
        try:
            return self._sensor_reader.read_sensor(kind)
        except Exception:  # noqa: BLE001 — SEP-003 catch-all is intentional
            _logger.warning("sensor read failed: kind=%s", kind.value, exc_info=True)
            return SensorReading(kind=kind, value=Decimal(0), healthy=False)

    def _apply(self, result: DetectionResult) -> None:
        """Drive side effects for a decision result."""
        if isinstance(result, Detected):
            self._on_detected()
            return
        if isinstance(result, Failed):
            self._on_failed()
            return
        # Healthy and Degraded both leave the alarm path quiet, but
        # transitioning back to a non-Detected result re-arms the alarm
        # so a subsequent recurrence is reported again (UT-006.1-16).
        self._alarm_armed = True

    def _on_detected(self) -> None:
        """Emit alarm and request the ERROR transition (idempotent while armed).

        Continuous detection (multiple consecutive ticks reporting
        Detected without an intervening Healthy / Degraded) collapses to
        one alarm event and one transition request per UT-006.1-15. The
        armed flag is reset by :meth:`_apply` whenever the result leaves
        the Detected branch.
        """
        if not self._alarm_armed:
            return
        event = AlarmEvent(
            alarm_id=_ALARM_ID_OCCLUSION,
            priority=AlarmPriority.HIGH,
            category=AlarmCategory.TECHNICAL,
            occurred_at=self._clock(),
            cause_code=_CAUSE_CODE_OCCLUSION,
        )
        try:
            self._alarm_reporter.report_alarm(event)
        except Exception:  # noqa: BLE001 — SEP-003 catch-all
            _logger.warning(
                "alarm reporter raised; continuing to state-transition request",
                exc_info=True,
            )
        self._alarm_armed = False
        self._state_machine.request_state_transition(
            TargetState.ERROR,
            reason=_REASON_DETECTED,
        )

    def _on_failed(self) -> None:
        """Both channels lost — escalate without an alarm payload."""
        self._state_machine.request_state_transition(
            TargetState.ERROR,
            reason=_REASON_UNAVAILABLE,
        )
        # Re-arm so that, if the sensors later recover and a real
        # detection occurs, the alarm is delivered.
        self._alarm_armed = True
