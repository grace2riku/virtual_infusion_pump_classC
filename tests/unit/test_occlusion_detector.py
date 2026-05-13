"""Unit tests for UNIT-006.1 Occlusion Detector (UTPR §7.3.19, Step 20 X).

Scope frozen at the start of Step 20 X (see DEVELOPMENT_STEPS.md
"Step 20 X 設計判断"):

* ``_evaluate`` pure decision function (UT-006.1-01..11).
* ``tick`` orchestration covering alarm-then-transition ordering and
  the idempotency contract (UT-006.1-12..16).
* Sensor-read exception suppression contract (UT-006.1-17..18).

Out of scope for Step 20 X (deferred to a later Step alongside SDD v0.6):

* UT-006.1-19+ concurrent-``tick`` resilience.
* Per-channel fault-detection internals (timeout / noise / consecutive
  error counts) — those live in UNIT-002.3 EventInjection extension.
* Threshold and tick-period validation against the SDD v0.6 final values.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from decimal import Decimal
from typing import TYPE_CHECKING

import pytest

from vip_detection.occlusion import (
    OCCLUSION_PRESSURE_THRESHOLD_KPA,
    Degraded,
    Detected,
    Failed,
    Healthy,
    OcclusionDetector,
)
from vip_detection.protocols import (
    AlarmEvent,
    AlarmPriority,
    SensorKind,
    SensorReading,
    TargetState,
)

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping


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
class _RecordingStateMachine:
    calls: list[tuple[TargetState, str]] = field(default_factory=list)

    def request_state_transition(self, target: TargetState, *, reason: str) -> None:
        self.calls.append((target, reason))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


_THRESHOLD = OCCLUSION_PRESSURE_THRESHOLD_KPA
_BELOW = _THRESHOLD - Decimal(10)
_ABOVE = _THRESHOLD + Decimal(10)
_AT = _THRESHOLD


def _reading(kind: SensorKind, value: Decimal, *, healthy: bool = True) -> SensorReading:
    return SensorReading(kind=kind, value=value, healthy=healthy)


def _both(primary: Decimal, secondary: Decimal) -> dict[SensorKind, SensorReading]:
    return {
        SensorKind.OCCLUSION_PRIMARY: _reading(SensorKind.OCCLUSION_PRIMARY, primary),
        SensorKind.OCCLUSION_SECONDARY: _reading(SensorKind.OCCLUSION_SECONDARY, secondary),
    }


def _build_detector(
    readings: Mapping[SensorKind, SensorReading],
    *,
    raises: set[SensorKind] | None = None,
    occurred_at: float = 0.0,
) -> tuple[OcclusionDetector, _RecordingReporter, _RecordingStateMachine]:
    reporter = _RecordingReporter()
    state_machine = _RecordingStateMachine()
    detector = OcclusionDetector(
        sensor_reader=_ScriptedSensorReader(readings, raises=raises),
        alarm_reporter=reporter,
        state_machine=state_machine,
        clock=lambda: occurred_at,
    )
    return detector, reporter, state_machine


# ---------------------------------------------------------------------------
# UT-006.1-01..04 — both sensors healthy, threshold decision (OR semantics).
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("primary", "secondary", "expected_cls"),
    [
        pytest.param(_BELOW, _BELOW, Healthy, id="UT-006.1-01_both_below"),
        pytest.param(_ABOVE, _BELOW, Detected, id="UT-006.1-02_primary_only"),
        pytest.param(_BELOW, _ABOVE, Detected, id="UT-006.1-03_secondary_only"),
        pytest.param(_ABOVE, _ABOVE, Detected, id="UT-006.1-04_both_above"),
    ],
)
def test_evaluate_both_healthy_or_logic(
    primary: Decimal,
    secondary: Decimal,
    expected_cls: type,
) -> None:
    """Either channel exceeding the threshold triggers Detected (SRS-040 OR)."""
    detector, _reporter, _sm = _build_detector(_both(primary, secondary))
    result = detector._evaluate(  # noqa: SLF001 — pure function tested directly
        _reading(SensorKind.OCCLUSION_PRIMARY, primary),
        _reading(SensorKind.OCCLUSION_SECONDARY, secondary),
    )
    assert isinstance(result, expected_cls)


def test_evaluate_detected_carries_offending_channel() -> None:
    """UT-006.1-02b — Detected names the channel(s) that triggered it."""
    detector, _r, _sm = _build_detector(_both(_ABOVE, _BELOW))
    result = detector._evaluate(  # noqa: SLF001
        _reading(SensorKind.OCCLUSION_PRIMARY, _ABOVE),
        _reading(SensorKind.OCCLUSION_SECONDARY, _BELOW),
    )
    assert isinstance(result, Detected)
    assert SensorKind.OCCLUSION_PRIMARY in result.triggering_channels
    assert SensorKind.OCCLUSION_SECONDARY not in result.triggering_channels


# ---------------------------------------------------------------------------
# UT-006.1-05..06 — threshold boundary.
# ---------------------------------------------------------------------------


def test_evaluate_threshold_boundary_inclusive_on_primary() -> None:
    """UT-006.1-05 — value == threshold counts as exceedance on primary."""
    detector, _r, _sm = _build_detector(_both(_AT, _BELOW))
    result = detector._evaluate(  # noqa: SLF001
        _reading(SensorKind.OCCLUSION_PRIMARY, _AT),
        _reading(SensorKind.OCCLUSION_SECONDARY, _BELOW),
    )
    assert isinstance(result, Detected)


def test_evaluate_threshold_boundary_inclusive_on_secondary() -> None:
    """UT-006.1-06 — value == threshold counts as exceedance on secondary."""
    detector, _r, _sm = _build_detector(_both(_BELOW, _AT))
    result = detector._evaluate(  # noqa: SLF001
        _reading(SensorKind.OCCLUSION_PRIMARY, _BELOW),
        _reading(SensorKind.OCCLUSION_SECONDARY, _AT),
    )
    assert isinstance(result, Detected)


# ---------------------------------------------------------------------------
# UT-006.1-07..09 — single-channel degradation (RCM-009 redundancy).
# ---------------------------------------------------------------------------


def test_evaluate_primary_failed_other_below_returns_degraded() -> None:
    """UT-006.1-07 — primary unhealthy, secondary below: Degraded, not detected."""
    detector, _r, _sm = _build_detector({})
    result = detector._evaluate(  # noqa: SLF001
        _reading(SensorKind.OCCLUSION_PRIMARY, _ABOVE, healthy=False),
        _reading(SensorKind.OCCLUSION_SECONDARY, _BELOW),
    )
    assert isinstance(result, Degraded)
    assert result.failed_channel is SensorKind.OCCLUSION_PRIMARY


def test_evaluate_secondary_failed_other_below_returns_degraded() -> None:
    """UT-006.1-08 — secondary unhealthy, primary below: Degraded mirror."""
    detector, _r, _sm = _build_detector({})
    result = detector._evaluate(  # noqa: SLF001
        _reading(SensorKind.OCCLUSION_PRIMARY, _BELOW),
        _reading(SensorKind.OCCLUSION_SECONDARY, _ABOVE, healthy=False),
    )
    assert isinstance(result, Degraded)
    assert result.failed_channel is SensorKind.OCCLUSION_SECONDARY


def test_evaluate_one_failed_other_exceeds_still_detects() -> None:
    """UT-006.1-09 — RCM-009: a failed channel must not mask the other's detection."""
    detector, _r, _sm = _build_detector({})
    result = detector._evaluate(  # noqa: SLF001
        _reading(SensorKind.OCCLUSION_PRIMARY, _BELOW, healthy=False),
        _reading(SensorKind.OCCLUSION_SECONDARY, _ABOVE),
    )
    assert isinstance(result, Detected)
    assert SensorKind.OCCLUSION_SECONDARY in result.triggering_channels


# ---------------------------------------------------------------------------
# UT-006.1-10..11 — both channels failed.
# ---------------------------------------------------------------------------


def test_evaluate_both_failed_returns_failed_safe_side() -> None:
    """UT-006.1-10 — both channels unhealthy returns Failed (safe-side)."""
    detector, _r, _sm = _build_detector({})
    result = detector._evaluate(  # noqa: SLF001
        _reading(SensorKind.OCCLUSION_PRIMARY, _BELOW, healthy=False),
        _reading(SensorKind.OCCLUSION_SECONDARY, _BELOW, healthy=False),
    )
    assert isinstance(result, Failed)


def test_tick_both_failed_requests_error_transition_without_alarm() -> None:
    """UT-006.1-11 — Failed escalates to ERROR transition; no alarm payload.

    Rationale: a Failed result means we cannot trust either reading, so a
    Detected alarm would be a fabrication. The State Machine handles the
    safe stop via the ERROR transition path.
    """
    readings = {
        SensorKind.OCCLUSION_PRIMARY: _reading(
            SensorKind.OCCLUSION_PRIMARY, _BELOW, healthy=False
        ),
        SensorKind.OCCLUSION_SECONDARY: _reading(
            SensorKind.OCCLUSION_SECONDARY, _BELOW, healthy=False
        ),
    }
    detector, reporter, state_machine = _build_detector(readings)
    detector.tick()
    assert state_machine.calls == [(TargetState.ERROR, "occlusion_detection_unavailable")]
    assert reporter.events == []


# ---------------------------------------------------------------------------
# UT-006.1-12..14 — tick: alarm-then-transition ordering on detection.
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
    """UT-006.1-12 — alarm goes out *before* the ERROR transition request.

    SAD v0.2 §11 / SDD §4.19: ordering guarantees the alarm path receives
    the event before the State Machine cuts off the control loop.
    """
    order: list[str] = []
    reporter = _TracingReporter(order)
    state_machine = _TracingStateMachine(order)
    detector = OcclusionDetector(
        sensor_reader=_ScriptedSensorReader(_both(_ABOVE, _BELOW)),
        alarm_reporter=reporter,
        state_machine=state_machine,
        clock=lambda: 0.0,
    )

    detector.tick()

    assert order == ["alarm", "transition"]
    assert state_machine.calls == [(TargetState.ERROR, "occlusion_detected")]


def test_tick_alarm_event_matches_srs_alm_004_contract() -> None:
    """UT-006.1-13 — emitted AlarmEvent satisfies SRS-ALM-004 (HIGH / TECHNICAL)."""
    detector, reporter, _sm = _build_detector(_both(_ABOVE, _BELOW), occurred_at=42.5)
    detector.tick()
    assert len(reporter.events) == 1
    event = reporter.events[0]
    assert event.cause_code == "occlusion"
    assert event.priority is AlarmPriority.HIGH
    assert event.category.value == "technical"
    assert event.occurred_at == pytest.approx(42.5)


def test_tick_reporter_exception_does_not_block_state_transition() -> None:
    """UT-006.1-14 — SEP-003: reporter failure must not stop the ERROR escalation."""
    reporter = _RaisingReporter()
    state_machine = _RecordingStateMachine()
    detector = OcclusionDetector(
        sensor_reader=_ScriptedSensorReader(_both(_ABOVE, _BELOW)),
        alarm_reporter=reporter,
        state_machine=state_machine,
        clock=lambda: 0.0,
    )

    detector.tick()  # must not raise

    assert len(reporter.events) == 1
    assert state_machine.calls == [(TargetState.ERROR, "occlusion_detected")]


# ---------------------------------------------------------------------------
# UT-006.1-15..16 — idempotency.
# ---------------------------------------------------------------------------


def test_tick_repeated_detection_emits_alarm_once() -> None:
    """UT-006.1-15 — two ticks under continuous occlusion = one alarm event."""
    detector, reporter, state_machine = _build_detector(_both(_ABOVE, _BELOW))
    detector.tick()
    detector.tick()
    assert len(reporter.events) == 1
    assert len(state_machine.calls) == 1


def test_tick_idempotency_resets_on_return_to_healthy() -> None:
    """UT-006.1-16 — after the occlusion clears, a new event re-arms reporting.

    Sequence: detected -> healthy (clears) -> detected again. Second
    detection must produce a fresh alarm so a recurring occlusion is not
    silenced by the idempotency guard.
    """
    readings: list[dict[SensorKind, SensorReading]] = [
        _both(_ABOVE, _BELOW),
        _both(_BELOW, _BELOW),
        _both(_ABOVE, _BELOW),
    ]
    reporter = _RecordingReporter()
    state_machine = _RecordingStateMachine()
    detector = OcclusionDetector(
        sensor_reader=_StepReader(readings),
        alarm_reporter=reporter,
        state_machine=state_machine,
        clock=lambda: 0.0,
    )
    detector.tick()  # detected -> alarm #1
    detector.tick()  # healthy -> arm reset
    detector.tick()  # detected again -> alarm #2
    assert len(reporter.events) == 2
    assert len(state_machine.calls) == 2


class _StepReader:
    """Reader that advances through a list of per-tick reading maps."""

    def __init__(self, steps: Iterable[Mapping[SensorKind, SensorReading]]) -> None:
        self._steps = [dict(s) for s in steps]
        self._index = 0
        self._lock = threading.Lock()

    def read_sensor(self, kind: SensorKind) -> SensorReading:
        with self._lock:
            step = self._steps[min(self._index, len(self._steps) - 1)]
            reading = step[kind]
            # Advance once both channels for the current step have been read.
            other = (
                SensorKind.OCCLUSION_SECONDARY
                if kind is SensorKind.OCCLUSION_PRIMARY
                else SensorKind.OCCLUSION_PRIMARY
            )
            if other in step and kind is SensorKind.OCCLUSION_SECONDARY:
                self._index += 1
            return reading


# ---------------------------------------------------------------------------
# UT-006.1-17..18 — sensor-read exception suppression.
# ---------------------------------------------------------------------------


def test_tick_swallows_sensor_exception_and_escalates_to_failed() -> None:
    """UT-006.1-17 — sensor RuntimeError is treated as both-channels-failed."""
    readings = _both(_ABOVE, _ABOVE)  # values won't matter, both raise
    detector, reporter, state_machine = _build_detector(
        readings,
        raises={SensorKind.OCCLUSION_PRIMARY, SensorKind.OCCLUSION_SECONDARY},
    )
    detector.tick()  # must not raise
    assert reporter.events == []
    assert state_machine.calls == [
        (TargetState.ERROR, "occlusion_detection_unavailable"),
    ]


def test_tick_partial_sensor_exception_treated_as_degraded() -> None:
    """UT-006.1-18 — one channel raises, the other below threshold = Degraded.

    The failing channel is logged as the failed_channel; no alarm fires and
    no state transition is requested (continuous monitoring continues).
    """
    readings = _both(_ABOVE, _BELOW)
    detector, reporter, state_machine = _build_detector(
        readings,
        raises={SensorKind.OCCLUSION_PRIMARY},
    )
    detector.tick()
    assert reporter.events == []
    assert state_machine.calls == []
