"""System test — ST-RCM (STPR-VIP-001 §6.3, Step 19 H2).

ST-RCM.1-01〜06(Inc.1 範囲全 RCM 6 件)を扱うが、Inc.1 CLI 範囲では対話
コマンド経由の RCM 検証ができない(SDD §3 設計方針 + B17 申し送り = 対話 UI
は Inc.4)ため、本 H2 では以下の通り Inc.1 範囲で実装可能なケースに限定:

* **Inc.1 範囲で実装(全期間 Pass 必要):** ST-RCM.1-04(RCM-015 / SRS-RCM-015
  起動時整合性 = HZ-007)— `vip-ctrl --diagnose` 経由で破損永続レコード
  (checksum 改ざん)を Integrity Validator(UNIT-004.1)が検出することを
  system レベルで実証。F6 IT-PWR で subprocess + SIGKILL シナリオを検証済 →
  本 ST は CLI 経由の検出経路を `--diagnose` で実証する。
* **Inc.4 申し送り(`pytest.mark.skip`):**
  - ST-RCM.1-01(RCM-001 範囲外コマンド拒否): 対話コマンド発行が必要
  - ST-RCM.1-02(RCM-003 SW Watchdog タイムアウト): 対話 RUNNING 状態が必要
  - ST-RCM.1-03(RCM-004 100 ms 制御サイクル jitter): 対話 RUNNING 状態が必要
  - ST-RCM.1-05(RCM-016 再開ガード): 対話 confirm コマンドが必要
  - ST-RCM.1-06(RCM-019 状態遷移違反): 対話 STOPPED 状態 + start コマンドが必要

  上記は ISS-H-002 拡張(Step 19 H2 着手中の発見)— Inc.4 UI 層実装時に
  正式実装する。F1〜F6 IT で各 RCM の不具合検出能力は実証済(IT-RCM001〜003
  / IT-PWR / IT-SEP / IT-SIDE)、ST 妥当性確認(IEC 62304 §5.7.4)はその
  system 再現で「不具合検出能力が適切である」項目を満たす設計。

関連 SRS: SRS-RCM-015(起動時整合性)+ SRS-RCM-001/003/004/016/020(Inc.4 申し送り)
関連 RCM: RCM-015(本 H2 実装)+ RCM-001/003/004/016/019(Inc.4 申し送り)
関連 HZ:  HZ-007(永続記録破損 — ST-RCM.1-04 で実証)、HZ-001 / HZ-002(Inc.4)
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest

from .conftest import run_vip_ctrl, write_corrupt_record

if TYPE_CHECKING:
    from pathlib import Path

    from .conftest import InstalledVenv

pytestmark = pytest.mark.system


# ---------------------------------------------------------------------------
# ST-RCM.1-01 — RCM-001 範囲外コマンド拒否(Inc.4 申し送り)
# ---------------------------------------------------------------------------
@pytest.mark.skip(
    reason=(
        "Inc.4 申し送り — Inc.1 CLI は対話 flow_rate コマンドを提供しない。"
        "F1 IT-RCM001 で機能整合検証済(ITPR §6.1)。Inc.4 UI 層実装時に CLI"
        " 経由 system 再現を実装。ISS-H-002 拡張、Step 19 H2 で確認。"
    ),
)
def test_st_rcm_1_01_command_range_rejection() -> None:
    """RCM-001 / SRS-RCM-001 — 範囲外 flow_rate コマンド拒否(Inc.4 で実装)."""


# ---------------------------------------------------------------------------
# ST-RCM.1-02 — RCM-003 SW Watchdog タイムアウト(Inc.4 申し送り)
# ---------------------------------------------------------------------------
@pytest.mark.skip(
    reason=(
        "Inc.4 申し送り — Inc.1 CLI は対話 RUNNING 状態に遷移できない(start"
        " コマンド非対応)。F2 IT-RCM003 で機能整合検証済(ITPR §6.2)。"
        "Inc.4 で CLI 経由 system 再現を実装。ISS-H-002 拡張参照。"
    ),
)
def test_st_rcm_1_02_sw_watchdog_timeout() -> None:
    """RCM-003 / SRS-RCM-003 — SW Watchdog タイムアウト → ERROR(Inc.4 で実装)."""


# ---------------------------------------------------------------------------
# ST-RCM.1-03 — RCM-004 100 ms 制御サイクル jitter(Inc.4 申し送り)
# ---------------------------------------------------------------------------
@pytest.mark.skip(
    reason=(
        "Inc.4 申し送り — Inc.1 CLI は対話 RUNNING 状態に遷移できない。F3"
        " IT-RCM004 で機能整合検証済 + F5 IT-PERF.1-01 で SDD §4.6.B 100 ms ±10 ms"
        " を統計検証済(ITPR §6.3 + §6.8)。Inc.4 で CLI 経由 system 再現を実装。"
        "ISS-H-002 拡張参照。"
    ),
)
def test_st_rcm_1_03_control_cycle_jitter() -> None:
    """RCM-004 / SRS-RCM-004 — 100 ms ± 10 ms 制御サイクル維持(Inc.4 で実装)."""


# ---------------------------------------------------------------------------
# ST-RCM.1-04 — RCM-015 起動時整合性検証(Inc.1 範囲で実装、HZ-007 検出)
# ---------------------------------------------------------------------------
def test_st_rcm_1_04_integrity_validation_on_startup_detects_tamper(
    installed_venv: InstalledVenv,
    persist_path: Path,
) -> None:
    """RCM-015 / SRS-RCM-015 — 改ざん永続レコードを起動時に検出(HZ-007 system 再現).

    F6 IT-PWR は SDD §4.4.B 不変条件(target / .bak の常在)を subprocess +
    SIGKILL で検証した。本 ST は **system レベルでの検出経路** —
    `vip-ctrl --diagnose` を CLI 経由で起動し、Integrity Validator
    (UNIT-004.1)が破損レコードを `FailsafeRecommended` で報告することを
    JSON Lines snapshot で確認する(SRS-027 フェイルセーフ起動経路、
    SRS-ALM-002 ログ整合)。

    合否基準:
    1. exit code == 0(CLI 設計上、warning level でも exit 0)
    2. JSON `level == "warning"`(SRS-OPS-010 + SRS-ALM-002)
    3. JSON `details.record_present == true`(レコード自体は存在)
    4. JSON `details.integrity_ok == false`(改ざん検出)
    5. JSON `details.failure_count >= 1`(Validator が `Checksum*` 等の
       failure を 1 件以上報告)
    """
    write_corrupt_record(persist_path)
    result = run_vip_ctrl(installed_venv, ["--diagnose", "--persist-path", str(persist_path)])
    assert result.returncode == 0, f"unexpected exit code: {result.stderr!r}"
    payload = json.loads(result.stdout.strip())
    assert payload["event"] == "diagnose"
    assert payload["level"] == "warning", (
        f"SRS-ALM-002 violated: expected warning level, got {payload['level']!r}"
    )
    details = payload["details"]
    assert details["record_present"] is True, "破損レコードはファイルとして存在する"
    assert details["integrity_ok"] is False, (
        "RCM-015 violated: Integrity Validator did not detect tampered checksum"
    )
    assert details["failure_count"] >= 1, (
        "RCM-015 violated: failure_count must report at least one Integrity Failure"
    )


# ---------------------------------------------------------------------------
# ST-RCM.1-05 — RCM-016 再開ガード(Inc.4 申し送り)
# ---------------------------------------------------------------------------
@pytest.mark.skip(
    reason=(
        "Inc.4 申し送り — Inc.1 CLI は対話 confirm コマンドを提供しない。"
        "UNIT-004.2 ResumeConfirmationGate を UT で網羅済(UTPR §7.3.5)。"
        "Inc.4 で CLI 経由 confirm 経路の system 再現を実装。ISS-H-002 拡張参照。"
    ),
)
def test_st_rcm_1_05_resume_gate_blocks_until_confirm() -> None:
    """RCM-016 / SRS-RCM-016 — 再開ガード(明示 confirm 待ち)(Inc.4 で実装)."""


# ---------------------------------------------------------------------------
# ST-RCM.1-06 — RCM-019 状態遷移違反コマンド拒否(Inc.4 申し送り)
# ---------------------------------------------------------------------------
@pytest.mark.skip(
    reason=(
        "Inc.4 申し送り — Inc.1 CLI は対話 start / stop コマンドを提供しないため"
        "「STOPPED から start 発行」が再現できない。F1 IT-RCM001(範囲外コマンド)"
        " + UT-005.1 / 005.2 で StateMachine 経由の遷移違反検出を網羅済。"
        "Inc.4 で CLI 経由 system 再現を実装。ISS-H-002 拡張参照。"
    ),
)
def test_st_rcm_1_06_state_transition_violation() -> None:
    """RCM-019 / SRS-RCM-020 — 状態遷移違反コマンド拒否(Inc.4 で実装)."""
