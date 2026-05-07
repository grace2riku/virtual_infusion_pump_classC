"""System test — ST-OPS (STPR-VIP-001 §6.2, Step 19 H2).

ST-OPS.1-01〜05 を全件 Inc.1 範囲で実装する(SRS-OPS-004「CI で自動実行」必須)。
ST-OPS.1-03 の対話 start / stop 要求は **`vip-ctrl` デフォルト起動 + `--diagnose`
の JSON Lines 出力検証** に簡略化する(ISS-H-002 = STPR §6.2 ST-OPS.1-03 の
対話シナリオ簡略化、Step 19 H2 で確定)。理由:Inc.1 CLI は対話 start/stop
を提供しないが、SRS-OPS-010 の「JSON Lines 形式 + 5 必須キー」要件は CLI が
emit する全イベント(boot_snapshot / diagnose)で網羅可能で、SRS-OPS-010
合否判定としては十分である。対話経路を含めた網羅は Inc.4 で再評価する。

関連 SRS:
* SRS-OPS-001(`pip install` で導入)— ST-OPS.1-01
* SRS-OPS-002(CLI `vip-ctrl` 起動)— ST-OPS.1-01
* SRS-OPS-003(初回起動デフォルト動作 IDLE / 0 / 0)— ST-OPS.1-02
* SRS-OPS-004(CI 自動受入試験)— 本ファイル全体が `system-test.yml` で実行
* SRS-OPS-010(JSON Lines ログ最低 5 キー)— ST-OPS.1-03
* SRS-OPS-011(`--diagnose`)— ST-OPS.1-04
* SRS-OPS-012(`pip install --upgrade`)— ST-OPS.1-05

関連 RCM: —(運用要求のため RCM 直接対応なし)
関連 HZ: HZ-007(SRS-OPS-003 デフォルトで安全側起動 — ST-OPS.1-02)
"""

from __future__ import annotations

import json
import subprocess
from typing import TYPE_CHECKING, Any

import pytest

from .conftest import PROJECT_ROOT, run_vip_ctrl, write_good_record

if TYPE_CHECKING:
    from pathlib import Path

    from .conftest import InstalledVenv

pytestmark = pytest.mark.system

_REQUIRED_JSON_LINES_KEYS: frozenset[str] = frozenset(
    {"timestamp", "level", "component", "event", "details"},
)


def _parse_json_lines(text: str) -> list[dict[str, Any]]:
    """改行区切りで JSON Lines を辞書リストに parse(空行は無視)."""
    return [json.loads(line) for line in text.splitlines() if line.strip()]


# ---------------------------------------------------------------------------
# ST-OPS.1-01 — SRS-OPS-001 + 002 インストール → CLI 起動経路
# ---------------------------------------------------------------------------
def test_st_ops_1_01_install_and_version_exit_zero(installed_venv: InstalledVenv) -> None:
    """SRS-OPS-001(`pip install`)+ SRS-OPS-002(CLI 起動)の End-to-End 受入.

    `installed_venv` fixture が **session 1 回限り** で(a) クリーン venv 作成、
    (b) `pip install -e .` 実行、(c) `vip-ctrl` script の bin/ 配置を実施。
    本試験は (d) `vip-ctrl --version` を起動して exit code 0 + バージョン
    1 行出力を確認する受入の最終段階。

    合否基準:
    1. `vip-ctrl` script が venv の bin/ に配置されている
    2. `vip-ctrl --version` の exit code == 0
    3. stdout に `vip-ctrl ` 接頭辞のバージョン行 1 行
    """
    assert installed_venv.vip_ctrl.exists(), (
        f"SRS-OPS-002 violated: vip-ctrl script not present at {installed_venv.vip_ctrl}"
    )
    result = run_vip_ctrl(installed_venv, ["--version"])
    assert result.returncode == 0, (
        f"SRS-OPS-002 violated: exit code {result.returncode} != 0, stderr={result.stderr!r}"
    )
    lines = result.stdout.splitlines()
    assert len(lines) == 1, f"expected single version line, got {lines}"
    assert lines[0].startswith("vip-ctrl "), (
        f"version line did not start with 'vip-ctrl ': {lines[0]!r}"
    )


# ---------------------------------------------------------------------------
# ST-OPS.1-02 — SRS-OPS-003 初回起動時のデフォルト動作(IDLE / 0 / 0)
# ---------------------------------------------------------------------------
def test_st_ops_1_02_default_boot_uses_idle_zero_zero(
    installed_venv: InstalledVenv,
    persist_path: Path,
) -> None:
    """SRS-OPS-003 — 永続レコード不在の初回起動で IDLE / 流量 0 / 積算 0.

    HZ-007(永続記録破損 / 不在時の安全側起動)整合経路でもある。
    """
    assert not persist_path.exists(), "fixture should give a non-existent persist path"
    result = run_vip_ctrl(installed_venv, ["--persist-path", str(persist_path)])
    assert result.returncode == 0, f"default boot failed: stderr={result.stderr!r}"
    payloads = _parse_json_lines(result.stdout)
    assert len(payloads) == 1, f"expected one boot_snapshot line, got {payloads}"
    payload = payloads[0]
    assert payload["event"] == "boot_snapshot"
    details = payload["details"]
    assert details["record_present"] is False
    assert details["default_state"] == "IDLE"
    assert details["default_flow_rate"] == "0.0"
    assert details["default_accumulated_volume"] == "0.0"
    # 起動メッセージ(SDD §4.18.D)が stderr に出力される
    assert "Inc.1" in result.stderr
    assert "Inc.4" in result.stderr  # 対話モード Inc.4 申し送りメッセージ


# ---------------------------------------------------------------------------
# ST-OPS.1-03 — SRS-OPS-010 JSON Lines ログ最低項目(簡略化、ISS-H-002)
# ---------------------------------------------------------------------------
def test_st_ops_1_03_jsonlines_minimum_keys_in_all_paths(
    installed_venv: InstalledVenv,
    persist_path: Path,
) -> None:
    """SRS-OPS-010 — boot_snapshot + diagnose 両経路で 5 必須キー網羅.

    ISS-H-002 簡略化:Inc.1 CLI に対話 start / stop が無いため、SRS-OPS-010
    必須要件「全行が JSON Lines 形式 + timestamp / level / component / event /
    details」は **CLI が emit する 2 経路の boot_snapshot / diagnose**
    全行で網羅する。対話経路追加は Inc.4 で再評価。
    """
    # 経路 1: デフォルト boot
    boot = run_vip_ctrl(installed_venv, ["--persist-path", str(persist_path)])
    assert boot.returncode == 0, f"boot failed: {boot.stderr!r}"
    # 経路 2: --diagnose
    diag = run_vip_ctrl(installed_venv, ["--diagnose", "--persist-path", str(persist_path)])
    assert diag.returncode == 0, f"diagnose failed: {diag.stderr!r}"

    all_lines = _parse_json_lines(boot.stdout) + _parse_json_lines(diag.stdout)
    assert len(all_lines) == 2, f"expected 2 JSON lines total, got {len(all_lines)}"
    for record in all_lines:
        assert set(record.keys()) >= _REQUIRED_JSON_LINES_KEYS, (
            f"SRS-OPS-010 violated: missing keys in {record!r}"
        )
        # value-type contract: timestamp は ISO 8601 文字列、level / component / event は str
        assert isinstance(record["timestamp"], str)
        assert isinstance(record["level"], str)
        assert isinstance(record["component"], str)
        assert isinstance(record["event"], str)
        assert isinstance(record["details"], dict)


# ---------------------------------------------------------------------------
# ST-OPS.1-04 — SRS-OPS-011 `--diagnose` 出力(整合レコード存在状態)
# ---------------------------------------------------------------------------
def test_st_ops_1_04_diagnose_with_valid_record(
    installed_venv: InstalledVenv,
    persist_path: Path,
) -> None:
    """SRS-OPS-011 — `--diagnose` で整合レコードを `integrity_ok=true` 報告.

    Integrity Validator(UNIT-004.1)を CLI 経由で起動し、永続レコードの
    schema / checksum / 状態整合性を検証する system レベル経路。
    """
    write_good_record(persist_path)
    result = run_vip_ctrl(installed_venv, ["--diagnose", "--persist-path", str(persist_path)])
    assert result.returncode == 0
    payloads = _parse_json_lines(result.stdout)
    assert len(payloads) == 1
    payload = payloads[0]
    assert payload["event"] == "diagnose"
    assert payload["level"] == "info"
    assert payload["details"]["record_present"] is True
    assert payload["details"]["integrity_ok"] is True
    assert payload["details"]["failure_count"] == 0


# ---------------------------------------------------------------------------
# ST-OPS.1-05 — SRS-OPS-012 アップデートインプレース(簡略化)
# ---------------------------------------------------------------------------
def test_st_ops_1_05_upgrade_preserves_persist_record(
    installed_venv: InstalledVenv,
    persist_path: Path,
) -> None:
    """SRS-OPS-012 — `pip install --upgrade` 相当の再インストール後も永続レコードは整合.

    簡略化:Inc.1 範囲では `v0.1.0-inc0` 等の架空旧バージョンは存在しないため、
    同一 venv に対して `pip install --upgrade -e .` を再実行し、(i) 永続レコードが
    破損せず、(ii) アップデート後の `vip-ctrl --diagnose` で `integrity_ok=true` を
    返すことで「アップデート経路で永続レコードが保持される」ことを system レベル
    で実証する。Inc.2+ で旧バージョン → 新バージョンの真のマイグレーション
    試験に拡張する申し送りとする。
    """
    write_good_record(persist_path)
    upgrade = subprocess.run(  # noqa: S603 — venv python + literal args, trusted
        [
            str(installed_venv.python),
            "-m",
            "pip",
            "install",
            "--quiet",
            "--upgrade",
            "-e",
            str(PROJECT_ROOT),
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=120.0,
    )
    assert upgrade.returncode == 0, (
        f"SRS-OPS-012 violated: pip install --upgrade failed exit={upgrade.returncode},"
        f" stderr={upgrade.stderr!r}"
    )
    diag = run_vip_ctrl(installed_venv, ["--diagnose", "--persist-path", str(persist_path)])
    assert diag.returncode == 0
    payload = _parse_json_lines(diag.stdout)[0]
    assert payload["details"]["record_present"] is True
    assert payload["details"]["integrity_ok"] is True
