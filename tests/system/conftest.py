"""System test fixtures (STPR-VIP-001 §6, Step 19 H2 で新設).

設計方針(Step 19 H2):

* **session-scoped venv fixture(`installed_venv`):** ST-OPS.1-01 で要求される
  クリーン venv → `pip install -e .` → `vip-ctrl` 起動経路を **session 1 回**
  で構築し、ST-OPS / ST-PERF / ST-RCM の各試験で再利用する。Step 19 F6
  IT-PWR の精密 subprocess 同期パターンとは異なり、本観点は「実 CLI 経路の
  正常動作確認」が目的のため標準 stdin / stdout / stderr 経路で対話する。
* **CLI 経由 subprocess 統一:** `subprocess.run([str(installed_venv.vip_ctrl), ...])`
  で実 CLI を起動する。`python -m vip_ctrl.cli` 経路は補助的に提供しない
  (CLI のパッケージング = `[project.scripts]` 経路の正常動作を含めて検証する
  のが ST-OPS の主目的のため、CLI script 経由を必須化)。
* **永続レコード fixture(`good_record_bytes` / `corrupt_record_bytes`):**
  UT-005.4(`tests/unit/test_cli.py` の `_build_good_record_bytes` 等)と
  同等のヘルパを system test 用に再構築する(UT のヘルパは `tests/unit`
  パッケージ private で system test から import するのは物理レイヤ越え
  になる + system は本来 import せず CLI 越し検証が原則のため、ヘルパは
  本 conftest 内で独立に提供する)。

Inc.4 申し送り(ISS-H-002 拡張、Step 19 H2 着手中の発見):

ST-PERF.1-01/02/03(対話 flow_rate / start / stop コマンド経由)+ ST-RCM.1-01/02/03/05/06
(対話 command 発行・confirm 経由)は **Inc.1 CLI 範囲外**(SDD §3 設計方針 +
B17 Step 19 申し送り = 対話 UI は Inc.4)のため `pytest.mark.skip` で骨格保持。
Inc.4 UI 層実装時に正式実装する。本 H2 では Inc.1 CLI 経路で検証可能な範囲
(ST-PERF.1-04 起動時間、ST-OPS.1-01〜05、ST-RCM.1-04 HZ-007 検出)を
完全実装する。
"""

from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from vip_ctrl.state_machine import State
from vip_persist import atomic_writer
from vip_persist.records import RuntimeState, Settings
from vip_persist.serializer import build_persisted_record, to_json

if TYPE_CHECKING:
    from collections.abc import Iterator

# 本パッケージの全試験に system マーカーを付与
pytestmark = pytest.mark.system

PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class InstalledVenv:
    """`pip install -e .` 済の system test 用 venv 情報."""

    venv_dir: Path
    python: Path
    vip_ctrl: Path


@pytest.fixture(scope="session")
def installed_venv(tmp_path_factory: pytest.TempPathFactory) -> InstalledVenv:
    """session 1 回限りで venv 構築 + `pip install -e .` を実行.

    ST-OPS.1-01(SRS-OPS-001 + 002)が要求する **クリーン venv インストール経路**
    を実環境で再現する fixture。同 venv の `vip-ctrl` script 実行ファイルを
    後続試験で再利用するため、session スコープでセットアップ時間を償却する。
    """
    venv_dir = tmp_path_factory.mktemp("vip_system_venv")
    subprocess.run(  # noqa: S603 — sys.executable + literal args, trusted
        [sys.executable, "-m", "venv", str(venv_dir)],
        check=True,
    )
    if sys.platform == "win32":
        bin_dir = venv_dir / "Scripts"
        python = bin_dir / "python.exe"
        vip_ctrl_path = bin_dir / "vip-ctrl.exe"
    else:
        bin_dir = venv_dir / "bin"
        python = bin_dir / "python"
        vip_ctrl_path = bin_dir / "vip-ctrl"
    # SRS-OPS-001 の `pip install` インプレース経路を実行(`-e` で開発エディタブル)
    subprocess.run(  # noqa: S603 — venv python + literal args, trusted
        [str(python), "-m", "pip", "install", "--quiet", "-e", str(PROJECT_ROOT)],
        check=True,
    )
    if not vip_ctrl_path.exists():  # pragma: no cover — defensive, tested in ST-OPS.1-01
        msg = f"vip-ctrl script was not installed at {vip_ctrl_path}"
        raise RuntimeError(msg)
    return InstalledVenv(venv_dir=venv_dir, python=python, vip_ctrl=vip_ctrl_path)


# ---------------------------------------------------------------------------
# 永続レコードヘルパ(UT-005.4 と同等の整合 / 破損レコードを system test 用に提供)
# ---------------------------------------------------------------------------


def build_good_record_bytes() -> bytes:
    """整合性検証 Ok を取れる代表値レコードを JSON bytes で返す."""
    settings = Settings(
        flow_rate=Decimal("60.0"),
        dose_volume=Decimal("60.0"),
        duration_min=60,
    )
    runtime_state = RuntimeState(
        state=State.IDLE,
        current_flow=Decimal("0.0"),
        accumulated_volume=Decimal("0.0"),
    )
    return to_json(build_persisted_record(settings, runtime_state, "2026-05-07T00:00:00Z"))


def write_good_record(path: Path) -> None:
    """整合レコードを `atomic_writer.write` 経由で配置."""
    res = atomic_writer.write(build_good_record_bytes(), path)
    if not isinstance(res, atomic_writer.WriteOk):  # pragma: no cover — fixture safety
        msg = f"failed to seed integrity-Ok record at {path}: {res}"
        raise RuntimeError(msg)  # noqa: TRY004 — fixture infra failure, RuntimeError appropriate


def write_corrupt_record(path: Path) -> None:
    """checksum 不一致になる破損レコードを配置(ST-RCM.1-04 = HZ-007 用).

    `_build_good_record_bytes` の checksum 文字列の先頭に `X` を挿入することで
    SHA-256 16 進値を逸脱させ、Integrity Validator(UNIT-004.1)が
    `FailsafeRecommended` を返す状態を作る。
    """
    data = build_good_record_bytes()
    text = data.decode()
    if '"checksum":"' not in text:  # pragma: no cover — schema invariant
        msg = "good record bytes did not contain checksum field"
        raise RuntimeError(msg)
    flipped = text.replace('"checksum":"', '"checksum":"X', 1)
    res = atomic_writer.write(flipped.encode(), path)
    if not isinstance(res, atomic_writer.WriteOk):  # pragma: no cover — fixture safety
        msg = f"failed to seed corrupted record at {path}: {res}"
        raise RuntimeError(msg)  # noqa: TRY004 — fixture infra failure, RuntimeError appropriate


@pytest.fixture
def persist_path(tmp_path: Path) -> Iterator[Path]:
    """各試験で使う一時 `--persist-path`(test 終了時に親ディレクトリ全消去)."""
    target = tmp_path / "persist.json"
    yield target
    # tmp_path は pytest が自動 cleanup するが、明示的に bak / temp も消しておく
    for sibling in (target, target.with_suffix(".json.bak"), target.with_suffix(".json.tmp")):
        if sibling.exists():
            sibling.unlink()


# ---------------------------------------------------------------------------
# CLI 起動ヘルパ(subprocess.run のラッパ)
# ---------------------------------------------------------------------------


def run_vip_ctrl(
    venv: InstalledVenv,
    args: list[str],
    *,
    timeout: float = 10.0,
) -> subprocess.CompletedProcess[str]:
    """`vip-ctrl` script を subprocess 経由で起動 + 結果を返す.

    `text=True` で str を扱う。`check=False` で exit code は呼出側で検証
    (CLI は warning level でも exit 0 を返す設計のため、合否判定は stdout
    JSON の `details.integrity_ok` で行うケースがある)。
    """
    return subprocess.run(  # noqa: S603 — venv-installed script + literal args, trusted
        [str(venv.vip_ctrl), *args],
        capture_output=True,
        text=True,
        check=False,
        timeout=timeout,
    )
