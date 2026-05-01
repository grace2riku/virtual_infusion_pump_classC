"""Integration test — IT-RCM001 (RCM-001 指令範囲チェックの結合検証).

ITPR-VIP-001 §6.1 の詳細化(Step 19 F1)。
Validator + Control API + Validation API クラス B 経路で **指令範囲チェック
(RCM-001)が結合状態でも維持されている** ことを検証する。

設計判断(Step 19 F1 → F1.6 で更新):

* 本観点は **Mock(spec=ValidationApi)** ベースで進める(機能整合に focus)。
  CR-0004 (b)(`vip_api/_validation_bridge.py` Adapter)が Step 19 F1.6 で
  解消済のため、本物 `vip_api_b.validate_settings` を ControlApi に注入する
  経路は Adapter 経由で可能。本物注入の SEP-001 越え経路検証は §6.7 IT-SEP
  (Step 19 F4)で扱う。
* IT-RCM001.1-01〜07 は `control_api_with_mocks`(全 Mock)で **契約整合**を検証。
* IT-RCM001.1-08 は `control_api_with_real_state_machine`(本物 StateMachine +
  本物 CommandHandler + Mock ValidationApi)で **Validation 拒否時の状態不変**
  を実証(SEP-001 越えで副作用が伝播しない契約の縮小版検証)。

関連 SRS: SRS-O-001(指令値域 0.0〜1200.0)、SRS-RCM-001、SRS-UX-001/004/005、SRS-005。
関連 RCM: RCM-001。
関連 HZ: HZ-001(過量投与)、HZ-002(流量異常)。
関連 IF-U: IF-U-001(ControlAPI → CommandHandler)、IF-U-011(ControlAPI → ValidationApi)、
IF-U-013(ValidationApi → Settings 検証ロジック)。
関連 UT: UT-001.4(Flow Validator、34 ケース)、UT-005.1(ControlAPI、21 ケース)、
UT-005.3(ValidationApi クラス B、16 ケース)。
"""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

import pytest

from vip_api.control_api import (
    ApiResult,
    Ok,
    ValidationError,
    ValidationFailed,
)
from vip_ctrl.state_machine import State
from vip_persist.records import Settings

from .conftest import make_consistent_settings

if TYPE_CHECKING:
    from unittest.mock import Mock

    from vip_api.control_api import ControlApi
    from vip_ctrl.state_machine import StateMachine


# 本ファイル全体に integration マーカーを付与(addopts -m "not integration" 排除対象)
pytestmark = pytest.mark.integration


# ---------------------------------------------------------------------------
# IT-RCM001.1-01 — 正常系: 範囲内 Settings → ValidationApi.Ok 等価 → Accepted
# ---------------------------------------------------------------------------
def test_it_rcm001_1_01_in_range_settings_accepted_through_validator(
    control_api_with_mocks: ControlApi,
    mock_validation_api: Mock,
    mock_command_handler: Mock,
) -> None:
    """範囲内 Settings は ValidationApi の空 list 返却を経由して CommandHandler に渡る。

    結合契約: ControlAPI が ValidationApi.validate_settings を呼出し、結果が空 list
    なら CommandHandler.enqueue に進む(IF-U-011 → IF-U-001 経路)。
    """
    settings = make_consistent_settings()  # flow=60, dose=60, duration=60(SRS-004 整合)

    result: ApiResult = control_api_with_mocks.start(settings)

    assert isinstance(result, Ok)
    mock_validation_api.validate_settings.assert_called_once_with(settings)
    mock_command_handler.enqueue.assert_called_once()


# ---------------------------------------------------------------------------
# IT-RCM001.1-02 — flow_rate 上限超(SRS-O-001 1200 超)→ ValidationFailed
# ---------------------------------------------------------------------------
def test_it_rcm001_1_02_flow_rate_above_max_rejected_blocks_command_handler(
    control_api_with_mocks: ControlApi,
    mock_validation_api: Mock,
    mock_command_handler: Mock,
) -> None:
    """flow_rate > 1200 は ValidationApi が拒否、CommandHandler は呼ばれない。

    結合契約: ValidationApi 拒否時に IF-U-001(CommandHandler.enqueue)が **不発火**
    であることを `assert_not_called` で実証(RCM-001 が結合状態でも機能する根拠)。
    """
    settings = make_consistent_settings(flow_rate=Decimal("1200.01"))
    mock_validation_api.validate_settings.return_value = [
        ValidationError(field="flow_rate", message="above max 1200.0"),
    ]

    result = control_api_with_mocks.start(settings)

    assert isinstance(result, ValidationFailed)
    assert len(result.errors) == 1
    assert result.errors[0].field == "flow_rate"
    mock_command_handler.enqueue.assert_not_called()


# ---------------------------------------------------------------------------
# IT-RCM001.1-03 — flow_rate 負(SRS-O-001 下限超)→ ValidationFailed
# ---------------------------------------------------------------------------
def test_it_rcm001_1_03_flow_rate_negative_rejected_blocks_command_handler(
    control_api_with_mocks: ControlApi,
    mock_validation_api: Mock,
    mock_command_handler: Mock,
) -> None:
    """flow_rate < 0 は ValidationApi が拒否、CommandHandler は呼ばれない."""
    settings = make_consistent_settings(flow_rate=Decimal("-1.0"))
    mock_validation_api.validate_settings.return_value = [
        ValidationError(field="flow_rate", message="below min 0.0"),
    ]

    result = control_api_with_mocks.start(settings)

    assert isinstance(result, ValidationFailed)
    assert result.errors[0].field == "flow_rate"
    mock_command_handler.enqueue.assert_not_called()


# ---------------------------------------------------------------------------
# IT-RCM001.1-04 — dose_volume 上限超(SRS-005 9999.9 超)→ ValidationFailed
# ---------------------------------------------------------------------------
def test_it_rcm001_1_04_dose_volume_above_max_rejected_blocks_command_handler(
    control_api_with_mocks: ControlApi,
    mock_validation_api: Mock,
    mock_command_handler: Mock,
) -> None:
    """dose_volume > 9999.9 は ValidationApi が拒否、CommandHandler は呼ばれない."""
    settings = make_consistent_settings(dose_volume=Decimal("10000.0"))
    mock_validation_api.validate_settings.return_value = [
        ValidationError(field="dose_volume", message="above max 9999.9"),
    ]

    result = control_api_with_mocks.start(settings)

    assert isinstance(result, ValidationFailed)
    assert result.errors[0].field == "dose_volume"
    mock_command_handler.enqueue.assert_not_called()


# ---------------------------------------------------------------------------
# IT-RCM001.1-05 — dose==0 かつ flow>0(SRS-004 整合性違反)→ Inconsistency 等価
# ---------------------------------------------------------------------------
def test_it_rcm001_1_05_zero_dose_with_positive_flow_rejected(
    control_api_with_mocks: ControlApi,
    mock_validation_api: Mock,
    mock_command_handler: Mock,
) -> None:
    """dose==0 だが flow>0 → SRS-004 整合性違反として拒否される.

    `vip_api_b.validate_settings` の論理出力(`Inconsistency` 失敗値オブジェクト)
    と等価な `ValidationError` を Mock が返すパターン。
    """
    settings = make_consistent_settings(
        flow_rate=Decimal("10.0"),
        dose_volume=Decimal("0.0"),
        duration_min=60,
    )
    mock_validation_api.validate_settings.return_value = [
        ValidationError(
            field="dose_consistency",
            message="dose=0 but flow>0 implies expected_dose>0",
        ),
    ]

    result = control_api_with_mocks.start(settings)

    assert isinstance(result, ValidationFailed)
    mock_command_handler.enqueue.assert_not_called()


# ---------------------------------------------------------------------------
# IT-RCM001.1-06 — flow*duration/60 と dose の差が ±1% 超(SRS-004 整合性違反)
# ---------------------------------------------------------------------------
def test_it_rcm001_1_06_srs_004_inconsistency_above_tolerance_rejected(
    control_api_with_mocks: ControlApi,
    mock_validation_api: Mock,
    mock_command_handler: Mock,
) -> None:
    """flow=60, duration=60 で expected_dose=60 だが dose=70 → 16% 差で拒否.

    SRS-004(±1% 整合性許容差)に対して 16% 差で逸脱 → ValidationApi が
    `Inconsistency` 等価で拒否することを Mock 経由で実証。
    """
    settings = Settings(
        flow_rate=Decimal("60.0"),
        dose_volume=Decimal("70.0"),  # expected 60 vs actual 70
        duration_min=60,
    )
    mock_validation_api.validate_settings.return_value = [
        ValidationError(
            field="dose_consistency",
            message="diff 16% > 1% tolerance (SRS-004)",
        ),
    ]

    result = control_api_with_mocks.start(settings)

    assert isinstance(result, ValidationFailed)
    mock_command_handler.enqueue.assert_not_called()


# ---------------------------------------------------------------------------
# IT-RCM001.1-07 — 多重失敗集約(flow + dose 両方範囲外)
# ---------------------------------------------------------------------------
def test_it_rcm001_1_07_multiple_failures_aggregated_in_single_response(
    control_api_with_mocks: ControlApi,
    mock_validation_api: Mock,
    mock_command_handler: Mock,
) -> None:
    """複数の失敗が `ValidationFailed.errors` に集約されて返ることを検証.

    結合契約: SRS-027(fail-safe boot path)で「検出した全異常を列挙」する
    要件と整合。1 件目の失敗で短絡せず全失敗を返す動作を Mock 経由で実証。
    """
    settings = Settings(
        flow_rate=Decimal("-1.0"),  # 範囲外
        dose_volume=Decimal("10000.0"),  # 範囲外
        duration_min=60,
    )
    mock_validation_api.validate_settings.return_value = [
        ValidationError(field="flow_rate", message="below min"),
        ValidationError(field="dose_volume", message="above max"),
    ]

    result = control_api_with_mocks.start(settings)

    assert isinstance(result, ValidationFailed)
    assert len(result.errors) == 2  # 両方の失敗が集約
    fields = {e.field for e in result.errors}
    assert fields == {"flow_rate", "dose_volume"}
    mock_command_handler.enqueue.assert_not_called()


# ---------------------------------------------------------------------------
# IT-RCM001.1-08 — Validation 拒否時の本物 StateMachine 不変(SEP-001 縮小版検証)
# ---------------------------------------------------------------------------
def test_it_rcm001_1_08_state_machine_unchanged_when_validation_rejects(
    control_api_with_real_state_machine: ControlApi,
    real_state_machine_idle: StateMachine,
    mock_validation_api: Mock,
) -> None:
    """ValidationFailed 時に **本物 State Machine が IDLE のまま不変** であることを実証.

    本ケースは IT-RCM001 の **唯一本物 StateMachine + 本物 CommandHandler を組み立てる**
    観点。Validation 拒否(クラス B Validation API 等価層)→ ControlAPI 経路で
    クラス C 制御系(StateMachine)に副作用が伝播しないことを実証する SEP-001
    縮小版検証(§6.7 IT-SEP の予告)。
    """
    settings = make_consistent_settings(flow_rate=Decimal("1200.01"))
    mock_validation_api.validate_settings.return_value = [
        ValidationError(field="flow_rate", message="above max 1200.0"),
    ]

    # 前提: State Machine は IDLE
    assert real_state_machine_idle.current() == State.IDLE

    result = control_api_with_real_state_machine.start(settings)

    # ValidationFailed が返り、State Machine は IDLE のまま不変
    assert isinstance(result, ValidationFailed)
    assert real_state_machine_idle.current() == State.IDLE
