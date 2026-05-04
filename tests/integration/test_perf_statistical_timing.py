"""Integration test — IT-PERF (SRS-P02 / P03 / P04 / P06 統計時間試験).

ITPR-VIP-001 §6.8 の詳細化(Step 19 F5)。SOUP-012 `pytest-benchmark` 初運用。
全 6 ケースに `@pytest.mark.integration` + `@pytest.mark.perf` +
`@pytest.mark.nightly` 付与(§8.1 規定どおり PR では除外、CI nightly +
ローカル `pytest -m perf` 3 連続安定確認で実施)。

設計判断(Step 19 F5、ITPR §6.8.4 と二重記録):

* **§6.8 数値訂正(MINOR、CR 不要):** ITPR v0.7 までの §6.8 骨格(L557)に
  対し、SRS / SDD / UTPR との数値乖離を着手前クロスレビューで発見し、本
  詳細化と同 PR で訂正。SRS-P02 = 100 ms ± 10 ms(SRS L123 / SDD §4.6.B)、
  SRS-P03 = SDD §4.7.E 内訳 100 ms(SRS 全体 500 ms は ST 範疇)、SRS-P04
  = SDD §4.7.A ファストパス 50 ms(SRS 全体 200 ms は ST 範疇)、SRS-P06 =
  IT-PERF.3-02 で永続化負荷下の SRS-P02 維持を新規追加。
* **本物 SUT 比率最大化:** F1 → F2 → F3 → F4 と進めてきた延長で、本 §6.8 は
  本物 ControlLoop / 本物 CommandHandler / 本物 HwFailsafeTimer / 本物
  atomic_writer を主体に Mock は StateMachine と PumpController に限定、
  MagicMock は `side_effect` で時刻記録するための Watchdog 偽装にのみ使用。
* **`linux_only` auto-skip + Linux nightly SRS/SDD 厳密判定**(Step 19 F5 着手中
  の発見):F2 / F3 で採用した「macOS sleep ジッタ対策 = 緩い境界」を本 §6.8
  でも当初試したが、CommandHandler 30 回スレッド lifecycle + Control Loop
  実時間スレッド + 永続化スレッド並行で macOS の OS noise が大きく flake
  発生(3 連続中 2 回 fail を実測)。`tests/conftest.py` に `linux_only`
  マーカー auto-skip hook を新規実装(F6 で予定だった機能を F5 で先取り、
  F6/F7 でも継続使用)し、ITPR §8.1 規定「IT-PERF / IT-PWR / IT-SIDE は
  Linux runner 限定 + nightly schedule」と完全整合。境界は SRS-P02 = 110
  ms / SDD ファストパス = 50 ms / SRS-P06 = 110 ms の **SRS / SDD 値で厳密
  判定**(macOS local では auto-skip で flake を回避、Linux nightly で
  実行)。
* **テスト定義順序:** IT-PERF.2 系 → IT-PERF.3-01 → IT-PERF.1-01 →
  IT-PERF.3-02 → IT-PERF.1-02(benchmark)の順で配置。`pytest-benchmark`
  fixture が後続テストの GC / スケジューリングに影響するため benchmark
  使用ケースを末尾に置く運用パターン(Step 19 F5 着手中の発見)。
* **IT-PERF.3-01 `heartbeat()` 削除設計:** 当初 `timer.start()` 直後に
  `timer.heartbeat()` を呼ぶ設計だったが、monitor スレッドの第 1 回
  `check_once()` と main の `heartbeat()` が同 lock を競合し、SDD §4.3.E
  のクロック逆転安全側発火条件(Step 19 B4 整合化)が偶発的に発動して
  trip elapsed が極端に小さくなる race condition を着手中に発見。
  `start()` で `_last_heartbeat = clock()` が設定済のため `heartbeat()`
  呼出は冗長 — `start()` 時刻を基準とすることで race を回避(本ファイル
  + ITPR §6.8.4 に二重記録)。

関連 SRS: SRS-P02、SRS-P03(SDD 内訳)、SRS-P04(SDD 内訳)、SRS-P06、
SRS-RCM-004(タイマ精度の長時間連続観察)。
関連 IF-U: IF-U-001 / IF-U-002(CommandHandler、IT-PERF.2-XX)、IF-U-003 / 004 /
005(ControlLoop、IT-PERF.1-XX / 3-02)、IF-U-005(HwFailsafeTimer、
IT-PERF.3-01)、IF-U-009(永続化、IT-PERF.3-02)。
関連 UT: UT-001.2-19(UTPR §7.3.9 v0.10 申し送り)、UT-001.3-19(UTPR §7.3.12
v0.13 申し送り)、UT-002.4(UTPR §7.3.3 v0.4 申し送り)。
"""

from __future__ import annotations

import threading
import time
from decimal import Decimal
from typing import TYPE_CHECKING

import pytest

from vip_ctrl.command_handler import (
    Accepted,
    Command,
    CommandHandler,
    CommandKind,
    Completed,
)
from vip_ctrl.control_loop import ControlLoop
from vip_ctrl.state_machine import State, StateMachine
from vip_persist import atomic_writer
from vip_persist.atomic_writer import WriteOk
from vip_sim.failsafe_timer import HwFailsafeTimer

from .conftest import make_consistent_record_settings

if TYPE_CHECKING:
    from pathlib import Path
    from unittest.mock import MagicMock, Mock

    from pytest_benchmark.fixture import BenchmarkFixture

    from vip_sim.pump_observer import PumpObserver
    from vip_sim.pump_simulator import PumpSimulator


# 本ファイル全体に integration + perf + nightly + linux_only マーカー付与
# (§8.1 規定:IT-PERF / IT-PWR / IT-SIDE は Linux runner 限定 + nightly schedule)
# `linux_only` は `tests/conftest.py` の hook で macOS / Windows では auto-skip
# される(Step 19 F5 で先取り実装、F6 / F7 で継続使用)。
pytestmark = [
    pytest.mark.integration,
    pytest.mark.perf,
    pytest.mark.nightly,
    pytest.mark.linux_only,
]


def _percentile(values: list[float], pct: float) -> float:
    """ソート済みリストから百分位値を取得(線形補間なし、簡易実装).

    pct は 0.0〜1.0 の範囲。線形補間ではないため、サンプル数が少ない場合
    (≥ 25)でも安定した境界判定ができる(F2 / F3 教訓継続)。
    """
    if not values:
        return 0.0
    sorted_vals = sorted(values)
    idx = int(len(sorted_vals) * pct)
    if idx >= len(sorted_vals):
        idx = len(sorted_vals) - 1
    return sorted_vals[idx]


# ---------------------------------------------------------------------------
# IT-PERF.2-01 — SRS-P03 start 応答 P95 ≤ 100 ms(SDD 内訳)
# ---------------------------------------------------------------------------
def test_it_perf_2_01_start_response_p95() -> None:
    """SRS-P03(SDD §4.7.E 内訳予算): start enqueue → completion P95 ≤ 100 ms.

    結合契約(IF-U-001/002):
    - 30 サンプル(各回新規 StateMachine + CommandHandler を構築、
      `set_initial` の単一呼出制約のため)
    - 各サンプルで `enqueue(START)` → `await_completion` の経過時間を計測
    - P95 ≤ 100 ms(SDD §4.7.E 内訳、SRS の全体 500 ms は ST 範疇で別途検証)
    """
    elapsed_ms_list: list[float] = []
    sample_count = 30
    for _ in range(sample_count):
        sm = StateMachine()
        sm.set_initial(State.IDLE, needs_confirm=False)
        handler = CommandHandler(state_machine=sm)
        handler.start()
        try:
            t0 = time.perf_counter()
            result = handler.enqueue(Command(kind=CommandKind.START))
            assert isinstance(result, Accepted)
            completion = handler.await_completion(result.token, timeout_ms=500)
            t1 = time.perf_counter()
            assert isinstance(completion, Completed), f"sample failed: {completion!r}"
            elapsed_ms_list.append((t1 - t0) * 1000)
        finally:
            handler.stop()
    assert len(elapsed_ms_list) == sample_count
    p95 = _percentile(elapsed_ms_list, 0.95)
    assert p95 <= 100.0, f"P95 = {p95:.2f} ms exceeds 100 ms (SDD §4.7.E 内訳予算)"


# ---------------------------------------------------------------------------
# IT-PERF.2-02 — SRS-P04 stop ファストパス P95 ≤ 50 ms(SDD 内訳厳密)
# ---------------------------------------------------------------------------
def test_it_perf_2_02_stop_fastpath_p95() -> None:
    """SRS-P04(SDD §4.7.A ファストパス): RUNNING で stop → completion P95 ≤ 50 ms.

    結合契約(IF-U-001/002):
    - 30 サンプル(各回 IDLE → START → RUNNING 遷移後に stop のみ計測)
    - stop は STOP_KINDS ファストパス(キューバイパス)を経由
    - P95 ≤ 50 ms(SDD §4.7.A ファストパス内訳厳密、Linux runner 限定 =
      `linux_only` auto-skip でローカル macOS では skip、ITPR §6.8.4 二重記録)
    - SRS の全体 200 ms は ST 範疇で別途検証
    """
    elapsed_ms_list: list[float] = []
    sample_count = 30
    for _ in range(sample_count):
        sm = StateMachine()
        sm.set_initial(State.IDLE, needs_confirm=False)
        handler = CommandHandler(state_machine=sm)
        handler.start()
        try:
            # IDLE → START → RUNNING まで前準備(計測対象外)
            start_result = handler.enqueue(Command(kind=CommandKind.START))
            assert isinstance(start_result, Accepted)
            start_done = handler.await_completion(start_result.token, timeout_ms=500)
            assert isinstance(start_done, Completed)
            assert sm.current() is State.RUNNING

            # stop ファストパスのみ計測
            t0 = time.perf_counter()
            stop_result = handler.enqueue(Command(kind=CommandKind.STOP))
            assert isinstance(stop_result, Accepted)
            stop_done = handler.await_completion(stop_result.token, timeout_ms=500)
            t1 = time.perf_counter()
            assert isinstance(stop_done, Completed), f"sample failed: {stop_done!r}"
            elapsed_ms_list.append((t1 - t0) * 1000)
        finally:
            handler.stop()
    assert len(elapsed_ms_list) == sample_count
    p95 = _percentile(elapsed_ms_list, 0.95)
    # Linux runner 限定実行(linux_only auto-skip)、SDD §4.7.A ファストパス
    # 内訳予算 50 ms で厳密判定。macOS local では auto-skip でこのアサート
    # を回避(ITPR §6.8.4 二重記録)。
    assert p95 <= 50.0, f"P95 = {p95:.2f} ms exceeds 50 ms (SDD §4.7.A ファストパス内訳)"


# ---------------------------------------------------------------------------
# IT-PERF.3-01 — HW Failsafe Timer 発火タイミング長時間観察
# ---------------------------------------------------------------------------
def test_it_perf_3_01_hw_failsafe_trip_timing(
    mock_pump_controller: Mock,
) -> None:
    """SRS-RCM-004: HW Failsafe Timer の発火経過時刻が 400-700 ms 内.

    結合契約(IF-U-005、SDD §4.3.B HEARTBEAT_TIMEOUT=0.5、MONITOR_INTERVAL=0.1):
    - `force_stop_failsafe.side_effect` で発火時刻記録
    - `start()` で `_last_heartbeat = clock()` が設定済のため `heartbeat()`
      呼出は冗長(かつ monitor 第 1 回 check_once との race condition で
      SDD §4.3.E クロック逆転安全側発火が偶発発動する race を回避するため
      明示的に呼ばない、Step 19 F5 着手中の設計是正、ITPR §6.8.4 二重記録)。
    - 発火経過 ∈ [400, 700] ms(macOS sleep ジッタ + MONITOR_INTERVAL 余裕)。
    """
    trip_times: list[float] = []

    def record_trip(reason: str) -> None:  # noqa: ARG001 — capture timing only
        trip_times.append(time.perf_counter())

    mock_pump_controller.force_stop_failsafe.side_effect = record_trip
    timer = HwFailsafeTimer(mock_pump_controller)
    timer.start()
    # `start()` が `_last_heartbeat = clock()` を設定済 — `heartbeat()` 呼出は
    # 冗長かつ race condition の発生源となるため呼ばない(設計是正)。
    t_initial = time.perf_counter()
    try:
        time.sleep(0.7)  # 500 ms timeout + MONITOR_INTERVAL 100 ms 余裕 + ジッタ
    finally:
        timer.stop()

    assert len(trip_times) == 1, f"expected exactly 1 trip, got {len(trip_times)}"
    elapsed_ms = (trip_times[0] - t_initial) * 1000
    assert 400 <= elapsed_ms <= 700, (
        f"trip elapsed = {elapsed_ms:.2f} ms out of [400, 700] ms"
        f" (HEARTBEAT_TIMEOUT 500 ms ± MONITOR_INTERVAL 100 ms + jitter)"
    )


# ---------------------------------------------------------------------------
# IT-PERF.1-01 — SRS-P02 Control Loop 100 ms 周期精度 P95
# ---------------------------------------------------------------------------
def test_it_perf_1_01_control_loop_period_p95(
    mock_running_state_machine: Mock,
    pump_simulator_real: PumpSimulator,
    pump_observer_real: PumpObserver,
    magicmock_sw_heartbeat_sink: MagicMock,
    magicmock_hw_heartbeat_sink: MagicMock,
) -> None:
    """SRS-P02: 本物 ControlLoop の sw_heartbeat 間隔 P95 ≤ 130 ms.

    結合契約(IF-U-003/004/005、SDD §4.6.B `PERIOD_SEC=0.1`):
    - sw_heartbeat 呼出時刻を `side_effect` で記録(F4 で確立した時刻計測パターン)
    - 3.0 秒動作で約 30 周期分のサンプル(間隔は 29 個程度)
    - P95 ≤ 0.110 sec(SRS-P02 100 ms ± 10 ms 厳密判定、Linux runner 限定
      = `linux_only` auto-skip でローカル macOS では skip、ITPR §6.8.4 二重記録)
    - 平均 ≤ 0.105 sec(SRS-P02 +5%)
    """
    timestamps: list[float] = []

    def record_sw_heartbeat() -> None:
        timestamps.append(time.perf_counter())

    magicmock_sw_heartbeat_sink.heartbeat.side_effect = record_sw_heartbeat
    settings = make_consistent_record_settings(flow_rate=Decimal("60.0"))
    loop = ControlLoop(
        state_machine=mock_running_state_machine,
        pump=pump_simulator_real,
        observer=pump_observer_real,
        sw_watchdog=magicmock_sw_heartbeat_sink,
        hw_watchdog=magicmock_hw_heartbeat_sink,
        settings_provider=lambda: settings,
    )
    loop.start()
    try:
        time.sleep(3.0)  # 約 30 周期分(SRS-P02 100 ms x 30 = 3 sec)
    finally:
        loop.stop()

    intervals = [timestamps[i + 1] - timestamps[i] for i in range(len(timestamps) - 1)]
    assert len(intervals) >= 25, f"sample count too few: {len(intervals)} (expected >= 25 in 3 sec)"
    p95 = _percentile(intervals, 0.95)
    mean_interval = sum(intervals) / len(intervals)
    # Linux runner 限定実行(linux_only auto-skip)、SRS-P02 100 ms ± 10% =
    # 110 ms で厳密判定(ITPR §6.8.4 二重記録)。
    assert p95 <= 0.110, f"P95 = {p95 * 1000:.2f} ms exceeds 110 ms (SRS-P02 100 ms +- 10%)"
    assert mean_interval <= 0.105, (
        f"mean = {mean_interval * 1000:.2f} ms exceeds 105 ms (SRS-P02 +5%)"
    )


# ---------------------------------------------------------------------------
# IT-PERF.3-02 — SRS-P06 永続化スレッド負荷下の SRS-P02 維持
# ---------------------------------------------------------------------------
def test_it_perf_3_02_persistence_load_does_not_block_control_loop(
    tmp_path: Path,
    mock_running_state_machine: Mock,
    pump_simulator_real: PumpSimulator,
    pump_observer_real: PumpObserver,
    magicmock_sw_heartbeat_sink: MagicMock,
    magicmock_hw_heartbeat_sink: MagicMock,
) -> None:
    """SRS-P06: 永続化負荷下でも sw_heartbeat 間隔 P95 ≤ 110 ms.

    結合契約(IF-U-003/004/005、IF-U-009):
    - Control Loop と並行に永続化スレッドで `atomic_writer.write` をループ
    - 3.0 秒間で Control Loop の sw_heartbeat 間隔 P95 を測定
    - P95 ≤ 0.110 sec(SRS-P06 = SRS-P02 ジッタ内 110 ms 厳密、Linux runner
      限定 = `linux_only` auto-skip、ITPR §6.8.4 二重記録)
    - 永続化スレッドが 3 秒間で ≥ 50 回成功(負荷の実証)
    """
    timestamps: list[float] = []

    def record_sw_heartbeat() -> None:
        timestamps.append(time.perf_counter())

    magicmock_sw_heartbeat_sink.heartbeat.side_effect = record_sw_heartbeat
    settings = make_consistent_record_settings(flow_rate=Decimal("60.0"))
    loop = ControlLoop(
        state_machine=mock_running_state_machine,
        pump=pump_simulator_real,
        observer=pump_observer_real,
        sw_watchdog=magicmock_sw_heartbeat_sink,
        hw_watchdog=magicmock_hw_heartbeat_sink,
        settings_provider=lambda: settings,
    )

    persist_target = tmp_path / "perf.dat"
    payload = b"x" * 1024
    persist_count = 0
    persist_stop = threading.Event()
    persist_count_lock = threading.Lock()

    def persist_loop() -> None:
        nonlocal persist_count
        while not persist_stop.is_set():
            result = atomic_writer.write(payload, persist_target)
            if isinstance(result, WriteOk):
                with persist_count_lock:
                    persist_count += 1

    persist_thread = threading.Thread(target=persist_loop, name="PersistLoad", daemon=True)
    persist_thread.start()
    loop.start()
    try:
        time.sleep(3.0)
    finally:
        loop.stop()
        persist_stop.set()
        persist_thread.join(timeout=2.0)

    intervals = [timestamps[i + 1] - timestamps[i] for i in range(len(timestamps) - 1)]
    assert len(intervals) >= 25, f"sample count too few: {len(intervals)} (expected >= 25 in 3 sec)"
    p95 = _percentile(intervals, 0.95)
    mean_interval = sum(intervals) / len(intervals)
    # Linux runner 限定実行(linux_only auto-skip)、SRS-P06 = SRS-P02 ジッタ
    # 内 110 ms で厳密判定(ITPR §6.8.4 二重記録)。
    assert p95 <= 0.110, (
        f"P95 = {p95 * 1000:.2f} ms exceeds 110 ms (SRS-P06 = SRS-P02 ジッタ内 100 ms +- 10%)"
    )
    assert mean_interval <= 0.105, (
        f"mean = {mean_interval * 1000:.2f} ms exceeds 105 ms (SRS-P02 +5%)"
    )
    with persist_count_lock:
        final_count = persist_count
    assert final_count >= 50, f"persistence count = {final_count} (expected >= 50 in 3 sec)"


# ---------------------------------------------------------------------------
# IT-PERF.1-02 — SRS-P02 tick() 平均サイクル時間(pytest-benchmark 初運用)
# ---------------------------------------------------------------------------
# 本テストは pytest-benchmark の plugin が後続テストの GC / スケジューリング
# に影響するため、ファイル末尾に配置する(Step 19 F5 着手中の発見、ITPR
# §6.8.4 二重記録)。
def test_it_perf_1_02_control_loop_tick_benchmark(
    benchmark: BenchmarkFixture,
    mock_running_state_machine: Mock,
    pump_simulator_real: PumpSimulator,
    pump_observer_real: PumpObserver,
    magicmock_sw_heartbeat_sink: MagicMock,
    magicmock_hw_heartbeat_sink: MagicMock,
) -> None:
    """SRS-P02: tick() 単発の平均サイクル時間 ≤ 10 ms(SOUP-012 初使用).

    `pytest-benchmark` の自動 round / iteration 調整で安定した平均時間を
    取得。SRS-P02 100 ms 周期に対し処理時間は十分余裕(緩い境界 10 ms)。
    """
    settings = make_consistent_record_settings(flow_rate=Decimal("60.0"))
    loop = ControlLoop(
        state_machine=mock_running_state_machine,
        pump=pump_simulator_real,
        observer=pump_observer_real,
        sw_watchdog=magicmock_sw_heartbeat_sink,
        hw_watchdog=magicmock_hw_heartbeat_sink,
        settings_provider=lambda: settings,
    )
    benchmark(loop.tick)
    # pytest-benchmark 5.x: benchmark.stats は計測完了後に値が入る(`Any | None` 型)
    stats = benchmark.stats
    assert stats is not None, "benchmark stats not populated"
    mean_sec: float = stats.stats.mean
    assert mean_sec <= 0.010, f"mean tick = {mean_sec * 1000:.2f} ms exceeds 10 ms"
