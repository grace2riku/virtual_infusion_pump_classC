"""UT-005.2 — State Observer API (UNIT-005.2 per SDD-VIP-001 §4.16).

Implements UTPR-VIP-001 §7.3.16 detailed test cases UT-005.2-01 .. UT-005.2-11.
Realises SRS-IF-003 (read-only state observation API), SRS-O-010
(machine-state output) and SRS-UX-002 (no-side-effect / idempotent).

Step 19 B17 design judgments (recorded in DEVELOPMENT_STEPS.md):

* `StateSnapshot` is `frozen=True, slots=True` (B11〜B16 pattern), not
  the `frozen pydantic` of SDD §4.16.B — pydantic adds runtime
  validation that is unnecessary for an immutable read-only output.
* `error_reason` is stringified (SDD §4.16 design judgment) so the
  internal `WatchdogReason` enum never leaks across the API boundary.
* The Observer never raises — but it does NOT wrap the injected
  collaborators in try/except (per SDD §4.16.E "design goal: no
  exceptions; if a collaborator throws, that's the caller's
  responsibility"). UT-005.2-11 documents this propagation contract.
* Injected collaborators are constructor-injected (B9/B10/B15/B16
  pattern); UT replaces them with `Mock(spec=...)`.

Related SRS: SRS-IF-003, SRS-O-010, SRS-UX-002.
Related RCM: — (read-only observation).
"""

from __future__ import annotations

import dataclasses
from datetime import UTC, datetime
from decimal import Decimal
from itertools import pairwise
from unittest.mock import Mock

import pytest

from vip_api.state_observer_api import StateObserverApi, StateSnapshot
from vip_ctrl.state_machine import State, StateMachine, WatchdogReason
from vip_integrity.resume_gate import ResumeConfirmationGate, ResumeDetail
from vip_persist.records import Settings
from vip_sim.pump_observer import PumpObserver, PumpSnapshot

# ---------- helpers ----------


def _make_pump_snapshot() -> PumpSnapshot:
    return PumpSnapshot(
        current_flow=Decimal("100.0"),
        target_flow=Decimal("120.0"),
        accumulated_volume=Decimal("50.0"),
        elapsed_min=Decimal("30.0"),
        failsafe_active=False,
        observed_at=12345.6,
    )


def _make_resume_detail() -> ResumeDetail:
    return ResumeDetail(
        settings=Settings(
            flow_rate=Decimal("100.0"),
            dose_volume=Decimal("250.0"),
            duration_min=150,
        ),
        state=State.PAUSED,
        accumulated_volume=Decimal("50.0"),
    )


@pytest.fixture
def state_machine_mock() -> Mock:
    sm: Mock = Mock(spec=StateMachine)
    sm.current.return_value = State.IDLE
    sm.error_reason.return_value = None
    return sm


@pytest.fixture
def pump_observer_mock() -> Mock:
    obs: Mock = Mock(spec=PumpObserver)
    obs.observe.return_value = _make_pump_snapshot()
    return obs


@pytest.fixture
def resume_gate_mock() -> Mock:
    gate: Mock = Mock(spec=ResumeConfirmationGate)
    gate.is_pending.return_value = False
    gate.pending_detail.return_value = None
    return gate


@pytest.fixture
def observer(
    state_machine_mock: Mock,
    pump_observer_mock: Mock,
    resume_gate_mock: Mock,
) -> StateObserverApi:
    return StateObserverApi(
        state_machine=state_machine_mock,
        pump_observer=pump_observer_mock,
        resume_gate=resume_gate_mock,
    )


# ---------- UT-005.2-01: 基本観測 ----------


def test_ut_005_2_01_observe_state_returns_aggregated_snapshot(
    observer: StateObserverApi,
) -> None:
    """3 つの注入から `StateSnapshot` を集約して返す。"""
    snap = observer.observe_state()

    assert isinstance(snap, StateSnapshot)
    assert snap.machine_state is State.IDLE
    assert snap.pump.current_flow == Decimal("100.0")
    assert snap.resume_pending is False
    assert snap.resume_set_at is None
    assert snap.error_reason is None
    assert isinstance(snap.observed_at, datetime)


# ---------- UT-005.2-02: idempotent / 副作用なし ----------


def test_ut_005_2_02_observe_state_is_idempotent_over_repeated_calls(
    observer: StateObserverApi,
    state_machine_mock: Mock,
    pump_observer_mock: Mock,
    resume_gate_mock: Mock,
) -> None:
    """100 回連続呼出で各注入の状態に副作用がない(SRS-UX-002)。"""
    for _ in range(100):
        observer.observe_state()

    # 各注入は read-only API のみ呼ばれている。
    assert state_machine_mock.current.call_count == 100
    assert pump_observer_mock.observe.call_count == 100
    assert resume_gate_mock.is_pending.call_count == 100
    # mutating API は一切呼ばれていない(spec=... の attr 集合に存在しない)。


# ---------- UT-005.2-03: machine_state 集約 ----------


@pytest.mark.parametrize(
    "state",
    [State.IDLE, State.RUNNING, State.PAUSED, State.STOPPED, State.ERROR],
)
def test_ut_005_2_03_machine_state_is_passed_through(
    observer: StateObserverApi,
    state_machine_mock: Mock,
    state: State,
) -> None:
    """State Machine が返した state がそのまま StateSnapshot.machine_state に反映される。"""
    state_machine_mock.current.return_value = state
    if state is State.ERROR:
        state_machine_mock.error_reason.return_value = WatchdogReason.SW_WATCHDOG

    snap = observer.observe_state()

    assert snap.machine_state is state


# ---------- UT-005.2-04: pump 集約 ----------


def test_ut_005_2_04_pump_snapshot_is_passed_through(
    observer: StateObserverApi,
    pump_observer_mock: Mock,
) -> None:
    """PumpObserver の PumpSnapshot 全フィールドが透過される。"""
    custom_pump = PumpSnapshot(
        current_flow=Decimal("250.5"),
        target_flow=Decimal("250.0"),
        accumulated_volume=Decimal("123.4"),
        elapsed_min=Decimal("12.3"),
        failsafe_active=True,
        observed_at=99999.9,
    )
    pump_observer_mock.observe.return_value = custom_pump

    snap = observer.observe_state()

    assert snap.pump is custom_pump


# ---------- UT-005.2-05: resume_pending = True で resume_set_at 透過 ----------


def test_ut_005_2_05_resume_pending_true_with_inc1_api_yields_none_resume_set_at(
    observer: StateObserverApi,
    resume_gate_mock: Mock,
) -> None:
    """is_pending=True かつ Inc.1 の Resume Gate API では resume_set_at は None。

    SDD §4.16.B は ``resume_set_at: Optional[datetime]`` を要求するが、Inc.1 の
    ``ResumeConfirmationGate.pending_detail()`` は ``ResumeDetail``(``set_at_wall`` を
    持たない)を返すため、Inc.1 範囲では None 固定が SDD §4.16.B の Optional 仕様に
    合致する。``set_at_wall`` の透過は Inc.4 UI 着手時に Resume Gate API 拡張で
    実装予定(申し送り)。本試験はこの Inc.1 範囲の挙動を契約として固定する。
    """
    resume_gate_mock.is_pending.return_value = True
    resume_gate_mock.pending_detail.return_value = _make_resume_detail()

    snap = observer.observe_state()

    assert snap.resume_pending is True
    # Inc.1 の ResumeDetail に set_at_wall がないため None。Inc.4 で拡張予定。
    assert snap.resume_set_at is None


# ---------- UT-005.2-06: resume_pending = False で resume_set_at is None ----------


def test_ut_005_2_06_resume_pending_false_sets_resume_set_at_to_none(
    observer: StateObserverApi,
    resume_gate_mock: Mock,
) -> None:
    """is_pending=False なら resume_set_at は None。"""
    resume_gate_mock.is_pending.return_value = False
    resume_gate_mock.pending_detail.return_value = None

    snap = observer.observe_state()

    assert snap.resume_pending is False
    assert snap.resume_set_at is None


# ---------- UT-005.2-07: ERROR 状態で error_reason を文字列化 ----------


def test_ut_005_2_07_error_state_stringifies_error_reason(
    observer: StateObserverApi,
    state_machine_mock: Mock,
) -> None:
    """machine_state=ERROR + error_reason=SW_WATCHDOG → 文字列化(SDD 設計判断:内部 enum 非露出)。"""
    state_machine_mock.current.return_value = State.ERROR
    state_machine_mock.error_reason.return_value = WatchdogReason.SW_WATCHDOG

    snap = observer.observe_state()

    assert snap.machine_state is State.ERROR
    assert isinstance(snap.error_reason, str)
    assert "SW_WATCHDOG" in snap.error_reason


# ---------- UT-005.2-08: 非 ERROR 状態で error_reason is None ----------


@pytest.mark.parametrize(
    "state",
    [State.IDLE, State.RUNNING, State.PAUSED, State.STOPPED],
)
def test_ut_005_2_08_non_error_state_has_no_error_reason(
    observer: StateObserverApi,
    state_machine_mock: Mock,
    state: State,
) -> None:
    """非 ERROR 状態では error_reason は None。"""
    state_machine_mock.current.return_value = state

    snap = observer.observe_state()

    assert snap.error_reason is None


# ---------- UT-005.2-09: observed_at の単調性 ----------


def test_ut_005_2_09_observed_at_is_monotonically_non_decreasing(
    observer: StateObserverApi,
) -> None:
    """連続観測で observed_at が単調非減少(B12 PumpSnapshot.observed_at と同じ契約)。"""
    timestamps = [observer.observe_state().observed_at for _ in range(50)]

    assert all(prev <= curr for prev, curr in pairwise(timestamps))


# ---------- UT-005.2-10: StateSnapshot frozen 契約 ----------


def test_ut_005_2_10_state_snapshot_is_frozen(
    observer: StateObserverApi,
) -> None:
    """`StateSnapshot` は frozen dataclass であり代入不可(B12 パターン継続)。"""
    snap = observer.observe_state()

    with pytest.raises(dataclasses.FrozenInstanceError):
        snap.machine_state = State.RUNNING  # type: ignore[misc]


# ---------- UT-005.2-11: 注入オブジェクト例外の伝播 ----------


def test_ut_005_2_11_collaborator_exception_propagates(
    observer: StateObserverApi,
    state_machine_mock: Mock,
) -> None:
    """注入オブジェクトの例外は伝播(SDD §4.16.E:本 API は try/except せず)。"""
    state_machine_mock.current.side_effect = RuntimeError("state machine crashed")

    with pytest.raises(RuntimeError, match="state machine crashed"):
        observer.observe_state()


# ---------- 境界:observed_at は UTC datetime ----------


def test_ut_005_2_12_observed_at_is_utc_datetime(
    observer: StateObserverApi,
) -> None:
    """observed_at は UTC タイムゾーン付き datetime。"""
    snap = observer.observe_state()

    assert snap.observed_at.tzinfo is UTC
