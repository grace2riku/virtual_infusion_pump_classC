"""Integration test fixtures (ITPR-VIP-001 §6).

Step 19 F0 で骨格化。各観点(F1: RCM-001 / F2: RCM-003 / F3: RCM-004 /
F4: SEP-001 / F5: IT-PERF / F6: IT-PWR / F7: IT-SIDE)で本 conftest を
拡張する想定:

- Step 19 F1+: RCM ごとの結合 fixture(永続化パイプライン全結合 / 制御系
  コア全結合 / API 層 + Validation API 経由など)
- Step 19 F5: pytest-benchmark fixture(SRS-P02/P03/P04 統計時間)
- Step 19 F6: subprocess + SIGKILL ヘルパ(ITPR §6.9 IT-PWR、linux_only)

本 F0 時点ではスモーク試験のみで個別 fixture は未追加。
"""
