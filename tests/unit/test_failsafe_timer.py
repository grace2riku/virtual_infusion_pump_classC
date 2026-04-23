"""UT-002.4 — HW-side Failsafe Timer (UNIT-002.4 per SDD-VIP-001 §4.3).

Implements UTPR-VIP-001 §7.3.3 test cases UT-002.4-01 .. UT-002.4-08.
Covers RCM-004 HW-side (independent heartbeat watchdog on the pump side)
per RMF-VIP-001 §6.1.

Step 19 B4 reconciles UTPR §7.3.3 with SDD §4.3 and adds two design
judgments noted in DEVELOPMENT_STEPS.md:

* Clock injection (`clock` parameter) for deterministic tests; production
  uses `time.monotonic`.
* Clock regression (`now < last`) is treated as a safety-side trip
  (SDD §4.3 leaves this case undefined; RCM-004 demands fail-safe).
* Logger plumbing is deferred — the HW failsafe identifier is carried by
  the `reason="HEARTBEAT_TIMEOUT"` argument of `force_stop_failsafe`.

Related SRS: SRS-RCM-004, SRS-032.
Related HZ:  HZ-001 (over-delivery), HZ-002 (under-delivery).
"""

from __future__ import annotations

import threading
import time
from unittest.mock import MagicMock

import pytest

from vip_sim.failsafe_timer import (
    HEARTBEAT_TIMEOUT,
    MONITOR_INTERVAL,
    HwFailsafeTimer,
)

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
def fake_pump() -> MagicMock:
    return MagicMock()


@pytest.fixture
def fake_clock() -> _FakeClock:
    return _FakeClock()


@pytest.fixture
def timer(fake_pump: MagicMock, fake_clock: _FakeClock) -> HwFailsafeTimer:
    return HwFailsafeTimer(pump=fake_pump, clock=fake_clock)


# ---------- UT-002.4-01: 正常受信、発火しない ----------


def test_ut_002_4_01_periodic_heartbeat_does_not_trip(
    timer: HwFailsafeTimer,
    fake_clock: _FakeClock,
) -> None:
    timer.heartbeat()
    for _ in range(10):
        fake_clock.advance(0.1)
        timer.heartbeat()
        timer.check_once()
    assert timer.is_tripped() is False


# ---------- UT-002.4-02: ハートビート途絶検知 ----------


def test_ut_002_4_02_heartbeat_silence_trips_failsafe(
    timer: HwFailsafeTimer,
    fake_clock: _FakeClock,
    fake_pump: MagicMock,
) -> None:
    timer.heartbeat()
    fake_clock.advance(0.501)
    timer.check_once()
    assert timer.is_tripped() is True
    fake_pump.force_stop_failsafe.assert_called_once_with(reason="HEARTBEAT_TIMEOUT")


# ---------- UT-002.4-03: 境界 499 ms ----------


def test_ut_002_4_03_below_timeout_does_not_trip(
    timer: HwFailsafeTimer,
    fake_clock: _FakeClock,
) -> None:
    timer.heartbeat()
    fake_clock.advance(0.499)
    timer.check_once()
    assert timer.is_tripped() is False


# ---------- UT-002.4-04a: 境界 500 ms ちょうど(`>` 判定で発火しない) ----------


def test_ut_002_4_04a_exact_timeout_does_not_trip(
    timer: HwFailsafeTimer,
    fake_clock: _FakeClock,
) -> None:
    """SDD §4.3.C: `(now - last) > timeout`. 境界値は発火しない。"""
    timer.heartbeat()
    fake_clock.advance(HEARTBEAT_TIMEOUT)
    timer.check_once()
    assert timer.is_tripped() is False


# ---------- UT-002.4-04b: 境界 500 ms + ε(発火) ----------


def test_ut_002_4_04b_just_above_timeout_trips(
    timer: HwFailsafeTimer,
    fake_clock: _FakeClock,
) -> None:
    timer.heartbeat()
    fake_clock.advance(HEARTBEAT_TIMEOUT + 0.0001)
    timer.check_once()
    assert timer.is_tripped() is True


# ---------- UT-002.4-05: 並行 heartbeat ----------


def test_ut_002_4_05_concurrent_heartbeats_no_data_race(
    timer: HwFailsafeTimer,
    fake_clock: _FakeClock,
) -> None:
    """2 スレッドから heartbeat を連打。Lock により最終値が最新 clock と一致。"""
    timer.heartbeat()
    barrier = threading.Barrier(2)

    def worker(advance_each: float) -> None:
        barrier.wait()
        for _ in range(50):
            fake_clock.advance(advance_each)
            timer.heartbeat()

    t1 = threading.Thread(target=worker, args=(0.001,))
    t2 = threading.Thread(target=worker, args=(0.001,))
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    timer.check_once()
    assert timer.is_tripped() is False
    assert timer.last_heartbeat() == fake_clock()


# ---------- UT-002.4-06: HW failsafe 識別子(reason) ----------


def test_ut_002_4_06_force_stop_called_with_hw_failsafe_reason(
    timer: HwFailsafeTimer,
    fake_clock: _FakeClock,
    fake_pump: MagicMock,
) -> None:
    """SW WDT(UNIT-001.5)とは独立に HW 側で発火することを reason 文字列で識別。"""
    timer.heartbeat()
    fake_clock.advance(1.0)
    timer.check_once()
    fake_pump.force_stop_failsafe.assert_called_once_with(reason="HEARTBEAT_TIMEOUT")


# ---------- UT-002.4-07: クロック逆転 → 発火(安全側) ----------


def test_ut_002_4_07_clock_regression_trips_failsafe(
    timer: HwFailsafeTimer,
    fake_clock: _FakeClock,
    fake_pump: MagicMock,
) -> None:
    """SDD §4.3 では未定義。設計判断:逆転(`now < last`)は安全側 = 発火。"""
    timer.heartbeat()
    fake_clock.advance(0.2)
    timer.heartbeat()
    fake_clock.set_to(0.05)
    timer.check_once()
    assert timer.is_tripped() is True
    fake_pump.force_stop_failsafe.assert_called_once_with(reason="HEARTBEAT_TIMEOUT")


# ---------- UT-002.4-08: Tripped 後 heartbeat 無視 / 冪等 ----------


def test_ut_002_4_08a_heartbeat_ignored_after_trip(
    timer: HwFailsafeTimer,
    fake_clock: _FakeClock,
) -> None:
    timer.heartbeat()
    fake_clock.advance(1.0)
    timer.check_once()
    assert timer.is_tripped() is True
    snapshot = timer.last_heartbeat()

    fake_clock.advance(0.1)
    timer.heartbeat()
    assert timer.last_heartbeat() == snapshot


def test_ut_002_4_08b_repeated_check_after_trip_is_idempotent(
    timer: HwFailsafeTimer,
    fake_clock: _FakeClock,
    fake_pump: MagicMock,
) -> None:
    timer.heartbeat()
    fake_clock.advance(1.0)
    timer.check_once()
    timer.check_once()
    timer.check_once()
    assert timer.is_tripped() is True
    fake_pump.force_stop_failsafe.assert_called_once()


# ---------- 補助観点:start / stop ライフサイクル ----------


def test_start_then_stop_lifecycle(timer: HwFailsafeTimer) -> None:
    timer.start()
    assert timer.is_running() is True
    timer.stop()
    assert timer.is_running() is False


def test_double_start_raises_runtime_error(timer: HwFailsafeTimer) -> None:
    timer.start()
    try:
        with pytest.raises(RuntimeError, match="already started"):
            timer.start()
    finally:
        timer.stop()


def test_double_stop_is_no_op(timer: HwFailsafeTimer) -> None:
    timer.start()
    timer.stop()
    timer.stop()


def test_stop_before_start_is_no_op(timer: HwFailsafeTimer) -> None:
    timer.stop()


# ---------- 補助観点:pump 例外でクラッシュしない ----------


def test_pump_exception_does_not_crash_check_once(
    fake_clock: _FakeClock,
) -> None:
    bad_pump = MagicMock()
    bad_pump.force_stop_failsafe.side_effect = RuntimeError("simulated pump fault")
    bad_timer = HwFailsafeTimer(pump=bad_pump, clock=fake_clock)
    bad_timer.heartbeat()
    fake_clock.advance(1.0)
    bad_timer.check_once()
    assert bad_timer.is_tripped() is True


# ---------- 補助観点:定数値 ----------


def test_heartbeat_timeout_constant_is_500ms() -> None:
    assert pytest.approx(0.5) == HEARTBEAT_TIMEOUT


def test_monitor_interval_constant_is_100ms() -> None:
    assert pytest.approx(0.1) == MONITOR_INTERVAL


# ---------- 統合スモーク:実時間 + 監視スレッド ----------


def test_real_time_thread_smoke_trips_within_window() -> None:
    """End-to-end smoke: real `time.monotonic` + monitor thread.

    1 秒以内の発火を要求する緩い境界。OS スケジューリングのジッタに強い。
    連打耐性側のスモークは macOS sleep ジッタで本質的に flaky のため
    fake_clock 試験(UT-002.4-01 / 05)に委ねる(本判断は DEVELOPMENT_STEPS
    の教訓に記録)。
    """
    pump = MagicMock()
    timer_obj = HwFailsafeTimer(pump=pump, timeout=0.1, monitor_interval=0.02)
    timer_obj.heartbeat()
    timer_obj.start()
    try:
        deadline = time.monotonic() + 1.0
        while time.monotonic() < deadline:
            if timer_obj.is_tripped():
                break
            time.sleep(0.02)
        assert timer_obj.is_tripped() is True
        pump.force_stop_failsafe.assert_called_with(reason="HEARTBEAT_TIMEOUT")
    finally:
        timer_obj.stop()
