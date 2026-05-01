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
from vip_integrity.resume_gate import ResumeConfirmationGate
from vip_persist.records import Settings


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
