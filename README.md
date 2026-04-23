# 仮想輸液ポンプ(Virtual Infusion Pump) — IEC 62304 クラス C 準拠ドキュメント作成プロジェクト

**本リポジトリは、IEC 62304:2006+A1:2015(JIS T 2304:2017)に基づく医療機器ソフトウェア開発プロセスの学習・参考実装を目的とした仮想プロジェクトです。**

実機・ハードウェアは存在せず、PC 単体で動作する仮想シミュレータ(ハードウェアモデル含む)を対象として、ソフトウェア安全クラス **C**(死亡又は重傷の可能性)の要求事項に則ったライフサイクル成果物を作成します。

## 目的

- IEC 62304 の開発プロセス(箇条 5)、保守(箇条 6)、リスクマネジメント(箇条 7)、構成管理(箇条 8)、問題解決(箇条 9)の各プロセスを、実プロジェクトと同等の粒度で体験・文書化する。
- 輸液ポンプという公知のハザード例が豊富な題材を用い、クラス C 特有の要求事項(箇条 5.3.5 / 5.4.2〜5.4.4 / 5.5.4 / 5.7.4)の実装を学ぶ。
- Markdown + Git + Pull Request ベースのドキュメント運用を実践する。

## 対象製品の概要

| 項目 | 内容 |
|------|------|
| 製品名 | 仮想輸液ポンプ(Virtual Infusion Pump) |
| 型式 | VIP-SIM-001 |
| ソフトウェア名称 | Virtual Infusion Pump Control Software(VIP-CTRL) |
| ソフトウェア安全クラス | **C**(IEC 62304) |
| 実装言語 | Python 3.12(PC 単独動作の仮想シミュレータ) |
| ライフサイクルモデル | V字モデル(インクリメンタル方式) |
| 開発インクリメント | Inc.1 流量制御コア → Inc.2 アラーム管理 → Inc.3 用量計算/ボーラス → Inc.4 ロギング/UI |

## ベース

本プロジェクトは [grace2riku/iec62304_template](https://github.com/grace2riku/iec62304_template) をベースとし、同テンプレートの構造・雛形を継承しています。テンプレート本体の更新は `upstream` remote から随時確認可能です。

## ドキュメント進捗

### 箇条 5 ソフトウェア開発プロセス

| 箇条 | ドキュメント | ファイル | 状態 |
|------|-----------|--------|------|
| 5.1 | ソフトウェア開発計画書(SDP) | [`5.1_.../software_development_plan.md`](./5.1_software_development_planning/software_development_plan.md) | ✅ v0.1 |
| 5.2 | ソフトウェア要求仕様書(SRS) | [`5.2_.../software_requirements_specification.md`](./5.2_software_requirements_analysis/software_requirements_specification.md) | 🟡 v0.1(Inc.1 範囲確定、Inc.2〜4 は今後追補) |
| 5.3 | ソフトウェアアーキテクチャ設計書 | [`5.3_.../software_architecture_design.md`](./5.3_software_architecture_design/software_architecture_design.md) | 🟡 v0.1(Inc.1 範囲確定、Inc.2〜4 は今後追補) |
| 5.4 | ソフトウェア詳細設計書 | [`5.4_.../software_detailed_design.md`](./5.4_software_detailed_design/software_detailed_design.md) | 🟡 v0.1(代表 5 ユニット詳細、SDD v0.2 で残 9 追補予定) |
| 5.5 | ユニット試験計画書/報告書 | [`5.5_.../software_unit_test_plan_report.md`](./5.5_software_unit_implementation/software_unit_test_plan_report.md) | ⬜ 未着手 |
| 5.6 | 結合試験計画書/報告書 | [`5.6_.../software_integration_test_plan_report.md`](./5.6_software_integration_testing/software_integration_test_plan_report.md) | ⬜ 未着手 |
| 5.7 | システム試験計画書/報告書 | [`5.7_.../software_system_test_plan_report.md`](./5.7_software_system_testing/software_system_test_plan_report.md) | ⬜ 未着手 |
| 5.8 | ソフトウェアマスタ仕様書 | [`5.8_.../software_master_specification.md`](./5.8_software_release/software_master_specification.md) | ⬜ 未着手 |

### 箇条 6〜9 ライフサイクルプロセス

| 箇条 | ドキュメント | ファイル | 状態 |
|------|-----------|--------|------|
| 6 保守 | ソフトウェア保守計画書(SMP) | [`6_.../software_maintenance_plan.md`](./6_software_maintenance_process/software_maintenance_plan.md) | ✅ v0.1 |
| 7 リスク | ソフトウェアリスクマネジメント計画書(SRMP) | [`7_.../software_risk_management_plan.md`](./7_software_risk_management_process/software_risk_management_plan.md) | ✅ v0.1 |
| 7 リスク | ソフトウェア安全クラス決定記録(SSC) | [`7_.../software_safety_class_determination_record.md`](./7_software_risk_management_process/software_safety_class_determination_record.md) | ✅ v0.1 |
| 7 リスク | リスクマネジメントファイル(RMF, ISO 14971) | [`7_.../risk_management_file.md`](./7_software_risk_management_process/risk_management_file.md) | ✅ v0.1 |
| 8 構成管理 | ソフトウェア構成管理計画書(SCMP) | [`8_.../software_configuration_management_plan.md`](./8_software_configuration_management_process/software_configuration_management_plan.md) | ✅ v0.2 |
| 8 構成管理 | 構成アイテム一覧(CIL) | [`8_.../configuration_item_list.md`](./8_software_configuration_management_process/configuration_item_list.md) | ✅ v0.1 |
| 8 構成管理 | CCB 運用規程 | [`8_.../ccb_operating_rules.md`](./8_software_configuration_management_process/ccb_operating_rules.md) | ✅ v0.1 |
| 8 構成管理 | 変更要求台帳 | [`8_.../change_request_register.md`](./8_software_configuration_management_process/change_request_register.md) | ✅ v0.1(空台帳) |
| 9 問題解決 | ソフトウェア問題解決手順書(SPRP) | [`9_.../software_problem_resolution_procedure.md`](./9_software_problem_resolution_process/software_problem_resolution_procedure.md) | ✅ v0.1 |

### 補助

| 目的 | ファイル |
|------|--------|
| **開発ステップ記録(お手本用)** | [`DEVELOPMENT_STEPS.md`](./DEVELOPMENT_STEPS.md) |
| 条項別 監査チェックリスト | [`compliance/audit_checklist.md`](./compliance/audit_checklist.md) |
| 作業・編集ガイド(AI 支援含む) | [`CLAUDE.md`](./CLAUDE.md) |

## 技術スタック(予定)

| カテゴリ | ツール |
|---------|-------|
| 言語 | Python 3.12 |
| パッケージ管理 | uv / pip + venv |
| 静的解析 | ruff / pylint / mypy(strict)/ bandit |
| 試験 | pytest / pytest-cov / hypothesis |
| 構成管理 | Git / GitHub |
| CI | GitHub Actions |
| ドキュメント検証 | markdownlint-cli2 / lychee |

詳細は SDP §6.2 および 構成アイテム一覧(CIL)を参照。

## 開発プロセスの方針

- **V字モデル(インクリメンタル方式)** を採用し、機能単位で V字サイクルを一周する。
- **テスト駆動開発(TDD)** を原則とし、型ヒント + 静的解析 + 徹底したユニット試験で品質を担保する。
- **Pull Request + GitHub Actions CI** による自動検証で、単独開発下でも機械的独立性を確保する。
- ベースラインは Inc. 完了時およびリリース時にタグで凍結する。

詳細は [SDP(SDP-VIP-001)](./5.1_software_development_planning/software_development_plan.md) を参照。

## CI(GitHub Actions)

Pull Request・push ごとに以下を自動検証します(`.github/workflows/docs-check.yml`):

1. 必須ディレクトリ・主要テンプレートファイルの存在確認
2. Markdown lint(`markdownlint-cli2`、日本語・密集テーブル向けに調整済)
3. 内部リンク切れ検出(`lychee`、オフラインモード)
4. 日付書式(ISO 8601 `YYYY-MM-DD` 強制)

ローカルで事前確認する場合:

```bash
npx markdownlint-cli2 "**/*.md"
lychee --offline --include-fragments './**/*.md'
```

コード用の CI(`.github/workflows/unit-test.yml`)を Step 19 B1(2026-04-23)で追加しました。`ruff check --select ALL` / `ruff format --check` / `mypy --strict` / `bandit` / `pytest`(カバレッジ付き)/ `pip-audit` を実行します。

## 開発環境セットアップ(Step 19 B1 以降)

本プロジェクトは Python 3.12 を使用します。以下の手順で開発環境を整えてください。

```bash
# venv 作成と依存関係のインストール(editable)
python3.12 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e ".[dev]"
```

### 日常の検証コマンド

CI と同じチェックをローカルで実行できます:

```bash
ruff check .              # lint(--select ALL、UTPR §3.1 / SDP §実装ルール)
ruff format --check .     # フォーマット確認(差分があれば `ruff format .` で適用)
mypy src tests            # 静的型検査(--strict)
bandit -ll -r src         # セキュリティ静的解析(本番コードのみ)
pytest --cov              # ユニット試験 + カバレッジ
pip-audit --strict \
  -r <(pip freeze --exclude-editable)  # 依存脆弱性監査(editable 自身は除外)
```

Inc.1 のユニット試験計画は [`5.5_software_unit_implementation/software_unit_test_plan_report.md`](5.5_software_unit_implementation/software_unit_test_plan_report.md)(UTPR-VIP-001 v0.1)を参照してください。TDD(Red-Green-Refactor)で進めます。

## 関連規格

| 規格 | 用途 |
|------|------|
| IEC 62304:2006+A1:2015 / JIS T 2304:2017 | 本プロジェクトの直接の根拠 |
| ISO 14971:2019 | リスクマネジメント(箇条 7、RMF で参照) |
| ISO 13485:2016 | 品質マネジメントシステム(保守プロセスで連携) |
| IEC 60601-2-24 | 輸液ポンプの安全性・基本性能に関する個別要求事項 |
| IEC 62366-1 | ユーザビリティエンジニアリング |
| IEC 60601-1-8 | アラームシステム |
| AAMI TIR45:2012 | アジャイル/インクリメンタル開発の医療機器ソフトウェアへの適用 |
| AAMI TIR57:2016 | 医療機器セキュリティのリスクマネジメント原則 |

## 免責事項

- 本プロジェクトは **学習目的の仮想プロジェクト** であり、実在の医療機器ではありません。
- 本リポジトリの成果物は、特定製品の規制適合を保証するものではなく、実運用前に各組織の品質マネジメントシステム・リスク受容基準・規制要求に従った調整と、QMS/RA 責任者の正式レビューが必要です。
- 医療的判断・薬剤投与に本ソフトウェアを使用しないでください。

## ライセンス

未設定(今後決定予定)。

## 参考: 元テンプレートの README

本プロジェクトのベースとなっているテンプレートの詳細は [grace2riku/iec62304_template](https://github.com/grace2riku/iec62304_template) を参照してください。
