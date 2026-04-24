# 構成アイテム一覧(CI List)

**ドキュメント ID:** CIL-VIP-001
**バージョン:** 0.16
**最終更新日:** 2026-04-24
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
| CI-SRC-001 | 流量制御コア(UNIT-001.*)| `src/vip_ctrl/` | **UNIT-001.1 State Machine v0.1**(Step 19 B2、`state_machine.py`、148 stmt、カバレッジ 100%、MC/DC 100%、RCM-019 実装)+ **UNIT-001.4 Flow Command Validator v0.1**(Step 19 B3、`flow_validator.py`、56 stmt、カバレッジ 100%、MC/DC 100%、RCM-001 実装)+ **UNIT-001.5 SW Watchdog v0.1**(Step 19 B9、`watchdog.py`、78 stmt、カバレッジ 100%、MC/DC 100%、RCM-003 SW 側実装:300 ms `HEARTBEAT_TIMEOUT` + `check_once` テストフック + クロック DI + 階層防御 SW<HW 時間順序確認)+ UNIT-001.2/001.3 骨格のみ(`__init__.py` のみ、Step 19 B10+ で TDD)| C | 運用中(UNIT-001.1 / 001.4 / 001.5 完了、UNIT-001.2 / 001.3 は TDD 未着手) |
| (予定) CI-SRC-002 | アラーム管理 | `src/vip_sim/event_injection.py` ほか | — | C(本版スタブ) | Inc.2 で作成予定 |
| (予定) CI-SRC-003 | 用量計算・ボーラス | 未定 | — | C | Inc.3 で作成予定 |
| (予定) CI-SRC-004 | ロギング・UI | 未定 | — | B/C(分離検討) | Inc.4 で作成予定 |
| CI-SRC-005 | 仮想ハードウェアモデル(UNIT-002.*)| `src/vip_sim/` | **UNIT-002.4 HW-side Failsafe Timer v0.1**(Step 19 B4、`failsafe_timer.py`、78 stmt、カバレッジ 100%、MC/DC 100%、RCM-004 HW 側実装)+ UNIT-002.1〜002.3 骨格のみ(`__init__.py`、Step 19 B1)| C | 運用中(UNIT-002.4 完了、UNIT-002.1〜002.3 は TDD 未着手) |
| CI-SRC-006 | 永続化(UNIT-003.*)| `src/vip_persist/` | **UNIT-003.1 Serializer v0.1**(Step 19 B7、`serializer.py`、47 stmt、カバレッジ 100%、MC/DC 100%、RCM-015 前提実装:Decimal/State/bytes 3 種タグ + sort_keys 決定論性 + build_persisted_record ファクトリ)+ **UNIT-003.2 Checksum Verifier v0.1**(Step 19 B8、`checksum.py`、17 stmt、カバレッジ 100%、MC/DC 100%、RCM-015 構成要素:SDD §4.13 compute / verify、`hmac.compare_digest` 定数時間比較、大小 hex 正規化)+ **UNIT-003.3 Atomic File Writer v0.1**(Step 19 B5、`atomic_writer.py`、78 stmt、カバレッジ 100%、MC/DC 100%、RCM-015 前提実装:temp→rename + 1 世代 bak)+ **共通データモデル v0.2**(Step 19 B6 初版 + Step 19 B7 で `PersistedRecord` 追加、`records.py`、45 stmt、カバレッジ 100%、pydantic frozen モデル `Settings` / `RuntimeState` / `RawPersistedRecord` / `PersistedRecord` / `TrustedRecord`)| C | 運用中(**UNIT-003.* 全完了** + 共通データモデル完了、永続化パイプライン完成) |
| CI-SRC-007 | 整合性検証(UNIT-004.*)| `src/vip_integrity/` | **UNIT-004.1 Integrity Validator v0.1**(Step 19 B6、`validator.py`、88 stmt、カバレッジ 100%、MC/DC 100%、RCM-015 実装:§4.5.B 9 検証項目 + hypothesis 破損注入プロパティ試験)+ UNIT-004.2 骨格のみ(`__init__.py`、Step 19 B1)| C | 運用中(UNIT-004.1 完了、UNIT-004.2 は TDD 未着手) |
| CI-SRC-008 | API クラス C(UNIT-005.1/005.2)| `src/vip_api/` | 骨格のみ(Step 19 B1)| C | 骨格完了、TDD 未着手 |
| CI-SRC-009 | API クラス B(UNIT-005.3)| `src/vip_api_b/` | 骨格のみ(Step 19 B1、SEP-001 分離)| **B** | 骨格完了、TDD 未着手 |

## 4. ドキュメント

Phase 3(M0 基盤整備期)終了 + Inc.1 設計凍結時点。バージョンは 2026-04-21 時点。

| CI ID | ドキュメント | パス | 現行バージョン | 状態 |
|-------|-----------|------|-------------|------|
| CI-DOC-SDP | ソフトウェア開発計画書 | `5.1_software_development_planning/software_development_plan.md` | 0.1 | ドラフト(セルフ承認) |
| CI-DOC-SRS | ソフトウェア要求仕様書 | `5.2_software_requirements_analysis/software_requirements_specification.md` | 0.1 | ドラフト(セルフ承認、Inc.1 範囲確定、Step 15a で §10 CCB §5.4 参照整合バージョン据置。Inc.2〜4 は追補予定) |
| CI-DOC-SAD | ソフトウェアアーキテクチャ設計書 | `5.3_software_architecture_design/software_architecture_design.md` | 0.1 | ドラフト(セルフ承認、Inc.1 範囲確定、Step 12c 反映、Step 15a で §8 CCB §5.4 参照整合バージョン据置) |
| CI-DOC-SDD | ソフトウェア詳細設計書 | `5.4_software_detailed_design/software_detailed_design.md` | 0.2 | ドラフト(セルフ承認、Inc.1 全 17 ユニット §5.4.2 完全充足、CR-0001 反映) |
| CI-DOC-UTPR | ユニットテスト計画書/報告書 | `5.5_software_unit_implementation/software_unit_test_plan_report.md` | 0.9 | ドラフト(セルフ承認、Step 19 B9:UNIT-001.5 実施結果を §9.2 / §11 に反映、Pass 19 tests / カバレッジ 100% / MC/DC 100%。§7.3.8 を新規詳細化(骨格の「500 ms」誤記訂正 → 300 ms 詳細テーブル UT-001.5-01〜12、運用性 1 + 専門性 5 論点を推奨方針で解消、UT 申し送りなし)、MINOR 区分・CR 不要、残骨格を 10 → 9 ユニットに更新)|
| CI-DOC-ITPR | 結合試験計画書/報告書 | `5.6_software_integration_testing/software_integration_test_plan_report.md` | — | 未着手(Inc.1 予定) |
| CI-DOC-STPR | システム試験計画書/報告書 | `5.7_software_system_testing/software_system_test_plan_report.md` | — | 未着手(Inc.1 予定) |
| CI-DOC-SMS | ソフトウェアマスタ仕様書 | `5.8_software_release/software_master_specification.md` | — | 未着手(M_final 予定) |
| CI-DOC-SMP | ソフトウェア保守計画書 | `6_software_maintenance_process/software_maintenance_plan.md` | 0.2 | ドラフト(セルフ承認、Step 15a で §4.6 変更区分表 1 分インターバル反映) |
| CI-DOC-SRMP | ソフトウェアリスクマネジメント計画書 | `7_software_risk_management_process/software_risk_management_plan.md` | 0.2 | ドラフト(セルフ承認、Step 15a で §3.2 独立性担保の時間間隔を 1 分に具体化) |
| CI-DOC-SSC | ソフトウェア安全クラス決定記録 | `7_software_risk_management_process/software_safety_class_determination_record.md` | 0.1 | ドラフト(セルフ承認) |
| CI-DOC-RMF | リスクマネジメントファイル(ISO 14971) | `7_software_risk_management_process/risk_management_file.md` | 0.2 | ドラフト(セルフ承認、継続更新。RCM-019 登録済) |
| CI-DOC-SCMP | ソフトウェア構成管理計画書 | `8_software_configuration_management_process/software_configuration_management_plan.md` | 0.3 | ドラフト(セルフ承認、Step 15a で §4.1 表・§4.1.1 手順 2 の 1 分インターバル反映) |
| CI-DOC-CIL | 構成アイテム一覧(本書) | `8_software_configuration_management_process/configuration_item_list.md` | 0.16 | ドラフト(セルフ承認、Step 19 B9 反映:CI-SRC-001 に UNIT-001.5 SW Watchdog v0.1 追記、CI-TD-001j 新規登録、CI-DOC-UTPR v0.9 反映、CI-DOC-DEVSTEPS v0.18 反映、自己参照 v0.16) |
| CI-DOC-CCB | CCB 運用規程 | `8_software_configuration_management_process/ccb_operating_rules.md` | 0.2 | ドラフト(セルフ承認、Step 15a で §5.4 大改訂 — 学習/実機 2 系統表記・1 分インターバル採用) |
| CI-DOC-CRR | 変更要求台帳 | `8_software_configuration_management_process/change_request_register.md` | 0.5 | ドラフト(セルフ承認、Step 15b 後段で CR-0002 CLOSED 記録反映 — 実装 PR #6、マージ 2026-04-22T23:46:05Z、SHA a741cda、インターバル実績 約 47h 14m) |
| CI-DOC-SPRP | ソフトウェア問題解決手順書 | `9_software_problem_resolution_process/software_problem_resolution_procedure.md` | 0.2 | ドラフト(セルフ承認、Step 15a で §5 CCB 通知行の 1 分インターバル反映) |
| CI-DOC-ACL | IEC 62304 監査チェックリスト | `compliance/audit_checklist.md` | テンプレートのまま | 未編集(Inc.1 以降で本プロジェクト向けに整備予定) |
| CI-DOC-README | プロジェクト README | `README.md` | — | 継続更新 |
| CI-DOC-DEVSTEPS | 開発ステップ記録(お手本) | `DEVELOPMENT_STEPS.md` | 0.18 | 継続更新(ステップ毎に追記、Step 19 B9 反映:UNIT-001.5 SW Watchdog TDD 実装、カバレッジ 100% / MC/DC 100% 達成、RCM-003 SW 側完了で Watchdog 系 SW/HW 二重冗長層が閉じた、残 10 → 9 ユニット、UTPR §7.3.8 を新規詳細化)|
| CI-DOC-CLAUDE | 編集ガイド(AI 支援含む) | `CLAUDE.md` | — | 本プロジェクト固有ルール追記済、Step 15a で単独開発下の独立性擬制セクションを 24h → 1 分に更新 |
| CI-DOC-UPSTREAM | iec62304_template への修正要望台帳 | `UPSTREAM_FEEDBACK.md` | 0.3 | ドラフト(セルフ承認、UF-001〜UF-009 全 9 件 upstream 受領済み反映 — PR #15〜#23 マージ、2026-04-21。※v0.2 時点 Step 17a で本 CIL 反映漏れを Step 17b で遡及補正) |

## 5. SOUP(Software of Unknown Provenance)

> **Step 19 B1(2026-04-23)で SOUP を正式登録。** `pyproject.toml` で依存を宣言し、`pip install -e ".[dev]"` による初回ビルドで実インストールされたバージョンを下記の「実測バージョン」列に記録した。`>=X.Y,<Z.0` 形式のバージョン制約(SemVer 互換性レンジ)を採用し、パッチ更新は許容、メジャー更新は CR 経由とする運用。SHA-256 による完全固定は Inc.1 完了ベースライン(`inc1-baseline`)付与時に `pip hash` で生成し、`requirements-lock.txt` を CI-CFG-010 として追加する計画(Step 19 B2 後段で決定)。

| CI ID | 名称 | 供給元 | 制約(pyproject) | 実測バージョン(Step 19 B1 時点) | ライセンス | 用途 | 関連ハザード |
|-----------|------|-------|-----------|-----------|----------|---------|------------|
| CI-SOUP-001 | CPython ランタイム | Python Software Foundation | `>=3.12`(`requires-python`)| 3.12.8 | PSF | 実行環境 | 全般 |
| CI-SOUP-002 | pytest | pytest-dev | `>=8.0` | 9.0.3 | MIT | ユニット試験実行 | — |
| CI-SOUP-003 | pytest-cov | pytest-dev | `>=5.0` | 7.1.0 | MIT | 網羅率計測 | — |
| CI-SOUP-004 | hypothesis | HypothesisWorks | `>=6.98` | 6.152.1 | MPL-2.0 | プロパティベース試験(UNIT-001.1, UNIT-004.1 中心) | HZ-006(計算誤り検出) |
| CI-SOUP-005 | ruff | Astral | `>=0.5` | 0.15.11 | MIT | lint(`--select ALL`) / 整形 | — |
| CI-SOUP-006 | pylint | Pylint | `>=3.2` | 4.0.5 | GPL-2.0 | 追加 lint | — |
| CI-SOUP-007 | mypy | Python | `>=1.10` | 1.20.2 | MIT | 静的型検査(`--strict`)、SEP-001 インポートグラフ検証 | HZ-003、HZ-006 |
| CI-SOUP-008 | bandit | PyCQA | `>=1.7` | 1.9.4 | Apache-2.0 | セキュリティ lint | — |
| CI-SOUP-009 | pydantic | Pydantic | `>=2.6,<3.0` | 2.13.3 | MIT | 実行時型検証 | HZ-003、HZ-008 |
| CI-SOUP-010 | pip-audit | PyPA | `>=2.7` | 2.10.0 | Apache-2.0 | SOUP 脆弱性スキャン(`--strict`) | — |
| CI-SOUP-011 | pytest-timeout | pytest-dev | `>=2.3` | 2.4.0 | MIT | 試験タイムアウト保護(デフォルト 30 秒) | — |

SRMP §4.3 の SOUP 評価(供給元の信頼性、ライセンス適合性、脆弱性履歴、バージョン更新の追跡性)は Step 19 B2 以降で UNIT-001.1 から順次、各 SOUP の利用が始まる時点に実施する。SHA-256 固定は上記の通り `inc1-baseline` 付与時に実施。

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
| CI-TOOL-008 | Python ランタイム | CPython | 3.12.8(Step 19 B1 時点、SOUP-001 と共通) | 実行環境 | — |
| CI-TOOL-009 | パッケージ管理 | pip + venv(標準ライブラリ) | pip 26.0.1、venv 標準 | 依存管理(`pip install -e ".[dev]"` で editable インストール) | — |
| CI-TOOL-010 | 静的解析スイート | ruff / pylint / mypy / bandit | SOUP-005〜008 参照 | 品質・型・セキュリティ検査 | — |
| CI-TOOL-011 | 試験フレームワーク | pytest / pytest-cov / hypothesis / pytest-timeout | SOUP-002〜004, 011 参照 | ユニット試験、網羅率、プロパティ試験、タイムアウト保護 | — |
| CI-TOOL-012 | 脆弱性スキャン | pip-audit | SOUP-010 参照 | SOUP 脆弱性検出(CI `unit-test.yml` に統合済) | — |

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
| CI-CFG-009 | Python プロジェクト設定 | `pyproject.toml` | 依存、ビルド、ruff / mypy / pytest / coverage / pylint / bandit の統合設定(Step 19 B1 で追加) |
| (予定) CI-CFG-010 | 依存ロックファイル(SHA-256 付) | `requirements-lock.txt`(計画) | 依存の完全固定。Step 19 B2 後段 or `inc1-baseline` 付与時に `pip hash` ベースで生成する計画 |
| CI-CFG-011 | コード CI ワークフロー | `.github/workflows/unit-test.yml` | ruff / ruff format / mypy / bandit / pytest(カバレッジ付)/ pip-audit を実行(Step 19 B1 で追加、`docs-check.yml` と並行)|

## 8. 試験データ・試験資産

> **Step 19 B1(2026-04-23)で初期試験資産を `tests/` 配下に追加。** Step 19 B2 以降で各 UNIT-NNN に対応するユニット試験ファイルを追加する。

| CI ID | 名称 | パス | 用途 |
|-----------|------|------|------|
| CI-TD-001 | ユニット試験ケース(パッケージ構造スモーク)| `tests/test_package_structure.py` | 6 サブシステムパッケージの import 可能性と SEP-001 分離の弱事前確認(7 ケース、Step 19 B1 で新規追加)|
| CI-TD-001a | 共通 pytest 設定・フィクスチャ | `tests/conftest.py` | 共通フィクスチャ置き場(Step 19 B2+ で拡充)|
| CI-TD-001b | UNIT-001.1 State Machine 試験 | `tests/unit/test_state_machine.py` | UT-001.1-01〜12 を 62 ケースに展開(正常系 / 境界値 / 異常系 / RCM-019 / 並行 / タイミング / プロパティ / 持続化結合スモーク)、100% カバレッジ / MC/DC 100%(Step 19 B2 で新規追加) |
| CI-TD-001d | UNIT-001.4 Flow Command Validator 試験 | `tests/unit/test_flow_validator.py` | UT-001.4-01〜12 を 34 ケースに展開(正常系 / 境界値 / 異常系 / RCM-001 / 状態別スキップ / 純粋性 / frozen / プロパティ)、100% カバレッジ / MC/DC 100%(Step 19 B3 で新規追加) |
| CI-TD-001e | UNIT-002.4 HW-side Failsafe Timer 試験 | `tests/unit/test_failsafe_timer.py` | UT-002.4-01〜08 を 18 ケースに展開(正常系 / 境界値 / 並行 / RCM-004 / クロック逆転 / 冪等 / start-stop / 例外耐性 / 実時間スレッド統合スモーク)、100% カバレッジ / MC/DC 100%(Step 19 B4 で新規追加) |
| CI-TD-001f | UNIT-003.3 Atomic File Writer 試験 | `tests/unit/test_atomic_writer.py` | UT-003.3-01〜10 を 21 ケースに展開(正常系 / 境界値 / 異常系 / 並行ステートレス / bak 世代管理 / read / rollback / best-effort unlink / 非 POSIX 早期リターン / fsync 検証 / OSError 注入経路網羅)、100% カバレッジ / MC/DC 100%(Step 19 B5 で新規追加)。subprocess + SIGKILL 電源断試験は ITPR §5.6 へ申し送り |
| CI-TD-001g | UNIT-004.1 Integrity Validator 試験 | `tests/unit/test_integrity_validator.py` | UT-004.1-01〜12 を 24 ケースに展開 + 補助観点 9 件 = 計 33 ケース(正常系 / 境界値 / RCM-015 / hypothesis 破損注入 3 種 / SettingsInconsistent / AccumulationExceedsDose / StateContradiction / UnsavableState / 純粋関数性 / frozen 性 / SUPPORTED_SCHEMA_VERSIONS 契約 / tolerance 境界 / dose==0 分岐 / §4.5.B 列挙順序 / compute_sha256 契約)、100% カバレッジ / MC/DC 100%(Step 19 B6 で新規追加) |
| CI-TD-001h | UNIT-003.1 Serializer 試験 | `tests/unit/test_serializer.py` | UT-003.1-01〜17 を展開して 26 ケース(正常系 / 不正 JSON・UTF-8 例外 / 必須フィールド欠落 / 未知 schema_version 通過 / Decimal 精度保持 / State 6 値 パラメータ化 / `__bytes__` base64 ラウンドトリップ / 決定論性 20 回 + hypothesis `max_examples=50` 5 回 / hypothesis ラウンドトリップ `max_examples=200` / Integrity Validator との統合 / compute_payload_checksum 決定論 / sort_keys=True 検証 / `_default` 未知型 TypeError / `_hook` パススルー)、100% カバレッジ / MC/DC 100%(Step 19 B7 で新規追加) |
| CI-TD-001i | UNIT-003.2 Checksum Verifier 試験 | `tests/unit/test_checksum.py` | UT-003.2-01〜15 を展開して 32 ケース(NIST 既知ベクタ 2 / ラウンドトリップ 5 パラメータ化 / 1 bit 改変検知 / 長さ違い `expected` 4 サブケース / 非 hex 文字 `expected` 4 サブケース / 大小混合 hex 正規化 2 / 決定論性 100 回 / 1 MB 入力 / 出力長 64 パラメータ化 4 / 小文字 hex パラメータ化 4 / hypothesis ラウンドトリップ `max_examples=200` / hypothesis 衝突試験 `max_examples=200` / 正しい digest 1 文字短縮 / 空白混入 expected)、100% カバレッジ / MC/DC 100%(Step 19 B8 で新規追加)。タイミング試験(SDD §4.13.F 参考)は ITPR §5.6 へ申し送り |
| CI-TD-001j | UNIT-001.5 SW Watchdog 試験 | `tests/unit/test_watchdog.py` | UT-001.5-01〜12 を展開して 19 ケース(正常系 1 / 境界値 299/300/300+ε/350 ms 4 / 並行 heartbeat / クロック逆転安全側 Trip / Tripped 後 heartbeat 無視 / `check_once` 冪等 / start-stop ライフサイクル 4 / State Machine 例外耐性(SDD §4.8.E)/ 定数値 2 / 実時間スレッド統合スモーク / 階層防御 SW<HW 時間順序 301 ms→501 ms)、100% カバレッジ / MC/DC 100%(Step 19 B9 で新規追加) |
| (予定) CI-TD-001c | UNIT-001.2 / 001.3 / 002.1 / 002.2 / 002.3 / 004.2 / 005.x 試験 | `tests/unit/test_*.py` | Step 19 B10+ 以降で UNIT-001.2 Control Loop などを順次 TDD Red で追加 |
| (予定) CI-TD-002 | 結合試験シナリオ | `tests/integration/` | 故障注入シナリオ含む結合試験(§5.6、ITPR v0.1 作成時) |
| (予定) CI-TD-003 | システム試験シナリオ | `tests/system/` | 要求ベースのシステム試験(§5.7、STPR v0.1 作成時) |
| (予定) CI-TD-004 | プロパティベース試験仕様 | `tests/properties/` or `tests/unit/` 直下 | hypothesis 用プロパティ定義(UNIT-001.1 / UNIT-004.1 中心) |
| (予定) CI-TD-005 | 試験入力データ | `tests/data/` | YAML/JSON 形式の試験データ |

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
| 0.8 | 2026-04-23 | Step 19 B1(Python パッケージ骨格 + コード CI 整備)に伴う整合化。**(1) §5 SOUP の正式登録**:CI-SOUP-001〜010 を候補から正式登録に昇格、CI-SOUP-011(pytest-timeout)を新規追加、各 SOUP の `pyproject.toml` 宣言制約と `pip install -e ".[dev]"` による初回インストール実測バージョンを表に追記(SHA-256 固定は Inc.1 完了ベースライン付与時に実施、計画を §5 前書きに明記)。**(2) §6 ツールの運用中化**:CI-TOOL-008(CPython 3.12.8)/ 009(pip+venv)/ 010(静的解析スイート)/ 011(試験フレームワーク)/ 012(pip-audit)を「予定」→ 運用中に遷移、各行の内容を実装状況に更新。**(3) §7 CFG の運用中化**:CI-CFG-009(`pyproject.toml`)と CI-CFG-011(`.github/workflows/unit-test.yml`)を「予定」→ 運用中に遷移、CI-CFG-010(依存ロックファイル)は計画のまま据置。**(4) §8 試験資産の初期登録**:CI-TD-001(`tests/test_package_structure.py`、6 パッケージ import 可能性 + SEP-001 弱事前確認、7 ケース)と CI-TD-001a(`tests/conftest.py`)を新規登録、CI-TD-001b〜005 は Step 19 B2 以降の予定として整理。**(5) 自己参照**:CI-DOC-CIL を v0.7 → v0.8、CI-DOC-DEVSTEPS を v0.9 → v0.10 に更新。Step 14d / Step 17b / Step 15b 後段教訓「派生ドキュメント更新漏れ」の四度目試行として、CR-なし新規成果物でも網羅レビューを実施 | k-abe |
| 0.9 | 2026-04-23 | Step 19 B2(UNIT-001.1 State Machine TDD 実装)に伴う整合化。**(1) §3 ソースコード:** CI-SRC-001(流量制御コア、UNIT-001.1 v0.1 運用中 = `src/vip_ctrl/state_machine.py`、148 stmt、カバレッジ 100%、MC/DC 100%、RCM-019 実装、UT-001.1-01〜12 Pass)に昇格、残 UNIT-001.2〜001.5 は骨格として同エントリに注記。CI-SRC-005〜009 を「UNIT-002〜005 対応サブパッケージの骨格(Step 19 B1 追加)」として新規登録。**(2) §8 試験資産:** CI-TD-001b(`tests/unit/test_state_machine.py`、62 ケース)を新規登録、CI-TD-001c(UNIT-001.2 以降の試験)を「予定」として追記。**(3) 連動反映:** CI-DOC-UTPR v0.1 → v0.2(第 II 部 §9.2 / §11 反映)、CI-DOC-DEVSTEPS v0.10 → v0.11(Step 19 B2 追記反映)、CI-DOC-CIL 自己参照 v0.9。**(4) coverage `fail_under` 復帰:** Step 19 B1 で 0 に一時緩和していた `pyproject.toml` の `coverage.fail_under` を 95 に戻す(戻し忘れ防止が成立、Step 19 B1 計画通り実行)。実績は UNIT-001.1 実装後で TOTAL 100.00%、`fail_under=95` を超えて CI Pass 確認済 | k-abe |
| 0.10 | 2026-04-23 | Step 19 B3(UNIT-001.4 Flow Command Validator TDD 実装)に伴う整合化。**(1) §3 ソースコード:** CI-SRC-001 行に **UNIT-001.4 Flow Command Validator v0.1**(`src/vip_ctrl/flow_validator.py`、56 stmt、カバレッジ 100%、MC/DC 100%、RCM-001 実装、UT-001.4-01〜12 Pass)を追記、状態を「UNIT-001.1 / 001.4 完了、UNIT-001.2 / 001.3 / 001.5 は TDD 未着手」に更新。**(2) §8 試験資産:** CI-TD-001d(`tests/unit/test_flow_validator.py`、34 ケース)を新規登録、CI-TD-001c の対象を残ユニット(UNIT-001.2 / 001.3 / 001.5 / 002.* 以降)に絞った表記へ更新。**(3) 連動反映:** CI-DOC-UTPR v0.2 → v0.3(第 I 部 §7.3.2 を SRS-O-001 / SDD §4.2 に整合化、第 II 部 §9.2 / §11 を Pass 反映、MINOR 区分・CR 不要)、CI-DOC-DEVSTEPS v0.11 → v0.12(Step 19 B3 追記反映)、CI-DOC-CIL 自己参照 v0.10。**(4) Step 14d / 17b / 15b 後段教訓「派生ドキュメント更新漏れ」の五度目試行:** UTPR・CI-SRC-001 行・CI-DOC-UTPR・CI-DOC-DEVSTEPS・自己参照 v0.10・新規 CI-TD-001d・改訂履歴の 7 箇所を事前リストアップして網羅レビュー実施。Step 19 B2 と同様、TOTAL カバレッジ 100.00% で CI `fail_under=95` Pass | k-abe |
| 0.11 | 2026-04-23 | Step 19 B4(UNIT-002.4 HW-side Failsafe Timer TDD 実装)に伴う整合化。**(1) §3 ソースコード:** CI-SRC-005 行を骨格 → **UNIT-002.4 HW-side Failsafe Timer v0.1**(`src/vip_sim/failsafe_timer.py`、78 stmt、カバレッジ 100%、MC/DC 100%、RCM-004 HW 側実装、UT-002.4-01〜08 Pass)に昇格、UNIT-002.1〜002.3 は骨格として注記。**(2) §8 試験資産:** CI-TD-001e(`tests/unit/test_failsafe_timer.py`、18 ケース)を新規登録、CI-TD-001c の対象を UNIT-002.1〜002.3 / 003.x / 004.x / 005.x に絞った表記へ更新。**(3) 連動反映:** CI-DOC-UTPR v0.3 → v0.4(§7.3.3 を SDD §4.3 に整合化:Logger 据置 + DI 採用 + 逆転安全側、第 II 部 §9.2 / §11 Pass 反映、MINOR 区分・CR 不要)、CI-DOC-DEVSTEPS v0.12 → v0.13(Step 19 B4 追記反映)、CI-DOC-CIL 自己参照 v0.11、CIL 冒頭バージョン v0.11 + 最終更新日 2026-04-23 を整合更新(Step 19 B3 教訓「冒頭バージョン表記の累積更新漏れ」の運用継続)。**(4) Step 14d / 17b / 15b 後段教訓「派生ドキュメント更新漏れ」の六度目試行:** UTPR・CI-SRC-005 行・CI-DOC-UTPR・CI-DOC-DEVSTEPS・自己参照 v0.11・新規 CI-TD-001e・冒頭メタ・改訂履歴の 8 箇所を事前リストアップして網羅レビュー実施。TOTAL カバレッジ 100.00%(stmt 282 + branch 40)で CI `fail_under=95` Pass | k-abe |
| 0.16 | 2026-04-24 | Step 19 B9(UNIT-001.5 SW Watchdog TDD 実装)に伴う整合化。**(1) §3 ソースコード:** CI-SRC-001 行に **UNIT-001.5 SW Watchdog v0.1**(`src/vip_ctrl/watchdog.py`、78 stmt、カバレッジ 100%、MC/DC 100%、RCM-003 SW 側実装:300 ms `HEARTBEAT_TIMEOUT` + `check_once` テストフック + クロック DI + State Machine `on_watchdog_timeout(SW_WATCHDOG)` 呼出 + 階層防御 SW<HW 時間順序確認)を追記、状態を「UNIT-001.1 / 001.4 / 001.5 完了」に更新。**(2) §8 試験資産:** CI-TD-001j(`tests/unit/test_watchdog.py`、19 ケース)を新規登録、CI-TD-001c の対象から UNIT-001.5 を除外。**(3) 連動反映:** CI-DOC-UTPR v0.8 → v0.9(§7.3.8 を骨格の「500 ms」誤記訂正 → 300 ms 詳細 UT-001.5-01〜12 に書き下ろし、残骨格 10 → 9 ユニット、MINOR 区分・CR 不要)、CI-DOC-DEVSTEPS v0.17 → v0.18(Step 19 B9 追記反映)、CI-DOC-CIL 自己参照 v0.16、CIL 冒頭バージョン v0.16 + 最終更新日 2026-04-24。**(4) 派生ドキュメント更新漏れ教訓の十一度目試行:** UTPR §7.3.8 新節・UTPR §9.2(UNIT-001.5 行実績化)・UTPR §11・CI-SRC-001 行・CI-DOC-UTPR・CI-DOC-DEVSTEPS・自己参照 v0.16・新規 CI-TD-001j・CI-TD-001c 対象更新・冒頭メタ・改訂履歴の 11 箇所を事前リストアップして網羅レビュー実施。TOTAL カバレッジ 100.00%(stmt 635 + branch 96)、283 tests 3 連続 stable で CI `fail_under=95` Pass。**Watchdog 系 SW/HW 二重冗長層(RCM-003 SW + RCM-004 HW)が閉じた重要節目** | k-abe |
| 0.15 | 2026-04-24 | Step 19 B8(UNIT-003.2 Checksum Verifier TDD 実装)に伴う整合化。**(1) §3 ソースコード:** CI-SRC-006 行に **UNIT-003.2 Checksum Verifier v0.1**(`src/vip_persist/checksum.py`、17 stmt、カバレッジ 100%、MC/DC 100%、RCM-015 構成要素実装:SDD §4.13 `compute` / `verify` の 2 公開 API、`hmac.compare_digest` 定数時間比較、大小 hex `.lower()` 正規化、不正 `expected` は例外なし `False`)を追記。永続化パイプライン(UNIT-003.1 / 003.2 / 003.3)全完了で状態を「永続化パイプライン完成」に更新。**(2) §8 試験資産:** CI-TD-001i(`tests/unit/test_checksum.py`、32 ケース)を新規登録、CI-TD-001c の対象を残 10 ユニットに更新。**(3) 連動反映:** CI-DOC-UTPR v0.7 → v0.8(§7.3.7 を骨格 → 詳細 UT-003.2-01〜15 に書き下ろし、残骨格 11 → 10 ユニット、MINOR 区分・CR 不要)、CI-DOC-DEVSTEPS v0.16 → v0.17(Step 19 B8 追記反映)、CI-DOC-CIL 自己参照 v0.15、CIL 冒頭バージョン v0.15 + 最終更新日 2026-04-24。**(4) 派生ドキュメント更新漏れ教訓の十度目試行:** UTPR §7.3.7 新節・UTPR §9.2(UNIT-003.2 行実績化 + UNIT-003.1 行二重状態解消)・UTPR §11・CI-SRC-006 行・CI-DOC-UTPR・CI-DOC-DEVSTEPS・自己参照 v0.15・新規 CI-TD-001i・CI-TD-001c 対象更新・冒頭メタ・改訂履歴の 11 箇所を事前リストアップして網羅レビュー実施。TOTAL カバレッジ 100.00%(stmt 557 + branch 84)、264 tests 3 連続 stable で CI `fail_under=95` Pass | k-abe |
| 0.14 | 2026-04-24 | Step 19 B7(UNIT-003.1 Serializer TDD 実装)に伴う整合化。**(1) §3 ソースコード:** CI-SRC-006 行に **UNIT-003.1 Serializer v0.1**(`src/vip_persist/serializer.py`、47 stmt、カバレッジ 100%、MC/DC 100%、RCM-015 前提実装:Decimal/State/bytes 3 種タグ付け + sort_keys 決定論性 + build_persisted_record ファクトリ + SHA-256 checksum 計算)を追記、共通データモデル v0.1 → v0.2(`records.py` に `PersistedRecord` モデル追加、37 → 45 stmt、カバレッジ 100%)に昇格、UNIT-003.2 は骨格として注記。状態を「UNIT-003.1 / 003.3 + 共通データモデル完了、UNIT-003.2 は TDD 未着手」に更新。**(2) §8 試験資産:** CI-TD-001h(`tests/unit/test_serializer.py`、26 ケース)を新規登録、CI-TD-001c の対象を UNIT-003.2 を含めた残ユニットに更新。**(3) 連動反映:** CI-DOC-UTPR v0.6 → v0.7(§7.3.6 を新規詳細化 — 7 論点 + 1 実装時論点を推奨方針で解消、残骨格 12 → 11 ユニット、MINOR 区分・CR 不要)、CI-DOC-DEVSTEPS v0.15 → v0.16(Step 19 B7 追記反映)、CI-DOC-CIL 自己参照 v0.14、CIL 冒頭バージョン v0.14 + 最終更新日 2026-04-24 を整合更新。**(4) 派生ドキュメント更新漏れ教訓の九度目試行:** UTPR §7.3.6 新節・UTPR §9.2・UTPR §11・CI-SRC-006 行(2 箇所更新:Serializer 追記 + 共通データモデル v0.2)・CI-DOC-UTPR・CI-DOC-DEVSTEPS・自己参照 v0.14・新規 CI-TD-001h・CI-TD-001c 対象更新・冒頭メタ・改訂履歴の 10 箇所を事前リストアップして網羅レビュー実施。TOTAL カバレッジ 100.00%(stmt 540 + branch 80)、232 tests 3 連続 stable で CI `fail_under=95` Pass | k-abe |
| 0.13 | 2026-04-23 | Step 19 B6(UNIT-004.1 Integrity Validator TDD 実装)に伴う整合化。**(1) §3 ソースコード:** CI-SRC-007 行を骨格 → **UNIT-004.1 Integrity Validator v0.1**(`src/vip_integrity/validator.py`、88 stmt、カバレッジ 100%、MC/DC 100%、RCM-015 実装:§4.5.B 9 検証項目 + hypothesis 破損注入プロパティ試験、UT-004.1-01〜12 展開 + 補助観点 9 = 33 tests Pass)に昇格、UNIT-004.2 は骨格として注記。CI-SRC-006 行に **共通データモデル v0.1**(`src/vip_persist/records.py`、37 stmt、カバレッジ 100%、pydantic frozen モデル `Settings` / `RuntimeState` / `RawPersistedRecord` / `TrustedRecord`、UNIT-003.1 Serializer 再利用前提)を追記(Step 19 B6 スコープ拡張、MINOR)。**(2) §8 試験資産:** CI-TD-001g(`tests/unit/test_integrity_validator.py`、33 ケース)を新規登録、CI-TD-001c の対象を UNIT-004.2 を含めた残ユニットに更新。**(3) 連動反映:** CI-DOC-UTPR v0.5 → v0.6(§7.3.5 を SDD §4.5 に 4 件整合化:戻り値型統一 / pydantic 管轄差し替え / FutureTimestamp 退け / ERROR 不変条件差し替え、第 II 部 §9.2 / §11 Pass 反映、MINOR 区分・CR 不要)、CI-DOC-DEVSTEPS v0.14 → v0.15(Step 19 B6 追記反映)、CI-DOC-CIL 自己参照 v0.13、CIL 冒頭バージョン v0.13 を整合更新。**(4) 派生ドキュメント更新漏れ教訓の八度目試行:** UTPR・CI-SRC-006 行・CI-SRC-007 行・CI-DOC-UTPR・CI-DOC-DEVSTEPS・自己参照 v0.13・新規 CI-TD-001g・冒頭メタ・改訂履歴の 9 箇所を事前リストアップして網羅レビュー実施。TOTAL カバレッジ 100.00%(stmt 485 + branch 68)、206 tests 3 連続 stable で CI `fail_under=95` Pass。**代表 5 ユニット(UNIT-001.1 / 001.4 / 002.4 / 003.3 / 004.1)全完了** | k-abe |
| 0.12 | 2026-04-23 | Step 19 B5(UNIT-003.3 Atomic File Writer TDD 実装)に伴う整合化。**(1) §3 ソースコード:** CI-SRC-006 行を骨格 → **UNIT-003.3 Atomic File Writer v0.1**(`src/vip_persist/atomic_writer.py`、78 stmt、カバレッジ 100%、MC/DC 100%、RCM-015 前提実装:temp → rename + 1 世代 bak、write/read/rollback 3 API、UT-003.3-01〜10 展開 + 補助観点 9 = 21 tests Pass)に昇格、UNIT-003.1 / 003.2 は骨格として注記。**(2) §8 試験資産:** CI-TD-001f(`tests/unit/test_atomic_writer.py`、21 ケース)を新規登録、CI-TD-001c の対象を UNIT-003.1 / 003.2 を含めた残ユニットに更新。**(3) 連動反映:** CI-DOC-UTPR v0.4 → v0.5(§7.3.4 を SDD §4.4 に 4 件整合化 + MC/DC 目標 95%→100% 引き上げ、第 II 部 §9.2 / §11 Pass 反映、MINOR 区分・CR 不要)、CI-DOC-DEVSTEPS v0.13 → v0.14(Step 19 B5 追記反映)、CI-DOC-CIL 自己参照 v0.12、CIL 冒頭バージョン v0.12 を整合更新。**(4) 派生ドキュメント更新漏れ教訓の七度目試行:** UTPR・CI-SRC-006 行・CI-DOC-UTPR・CI-DOC-DEVSTEPS・自己参照 v0.12・新規 CI-TD-001f・冒頭メタ・改訂履歴の 8 箇所を事前リストアップして網羅レビュー実施。TOTAL カバレッジ 100.00%(stmt 360 + branch 46)、173 tests 3 連続 stable で CI `fail_under=95` Pass | k-abe |
