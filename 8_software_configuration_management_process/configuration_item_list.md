# 構成アイテム一覧(CI List)

**ドキュメント ID:** CIL-{{製品コード}}-001
**バージョン:** 0.1
**最終更新日:** {{YYYY-MM-DD}}
**対象製品:** {{製品名}} / {{型式}}
**対象リリース:** {{x.y.z}}

| 役割 | 氏名 | 所属 | 日付 | 署名 |
|------|------|------|------|------|
| 管理者 | {{氏名}} | {{部署}} | {{YYYY-MM-DD}} | |
| 承認者 | {{氏名}} | {{部署}} | {{YYYY-MM-DD}} | |

---

## 1. 目的と適用範囲

本書は、IEC 62304 箇条 5.1.10(管理対象となる支援項目)および箇条 8.1(構成識別)に基づき、構成管理対象となるすべての構成アイテム(CI: Configuration Item)を識別・記録する。本書はベースライン毎にスナップショットを取り、アーカイブ(5.8.7)の一部として保管する。

## 2. 記録ルール

- 各 CI には一意の `CI ID` を付与する。
- バージョンは Git タグ又はコミットハッシュで識別する。SOUP 等の外部成果物はベンダ提供バージョン。
- 本一覧は変更のたびに更新し、改訂履歴にベースラインとの関連を記録する。

## 3. ソースコード

| CI ID | 名称 | リポジトリ / パス | 現行バージョン | 安全クラス |
|-------|------|-----------------|-------------|----------|
| CI-SRC-001 | {{アプリケーション層}} | {{URL}} / `src/app` | {{hash/tag}} | C |
| CI-SRC-002 | {{ドライバ層}} | {{URL}} / `src/drv` | {{hash/tag}} | C |

## 4. ドキュメント

| CI ID | ドキュメント | パス | 現行バージョン | 状態 |
|-------|-----------|------|-------------|------|
| CI-DOC-SDP | ソフトウェア開発計画書 | `5.1_software_development_planning/` | {{v}} | 承認済 |
| CI-DOC-SRS | ソフトウェア要求仕様書 | `5.2_software_requirements_analysis/` | {{v}} | 承認済 |
| CI-DOC-SAD | ソフトウェアアーキテクチャ設計書 | `5.3_software_architecture_design/` | {{v}} | 承認済 |
| CI-DOC-SDD | ソフトウェア詳細設計書 | `5.4_software_detailed_design/` | {{v}} | 承認済 |
| CI-DOC-UTPR | ユニットテスト計画書/報告書 | `5.5_software_unit_implementation/` | {{v}} | 承認済 |
| CI-DOC-ITPR | 結合試験計画書/報告書 | `5.6_software_integration_testing/` | {{v}} | 承認済 |
| CI-DOC-STPR | システム試験計画書/報告書 | `5.7_software_system_testing/` | {{v}} | 承認済 |
| CI-DOC-SMS | ソフトウェアマスタ仕様書 | `5.8_software_release/` | {{v}} | 承認済 |
| CI-DOC-SMP | ソフトウェア保守計画書 | `6_software_maintenance_process/` | {{v}} | 承認済 |
| CI-DOC-SRMP | ソフトウェアリスクマネジメント計画書 | `7_software_risk_management_process/` | {{v}} | 承認済 |
| CI-DOC-SSC | ソフトウェア安全クラス決定記録 | `7_software_risk_management_process/` | {{v}} | 承認済 |
| CI-DOC-RMF | リスクマネジメントファイル(ISO 14971) | `7_software_risk_management_process/` | {{v}} | 承認済 |
| CI-DOC-SCMP | ソフトウェア構成管理計画書 | `8_software_configuration_management_process/` | {{v}} | 承認済 |
| CI-DOC-CCB | CCB 運用規程 | `8_software_configuration_management_process/` | {{v}} | 承認済 |
| CI-DOC-CRR | 変更要求台帳 | `8_software_configuration_management_process/` | {{v}} | 承認済 |
| CI-DOC-SPRP | ソフトウェア問題解決手順書 | `9_software_problem_resolution_process/` | {{v}} | 承認済 |
| CI-DOC-ACL | IEC 62304 監査チェックリスト | `compliance/` | {{v}} | 承認済 |

## 5. SOUP(Software of Unknown Provenance)

| CI ID | 名称 | 供給元 | バージョン | ライセンス | 入手日 | SHA-256 |
|-------|------|-------|----------|----------|-------|---------|
| CI-SOUP-001 | {{OS/RTOS 等}} | {{}} | {{}} | {{}} | {{YYYY-MM-DD}} | {{}} |
| CI-SOUP-002 | {{ライブラリ}} | {{}} | {{}} | {{}} | {{YYYY-MM-DD}} | {{}} |

## 6. 開発・検証ツール

| CI ID | 種別 | ツール名 | バージョン | 役割 | 校正/資格認定 |
|-------|------|--------|----------|------|------------|
| CI-TOOL-001 | コンパイラ | {{}} | {{}} | ビルド | {{ツール認定記録 ID}} |
| CI-TOOL-002 | 静的解析 | {{}} | {{}} | ユニット受入 | |
| CI-TOOL-003 | 試験フレームワーク | {{}} | {{}} | ユニット試験 | |
| CI-TOOL-004 | カバレッジ計測 | {{}} | {{}} | カバレッジ取得 | |
| CI-TOOL-005 | 課題追跡 | {{}} | {{}} | CR・問題管理 | — |
| CI-TOOL-006 | バージョン管理 | Git | {{}} | 構成管理 | — |
| CI-TOOL-007 | CI/CD | {{}} | {{}} | 自動ビルド・試験 | — |

## 7. 試験データ・試験資産

| CI ID | 名称 | パス | 現行バージョン |
|-------|------|------|-------------|
| CI-TD-001 | ユニット試験データ | `test/unit/data` | {{hash}} |
| CI-TD-002 | 結合試験シナリオ | `test/integration` | {{hash}} |
| CI-TD-003 | システム試験シナリオ | `test/system` | {{hash}} |

## 8. 成果バイナリ・配布物

| CI ID | 名称 | 形式 | SHA-256 | 保管場所 |
|-------|------|------|---------|--------|
| CI-BIN-001 | {{firmware.bin}} | バイナリ | {{}} | {{}} |
| CI-BIN-002 | {{installer.pkg}} | インストーラ | {{}} | {{}} |

## 9. ベースライン履歴

| ベースライン ID | 日付 | 目的 | 承認者 | 関連 CR |
|--------------|------|------|-------|---------|
| BL-{{YYYYMMDD-001}} | {{YYYY-MM-DD}} | 要求凍結 | | — |
| BL-{{YYYYMMDD-002}} | {{YYYY-MM-DD}} | 設計凍結 | | |
| BL-{{YYYYMMDD-003}} | {{YYYY-MM-DD}} | リリース `v{{x.y.z}}` | | |

## 10. 改訂履歴

| バージョン | 日付 | 変更内容 | 変更者 |
|----------|------|---------|--------|
| 0.1 | {{YYYY-MM-DD}} | 初版作成 | {{氏名}} |
