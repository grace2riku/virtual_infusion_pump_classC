# 構成アイテム一覧(CI List)

**ドキュメント ID:** CIL-VIP-001
**バージョン:** 0.4
**最終更新日:** 2026-04-21
**対象製品:** 仮想輸液ポンプ(Virtual Infusion Pump) / VIP-SIM-001
**対象リリース:** 0.1.0(初期開発)以降

| 役割 | 氏名 | 所属 | 日付 | 署名 |
|------|------|------|------|------|
| 管理者 | k-abe | — | 2026-04-18 | |
| 承認者 | — | — | — | |

> **本プロジェクトの位置づけ(注記)**
> 本ドキュメントは IEC 62304 に基づく医療機器ソフトウェア開発プロセスの学習・参考実装を目的とした **仮想プロジェクト** の成果物である。本 CIL は Phase 3(M0 基盤整備期)時点の構成アイテムを網羅し、以降インクリメント進行に応じて追加更新する。

---

## 1. 目的と適用範囲

本書は、IEC 62304 箇条 5.1.10(管理対象となる支援項目)および箇条 8.1(構成識別)に基づき、構成管理対象となるすべての構成アイテム(CI)を識別・記録する。本書はベースライン毎にスナップショットを取り、アーカイブの一部として保管する(SCMP-VIP-001 §5 参照)。

## 2. 記録ルール

- 各 CI には一意の `CI ID` を付与する。種別プレフィクス + 連番または略称:
  - `CI-SRC-NNN` — ソースコード
  - `CI-DOC-XXX` — ドキュメント(XXX は略称、例: SDP、SRS)
  - `CI-SOUP-NNN` — SOUP(外部ライブラリ、ランタイム等)
  - `CI-TOOL-NNN` — 開発・検証ツール
  - `CI-TD-NNN` — 試験データ
  - `CI-BIN-NNN` — 成果バイナリ・配布物
  - `CI-CFG-NNN` — 構成定義ファイル(lint 設定、CI 設定等)
- バージョンは Git タグ又はコミットハッシュで識別。SOUP 等の外部成果物はベンダ提供バージョン + SHA-256。
- 本一覧は変更のたびに更新し、改訂履歴にベースラインとの関連を記録する。
- SOUP のバージョン固定は `pyproject.toml` + `uv.lock`(または `requirements.txt` with hashes)で実施する。

## 3. ソースコード

> **現時点(Phase 3 終了時)、実装ソースコードは存在しない。** Inc.1 着手時(Step 11 以降)に追加する。

| CI ID | 名称 | リポジトリ / パス | 現行バージョン | 安全クラス | 備考 |
|-------|------|-----------------|-------------|----------|------|
| (予定) CI-SRC-001 | 流量制御コア | `src/vip_ctrl/flow_control/` | — | C | Inc.1 で作成予定 |
| (予定) CI-SRC-002 | アラーム管理 | `src/vip_ctrl/alarm/` | — | C | Inc.2 で作成予定 |
| (予定) CI-SRC-003 | 用量計算・ボーラス | `src/vip_ctrl/dosage/` | — | C | Inc.3 で作成予定 |
| (予定) CI-SRC-004 | ロギング・UI | `src/vip_ctrl/ui/`、`src/vip_ctrl/logging/` | — | B/C(分離検討) | Inc.4 で作成予定 |
| (予定) CI-SRC-005 | 仮想ハードウェアモデル | `src/vip_ctrl/virtual_hw/` | — | C | Inc.1 で作成予定 |

## 4. ドキュメント

Phase 3(M0 基盤整備期)終了 + Inc.1 設計凍結時点。バージョンは 2026-04-21 時点。

| CI ID | ドキュメント | パス | 現行バージョン | 状態 |
|-------|-----------|------|-------------|------|
| CI-DOC-SDP | ソフトウェア開発計画書 | `5.1_software_development_planning/software_development_plan.md` | 0.1 | ドラフト(セルフ承認) |
| CI-DOC-SRS | ソフトウェア要求仕様書 | `5.2_software_requirements_analysis/software_requirements_specification.md` | 0.1 | ドラフト(セルフ承認、Inc.1 範囲確定、Step 15a で §10 CCB §5.4 参照整合バージョン据置。Inc.2〜4 は追補予定) |
| CI-DOC-SAD | ソフトウェアアーキテクチャ設計書 | `5.3_software_architecture_design/software_architecture_design.md` | 0.1 | ドラフト(セルフ承認、Inc.1 範囲確定、Step 12c 反映、Step 15a で §8 CCB §5.4 参照整合バージョン据置) |
| CI-DOC-SDD | ソフトウェア詳細設計書 | `5.4_software_detailed_design/software_detailed_design.md` | 0.2 | ドラフト(セルフ承認、Inc.1 全 17 ユニット §5.4.2 完全充足、CR-0001 反映) |
| CI-DOC-UTPR | ユニットテスト計画書/報告書 | `5.5_software_unit_implementation/software_unit_test_plan_report.md` | 0.1 | ドラフト(セルフ承認、Step 19 A:Inc.1 全 17 ユニットの UT-UID 採番、代表 5 ユニット詳細記述、第 II 部報告は Step 19 B 以降で埋める) |
| CI-DOC-ITPR | 結合試験計画書/報告書 | `5.6_software_integration_testing/software_integration_test_plan_report.md` | — | 未着手(Inc.1 予定) |
| CI-DOC-STPR | システム試験計画書/報告書 | `5.7_software_system_testing/software_system_test_plan_report.md` | — | 未着手(Inc.1 予定) |
| CI-DOC-SMS | ソフトウェアマスタ仕様書 | `5.8_software_release/software_master_specification.md` | — | 未着手(M_final 予定) |
| CI-DOC-SMP | ソフトウェア保守計画書 | `6_software_maintenance_process/software_maintenance_plan.md` | 0.2 | ドラフト(セルフ承認、Step 15a で §4.6 変更区分表 1 分インターバル反映) |
| CI-DOC-SRMP | ソフトウェアリスクマネジメント計画書 | `7_software_risk_management_process/software_risk_management_plan.md` | 0.2 | ドラフト(セルフ承認、Step 15a で §3.2 独立性担保の時間間隔を 1 分に具体化) |
| CI-DOC-SSC | ソフトウェア安全クラス決定記録 | `7_software_risk_management_process/software_safety_class_determination_record.md` | 0.1 | ドラフト(セルフ承認) |
| CI-DOC-RMF | リスクマネジメントファイル(ISO 14971) | `7_software_risk_management_process/risk_management_file.md` | 0.2 | ドラフト(セルフ承認、継続更新。RCM-019 登録済) |
| CI-DOC-SCMP | ソフトウェア構成管理計画書 | `8_software_configuration_management_process/software_configuration_management_plan.md` | 0.3 | ドラフト(セルフ承認、Step 15a で §4.1 表・§4.1.1 手順 2 の 1 分インターバル反映) |
| CI-DOC-CIL | 構成アイテム一覧(本書) | `8_software_configuration_management_process/configuration_item_list.md` | 0.7 | ドラフト(セルフ承認、Step 19 A 反映:UTPR-VIP-001 v0.1 新規作成に連動、CI-DOC-UTPR を「未着手」→ v0.1 に昇格、自己参照 v0.7) |
| CI-DOC-CCB | CCB 運用規程 | `8_software_configuration_management_process/ccb_operating_rules.md` | 0.2 | ドラフト(セルフ承認、Step 15a で §5.4 大改訂 — 学習/実機 2 系統表記・1 分インターバル採用) |
| CI-DOC-CRR | 変更要求台帳 | `8_software_configuration_management_process/change_request_register.md` | 0.5 | ドラフト(セルフ承認、Step 15b 後段で CR-0002 CLOSED 記録反映 — 実装 PR #6、マージ 2026-04-22T23:46:05Z、SHA a741cda、インターバル実績 約 47h 14m) |
| CI-DOC-SPRP | ソフトウェア問題解決手順書 | `9_software_problem_resolution_process/software_problem_resolution_procedure.md` | 0.2 | ドラフト(セルフ承認、Step 15a で §5 CCB 通知行の 1 分インターバル反映) |
| CI-DOC-ACL | IEC 62304 監査チェックリスト | `compliance/audit_checklist.md` | テンプレートのまま | 未編集(Inc.1 以降で本プロジェクト向けに整備予定) |
| CI-DOC-README | プロジェクト README | `README.md` | — | 継続更新 |
| CI-DOC-DEVSTEPS | 開発ステップ記録(お手本) | `DEVELOPMENT_STEPS.md` | 0.9 | 継続更新(ステップ毎に追記、Step 19 A 反映:UTPR-VIP-001 v0.1 新規作成の記録) |
| CI-DOC-CLAUDE | 編集ガイド(AI 支援含む) | `CLAUDE.md` | — | 本プロジェクト固有ルール追記済、Step 15a で単独開発下の独立性擬制セクションを 24h → 1 分に更新 |
| CI-DOC-UPSTREAM | iec62304_template への修正要望台帳 | `UPSTREAM_FEEDBACK.md` | 0.3 | ドラフト(セルフ承認、UF-001〜UF-009 全 9 件 upstream 受領済み反映 — PR #15〜#23 マージ、2026-04-21。※v0.2 時点 Step 17a で本 CIL 反映漏れを Step 17b で遡及補正) |

## 5. SOUP(Software of Unknown Provenance)

> **現時点で採用済みの SOUP はない。** 本プロジェクトはまだ Python ソースコードを含まず、実行時依存がない。将来採用予定の SOUP を **候補** として以下に記録する。採用時に本表を正式登録に昇格する。

| CI ID(予定) | 名称 | 供給元 | 予定バージョン | ライセンス | 予定用途 | 関連ハザード |
|-----------|------|-------|-------------|----------|---------|------------|
| CI-SOUP-001 | CPython ランタイム | Python Software Foundation | 3.12.x | PSF | 実行環境 | 全般 |
| CI-SOUP-002 | pytest | pytest-dev | 最新安定版 | MIT | ユニット試験実行 | — |
| CI-SOUP-003 | pytest-cov | pytest-dev | 最新安定版 | MIT | 網羅率計測 | — |
| CI-SOUP-004 | hypothesis | HypothesisWorks | 最新安定版 | MPL-2.0 | プロパティベース試験 | HZ-006(計算誤り検出) |
| CI-SOUP-005 | ruff | Astral | 最新安定版 | MIT | lint / 整形 | — |
| CI-SOUP-006 | pylint | Pylint | 最新安定版 | GPL-2.0 | 追加 lint | — |
| CI-SOUP-007 | mypy | Python | 最新安定版 | MIT | 静的型検査(strict) | HZ-003、HZ-006 |
| CI-SOUP-008 | bandit | PyCQA | 最新安定版 | Apache-2.0 | セキュリティ lint | — |
| CI-SOUP-009 | pydantic | Pydantic | 最新安定版 | MIT | 実行時型検証 | HZ-003、HZ-008 |
| CI-SOUP-010 | pip-audit | PyPA | 最新安定版 | Apache-2.0 | SOUP 脆弱性スキャン | — |

採用決定・バージョン固定・SHA-256 記録は Inc.1 実装開始時(Step 11 以降)に実施する。その際 SRMP §4.3 の SOUP 評価を各 SOUP に対して完了させる。

## 6. 開発・検証ツール

現時点で運用中のツール。

| CI ID | 種別 | ツール名 | バージョン | 役割 | 校正/資格認定 |
|-------|------|--------|----------|------|------------|
| CI-TOOL-001 | バージョン管理 | Git | 2.40+(ローカル) | 構成管理 | — |
| CI-TOOL-002 | ホスティング | GitHub | — | リモートリポジトリ、CI、Issue、PR | — |
| CI-TOOL-003 | CLI | gh(GitHub CLI) | 最新 | GitHub API 操作、リポジトリ作成、run 確認等 | — |
| CI-TOOL-004 | CI/CD | GitHub Actions | — | 自動 lint・ドキュメント検証 | — |
| CI-TOOL-005 | ドキュメント lint | markdownlint-cli2 | 0.13.0(CI 側固定) | Markdown 書式検査 | — |
| CI-TOOL-006 | リンクチェック | lychee | CI 側最新 | 内部リンク切れ検出 | — |
| CI-TOOL-007 | 課題追跡 | GitHub Issues | — | CR / PRB 管理 | — |
| (予定) CI-TOOL-008 | Python ランタイム | CPython | 3.12.x | 実行環境(兼 SOUP-001) | — |
| (予定) CI-TOOL-009 | パッケージ管理 | uv または pip+venv | 最新 | 依存管理 | — |
| (予定) CI-TOOL-010 | 静的解析スイート | ruff / pylint / mypy / bandit | 最新 | 品質・型・セキュリティ検査 | — |
| (予定) CI-TOOL-011 | 試験フレームワーク | pytest / pytest-cov / hypothesis | 最新 | ユニット試験、網羅率、プロパティ試験 | — |
| (予定) CI-TOOL-012 | 脆弱性スキャン | pip-audit | 最新 | SOUP 脆弱性検出(CI 組込予定) | — |

## 7. 構成定義ファイル(CFG)

| CI ID | 名称 | パス | 用途 |
|-------|------|------|------|
| CI-CFG-001 | markdownlint 設定 | `.markdownlint-cli2.yaml` | Markdown lint ルール定義(MD013/MD033/MD024 等の緩和) |
| CI-CFG-002 | lychee 設定 | `lychee.toml` | リンクチェック設定 |
| CI-CFG-003 | GitHub Actions ワークフロー | `.github/workflows/docs-check.yml` | ドキュメント系 CI 定義 |
| CI-CFG-004 | Issue テンプレート(PRB) | `.github/ISSUE_TEMPLATE/problem_report.md` | 問題報告起票用 |
| CI-CFG-005 | Issue テンプレート(CR) | `.github/ISSUE_TEMPLATE/change_request.md` | 変更要求起票用 |
| CI-CFG-006 | Issue テンプレート config | `.github/ISSUE_TEMPLATE/config.yml` | contact_links、blank issue 制御 |
| CI-CFG-007 | PR テンプレート | `.github/pull_request_template.md` | PR 作成時の必須情報収集 |
| CI-CFG-008 | .gitignore | `.gitignore` | Git 対象外ファイルの定義 |
| (予定) CI-CFG-009 | Python プロジェクト設定 | `pyproject.toml` | 依存・ツール設定(Inc.1 で追加) |
| (予定) CI-CFG-010 | 依存ロックファイル | `uv.lock` または `requirements.txt` | 依存バージョン固定(Inc.1 で追加) |
| (予定) CI-CFG-011 | コード CI ワークフロー | `.github/workflows/code-check.yml` | ruff/mypy/pytest/pip-audit 実行(Inc.1 で追加) |

## 8. 試験データ・試験資産

> **現時点で試験データは存在しない。** Inc.1 のユニット試験着手時に追加する。

| CI ID(予定) | 名称 | パス | 用途 |
|-----------|------|------|------|
| CI-TD-001 | ユニット試験ケース | `tests/unit/` | pytest ユニット試験 |
| CI-TD-002 | 結合試験シナリオ | `tests/integration/` | 故障注入シナリオ含む結合試験 |
| CI-TD-003 | システム試験シナリオ | `tests/system/` | 要求ベースのシステム試験 |
| CI-TD-004 | プロパティベース試験仕様 | `tests/properties/` | hypothesis 用プロパティ定義 |
| CI-TD-005 | 試験入力データ | `tests/data/` | YAML/JSON 形式の試験データ |

## 9. 成果バイナリ・配布物

> **現時点で成果バイナリは存在しない。** リリース時に GitHub Releases 経由で配布する。

| CI ID(予定) | 名称 | 形式 | SHA-256 | 保管場所 |
|-----------|------|------|---------|--------|
| CI-BIN-001 | vip_ctrl wheel パッケージ | Python wheel | — | GitHub Releases |
| CI-BIN-002 | vip_ctrl sdist | ソース配布 | — | GitHub Releases |
| CI-BIN-003 | システム試験記録アーカイブ | tar.gz | — | GitHub Releases |

## 10. ベースライン履歴

ベースライン凍結時に本表に追記する。各ベースラインは Git タグで永続化される(SCMP §5 参照)。

| ベースライン ID | Git タグ | 日付 | 目的 | 承認者 | 含まれる主要 CI | 関連 CR |
|---------------|---------|------|------|-------|--------------|---------|
| BL-20260418-001 | `planning-baseline` | 2026-04-18 | 計画凍結(M0 基盤整備期完了) | k-abe(セルフ) | CI-DOC-{SDP, SMP, SRMP, SSC, RMF v0.1, SCMP, SPRP, CIL v0.1, CCB, CRR}、CI-CFG-{001〜008}、CI-DOC-{README, DEVSTEPS, CLAUDE} | — |
| BL-20260418-002 | `inc1-requirements-frozen` | 2026-04-18 | Inc.1 要求凍結(SRS v0.1 + RMF v0.2 + CIL v0.2 同期完了) | k-abe(セルフ) | 上記 + CI-DOC-SRS(v0.1、Inc.1 範囲確定)、RMF v0.2、CIL v0.2 | — |
| BL-20260421-001 | `inc1-design-frozen` | 2026-04-21 | Inc.1 設計凍結(SDD v0.2 完成、Inc.1 実装着手準備完了) | k-abe(セルフ) | 上記 + CI-DOC-{SAD v0.1, SDD v0.2, CRR v0.3, CIL v0.3, DEVSTEPS v0.3, CCB v0.1} | CR-0001(Issue #1、PR #2、マージ SHA 77fd145) |
| (予定) BL-YYYYMMDD-NNN | `inc1-baseline` | — | Inc.1 完了(試験合格) | — | + CI-SRC-{001, 005}、CI-TD-* | — |
| (予定) BL-YYYYMMDD-NNN | `v1.0.0` | — | 初回リリース | — | 全 CI | — |

> `planning-baseline` タグ付与済(2026-04-18、commit ベース)。`inc1-requirements-frozen` タグ付与済(2026-04-18、BL-20260418-002)。`inc1-design-frozen` タグは本 CIL v0.3 + DEVSTEPS v0.3 の統合コミット直後に付与予定(BL-20260421-001、Step 14d/14e)。

## 11. 改訂履歴

| バージョン | 日付 | 変更内容 | 変更者 |
|----------|------|---------|--------|
| 0.1 | 2026-04-18 | 初版作成(Phase 3 時点の CI を網羅登録 — ドキュメント 18 件、ツール 7 件(運用中)+ 5 件(予定)、構成ファイル 8 件(運用中)+ 3 件(予定)、SOUP 候補 10 件、ベースライン候補 5 件) | k-abe |
| 0.2 | 2026-04-18 | Step 11/12a の成果物を反映: CI-DOC-SRS を v0.1(Inc.1 範囲確定)へ昇格、CI-DOC-RMF を v0.2(RCM-019 登録)へ昇格、ベースライン履歴を更新し `planning-baseline` の付与済状態と `inc1-requirements-frozen` の実付与予定を反映 | k-abe |
| 0.3 | 2026-04-21 | Step 14d(Inc.1 設計凍結)に伴う整合化: (1) CR-0001 マージ完了反映 — CI-DOC-SDD を v0.2(§5.4.2 完全充足)へ昇格、CI-DOC-CRR を v0.3(クローズ記録反映)へ昇格。(2) v0.2 時点の更新漏れ補正 — CI-DOC-SAD を v0.1(Step 12c 反映)、CI-DOC-CCB を v0.1(Step 10c 反映)、CI-DOC-CIL 自己参照を v0.3、CI-DOC-DEVSTEPS を v0.3(Step 14b〜14e 追記反映)へ更新。(3) ベースライン履歴に BL-20260421-001 `inc1-design-frozen` を確定エントリとして記入、§10 末尾の注記も更新 | k-abe |
| 0.4 | 2026-04-21 | Step 16(運用改善)に伴う整合化:`UPSTREAM_FEEDBACK.md`(iec62304_template への修正要望台帳)を新規作成し、`CI-DOC-UPSTREAM` v0.1 として §4 ドキュメント一覧に登録(UF-001〜UF-009 の 9 件初期エントリ)。併せて `.gitignore` に `.claude/settings.local.json` の除外を追記(CI-CFG-008 の内容更新、CI 登録は既存のまま)。CI-DOC-CIL 自己参照を v0.4 に更新 | k-abe |
| 0.5 | 2026-04-21 | Step 17b(upstream 9 件受領確認)に伴う整合化:UF-001〜UF-009 全 9 件が upstream リポジトリ `grace2riku/iec62304_template` で PR #15〜#23 として受領・マージされたことを確認、UPSTREAM_FEEDBACK.md を v0.3(状態「受領済み」昇格)に更新したことを受け、`CI-DOC-UPSTREAM` を v0.1 → **v0.3** に一気に昇格(v0.2 時点で Step 17a の CIL 反映漏れが発生していたため遡及補正、Step 14d 教訓「CIL の派生ドキュメント更新漏れ」の再発事例として記録)。`CI-DOC-DEVSTEPS` を v0.3 → v0.6 に更新(Step 17b 追記反映)、CI-DOC-CIL 自己参照を v0.5 に更新 | k-abe |
| 0.6 | 2026-04-22 | Step 15b 後段(CR-0002 マージ後アクション)に伴う整合化:CR-0002 本体 PR #6(マージ 2026-04-22T23:46:05Z、SHA a741cda)でプロセス規程 11 文書が改訂されたことを §4 ドキュメント一覧に反映。**(1) 昇格:** `CI-DOC-CCB` v0.1 → v0.2(§5.4 大改訂、学習/実機 2 系統表記)、`CI-DOC-SCMP` v0.2 → v0.3(§4.1 表・手順 2 の 1 分反映)、`CI-DOC-SRMP` v0.1 → v0.2(§3.2 独立性担保の時間間隔を 1 分に具体化)、`CI-DOC-SPRP` v0.1 → v0.2(§5 CCB 通知行の 1 分反映)、`CI-DOC-SMP` v0.1 → v0.2(§4.6 変更区分表の 1 分反映)、`CI-DOC-CRR` v0.3 → v0.5(CR-0002 TRIAGED 追加+CLOSED 記録を Step 15b 後段で一括反映)。**(2) 据置(凍結整合):** `CI-DOC-SRS` v0.1・`CI-DOC-SAD` v0.1 は `inc1-requirements-frozen` / `inc1-design-frozen` ベースライン整合保持のため据置、参照整合の状態注記のみ更新。**(3) CLAUDE 更新注記:** 独立性擬制セクションの 1 分化を注記欄に反映。**(4) DEVSTEPS:** v0.6 → v0.8 に更新(Step 15b 本体マージ解消 v0.7 + 本 Step 15b 後段 v0.8)。**(5) CI-DOC-CIL 自己参照:** v0.5 → v0.6 に更新。Step 14d 教訓「CIL の派生ドキュメント更新漏れ」の二度目再発(Step 17b で既に一度再発)を防ぐため、本 Step 15b 後段は CR-0002 対象の全 11 文書の反映を網羅的にレビュー | k-abe |
| 0.7 | 2026-04-23 | Step 19 A(Inc.1 UTPR v0.1 新規作成)に伴う整合化:`CI-DOC-UTPR` を「未着手」→ v0.1 に昇格(Inc.1 全 17 ユニットに UT-UID 採番、代表 5 ユニット詳細記述、第 II 部報告は Step 19 B 以降)。CI-DOC-DEVSTEPS を v0.8 → v0.9 に更新(Step 19 A 追記)、CI-DOC-CIL 自己参照を v0.7 に更新。SRS-VIP-001 §10 の UT-ID 列は `inc1-requirements-frozen` 整合保持のため v0.1 据置、UT-ID 充填は Inc.1 実装完了時に統合実施する計画を UTPR §11 改訂履歴に明記済 | k-abe |
