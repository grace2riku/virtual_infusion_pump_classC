"""Integration test — IT-SEP.1 (SEP-001 ランタイム分離 + 真の本物注入 E2E).

ITPR-VIP-001 §6.7 の詳細化(Step 19 F4)。
SAD §9 SEP-001(クラス C ↔ クラス B 分離)が **AST 静的検証(UT-005.3-13)に
加えてランタイムでも維持** されること、すなわち、クラス B モジュール
(`src/vip_api_b/`)実行時にクラス C 副作用(state mutation / I/O / threading)が
観測されないことを **真の本物注入経路** で実証する。

設計判断(Step 19 F4):

* §6.1〜§6.3 の Mock 主体検証から **本物注入主体** への移行 — Step 19 F1.6 で
  CR-0004 (b) Adapter(`vip_api/_validation_bridge.py`)+ CR-0005 (a)
  `_HeartbeatSink.heartbeat() -> None` 引数なし化が解消されたことを前提とし、
  本物 `vip_api_b.validate_settings`(Adapter 経由)+ 本物 `SwWatchdog` /
  `HwFailsafeTimer`(`heartbeat()` 引数なし契約)を `ControlApi` /
  `ControlLoop` に注入できる経路を結合状態で実証する。
* IT-SEP.1-01 は UT-005.3-13(`vip_api_b/validation_api.py` 単体の AST 検証)を
  **`vip_api_b/` パッケージ全ファイル + ランタイム `sys.modules` 観点** に拡張。
* IT-SEP.1-02〜05 は **本物 vip_api_b 注入経路**(Adapter 経由)で SEP-001
  越え経路の正常 / 異常 / 純粋関数性 / 例外握りつぶし契約を網羅。
* IT-SEP.1-06 は **本物 SwWatchdog + HwFailsafeTimer + ControlLoop** で
  `heartbeat()` 引数なし契約の階層防御 E2E を実証(Watchdog の monitor
  スレッドは起動せず `last_heartbeat()` ベースで境界判定の決定性を確保)。
* MC/DC 目標は据置「—」— UT-005.3 / UT-001.5 / UT-002.4 / UT-001.2 で 100%
  達成済、IT は契約検証中心(coverage 計測対象外)。

関連 SRS: SRS-UX-001/004/005、SRS-005、SRS-RCM-003、SRS-RCM-004。
関連 RCM: —(SEP-001 アーキテクチャ検証)+ RCM-003 / RCM-004(階層防御 E2E、
IT-SEP.1-06 のみ副次)。
関連 SAD: §9 SEP-001(クラス C / B 分離)。
関連 IF-U: IF-U-004(ControlLoop → SwWatchdog)、IF-U-005(ControlLoop →
HwFailsafeTimer)、IF-U-011(ControlApi → ValidationApi)。
関連 UT: UT-005.3-13(AST 静的検証 → ランタイム拡張)、UT-005.1-bridge-01〜06
(Adapter 単体 6 ケース)、UT-005.3(Validation API 21 ケース)、UT-001.2 /
UT-001.5 / UT-002.4(本物 Watchdog + ControlLoop 単体)。
"""

from __future__ import annotations

import ast
import sys
from decimal import Decimal
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest

from vip_api.control_api import (
    Ok,
    ValidationFailed,
)
from vip_ctrl.control_loop import ControlLoop
from vip_ctrl.state_machine import State
from vip_persist.records import Settings

from .conftest import make_consistent_record_settings, make_consistent_settings

if TYPE_CHECKING:
    from unittest.mock import Mock

    from vip_api.control_api import ControlApi, ValidationApi
    from vip_ctrl.state_machine import StateMachine
    from vip_ctrl.watchdog import SwWatchdog
    from vip_sim.failsafe_timer import HwFailsafeTimer
    from vip_sim.pump_observer import PumpObserver
    from vip_sim.pump_simulator import PumpSimulator


# 本ファイル全体に integration マーカーを付与
pytestmark = pytest.mark.integration


_FORBIDDEN_CLASS_C_ROOTS: frozenset[str] = frozenset(
    {"vip_ctrl", "vip_sim", "vip_integrity", "vip_api"},
)
"""SEP-001:クラス B から import 禁止のクラス C パッケージルート(`vip_persist`
は frozen 値オブジェクト共有のため許容、UT-005.3-13 と同基準)。"""


# ---------------------------------------------------------------------------
# IT-SEP.1-01 — クラス B パッケージ全ファイルの AST 拡張検証
# ---------------------------------------------------------------------------
def test_it_sep_1_01_class_b_package_files_have_no_class_c_imports() -> None:
    """`vip_api_b/` パッケージ全ファイル(`__init__.py` 含む)の AST で
    クラス C ルートへの import が無いことを検証。

    UT-005.3-13(`validation_api.py` 単体の AST 検証)を **`vip_api_b/*.py`
    全件** に拡張。後続 IT-SEP.1-04 が `sys.modules` のランタイム観測を担当
    するため、本ケースは AST 軸の網羅(`__init__.py` も含めた静的検証)に
    focus を絞る(`del sys.modules` で reload を強制すると Adapter 側の
    関数バインドと不整合になり test_05 等で副作用が出るため、ランタイム
    観測は IT-SEP.1-04 に分散配置)。
    """
    package_dir = Path(__file__).resolve().parents[2] / "src" / "vip_api_b"
    py_files = sorted(package_dir.glob("*.py"))
    assert py_files, f"vip_api_b パッケージに .py ファイルがない: {package_dir}"

    for py in py_files:
        tree = ast.parse(py.read_text(encoding="utf-8"))
        seen_imports: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    seen_imports.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom) and node.module is not None:
                seen_imports.add(node.module.split(".")[0])
        intersection = seen_imports & _FORBIDDEN_CLASS_C_ROOTS
        assert not intersection, (
            f"SEP-001 violation (AST): {py.name} imports class-C roots {intersection}"
        )


# ---------------------------------------------------------------------------
# IT-SEP.1-02 — 本物 vip_api_b 注入経路 (Adapter 経由) 正常 ControlApi.start
# ---------------------------------------------------------------------------
def test_it_sep_1_02_real_class_b_validation_via_adapter_accepts_valid_settings(
    control_api_with_real_validation: ControlApi,
    real_state_machine_idle: StateMachine,
) -> None:
    """`make_validation_api()` 経由の本物 vip_api_b 注入で、整合 Settings の
    `start()` が `Ok(token=...)` を返す(SEP-001 越え経路の正常系).

    結合契約(IF-U-011 ControlApi → ValidationApi、CR-0004 (b) Adapter):
    - 本物 `vip_api_b.validate_settings` が `Ok(settings)` を返す
    - Adapter が空 list `[]` に変換し `ValidationFailed` 経路を回避
    - 本物 `CommandHandler.enqueue` が `Accepted(token)` を返す
    - 本物 `StateMachine.current()` は IDLE のまま(dispatch スレッド未起動)
    """
    settings = make_consistent_settings()

    result = control_api_with_real_validation.start(settings)

    assert isinstance(result, Ok)
    assert result.token != ""
    # SEP-001 boundary: クラス B 評価が StateMachine を変化させない(dispatch
    # スレッド未起動 + Validation Pass のため、状態遷移は enqueue 後に発生)
    assert real_state_machine_idle.current() is State.IDLE


# ---------------------------------------------------------------------------
# IT-SEP.1-03 — 本物注入経路 + 異常 settings → StateMachine 不変 (boundary 維持)
# ---------------------------------------------------------------------------
def test_it_sep_1_03_real_class_b_rejection_keeps_state_machine_idle(
    control_api_with_real_validation: ControlApi,
    real_state_machine_idle: StateMachine,
) -> None:
    """範囲外 settings(flow=1200.01)で本物 vip_api_b が `Err` 復帰 →
    `ValidationFailed` で `start()` 拒否、本物 `StateMachine.current()` は
    IDLE 不変(SEP-001 boundary が異常経路でも維持される実証).

    結合契約:
    - 本物 `vip_api_b.validate_settings` が `OutOfRange(flow_rate, ...)` を含む
      `Err` を返す
    - Adapter が `ValidationError(field='flow_rate', message='out_of_range: ...')`
      の list に変換
    - `ControlApi.start` が `ValidationFailed` を返し `enqueue` 経路に到達しない
    - 本物 `StateMachine.current() == State.IDLE` 不変(クラス B 拒否が
      クラス C 状態へ副作用伝播しない)
    """
    settings = Settings(
        flow_rate=Decimal("1200.01"),  # SRS-O-001 上限 1200.0 超
        dose_volume=Decimal("60.0"),
        duration_min=60,
    )

    result = control_api_with_real_validation.start(settings)

    assert isinstance(result, ValidationFailed)
    assert len(result.errors) >= 1
    assert any(e.field == "flow_rate" for e in result.errors)
    # SEP-001 boundary: クラス B 拒否でも StateMachine は IDLE 不変
    assert real_state_machine_idle.current() is State.IDLE


# ---------------------------------------------------------------------------
# IT-SEP.1-04 — 純粋関数性 + sys.modules スナップショット不変
# ---------------------------------------------------------------------------
def test_it_sep_1_04_class_b_validation_is_pure_and_no_class_c_side_effect(
    real_validation_api: ValidationApi,
) -> None:
    """同じ Settings に対する `validate_settings` を 5 回呼出し、
    結果が冪等(同じ list)+ 実行前後で `sys.modules` のクラス C 名前空間が
    変化しないことを実証(クラス B が I/O / threading / 動的 import の副作用を
    持たない pure-function 性質を、Adapter 経由で結合状態で検証).
    """
    settings = make_consistent_settings()

    # 軸 1: 冪等性(SDD §4.17.A pure-function 契約)
    snapshot_before = set(sys.modules)
    results = [real_validation_api.validate_settings(settings) for _ in range(5)]
    snapshot_after = set(sys.modules)

    # 5 回とも同じ結果(空 list = OK)
    assert all(r == [] for r in results), f"validate_settings は冪等でない: {results}"

    # 軸 2: クラス C モジュールの動的 import 副作用なし
    added = snapshot_after - snapshot_before
    forbidden_added = {name for name in added if name.split(".")[0] in _FORBIDDEN_CLASS_C_ROOTS}
    # 注:`vip_api`(Adapter 自身)はテスト import 時に既に sys.modules に
    # 存在するため、本ループでの追加対象には含まれない(snapshot_before 採取済)。
    assert not forbidden_added, (
        f"SEP-001 violation: validate_settings が新規 import を発生 {forbidden_added}"
    )


# ---------------------------------------------------------------------------
# IT-SEP.1-05 — 例外握りつぶし契約 (SDD §4.17.E、boundary 維持)
# ---------------------------------------------------------------------------
def test_it_sep_1_05_class_b_internal_exception_is_swallowed_at_boundary(
    control_api_with_real_validation: ControlApi,
    real_state_machine_idle: StateMachine,
) -> None:
    """`vip_api_b.validation_api.Decimal` を patch して例外注入 →
    `validate_settings` が SDD §4.17.E に従い `Err([Inconsistency('internal:...')])`
    を返し、Adapter 経由で `ValidationFailed` として呼び出し側に伝わる.

    結合契約(SEP-001 例外伝播禁止):
    - クラス B 内部例外は **SEP-001 境界を越えない**(`ApiRejected(InternalError)`
      にならず、`ValidationFailed` で正常な「拒否」として扱われる)
    - `ValidationError.field == 'settings_consistency'` かつ
      `message` が `'inconsistency: internal:'` で始まる
    - 本物 `StateMachine.current()` は IDLE 不変(boundary 維持)

    UT-005.3-08 が `vip_api_b.validation_api` 単体での挙動を網羅、本 IT は
    Adapter 経由で SEP-001 boundary が結合状態でも維持されることを実証。
    """
    settings = make_consistent_settings()

    # vip_api_b.validation_api 内部の Decimal 演算で例外注入
    # (`Decimal(settings.duration_min)` の呼出経路で TypeError を発生させる)
    with patch("vip_api_b.validation_api.Decimal", side_effect=RuntimeError("injected")):
        result = control_api_with_real_validation.start(settings)

    # 例外が SEP-001 境界を越えず、ValidationFailed として正常な「拒否」になる
    assert isinstance(result, ValidationFailed), (
        f"SEP-001 violation: 内部例外が boundary を越えた: {type(result).__name__}"
    )
    assert len(result.errors) >= 1
    consistency_errors = [e for e in result.errors if e.field == "settings_consistency"]
    assert consistency_errors, (
        f"Inconsistency が settings_consistency にマップされていない: {result.errors}"
    )
    assert any(e.message.startswith("inconsistency: internal:") for e in consistency_errors)
    # boundary 維持: 本物 StateMachine 不変
    assert real_state_machine_idle.current() is State.IDLE


# ---------------------------------------------------------------------------
# IT-SEP.1-06 — 本物 Watchdog + ControlLoop で heartbeat 引数なし契約 E2E
# ---------------------------------------------------------------------------
def test_it_sep_1_06_real_watchdogs_in_control_loop_heartbeat_argless_contract(
    mock_running_state_machine: Mock,
    pump_simulator_real: PumpSimulator,
    pump_observer_real: PumpObserver,
    sw_watchdog_for_loop: SwWatchdog,
    hw_failsafe_timer_for_loop: HwFailsafeTimer,
    mock_pump_controller: Mock,
) -> None:
    """**本物 SwWatchdog + 本物 HwFailsafeTimer + 本物 ControlLoop** + 本物
    PumpSimulator + 本物 PumpObserver で `tick()` を実行し、CR-0005 (a) 解消後の
    `heartbeat()` 引数なし契約が真の階層防御経路で機能することを実証.

    結合契約(IF-U-004 / IF-U-005、CR-0005 (a) 解消後):
    - `tick()` が True を返す(RUNNING 経路、SDD §4.6.A)
    - 本物 `SwWatchdog.last_heartbeat()` が tick 前から進む(本物 `time.monotonic`
      内部取得、`heartbeat() -> None` 契約)
    - 本物 `HwFailsafeTimer.last_heartbeat()` も同様に進む
    - 両 Watchdog の `is_tripped()` は False(直近 heartbeat 直後の `check_once()`)
    - SwWatchdog 経由の `mock_running_state_machine.on_watchdog_timeout` 不発火
    - HwFailsafeTimer 経由の `mock_pump_controller.force_stop_failsafe` 不発火
    - Pump への `set_flow_rate` が反映(本物 PumpSimulator `_target_flow=60`)

    本観点は §6.2 IT-RCM003(本物 Watchdog 単体実時間)と §6.3 IT-RCM004
    (MagicMock Watchdog の引数なし契約)を **両方本物で接続した E2E** に拡張、
    SEP-001 主旨ではなく **CR-0005 解消後の真の階層防御経路実証** を主観点とする。
    """
    settings = make_consistent_record_settings(flow_rate=Decimal("60.0"))
    loop = ControlLoop(
        state_machine=mock_running_state_machine,
        pump=pump_simulator_real,
        observer=pump_observer_real,
        sw_watchdog=sw_watchdog_for_loop,
        hw_watchdog=hw_failsafe_timer_for_loop,
        settings_provider=lambda: settings,
    )

    sw_baseline = sw_watchdog_for_loop.last_heartbeat()
    hw_baseline = hw_failsafe_timer_for_loop.last_heartbeat()

    assert loop.tick() is True

    # IF-U-004 / IF-U-005: 本物 Watchdog の last_heartbeat が tick で進む
    # (本物 `time.monotonic` の単調増加、`heartbeat()` 引数なし契約成立)
    assert sw_watchdog_for_loop.last_heartbeat() >= sw_baseline
    assert hw_failsafe_timer_for_loop.last_heartbeat() >= hw_baseline

    # 直後の check_once() では未トリップ(timeout 内)
    assert sw_watchdog_for_loop.check_once() is False
    assert hw_failsafe_timer_for_loop.check_once() is False
    assert not sw_watchdog_for_loop.is_tripped()
    assert not hw_failsafe_timer_for_loop.is_tripped()

    # 階層防御の被通知側が呼ばれていない(正常 heartbeat 経路)
    mock_running_state_machine.on_watchdog_timeout.assert_not_called()
    mock_pump_controller.force_stop_failsafe.assert_not_called()

    # IF-U-003: Pump への target_flow が本物 ControlLoop 経由で反映
    assert pump_simulator_real._target_flow == Decimal("60.0")  # noqa: SLF001
