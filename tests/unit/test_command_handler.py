"""UT-001.3 — Command Handler (UNIT-001.3 per SDD-VIP-001 §4.7).

Implements UTPR-VIP-001 §7.3.12 test cases UT-001.3-01 .. UT-001.3-21.
Realises the dispatch path between Control API (UNIT-005.1) and the
State Machine (UNIT-001.1) with a stop-fast-path (SRS-P04, ≤ 50 ms)
and a normal FIFO queue for the remaining commands.

Step 19 B13 design judgments (recorded in DEVELOPMENT_STEPS.md):

* `Command` and `CommandKind` are owned by `command_handler.py`;
  UNIT-005.1 will import them in a later step.
* `_is_acceptable_in_state` consults the existing `TRANSITION_TABLE`
  in `state_machine.py` (DRY: state-machine table is the source of
  truth, no duplication in Command Handler).
* SRS-P03/P04 statistical timing measurement is deferred to
  ITPR §5.6 (continuation of B4/B5/B8/B10 deferral pattern).
  This UT exercises only the deterministic fast-path semantics +
  one loose-bound smoke (≤ 200 ms) for SRS-P04 functional check.
* `Command(kind, payload)` keeps the value object simple — payload
  validation lives in UNIT-005.1 Control API; Command Handler
  treats payload as opaque.

Related SRS: SRS-010, SRS-013, SRS-014, SRS-P03, SRS-P04.
Related HZ:  HZ-001 (over-delivery), HZ-002 (under-delivery).
"""

from __future__ import annotations

import dataclasses
import threading
import time
from datetime import UTC, datetime
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest

if TYPE_CHECKING:
    from collections.abc import Iterator

from vip_ctrl.command_handler import (
    MAX_QUEUE_SIZE,
    STOP_KINDS,
    Accepted,
    AcceptResult,
    Command,
    CommandHandler,
    CommandKind,
    Completed,
    CompletionResult,
    Failed,
    Rejected,
    RejectReason,
    SupersededByStopError,
    TimedOut,
    UnknownTokenError,
)
from vip_ctrl.state_machine import (
    EventKind,
    State,
    StateMachine,
    TransitionEvent,
    WatchdogReason,
)

# ---------- helpers / fixtures ----------


def _make_event(kind: EventKind) -> TransitionEvent:
    return TransitionEvent(kind=kind, timestamp=datetime.now(UTC))


@pytest.fixture
def sm_idle() -> StateMachine:
    """Fresh State Machine in IDLE."""
    sm = StateMachine()
    sm.set_initial(State.IDLE, needs_confirm=False)
    return sm


@pytest.fixture
def sm_running() -> StateMachine:
    """State Machine transitioned to RUNNING."""
    sm = StateMachine()
    sm.set_initial(State.IDLE, needs_confirm=False)
    sm.request_transition(_make_event(EventKind.CMD_START))
    return sm


@pytest.fixture
def sm_error() -> StateMachine:
    """State Machine forced to ERROR."""
    sm = StateMachine()
    sm.set_initial(State.IDLE, needs_confirm=False)
    sm.on_watchdog_timeout(WatchdogReason.OTHER)
    return sm


@pytest.fixture
def handler_idle(sm_idle: StateMachine) -> Iterator[CommandHandler]:
    h = CommandHandler(state_machine=sm_idle)
    h.start()
    yield h
    h.stop()


@pytest.fixture
def handler_running(sm_running: StateMachine) -> Iterator[CommandHandler]:
    h = CommandHandler(state_machine=sm_running)
    h.start()
    yield h
    h.stop()


@pytest.fixture
def handler_error(sm_error: StateMachine) -> Iterator[CommandHandler]:
    h = CommandHandler(state_machine=sm_error)
    h.start()
    yield h
    h.stop()


# ---------- UT-001.3-01: 初期 IDLE で START Accepted + token 取得 ----------


def test_ut_001_3_01_start_in_idle_is_accepted(
    handler_idle: CommandHandler,
) -> None:
    result: AcceptResult = handler_idle.enqueue(Command(kind=CommandKind.START))
    assert isinstance(result, Accepted)
    assert isinstance(result.token, str)
    assert len(result.token) > 0


# ---------- UT-001.3-02: await_completion で State Machine が RUNNING に遷移 ----------


def test_ut_001_3_02_await_completion_transitions_state_machine(
    sm_idle: StateMachine,
    handler_idle: CommandHandler,
) -> None:
    accepted = handler_idle.enqueue(Command(kind=CommandKind.START))
    assert isinstance(accepted, Accepted)
    completion: CompletionResult = handler_idle.await_completion(
        accepted.token,
        timeout_ms=1000,
    )
    assert isinstance(completion, Completed)
    assert sm_idle.current() == State.RUNNING


# ---------- UT-001.3-03: 不正状態で Rejected(INVALID_FOR_CURRENT_STATE) ----------


def test_ut_001_3_03_invalid_command_for_state_is_rejected(
    handler_idle: CommandHandler,
) -> None:
    """IDLE 中に STOP は TRANSITION_TABLE に登録なし → 早期拒否。"""
    result = handler_idle.enqueue(Command(kind=CommandKind.STOP))
    assert isinstance(result, Rejected)
    assert result.reason == RejectReason.INVALID_FOR_CURRENT_STATE


# ---------- UT-001.3-04: キュー満杯で Rejected(QUEUE_FULL) ----------


def test_ut_001_3_04_queue_full_rejects_with_queue_full(
    sm_running: StateMachine,
) -> None:
    """通常パスのみで MAX_QUEUE_SIZE を埋める。dispatch スレッドが処理しないように
    State Machine を停滞させる構造を作るため、handler を未起動のまま enqueue する。
    """
    h = CommandHandler(state_machine=sm_running)
    # dispatch を起動しないので queue は消費されない
    accepted_count = 0
    rejected_full = False
    for _ in range(MAX_QUEUE_SIZE + 5):
        result = h.enqueue(Command(kind=CommandKind.PAUSE))
        if isinstance(result, Accepted):
            accepted_count += 1
        elif isinstance(result, Rejected) and result.reason == RejectReason.QUEUE_FULL:
            rejected_full = True
            break
    assert accepted_count == MAX_QUEUE_SIZE
    assert rejected_full is True


# ---------- UT-001.3-05: stop ファストパス — 通常コマンドを破棄 ----------


def test_ut_001_3_05_stop_fast_path_supersedes_pending(
    sm_running: StateMachine,
) -> None:
    """RUNNING 中に PAUSE 5 件 + STOP enqueue → STOP が先、他は SupersededByStop。"""
    h = CommandHandler(state_machine=sm_running)
    # dispatch 未起動で 5 件溜める(通常キューに堆積)
    pause_tokens: list[str] = []
    for _ in range(5):
        result = h.enqueue(Command(kind=CommandKind.PAUSE))
        assert isinstance(result, Accepted)
        pause_tokens.append(result.token)
    stop_result = h.enqueue(Command(kind=CommandKind.STOP))
    assert isinstance(stop_result, Accepted)

    # ここで dispatch を起動する -> ファストパスが先に処理される
    h.start()
    try:
        stop_completion = h.await_completion(stop_result.token, timeout_ms=1000)
        assert isinstance(stop_completion, Completed)
        assert sm_running.current() == State.STOPPED
        # 破棄された PAUSE は SupersededByStopError で完了
        for tok in pause_tokens:
            comp = h.await_completion(tok, timeout_ms=1000)
            assert isinstance(comp, Failed)
            assert isinstance(comp.error, SupersededByStopError)
    finally:
        h.stop()


# ---------- UT-001.3-06: ERROR_RESET ファストパス ----------


def test_ut_001_3_06_error_reset_fast_path(
    sm_error: StateMachine,
    handler_error: CommandHandler,
) -> None:
    accepted = handler_error.enqueue(Command(kind=CommandKind.ERROR_RESET))
    assert isinstance(accepted, Accepted)
    completion = handler_error.await_completion(accepted.token, timeout_ms=1000)
    assert isinstance(completion, Completed)
    assert sm_error.current() == State.IDLE


# ---------- UT-001.3-07: 不明 token への await → UnknownTokenError ----------


def test_ut_001_3_07_unknown_token_returns_failed(
    handler_idle: CommandHandler,
) -> None:
    completion = handler_idle.await_completion(
        "00000000-0000-0000-0000-000000000000",
        timeout_ms=10,
    )
    assert isinstance(completion, Failed)
    assert isinstance(completion.error, UnknownTokenError)


# ---------- UT-001.3-08: timeout — TimedOut ----------


def test_ut_001_3_08_timeout_returns_timed_out(
    sm_running: StateMachine,
) -> None:
    """dispatch を起動しないため event がセットされず timeout する。"""
    h = CommandHandler(state_machine=sm_running)
    accepted = h.enqueue(Command(kind=CommandKind.PAUSE))
    assert isinstance(accepted, Accepted)
    completion = h.await_completion(accepted.token, timeout_ms=10)
    assert isinstance(completion, TimedOut)
    assert completion.elapsed_ms == 10


# ---------- UT-001.3-09: token 一意性 ----------


def test_ut_001_3_09_token_uniqueness_under_concurrent_enqueue(
    sm_running: StateMachine,
) -> None:
    """並行 100 件 enqueue で全 token がユニーク。"""
    h = CommandHandler(state_machine=sm_running)
    tokens: list[str] = []
    lock = threading.Lock()

    def worker() -> None:
        for _ in range(10):
            r = h.enqueue(Command(kind=CommandKind.PAUSE))
            if isinstance(r, Accepted):
                with lock:
                    tokens.append(r.token)
            elif isinstance(r, Rejected) and r.reason == RejectReason.QUEUE_FULL:
                # キュー満杯は許容(token 一意性の検証目的)
                pass

    threads = [threading.Thread(target=worker) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(tokens) >= MAX_QUEUE_SIZE  # 少なくとも MAX_QUEUE_SIZE 個は受領
    assert len(set(tokens)) == len(tokens)  # 全件ユニーク


# ---------- UT-001.3-10: 順次処理(FIFO) ----------


def test_ut_001_3_10_normal_queue_is_fifo(
    handler_running: CommandHandler,
    sm_running: StateMachine,
) -> None:
    """RUNNING で PAUSE → RUNNING からは CMD_PAUSE のみ受理可能。
    1 件ずつ順次完了することを await_completion で確認。
    """
    accepted = handler_running.enqueue(Command(kind=CommandKind.PAUSE))
    assert isinstance(accepted, Accepted)
    completion = handler_running.await_completion(accepted.token, timeout_ms=1000)
    assert isinstance(completion, Completed)
    assert sm_running.current() == State.PAUSED


# ---------- UT-001.3-11: 完了通知 cleanup — 2 回目は UnknownToken ----------


def test_ut_001_3_11_completion_token_is_consumed_once(
    handler_idle: CommandHandler,
) -> None:
    accepted = handler_idle.enqueue(Command(kind=CommandKind.START))
    assert isinstance(accepted, Accepted)
    first = handler_idle.await_completion(accepted.token, timeout_ms=1000)
    assert isinstance(first, Completed)
    second = handler_idle.await_completion(accepted.token, timeout_ms=10)
    assert isinstance(second, Failed)
    assert isinstance(second.error, UnknownTokenError)


# ---------- UT-001.3-12: dispatch スレッド task 例外 — Failed、ループ継続 ----------


def test_ut_001_3_12_task_exception_results_in_failed_and_loop_continues(
    sm_running: StateMachine,
) -> None:
    """`request_transition` を例外を上げる stub に差し替えて _handle 内 try/except を試す。"""
    h = CommandHandler(state_machine=sm_running)
    h.start()
    try:
        with patch.object(
            sm_running,
            "request_transition",
            side_effect=RuntimeError("simulated"),
        ):
            accepted = h.enqueue(Command(kind=CommandKind.PAUSE))
            assert isinstance(accepted, Accepted)
            completion = h.await_completion(accepted.token, timeout_ms=1000)
            assert isinstance(completion, Failed)
            assert isinstance(completion.error, RuntimeError)
        # ループ継続確認 — 次のコマンドが正常に処理される
        next_accepted = h.enqueue(Command(kind=CommandKind.PAUSE))
        assert isinstance(next_accepted, Accepted)
        next_completion = h.await_completion(next_accepted.token, timeout_ms=1000)
        assert isinstance(next_completion, Completed)
    finally:
        h.stop()


# ---------- UT-001.3-13: start/stop ライフサイクル ----------


def test_ut_001_3_13_start_then_stop_lifecycle(sm_idle: StateMachine) -> None:
    h = CommandHandler(state_machine=sm_idle)
    h.start()
    assert h.is_running() is True
    h.stop()
    assert h.is_running() is False


# ---------- UT-001.3-14: 2 重 start → RuntimeError ----------


def test_ut_001_3_14_double_start_raises_runtime_error(sm_idle: StateMachine) -> None:
    h = CommandHandler(state_machine=sm_idle)
    h.start()
    try:
        with pytest.raises(RuntimeError, match="already started"):
            h.start()
    finally:
        h.stop()


# ---------- UT-001.3-15: 2 重 stop → no-op ----------


def test_ut_001_3_15_double_stop_is_no_op(sm_idle: StateMachine) -> None:
    h = CommandHandler(state_machine=sm_idle)
    h.start()
    h.stop()
    h.stop()


# ---------- UT-001.3-16: stop before start → no-op ----------


def test_ut_001_3_16_stop_before_start_is_no_op(sm_idle: StateMachine) -> None:
    h = CommandHandler(state_machine=sm_idle)
    h.stop()


# ---------- UT-001.3-17: 定数 MAX_QUEUE_SIZE == 16 ----------


def test_ut_001_3_17_max_queue_size_is_16() -> None:
    assert MAX_QUEUE_SIZE == 16


# ---------- UT-001.3-18: STOP_KINDS == {STOP, ERROR_RESET} ----------


def test_ut_001_3_18_stop_kinds_contract() -> None:
    assert frozenset({CommandKind.STOP, CommandKind.ERROR_RESET}) == STOP_KINDS


# ---------- UT-001.3-19: stop ファストパス スモーク(緩い 200 ms 境界) ----------


def test_ut_001_3_19_stop_fast_path_smoke_under_200ms(
    handler_running: CommandHandler,
) -> None:
    """SRS-P04(stop ≤ 200 ms)の機能スモーク。

    P95 統計試験は ITPR §5.6 申し送り。本 UT は緩い境界(200 ms 以内)
    で「ファストパス機能の動作」を確認。
    """
    start_ts = time.monotonic()
    accepted = handler_running.enqueue(Command(kind=CommandKind.STOP))
    assert isinstance(accepted, Accepted)
    completion = handler_running.await_completion(accepted.token, timeout_ms=500)
    elapsed = time.monotonic() - start_ts
    assert isinstance(completion, Completed)
    assert elapsed < 0.2  # 200 ms 以内


# ---------- UT-001.3-20: コマンド種別マッピング ----------


def test_ut_001_3_20_command_kind_to_event_kind_mapping(
    sm_running: StateMachine,
    handler_running: CommandHandler,
) -> None:
    """RUNNING で PAUSE → State Machine は CMD_PAUSE で PAUSED に遷移。"""
    accepted = handler_running.enqueue(Command(kind=CommandKind.PAUSE))
    assert isinstance(accepted, Accepted)
    completion = handler_running.await_completion(accepted.token, timeout_ms=1000)
    assert isinstance(completion, Completed)
    assert sm_running.current() == State.PAUSED


# ---------- UT-001.3-21: Command の不変性 ----------


def test_ut_001_3_21_command_is_frozen() -> None:
    """frozen dataclass: 書き換え時に `FrozenInstanceError`。"""
    cmd = Command(kind=CommandKind.START)
    with pytest.raises(dataclasses.FrozenInstanceError):
        cmd.kind = CommandKind.STOP  # type: ignore[misc]


# ---------- UT-001.3-22: payload は opaque に保持される ----------


def test_ut_001_3_22_command_payload_is_opaque(
    handler_idle: CommandHandler,
) -> None:
    """Command Handler は payload を検証せず、State Machine 側に opaque に渡す。

    Inc.1 範囲では payload は使われない(UNIT-005.1 で検証実装)。
    """
    cmd = Command(kind=CommandKind.START, payload={"key": "value"})
    accepted = handler_idle.enqueue(cmd)
    assert isinstance(accepted, Accepted)
    completion = handler_idle.await_completion(accepted.token, timeout_ms=1000)
    assert isinstance(completion, Completed)


# ---------- UT-001.3-23: CONFIRM_RESUME (未マップ) は INVALID_FOR_CURRENT_STATE ----------


def test_ut_001_3_23_unmapped_command_kind_is_rejected(
    handler_idle: CommandHandler,
) -> None:
    """`CommandKind.CONFIRM_RESUME` は `_CMD_TO_EVENT` に未登録(SDD §4.7.A の
    confirm_resume は UNIT-004.2 Resume Confirmation Gate 経由で別経路)。
    したがって本ユニット経由では `INVALID_FOR_CURRENT_STATE` で拒否される。
    """
    result = handler_idle.enqueue(Command(kind=CommandKind.CONFIRM_RESUME))
    assert isinstance(result, Rejected)
    assert result.reason == RejectReason.INVALID_FOR_CURRENT_STATE
