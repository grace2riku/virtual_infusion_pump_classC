"""Integration test fixtures (ITPR-VIP-001 §6).

Step 19 F0 で骨格化、Step 19 F1 で RCM-001 用 fixture 群を追加。
各観点(F1: RCM-001 / F2: RCM-003 / F3: RCM-004 / F4: SEP-001 /
F5: IT-PERF / F6: IT-PWR / F7: IT-SIDE)で本 conftest を拡張する想定。

設計方針(Step 19 F1 → F1.6 で更新):

* `Mock(spec=...)` 系 fixture は UT-005.1(`tests/unit/test_control_api.py`)の
  パターンを踏襲 — IT 観点では「ユニット間の **契約整合**」検証に焦点を当て、
  各ユニット内部分岐は UT が網羅済(stmt/branch 100%)。
* CR-0004 (b)(`vip_api/_validation_bridge.py` Adapter)+ CR-0005 (a)
  (`_HeartbeatSink.heartbeat() -> None` 引数なし化)が Step 19 F1.6 で
  解消済。本物 `vip_api_b.validate_settings` の `ControlApi` への注入は
  Adapter 経由(`make_validation_api()`)で可能、本物 `SwWatchdog` /
  `HwFailsafeTimer` の `ControlLoop` 注入は引数なし契約で可能。本物注入
  による SEP-001 越え経路 + 階層防御 E2E の実証は §6.7 IT-SEP
  (Step 19 F4)で扱う。本 §6.1〜§6.3 は Mock 主体の機能整合検証を維持。
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
# 設計判断(Step 19 F3 → F1.6 で更新):
# CR-0005 (a) で `_HeartbeatSink.heartbeat() -> None`(引数なし)に整合化済。
# 本物 SwWatchdog/HwFailsafeTimer を ControlLoop に注入できる経路は §6.7
# IT-SEP(Step 19 F4)で扱い、本 §6.3 は機能整合のみに focus を維持するため
# 引き続き MagicMock(spec なし)を使う。


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
    """MagicMock で `_HeartbeatSink` を偽装(SwWatchdog 役、CR-0005 (a) 解消後).

    `heartbeat()` 引数なし呼出を捕捉(IF-U-004 Control Loop → SW Watchdog)。
    """
    from unittest.mock import MagicMock  # noqa: PLC0415

    return MagicMock()


@pytest.fixture
def magicmock_hw_heartbeat_sink() -> Mock:
    """MagicMock で `_HeartbeatSink` を偽装(HwFailsafeTimer 役、CR-0005 (a) 解消後)."""
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


# ---------------------------------------------------------------------------
# Step 19 F4(IT-SEP-001): SEP-001 ランタイム分離 + 真の本物注入経路 fixture
# ---------------------------------------------------------------------------
#
# 設計判断(Step 19 F4):
# §6.1〜§6.3 が Mock 主体の機能整合検証だったのに対し、§6.7 は CR-0004 (b)
# Adapter + CR-0005 (a) Protocol 引数なし化が解消された前提で、
#   * 本物 `vip_api_b.validate_settings`(Adapter `make_validation_api()` 経由)
#   * 本物 `SwWatchdog` / `HwFailsafeTimer`(`heartbeat() -> None` 引数なし契約)
# を真に注入することで「SEP-001 越え経路 + 階層防御 E2E」を実証する。


@pytest.fixture
def real_validation_api() -> ValidationApi:
    """本物 `ValidationApi`(`vip_api/_validation_bridge.make_validation_api()` 経由).

    内部で `vip_api_b.validation_api.validate_settings`(クラス B)を呼び出す
    Adapter。SEP-001 の越え経路を **本物注入** で検証するための主軸 fixture。
    """
    from vip_api._validation_bridge import make_validation_api  # noqa: PLC0415

    return make_validation_api()


@pytest.fixture
def control_api_with_real_validation(
    real_state_machine_idle: StateMachine,
    mock_resume_gate: Mock,
    real_validation_api: ValidationApi,
) -> ControlApi:
    """`ControlAPI`(本物 ValidationApi Adapter + 本物 StateMachine + 本物 CommandHandler).

    IT-SEP.1-02 / 03 / 05 で「真の SEP-001 越え経路」を実証するための fixture。
    `CommandHandler` は **dispatch スレッドを起動しない** — 本観点は
    `enqueue` 自体の挙動 + Validation 経路の SEP-001 boundary 維持を主検証
    するため、スレッド lifecycle は §6.6 IT-RCM019 で別途網羅済。
    """
    handler = CommandHandler(state_machine=real_state_machine_idle)
    return ControlApi(
        command_handler=handler,
        resume_gate=mock_resume_gate,
        validation_api=real_validation_api,
    )


@pytest.fixture
def sw_watchdog_for_loop(mock_running_state_machine: Mock) -> SwWatchdog:
    """本物 `SwWatchdog`(ControlLoop 注入用、`mock_running_state_machine` 連動).

    §6.2 fixture と異なり、ControlLoop 結合観点では `current() == RUNNING`
    の StateMachine と紐付ける(`SwWatchdog.on_watchdog_timeout` 呼出捕捉用)。
    """
    return SwWatchdog(
        mock_running_state_machine,
        timeout=SW_HEARTBEAT_TIMEOUT,
        monitor_interval=SW_MONITOR_INTERVAL,
    )


@pytest.fixture
def hw_failsafe_timer_for_loop(mock_pump_controller: Mock) -> HwFailsafeTimer:
    """本物 `HwFailsafeTimer`(ControlLoop 注入用)."""
    return HwFailsafeTimer(
        mock_pump_controller,
        timeout=HW_HEARTBEAT_TIMEOUT,
        monitor_interval=HW_MONITOR_INTERVAL,
    )
