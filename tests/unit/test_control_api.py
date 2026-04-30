"""UT-005.1 — Control API (UNIT-005.1 per SDD-VIP-001 §4.15).

Implements UTPR-VIP-001 §7.3.15 detailed test cases UT-005.1-01 .. UT-005.1-18.
Realises SRS-IF-002 (external command interface) and SRS-010〜014
(start/stop/pause/resume/error_reset semantics). The Control API is a
thin Facade over Command Handler (UNIT-001.3), Resume Confirmation Gate
(UNIT-004.2), and Validation API (UNIT-005.3 — Mocked here as a
`ValidationApi` Protocol since UNIT-005.3 is not yet implemented).

Step 19 B16 design judgments (recorded in DEVELOPMENT_STEPS.md):

* The 8 public methods (`start` / `stop` / `pause` / `resume` / `reset` /
  `error_reset` / `confirm_resume` / `await_command`) all return values
  via `ApiResult` (sealed hierarchy: `Ok` / `ValidationFailed` /
  `ApiRejected` + Resume-Gate `Confirmed` / `WrongToken` / `Expired` /
  `NotPending`) and never raise — every catch path returns
  `ApiRejected(INTERNAL_ERROR)` (SDD §4.15.E "例外を投げない契約").
* `Settings.model_dump()` converts pydantic to `Mapping[str, object]`
  so the Command Handler's `Command(payload=...)` contract is satisfied
  without leaking pydantic into the Handler.
* `ValidationApi` is defined here as a `Protocol` (`validate_settings(s)
  -> list[ValidationError]`), so UNIT-005.3 can satisfy it later via
  structural typing without `vip_api` importing `vip_api_b` (SEP-001).
* The `drug_name` lever from SDD §4.15.B is NOT exercised here — Inc.1
  `vip_persist.records.Settings` lacks `drug_name`, and adding it
  ripples through B6/B7 tests; the integration is deferred to Inc.4 UI
  work (continuing the B15 hand-off discussion).

Related SRS: SRS-IF-002, SRS-010〜014.
Related RCM: — (delegation; RCMs are realised inside the delegated
units: RCM-019 in UNIT-001.1, RCM-016 in UNIT-004.2, etc.).
"""

from __future__ import annotations

import dataclasses
from decimal import Decimal
from unittest.mock import Mock

import pytest

from vip_api.control_api import (
    ApiRejected,
    ApiResult,
    ControlApi,
    InternalError,
    Ok,
    ValidationApi,
    ValidationError,
    ValidationFailed,
)
from vip_ctrl.command_handler import (
    Accepted,
    CommandHandler,
    CommandKind,
    Completed,
    Failed,
    RejectReason,
    TimedOut,
)
from vip_ctrl.command_handler import (
    Rejected as HandlerRejected,
)
from vip_ctrl.state_machine import State
from vip_integrity.resume_gate import (
    Confirmed,
    Expired,
    NotPending,
    ResumeConfirmationGate,
    ResumeDetail,
    WrongToken,
)
from vip_persist.records import Settings

# ---------- helpers ----------


def _make_settings() -> Settings:
    return Settings(
        flow_rate=Decimal("100.0"),
        dose_volume=Decimal("250.0"),
        duration_min=150,
    )


def _make_resume_detail() -> ResumeDetail:
    return ResumeDetail(
        settings=_make_settings(),
        state=State.PAUSED,
        accumulated_volume=Decimal("50.0"),
    )


@pytest.fixture
def command_handler_mock() -> Mock:
    h: Mock = Mock(spec=CommandHandler)
    h.enqueue.return_value = Accepted(token="cmd-token-001")
    h.await_completion.return_value = Completed(state=State.RUNNING)
    return h


@pytest.fixture
def resume_gate_mock() -> Mock:
    g: Mock = Mock(spec=ResumeConfirmationGate)
    g.confirm.return_value = Confirmed(detail=_make_resume_detail())
    return g


@pytest.fixture
def validation_api_mock() -> Mock:
    v: Mock = Mock(spec=ValidationApi)
    v.validate_settings.return_value = []  # 空 list = Pass
    return v


@pytest.fixture
def api(
    command_handler_mock: Mock,
    resume_gate_mock: Mock,
    validation_api_mock: Mock,
) -> ControlApi:
    return ControlApi(
        command_handler=command_handler_mock,
        resume_gate=resume_gate_mock,
        validation_api=validation_api_mock,
    )


# ---------- UT-005.1-01: start 正常フロー ----------


def test_ut_005_1_01_start_returns_ok_when_validation_and_enqueue_succeed(
    api: ControlApi,
    command_handler_mock: Mock,
    validation_api_mock: Mock,
) -> None:
    """start: Validator Pass + Handler Accepted → `Ok(token)` を返す。"""
    settings = _make_settings()

    result = api.start(settings)

    assert isinstance(result, Ok)
    assert result.token == "cmd-token-001"
    validation_api_mock.validate_settings.assert_called_once_with(settings)
    command_handler_mock.enqueue.assert_called_once()
    enq_arg = command_handler_mock.enqueue.call_args.args[0]
    assert enq_arg.kind is CommandKind.START
    # payload は Settings を Mapping[str, object] に変換したもの。
    assert enq_arg.payload is not None
    assert enq_arg.payload["flow_rate"] == Decimal("100.0")


# ---------- UT-005.1-02: start 検証失敗 → ValidationFailed ----------


def test_ut_005_1_02_start_returns_validation_failed_when_validator_returns_errors(
    api: ControlApi,
    command_handler_mock: Mock,
    validation_api_mock: Mock,
) -> None:
    """start: Validator が errors を返したら `ValidationFailed`、Handler に enqueue されない。"""
    errors = [ValidationError(field="flow_rate", message="out of range")]
    validation_api_mock.validate_settings.return_value = errors

    result = api.start(_make_settings())

    assert isinstance(result, ValidationFailed)
    assert result.errors == errors
    command_handler_mock.enqueue.assert_not_called()


# ---------- UT-005.1-03: start Handler Rejected → ApiRejected ----------


def test_ut_005_1_03_start_returns_api_rejected_when_handler_rejects(
    api: ControlApi,
    command_handler_mock: Mock,
) -> None:
    """start: Handler が `Rejected` を返したら `ApiRejected(reason)` で復帰。"""
    command_handler_mock.enqueue.return_value = HandlerRejected(
        reason=RejectReason.INVALID_FOR_CURRENT_STATE,
    )

    result = api.start(_make_settings())

    assert isinstance(result, ApiRejected)
    assert result.reason is RejectReason.INVALID_FOR_CURRENT_STATE


# ---------- UT-005.1-04 .. UT-005.1-08: stop/pause/resume/reset/error_reset ----------


@pytest.mark.parametrize(
    ("method_name", "expected_kind"),
    [
        ("stop", CommandKind.STOP),
        ("pause", CommandKind.PAUSE),
        ("resume", CommandKind.RESUME),
        ("reset", CommandKind.RESET),
        ("error_reset", CommandKind.ERROR_RESET),
    ],
)
def test_ut_005_1_04_to_08_simple_commands_enqueue_and_return_ok(
    api: ControlApi,
    command_handler_mock: Mock,
    method_name: str,
    expected_kind: CommandKind,
) -> None:
    """stop / pause / resume / reset / error_reset は payload 不要、`Ok(token)` を返す。"""
    method = getattr(api, method_name)

    result = method()

    assert isinstance(result, Ok)
    assert result.token == "cmd-token-001"
    enq_arg = command_handler_mock.enqueue.call_args.args[0]
    assert enq_arg.kind is expected_kind
    assert enq_arg.payload is None


# ---------- UT-005.1-09: confirm_resume Confirmed → Ok ----------


def test_ut_005_1_09_confirm_resume_returns_ok_when_gate_returns_confirmed(
    api: ControlApi,
    resume_gate_mock: Mock,
) -> None:
    """confirm_resume: Gate が `Confirmed` → `Ok(token)` を返す。"""
    result = api.confirm_resume("a" * 32)

    assert isinstance(result, Ok)
    resume_gate_mock.confirm.assert_called_once_with("a" * 32)


# ---------- UT-005.1-10..12: confirm_resume の WrongToken/Expired/NotPending ----------


@pytest.mark.parametrize(
    ("gate_result", "expected_type"),
    [
        (WrongToken(), WrongToken),
        (Expired(), Expired),
        (NotPending(), NotPending),
    ],
)
def test_ut_005_1_10_to_12_confirm_resume_propagates_gate_failure_results(
    api: ControlApi,
    resume_gate_mock: Mock,
    gate_result: object,
    expected_type: type,
) -> None:
    """Gate の WrongToken / Expired / NotPending を Control API がそのまま透過する。"""
    resume_gate_mock.confirm.return_value = gate_result

    result = api.confirm_resume("0" * 32)

    assert isinstance(result, expected_type)


# ---------- UT-005.1-13: await_command Completed ----------


def test_ut_005_1_13_await_command_returns_handler_completion_result(
    api: ControlApi,
    command_handler_mock: Mock,
) -> None:
    """await_command は Handler.await_completion の戻り値をそのまま透過する。"""
    expected = Completed(state=State.RUNNING)
    command_handler_mock.await_completion.return_value = expected

    result = api.await_command("cmd-token-001", timeout_ms=100)

    assert result is expected
    command_handler_mock.await_completion.assert_called_once_with(
        "cmd-token-001",
        timeout_ms=100,
    )


# ---------- UT-005.1-14: await_command の TimedOut / Failed 透過 ----------


@pytest.mark.parametrize(
    "completion",
    [
        TimedOut(elapsed_ms=200),
        Failed(error=RuntimeError("boom")),
    ],
)
def test_ut_005_1_14_await_command_passes_through_timed_out_and_failed(
    api: ControlApi,
    command_handler_mock: Mock,
    completion: object,
) -> None:
    """await_command は TimedOut / Failed もそのまま透過する。"""
    command_handler_mock.await_completion.return_value = completion

    result = api.await_command("cmd-token-001")

    assert result is completion


# ---------- UT-005.1-15: 例外耐性 — Handler.enqueue が例外 ----------


def test_ut_005_1_15_start_returns_internal_error_when_handler_enqueue_raises(
    api: ControlApi,
    command_handler_mock: Mock,
) -> None:
    """Handler.enqueue 例外でも Control API は ApiRejected(INTERNAL_ERROR) で復帰。"""
    command_handler_mock.enqueue.side_effect = RuntimeError("handler crashed")

    result = api.start(_make_settings())

    assert isinstance(result, ApiRejected)
    assert result.reason is InternalError.UNEXPECTED_EXCEPTION


# ---------- UT-005.1-16: 例外耐性 — ValidationApi が例外 ----------


def test_ut_005_1_16_start_returns_internal_error_when_validation_api_raises(
    api: ControlApi,
    validation_api_mock: Mock,
) -> None:
    """Validation API が例外を raise しても Control API は ApiRejected(INTERNAL_ERROR) で復帰。"""
    validation_api_mock.validate_settings.side_effect = ValueError("validator crashed")

    result = api.start(_make_settings())

    assert isinstance(result, ApiRejected)
    assert result.reason is InternalError.UNEXPECTED_EXCEPTION


# ---------- UT-005.1-17: 例外耐性 — Resume Gate が例外 ----------


def test_ut_005_1_17_confirm_resume_returns_internal_error_when_gate_raises(
    api: ControlApi,
    resume_gate_mock: Mock,
) -> None:
    """Resume Gate が例外を raise しても Control API は ApiRejected(INTERNAL_ERROR) で復帰。"""
    resume_gate_mock.confirm.side_effect = RuntimeError("gate crashed")

    result = api.confirm_resume("a" * 32)

    assert isinstance(result, ApiRejected)
    assert result.reason is InternalError.UNEXPECTED_EXCEPTION


# ---------- UT-005.1-18: ApiResult sealed hierarchy frozen 契約 ----------


def test_ut_005_1_18_api_result_value_objects_are_frozen() -> None:
    """`Ok` / `ApiRejected` / `ValidationFailed` / `ValidationError` は frozen dataclass。"""
    ok = Ok(token="t")
    rejected = ApiRejected(reason=RejectReason.QUEUE_FULL)
    validation_failed = ValidationFailed(errors=[])
    validation_error = ValidationError(field="x", message="m")

    for obj, attr in [
        (ok, "token"),
        (rejected, "reason"),
        (validation_failed, "errors"),
        (validation_error, "field"),
    ]:
        with pytest.raises(dataclasses.FrozenInstanceError):
            setattr(obj, attr, "tampered")


# ---------- 型注釈の sanity check (mypy + isinstance) ----------


def test_ut_005_1_20_simple_commands_return_internal_error_when_handler_raises(
    api: ControlApi,
    command_handler_mock: Mock,
) -> None:
    """stop 系 5 メソッドも Handler 例外で ApiRejected(INTERNAL_ERROR) で復帰する。"""
    command_handler_mock.enqueue.side_effect = RuntimeError("handler crashed")

    for method_name in ("stop", "pause", "resume", "reset", "error_reset"):
        result = getattr(api, method_name)()
        assert isinstance(result, ApiRejected)
        assert result.reason is InternalError.UNEXPECTED_EXCEPTION


def test_ut_005_1_19_api_result_union_covers_all_response_types() -> None:
    """`ApiResult` Union が API のすべての戻り値型を含む(命名・export 整合性)。"""
    samples: list[ApiResult] = [
        Ok(token="t"),
        ApiRejected(reason=RejectReason.QUEUE_FULL),
        ValidationFailed(errors=[]),
        Confirmed(detail=_make_resume_detail()),
        WrongToken(),
        Expired(),
        NotPending(),
    ]
    # それぞれが ApiResult Union のメンバとして isinstance 検査を通る。
    union = Ok | ApiRejected | ValidationFailed | Confirmed | WrongToken | Expired | NotPending
    assert all(isinstance(s, union) for s in samples)
