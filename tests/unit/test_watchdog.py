"""UT-001.5 — SW Watchdog (UNIT-001.5 per SDD-VIP-001 §4.8).

Implements UTPR-VIP-001 §7.3.9 test cases UT-001.5-01 .. UT-001.5-12.
Covers RCM-003 SW-side (heartbeat watchdog monitoring the control loop)
per RMF-VIP-001 §6.1.

Step 19 B9 reconciles UTPR §7.3.8 骨格 (previously mis-specified "500 ms")
with SDD §4.8 (300 ms) and records four design judgments mirroring B4:

* Clock injection (`clock` parameter) for deterministic tests.
* Clock regression (`now < last`) is treated as a safety-side trip
  (SDD §4.8 only states "Python 仕様で単調増加保証" — the injected
  clock may regress under faults so we fail safe).
* Logger plumbing deferred; the SW watchdog identifier is
  `WatchdogReason.SW_WATCHDOG` (existing enum in state_machine.py).
* `check_once` is exposed as a test-friendly single-tick entry point.

Related SRS: SRS-RCM-003.
Related HZ:  HZ-001 (over-delivery), HZ-002 (under-delivery).
"""

from __future__ import annotations

import threading
import time
from unittest.mock import MagicMock

import pytest

from vip_ctrl.state_machine import WatchdogReason
from vip_ctrl.watchdog import (
    HEARTBEAT_TIMEOUT,
    MONITOR_INTERVAL,
    SwWatchdog,
)
from vip_sim.failsafe_timer import HwFailsafeTimer

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

    def set_to(self, value: float) -> None:
        with self._lock:
            self._t = value


@pytest.fixture
def fake_state_machine() -> MagicMock:
    return MagicMock()


@pytest.fixture
def fake_clock() -> _FakeClock:
    return _FakeClock()


@pytest.fixture
def watchdog(fake_state_machine: MagicMock, fake_clock: _FakeClock) -> SwWatchdog:
    return SwWatchdog(state_machine=fake_state_machine, clock=fake_clock)


# ---------- UT-001.5-01: 正常ハートビートで Trip しない ----------


def test_ut_001_5_01_periodic_heartbeat_does_not_trip(
    watchdog: SwWatchdog,
    fake_clock: _FakeClock,
    fake_state_machine: MagicMock,
) -> None:
    """制御周期 100 ms 相当のハートビートが 10 回続いても Trip しない。"""
    watchdog.heartbeat()
    for _ in range(10):
        fake_clock.advance(0.1)
        watchdog.heartbeat()
        watchdog.check_once()
    assert watchdog.is_tripped() is False
    fake_state_machine.on_watchdog_timeout.assert_not_called()


# ---------- UT-001.5-02: ハートビート途絶検知 → on_watchdog_timeout 呼出 ----------


def test_ut_001_5_02_heartbeat_silence_trips_and_notifies_state_machine(
    watchdog: SwWatchdog,
    fake_clock: _FakeClock,
    fake_state_machine: MagicMock,
) -> None:
    """300 ms 超過で Trip、state_machine.on_watchdog_timeout(SW_WATCHDOG) 1 回呼出。"""
    watchdog.heartbeat()
    fake_clock.advance(0.301)
    watchdog.check_once()
    assert watchdog.is_tripped() is True
    fake_state_machine.on_watchdog_timeout.assert_called_once_with(
        WatchdogReason.SW_WATCHDOG,
    )


# ---------- UT-001.5-03a: 境界 299 ms(Trip しない) ----------


def test_ut_001_5_03a_below_timeout_does_not_trip(
    watchdog: SwWatchdog,
    fake_clock: _FakeClock,
) -> None:
    watchdog.heartbeat()
    fake_clock.advance(0.299)
    watchdog.check_once()
    assert watchdog.is_tripped() is False


# ---------- UT-001.5-03b: 境界 300 ms ちょうど(`>` 判定で Trip しない) ----------


def test_ut_001_5_03b_exact_timeout_does_not_trip(
    watchdog: SwWatchdog,
    fake_clock: _FakeClock,
) -> None:
    """SDD §4.8.C: `(now - last) > HEARTBEAT_TIMEOUT`. 境界値は発火しない。"""
    watchdog.heartbeat()
    fake_clock.advance(HEARTBEAT_TIMEOUT)
    watchdog.check_once()
    assert watchdog.is_tripped() is False


# ---------- UT-001.5-03c: 境界 300 ms + ε(Trip) ----------


def test_ut_001_5_03c_just_above_timeout_trips(
    watchdog: SwWatchdog,
    fake_clock: _FakeClock,
) -> None:
    watchdog.heartbeat()
    fake_clock.advance(HEARTBEAT_TIMEOUT + 0.0001)
    watchdog.check_once()
    assert watchdog.is_tripped() is True


# ---------- UT-001.5-03d: 最大検出遅延 350 ms(Trip) ----------


def test_ut_001_5_03d_max_detection_delay_trips(
    watchdog: SwWatchdog,
    fake_clock: _FakeClock,
) -> None:
    """SDD §4.8.D: 最大検出遅延 = HEARTBEAT_TIMEOUT + MONITOR_INTERVAL = 350 ms。"""
    watchdog.heartbeat()
    fake_clock.advance(HEARTBEAT_TIMEOUT + MONITOR_INTERVAL)
    watchdog.check_once()
    assert watchdog.is_tripped() is True


# ---------- UT-001.5-04: 並行 heartbeat(Lock で保護) ----------


def test_ut_001_5_04_concurrent_heartbeats_no_data_race(
    watchdog: SwWatchdog,
    fake_clock: _FakeClock,
) -> None:
    """2 スレッドから heartbeat を連打。Lock により最終値が最新 clock と一致。"""
    watchdog.heartbeat()
    barrier = threading.Barrier(2)

    def worker(advance_each: float) -> None:
        barrier.wait()
        for _ in range(50):
            fake_clock.advance(advance_each)
            watchdog.heartbeat()

    t1 = threading.Thread(target=worker, args=(0.001,))
    t2 = threading.Thread(target=worker, args=(0.001,))
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    watchdog.check_once()
    assert watchdog.is_tripped() is False
    assert watchdog.last_heartbeat() == fake_clock()


# ---------- UT-001.5-05: クロック逆転 → Trip(安全側) ----------


def test_ut_001_5_05_clock_regression_trips_failsafe(
    watchdog: SwWatchdog,
    fake_clock: _FakeClock,
    fake_state_machine: MagicMock,
) -> None:
    """SDD §4.8 では「Python 仕様で単調増加保証」としているが、
    注入クロックは逆転し得るため安全側 = Trip。B4 と同じ設計判断。
    """
    watchdog.heartbeat()
    fake_clock.advance(0.1)
    watchdog.heartbeat()
    fake_clock.set_to(0.05)
    watchdog.check_once()
    assert watchdog.is_tripped() is True
    fake_state_machine.on_watchdog_timeout.assert_called_once_with(
        WatchdogReason.SW_WATCHDOG,
    )


# ---------- UT-001.5-06a: Tripped 後の heartbeat は無視 ----------


def test_ut_001_5_06a_heartbeat_ignored_after_trip(
    watchdog: SwWatchdog,
    fake_clock: _FakeClock,
) -> None:
    """Trip 後の heartbeat で `_last_heartbeat` を更新しない(自動復帰禁止、SDD §4.8.E)。"""
    watchdog.heartbeat()
    fake_clock.advance(1.0)
    watchdog.check_once()
    assert watchdog.is_tripped() is True
    snapshot = watchdog.last_heartbeat()

    fake_clock.advance(0.1)
    watchdog.heartbeat()
    assert watchdog.last_heartbeat() == snapshot


# ---------- UT-001.5-06b: check_once 冪等(on_watchdog_timeout は 1 回のみ) ----------


def test_ut_001_5_06b_repeated_check_after_trip_is_idempotent(
    watchdog: SwWatchdog,
    fake_clock: _FakeClock,
    fake_state_machine: MagicMock,
) -> None:
    watchdog.heartbeat()
    fake_clock.advance(1.0)
    watchdog.check_once()
    watchdog.check_once()
    watchdog.check_once()
    assert watchdog.is_tripped() is True
    fake_state_machine.on_watchdog_timeout.assert_called_once_with(
        WatchdogReason.SW_WATCHDOG,
    )


# ---------- UT-001.5-07a: start / stop ライフサイクル ----------


def test_ut_001_5_07a_start_then_stop_lifecycle(watchdog: SwWatchdog) -> None:
    watchdog.start()
    assert watchdog.is_running() is True
    watchdog.stop()
    assert watchdog.is_running() is False


# ---------- UT-001.5-07b: 2 重 start → RuntimeError ----------


def test_ut_001_5_07b_double_start_raises_runtime_error(
    watchdog: SwWatchdog,
) -> None:
    watchdog.start()
    try:
        with pytest.raises(RuntimeError, match="already started"):
            watchdog.start()
    finally:
        watchdog.stop()


# ---------- UT-001.5-07c: 2 重 stop → no-op ----------


def test_ut_001_5_07c_double_stop_is_no_op(watchdog: SwWatchdog) -> None:
    watchdog.start()
    watchdog.stop()
    watchdog.stop()


# ---------- UT-001.5-07d: stop before start → no-op ----------


def test_ut_001_5_07d_stop_before_start_is_no_op(watchdog: SwWatchdog) -> None:
    watchdog.stop()


# ---------- UT-001.5-08: state_machine 例外でクラッシュしない ----------


def test_ut_001_5_08_state_machine_exception_does_not_crash_check_once(
    fake_clock: _FakeClock,
) -> None:
    """SDD §4.8.E: on_watchdog_timeout 例外 → ログ + 次周期再試行(状態遷移は冪等)。

    本 UT では「例外でクラッシュせず Tripped 扱いにする」を検証。
    """
    bad_state_machine = MagicMock()
    bad_state_machine.on_watchdog_timeout.side_effect = RuntimeError("simulated sm fault")
    bad_watchdog = SwWatchdog(state_machine=bad_state_machine, clock=fake_clock)
    bad_watchdog.heartbeat()
    fake_clock.advance(1.0)
    bad_watchdog.check_once()
    assert bad_watchdog.is_tripped() is True


# ---------- UT-001.5-09: 定数 HEARTBEAT_TIMEOUT == 300 ms ----------


def test_ut_001_5_09_heartbeat_timeout_constant_is_300ms() -> None:
    assert pytest.approx(0.3) == HEARTBEAT_TIMEOUT


# ---------- UT-001.5-10: 定数 MONITOR_INTERVAL == 50 ms ----------


def test_ut_001_5_10_monitor_interval_constant_is_50ms() -> None:
    assert pytest.approx(0.05) == MONITOR_INTERVAL


# ---------- UT-001.5-11: 実時間スレッド統合スモーク ----------


def test_ut_001_5_11_real_time_thread_smoke_trips_within_window() -> None:
    """End-to-end smoke: real `time.monotonic` + monitor thread.

    実時間スレッドは OS スケジューリングジッタで flaky になり得るため、
    緩い 1 秒境界で Trip 到達を確認する。並行側スモーク(高頻度 heartbeat)
    は fake_clock 試験(UT-001.5-01 / 04)に委ねる。
    """
    sm = MagicMock()
    wd = SwWatchdog(state_machine=sm, timeout=0.1, monitor_interval=0.02)
    wd.heartbeat()
    wd.start()
    try:
        deadline = time.monotonic() + 1.0
        while time.monotonic() < deadline:
            if wd.is_tripped():
                break
            time.sleep(0.02)
        assert wd.is_tripped() is True
        sm.on_watchdog_timeout.assert_called_with(WatchdogReason.SW_WATCHDOG)
    finally:
        wd.stop()


# ---------- UT-001.5-12: 階層防御(SW が HW より先に Trip) ----------


def test_ut_001_5_12_sw_trips_before_hw_in_layered_defence(
    fake_clock: _FakeClock,
) -> None:
    """SDD §4.8 本体:SW(300 ms)が HW(500 ms)より先に Trip する。

    同一 fake_clock に対して SW Watchdog と HW Failsafe Timer を並行動作させ、
    301 ms 時点では SW のみ Trip、501 ms 時点で HW も Trip することを確認。
    SW 側が先に State 機械を ERROR にするため、HW の最終防衛ラインとの
    二重冗長が時間順序で成立することを証明する。
    """
    sm = MagicMock()
    pump = MagicMock()
    sw = SwWatchdog(state_machine=sm, clock=fake_clock)
    hw = HwFailsafeTimer(pump=pump, clock=fake_clock)

    # 同時に heartbeat 受信
    sw.heartbeat()
    hw.heartbeat()

    # 301 ms 経過:SW のみ Trip
    fake_clock.advance(0.301)
    sw.check_once()
    hw.check_once()
    assert sw.is_tripped() is True
    assert hw.is_tripped() is False

    # さらに 200 ms 経過して通算 501 ms:HW も Trip
    fake_clock.advance(0.2)
    hw.check_once()
    assert hw.is_tripped() is True
