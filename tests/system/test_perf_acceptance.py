"""System test — ST-PERF (STPR-VIP-001 §6.1, Step 19 H2).

ST-PERF.1-01〜05(SRS-P01 / P03 / P04 / P05 / P07 全体予算)を扱うが、
**Inc.1 CLI 範囲では対話 start / stop / flow_rate コマンドが提供されない**
(SDD §3 設計方針 + Step 19 H1 で確定:対話 UI は Inc.4 で正式実装)ため、
本 H2 では以下の通り Inc.1 範囲で実装可能なケースに限定する:

* **Inc.1 範囲で実装(全期間 Pass 必要):** ST-PERF.1-04(SRS-P05 起動時間)
  — `vip-ctrl --version` 起動時間を 10 サンプル median で測定し、SRS-P05
  全体予算 ≤ 3 sec を判定。
* **Inc.4 申し送り(`pytest.mark.skip`):** ST-PERF.1-01/02/03(SRS-P01 流量
  精度 / SRS-P03 start 全体応答 / SRS-P04 stop 全体応答)— いずれも対話
  start / stop コマンドが Inc.1 CLI に存在しないため、Inc.4 UI 層実装時に
  正式実装する(ISS-H-002 拡張、本 H2 着手中の発見、DEVELOPMENT_STEPS.md
  Step 19 H2 セクションに記録)。
* **Inc.1 完了タグ後申し送り(`pytest.mark.skip`):** ST-PERF.1-05(SRS-P07
  24 時間連続運転)— GitHub Actions 標準 runner 6 時間 timeout を超えるため、
  STPR §6.1.5 申し送りに従い self-hosted runner または別途実機環境で
  Inc.1 完了タグ後の後追い試験として実施。

関連 SRS: SRS-P01 / P03 / P04 / P05 / P07
関連 RCM: RCM-004(SRS-P07 経由で長期挙動、Inc.1 完了タグ後)
関連 HZ:  HZ-001(過量投与)、HZ-002(注入停止失敗)
"""

from __future__ import annotations

import statistics
import subprocess
import sys
import time
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from .conftest import InstalledVenv

pytestmark = pytest.mark.system


# ---------------------------------------------------------------------------
# ST-PERF.1-01 — SRS-P01 流量精度 ±5%(Inc.4 申し送り)
# ---------------------------------------------------------------------------
@pytest.mark.skip(
    reason=(
        "Inc.4 申し送り — Inc.1 CLI(vip-ctrl)は対話 flow_rate / start コマンドを"
        " 提供しない(SDD §3 設計方針 + B17 申し送り = 対話 UI は Inc.4 UI 層実装)。"
        "ISS-H-002 拡張、Step 19 H2 着手中に確認、DEVELOPMENT_STEPS.md Step 19 H2 参照。"
    ),
)
def test_st_perf_1_01_flow_rate_accuracy_within_5_percent() -> None:
    """SRS-P01 流量精度 ±5%(IEC 60601-2-24 相当、Inc.4 で実装)."""


# ---------------------------------------------------------------------------
# ST-PERF.1-02 — SRS-P03 start 全体応答 ≤ 500 ms(Inc.4 申し送り)
# ---------------------------------------------------------------------------
@pytest.mark.skip(
    reason=(
        "Inc.4 申し送り — Inc.1 CLI は対話 start コマンドを提供しない。"
        "F5 IT-PERF.2-01 で SDD §4.7.E 内訳 100 ms を検証済(IT/ST 分散配置)、"
        "ST 全体予算 500 ms は Inc.4 で正式実装。ISS-H-002 拡張参照。"
    ),
)
def test_st_perf_1_02_start_response_within_500ms() -> None:
    """SRS-P03 start 全体応答 ≤ 500 ms(Inc.4 で実装)."""


# ---------------------------------------------------------------------------
# ST-PERF.1-03 — SRS-P04 stop 全体応答 ≤ 200 ms(Inc.4 申し送り)
# ---------------------------------------------------------------------------
@pytest.mark.skip(
    reason=(
        "Inc.4 申し送り — Inc.1 CLI は対話 stop コマンドを提供しない。"
        "F5 IT-PERF.2-02 で SDD §4.7.A ファストパス 50 ms を検証済(IT/ST 分散配置)、"
        "ST 全体予算 200 ms は Inc.4 で正式実装。ISS-H-002 拡張参照。"
    ),
)
def test_st_perf_1_03_stop_response_within_200ms() -> None:
    """SRS-P04 stop 全体応答 ≤ 200 ms(Inc.4 で実装)."""


# ---------------------------------------------------------------------------
# ST-PERF.1-04 — SRS-P05 起動時間 ≤ 3 秒(Inc.1 範囲で実装)
# ---------------------------------------------------------------------------
def test_st_perf_1_04_startup_time_within_3_seconds(installed_venv: InstalledVenv) -> None:
    """SRS-P05 起動時間 ≤ 3 秒.

    `vip-ctrl --version` を 10 回 subprocess で起動し、各回の wall-clock
    経過時間(`time.perf_counter()` で計測)を記録する。median ≤ 3.0 sec
    を合否基準とする(SRS-P05 推奨要求の SRS 全体予算)。

    `--version` を選んだ理由:
    * 永続レコードを介在させず、CLI 立ち上げ + Python import グラフ完成 +
      `importlib.metadata.version` 解決までの「真の起動時間」を計測できる
    * Inc.1 範囲 CLI で動作する 3 経路(--version / --diagnose / デフォルト)
      のうち最短経路で SRS-P05 「IDLE 状態到達まで」≒ CLI が exit 0 で
      終了するまでを近似する

    `time.perf_counter()` 採用:F5 IT-PERF / F6 IT-PWR で `perf_counter_ns`
    を採用したのと同パターン(monotonic 時計 + 高精度)。
    """
    samples: list[float] = []
    for _ in range(10):
        start = time.perf_counter()
        result = subprocess.run(  # noqa: S603 — venv-installed script + literal args, trusted
            [str(installed_venv.vip_ctrl), "--version"],
            capture_output=True,
            text=True,
            check=True,
            timeout=10.0,
        )
        elapsed = time.perf_counter() - start
        assert result.returncode == 0, f"vip-ctrl --version failed: {result.stderr!r}"
        samples.append(elapsed)
    median = statistics.median(samples)
    assert median <= 3.0, (
        f"SRS-P05 violated: median startup {median:.3f} s > 3.0 s "
        f"(samples={[f'{s:.3f}' for s in samples]}, platform={sys.platform})"
    )


# ---------------------------------------------------------------------------
# ST-PERF.1-05 — SRS-P07 24 時間連続運転(Inc.1 完了タグ後申し送り)
# ---------------------------------------------------------------------------
@pytest.mark.skip(
    reason=(
        "Inc.1 完了タグ後申し送り(STPR §6.1.5)— GitHub Actions 標準 runner は 6 時間"
        " timeout、24 時間連続試験は self-hosted runner または別途実機環境が必要。"
        "Inc.1 完了タグ `v0.1.0-inc1` 付与後の後追い試験として実施(SDP §4.4 リリース"
        "判定遅延入力)。本ケースは Inc.4 でなく Inc.1 完了タグ後の即時実施対象。"
    ),
)
def test_st_perf_1_05_24h_continuous_run() -> None:
    """SRS-P07 24 時間連続運転 + SRS-P01 維持(Inc.1 完了タグ後 self-hosted runner で実施)."""
