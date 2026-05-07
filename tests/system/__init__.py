"""System test package — STPR-VIP-001 §6 (Step 19 H2 で骨格化).

ITPR §6 が「ユニット間結合の契約整合」を主軸とするのに対し、本パッケージは
**SRS 要求の外部観点ベース検証** を主軸とする。試験対象は `pip install` で
導入された VIP-CTRL の CLI `vip-ctrl` 単位 + 永続化レコードを介した system
レベル統合状態。

各試験ファイル全体に `@pytest.mark.system` が付与され、`pyproject.toml`
addopts の `not system` 既定で UT 実行(`unit-test.yml`)から除外される。
`pytest -m system` で明示的に選択可能(本マーカー仕様は ITPR §8.1 + STPR
§4.4 を踏襲)。
"""
