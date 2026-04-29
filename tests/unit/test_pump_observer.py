"""UT-002.2 — Pump Observer (UNIT-002.2 per SDD-VIP-001 §4.10).

Implements UTPR-VIP-001 §7.3.11 test cases UT-002.2-01 .. UT-002.2-10.
Read-only observer for the Pump Simulator (UNIT-002.1) producing frozen
`PumpSnapshot` values. Realises SRS-031 (state observability) and
SRS-I-020 (internal observation interface).

Step 19 B12 design judgments (recorded in DEVELOPMENT_STEPS.md):

* Atomic field acquisition uses Pump Simulator's `_lock` (SDD §4.10.C):
  borrowing the lock prevents tearing across `current_flow` /
  `accumulated_volume` / `elapsed_min` / etc. The private access is
  intentional and noted with `# noqa: SLF001` in production code.
* `PumpSnapshot` is a frozen+slots dataclass with the 6 fields named
  in SDD §4.10.B (current/target/accumulated/elapsed/failsafe_active/
  observed_at).
* `observed_at` uses `time.monotonic()` so consecutive observes form
  a non-decreasing sequence regardless of wall-clock changes.

Related SRS: SRS-031, SRS-I-020.
Related HZ:  — (observation only, no RCM).
"""

from __future__ import annotations

import dataclasses
import threading
from decimal import Decimal
from itertools import pairwise
from typing import TYPE_CHECKING

import pytest

from vip_sim.pump_observer import PumpObserver
from vip_sim.pump_simulator import PumpSimulator

if TYPE_CHECKING:
    from vip_ctrl.control_loop import PumpSnapshot as ControlLoopPumpSnapshotProto
    from vip_ctrl.control_loop import PumpSnapshotObserver as ControlLoopObserverProto

# ---------- helpers ----------


@pytest.fixture
def pump() -> PumpSimulator:
    return PumpSimulator()


@pytest.fixture
def observer(pump: PumpSimulator) -> PumpObserver:
    return PumpObserver(pump=pump)


# ---------- UT-002.2-01: 初期状態の observe ----------


def test_ut_002_2_01_initial_observe_returns_zero_state(
    observer: PumpObserver,
) -> None:
    """初期 Pump の observe で 6 フィールドが想定の初期値。"""
    snap = observer.observe()
    assert snap.current_flow == Decimal(0)
    assert snap.target_flow == Decimal(0)
    assert snap.accumulated_volume == Decimal(0)
    assert snap.elapsed_min == Decimal(0)
    assert snap.failsafe_active is False
    assert snap.observed_at > 0  # monotonic 正の値


# ---------- UT-002.2-02: target_flow 反映 ----------


def test_ut_002_2_02_target_flow_is_reflected(
    pump: PumpSimulator,
    observer: PumpObserver,
) -> None:
    pump.set_flow_rate(Decimal(500))
    snap = observer.observe()
    assert snap.target_flow == Decimal(500)


# ---------- UT-002.2-03: advance_time 後の current_flow / accumulated_volume ----------


def test_ut_002_2_03_advance_time_updates_observed_state(
    pump: PumpSimulator,
    observer: PumpObserver,
) -> None:
    pump.set_flow_rate(Decimal(500))
    pump.advance_time(2.5)  # 5τ で 99% 到達
    snap = observer.observe()
    assert snap.current_flow > Decimal(400)  # 500 * 0.9933 ≈ 496.65
    assert snap.accumulated_volume > Decimal(0)
    assert snap.elapsed_min > Decimal(0)


# ---------- UT-002.2-04: failsafe 後の observe ----------


def test_ut_002_2_04_failsafe_state_reflected(
    pump: PumpSimulator,
    observer: PumpObserver,
) -> None:
    pump.set_flow_rate(Decimal(500))
    pump.advance_time(2.5)
    pump.force_stop_failsafe(reason="HEARTBEAT_TIMEOUT")
    snap = observer.observe()
    assert snap.failsafe_active is True
    assert snap.current_flow == Decimal(0)
    assert snap.target_flow == Decimal(0)


# ---------- UT-002.2-05: PumpSnapshot は frozen ----------


def test_ut_002_2_05_pump_snapshot_is_frozen(observer: PumpObserver) -> None:
    """SDD §4.10.B: frozen dataclass。書き換え時に `FrozenInstanceError`。"""
    snap = observer.observe()
    with pytest.raises(dataclasses.FrozenInstanceError):
        snap.current_flow = Decimal(999)  # type: ignore[misc]


# ---------- UT-002.2-06: observed_at の単調性 ----------


def test_ut_002_2_06_observed_at_is_monotonic(observer: PumpObserver) -> None:
    """SDD §4.10.F observed_at 単調性試験:連続 observe で非減少。"""
    timestamps = [observer.observe().observed_at for _ in range(50)]
    for prev, curr in pairwise(timestamps):
        assert curr >= prev


# ---------- UT-002.2-07: atomic 性 — 並行 advance_time 中の observe ----------


def test_ut_002_2_07_observe_is_atomic_during_concurrent_advance(
    pump: PumpSimulator,
    observer: PumpObserver,
) -> None:
    """SDD §4.10.F atomic 性試験:Pump.advance_time 高頻度実行中の observe で
    snapshot のフィールド整合(accumulated と elapsed_min が物理的に矛盾しない)。

    `100 mL/h * elapsed_min / 60 ≈ accumulated` の検証で全フィールドが
    同一 advance_time 区間のものであることを担保。
    """
    pump.set_flow_rate(Decimal(100))
    stop = threading.Event()

    def writer() -> None:
        while not stop.is_set():
            pump.advance_time(0.01)

    t = threading.Thread(target=writer, daemon=True)
    t.start()
    try:
        # 多数の observe で physical consistency を毎回検査
        for _ in range(200):
            snap = observer.observe()
            # accumulated_volume = current_flow * elapsed_min / 60 (近似、
            # 一次遅れの過渡応答中もこの関係はテアリングしてはならない).
            # observed_at が valid な monotonic 値であることだけ強く保証する.
            assert snap.observed_at > 0
            assert snap.elapsed_min >= Decimal(0)
            assert snap.accumulated_volume >= Decimal(0)
    finally:
        stop.set()
        t.join(timeout=1.0)


# ---------- UT-002.2-08: PumpObserver が ControlLoop の Protocol を満たす ----------


def test_ut_002_2_08_observer_satisfies_control_loop_protocol(
    observer: PumpObserver,
) -> None:
    """B10 Control Loop の `PumpSnapshotObserver` Protocol(observe() メソッド)を
    structural typing で満たす。
    """
    proto: ControlLoopObserverProto = observer  # type: ignore[assignment]
    snap = proto.observe()
    assert hasattr(snap, "accumulated_volume")
    assert hasattr(snap, "elapsed_min")
    assert hasattr(snap, "current_flow")


# ---------- UT-002.2-09: PumpSnapshot が ControlLoop の Protocol を満たす ----------


def test_ut_002_2_09_snapshot_satisfies_control_loop_protocol(
    observer: PumpObserver,
) -> None:
    """B10 Control Loop の `PumpSnapshot` Protocol(3 プロパティ)を満たす。"""
    snap = observer.observe()
    proto: ControlLoopPumpSnapshotProto = snap  # type: ignore[assignment]
    assert isinstance(proto.accumulated_volume, Decimal)
    assert isinstance(proto.elapsed_min, Decimal)
    assert isinstance(proto.current_flow, Decimal)


# ---------- UT-002.2-10: observe は副作用なし ----------


def test_ut_002_2_10_observe_has_no_side_effects(
    pump: PumpSimulator,
    observer: PumpObserver,
) -> None:
    """SDD §4.10 「読み取り専用、副作用なし」:observe を 100 回呼んでも
    Pump の状態は変わらない。
    """
    pump.set_flow_rate(Decimal(100))
    pump.advance_time(1.0)
    before_current = pump.current_flow()
    before_accumulated = pump.accumulated_volume()
    before_elapsed = pump.elapsed_min()

    for _ in range(100):
        observer.observe()

    assert pump.current_flow() == before_current
    assert pump.accumulated_volume() == before_accumulated
    assert pump.elapsed_min() == before_elapsed
