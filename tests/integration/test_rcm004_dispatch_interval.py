"""Integration test — IT-RCM004 (RCM-004 送出間隔、Control Loop + Pump 結合).

ITPR-VIP-001 §6.3 の詳細化(Step 19 F3)。
RCM-004(送出間隔 200 ms ± 10%、SRS-P02、SDD §4.6 / §4.9)が結合状態でも
維持され、Control Loop の `tick()` が **本物 PumpSimulator + 本物
PumpObserver + 本物 Flow Validator** を経由して機能整合的に動作することを
検証する。SRS-P02 ±10% 統計時間試験は §6.8 IT-PERF(Step 19 F5)に分散
配置済。本観点は **機能整合性のみ** に焦点。

設計判断(Step 19 F3 → F1.6 で更新):

* **本物 SUT 比率を F2 からさらに増加**:本物 ControlLoop + 本物
  PumpSimulator + 本物 PumpObserver + 本物 Flow Validator(ControlLoop 内
  ハードコード呼出)+ Mock StateMachine + MagicMock Watchdog 2 件。
* **CR-0005 (a) 解消済(Step 19 F1.6)**:`ControlLoop._HeartbeatSink` Protocol
  を `heartbeat() -> None`(引数なし)に整合化、`ControlLoop._dispatch_*` の
  `self._sw_watchdog.heartbeat()` / `self._hw_watchdog.heartbeat()` 呼出も
  整合化。本物 SwWatchdog/HwFailsafeTimer を ControlLoop に注入できる
  経路は §6.7 IT-SEP(Step 19 F4)で本物階層防御 E2E として実証する。
  本 §6.3 では引き続き機能整合のみに焦点を当てる(Mock 主体維持)。
* `tick()` 直接呼出ベース(ControlLoop の本物スレッドは UT-001.2-19 で
  網羅済 + IT-RCM003.1-05 で SwWatchdog 監視スレッドの実時間検証済)。

関連 SRS: SRS-031、SRS-P02(機能整合のみ、統計時間は §6.8 へ)、SRS-RCM-004。
関連 RCM: RCM-004(SW 送出側 + HW 監視側)。
関連 HZ: HZ-001(過量投与)、HZ-002(流量異常)。
関連 IF-U: IF-U-003(ControlLoop → Pump set_flow_rate)、IF-U-004(ControlLoop →
SwWatchdog heartbeat、CR-0005 解消済)、IF-U-005(ControlLoop → HwFailsafeTimer
heartbeat、CR-0005 解消済)。
関連 UT: UT-001.2(ControlLoop、21 ケース MagicMock 主体)、UT-002.1(PumpSimulator、
21 ケース)、UT-002.2(PumpObserver、10 ケース)。
"""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

import pytest

from vip_ctrl.control_loop import ControlLoop
from vip_ctrl.state_machine import EventKind, State, WatchdogReason
from vip_persist.records import Settings

from .conftest import make_consistent_record_settings

if TYPE_CHECKING:
    from unittest.mock import MagicMock, Mock

    from vip_sim.pump_observer import PumpObserver
    from vip_sim.pump_simulator import PumpSimulator


# 本ファイル全体に integration マーカーを付与
pytestmark = pytest.mark.integration


def _build_control_loop(
    *,
    state_machine: Mock,
    pump: PumpSimulator,
    observer: PumpObserver,
    sw_watchdog: MagicMock,
    hw_watchdog: MagicMock,
    settings: Settings,
) -> ControlLoop:
    """ControlLoop の本物インスタンスを 6 依存注入で組み立てるヘルパ."""
    return ControlLoop(
        state_machine=state_machine,
        pump=pump,
        observer=observer,
        sw_watchdog=sw_watchdog,
        hw_watchdog=hw_watchdog,
        settings_provider=lambda: settings,
    )


# ---------------------------------------------------------------------------
# IT-RCM004.1-01 — 正常系:RUNNING 状態 tick で Pump set_flow_rate + heartbeat 送出
# ---------------------------------------------------------------------------
def test_it_rcm004_1_01_running_tick_dispatches_flow_and_heartbeats(
    mock_running_state_machine: Mock,
    pump_simulator_real: PumpSimulator,
    pump_observer_real: PumpObserver,
    magicmock_sw_heartbeat_sink: MagicMock,
    magicmock_hw_heartbeat_sink: MagicMock,
) -> None:
    """RUNNING + 整合 Settings(flow=60)で `tick()` → Pump に target=60 設定 +
    両 Watchdog に heartbeat 送出。

    結合契約(IF-U-003/004/005):
    - `tick()` が True を返す(SDD §4.6.A 仕様)
    - Pump 内部 `_target_flow` が 60.0 になる(本物 PumpSimulator の
      `set_flow_rate` 経由)
    - SwWatchdog/HwFailsafeTimer の `heartbeat(ts)` が **各 1 回** 呼ばれる
    """
    settings = make_consistent_record_settings(flow_rate=Decimal("60.0"))
    loop = _build_control_loop(
        state_machine=mock_running_state_machine,
        pump=pump_simulator_real,
        observer=pump_observer_real,
        sw_watchdog=magicmock_sw_heartbeat_sink,
        hw_watchdog=magicmock_hw_heartbeat_sink,
        settings=settings,
    )

    assert loop.tick() is True

    # IF-U-003: Pump への target_flow 反映(本物 PumpSimulator の internal state)
    assert pump_simulator_real._target_flow == Decimal("60.0")  # noqa: SLF001
    # IF-U-004 / IF-U-005: 両 Watchdog に heartbeat(ts) 送出
    magicmock_sw_heartbeat_sink.heartbeat.assert_called_once()
    magicmock_hw_heartbeat_sink.heartbeat.assert_called_once()
    # State Machine 遷移は発生しない(正常 dispatch のみ)
    mock_running_state_machine.request_transition.assert_not_called()
    mock_running_state_machine.on_watchdog_timeout.assert_not_called()


# ---------------------------------------------------------------------------
# IT-RCM004.1-02 — tick + advance_time 連続 → Pump 過渡応答が target に追従
# ---------------------------------------------------------------------------
def test_it_rcm004_1_02_pump_transient_response_follows_target_via_tick(
    mock_running_state_machine: Mock,
    pump_simulator_real: PumpSimulator,
    pump_observer_real: PumpObserver,
    magicmock_sw_heartbeat_sink: MagicMock,
    magicmock_hw_heartbeat_sink: MagicMock,
) -> None:
    """tick() を 5 回 + 各回後に `pump.advance_time(0.5)` で時間進行
    → 本物 PumpSimulator の current_flow が target 60 に追従(機能整合のみ).

    SRS-P01 ±5% 過渡応答精度は §6.8 IT-PERF へ分散配置。本ケースは
    「tick 経由で target が反映され、Pump が 0 → 60 mL/h に近づく」契約のみ。
    """
    settings = make_consistent_record_settings(flow_rate=Decimal("60.0"))
    loop = _build_control_loop(
        state_machine=mock_running_state_machine,
        pump=pump_simulator_real,
        observer=pump_observer_real,
        sw_watchdog=magicmock_sw_heartbeat_sink,
        hw_watchdog=magicmock_hw_heartbeat_sink,
        settings=settings,
    )

    initial = pump_observer_real.observe()
    assert initial.current_flow == Decimal("0.0")

    for _ in range(5):
        loop.tick()
        pump_simulator_real.advance_time(0.5)  # 0.5 秒進行

    # 5 tick 後の current_flow は 0 から target=60 方向に増加(機能整合)
    final = pump_observer_real.observe()
    assert final.current_flow > initial.current_flow
    assert final.current_flow > Decimal("0.0")
    # Pump への dispatch は 5 回(tick 毎)
    assert magicmock_sw_heartbeat_sink.heartbeat.call_count == 5
    assert magicmock_hw_heartbeat_sink.heartbeat.call_count == 5


# ---------------------------------------------------------------------------
# IT-RCM004.1-03 — heartbeat は両 Watchdog に引数なしで送出(CR-0005 (a) 解消後)
# ---------------------------------------------------------------------------
def test_it_rcm004_1_03_heartbeat_dispatched_argless_to_both_watchdogs(
    mock_running_state_machine: Mock,
    pump_simulator_real: PumpSimulator,
    pump_observer_real: PumpObserver,
    magicmock_sw_heartbeat_sink: MagicMock,
    magicmock_hw_heartbeat_sink: MagicMock,
) -> None:
    """tick() 1 回で SW/HW 両 heartbeat が **引数なし** で 1 回ずつ呼ばれる契約.

    CR-0005 (a) 解消後の `_HeartbeatSink.heartbeat() -> None` 仕様を結合状態で実証。
    各 Watchdog は内部 clock で timestamp を取得するため、ControlLoop は外部から
    timestamp を渡さない(SDD §4.8.A / §4.3.A)。
    """
    settings = make_consistent_record_settings()
    loop = _build_control_loop(
        state_machine=mock_running_state_machine,
        pump=pump_simulator_real,
        observer=pump_observer_real,
        sw_watchdog=magicmock_sw_heartbeat_sink,
        hw_watchdog=magicmock_hw_heartbeat_sink,
        settings=settings,
    )

    loop.tick()

    # 両 Watchdog の heartbeat() は **引数なし** で 1 回ずつ呼ばれる
    magicmock_sw_heartbeat_sink.heartbeat.assert_called_once_with()
    magicmock_hw_heartbeat_sink.heartbeat.assert_called_once_with()


# ---------------------------------------------------------------------------
# IT-RCM004.1-04 — 異常入力(Validator NEGATIVE)→ State Machine WDT_TIMEOUT 経路
# ---------------------------------------------------------------------------
def test_it_rcm004_1_04_negative_flow_rate_escalates_to_state_machine(
    mock_running_state_machine: Mock,
    pump_simulator_real: PumpSimulator,
    pump_observer_real: PumpObserver,
    magicmock_sw_heartbeat_sink: MagicMock,
    magicmock_hw_heartbeat_sink: MagicMock,
) -> None:
    """flow_rate=-1.0 (Validator NEGATIVE 経路)で tick() →
    StateMachine.request_transition(WDT_TIMEOUT, reason='validation_failed').

    SRS-RCM-004 の **異常検出経路** を本物 Flow Validator 経由で実証。
    Pump への set_flow_rate は呼ばれない(エスカレーション後の dispatch 回避)。
    """
    settings = Settings(
        flow_rate=Decimal("-1.0"),  # 範囲外(本物 Flow Validator が NEGATIVE 検出)
        dose_volume=Decimal("60.0"),
        duration_min=60,
    )
    loop = _build_control_loop(
        state_machine=mock_running_state_machine,
        pump=pump_simulator_real,
        observer=pump_observer_real,
        sw_watchdog=magicmock_sw_heartbeat_sink,
        hw_watchdog=magicmock_hw_heartbeat_sink,
        settings=settings,
    )

    initial_target = pump_simulator_real._target_flow  # noqa: SLF001
    assert loop.tick() is True  # tick 自体は実行(heartbeat 経路は通る)

    # heartbeat は **エスカレーション前** に送出済
    magicmock_sw_heartbeat_sink.heartbeat.assert_called_once()
    magicmock_hw_heartbeat_sink.heartbeat.assert_called_once()
    # StateMachine.request_transition が WDT_TIMEOUT で 1 回呼出
    mock_running_state_machine.request_transition.assert_called_once()
    call_event = mock_running_state_machine.request_transition.call_args.args[0]
    assert call_event.kind is EventKind.WDT_TIMEOUT
    assert call_event.metadata["reason"] == "validation_failed"
    # Pump への set_flow_rate は呼ばれない(target 不変)
    assert pump_simulator_real._target_flow == initial_target  # noqa: SLF001


# ---------------------------------------------------------------------------
# IT-RCM004.1-05 — IDLE 状態では tick が早期 return(skip)
# ---------------------------------------------------------------------------
def test_it_rcm004_1_05_idle_state_tick_skips_dispatch_and_heartbeat(
    pump_simulator_real: PumpSimulator,
    pump_observer_real: PumpObserver,
    magicmock_sw_heartbeat_sink: MagicMock,
    magicmock_hw_heartbeat_sink: MagicMock,
) -> None:
    """StateMachine.current() が IDLE(RUNNING 以外)→ tick は False を返し、
    Pump dispatch も heartbeat も行わない.

    SDD §4.6.A の早期 return 仕様を結合状態で実証。本観点は「Failsafe 発火時
    に Control Loop が安全側に振る舞う」契約の論理的等価:Pump が failsafe
    状態にあるとき、上位の StateMachine は ERROR(または STOPPED)に遷移しており、
    その間 Control Loop が新規 dispatch しないことを保証する。
    """
    from unittest.mock import Mock  # noqa: PLC0415

    from vip_ctrl.state_machine import StateMachine  # noqa: PLC0415

    sm_idle: Mock = Mock(spec=StateMachine)
    sm_idle.current.return_value = State.IDLE

    settings = make_consistent_record_settings()
    loop = _build_control_loop(
        state_machine=sm_idle,
        pump=pump_simulator_real,
        observer=pump_observer_real,
        sw_watchdog=magicmock_sw_heartbeat_sink,
        hw_watchdog=magicmock_hw_heartbeat_sink,
        settings=settings,
    )

    initial_target = pump_simulator_real._target_flow  # noqa: SLF001
    assert loop.tick() is False  # 早期 return

    # heartbeat / dispatch / 状態遷移 すべて呼ばれない
    magicmock_sw_heartbeat_sink.heartbeat.assert_not_called()
    magicmock_hw_heartbeat_sink.heartbeat.assert_not_called()
    sm_idle.request_transition.assert_not_called()
    sm_idle.on_watchdog_timeout.assert_not_called()
    assert pump_simulator_real._target_flow == initial_target  # noqa: SLF001
    # WatchdogReason は使わないが、import の sentinel として参照
    assert WatchdogReason.SW_WATCHDOG.name == "SW_WATCHDOG"
