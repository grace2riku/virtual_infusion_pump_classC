"""Unit tests for UNIT-006.2 Air-Bubble Detector (UTPR §7.3.20, Step 20 X4).

Scope frozen at the start of Step 20 X4 (see DEVELOPMENT_STEPS.md
"Step 20 X4 設計判断"):

* ``_evaluate`` pure decision function over the multi-stage (warning +
  critical) thresholds (UT-006.2-01..09).
* ``tick`` orchestration covering alarm-then-transition ordering on
  detected, warning-only logging, the idempotency contract, and the
  alarm/warning re-arm behaviour after a healthy tick
  (UT-006.2-10..18).
* Sensor / reporter / warning-logger exception suppression contracts
  (UT-006.2-15/16, 19/20).

Out of scope for Step 20 X4 (deferred):

* Warning-state hold time / continuous-warning-to-critical timing
  contract — SDD v0.7 §4.20.G.x.
* Per-channel fault-detection internals (timeout / noise / consecutive
  error counts) — UNIT-002.3 extension.
* Threshold validation against bench data — SDD v0.7.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import TYPE_CHECKING

import pytest

from vip_detection.air_bubble import (
    AIR_BUBBLE_CRITICAL_THRESHOLD,
    AIR_BUBBLE_WARN_THRESHOLD,
    AirBubbleDetector,
    Degraded,
    Detected,
    Failed,
    Healthy,
    Warning,  # noqa: A004 — SDD §4.20 names this stage "Warning"; shadow deliberate
)
from vip_detection.protocols import (
    AlarmEvent,
    AlarmPriority,
    SensorKind,
    SensorReading,
    TargetState,
)

if TYPE_CHECKING:
    from collections.abc import Mapping


# ---------------------------------------------------------------------------
# Test fakes — minimal protocol implementations.
# ---------------------------------------------------------------------------


class _ScriptedSensorReader:
    """Sensor reader that returns pre-scripted readings per channel."""

    def __init__(
        self,
        readings: Mapping[SensorKind, SensorReading],
        *,
        raises: set[SensorKind] | None = None,
    ) -> None:
        self._readings = dict(readings)
        self._raises = raises or set()
        self.calls: list[SensorKind] = []

    def read_sensor(self, kind: SensorKind) -> SensorReading:
        self.calls.append(kind)
        if kind in self._raises:
            msg = f"hardware fault on {kind.value}"
            raise RuntimeError(msg)
        return self._readings[kind]


@dataclass(slots=True)
class _RecordingReporter:
    events: list[AlarmEvent] = field(default_factory=list)

    def report_alarm(self, event: AlarmEvent) -> None:
        self.events.append(event)


@dataclass(slots=True)
class _RaisingReporter:
    """Reporter that always raises — exercises the SEP-003 contract."""

    events: list[AlarmEvent] = field(default_factory=list)

    def report_alarm(self, event: AlarmEvent) -> None:
        self.events.append(event)
        msg = "reporter unavailable"
        raise RuntimeError(msg)


@dataclass(slots=True)
class _WarningRecord:
    detector_id: str
    threshold_value: Decimal
    observed_value: Decimal
    occurred_at: float


@dataclass(slots=True)
class _RecordingWarningLogger:
    records: list[_WarningRecord] = field(default_factory=list)

    def log_warning(
        self,
        detector_id: str,
        *,
        threshold_value: Decimal,
        observed_value: Decimal,
        occurred_at: float,
    ) -> None:
        self.records.append(
            _WarningRecord(
                detector_id=detector_id,
                threshold_value=threshold_value,
                observed_value=observed_value,
                occurred_at=occurred_at,
            ),
        )


@dataclass(slots=True)
class _RaisingWarningLogger:
    """WarningLogger that always raises — exercises the SEP-003 contract."""

    records: list[_WarningRecord] = field(default_factory=list)

    def log_warning(
        self,
        detector_id: str,
        *,
        threshold_value: Decimal,
        observed_value: Decimal,
        occurred_at: float,
    ) -> None:
        self.records.append(
            _WarningRecord(
                detector_id=detector_id,
                threshold_value=threshold_value,
                observed_value=observed_value,
                occurred_at=occurred_at,
            ),
        )
        msg = "warning logger unavailable"
        raise RuntimeError(msg)


@dataclass(slots=True)
class _RecordingStateMachine:
    calls: list[tuple[TargetState, str]] = field(default_factory=list)

    def request_state_transition(self, target: TargetState, *, reason: str) -> None:
        self.calls.append((target, reason))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


_WARN = AIR_BUBBLE_WARN_THRESHOLD
_CRIT = AIR_BUBBLE_CRITICAL_THRESHOLD
_BELOW_WARN = _WARN - Decimal(10)
_BETWEEN = _WARN + Decimal(10)  # >= warn, < critical
_ABOVE_CRIT = _CRIT + Decimal(10)


def _reading(kind: SensorKind, value: Decimal, *, healthy: bool = True) -> SensorReading:
    return SensorReading(kind=kind, value=value, healthy=healthy)


def _both(warn: Decimal, critical: Decimal) -> dict[SensorKind, SensorReading]:
    return {
        SensorKind.AIR_BUBBLE_WARN: _reading(SensorKind.AIR_BUBBLE_WARN, warn),
        SensorKind.AIR_BUBBLE_CRITICAL: _reading(SensorKind.AIR_BUBBLE_CRITICAL, critical),
    }


def _build_detector(
    readings: Mapping[SensorKind, SensorReading],
    *,
    raises: set[SensorKind] | None = None,
    occurred_at: float = 0.0,
) -> tuple[
    AirBubbleDetector,
    _RecordingReporter,
    _RecordingWarningLogger,
    _RecordingStateMachine,
]:
    reporter = _RecordingReporter()
    warning_logger = _RecordingWarningLogger()
    state_machine = _RecordingStateMachine()
    detector = AirBubbleDetector(
        sensor_reader=_ScriptedSensorReader(readings, raises=raises),
        alarm_reporter=reporter,
        warning_logger=warning_logger,
        state_machine=state_machine,
        clock=lambda: occurred_at,
    )
    return detector, reporter, warning_logger, state_machine


# ---------------------------------------------------------------------------
# UT-006.2-01..04 — _evaluate threshold matrix (parametrized).
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("warn_value", "critical_value", "expected_cls"),
    [
        pytest.param(_BELOW_WARN, _BELOW_WARN, Healthy, id="UT-006.2-01_both_below"),
        pytest.param(_BETWEEN, _BELOW_WARN, Warning, id="UT-006.2-02_warn_only"),
        pytest.param(_BELOW_WARN, _ABOVE_CRIT, Detected, id="UT-006.2-03_critical_only"),
        pytest.param(_BETWEEN, _ABOVE_CRIT, Detected, id="UT-006.2-04_both_above_critical_wins"),
    ],
)
def test_evaluate_multistage_threshold_matrix(
    warn_value: Decimal,
    critical_value: Decimal,
    expected_cls: type,
) -> None:
    """Critical takes precedence; warning fires only when critical stays low."""
    detector, *_ = _build_detector(_both(warn_value, critical_value))
    result = detector._evaluate(  # noqa: SLF001 — pure function tested directly
        _reading(SensorKind.AIR_BUBBLE_WARN, warn_value),
        _reading(SensorKind.AIR_BUBBLE_CRITICAL, critical_value),
    )
    assert isinstance(result, expected_cls)


def test_evaluate_detected_carries_critical_value() -> None:
    """UT-006.2-04b — Detected reports the critical sensor's reading.

    Even when warning is also exceeded (UT-006.2-04 path), the offending
    value handed to the alarm path is the *critical* one — the warning
    channel is informational only at that point.
    """
    detector, *_ = _build_detector(_both(_BETWEEN, _ABOVE_CRIT))
    result = detector._evaluate(  # noqa: SLF001
        _reading(SensorKind.AIR_BUBBLE_WARN, _BETWEEN),
        _reading(SensorKind.AIR_BUBBLE_CRITICAL, _ABOVE_CRIT),
    )
    assert isinstance(result, Detected)
    assert result.triggering_value == _ABOVE_CRIT


def test_evaluate_warning_carries_warn_value() -> None:
    """UT-006.2-04c — Warning carries the warning sensor's reading."""
    detector, *_ = _build_detector(_both(_BETWEEN, _BELOW_WARN))
    result = detector._evaluate(  # noqa: SLF001
        _reading(SensorKind.AIR_BUBBLE_WARN, _BETWEEN),
        _reading(SensorKind.AIR_BUBBLE_CRITICAL, _BELOW_WARN),
    )
    assert isinstance(result, Warning)
    assert result.triggering_value == _BETWEEN


# ---------------------------------------------------------------------------
# UT-006.2-05..06 — threshold boundary (inclusive).
# ---------------------------------------------------------------------------


def test_evaluate_warning_boundary_inclusive() -> None:
    """UT-006.2-05 — warn == warning threshold counts as exceedance."""
    detector, *_ = _build_detector(_both(_WARN, _BELOW_WARN))
    result = detector._evaluate(  # noqa: SLF001
        _reading(SensorKind.AIR_BUBBLE_WARN, _WARN),
        _reading(SensorKind.AIR_BUBBLE_CRITICAL, _BELOW_WARN),
    )
    assert isinstance(result, Warning)


def test_evaluate_critical_boundary_inclusive() -> None:
    """UT-006.2-06 — critical == critical threshold counts as exceedance."""
    detector, *_ = _build_detector(_both(_BELOW_WARN, _CRIT))
    result = detector._evaluate(  # noqa: SLF001
        _reading(SensorKind.AIR_BUBBLE_WARN, _BELOW_WARN),
        _reading(SensorKind.AIR_BUBBLE_CRITICAL, _CRIT),
    )
    assert isinstance(result, Detected)


# ---------------------------------------------------------------------------
# UT-006.2-07 — stage independence (critical fires regardless of warn).
# ---------------------------------------------------------------------------


def test_evaluate_stage_independence_critical_ignores_warn() -> None:
    """UT-006.2-07 — critical decision uses only the critical sensor (SDD §4.20).

    A pathologically low warning sensor must not mask the critical
    sensor's decision; the two stages are independent inputs.
    """
    detector, *_ = _build_detector(_both(Decimal(-1000), _ABOVE_CRIT))
    result = detector._evaluate(  # noqa: SLF001
        _reading(SensorKind.AIR_BUBBLE_WARN, Decimal(-1000)),
        _reading(SensorKind.AIR_BUBBLE_CRITICAL, _ABOVE_CRIT),
    )
    assert isinstance(result, Detected)


# ---------------------------------------------------------------------------
# UT-006.2-08..09 — single-channel degradation.
# ---------------------------------------------------------------------------


def test_evaluate_warn_channel_failed_returns_degraded() -> None:
    """UT-006.2-08 — warn unhealthy, critical below: Degraded(WARN)."""
    detector, *_ = _build_detector({})
    result = detector._evaluate(  # noqa: SLF001
        _reading(SensorKind.AIR_BUBBLE_WARN, _ABOVE_CRIT, healthy=False),
        _reading(SensorKind.AIR_BUBBLE_CRITICAL, _BELOW_WARN),
    )
    assert isinstance(result, Degraded)
    assert result.failed_channel is SensorKind.AIR_BUBBLE_WARN


def test_evaluate_critical_channel_failed_returns_degraded() -> None:
    """UT-006.2-09 — critical unhealthy, warn below: Degraded(CRITICAL).

    The warn channel cannot substitute for the critical channel, so this
    yields Degraded rather than Failed — detection downgraded but not
    fully unavailable.
    """
    detector, *_ = _build_detector({})
    result = detector._evaluate(  # noqa: SLF001
        _reading(SensorKind.AIR_BUBBLE_WARN, _BELOW_WARN),
        _reading(SensorKind.AIR_BUBBLE_CRITICAL, _ABOVE_CRIT, healthy=False),
    )
    assert isinstance(result, Degraded)
    assert result.failed_channel is SensorKind.AIR_BUBBLE_CRITICAL


# ---------------------------------------------------------------------------
# UT-006.2-10..11 — both channels failed.
# ---------------------------------------------------------------------------


def test_evaluate_both_failed_returns_failed_safe_side() -> None:
    """UT-006.2-10 — both channels unhealthy returns Failed."""
    detector, *_ = _build_detector({})
    result = detector._evaluate(  # noqa: SLF001
        _reading(SensorKind.AIR_BUBBLE_WARN, _BELOW_WARN, healthy=False),
        _reading(SensorKind.AIR_BUBBLE_CRITICAL, _BELOW_WARN, healthy=False),
    )
    assert isinstance(result, Failed)


def test_tick_both_failed_requests_error_without_alarm_or_warning() -> None:
    """UT-006.2-11 — Failed tick escalates to ERROR; no alarm, no warning log."""
    readings = {
        SensorKind.AIR_BUBBLE_WARN: _reading(
            SensorKind.AIR_BUBBLE_WARN,
            _BELOW_WARN,
            healthy=False,
        ),
        SensorKind.AIR_BUBBLE_CRITICAL: _reading(
            SensorKind.AIR_BUBBLE_CRITICAL,
            _BELOW_WARN,
            healthy=False,
        ),
    }
    detector, reporter, warning_logger, state_machine = _build_detector(readings)
    detector.tick()
    assert reporter.events == []
    assert warning_logger.records == []
    assert state_machine.calls == [(TargetState.ERROR, "air_bubble_detection_unavailable")]


# ---------------------------------------------------------------------------
# UT-006.2-12 — Detected: alarm-before-transition ordering.
# ---------------------------------------------------------------------------


class _TracingReporter:
    """Reporter variant that appends to a shared order trace."""

    def __init__(self, trace: list[str]) -> None:
        self.events: list[AlarmEvent] = []
        self._trace = trace

    def report_alarm(self, event: AlarmEvent) -> None:
        self._trace.append("alarm")
        self.events.append(event)


class _TracingStateMachine:
    """State-machine variant that appends to a shared order trace."""

    def __init__(self, trace: list[str]) -> None:
        self.calls: list[tuple[TargetState, str]] = []
        self._trace = trace

    def request_state_transition(self, target: TargetState, *, reason: str) -> None:
        self._trace.append("transition")
        self.calls.append((target, reason))


def test_tick_detection_reports_alarm_before_state_transition() -> None:
    """UT-006.2-12 — alarm precedes the ERROR transition on Detected (SDD §4.20)."""
    order: list[str] = []
    reporter = _TracingReporter(order)
    state_machine = _TracingStateMachine(order)
    detector = AirBubbleDetector(
        sensor_reader=_ScriptedSensorReader(_both(_BETWEEN, _ABOVE_CRIT)),
        alarm_reporter=reporter,
        warning_logger=_RecordingWarningLogger(),
        state_machine=state_machine,
        clock=lambda: 0.0,
    )

    detector.tick()

    assert order == ["alarm", "transition"]
    assert state_machine.calls == [(TargetState.ERROR, "air_bubble_detected")]


# ---------------------------------------------------------------------------
# UT-006.2-13 — Warning tick: logger only, no alarm, no transition.
# ---------------------------------------------------------------------------


def test_tick_warning_logs_only() -> None:
    """UT-006.2-13 — warning-only stage records via WarningLogger, nothing else."""
    detector, reporter, warning_logger, state_machine = _build_detector(
        _both(_BETWEEN, _BELOW_WARN),
        occurred_at=12.5,
    )
    detector.tick()
    assert reporter.events == []
    assert state_machine.calls == []
    assert len(warning_logger.records) == 1
    record = warning_logger.records[0]
    assert record.detector_id == "UNIT-006.2"
    assert record.threshold_value == _WARN
    assert record.observed_value == _BETWEEN
    assert record.occurred_at == pytest.approx(12.5)


# ---------------------------------------------------------------------------
# UT-006.2-14 — AlarmEvent contract on Detected.
# ---------------------------------------------------------------------------


def test_tick_alarm_event_matches_srs_alm_005_contract() -> None:
    """UT-006.2-14 — emitted AlarmEvent satisfies SRS-ALM-005 (HIGH / TECHNICAL)."""
    detector, reporter, _wl, _sm = _build_detector(
        _both(_BELOW_WARN, _ABOVE_CRIT),
        occurred_at=99.25,
    )
    detector.tick()
    assert len(reporter.events) == 1
    event = reporter.events[0]
    assert event.cause_code == "air_bubble"
    assert event.priority is AlarmPriority.HIGH
    assert event.category.value == "technical"
    assert event.occurred_at == pytest.approx(99.25)


# ---------------------------------------------------------------------------
# UT-006.2-15..16 — SEP-003 boundary: reporter / warning-logger exceptions.
# ---------------------------------------------------------------------------


def test_tick_reporter_exception_does_not_block_state_transition() -> None:
    """UT-006.2-15 — SEP-003: reporter failure must not stop ERROR escalation."""
    reporter = _RaisingReporter()
    state_machine = _RecordingStateMachine()
    detector = AirBubbleDetector(
        sensor_reader=_ScriptedSensorReader(_both(_BELOW_WARN, _ABOVE_CRIT)),
        alarm_reporter=reporter,
        warning_logger=_RecordingWarningLogger(),
        state_machine=state_machine,
        clock=lambda: 0.0,
    )

    detector.tick()  # must not raise

    assert len(reporter.events) == 1
    assert state_machine.calls == [(TargetState.ERROR, "air_bubble_detected")]


def test_tick_warning_logger_exception_does_not_disrupt_subsequent_tick() -> None:
    """UT-006.2-16 — SEP-003: a raising WarningLogger must not crash the tick.

    The next tick (with the same warning-only readings, idempotency
    already triggered) still runs to completion without raising.
    """
    warning_logger = _RaisingWarningLogger()
    detector = AirBubbleDetector(
        sensor_reader=_ScriptedSensorReader(_both(_BETWEEN, _BELOW_WARN)),
        alarm_reporter=_RecordingReporter(),
        warning_logger=warning_logger,
        state_machine=_RecordingStateMachine(),
        clock=lambda: 0.0,
    )

    detector.tick()  # records one warning, raises internally — suppressed
    detector.tick()  # idempotent: warning_armed=False, must not retry the logger

    assert len(warning_logger.records) == 1


# ---------------------------------------------------------------------------
# UT-006.2-17..18 — idempotency for both severity stages.
# ---------------------------------------------------------------------------


def test_tick_repeated_detection_emits_alarm_once() -> None:
    """UT-006.2-17 — two ticks under continuous Detected = one alarm event."""
    detector, reporter, _wl, state_machine = _build_detector(_both(_BELOW_WARN, _ABOVE_CRIT))
    detector.tick()
    detector.tick()
    assert len(reporter.events) == 1
    assert len(state_machine.calls) == 1


def test_tick_repeated_warning_logs_once_until_cleared() -> None:
    """UT-006.2-18 — continuous warning collapses to one logger record."""
    detector, _r, warning_logger, _sm = _build_detector(_both(_BETWEEN, _BELOW_WARN))
    detector.tick()
    detector.tick()
    detector.tick()
    assert len(warning_logger.records) == 1


def test_tick_idempotency_resets_on_return_to_healthy() -> None:
    """UT-006.2-19 — after Healthy, both alarm- and warning-armed reset.

    Sequence: warning -> detected -> healthy -> detected -> warning.
    All four signal-emitting transitions must produce fresh records on
    each re-entry; a Healthy tick re-arms both severity stages.
    """
    readings_sequence: list[dict[SensorKind, SensorReading]] = [
        _both(_BETWEEN, _BELOW_WARN),  # warning #1
        _both(_BELOW_WARN, _ABOVE_CRIT),  # detected #1
        _both(_BELOW_WARN, _BELOW_WARN),  # healthy -> re-arm both
        _both(_BELOW_WARN, _ABOVE_CRIT),  # detected #2
        _both(_BELOW_WARN, _BELOW_WARN),  # healthy -> re-arm both
        _both(_BETWEEN, _BELOW_WARN),  # warning #2
    ]

    class _StepReader:
        def __init__(self) -> None:
            self._index = 0

        def read_sensor(self, kind: SensorKind) -> SensorReading:
            step = readings_sequence[min(self._index, len(readings_sequence) - 1)]
            reading = step[kind]
            if kind is SensorKind.AIR_BUBBLE_CRITICAL:
                self._index += 1
            return reading

    reporter = _RecordingReporter()
    warning_logger = _RecordingWarningLogger()
    state_machine = _RecordingStateMachine()
    detector = AirBubbleDetector(
        sensor_reader=_StepReader(),
        alarm_reporter=reporter,
        warning_logger=warning_logger,
        state_machine=state_machine,
        clock=lambda: 0.0,
    )
    for _ in range(len(readings_sequence)):
        detector.tick()

    assert len(reporter.events) == 2
    assert len(state_machine.calls) == 2
    assert len(warning_logger.records) == 2


# ---------------------------------------------------------------------------
# UT-006.2-20 — sensor-read exception suppression.
# ---------------------------------------------------------------------------


def test_tick_swallows_all_sensor_exceptions_and_escalates_to_failed() -> None:
    """UT-006.2-20 — both sensors raising is funnelled into the Failed branch."""
    detector, reporter, warning_logger, state_machine = _build_detector(
        _both(_ABOVE_CRIT, _ABOVE_CRIT),  # values ignored, both raise
        raises={SensorKind.AIR_BUBBLE_WARN, SensorKind.AIR_BUBBLE_CRITICAL},
    )
    detector.tick()  # must not raise
    assert reporter.events == []
    assert warning_logger.records == []
    assert state_machine.calls == [(TargetState.ERROR, "air_bubble_detection_unavailable")]
