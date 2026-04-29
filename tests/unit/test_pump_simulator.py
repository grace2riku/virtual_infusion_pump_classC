"""UT-002.1 — Pump Simulator (UNIT-002.1 per SDD-VIP-001 §4.9).

Implements UTPR-VIP-001 §7.3.10 test cases UT-002.1-01 .. UT-002.1-21.
Covers RCM-004 HW-side callee (`force_stop_failsafe`) and SRS-030/031/P01
per RMF-VIP-001 §6.1.

Step 19 B11 design judgments (recorded in DEVELOPMENT_STEPS.md):

* SRS-031 observation contract is exposed via thread-safe getters
  (`current_flow` / `accumulated_volume` / `elapsed_min` /
  `is_failsafe_active` / `failsafe_reason`). UNIT-002.2 Pump Observer
  (a future TDD step) will wrap them in a frozen `PumpSnapshot`.
* Accumulation overflow (>9999.9 mL per SRS-I-020) emits a
  `logger.warning` and continues; clamping is not done.
* `release_failsafe()` is implemented public for unit testability;
  the production wiring via UNIT-005.1 (CMD_ERROR_RESET) will land later.

Related SRS: SRS-030, SRS-031, SRS-P01, SRS-RCM-004 (HW-side callee).
Related HZ:  HZ-001 (over-delivery), HZ-002 (under-delivery).
"""

from __future__ import annotations

import threading
from decimal import Decimal

import pytest

from vip_sim.pump_simulator import (
    MAX_ACCUMULATED_VOLUME,
    TIME_CONSTANT_SEC,
    PumpSimulator,
)

# ---------- helpers ----------


def _approx(value: Decimal, expected: Decimal, tolerance: Decimal) -> bool:
    """Return True when |value - expected| <= tolerance."""
    return abs(value - expected) <= tolerance


# ---------- UT-002.1-01: 初期状態 ----------


def test_ut_002_1_01_initial_state_is_zero() -> None:
    """初期状態で current_flow / accumulated_volume / elapsed_min はすべて 0。"""
    pump = PumpSimulator()
    assert pump.current_flow() == Decimal(0)
    assert pump.accumulated_volume() == Decimal(0)
    assert pump.elapsed_min() == Decimal(0)
    assert pump.is_failsafe_active() is False
    assert pump.failsafe_reason() is None


# ---------- UT-002.1-02: set_flow_rate で target が更新される ----------


def test_ut_002_1_02_set_flow_rate_updates_target() -> None:
    """SDD §4.9.A: 内部目標値更新、次 advance_time で実流量が漸近。"""
    pump = PumpSimulator()
    pump.set_flow_rate(Decimal(500))
    # 直接の target_flow getter は契約外。advance_time(短時間) 後に変化を観測
    pump.advance_time(0.001)
    assert pump.current_flow() > Decimal(0)


# ---------- UT-002.1-03: 過渡応答 0.5 s ≈ 63%(SRS-P01 一次遅れ τ=0.5)----------


def test_ut_002_1_03_transient_response_at_one_tau_reaches_63_percent() -> None:
    """SDD §4.9 過渡応答試験:`advance_time(τ)` で 63% (=1-1/e) に到達。"""
    pump = PumpSimulator()
    pump.set_flow_rate(Decimal(500))
    pump.advance_time(TIME_CONSTANT_SEC)
    # 1-exp(-1) ≈ 0.632、許容 ±5% (50/1000)
    expected = Decimal(500) * Decimal("0.6321")
    assert _approx(pump.current_flow(), expected, Decimal(25))


# ---------- UT-002.1-04: 過渡応答 5τ ≈ 99% ----------


def test_ut_002_1_04_transient_response_at_five_tau_reaches_99_percent() -> None:
    """SDD §4.9: `advance_time(5τ)` で 99% (=1-exp(-5)) 到達。"""
    pump = PumpSimulator()
    pump.set_flow_rate(Decimal(500))
    pump.advance_time(TIME_CONSTANT_SEC * 5)
    # 1-exp(-5) ≈ 0.9933、許容 ±2%
    expected = Decimal(500) * Decimal("0.9933")
    assert _approx(pump.current_flow(), expected, Decimal(10))


# ---------- UT-002.1-05: advance_time(0) → ValueError ----------


def test_ut_002_1_05_advance_time_zero_raises_value_error() -> None:
    pump = PumpSimulator()
    with pytest.raises(ValueError, match="dt must be positive"):
        pump.advance_time(0.0)


# ---------- UT-002.1-06: advance_time(負) → ValueError ----------


def test_ut_002_1_06_advance_time_negative_raises_value_error() -> None:
    pump = PumpSimulator()
    with pytest.raises(ValueError, match="dt must be positive"):
        pump.advance_time(-1.0)


# ---------- UT-002.1-07: 1 時間で 100 mL/h → 積算 ≈100 mL(SRS-P01 ±5%)----------


def test_ut_002_1_07_accumulation_after_one_hour_is_within_5_percent() -> None:
    """SDD §4.9.F 積算量試験:100 mL/h で 1 時間 → 100 mL ±5%。"""
    pump = PumpSimulator()
    pump.set_flow_rate(Decimal(100))
    pump.advance_time(3600.0)
    # 過渡応答が 5τ で 99% 到達するため、定常状態とほぼ同じ
    actual = pump.accumulated_volume()
    assert _approx(actual, Decimal(100), Decimal(5))


# ---------- UT-002.1-08: force_stop_failsafe で current/target=0 ----------


def test_ut_002_1_08_force_stop_failsafe_zeros_flow() -> None:
    pump = PumpSimulator()
    pump.set_flow_rate(Decimal(500))
    pump.advance_time(2.5)  # current_flow ≈ 99% to 500
    pump.force_stop_failsafe(reason="HEARTBEAT_TIMEOUT")
    assert pump.current_flow() == Decimal(0)
    assert pump.is_failsafe_active() is True
    assert pump.failsafe_reason() == "HEARTBEAT_TIMEOUT"


# ---------- UT-002.1-09: force_stop_failsafe 冪等(初発 reason 保持)----------


def test_ut_002_1_09_force_stop_failsafe_is_idempotent_first_reason_kept() -> None:
    """SDD §4.9.A: 冪等(2 回目以降は最初の reason を保持)。"""
    pump = PumpSimulator()
    pump.force_stop_failsafe(reason="REASON_FIRST")
    pump.force_stop_failsafe(reason="REASON_SECOND")
    assert pump.failsafe_reason() == "REASON_FIRST"


# ---------- UT-002.1-10: failsafe 中の set_flow_rate は no-op ----------


def test_ut_002_1_10_set_flow_rate_is_noop_during_failsafe() -> None:
    pump = PumpSimulator()
    pump.force_stop_failsafe(reason="X")
    pump.set_flow_rate(Decimal(500))
    pump.advance_time(2.5)
    assert pump.current_flow() == Decimal(0)


# ---------- UT-002.1-11: failsafe 中の reset は no-op ----------


def test_ut_002_1_11_reset_is_noop_during_failsafe() -> None:
    """SDD §4.9.A: failsafe 中: no-op + ログ。"""
    pump = PumpSimulator()
    pump.force_stop_failsafe(reason="X")
    pump.reset()  # 例外なし、failsafe フラグも維持
    assert pump.is_failsafe_active() is True


# ---------- UT-002.1-12: failsafe 中 advance_time は時間のみ進む ----------


def test_ut_002_1_12_advance_time_during_failsafe_progresses_time_only() -> None:
    """SDD §4.9.C: failsafe 中は流量 0 を維持、時間進行のみ(積算は加算しない)。"""
    pump = PumpSimulator()
    pump.set_flow_rate(Decimal(500))
    pump.advance_time(1.0)  # 一定流量に近づく
    pump.force_stop_failsafe(reason="X")
    accumulated_at_failsafe = pump.accumulated_volume()
    elapsed_at_failsafe = pump.elapsed_min()

    pump.advance_time(60.0)  # 1 分経過

    assert pump.current_flow() == Decimal(0)
    assert pump.accumulated_volume() == accumulated_at_failsafe  # 不変
    assert pump.elapsed_min() > elapsed_at_failsafe  # 時間は進む


# ---------- UT-002.1-13: release_failsafe で復帰、set_flow_rate 機能 ----------


def test_ut_002_1_13_release_failsafe_re_enables_flow() -> None:
    pump = PumpSimulator()
    pump.force_stop_failsafe(reason="X")
    pump.release_failsafe()
    assert pump.is_failsafe_active() is False
    pump.set_flow_rate(Decimal(500))
    pump.advance_time(2.5)
    # 過渡応答 5τ で 99% 到達
    assert pump.current_flow() > Decimal(400)


# ---------- UT-002.1-14: release_failsafe 未発動時は no-op ----------


def test_ut_002_1_14_release_failsafe_when_not_active_is_no_op() -> None:
    """SDD §4.9.A: 未発動: no-op。"""
    pump = PumpSimulator()
    pump.release_failsafe()
    assert pump.is_failsafe_active() is False


# ---------- UT-002.1-15: reset() で全状態が初期値 ----------


def test_ut_002_1_15_reset_clears_all_state() -> None:
    pump = PumpSimulator()
    pump.set_flow_rate(Decimal(300))
    pump.advance_time(10.0)
    assert pump.accumulated_volume() > Decimal(0)
    pump.reset()
    assert pump.current_flow() == Decimal(0)
    assert pump.accumulated_volume() == Decimal(0)
    assert pump.elapsed_min() == Decimal(0)


# ---------- UT-002.1-16: 定数 TIME_CONSTANT_SEC == 0.5 ----------


def test_ut_002_1_16_time_constant_is_500ms() -> None:
    assert pytest.approx(0.5) == TIME_CONSTANT_SEC


# ---------- UT-002.1-17: 並行性 — failsafe が set_flow_rate と競合しても勝つ ----------


def test_ut_002_1_17_failsafe_wins_concurrent_set_flow_rate() -> None:
    """SDD §4.9.D: Control Loop と HW Failsafe Timer の別スレッドからの呼出で
    failsafe が勝つこと(RLock + 状態フラグの一貫性)。
    """
    pump = PumpSimulator()
    pump.set_flow_rate(Decimal(500))
    pump.advance_time(2.5)  # 流量を 99% まで上げる

    barrier = threading.Barrier(2)
    failsafe_done = threading.Event()

    def setter() -> None:
        barrier.wait()
        for _ in range(100):
            pump.set_flow_rate(Decimal(500))

    def trigger() -> None:
        barrier.wait()
        pump.force_stop_failsafe(reason="CONCURRENT_TEST")
        failsafe_done.set()

    t1 = threading.Thread(target=setter)
    t2 = threading.Thread(target=trigger)
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    assert failsafe_done.is_set()
    assert pump.is_failsafe_active() is True
    assert pump.current_flow() == Decimal(0)


# ---------- UT-002.1-18: 境界 — set_flow_rate(0) で 0 維持 ----------


def test_ut_002_1_18_set_flow_rate_zero_keeps_zero_flow() -> None:
    pump = PumpSimulator()
    pump.set_flow_rate(Decimal(0))
    pump.advance_time(5.0)
    assert pump.current_flow() == Decimal(0)
    assert pump.accumulated_volume() == Decimal(0)


# ---------- UT-002.1-19: 境界 — set_flow_rate(1200) 上限 ----------


def test_ut_002_1_19_set_flow_rate_max_reaches_1200() -> None:
    """SRS-O-001 上限 1200 mL/h で安定に到達(±5%)。"""
    pump = PumpSimulator()
    pump.set_flow_rate(Decimal(1200))
    pump.advance_time(2.5)  # 5τ で 99%
    expected = Decimal(1200) * Decimal("0.9933")
    assert _approx(pump.current_flow(), expected, Decimal(60))


# ---------- UT-002.1-20: 積算量オーバーフロー警告(>9999.9 mL)----------


def test_ut_002_1_20_accumulation_overflow_emits_warning(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """SDD §4.9.F: `accumulated_volume` の 9999.9 越えはオーバーフロー警告。

    9999.9 を越えても加算は継続(Inc.1 範囲)、警告ログのみ出力する。
    """
    pump = PumpSimulator()
    pump.set_flow_rate(Decimal(1200))  # 最大流量
    # 過渡応答完了させてから定常状態で大量積算
    pump.advance_time(2.5)
    with caplog.at_level("WARNING", logger="vip_sim.pump_simulator"):
        # 1200 mL/h * 9 hours = 10800 mL > 9999.9
        pump.advance_time(3600.0 * 9)
    assert pump.accumulated_volume() > MAX_ACCUMULATED_VOLUME
    assert any("overflow" in rec.message.lower() for rec in caplog.records)


# ---------- UT-002.1-21: SRS-031 観測契約 ----------


def test_ut_002_1_21_srs_031_observation_contract() -> None:
    """SRS-031: 仮想ポンプモデルは <現在流量, 積算量, 経過時間, 機構状態> を観測可能。

    本ユニットの 5 getter (current_flow / accumulated_volume / elapsed_min /
    is_failsafe_active / failsafe_reason) で SRS-031 4 項目 + failsafe 拡張を網羅。
    """
    pump = PumpSimulator()
    pump.set_flow_rate(Decimal(100))
    pump.advance_time(60.0)
    pump.force_stop_failsafe(reason="OBSERVATION_TEST")

    # 観測値が型整合
    assert isinstance(pump.current_flow(), Decimal)
    assert isinstance(pump.accumulated_volume(), Decimal)
    assert isinstance(pump.elapsed_min(), Decimal)
    assert isinstance(pump.is_failsafe_active(), bool)
    assert isinstance(pump.failsafe_reason(), str)
