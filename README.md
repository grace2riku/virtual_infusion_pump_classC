# IEC 62304 ドキュメントテンプレート(クラス C)

[![Documentation Checks](https://github.com/grace2riku/iec62304_template/actions/workflows/docs-check.yml/badge.svg)](https://github.com/grace2riku/iec62304_template/actions/workflows/docs-check.yml)

**IEC 62304:2006+A1:2015**(JIS T 2304:2017)で要求される医療機器ソフトウェアライフサイクル成果物の **Markdown テンプレート集** です。安全クラス **C**(死亡又は重傷の可能性)を前提とし、クラス A/B の要求事項も包含しています。

## 想定する使い方

1. 本リポジトリを新規プロジェクト用にクローン or フォーク
2. 各テンプレートの `{{製品名}}` / `{{YYYY-MM-DD}}` などのプレースホルダを自プロジェクトの値で置換
3. Pull Request ベースでドキュメント変更を運用(承認記録・差分レビューが自動的に残る)
4. リリース毎にタグを打ち、各書類のバージョンをベースラインとして凍結

## 収録ドキュメント

### 箇条 5 ソフトウェア開発プロセス

| 箇条 | ドキュメント | ファイル |
|------|-----------|--------|
| 5.1 | ソフトウェア開発計画書 | [`5.1_.../software_development_plan.md`](./5.1_software_development_planning/software_development_plan.md) |
| 5.2 | ソフトウェア要求仕様書 | [`5.2_.../software_requirements_specification.md`](./5.2_software_requirements_analysis/software_requirements_specification.md) |
| 5.3 | ソフトウェアアーキテクチャ設計書 | [`5.3_.../software_architecture_design.md`](./5.3_software_architecture_design/software_architecture_design.md) |
| 5.4 | ソフトウェア詳細設計書 | [`5.4_.../software_detailed_design.md`](./5.4_software_detailed_design/software_detailed_design.md) |
| 5.5 | ユニットテスト計画書/報告書 | [`5.5_.../software_unit_test_plan_report.md`](./5.5_software_unit_implementation/software_unit_test_plan_report.md) |
| 5.6 | 結合試験計画書/報告書 | [`5.6_.../software_integration_test_plan_report.md`](./5.6_software_integration_testing/software_integration_test_plan_report.md) |
| 5.7 | システム試験計画書/報告書 | [`5.7_.../software_system_test_plan_report.md`](./5.7_software_system_testing/software_system_test_plan_report.md) |
| 5.8 | ソフトウェアマスタ仕様書 | [`5.8_.../software_master_specification.md`](./5.8_software_release/software_master_specification.md) |

### 箇条 6〜9 ライフサイクルプロセス

| 箇条 | ドキュメント | ファイル |
|------|-----------|--------|
| 6 保守 | ソフトウェア保守計画書 | [`6_.../software_maintenance_plan.md`](./6_software_maintenance_process/software_maintenance_plan.md) |
| 7 リスク | ソフトウェアリスクマネジメント計画書 | [`7_.../software_risk_management_plan.md`](./7_software_risk_management_process/software_risk_management_plan.md) |
| 7 リスク | ソフトウェア安全クラス決定記録 | [`7_.../software_safety_class_determination_record.md`](./7_software_risk_management_process/software_safety_class_determination_record.md) |
| 7 リスク | リスクマネジメントファイル(ISO 14971) | [`7_.../risk_management_file.md`](./7_software_risk_management_process/risk_management_file.md) |
| 8 構成管理 | ソフトウェア構成管理計画書 | [`8_.../software_configuration_management_plan.md`](./8_software_configuration_management_process/software_configuration_management_plan.md) |
| 8 構成管理 | 構成アイテム一覧 | [`8_.../configuration_item_list.md`](./8_software_configuration_management_process/configuration_item_list.md) |
| 8 構成管理 | CCB 運用規程 | [`8_.../ccb_operating_rules.md`](./8_software_configuration_management_process/ccb_operating_rules.md) |
| 8 構成管理 | 変更要求台帳 | [`8_.../change_request_register.md`](./8_software_configuration_management_process/change_request_register.md) |
| 9 問題解決 | ソフトウェア問題解決手順書 | [`9_.../software_problem_resolution_procedure.md`](./9_software_problem_resolution_process/software_problem_resolution_procedure.md) |

### 補助

| 目的 | ファイル |
|------|--------|
| 条項別 監査チェックリスト | [`compliance/audit_checklist.md`](./compliance/audit_checklist.md) |
| 作業・編集ガイド(AI 支援含む) | [`CLAUDE.md`](./CLAUDE.md) |

## 特徴

- **クラス C 完全対応**: 箇条 5.3.5(分離)、5.4.2〜5.4.4(詳細設計)、5.5.4(追加ユニット受入基準)、5.7.4(試験妥当性確認)を漏れなく収録
- **トレーサビリティ骨格**: `SRS- / ARCH- / SDD- / UNIT- / UT- / IT- / ST- / RCM- / HZ-` など統一 ID 体系と、各書類のトレーサビリティマトリクス
- **箇条 5〜9 まで網羅**: 開発だけでなく保守・リスクマネジメント・構成管理・問題解決プロセスを同一リポジトリで一元管理
- **Git/PR 運用前提**: Markdown ベースで差分レビュー・承認記録・ベースライン凍結が自然に行える
- **監査対応**: 条項番号単位の対応表で、1 行ずつの規格適合性を確認可能

## CI(GitHub Actions)

Pull Request・push ごとに以下を自動検証します(`.github/workflows/docs-check.yml`):

1. 必須ディレクトリ・主要テンプレートファイルの存在確認
2. Markdown lint(`markdownlint-cli2`、日本語・密集テーブル向けに調整済)
3. 内部リンク切れ検出(`lychee`、オフラインモード)
4. 日付書式(ISO 8601 `YYYY-MM-DD` 強制)

ローカルで事前確認したい場合は以下を実行します:

```bash
npx markdownlint-cli2 "**/*.md"
lychee --offline --include-fragments './**/*.md'
```

## 関連規格

| 規格 | 用途 |
|------|------|
| IEC 62304:2006+A1:2015 / JIS T 2304:2017 | 本テンプレートの直接の根拠 |
| ISO 14971:2019 | リスクマネジメント(箇条 7 と RMF で参照) |
| ISO 13485:2016 | 品質マネジメントシステム(保守プロセスで連携) |
| IEC 62366-1 | ユーザビリティエンジニアリング |
| IEC 60601-1-8 | アラームシステム |
| IEC 80001-1 | IT ネットワーク適用のリスクマネジメント |
| IEC 81001-5-1 | ヘルスソフトウェアのセキュリティ |
| AAMI TIR57 | 医療機器セキュリティのリスクマネジメント原則 |

## 免責事項

本テンプレートは **参考実装** であり、各組織・各製品固有の規制要求・品質システム・リスク受容基準に従った調整が必要です。本テンプレートの使用による規制適合を保証するものではありません。実運用前に **規格原本との 1 行ずつの照合**(`compliance/audit_checklist.md` を活用)と、**QMS 責任者・RA 責任者のレビュー** を推奨します。

## 貢献

Issue・Pull Request ともに歓迎します。テンプレート改善の提案時は、可能であれば対応する IEC 62304 条項番号を明記してください。

## ライセンス

{{ライセンス未設定 — プロジェクトに適したライセンスを LICENSE ファイルとして追加してください}}
