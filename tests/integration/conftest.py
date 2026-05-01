"""Integration test fixtures (ITPR-VIP-001 §6).

Step 19 F0 で骨格化、Step 19 F1 で RCM-001 用 fixture 群を追加。
各観点(F1: RCM-001 / F2: RCM-003 / F3: RCM-004 / F4: SEP-001 /
F5: IT-PERF / F6: IT-PWR / F7: IT-SIDE)で本 conftest を拡張する想定。

設計方針(Step 19 F1):

* `Mock(spec=...)` 系 fixture は UT-005.1(`tests/unit/test_control_api.py`)の
  パターンを踏襲 — IT 観点では「ユニット間の **契約整合**」検証に焦点を当て、
  各ユニット内部分岐は UT が網羅済(stmt/branch 100%)。
* `vip_api.ValidationApi` Protocol(`validate_settings(s) -> list[ValidationError]`)
  と `vip_api_b.validation_api.validate_settings`(関数、`Settings -> Ok | Err`)の
  型不整合は **CR-0004 として別途起票予定**(Step 19 F1 着手時に発見)。
  本 IT は Protocol 契約での Mock ベースで進める。本物 vip_api_b 注入による
  SEP-001 越え経路の検証は §6.7 IT-SEP(Step 19 F4)で扱う。
* `control_api_with_real_state_machine` は **本物 StateMachine + 本物 CommandHandler**
  を組み立てて Validation 拒否時の **State Machine 不変性** を検証する fixture
  (IT-RCM001.1-08 用)。CommandHandler の dispatch スレッドは起動しない
  (`enqueue` が呼ばれないことを実証する観点のため)。
"""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import Mock

import pytest

from vip_api.control_api import ControlApi, ValidationApi
from vip_ctrl.command_handler import (
    Accepted,
    CommandHandler,
)
from vip_ctrl.state_machine import State, StateMachine
from vip_ctrl.watchdog import (
    HEARTBEAT_TIMEOUT as SW_HEARTBEAT_TIMEOUT,  # 0.3 sec
)
from vip_ctrl.watchdog import (
    MONITOR_INTERVAL as SW_MONITOR_INTERVAL,  # 0.05 sec
)
from vip_ctrl.watchdog import (
    SwWatchdog,
)
from vip_integrity.resume_gate import ResumeConfirmationGate
from vip_persist.records import Settings
from vip_sim.failsafe_timer import (
    HEARTBEAT_TIMEOUT as HW_HEARTBEAT_TIMEOUT,  # 0.5 sec
)
from vip_sim.failsafe_timer import (
    MONITOR_INTERVAL as HW_MONITOR_INTERVAL,  # 0.1 sec
)
from vip_sim.failsafe_timer import (
    HwFailsafeTimer,
    PumpController,
)


def make_consistent_settings(
    flow_rate: Decimal = Decimal("60.0"),
    dose_volume: Decimal = Decimal("60.0"),
    duration_min: int = 60,
) -> Settings:
    """SRS-004 整合 Settings を生成(flow x duration / 60 == dose、デフォルト 60/60/60).

    既定値は flow_rate=60.0 mL/h, duration=60 min, dose=60.0 mL で SRS-004 整合
    (`60.0 * 60 / 60 == 60.0`)。各引数を上書きすることで範囲外 / 整合性違反
    パターンを生成できる。
    """
    return Settings(
        flow_rate=flow_rate,
        dose_volume=dose_volume,
        duration_min=duration_min,
    )


@pytest.fixture
def mock_command_handler() -> Mock:
    """`CommandHandler` を Mock 化。`enqueue` は `Accepted` を既定値で返す."""
    h: Mock = Mock(spec=CommandHandler)
    h.enqueue.return_value = Accepted(token="cmd-it-rcm001-token")
    return h


@pytest.fixture
def mock_resume_gate() -> Mock:
    """`ResumeConfirmationGate` を Mock 化(本観点では `confirm` は呼ばれない)."""
    return Mock(spec=ResumeConfirmationGate)


@pytest.fixture
def mock_validation_api() -> Mock:
    """`ValidationApi` を Mock 化。デフォルトは空 list(= Pass)."""
    v: Mock = Mock(spec=ValidationApi)
    v.validate_settings.return_value = []
    return v


@pytest.fixture
def control_api_with_mocks(
    mock_command_handler: Mock,
    mock_resume_gate: Mock,
    mock_validation_api: Mock,
) -> ControlApi:
    """`ControlAPI`(全注入 Mock 版、IT-RCM001.1-01〜07 用)."""
    return ControlApi(
        command_handler=mock_command_handler,
        resume_gate=mock_resume_gate,
        validation_api=mock_validation_api,
    )


@pytest.fixture
def real_state_machine_idle() -> StateMachine:
    """本物 `StateMachine` を IDLE 状態で生成(IT-RCM001.1-08 用).

    `INITIALIZING` から `set_initial(State.IDLE)` で IDLE に遷移済の状態。
    本 fixture を受け取った試験は「Validation 拒否時にこの状態が不変であること」
    を主検証する。
    """
    sm = StateMachine()
    sm.set_initial(State.IDLE, needs_confirm=False)
    return sm


@pytest.fixture
def control_api_with_real_state_machine(
    real_state_machine_idle: StateMachine,
    mock_resume_gate: Mock,
    mock_validation_api: Mock,
) -> ControlApi:
    """`ControlAPI`(本物 StateMachine + 本物 CommandHandler + Mock ValidationApi).

    IT-RCM001.1-08 で「Validation 拒否時の State Machine 不変性」を実証するための
    fixture。CommandHandler の dispatch スレッドは起動しない(`start()` を呼ばない):
    本観点は **`enqueue` が呼ばれないこと自体を検証する** ため、スレッド起動は
    不要かつ teardown 複雑化を避ける目的。
    """
    handler = CommandHandler(state_machine=real_state_machine_idle)
    return ControlApi(
        command_handler=handler,
        resume_gate=mock_resume_gate,
        validation_api=mock_validation_api,
    )


# ---------------------------------------------------------------------------
# Step 19 F2(IT-RCM003): SW / HW Watchdog 階層防御 fixture
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_state_machine() -> Mock:
    """`StateMachine` を Mock 化(SwWatchdog の `on_watchdog_timeout` 呼出捕捉用)."""
    return Mock(spec=StateMachine)


@pytest.fixture
def mock_pump_controller() -> Mock:
    """`PumpController` Protocol を Mock 化(HwFailsafeTimer の `force_stop_failsafe` 呼出捕捉用)."""
    return Mock(spec=PumpController)


@pytest.fixture
def sw_watchdog_real(mock_state_machine: Mock) -> SwWatchdog:
    """本物 `SwWatchdog`(SDD §4.8 デフォルト:timeout=0.3 sec、monitor=0.05 sec).

    本物 `time.monotonic` を内部で使用、Mock(spec=StateMachine)を注入。
    `start()` は各試験で必要に応じて呼ぶ(IT-RCM003.1-05 のみ起動)、
    その他試験は `check_once()` 直接呼出ベース。
    """
    return SwWatchdog(
        mock_state_machine,
        timeout=SW_HEARTBEAT_TIMEOUT,  # 0.3 sec
        monitor_interval=SW_MONITOR_INTERVAL,  # 0.05 sec
    )


@pytest.fixture
def hw_failsafe_timer_real(mock_pump_controller: Mock) -> HwFailsafeTimer:
    """本物 `HwFailsafeTimer`(SDD §4.3 デフォルト:timeout=0.5 sec、monitor=0.1 sec).

    本物 `time.monotonic` を内部で使用、Mock(spec=PumpController)を注入。
    """
    return HwFailsafeTimer(
        mock_pump_controller,
        timeout=HW_HEARTBEAT_TIMEOUT,  # 0.5 sec
        monitor_interval=HW_MONITOR_INTERVAL,  # 0.1 sec
    )


# ---------------------------------------------------------------------------
# Step 19 F3(IT-RCM004): Control Loop + Pump Simulator + Watchdog 結合 fixture
# ---------------------------------------------------------------------------
#
# 設計判断(Step 19 F3):
# `vip_ctrl.control_loop._HeartbeatSink` Protocol(`heartbeat(self, ts: float)`)と
# `vip_ctrl.watchdog.SwWatchdog.heartbeat`(引数なし、内部 `self._clock()` で取得)+
# `vip_sim.failsafe_timer.HwFailsafeTimer.heartbeat`(同上、引数なし)の
# シグネチャ不整合を着手前クロスレビューで発見(CR-0005 候補、F3 完了後に起票予定)。
# 本物 SwWatchdog/HwFailsafeTimer を ControlLoop に注入すると `TypeError` で動作不能。
# 本観点では `MagicMock`(spec なし、`heartbeat(ts)` 許容)で進め、CR-0005 決着後に
# §6.3 を本物 Watchdog 注入経路で再強化する想定(F1 / F1.5 と同じパターン継続)。


@pytest.fixture
def mock_running_state_machine() -> Mock:
    """`StateMachine` を Mock 化、`current()` は `State.RUNNING` を返す.

    `request_transition` / `on_watchdog_timeout` は呼出捕捉用に MagicMock デフォルト。
    """
    sm: Mock = Mock(spec=StateMachine)
    sm.current.return_value = State.RUNNING
    return sm


@pytest.fixture
def magicmock_sw_heartbeat_sink() -> Mock:
    """MagicMock(spec なし)で `_HeartbeatSink` を偽装(SwWatchdog 役、CR-0005 待ち).

    spec を指定しないことで `heartbeat(ts: float)` の呼出を許容。
    `assert_called_with(now)` で IF-U-004(Control Loop → SW Watchdog)を検証。
    """
    from unittest.mock import MagicMock  # noqa: PLC0415

    return MagicMock()


@pytest.fixture
def magicmock_hw_heartbeat_sink() -> Mock:
    """MagicMock(spec なし)で `_HeartbeatSink` を偽装(HwFailsafeTimer 役、CR-0005 待ち)."""
    from unittest.mock import MagicMock  # noqa: PLC0415

    return MagicMock()


@pytest.fixture
def pump_simulator_real() -> object:
    """本物 `PumpSimulator`(UNIT-002.1)— Decimal 演算 + RLock 保護."""
    from vip_sim.pump_simulator import PumpSimulator  # noqa: PLC0415

    return PumpSimulator()


@pytest.fixture
def pump_observer_real(pump_simulator_real: object) -> object:
    """本物 `PumpObserver`(UNIT-002.2)、Pump に紐付け SDD §4.10 整合."""
    from vip_sim.pump_observer import PumpObserver  # noqa: PLC0415

    return PumpObserver(pump=pump_simulator_real)  # type: ignore[arg-type]


def make_consistent_record_settings(
    flow_rate: Decimal = Decimal("60.0"),
    dose_volume: Decimal = Decimal("60.0"),
    duration_min: int = 60,
) -> Settings:
    """`vip_persist.records.Settings` を生成(`make_consistent_settings` の alias)."""
    return Settings(
        flow_rate=flow_rate,
        dose_volume=dose_volume,
        duration_min=duration_min,
    )
