"""Unit tests for UNIT-006.3 Reservoir Empty Detector (UTPR §7.3.21, Step 20 X7).

Scope frozen at the start of Step 20 X7 (see DEVELOPMENT_STEPS.md
"Step 20 X7 着手前ユーザ確認"):

* ``_evaluate`` pure threshold function over the single ``RESERVOIR``
  channel (UT-006.3-01..03, 03b, 11).
* ``tick`` orchestration: alarm-before-PAUSED-transition ordering on
  Empty (UT-006.3-04), the AlarmEvent content contract (UT-006.3-05),
  the no-op Healthy path (UT-006.3-06), the armed-idempotency contract
  (UT-006.3-07), re-arm after a healthy (refill) tick (UT-006.3-08),
  and the no-auto-RUNNING-recovery contract (UT-006.3-09).
* Sensor / reporter exception suppression contracts (SEP-003,
  UT-006.3-10, 13) and the sensor-failure ``Failed`` -> ERROR safe-side
  path (UT-006.3-12, 14).

Out of scope for Step 20 X7 (deferred):

* Hysteresis / chatter suppression (dual-threshold band) — SDD v0.8
  §4.21.G.x.
* Per-channel fault-detection internals (timeout / noise / out-of-range)
  — UNIT-002.3 extension.
* Threshold validation against bench data — SDD v0.8;
  :data:`RESERVOIR_EMPTY_THRESHOLD` is a placeholder scale.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

import pytest

from vip_detection.protocols import (
    AlarmEvent,
    AlarmPriority,
    SensorKind,
    SensorReading,
    TargetState,
)
from vip_detection.reservoir import (
    RESERVOIR_EMPTY_THRESHOLD,
    Empty,
    Failed,
    Healthy,
    ReservoirEmptyDetector,
)

# ---------------------------------------------------------------------------
# Test fakes — minimal protocol implementations.
# ---------------------------------------------------------------------------


class _ScriptedSensorReader:
    """Sensor reader that returns a pre-scripted reading for RESERVOIR."""

    def __init__(
        self,
        reading: SensorReading,
        *,
        raises: bool = False,
    ) -> None:
        self._reading = reading
        self._raises = raises
        self.calls: list[SensorKind] = []

    def read_sensor(self, kind: SensorKind) -> SensorReading:
        self.calls.append(kind)
        if self._raises:
            msg = f"hardware fault on {kind.value}"
            raise RuntimeError(msg)
        return self._reading


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
class _RecordingStateMachine:
    calls: list[tuple[TargetState, str]] = field(default_factory=list)

    def request_state_transition(self, target: TargetState, *, reason: str) -> None:
        self.calls.append((target, reason))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


_THRESHOLD = RESERVOIR_EMPTY_THRESHOLD
_ABOVE = _THRESHOLD + Decimal(10)  # comfortably above empty
_BELOW = _THRESHOLD - Decimal(10)  # comfortably below empty


def _reading(value: Decimal, *, healthy: bool = True) -> SensorReading:
    return SensorReading(kind=SensorKind.RESERVOIR, value=value, healthy=healthy)


def _build_detector(
    reading: SensorReading,
    *,
    raises: bool = False,
    occurred_at: float = 0.0,
) -> tuple[ReservoirEmptyDetector, _RecordingReporter, _RecordingStateMachine]:
    reporter = _RecordingReporter()
    state_machine = _RecordingStateMachine()
    detector = ReservoirEmptyDetector(
        sensor_reader=_ScriptedSensorReader(reading, raises=raises),
        alarm_reporter=reporter,
        state_machine=state_machine,
        clock=lambda: occurred_at,
    )
    return detector, reporter, state_machine


# ---------------------------------------------------------------------------
# UT-006.3-01..03 — _evaluate threshold matrix (parametrized).
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("value", "expected_cls"),
    [
        pytest.param(_ABOVE, Healthy, id="UT-006.3-01_above_threshold_healthy"),
        pytest.param(_THRESHOLD, Empty, id="UT-006.3-02_at_threshold_empty_inclusive"),
        pytest.param(_BELOW, Empty, id="UT-006.3-03_below_threshold_empty"),
    ],
)
def test_evaluate_threshold_matrix(value: Decimal, expected_cls: type) -> None:
    """Reservoir at or below the threshold counts as Empty; ``<=`` is inclusive."""
    detector, *_ = _build_detector(_reading(value))
    result = detector._evaluate(_reading(value))  # noqa: SLF001 — pure fn tested directly
    assert isinstance(result, expected_cls)


def test_evaluate_empty_carries_reservoir_value() -> None:
    """UT-006.3-03b — Empty reports the offending reservoir reading."""
    detector, *_ = _build_detector(_reading(_BELOW))
    result = detector._evaluate(_reading(_BELOW))  # noqa: SLF001
    assert isinstance(result, Empty)
    assert result.triggering_value == _BELOW


# ---------------------------------------------------------------------------
# UT-006.3-04 — Empty tick: alarm before PAUSED transition.
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


def test_tick_empty_reports_alarm_before_pause_transition() -> None:
    """UT-006.3-04 — alarm precedes the PAUSED transition on Empty (SDD §4.21)."""
    order: list[str] = []
    reporter = _TracingReporter(order)
    state_machine = _TracingStateMachine(order)
    detector = ReservoirEmptyDetector(
        sensor_reader=_ScriptedSensorReader(_reading(_BELOW)),
        alarm_reporter=reporter,
        state_machine=state_machine,
        clock=lambda: 0.0,
    )

    detector.tick()

    assert order == ["alarm", "transition"]
    assert state_machine.calls == [(TargetState.PAUSED, "reservoir_empty")]


# ---------------------------------------------------------------------------
# UT-006.3-05 — AlarmEvent contract on Empty.
# ---------------------------------------------------------------------------


def test_tick_alarm_event_matches_srs_alm_006_contract() -> None:
    """UT-006.3-05 — emitted AlarmEvent satisfies SRS-ALM-006 (MEDIUM / TECHNICAL)."""
    detector, reporter, _sm = _build_detector(_reading(_BELOW), occurred_at=51.5)
    detector.tick()
    assert len(reporter.events) == 1
    event = reporter.events[0]
    assert event.cause_code == "reservoir_empty"
    assert event.priority is AlarmPriority.MEDIUM
    assert event.category.value == "technical"
    assert event.occurred_at == pytest.approx(51.5)
    assert event.metadata["triggering_value"] == _BELOW


# ---------------------------------------------------------------------------
# UT-006.3-06 — Healthy tick: no alarm, no transition.
# ---------------------------------------------------------------------------


def test_tick_healthy_does_nothing() -> None:
    """UT-006.3-06 — a reservoir above threshold produces no side effects."""
    detector, reporter, state_machine = _build_detector(_reading(_ABOVE))
    detector.tick()
    assert reporter.events == []
    assert state_machine.calls == []


# ---------------------------------------------------------------------------
# UT-006.3-07 — armed idempotency under continuous Empty.
# ---------------------------------------------------------------------------


def test_tick_repeated_empty_emits_alarm_once() -> None:
    """UT-006.3-07 — two ticks under continuous Empty = one alarm, one PAUSED."""
    detector, reporter, state_machine = _build_detector(_reading(_BELOW))
    detector.tick()
    detector.tick()
    assert len(reporter.events) == 1
    assert len(state_machine.calls) == 1


# ---------------------------------------------------------------------------
# UT-006.3-08..09 — refill (return to Healthy) re-arms; no auto RUNNING.
# ---------------------------------------------------------------------------


class _StepReader:
    """Sensor reader that walks a per-tick reading sequence."""

    def __init__(self, readings: list[SensorReading]) -> None:
        self._readings = readings
        self._index = 0

    def read_sensor(self, kind: SensorKind) -> SensorReading:  # noqa: ARG002
        reading = self._readings[min(self._index, len(self._readings) - 1)]
        self._index += 1
        return reading


def test_tick_refill_re_arms_for_fresh_detection() -> None:
    """UT-006.3-08 — Empty -> refill (Healthy) -> Empty fires a fresh alarm."""
    reporter = _RecordingReporter()
    state_machine = _RecordingStateMachine()
    detector = ReservoirEmptyDetector(
        sensor_reader=_StepReader(
            [
                _reading(_BELOW),  # empty #1
                _reading(_ABOVE),  # refilled -> re-arm
                _reading(_BELOW),  # empty #2
            ],
        ),
        alarm_reporter=reporter,
        state_machine=state_machine,
        clock=lambda: 0.0,
    )
    for _ in range(3):
        detector.tick()
    assert len(reporter.events) == 2
    assert len(state_machine.calls) == 2


def test_tick_refill_never_requests_running_recovery() -> None:
    """UT-006.3-09 — the detector never auto-recovers; refill requests no RUNNING.

    After an Empty -> refill sequence the operator must explicitly resume
    (IEC 60601-1-8 §6.4). The detector's only transition target is PAUSED;
    a return to Healthy re-arms it silently without any transition request.
    """
    reporter = _RecordingReporter()
    state_machine = _RecordingStateMachine()
    detector = ReservoirEmptyDetector(
        sensor_reader=_StepReader(
            [
                _reading(_BELOW),  # empty -> PAUSED
                _reading(_ABOVE),  # refilled -> silent re-arm, NO transition
                _reading(_BELOW),  # empty again -> PAUSED
            ],
        ),
        alarm_reporter=reporter,
        state_machine=state_machine,
        clock=lambda: 0.0,
    )
    for _ in range(3):
        detector.tick()
    # Every transition request is PAUSED — the detector has no RUNNING path.
    assert state_machine.calls == [
        (TargetState.PAUSED, "reservoir_empty"),
        (TargetState.PAUSED, "reservoir_empty"),
    ]


# ---------------------------------------------------------------------------
# UT-006.3-10 — SEP-003 boundary: reporter exception.
# ---------------------------------------------------------------------------


def test_tick_reporter_exception_does_not_block_pause_transition() -> None:
    """UT-006.3-10 — SEP-003: reporter failure must not stop the PAUSED request."""
    reporter = _RaisingReporter()
    state_machine = _RecordingStateMachine()
    detector = ReservoirEmptyDetector(
        sensor_reader=_ScriptedSensorReader(_reading(_BELOW)),
        alarm_reporter=reporter,
        state_machine=state_machine,
        clock=lambda: 0.0,
    )

    detector.tick()  # must not raise

    assert len(reporter.events) == 1
    assert state_machine.calls == [(TargetState.PAUSED, "reservoir_empty")]


# ---------------------------------------------------------------------------
# UT-006.3-11..12 — sensor-failure Failed -> ERROR safe-side path.
# ---------------------------------------------------------------------------


def test_evaluate_unhealthy_reading_returns_failed() -> None:
    """UT-006.3-11 — an unhealthy reservoir reading evaluates to Failed."""
    detector, *_ = _build_detector(_reading(_BELOW, healthy=False))
    result = detector._evaluate(_reading(_BELOW, healthy=False))  # noqa: SLF001
    assert isinstance(result, Failed)


def test_tick_failed_requests_error_without_alarm() -> None:
    """UT-006.3-12 — Failed tick escalates to ERROR; no alarm, distinct reason."""
    detector, reporter, state_machine = _build_detector(_reading(_BELOW, healthy=False))
    detector.tick()
    assert reporter.events == []
    assert state_machine.calls == [
        (TargetState.ERROR, "reservoir_detection_unavailable"),
    ]


# ---------------------------------------------------------------------------
# UT-006.3-13 — SEP-003 boundary: sensor-read exception -> Failed.
# ---------------------------------------------------------------------------


def test_tick_swallows_sensor_exception_and_escalates_to_failed() -> None:
    """UT-006.3-13 — a raising sensor is funnelled into the Failed branch."""
    detector, reporter, state_machine = _build_detector(
        _reading(_BELOW),  # value ignored, the reader raises
        raises=True,
    )
    detector.tick()  # must not raise
    assert reporter.events == []
    assert state_machine.calls == [
        (TargetState.ERROR, "reservoir_detection_unavailable"),
    ]


# ---------------------------------------------------------------------------
# UT-006.3-14 — Failed re-arms: recovery to Empty fires a fresh alarm.
# ---------------------------------------------------------------------------


def test_tick_failed_re_arms_for_subsequent_empty() -> None:
    """UT-006.3-14 — Empty -> Failed -> Empty: the Failed tick re-arms the detector.

    A sensor fault must not silence a genuine reservoir-empty condition
    observed after the sensor recovers.
    """
    reporter = _RecordingReporter()
    state_machine = _RecordingStateMachine()
    detector = ReservoirEmptyDetector(
        sensor_reader=_StepReader(
            [
                _reading(_BELOW),  # empty #1 -> PAUSED, disarm
                _reading(_BELOW, healthy=False),  # sensor fault -> ERROR, re-arm
                _reading(_BELOW),  # empty #2 -> PAUSED again
            ],
        ),
        alarm_reporter=reporter,
        state_machine=state_machine,
        clock=lambda: 0.0,
    )
    for _ in range(3):
        detector.tick()
    assert len(reporter.events) == 2
    assert state_machine.calls == [
        (TargetState.PAUSED, "reservoir_empty"),
        (TargetState.ERROR, "reservoir_detection_unavailable"),
        (TargetState.PAUSED, "reservoir_empty"),
    ]
