"""Step 19 F0 — Integration test scaffolding smoke tests.

ITPR-VIP-001 §8.1 自動化方針の **CI 経路動作確認** を目的とする最小スモーク。
F1 以降で各観点(RCM-001 / RCM-003 / RCM-004 / SEP-001 / IT-PERF /
IT-PWR / IT-SIDE)の本格試験を追加する前段として、以下を確認する:

1. `@pytest.mark.integration` マーカーが pytest に登録されている
2. `pytest -m "integration and not nightly"` で本ファイルが選択され実行される
3. UT(`unit-test.yml`)では `addopts = ["-m", "not integration"]` により
   本ファイルが除外される(unit-test.yml 側で確認)
4. Inc.1 全 17 ユニット(UT 完了済)の代表 import がエラーなく機能する
"""

from __future__ import annotations

import pytest


@pytest.mark.integration
def test_integration_marker_registered_and_collected() -> None:
    """integration マーカー経由で本試験が collect されたことを assert で残す。

    本試験が実行された時点で(1)〜(3)は CI 経路として成立している。
    """
    assert True, "integration test was collected via -m integration"


@pytest.mark.integration
def test_inc1_all_subsystems_importable() -> None:
    """Inc.1 全 6 パッケージ + 主要モジュールの import 健全性を確認する。

    各ユニットの単独 import は UT(`tests/test_package_structure.py`)で
    検証済だが、本試験は **IT 環境でも同じ import グラフが成立する** ことの
    再現確認(F1 以降の各 RCM 結合試験で複数パッケージ横断 import を行う前提
    が崩れていないか早期検知する目的)。
    """
    import vip_api  # noqa: PLC0415
    import vip_api_b  # noqa: PLC0415
    import vip_ctrl  # noqa: PLC0415
    import vip_integrity  # noqa: PLC0415
    import vip_persist  # noqa: PLC0415
    import vip_sim  # noqa: PLC0415

    # 副作用なしの軽量 attribute アクセス(各パッケージの __name__ が
    # ロード時に正しく設定されていることだけ確認、SDD §3.1 の階層構造維持)。
    assert vip_ctrl.__name__ == "vip_ctrl"
    assert vip_sim.__name__ == "vip_sim"
    assert vip_persist.__name__ == "vip_persist"
    assert vip_integrity.__name__ == "vip_integrity"
    assert vip_api.__name__ == "vip_api"
    assert vip_api_b.__name__ == "vip_api_b"
