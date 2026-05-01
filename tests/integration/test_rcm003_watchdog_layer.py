"""Integration test — IT-RCM003 (SW Watchdog + 階層防御 SW<HW、本物実時間連動).

ITPR-VIP-001 §6.2 の詳細化(Step 19 F2)。
SwWatchdog(RCM-003、SDD §4.8、timeout 300 ms)+ HwFailsafeTimer(RCM-004
HW 側、SDD §4.3、timeout 500 ms)の **階層防御時間順序** が結合状態でも
維持されることを **本物 `time.monotonic` + 実時間 `time.sleep`** で検証する。

設計判断(Step 19 F2):

* IT-RCM003.1-01〜04 / 06 は `check_once()` 直接呼出ベース(monitor スレッド
  非起動)で **境界判定の決定性を確保**(monitor スレッドの `monitor_interval`
  ジッタを排除して観点を絞る)。
* IT-RCM003.1-05 のみ **本物 monitor スレッドを起動**(`start()`)し、
  実時間タイマー精度 + start/stop lifecycle の組み合わせを実証(F1 の
  Mock パターンから一歩進めた「複数ユニット結合 + 本物実時間連動」観点)。
* 当初検討した「クロック逆転耐性」は UT-001.5-04 等の fake_clock 試験で
  網羅済のため IT 化せず、上記スレッド試験に置換(Step 19 F2 着手前
  クロスレビューで判断、ユーザー合意済)。
* macOS sleep ジッタ対策(Step 19 B4 教訓):実時間境界の判定は **緩い余裕**
  (sleep 後の経過 ≥ timeout + 50 ms 以上)を確保、フレーキー回避。

関連 SRS: SRS-RCM-003、SRS-RCM-004。
関連 RCM: RCM-003(SW Watchdog 300 ms)、RCM-004(HW Watchdog 500 ms 階層防御)。
関連 HZ: HZ-001(過量投与)、HZ-002(流量異常)。
関連 IF-U: IF-U-004(ControlLoop → SwWatchdog)、IF-U-005(ControlLoop → HwFailsafeTimer)、
IF-U-006(SwWatchdog → StateMachine)、IF-U-007(HwFailsafeTimer → Pump)。
関連 UT: UT-001.5(SwWatchdog、19 ケース fake_clock 主体)、UT-002.4(HwFailsafeTimer、
18 ケース fake_clock 主体)。
"""

from __future__ import annotations

import threading
import time
from typing import TYPE_CHECKING

import pytest

from vip_ctrl.state_machine import WatchdogReason

if TYPE_CHECKING:
    from unittest.mock import Mock

    from vip_ctrl.watchdog import SwWatchdog
    from vip_sim.failsafe_timer import HwFailsafeTimer


# 本ファイル全体に integration マーカーを付与
pytestmark = pytest.mark.integration


# ---------------------------------------------------------------------------
# IT-RCM003.1-01 — 正常系: 両 Watchdog が継続 heartbeat 下で発火しない
# ---------------------------------------------------------------------------
def test_it_rcm003_1_01_neither_watchdog_fires_with_continuous_heartbeat(
    sw_watchdog_real: SwWatchdog,
    hw_failsafe_timer_real: HwFailsafeTimer,
    mock_state_machine: Mock,
    mock_pump_controller: Mock,
) -> None:
    """50 ms 間隔で 1 秒間継続的に heartbeat → 両 Watchdog 不発火.

    SW timeout 300 ms / HW timeout 500 ms 共に最後の heartbeat から
    50 ms 以下しか経過しない条件下では発火しない契約を実時間で実証。
    """
    deadline = time.monotonic() + 1.0
    while time.monotonic() < deadline:
        sw_watchdog_real.heartbeat()
        hw_failsafe_timer_real.heartbeat()
        time.sleep(0.05)

    assert sw_watchdog_real.check_once() is False
    assert hw_failsafe_timer_real.check_once() is False
    assert not sw_watchdog_real.is_tripped()
    assert not hw_failsafe_timer_real.is_tripped()
    mock_state_machine.on_watchdog_timeout.assert_not_called()
    mock_pump_controller.force_stop_failsafe.assert_not_called()


# ---------------------------------------------------------------------------
# IT-RCM003.1-02 — SW Watchdog 単独発火(SW 350 ms / HW 350 ms 経過)
# ---------------------------------------------------------------------------
def test_it_rcm003_1_02_sw_watchdog_fires_alone_after_sw_timeout(
    sw_watchdog_real: SwWatchdog,
    hw_failsafe_timer_real: HwFailsafeTimer,
    mock_state_machine: Mock,
    mock_pump_controller: Mock,
) -> None:
    """heartbeat 停止 → 350 ms 経過: SW(300 ms 超)発火、HW(500 ms 未満)未発火.

    階層防御の **SW 先行** 性を機能整合性レベルで実証。
    """
    sw_watchdog_real.heartbeat()
    hw_failsafe_timer_real.heartbeat()
    time.sleep(0.35)  # SW 300 ms 超 + HW 500 ms 未満

    assert sw_watchdog_real.check_once() is True  # SW 発火
    assert hw_failsafe_timer_real.check_once() is False  # HW 未発火
    mock_state_machine.on_watchdog_timeout.assert_called_once_with(
        WatchdogReason.SW_WATCHDOG,
    )
    mock_pump_controller.force_stop_failsafe.assert_not_called()


# ---------------------------------------------------------------------------
# IT-RCM003.1-03 — 階層防御時間順序: SW 先行発火後の HW 後続経過
# ---------------------------------------------------------------------------
def test_it_rcm003_1_03_sw_fires_first_then_hw_with_state_machine_idempotent(
    sw_watchdog_real: SwWatchdog,
    hw_failsafe_timer_real: HwFailsafeTimer,
    mock_state_machine: Mock,
    mock_pump_controller: Mock,
) -> None:
    """heartbeat 停止 → SW(350 ms 経過、発火)→ さらに 250 ms 経過(累積 600 ms、HW も超過).

    階層防御契約: (1) SW が **先に** 発火し StateMachine ERROR を 1 回だけ呼出、
    (2) HW が **後に** 発火しても StateMachine 二重遷移なし(SwWatchdog 冪等)、
    (3) 一方で Pump への HW 強制停止呼出は HW 側の独立契約として実行される。
    """
    sw_watchdog_real.heartbeat()
    hw_failsafe_timer_real.heartbeat()

    # フェーズ 1: SW のみ発火する時間帯
    time.sleep(0.35)
    sw_watchdog_real.check_once()  # SW 発火
    assert sw_watchdog_real.is_tripped()
    assert not hw_failsafe_timer_real.is_tripped()

    # フェーズ 2: HW も発火する時間帯
    time.sleep(0.25)  # 累積 600 ms
    hw_failsafe_timer_real.check_once()  # HW 発火
    assert hw_failsafe_timer_real.is_tripped()

    # SwWatchdog の冪等性: SW 発火後に check_once を再度呼んでも StateMachine への
    # on_watchdog_timeout は最初の 1 回のみ(SDD §4.8 冪等性契約)。
    sw_watchdog_real.check_once()  # 2 回目の呼出
    mock_state_machine.on_watchdog_timeout.assert_called_once_with(
        WatchdogReason.SW_WATCHDOG,
    )
    # HW は独立契約で Pump への停止指示を 1 回呼出
    mock_pump_controller.force_stop_failsafe.assert_called_once_with(
        reason="HEARTBEAT_TIMEOUT",
    )


# ---------------------------------------------------------------------------
# IT-RCM003.1-04 — HW Watchdog 単独発火(SW Watchdog 起動なしシナリオ)
# ---------------------------------------------------------------------------
def test_it_rcm003_1_04_hw_watchdog_fires_independently_when_sw_inactive(
    hw_failsafe_timer_real: HwFailsafeTimer,
    mock_pump_controller: Mock,
) -> None:
    """SW Watchdog を起動しないシナリオ → HW のみで Pump 強制停止が発火する.

    階層防御の **HW 独立性**(SW 系統障害でも HW で安全側担保)を実証。
    SDD §4.3 通り `force_stop_failsafe(reason="HEARTBEAT_TIMEOUT")` を 1 回呼出。
    """
    hw_failsafe_timer_real.heartbeat()
    time.sleep(0.55)  # HW 500 ms 超

    assert hw_failsafe_timer_real.check_once() is True
    assert hw_failsafe_timer_real.is_tripped()
    mock_pump_controller.force_stop_failsafe.assert_called_once_with(
        reason="HEARTBEAT_TIMEOUT",
    )


# ---------------------------------------------------------------------------
# IT-RCM003.1-05 — 監視スレッド経由の自動トリップ(本物 lifecycle + 実時間)
# ---------------------------------------------------------------------------
def test_it_rcm003_1_05_sw_monitor_thread_auto_trips_on_heartbeat_stop(
    sw_watchdog_real: SwWatchdog,
    mock_state_machine: Mock,
) -> None:
    """`SwWatchdog.start()` で監視スレッド起動 → heartbeat 停止 → 自動検出 → トリップ.

    UT-001.5 で fake_clock 経由の `check_once` 直接呼出は網羅済のため、
    本 IT は **本物 monitor スレッド + 実時間 timer 精度** の組み合わせを実証
    (`start/stop` lifecycle の確実な動作 + `monitor_interval=50 ms` 周期での
    自動検出 + State Machine への自動通知)。
    """
    sw_watchdog_real.heartbeat()
    sw_watchdog_real.start()
    try:
        # 350 ms + 余裕 100 ms = 450 ms 待機(monitor_interval=50 ms で 9 周期相当)
        time.sleep(0.45)
    finally:
        sw_watchdog_real.stop()

    assert sw_watchdog_real.is_tripped()
    mock_state_machine.on_watchdog_timeout.assert_called_with(
        WatchdogReason.SW_WATCHDOG,
    )


# ---------------------------------------------------------------------------
# IT-RCM003.1-06 — 高頻度並行 heartbeat の Lock 競合なし(deadlock-free)
# ---------------------------------------------------------------------------
def test_it_rcm003_1_06_concurrent_high_frequency_heartbeat_no_lock_contention(
    sw_watchdog_real: SwWatchdog,
    hw_failsafe_timer_real: HwFailsafeTimer,
) -> None:
    """2 スレッドから 1 ms 間隔で 100 回 heartbeat を並行送信 → Lock 競合なし.

    SDD §4.8.B / §4.3.B で規定の `Lock` 保護下での `_last_heartbeat` 更新が、
    実時間並行下でも deadlock せず両スレッドが完走することを実証。
    timeout を 1 sec に拡大し本試験中に Watchdog が発火しない条件下で
    検証(Lock 競合のみに焦点)。
    """
    # 通常 fixture は 0.3/0.5 sec timeout だが、並行性試験では十分に長くする
    # (試験総時間が timeout に達するとフレーキー要因になる)
    sw_long = type(sw_watchdog_real)(
        sw_watchdog_real._state_machine,  # noqa: SLF001
        timeout=2.0,
    )
    hw_long = type(hw_failsafe_timer_real)(
        hw_failsafe_timer_real._pump,  # noqa: SLF001
        timeout=2.0,
    )

    iterations_per_thread = 100

    def heartbeat_loop() -> None:
        for _ in range(iterations_per_thread):
            sw_long.heartbeat()
            hw_long.heartbeat()
            time.sleep(0.001)  # 1 ms 間隔

    threads = [threading.Thread(target=heartbeat_loop) for _ in range(2)]
    start_at = time.monotonic()
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=2.0)
    elapsed = time.monotonic() - start_at

    # 全スレッド完走(deadlock していれば join がタイムアウトして t.is_alive() が True)
    for t in threads:
        assert not t.is_alive(), "deadlock detected: thread did not complete"
    # 試験総時間 < timeout(2 sec)で完了したため Watchdog 不発火
    assert elapsed < 2.0
    assert not sw_long.is_tripped()
    assert not hw_long.is_tripped()
