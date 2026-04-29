"""UT-001.2 — Control Loop (UNIT-001.2 per SDD-VIP-001 §4.6).

Implements UTPR-VIP-001 §7.3.9 test cases UT-001.2-01 .. UT-001.2-18.
Covers RCM-004 SW-side heartbeat dispatch and SRS-031 auto-stop dispatch
per RMF-VIP-001 §6.1.

Step 19 B10 reconciles UTPR §7.3.9 骨格 with SDD §4.6 and records four
design judgments mirroring B4/B9:

* Clock injection (`clock` parameter) for deterministic tests.
* `tick()` exposed as a test-friendly single-tick entry point.
* Logger plumbing deferred (use `logging.getLogger(__name__)` directly).
* SRS-P02 ±10% real-time period jitter testing is deferred to ITPR §5.6
  (the UT exercises only the deadline arithmetic with a fake clock).

Design integrations against state_machine.py existing API:

* `WatchdogReason.CONTROL_LOOP_EXCEPTION` (SDD §4.6.C pseudocode) is
  mapped to existing `WatchdogReason.OTHER` (B9 "add-only" continuation).
* `EventKind.AUTO_STOP_DURATION_REACHED` (SDD §4.6.C pseudocode) is not
  implemented in this Inc.1 baseline because SRS-012/031 only require
  dose-based auto-stop. The duration branch is deferred to a future CR.

Related SRS: SRS-011, SRS-012, SRS-031, SRS-P02, SRS-RCM-004.
Related HZ:  HZ-001 (over-delivery), HZ-002 (under-delivery).
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from vip_ctrl.control_loop import (
    PERIOD_SEC,
    ControlLoop,
    PumpFlowController,
    PumpSnapshot,
    PumpSnapshotObserver,
)
from vip_ctrl.state_machine import (
    EventKind,
    State,
    StateMachine,
    TransitionEvent,
    WatchdogReason,
)
from vip_persist.records import Settings as RecordSettings

# ---------- helpers / fixtures ----------


class _FakeClock:
    """Manual clock returning a controlled monotonic-style float."""

    def __init__(self, start: float = 0.0) -> None:
        self._t = start
        self._lock = threading.Lock()

    def __call__(self) -> float:
        with self._lock:
            return self._t

    def advance(self, delta: float) -> None:
        with self._lock:
            self._t += delta


@dataclass(frozen=True, slots=True)
class _FakePumpSnapshot:
    """Test-side dummy snapshot satisfying PumpSnapshot protocol."""

    accumulated_volume: Decimal
    elapsed_min: Decimal
    current_flow: Decimal
    state: str = "RUNNING"


def _make_settings(
    *,
    flow_rate: str = "100.0",
    dose_volume: str = "500.0",
    duration_min: int = 300,
) -> RecordSettings:
    return RecordSettings(
        flow_rate=Decimal(flow_rate),
        dose_volume=Decimal(dose_volume),
        duration_min=duration_min,
    )


def _make_snapshot(
    *,
    accumulated_volume: str = "0.0",
    elapsed_min: str = "0",
    current_flow: str = "0.0",
) -> _FakePumpSnapshot:
    return _FakePumpSnapshot(
        accumulated_volume=Decimal(accumulated_volume),
        elapsed_min=Decimal(elapsed_min),
        current_flow=Decimal(current_flow),
    )


@pytest.fixture
def fake_clock() -> _FakeClock:
    return _FakeClock()


@pytest.fixture
def state_machine() -> StateMachine:
    sm = StateMachine()
    sm.set_initial(State.IDLE, needs_confirm=False)
    sm.request_transition(_make_event(EventKind.CMD_START))
    return sm


def _make_event(kind: EventKind) -> TransitionEvent:
    return TransitionEvent(kind=kind, timestamp=datetime.now(UTC))


@pytest.fixture
def fake_pump() -> MagicMock:
    return MagicMock(spec=PumpFlowController)


@pytest.fixture
def fake_observer() -> MagicMock:
    obs = MagicMock(spec=PumpSnapshotObserver)
    obs.observe.return_value = _make_snapshot()
    return obs


@pytest.fixture
def fake_sw_watchdog() -> MagicMock:
    return MagicMock()


@pytest.fixture
def fake_hw_watchdog() -> MagicMock:
    return MagicMock()


@pytest.fixture
def settings_provider() -> MagicMock:
    return MagicMock(return_value=_make_settings())


@pytest.fixture
def loop(
    state_machine: StateMachine,
    fake_pump: MagicMock,
    fake_observer: MagicMock,
    fake_sw_watchdog: MagicMock,
    fake_hw_watchdog: MagicMock,
    settings_provider: MagicMock,
    fake_clock: _FakeClock,
) -> ControlLoop:
    return ControlLoop(
        state_machine=state_machine,
        pump=fake_pump,
        observer=fake_observer,
        sw_watchdog=fake_sw_watchdog,
        hw_watchdog=fake_hw_watchdog,
        settings_provider=settings_provider,
        clock=fake_clock,
    )


# ---------- UT-001.2-01: State.RUNNING でない場合 tick() は no-op ----------


def test_ut_001_2_01_tick_is_noop_when_not_running(
    fake_pump: MagicMock,
    fake_observer: MagicMock,
    fake_sw_watchdog: MagicMock,
    fake_hw_watchdog: MagicMock,
    settings_provider: MagicMock,
    fake_clock: _FakeClock,
) -> None:
    """IDLE / PAUSED / STOPPED / ERROR では tick() は副作用を起こさない。"""
    sm = StateMachine()
    sm.set_initial(State.IDLE, needs_confirm=False)
    loop_obj = ControlLoop(
        state_machine=sm,
        pump=fake_pump,
        observer=fake_observer,
        sw_watchdog=fake_sw_watchdog,
        hw_watchdog=fake_hw_watchdog,
        settings_provider=settings_provider,
        clock=fake_clock,
    )
    loop_obj.tick()
    fake_pump.set_flow_rate.assert_not_called()
    fake_observer.observe.assert_not_called()
    fake_sw_watchdog.heartbeat.assert_not_called()
    fake_hw_watchdog.heartbeat.assert_not_called()


# ---------- UT-001.2-02: State.RUNNING で tick() の主処理が呼ばれる順序 ----------


def test_ut_001_2_02_tick_dispatches_heartbeat_command_observe(
    loop: ControlLoop,
    fake_pump: MagicMock,
    fake_observer: MagicMock,
    fake_sw_watchdog: MagicMock,
    fake_hw_watchdog: MagicMock,
) -> None:
    loop.tick()
    fake_sw_watchdog.heartbeat.assert_called_once()
    fake_hw_watchdog.heartbeat.assert_called_once()
    fake_pump.set_flow_rate.assert_called_once_with(Decimal("100.0"))
    fake_observer.observe.assert_called_once()


# ---------- UT-001.2-03: heartbeat は validator/pump 例外より先に送出 ----------


def test_ut_001_2_03_heartbeat_emitted_before_pump_failure(
    loop: ControlLoop,
    fake_pump: MagicMock,
    fake_sw_watchdog: MagicMock,
    fake_hw_watchdog: MagicMock,
    state_machine: StateMachine,
) -> None:
    """SDD §4.6 キーポイント:Watchdog からみた『生存』を先に記録する設計。"""
    fake_pump.set_flow_rate.side_effect = RuntimeError("pump fault")
    loop.tick()
    fake_sw_watchdog.heartbeat.assert_called_once()
    fake_hw_watchdog.heartbeat.assert_called_once()
    assert state_machine.current() == State.ERROR


# ---------- UT-001.2-04: Validator Err → State Machine に WDT_TIMEOUT ----------


def test_ut_001_2_04_validator_failure_triggers_wdt_timeout(
    loop: ControlLoop,
    fake_pump: MagicMock,
    settings_provider: MagicMock,
    state_machine: StateMachine,
) -> None:
    """流量指令値が設定値と乖離 → Validator が MISMATCH_WITH_SETTINGS で Err。
    pump.set_flow_rate は呼ばれず State Machine が ERROR に遷移する。
    """
    # Settings.flow_rate と乖離した値を設定して MISMATCH を誘発する代わりに、
    # Validator が NaN/負の値を返すように flow_rate を NaN に設定すると
    # records.Settings の Decimal 検証が落ちるため、settings_provider を差し替え、
    # validator が NEGATIVE/OUT_OF_RANGE を返す状況は別ユニットの責任なので
    # ここでは settings_provider が NEGATIVE を返すパターンで検証する。
    settings_provider.return_value = _make_settings(flow_rate="-1.0")
    loop.tick()
    fake_pump.set_flow_rate.assert_not_called()
    assert state_machine.current() == State.ERROR


# ---------- UT-001.2-05: 積算量 > dose_volume で AUTO_STOP_DOSE_REACHED ----------


def test_ut_001_2_05_auto_stop_when_dose_exceeded(
    loop: ControlLoop,
    fake_observer: MagicMock,
    state_machine: StateMachine,
) -> None:
    fake_observer.observe.return_value = _make_snapshot(
        accumulated_volume="500.1",  # dose_volume = 500.0
    )
    loop.tick()
    assert state_machine.current() == State.STOPPED


# ---------- UT-001.2-06a: 境界 — accumulated == dose で AUTO_STOP ----------


def test_ut_001_2_06a_auto_stop_at_exact_dose(
    loop: ControlLoop,
    fake_observer: MagicMock,
    state_machine: StateMachine,
) -> None:
    """SDD §4.6.C: `accumulated_volume >= settings.dose_volume`。境界値で発動。"""
    fake_observer.observe.return_value = _make_snapshot(
        accumulated_volume="500.0",
    )
    loop.tick()
    assert state_machine.current() == State.STOPPED


# ---------- UT-001.2-06b: 境界 — accumulated < dose で AUTO_STOP しない ----------


def test_ut_001_2_06b_no_auto_stop_below_dose(
    loop: ControlLoop,
    fake_observer: MagicMock,
    state_machine: StateMachine,
) -> None:
    fake_observer.observe.return_value = _make_snapshot(
        accumulated_volume="499.999",
    )
    loop.tick()
    assert state_machine.current() == State.RUNNING


# ---------- UT-001.2-07: settings_provider 例外 → ERROR 誘発 ----------


def test_ut_001_2_07_settings_provider_exception_triggers_error(
    loop: ControlLoop,
    settings_provider: MagicMock,
    state_machine: StateMachine,
    fake_sw_watchdog: MagicMock,
) -> None:
    """SDD §4.6.E: `_settings_provider` 例外は致命的扱い。

    ただしハートビートは tick 先頭で送出済(UT-001.2-03 と同様)。
    """
    settings_provider.side_effect = RuntimeError("config failure")
    loop.tick()
    assert state_machine.current() == State.ERROR
    fake_sw_watchdog.heartbeat.assert_called_once()


# ---------- UT-001.2-08: tick 例外で on_watchdog_timeout(OTHER) 呼出 ----------


def test_ut_001_2_08_pump_exception_records_other_reason(
    loop: ControlLoop,
    fake_pump: MagicMock,
    state_machine: StateMachine,
) -> None:
    """SDD §4.6.E: 制御ループ例外 → ERROR 誘発。

    既存 enum `WatchdogReason.OTHER` にマップ(SDD §4.6.C 擬似コード
    `CONTROL_LOOP_EXCEPTION` は state_machine.py 既存 enum に存在せず、
    Step 19 B9 「add-only / 既存 enum 不変」継続)。
    """
    fake_pump.set_flow_rate.side_effect = RuntimeError("pump fault")
    loop.tick()
    assert state_machine.current() == State.ERROR
    assert state_machine.error_reason() == WatchdogReason.OTHER


# ---------- UT-001.2-09: start/stop ライフサイクル ----------


def test_ut_001_2_09_start_then_stop_lifecycle(loop: ControlLoop) -> None:
    loop.start()
    assert loop.is_running() is True
    loop.stop()
    assert loop.is_running() is False


# ---------- UT-001.2-10: 2 重 start → RuntimeError ----------


def test_ut_001_2_10_double_start_raises_runtime_error(loop: ControlLoop) -> None:
    loop.start()
    try:
        with pytest.raises(RuntimeError, match="already started"):
            loop.start()
    finally:
        loop.stop()


# ---------- UT-001.2-11: 2 重 stop → no-op ----------


def test_ut_001_2_11_double_stop_is_no_op(loop: ControlLoop) -> None:
    loop.start()
    loop.stop()
    loop.stop()


# ---------- UT-001.2-12: stop before start → no-op ----------


def test_ut_001_2_12_stop_before_start_is_no_op(loop: ControlLoop) -> None:
    loop.stop()


# ---------- UT-001.2-13: 周期定数 PERIOD_SEC == 100 ms ----------


def test_ut_001_2_13_period_constant_is_100ms() -> None:
    assert pytest.approx(0.1) == PERIOD_SEC


# ---------- UT-001.2-14: tick() は False を返す(state≠RUNNING)/ True(RUNNING) ----------


def test_ut_001_2_14a_tick_returns_false_when_not_running(
    fake_pump: MagicMock,
    fake_observer: MagicMock,
    fake_sw_watchdog: MagicMock,
    fake_hw_watchdog: MagicMock,
    settings_provider: MagicMock,
    fake_clock: _FakeClock,
) -> None:
    sm = StateMachine()
    sm.set_initial(State.IDLE, needs_confirm=False)
    loop_obj = ControlLoop(
        state_machine=sm,
        pump=fake_pump,
        observer=fake_observer,
        sw_watchdog=fake_sw_watchdog,
        hw_watchdog=fake_hw_watchdog,
        settings_provider=settings_provider,
        clock=fake_clock,
    )
    assert loop_obj.tick() is False


def test_ut_001_2_14b_tick_returns_true_when_running(loop: ControlLoop) -> None:
    assert loop.tick() is True


# ---------- UT-001.2-15: ハートビートは fake_clock の現在値を渡す ----------


def test_ut_001_2_15_heartbeat_carries_clock_timestamp(
    loop: ControlLoop,
    fake_clock: _FakeClock,
    fake_sw_watchdog: MagicMock,
    fake_hw_watchdog: MagicMock,
) -> None:
    fake_clock.advance(1.234)
    loop.tick()
    fake_sw_watchdog.heartbeat.assert_called_once_with(1.234)
    fake_hw_watchdog.heartbeat.assert_called_once_with(1.234)


# ---------- UT-001.2-16: validate に渡される ControlContext の整合性 ----------


def test_ut_001_2_16_validator_receives_running_context(
    loop: ControlLoop,
    fake_pump: MagicMock,
    settings_provider: MagicMock,
) -> None:
    """Validator には現 Settings.flow_rate と State.RUNNING を含む ControlContext が渡る。

    pump.set_flow_rate が呼び出されることで間接的に validation 通過を確認。
    """
    settings_provider.return_value = _make_settings(flow_rate="50.0")
    loop.tick()
    fake_pump.set_flow_rate.assert_called_once_with(Decimal("50.0"))


# ---------- UT-001.2-17: 実時間スレッド統合スモーク ----------


def test_ut_001_2_17_real_time_thread_smoke_executes_tick(
    fake_pump: MagicMock,
    fake_observer: MagicMock,
    fake_sw_watchdog: MagicMock,
    fake_hw_watchdog: MagicMock,
    settings_provider: MagicMock,
) -> None:
    """End-to-end smoke: 実 `time.monotonic` + 監視スレッドで tick が発動。

    緩い 1 秒境界。OS スケジューリングのジッタに強い。SRS-P02 ±10% の
    厳密な周期精度試験は ITPR §5.6 申し送り。
    """
    sm = StateMachine()
    sm.set_initial(State.IDLE, needs_confirm=False)
    sm.request_transition(_make_event(EventKind.CMD_START))
    loop_obj = ControlLoop(
        state_machine=sm,
        pump=fake_pump,
        observer=fake_observer,
        sw_watchdog=fake_sw_watchdog,
        hw_watchdog=fake_hw_watchdog,
        settings_provider=settings_provider,
        period_sec=0.02,  # 短周期で素早く tick を発動
    )
    loop_obj.start()
    try:
        deadline = time.monotonic() + 1.0
        while time.monotonic() < deadline:
            if fake_pump.set_flow_rate.called:
                break
            time.sleep(0.02)
        assert fake_pump.set_flow_rate.called is True
    finally:
        loop_obj.stop()


# ---------- UT-001.2-18: PumpSnapshot Protocol 準拠 ----------


def test_ut_001_2_18_pump_snapshot_protocol_compliance() -> None:
    """`PumpSnapshot` は accumulated_volume / elapsed_min / current_flow を持つ。"""
    snap: PumpSnapshot = _make_snapshot(
        accumulated_volume="100.0",
        elapsed_min="60",
        current_flow="50.0",
    )
    assert snap.accumulated_volume == Decimal("100.0")
    assert snap.elapsed_min == Decimal(60)
    assert snap.current_flow == Decimal("50.0")


# ---------- UT-001.2-19: 周期オーバーラン警告ログ ----------


def test_ut_001_2_19_overrun_logs_warning(
    fake_pump: MagicMock,
    fake_observer: MagicMock,
    fake_sw_watchdog: MagicMock,
    fake_hw_watchdog: MagicMock,
    settings_provider: MagicMock,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """SDD §4.6.E: 周期遅延(オーバーラン)はログのみ。

    `period_sec=0` で _loop 内 sleep_sec <= 0 を確実に通過させ、warning ログを検証。
    SW Watchdog が後段で SRS-RCM-003 のタイムアウト判定を行う前提。
    """
    sm = StateMachine()
    sm.set_initial(State.IDLE, needs_confirm=False)
    loop_obj = ControlLoop(
        state_machine=sm,
        pump=fake_pump,
        observer=fake_observer,
        sw_watchdog=fake_sw_watchdog,
        hw_watchdog=fake_hw_watchdog,
        settings_provider=settings_provider,
        period_sec=0.0,  # 必ず sleep_sec <= 0 になる
    )
    with caplog.at_level("WARNING", logger="vip_ctrl.control_loop"):
        loop_obj.start()
        # 数 tick 動かしてから停止
        time.sleep(0.05)
        loop_obj.stop()
    assert any("overrun" in rec.message for rec in caplog.records)
