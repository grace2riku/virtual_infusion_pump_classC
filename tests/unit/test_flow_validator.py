"""UT-001.4 — Flow Command Validator unit tests (UNIT-001.4 per SDD-VIP-001 §4.2).

Implements UTPR-VIP-001 §7.3.2 test cases UT-001.4-01 .. UT-001.4-12.
Covers RCM-001 (flow command range/settings validation) per RMF-VIP-001 §6.1.

Step 19 B3 reconciles UTPR §7.3.2 with SRS-O-001 / SRS-RCM-001 / SDD §4.2:
the command range is `0.0 ≤ value ≤ 1200.0` (commands include the stop value),
ValidationReason names follow SDD §4.2.B, and the settings consistency check
fires only when `current_state == State.RUNNING`.

Related SRS: SRS-O-001, SRS-RCM-001, SRS-005.
Related HZ:  HZ-001 (over-delivery), HZ-002 (under-delivery).
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from vip_ctrl.flow_validator import (
    MAX_FLOW,
    MIN_FLOW,
    ControlContext,
    FlowCommand,
    Settings,
    ValidatedFlowCommand,
    ValidationErr,
    ValidationOk,
    ValidationReason,
    validate,
)
from vip_ctrl.state_machine import State

# ---------- helpers / fixtures ----------


def _ts() -> datetime:
    return datetime.now(UTC)


def _command(rate: Decimal | str | int) -> FlowCommand:
    return FlowCommand(flow_rate=Decimal(str(rate)), timestamp=_ts())


def _context(setting: Decimal | str | int, state: State) -> ControlContext:
    return ControlContext(
        current_settings=Settings(flow_rate=Decimal(str(setting))),
        current_state=state,
    )


@pytest.fixture
def stopped_ctx() -> ControlContext:
    return _context("0", State.STOPPED)


# ---------- UT-001.4-01: 正常範囲内 ----------


def test_ut_001_4_01_validate_normal_range_returns_ok() -> None:
    cmd = _command("100")
    result = validate(cmd, _context("100", State.RUNNING))
    assert isinstance(result, ValidationOk)
    assert result.validated.flow_rate == Decimal(100)


def test_ut_001_4_01b_validated_command_preserves_timestamp() -> None:
    ts = datetime(2026, 4, 23, 12, 0, 0, tzinfo=UTC)
    cmd = FlowCommand(flow_rate=Decimal(100), timestamp=ts)
    result = validate(cmd, _context("100", State.RUNNING))
    assert isinstance(result, ValidationOk)
    assert result.validated.approved_at == ts


# ---------- UT-001.4-02: 範囲最小境界(指令の最小は 0.0、停止指令を含む) ----------


def test_ut_001_4_02_min_boundary_zero_in_stopped_returns_ok(
    stopped_ctx: ControlContext,
) -> None:
    cmd = _command("0.0")
    result = validate(cmd, stopped_ctx)
    assert isinstance(result, ValidationOk)
    assert result.validated.flow_rate == Decimal("0.0")


def test_ut_001_4_02b_zero_setting_zero_command_in_running_returns_ok() -> None:
    cmd = _command("0.0")
    result = validate(cmd, _context("0.0", State.RUNNING))
    assert isinstance(result, ValidationOk)


def test_ut_001_4_02c_min_setting_value_in_running_returns_ok() -> None:
    cmd = _command("0.1")
    result = validate(cmd, _context("0.1", State.RUNNING))
    assert isinstance(result, ValidationOk)


# ---------- UT-001.4-03: 範囲最大境界 ----------


def test_ut_001_4_03_max_boundary_returns_ok() -> None:
    cmd = _command("1200.0")
    result = validate(cmd, _context("1200.0", State.RUNNING))
    assert isinstance(result, ValidationOk)
    assert result.validated.flow_rate == Decimal("1200.0")


# ---------- UT-001.4-04: 範囲下限 - ε(負側 ε)→ NEGATIVE ----------


def test_ut_001_4_04_below_min_returns_negative_err(
    stopped_ctx: ControlContext,
) -> None:
    cmd = _command("-0.01")
    result = validate(cmd, stopped_ctx)
    assert isinstance(result, ValidationErr)
    assert result.reason is ValidationReason.NEGATIVE


# ---------- UT-001.4-05: 範囲上限 + ε ----------


def test_ut_001_4_05_above_max_returns_out_of_range_err(
    stopped_ctx: ControlContext,
) -> None:
    cmd = _command("1200.01")
    result = validate(cmd, stopped_ctx)
    assert isinstance(result, ValidationErr)
    assert result.reason is ValidationReason.OUT_OF_RANGE


def test_ut_001_4_05b_far_above_max_returns_out_of_range_err(
    stopped_ctx: ControlContext,
) -> None:
    cmd = _command("9999")
    result = validate(cmd, stopped_ctx)
    assert isinstance(result, ValidationErr)
    assert result.reason is ValidationReason.OUT_OF_RANGE


# ---------- UT-001.4-06: 負値 ----------


def test_ut_001_4_06_negative_one_returns_negative_err(
    stopped_ctx: ControlContext,
) -> None:
    cmd = _command("-1")
    result = validate(cmd, stopped_ctx)
    assert isinstance(result, ValidationErr)
    assert result.reason is ValidationReason.NEGATIVE


def test_ut_001_4_06b_large_negative_returns_negative_err(
    stopped_ctx: ControlContext,
) -> None:
    cmd = _command("-1000")
    result = validate(cmd, stopped_ctx)
    assert isinstance(result, ValidationErr)
    assert result.reason is ValidationReason.NEGATIVE


# ---------- UT-001.4-07: NaN / Inf ----------


@pytest.mark.parametrize(
    "rate",
    [
        Decimal("NaN"),
        Decimal("Infinity"),
        Decimal("-Infinity"),
    ],
)
def test_ut_001_4_07_nan_or_infinite_returns_invalid_value_err(
    rate: Decimal,
    stopped_ctx: ControlContext,
) -> None:
    cmd = FlowCommand(flow_rate=rate, timestamp=_ts())
    result = validate(cmd, stopped_ctx)
    assert isinstance(result, ValidationErr)
    assert result.reason is ValidationReason.NAN_OR_INFINITE


# ---------- UT-001.4-08: 設定値との不一致(許容誤差超)→ MISMATCH ----------


def test_ut_001_4_08_diff_above_tolerance_in_running_returns_mismatch() -> None:
    cmd = _command("100")
    result = validate(cmd, _context("50", State.RUNNING))
    assert isinstance(result, ValidationErr)
    assert result.reason is ValidationReason.MISMATCH_WITH_SETTINGS


def test_ut_001_4_08b_zero_setting_nonzero_command_returns_mismatch() -> None:
    cmd = _command("0.1")
    result = validate(cmd, _context("0.0", State.RUNNING))
    assert isinstance(result, ValidationErr)
    assert result.reason is ValidationReason.MISMATCH_WITH_SETTINGS


# ---------- UT-001.4-09: 設定値との不一致(許容誤差内)→ Ok ----------


def test_ut_001_4_09_diff_within_tolerance_in_running_returns_ok() -> None:
    cmd = _command("102")
    result = validate(cmd, _context("100", State.RUNNING))
    assert isinstance(result, ValidationOk)


def test_ut_001_4_09b_diff_exactly_tolerance_returns_ok() -> None:
    # diff_ratio == TOLERANCE は許容(SDD §4.2.C は `>` で判定)。
    cmd = _command("105")
    result = validate(cmd, _context("100", State.RUNNING))
    assert isinstance(result, ValidationOk)


def test_ut_001_4_09c_diff_just_above_tolerance_returns_mismatch() -> None:
    # diff_ratio = 0.0501 > TOLERANCE → 不一致
    cmd = _command("105.01")
    result = validate(cmd, _context("100", State.RUNNING))
    assert isinstance(result, ValidationErr)
    assert result.reason is ValidationReason.MISMATCH_WITH_SETTINGS


# ---------- UT-001.4-10: プロパティ:STOPPED 状態で範囲内は常に Ok ----------


@settings(
    max_examples=200,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@given(
    rate=st.decimals(
        min_value=Decimal("0.0"),
        max_value=Decimal("1200.0"),
        allow_nan=False,
        allow_infinity=False,
        places=1,
    ),
)
def test_ut_001_4_10_property_in_range_in_stopped_always_ok(
    rate: Decimal,
    stopped_ctx: ControlContext,
) -> None:
    cmd = FlowCommand(flow_rate=rate, timestamp=_ts())
    result = validate(cmd, stopped_ctx)
    assert isinstance(result, ValidationOk)
    assert result.validated.flow_rate == rate


# ---------- UT-001.4-11: プロパティ:範囲外は常に Err ----------


@settings(
    max_examples=200,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@given(
    rate=st.one_of(
        st.decimals(
            min_value=Decimal(-10000),
            max_value=Decimal("-0.01"),
            allow_nan=False,
            allow_infinity=False,
            places=2,
        ),
        st.decimals(
            min_value=Decimal("1200.01"),
            max_value=Decimal(1000000),
            allow_nan=False,
            allow_infinity=False,
            places=2,
        ),
    ),
)
def test_ut_001_4_11_property_out_of_range_always_err(
    rate: Decimal,
    stopped_ctx: ControlContext,
) -> None:
    cmd = FlowCommand(flow_rate=rate, timestamp=_ts())
    result = validate(cmd, stopped_ctx)
    assert isinstance(result, ValidationErr)
    assert result.reason in {
        ValidationReason.NEGATIVE,
        ValidationReason.OUT_OF_RANGE,
    }


# ---------- UT-001.4-12: Decimal 入力(精度 2 桁保持)----------


def test_ut_001_4_12_decimal_precision_two_digits_preserved() -> None:
    cmd = FlowCommand(flow_rate=Decimal("100.00"), timestamp=_ts())
    result = validate(cmd, _context("100.00", State.RUNNING))
    assert isinstance(result, ValidationOk)
    # 入力の精度(指数)を保持していること(`as_tuple().exponent == -2`)
    assert result.validated.flow_rate.as_tuple().exponent == -2
    assert result.validated.flow_rate == Decimal("100.00")


# ---------- 補助観点:設定値整合性検証は RUNNING 以外でスキップ ----------


@pytest.mark.parametrize(
    "state",
    [
        State.INITIALIZING,
        State.IDLE,
        State.PAUSED,
        State.STOPPED,
        State.ERROR,
    ],
)
def test_setting_check_skipped_when_not_running(state: State) -> None:
    cmd = _command("100")
    # setting=50 と大きく乖離していても、RUNNING でなければ Ok
    result = validate(cmd, _context("50", state))
    assert isinstance(result, ValidationOk)


# ---------- 補助観点:純粋性 / 冪等性 ----------


def test_validate_is_pure_repeated_calls_return_equal_results() -> None:
    cmd = _command("100")
    ctx = _context("100", State.RUNNING)
    r1 = validate(cmd, ctx)
    r2 = validate(cmd, ctx)
    assert isinstance(r1, ValidationOk)
    assert isinstance(r2, ValidationOk)
    assert r1.validated == r2.validated


# ---------- 補助観点:データクラスは frozen ----------


def test_flow_command_is_frozen() -> None:
    cmd = _command("100")
    with pytest.raises((AttributeError, TypeError)):
        cmd.flow_rate = Decimal(200)  # type: ignore[misc]


def test_validated_flow_command_is_frozen() -> None:
    validated = ValidatedFlowCommand(flow_rate=Decimal(100), approved_at=_ts())
    with pytest.raises((AttributeError, TypeError)):
        validated.flow_rate = Decimal(200)  # type: ignore[misc]


def test_settings_is_frozen() -> None:
    s = Settings(flow_rate=Decimal(100))
    with pytest.raises((AttributeError, TypeError)):
        s.flow_rate = Decimal(200)  # type: ignore[misc]


def test_control_context_is_frozen() -> None:
    ctx = _context("100", State.RUNNING)
    with pytest.raises((AttributeError, TypeError)):
        ctx.current_state = State.IDLE  # type: ignore[misc]


# ---------- 補助観点:範囲定数 ----------


def test_min_flow_constant_is_zero() -> None:
    # SDD §4.2.C: MIN_FLOW = Decimal("0.0")
    assert Decimal("0.0") == MIN_FLOW


def test_max_flow_constant_is_1200() -> None:
    # SDD §4.2.C: MAX_FLOW = Decimal("1200.0")
    assert Decimal("1200.0") == MAX_FLOW
