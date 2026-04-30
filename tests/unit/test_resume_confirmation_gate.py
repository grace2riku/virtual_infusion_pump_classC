"""UT-004.2 — Resume Confirmation Gate (UNIT-004.2 per SDD-VIP-001 §4.14).

Implements UTPR-VIP-001 §7.3.14 detailed test cases UT-004.2-01 .. UT-004.2-15.
Realises RCM-016 (resume confirmation, HZ-007 protective measure) and
SRS-028 (no auto-resume of interrupted infusions). The gate holds an
optional pending resume request, issues a 128-bit `secrets.token_hex(16)`
token, and forwards the operator-confirmed `CMD_RESUME` transition to the
State Machine — never auto-resuming.

Step 19 B15 design judgments (recorded in DEVELOPMENT_STEPS.md):

* `ResumeDetail` is defined inside `resume_gate.py` (concern locality —
  only consumed here in Inc.1; promotion to `vip_persist.records` is an
  Inc.4 task once the integrity-validator → resume-gate path is wired).
* `StateMachine` is constructor-injected (B9/B10 pattern); UT replaces it
  with `unittest.mock.Mock(spec=StateMachine)` to verify the
  `request_transition(TransitionEvent(CMD_RESUME, meta=...))` call.
* `clock: Callable[[], float] = time.monotonic` is constructor-injected
  (B4/B9 pattern) so UT-004.2-07 can advance fake time past EXPIRY_SEC
  without touching real clocks.
* All value objects (`PendingResume`, `ResumeDetail`, `Confirmed`,
  `WrongToken`, `NotPending`, `Expired`) are `frozen=True, slots=True`
  (B11/B12/B13/B14 pattern); UT-004.2-12 exercises the frozen contract.
* MC/DC 100% target — RCM-016 unit, every branch of `confirm` (not
  pending / wrong token / expired / ok) and `set_pending` (already
  pending / fresh) and `check_expiry` (none / expired / fresh) covered.

Related SRS: SRS-028, SRS-RCM-016.
Related RCM: RCM-016.
Related HZ:  HZ-007 (persisted-data corruption / unsafe auto-resume).
"""

from __future__ import annotations

import dataclasses
import logging
import threading
from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import Mock

import pytest

from vip_ctrl.state_machine import (
    EventKind,
    State,
    StateMachine,
    TransitionEvent,
    TransitionOk,
)
from vip_integrity.resume_gate import (
    EXPIRY_SEC,
    Confirmed,
    Expired,
    NotPending,
    PendingResume,
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


def _make_detail() -> ResumeDetail:
    return ResumeDetail(
        settings=_make_settings(),
        state=State.PAUSED,
        accumulated_volume=Decimal("50.0"),
    )


class FakeClock:
    """Mutable monotonic stand-in for `time.monotonic()` in UT."""

    def __init__(self, t0: float = 1000.0) -> None:
        self.t = t0

    def __call__(self) -> float:
        return self.t

    def advance(self, dt: float) -> None:
        self.t += dt


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock()


@pytest.fixture
def state_machine_mock() -> Mock:
    sm: Mock = Mock(spec=StateMachine)
    sm.request_transition.return_value = TransitionOk(State.RUNNING)
    return sm


@pytest.fixture
def gate(state_machine_mock: Mock, clock: FakeClock) -> ResumeConfirmationGate:
    return ResumeConfirmationGate(state_machine=state_machine_mock, clock=clock)


# ---------- UT-004.2-01: token は 32 hex (128 bit) ----------


def test_ut_004_2_01_set_pending_returns_32_hex_token(
    gate: ResumeConfirmationGate,
) -> None:
    """`set_pending` の戻り値 token は 32 桁の hex 文字列(SDD §4.14.A)。"""
    token = gate.set_pending(_make_detail())

    assert isinstance(token, str)
    assert len(token) == 32
    assert all(c in "0123456789abcdef" for c in token)


# ---------- UT-004.2-02: is_pending / pending_detail の遷移 ----------


def test_ut_004_2_02_is_pending_and_detail_are_reflected(
    gate: ResumeConfirmationGate,
) -> None:
    """`set_pending` 前後で `is_pending` と `pending_detail` が遷移する。"""
    assert gate.is_pending() is False
    assert gate.pending_detail() is None

    detail = _make_detail()
    gate.set_pending(detail)

    assert gate.is_pending() is True
    assert gate.pending_detail() == detail


# ---------- UT-004.2-03: 正常 confirm + State Machine 連携 ----------


def test_ut_004_2_03_confirm_with_valid_token_returns_confirmed_and_drives_state_machine(
    gate: ResumeConfirmationGate,
    state_machine_mock: Mock,
) -> None:
    """正 token で confirm すると `Confirmed(detail)` と CMD_RESUME 遷移要求。"""
    detail = _make_detail()
    token = gate.set_pending(detail)

    result = gate.confirm(token)

    assert isinstance(result, Confirmed)
    assert result.detail == detail
    state_machine_mock.request_transition.assert_called_once()
    call_arg = state_machine_mock.request_transition.call_args.args[0]
    assert isinstance(call_arg, TransitionEvent)
    assert call_arg.kind is EventKind.CMD_RESUME
    assert call_arg.metadata.get("resume_token") == token
    assert gate.is_pending() is False


# ---------- UT-004.2-04: 誤 token は WrongToken、pending 維持 ----------


def test_ut_004_2_04_confirm_with_wrong_token_keeps_pending(
    gate: ResumeConfirmationGate,
    state_machine_mock: Mock,
) -> None:
    """誤 token で confirm すると `WrongToken`、pending は維持される。"""
    detail = _make_detail()
    gate.set_pending(detail)

    result = gate.confirm("0" * 32)

    assert isinstance(result, WrongToken)
    assert gate.is_pending() is True
    assert gate.pending_detail() == detail
    state_machine_mock.request_transition.assert_not_called()


# ---------- UT-004.2-05: 未 pending での confirm は NotPending ----------


def test_ut_004_2_05_confirm_when_not_pending_returns_not_pending(
    gate: ResumeConfirmationGate,
    state_machine_mock: Mock,
) -> None:
    """pending なしで confirm すると `NotPending`、State Machine 不変。"""
    result = gate.confirm("a" * 32)

    assert isinstance(result, NotPending)
    state_machine_mock.request_transition.assert_not_called()


# ---------- UT-004.2-06: 2 重 set_pending は RuntimeError ----------


def test_ut_004_2_06_double_set_pending_raises_runtime_error(
    gate: ResumeConfirmationGate,
) -> None:
    """既に pending のとき set_pending を再度呼ぶと `RuntimeError`(SDD §4.14.E)。"""
    gate.set_pending(_make_detail())

    with pytest.raises(RuntimeError, match="ResumeGate already pending"):
        gate.set_pending(_make_detail())


# ---------- UT-004.2-07: 期限切れ後の confirm は Expired + pending 解除 ----------


def test_ut_004_2_07_expired_confirm_returns_expired_and_clears_pending(
    gate: ResumeConfirmationGate,
    clock: FakeClock,
    state_machine_mock: Mock,
) -> None:
    """`set_pending` 後 EXPIRY_SEC + ε 経過 → confirm で Expired、pending 解除。"""
    token = gate.set_pending(_make_detail())
    clock.advance(EXPIRY_SEC + 1)

    result = gate.confirm(token)

    assert isinstance(result, Expired)
    assert gate.is_pending() is False
    state_machine_mock.request_transition.assert_not_called()


# ---------- UT-004.2-08: cancel で pending 解除 + 再 confirm は NotPending ----------


def test_ut_004_2_08_cancel_clears_pending_and_subsequent_confirm_is_not_pending(
    gate: ResumeConfirmationGate,
) -> None:
    """`cancel` で pending 解除、その後の confirm(同一 token)は `NotPending`。"""
    token = gate.set_pending(_make_detail())

    gate.cancel()

    assert gate.is_pending() is False
    assert isinstance(gate.confirm(token), NotPending)


# ---------- UT-004.2-09: 1000 回 cycle で token ユニーク(エントロピー試験) ----------


def test_ut_004_2_09_token_uniqueness_over_1000_cycles(
    gate: ResumeConfirmationGate,
) -> None:
    """1000 回 set_pending → cancel cycle で全 token がユニーク(128 bit エントロピー)。"""
    tokens: set[str] = set()
    for _ in range(1000):
        tokens.add(gate.set_pending(_make_detail()))
        gate.cancel()

    assert len(tokens) == 1000


# ---------- UT-004.2-10: check_expiry で期限超過時に warning 発火 ----------


def test_ut_004_2_10_check_expiry_logs_warning_when_expired(
    gate: ResumeConfirmationGate,
    clock: FakeClock,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """check_expiry が期限超過の pending を検出して warning ログ発火。"""
    gate.set_pending(_make_detail())
    clock.advance(EXPIRY_SEC + 1)

    with caplog.at_level(logging.WARNING, logger="vip_integrity.resume_gate"):
        gate.check_expiry()

    warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert any("expir" in r.message.lower() for r in warnings)
    # 期限切れ警告は pending を解除しない(明示的 confirm/cancel が必要)。
    assert gate.is_pending() is True


# ---------- UT-004.2-11: check_expiry で期限内は警告なし ----------


def test_ut_004_2_11_check_expiry_silent_when_not_expired(
    gate: ResumeConfirmationGate,
    clock: FakeClock,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """check_expiry が期限内の場合は warning を出さない。"""
    gate.set_pending(_make_detail())
    clock.advance(EXPIRY_SEC - 1)

    with caplog.at_level(logging.WARNING, logger="vip_integrity.resume_gate"):
        gate.check_expiry()

    warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert warnings == []


# ---------- UT-004.2-12: PendingResume の frozen 契約 ----------


def test_ut_004_2_12_pending_resume_is_frozen() -> None:
    """`PendingResume` は frozen dataclass であり代入不可。"""
    pending = PendingResume(
        token="0" * 32,
        detail=_make_detail(),
        set_at=0.0,
        set_at_wall=datetime.now(UTC),
    )

    with pytest.raises(dataclasses.FrozenInstanceError):
        pending.token = "1" * 32  # type: ignore[misc]


# ---------- UT-004.2-13: cancel の未 pending 時 no-op ----------


def test_ut_004_2_13_cancel_when_not_pending_is_no_op(
    gate: ResumeConfirmationGate,
    state_machine_mock: Mock,
) -> None:
    """pending なしで cancel を呼んでも例外なし、State Machine 不変。"""
    gate.cancel()
    gate.cancel()  # 冪等

    assert gate.is_pending() is False
    state_machine_mock.request_transition.assert_not_called()


# ---------- UT-004.2-14: check_expiry が pending なしのとき静黙 ----------


def test_ut_004_2_14_check_expiry_silent_when_no_pending(
    gate: ResumeConfirmationGate,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """pending なしで check_expiry を呼んでも warning なし。"""
    with caplog.at_level(logging.WARNING, logger="vip_integrity.resume_gate"):
        gate.check_expiry()

    warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert warnings == []


# ---------- UT-004.2-15: 並行 confirm の排他性 ----------


def test_ut_004_2_15_concurrent_confirm_only_one_succeeds(
    gate: ResumeConfirmationGate,
    state_machine_mock: Mock,
) -> None:
    """同一 token を 2 スレッドで confirm すると 1 つだけ Confirmed、もう 1 つは NotPending。"""
    detail = _make_detail()
    token = gate.set_pending(detail)

    barrier = threading.Barrier(2)
    results: list[object] = []
    results_lock = threading.Lock()

    def _race() -> None:
        barrier.wait(timeout=2.0)
        r = gate.confirm(token)
        with results_lock:
            results.append(r)

    threads = [threading.Thread(target=_race) for _ in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=5.0)
        assert not t.is_alive()

    confirmed_count = sum(isinstance(r, Confirmed) for r in results)
    not_pending_count = sum(isinstance(r, NotPending) for r in results)
    assert confirmed_count == 1
    assert not_pending_count == 1
    state_machine_mock.request_transition.assert_called_once()
