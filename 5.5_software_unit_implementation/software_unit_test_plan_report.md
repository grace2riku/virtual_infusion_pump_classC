# ソフトウェアユニットテスト計画書/報告書

**ドキュメント ID:** UTPR-VIP-001
**バージョン:** 0.3
**作成日:** 2026-04-23
**対象製品:** 仮想輸液ポンプ(Virtual Infusion Pump)/ VIP-SIM-001
**対象ソフトウェアバージョン:** v0.2.0-inc1(予定、Inc.1 完了時)
**対象範囲:** Inc.1(流量制御コア、全 17 ソフトウェアユニット)
**安全クラス:** C(IEC 62304)

| 役割 | 氏名 | 所属 | 日付 | 署名 |
|------|------|------|------|------|
| 作成者 | k-abe | — | 2026-04-23 | (セルフ) |
| レビュー者 | k-abe(単独開発下の独立性擬制 — CCB-VIP-001 §4.1.1 / SRMP-VIP-001 §3.2 準拠) | — | 2026-04-23 | (セルフ) |
| 承認者 | k-abe(CCB 兼任、軽微区分のためインターバル対象外) | — | 2026-04-23 | (セルフ) |

---

> 本書はユニット試験の **計画**(第 I 部)と **実施結果**(第 II 部、報告)を一体で管理する。v0.1 時点では計画のみを記述する。各ユニットの実装着手(Step 19 B 以降、TDD Red-Green-Refactor で進行)に合わせて第 II 部を追記し、Inc.1 完了時に全ユニットを Verified に昇格する。

## 用語と略語(本書で初出のもの)

| 略語 | フルネーム | 意味 |
|------|-----------|------|
| UT | Unit Test | ユニット試験 |
| UTPR | Unit Test Plan/Report | ユニットテスト計画書/報告書 |
| TDD | Test-Driven Development | テスト駆動開発(Red-Green-Refactor サイクル) |
| MC/DC | Modified Condition/Decision Coverage | 改良条件分岐網羅 |

その他、SRS/SAD/SDD 参照略語は CLAUDE.md 略語表に準拠。

## 1. 目的と適用範囲

本書は、IEC 62304 箇条 5.5(ソフトウェアユニットの実装)に基づき、本プロジェクトの **Inc.1(流量制御コア)で定義された全 17 ソフトウェアユニット** の実装と検証(ユニット試験)の計画および結果を記録する。

**適用範囲:**

- **対象ユニット:** SDD-VIP-001 v0.2 §3 で改良された 17 ユニット(UNIT-001.1〜UNIT-005.3)
- **対象 SRS 要求:** SRS-VIP-001 v0.1 §9 Inc.1 受入基準に列挙された全必須要求(SRS-001〜032、P01〜P07、I-*、O-*、IF-001〜005、ALM-001〜003、SEC-001〜003、UX-001〜002、DATA-001〜004、OPS-001〜012、RCM-001〜020)
- **対象 RCM:** RMF-VIP-001 v0.2 のうち Inc.1 範囲(RCM-001, 003, 004, 015, 016, 019/SRS-RCM-020)
- **除外範囲:** Inc.2〜4 の要求(アラーム UI、用量計算、UI/ロギング本体)およびスタブ I/F の Inc.2 以降の本実装

**位置づけ:**

- 本書は結合試験(ITPR-VIP-001、§5.6 予定)と システム試験(STPR-VIP-001、§5.7 予定)の **土台** として機能する。UT Pass がない状態では結合試験に進まない(SDP §開発フロー)。
- 試験ケースは SDD §5.4.4 で規定された各ユニットの「検証方法」を具体的な UT-ID に展開したものである。
- 本プロジェクトは **TDD(Red-Green-Refactor)** を採用する(SDP v0.1)。したがって本書 v0.1(計画)の完成後、各ユニット実装(Step 19 B)は「UT を Red で先に書く → 実装で Green 化 → Refactor」の順に進める。

## 2. 参照文書

| ID | 文書名 | バージョン | 参照箇所 |
|----|--------|----------|---------|
| [1] | ソフトウェア開発計画書(SDP-VIP-001) | v0.1 | 実装ルール、TDD 採用、静的解析スタック |
| [2] | ソフトウェア要求仕様書(SRS-VIP-001) | v0.1 | §9 Inc.1 受入基準、機能/性能/RCM 要求 |
| [3] | ソフトウェアアーキテクチャ設計書(SAD-VIP-001) | v0.1 | ARCH-001〜007、SEP-001〜003、SOUP |
| [4] | ソフトウェア詳細設計書(SDD-VIP-001) | v0.2 | §4.1〜§4.17 全 17 ユニット詳細、検証方法 |
| [5] | ソフトウェアリスクマネジメント計画書(SRMP-VIP-001) | v0.2 | §3.2 独立性、§7.2 影響解析 |
| [6] | リスクマネジメントファイル(RMF-VIP-001) | v0.2 | RCM-001〜019 検証状態 |
| [7] | ソフトウェア構成管理計画書(SCMP-VIP-001) | v0.3 | §4.1 CR 区分、§5 ベースライン |
| [8] | CCB 運用規程(CCB-VIP-001) | v0.2 | §5.4 インターバル(1 分、学習プロジェクト特例) |
| [9] | ソフトウェア問題解決手順書(SPRP-VIP-001) | v0.2 | 試験中発見の不具合の PRB 起票運用 |

---

# 第 I 部 計画

## 3. ソフトウェアユニットの実装(箇条 5.5.1)

### 3.1 実装ルール

| 項目 | 内容 |
|------|------|
| 言語・バージョン | Python 3.12(CPython、SOUP-001 予定) |
| コーディング規約 | PEP 8、PEP 257(docstring)、本プロジェクト独自は後続 CR-0004 予定(`coding_standards.md` 新規) |
| 静的解析(必須) | `ruff check --select ALL`(警告 0)、`ruff format --check`、`pylint`(指摘ゼロまたは正当化コメント)、`mypy --strict`(型エラー 0)、`bandit -ll`(セキュリティ指摘 0)|
| 静的解析(補助) | SBOM 生成(`pip-audit`)、依存脆弱性 0 件 |
| コードレビュー | PR 経由のセルフレビュー(単独開発下の独立性擬制 — SCMP §4.1.1、CCB §4.1.1)+ 自己レビューチェックリスト(PR テンプレート埋込) |
| 開発手法 | **TDD(Red-Green-Refactor)**:UT を先に書き、Red(失敗)→ 最小実装で Green(合格)→ Refactor(整形・重複排除)の順 |
| コミット粒度 | 1 ユニット 1 ブランチ(`feat/unit-NNN-xxx`)推奨、小さなリファクタは別コミット |
| エディタ設定 | EditorConfig(CI 検証、行末改行・インデント統一) |

### 3.2 実装対象ユニット一覧

| ユニット ID | 名称 | ARCH | 安全クラス | SDD 参照 | 予定ソースファイル |
|------------|------|------|-----------|---------|------------------|
| UNIT-001.1 | State Machine | ARCH-001 | C | §4.1(v0.1) | `src/vip_ctrl/state_machine.py` |
| UNIT-001.2 | Control Loop | ARCH-001 | C | §4.6(v0.2) | `src/vip_ctrl/control_loop.py` |
| UNIT-001.3 | Command Handler | ARCH-001 | C | §4.7(v0.2) | `src/vip_ctrl/command_handler.py` |
| UNIT-001.4 | Flow Command Validator | ARCH-001 | C | §4.2(v0.1) | `src/vip_ctrl/flow_validator.py` |
| UNIT-001.5 | Watchdog (SW side) | ARCH-001 | C | §4.8(v0.2) | `src/vip_ctrl/watchdog.py` |
| UNIT-002.1 | Pump Simulator | ARCH-002 | C | §4.9(v0.2) | `src/vip_sim/pump.py` |
| UNIT-002.2 | Pump Observer | ARCH-002 | C | §4.10(v0.2) | `src/vip_sim/observer.py` |
| UNIT-002.3 | Event Injection Stub | ARCH-002 | C(本版スタブ) | §4.11(v0.2) | `src/vip_sim/event_injection.py` |
| UNIT-002.4 | HW-side Failsafe Timer | ARCH-002 | C | §4.3(v0.1) | `src/vip_sim/failsafe_timer.py` |
| UNIT-003.1 | Serializer | ARCH-003 | C | §4.12(v0.2) | `src/vip_persist/serializer.py` |
| UNIT-003.2 | Checksum Verifier | ARCH-003 | C | §4.13(v0.2) | `src/vip_persist/checksum.py` |
| UNIT-003.3 | Atomic File Writer | ARCH-003 | C | §4.4(v0.1) | `src/vip_persist/atomic_writer.py` |
| UNIT-004.1 | Integrity Validator | ARCH-004 | C | §4.5(v0.1) | `src/vip_integrity/validator.py` |
| UNIT-004.2 | Resume Confirmation Gate | ARCH-004 | C | §4.14(v0.2) | `src/vip_integrity/resume_gate.py` |
| UNIT-005.1 | Control API | ARCH-005 | C | §4.15(v0.2) | `src/vip_api/control.py` |
| UNIT-005.2 | State Observer API | ARCH-005 | C | §4.16(v0.2) | `src/vip_api/observer.py` |
| UNIT-005.3 | Validation API | ARCH-005 | **B(分離対象、SEP-001)** | §4.17(v0.2) | `src/vip_api_b/validation.py` |

> **SEP-001(論理的分離):** UNIT-005.3 は物理分離不可(単一プロセス Python)のため、SAD §9 の定める **論理的分離**(抽象 I/F・一方向依存・frozen データ・静的解析ルール)で担保する。具体手段として本 UT 計画では `src/vip_api_b/` サブパッケージを分離境界とし、`mypy --strict` で相互依存の禁止を機械検証する。

## 4. ソフトウェアユニット検証プロセスの確立(箇条 5.5.2)

### 4.1 検証方法

| 方法 | 適用範囲 | ツール |
|------|---------|-------|
| 静的解析(型) | 全ユニット | `mypy --strict` |
| 静的解析(lint) | 全ユニット | `ruff check --select ALL`、`pylint` |
| 静的解析(セキュリティ) | 全ユニット | `bandit -ll` |
| フォーマッタ | 全ユニット | `ruff format --check` |
| ユニット試験(正常系・境界値・異常系) | 全ユニット | `pytest`(SOUP-002 予定)|
| プロパティベース試験 | RCM 関連・状態機械・整合性検証 | `hypothesis`(SOUP-004 予定)|
| 並行性試験 | スレッド競合が存在するユニット | `pytest` + `threading` / `concurrent.futures` + `pytest-timeout` |
| タイミング試験 | SRS-P01〜P07 に紐づくユニット | `pytest` + `pytest-benchmark`(SOUP 候補、採択は Step 19 B で決定) |
| 網羅率計測 | 全ユニット | `pytest-cov`(SOUP-003 予定)|
| コードレビュー | 全ユニット | PR テンプレート + CI 自動 lint |

### 4.2 本プロジェクト固有の検証強化

- **RCM 実装箇所の MC/DC:** RCM-001/003/004/015/016/019 が実装されるユニット(UNIT-001.1、001.4、001.5、002.4、004.1)は **MC/DC 100%** を目標(§7.4 参照)。
- **プロパティ試験の対象拡張:** UNIT-001.1 State Machine は宣言的遷移表を持つため、hypothesis により「任意のイベント列から到達可能な状態のみが出現する」ことをプロパティで検証。UNIT-004.1 Integrity Validator は破損注入に対する頑健性を hypothesis で広範に検証。
- **並行性試験の必須化:** UNIT-001.1、001.2、001.5、002.4 は複数スレッドから呼出されうるため、`pytest` の `threading` を使った競合試験を必須化。
- **SEP-001 境界の静的検証:** UNIT-005.3(クラス B 分離)と他ユニット(クラス C)との依存方向を `mypy` インポートグラフで検証。B → C への上向き依存は許容、C → B は禁止。

## 5. ソフトウェアユニット受入基準(箇条 5.5.3)

各ユニットは以下の基準を **全て** 満たすことを受入条件とする:

1. **詳細設計との一致:** SDD-VIP-001 v0.2 §4.X の公開 API・データ構造・アルゴリズムと実装が一致している(公開 API のシグネチャ・事前/事後条件・エラー処理が §4.X.A および §4.X.1 と一致)
2. **コーディング規約違反なし:** PEP 8、`ruff check --select ALL`、`pylint`、`mypy --strict`、`bandit` の全てで指摘 0 件(もしくは正当化コメント付き)
3. **ユニット試験の合格:** 本書 §7 に記載された全試験ケースが Pass、本書 §6 のクラス C 追加基準の網羅確認が完了
4. **網羅率達成:** 本書 §7.4 のカバレッジ目標達成
5. **レビュー記録の保存:** PR に自己レビューチェックリストの記入済、CI 全 Pass のエビデンスを PR コメント・GitHub Actions ログとして保存

## 6. 追加のユニット受入基準(箇条 5.5.4 ― クラス C)

クラス C では IEC 62304 §5.5.4 に基づき、以下 9 項目を **全ユニット** で網羅的に確認する。各ユニット実装完了時のチェックリストとして機能する。

- [ ] **正常系の動作確認:** 正常入力で期待出力が得られること
- [ ] **境界値試験:** 入力値域の最小・最大・境界±1(数値域、コレクション長、文字列長、列挙値)
- [ ] **異常系・エラー入力:** 値域外、NULL/None、不正状態からの呼出、型不整合(mypy でも補完)
- [ ] **資源使用:** メモリ(固定上限ユニットでは定数検証)、ファイルハンドラ、ロック、キュー長
- [ ] **制御フロー網羅:** 分岐網羅 100%(全ユニット)、RCM 関連は MC/DC 100%
- [ ] **データフロー:** 未初期化変数(Python では `UnboundLocalError` テスト)・未使用定義の排除(`ruff` で機械検証)
- [ ] **ハードウェア障害・ソフトウェア障害:** 仮想 HW 障害(Pump Simulator の強制フェイルセーフ、Event Injection Stub 経由の障害注入)・SW 障害(永続化キュー満杯、ファイル破損、クロック逆転)の検出と処置が設計どおり
- [ ] **並行処理:** 競合・デッドロック・優先度逆転(Python の場合 GIL 下でも race condition は起こる、`threading.RLock` の挙動含む)
- [ ] **タイミング:** タイムアウト(SW WDT 500 ms、HW Failsafe 500 ms)・制御サイクル(100 ms ±10%、SRS-P02)・応答時間(start ≤ 100 ms・stop ≤ 50 ms、SRS-P03/P04)が規定時間内

> 本チェックリストは各ユニットの第 II 部(報告)で個別に記入する。未達項目は §8.5 で正当化または是正計画を記載する。

## 7. ソフトウェアユニット試験(箇条 5.5.5)

### 7.1 試験環境

| 項目 | 内容 |
|------|------|
| ホスト OS | macOS / Linux(CI: `ubuntu-latest` / GitHub Actions) |
| Python バージョン | 3.12.x(CPython、SOUP-001 予定)、必要に応じて 3.11 も並行試験(CI マトリクス候補) |
| 仮想環境 | `venv` または `uv`(`requirements.txt` / `pyproject.toml` 管理) |
| 試験フレームワーク | `pytest`(SOUP-002 予定) |
| 網羅率計測 | `pytest-cov`(SOUP-003 予定、HTML + terminal 出力、CI アーティファクトとして保存) |
| プロパティ試験 | `hypothesis`(SOUP-004 予定) |
| 並行性試験補助 | `pytest-timeout`、`pytest-xdist`(並列実行、実 CPU ≥ 2 で) |
| ターゲット環境 | **なし**(仮想製品のため実機なし、ホスト環境 = ターゲット環境) |
| CI 実行 | `.github/workflows/unit-test.yml`(Step 19 B で新規追加予定、`docs-check.yml` と分離) |

### 7.2 試験 ID 体系

UT-ID 形式: **`UT-{UNIT連番}.{サブ連番}-{試験ケース連番2桁}`**

例:
- `UT-001.1-01` = UNIT-001.1(State Machine)の試験ケース 01
- `UT-004.1-12` = UNIT-004.1(Integrity Validator)の試験ケース 12

種別タグ(試験ケース記述の `種別` 欄):

| タグ | 意味 |
|------|------|
| 正常系 | 期待される正常入力での動作確認 |
| 境界値 | 値域の最小・最大・境界±1 |
| 異常系 | 値域外、NULL/None、不正状態、型不整合 |
| RCM | RCM 実装の動作確認(正しく防御できるか) |
| 並行 | 複数スレッド・プロセスからの競合試験 |
| タイミング | 時間制約(WDT、制御サイクル、応答時間)の試験 |
| プロパティ | hypothesis によるプロパティベース試験 |
| 資源 | メモリ・ファイルハンドラ・キュー長等の資源使用確認 |
| 分離 | SEP-001 境界(クラス B/C)の静的/動的検証 |

### 7.3 試験ケース定義

本 v0.1 では、**代表 5 ユニット(UNIT-001.1、001.4、002.4、003.3、004.1)** について試験ケースを詳細記述し、**残 12 ユニット** は試験観点とケース数目安のみを骨格記述する。Step 19 B(実装着手)で各ユニットに入る際、対応する UT を TDD の Red フェーズで詳細化する。

#### 7.3.1 UNIT-001.1 State Machine(代表・詳細)

**関連 SRS:** SRS-020, SRS-021, SRS-025, SRS-RCM-020(+ RCM-019)、**関連 RCM:** RCM-019、**関連 HZ:** HZ-001, HZ-002(状態誤認から流量誤制御への波及経路)

| 試験 ID | 対象 API / 観点 | 入力 / 条件 | 期待結果 | 種別 |
|---------|---------------|-----------|---------|------|
| UT-001.1-01 | `current()` 初期値 | 生成直後 | `INITIALIZING` | 正常系 |
| UT-001.1-02 | `set_initial(IDLE, False)` 正常遷移 | `current() == INITIALIZING` | 状態 `IDLE`、`needs_resume_confirm == False` | 正常系 |
| UT-001.1-03 | `set_initial` 二重呼出 | 既に IDLE | `InvalidInitializationError` 送出、状態不変 | 異常系 |
| UT-001.1-04 | `request_transition` 遷移表全エントリ(Pass 側) | TRANSITION_TABLE の 14 エントリ × 2 方向 | 各 `Ok(new_state)`、状態・タイムスタンプ更新、永続化キュー投入 | 正常系 |
| UT-001.1-05 | `request_transition` 不正遷移拒否 | 非対応の(状態, イベント)組合せ(全 6 状態 × 全 イベント - 14 = 多数) | `Err(InvalidTransitionError)`、状態不変、ログ出力 | RCM(RCM-019) |
| UT-001.1-06 | `on_watchdog_timeout` | 任意状態で呼出 | `current() == ERROR`、`_error_reason` 記録 | RCM |
| UT-001.1-07 | `on_watchdog_timeout` 冪等性 | 既に ERROR で再呼出 | 最初の reason を保持、二度目の更新なし | 正常系 |
| UT-001.1-08 | 永続化キュー満杯 | `_persistence_queue` を事前に満杯にする(モック) | ERROR 遷移、ログ記録 | 異常系 |
| UT-001.1-09 | ロック取得タイムアウト | `_lock` を他スレッドで 200 ms 保持 | `StateLockTimeout` 例外、呼出元で ERROR 誘発 | 異常系・並行 |
| UT-001.1-10 | 並行 `request_transition` | 10 スレッドから同時に有効遷移要求 | 状態不整合なし(最終状態は遷移表に従う)、競合ログなし | 並行 |
| UT-001.1-11 | プロパティ:到達可能状態の閉包 | hypothesis:任意長(≤ 100)のイベント列 | 出現状態は TRANSITION_TABLE から到達可能なもののみ | プロパティ |
| UT-001.1-12 | プロパティ:冪等ガード | hypothesis:同一イベント連続適用 | 2 回目以降は状態不変 or 不正遷移拒否 | プロパティ |

**ケース数目安:** 正常系 6、境界値 0(列挙型のため)、異常系 4、RCM 2、並行 1、プロパティ 2、資源 1 = **合計 ≥ 16**
**MC/DC 目標:** 100%(RCM-019、状態遷移表の全条件分岐)

#### 7.3.2 UNIT-001.4 Flow Command Validator(代表・詳細)

**関連 SRS:** SRS-O-001, SRS-RCM-001, SRS-005、**関連 RCM:** RCM-001、**関連 HZ:** HZ-001(過量投与)、HZ-002(過少投与)

> **Step 19 B3 整合化(2026-04-23、本節 v0.3):** v0.2 までの本節は UTPR 初版(Step 19 A)で SRS/SDD クロスレビューが不十分だったため、(a) 指令値域を **設定値域** と誤記(SRS-O-001 では指令値域は `0.0 ≤ value ≤ 1200.0`、設定値域 SRS-I-001 とは異なる)、(b) ValidationReason 名が SDD §4.2.B の enum 名と不一致(`OutOfRangeError` 等の擬似名)、(c) 設定値整合性検証が `state == State.RUNNING` のときのみ発火する SDD §4.2.C の前提を未明示、の 3 点で SRS-O-001 / SRS-RCM-001 / SDD §4.2 と齟齬していた。本節を SRS/SDD に整合化(MINOR 区分、CR 不要、SRS/SDD/RMF/SAD は不変)。教訓は DEVELOPMENT_STEPS §教訓「UTPR v0.1 作成時の SRS/SDD クロスレビュー漏れ」に記録。

| 試験 ID | 対象 API / 観点 | 入力 / 条件 | 期待結果 | 種別 |
|---------|---------------|-----------|---------|------|
| UT-001.4-01 | `validate(cmd, ctx)` 正常範囲内 | 流量 = 100 mL/h、設定 = 100、`state=RUNNING` | `ValidationOk(validated)` | 正常系 |
| UT-001.4-02 | 範囲最小境界(指令最小、停止指令を含む) | 流量 = 0.0 mL/h、`state=STOPPED`(設定値検証スキップ) | `ValidationOk` | 境界値 |
| UT-001.4-03 | 範囲最大境界 | 流量 = 1200.0 mL/h、設定 = 1200.0、`state=RUNNING` | `ValidationOk` | 境界値 |
| UT-001.4-04 | 範囲下限 - ε(負側) | 流量 = -0.01 mL/h | `ValidationErr(NEGATIVE)` | RCM(RCM-001) |
| UT-001.4-05 | 範囲上限 + ε | 流量 = 1200.01 mL/h | `ValidationErr(OUT_OF_RANGE)` | RCM |
| UT-001.4-06 | 負値 | 流量 = -1 mL/h | `ValidationErr(NEGATIVE)` | 異常系 |
| UT-001.4-07 | NaN / +Inf / -Inf | 流量 = `Decimal('NaN')` / `Decimal('Infinity')` / `Decimal('-Infinity')` | `ValidationErr(NAN_OR_INFINITE)` | 異常系 |
| UT-001.4-08 | 設定値との不一致(許容誤差超)、`state=RUNNING` | 流量 = 100、設定 = 50(SRS-005 許容誤差 ±5% 超) | `ValidationErr(MISMATCH_WITH_SETTINGS)` | RCM |
| UT-001.4-09 | 設定値との不一致(許容誤差内)、`state=RUNNING` | 流量 = 102、設定 = 100(+2% 以内、および境界 +5.00%) | `ValidationOk` | 正常系 |
| UT-001.4-10 | プロパティ:`state=STOPPED` で範囲内は常に Ok | hypothesis:`0.0 ≤ rate ≤ 1200.0`(設定値検証スキップ) | `ValidationOk` | プロパティ |
| UT-001.4-11 | プロパティ:範囲外は常に Err | hypothesis:`rate < 0.0` or `rate > 1200.0` | `ValidationErr` | プロパティ |
| UT-001.4-12 | Decimal 入力(精度 2 桁保持) | `Decimal("100.00")` | `ValidationOk`、`flow_rate.as_tuple().exponent == -2` | 正常系 |

**展開実装(Step 19 B3 時点、`tests/unit/test_flow_validator.py`):**

- UT-001.4-07 を NaN / +Inf / -Inf の 3 サブケースに `pytest.parametrize` 展開
- UT-001.4-09 を「±2% 以内」「±5.00% 境界」「+5.01%(MISMATCH 側)」の 3 サブケースに展開
- 補助観点:`state ∈ {INITIALIZING, IDLE, PAUSED, STOPPED, ERROR}` で設定値検証がスキップされることを 5 状態 × 1 件で網羅(RCM-001 の状態依存分岐 MC/DC を試験設計で担保)
- 補助観点:純粋性(同一入力 2 回呼出の冪等)、frozen 検証(4 dataclass)、範囲定数(MIN/MAX)
- `hypothesis` は `max_examples=200, deadline=None` でプロパティ 2 件を実行
- **実測ケース数 34 件、全 Pass(2026-04-23)**

**ケース数目安:** 正常系 3、境界値 2、異常系 2、RCM 3、プロパティ 2 = **合計 ≥ 12**(展開後 34)
**MC/DC 目標:** 100%(RCM-001、範囲チェック + 設定値整合性の複合条件)

#### 7.3.3 UNIT-002.4 HW-side Failsafe Timer(代表・詳細)

**関連 SRS:** SRS-RCM-004, SRS-032、**関連 RCM:** RCM-004(HW 側)、**関連 HZ:** HZ-001, HZ-002(SW 停止時の過量継続)

| 試験 ID | 対象 API / 観点 | 入力 / 条件 | 期待結果 | 種別 |
|---------|---------------|-----------|---------|------|
| UT-002.4-01 | `heartbeat()` 正常受信 | 毎 100 ms で呼出 | タイマ未発火 | 正常系 |
| UT-002.4-02 | ハートビート途絶検知 | 最終 heartbeat から 500 ms 経過 | `force_stop_failsafe()` が Pump Simulator で呼出される | RCM(RCM-004 HW 側) |
| UT-002.4-03 | 境界:499 ms | タイマ精度内 | 発火しない | 境界値 |
| UT-002.4-04 | 境界:500 ms(+ ε) | 500 ms 超過 | 発火する | 境界値 |
| UT-002.4-05 | 複数スレッドからの heartbeat | 2 スレッドが同時に呼出 | 競合せず最新タイムスタンプが記録 | 並行 |
| UT-002.4-06 | 二重冗長動作 | SW WDT(UNIT-001.5)が発火前に停止しない状況で、本ユニットが独立に発火 | Pump Simulator が強制停止、ログに「HW failsafe triggered」記録 | RCM・タイミング |
| UT-002.4-07 | クロック逆転 | モックで時刻を後退させる | 異常検知、安全側に倒す(発火または ERROR 誘発) | 異常系 |
| UT-002.4-08 | タイマ停止後の heartbeat | `force_stop_failsafe` 後 | タイマは再開しない(冪等) | 正常系 |

**ケース数目安:** 正常系 2、境界値 2、異常系 1、RCM 2、並行 1、タイミング 1 = **合計 ≥ 9**
**MC/DC 目標:** 100%(RCM-004 HW 側、ハートビート判定)

#### 7.3.4 UNIT-003.3 Atomic File Writer(代表・詳細)

**関連 SRS:** SRS-DATA-002, SRS-DATA-003、**関連 RCM:** RCM-015 前提、**関連 HZ:** HZ-007(永続化破損)

| 試験 ID | 対象 API / 観点 | 入力 / 条件 | 期待結果 | 種別 |
|---------|---------------|-----------|---------|------|
| UT-003.3-01 | `write_atomic(path, data)` 新規書込 | 存在しないパス | ファイル生成、内容一致 | 正常系 |
| UT-003.3-02 | 上書き | 既存ファイル | 原子的に置換(途中状態が観測されない) | 正常系 |
| UT-003.3-03 | 一時ファイル残存確認 | 正常終了時 | `.tmp` が残らない | 正常系 |
| UT-003.3-04 | 書込中の例外(モック `os.rename` 失敗) | 書込途中で失敗を注入 | 元ファイル不変、`.tmp` がクリーンアップ対象に | 異常系 |
| UT-003.3-05 | 空データ書込 | `data = b""` | 空ファイル生成 | 境界値 |
| UT-003.3-06 | 大容量書込 | `data = b"x" * 10**6`(1 MB) | 正常終了、メモリリークなし | 境界値・資源 |
| UT-003.3-07 | 並行書込(同一パス) | 2 スレッドが同時に書込 | 一方成功、他方失敗(ロック機構動作)、ファイルは必ず一方の内容 | 並行 |
| UT-003.3-08 | ディスクフル(モック) | `OSError(ENOSPC)` 注入 | `Err(DiskFullError)` | 異常系 |
| UT-003.3-09 | 読込専用ディレクトリ | 書込不可パス | `Err(PermissionError)`、元ファイル不変 | 異常系 |
| UT-003.3-10 | 書込中の電源断シミュレーション | `os.fsync` 直前で SIGKILL 注入(サブプロセス試験) | 元ファイルが保持されている(原子性) | RCM 前提・異常系 |

**ケース数目安:** 正常系 3、境界値 2、異常系 3、並行 1、RCM 前提 1 = **合計 ≥ 10**
**MC/DC 目標:** 95%(RCM 前提、直接の RCM 実装ではないため)

#### 7.3.5 UNIT-004.1 Integrity Validator(代表・詳細)

**関連 SRS:** SRS-026, SRS-027, SRS-RCM-015、**関連 RCM:** RCM-015、**関連 HZ:** HZ-007

| 試験 ID | 対象 API / 観点 | 入力 / 条件 | 期待結果 | 種別 |
|---------|---------------|-----------|---------|------|
| UT-004.1-01 | `validate(snapshot)` 正常 | 完全な RuntimeState、checksum 一致 | `Ok(snapshot)` | 正常系 |
| UT-004.1-02 | checksum 不一致 | 同一データで checksum のみ改竄 | `Err([ChecksumMismatch])` | RCM(RCM-015) |
| UT-004.1-03 | 型不整合 | `flow_rate` フィールドが文字列 | `Err([TypeError])` | 異常系 |
| UT-004.1-04 | 必須フィールド欠落 | `state` フィールドなし | `Err([MissingField("state")])` | 異常系 |
| UT-004.1-05 | 値域外フィールド | `flow_rate = -1` | `Err([OutOfRange("flow_rate")])` | 異常系 |
| UT-004.1-06 | 複数エラーの列挙 | checksum 不一致 + 値域外 | `Err([ChecksumMismatch, OutOfRange])`(複合) | RCM |
| UT-004.1-07 | 破損注入(ランダムビット反転) | hypothesis:バイト列の 1 ビットを反転 | 100% の反転パターンで `Err` を返す | プロパティ・RCM |
| UT-004.1-08 | 空スナップショット | `b""` / `None` | `Err([Empty])` | 異常系 |
| UT-004.1-09 | タイムスタンプ未来(クロック逆転) | snapshot.ts > now + 1 分 | `Err([FutureTimestamp])` | RCM |
| UT-004.1-10 | 不変条件違反 | state == ERROR ∧ error_reason == None | `Err([InvariantViolation])` | RCM |
| UT-004.1-11 | プロパティ:正常 snapshot は常に Ok | hypothesis 生成器で正常値域のみ | `Ok` | プロパティ |
| UT-004.1-12 | プロパティ:2 箇所以上破損 → 常に Err | hypothesis:≥ 2 フィールド破損 | `Err(≥ 1 エラー列挙)` | プロパティ・RCM |

**ケース数目安:** 正常系 1、境界値 0、異常系 4、RCM 3、プロパティ 3 = **合計 ≥ 12**
**MC/DC 目標:** 100%(RCM-015、整合性検証の複合条件)

#### 7.3.6 残 12 ユニット骨格(Step 19 B の TDD Red で詳細化)

| ユニット ID | 主要試験観点 | ケース数目安 | MC/DC 目標 | 備考 |
|------------|-----------|-----------|-----------|------|
| UNIT-001.2 Control Loop | タイミング(100 ms 周期 ±10%、SRS-P02)、heartbeat 送出、SRS-031 自動停止判定、ERROR 誘発、並行 | ≥ 12 | 100%(RCM-004 SW 側送出)| `pytest-benchmark` でサイクル計測 |
| UNIT-001.3 Command Handler | コマンドキュー、stop ファストパス(SRS-P04 ≤ 50 ms)、順次処理、境界値 | ≥ 10 | 95% | stop ファストパスの応答時間計測必須 |
| UNIT-001.5 Watchdog (SW side) | 500 ms 判定(境界 499/500/501)、冪等、並行、クロック逆転 | ≥ 8 | 100%(RCM-003)| |
| UNIT-002.1 Pump Simulator | 指令反映、`force_stop_failsafe` 冪等、SRS-030/031 準拠、積算量計算 | ≥ 10 | 95% | `force_stop_failsafe` は RCM-004 HW 側の被呼出側 |
| UNIT-002.2 Pump Observer | 観測 API の不変性(pure)、状態整合性 | ≥ 6 | — | 観測のみ、RCM なし |
| UNIT-002.3 Event Injection Stub | Inc.2 以降のスタブ、本 Inc.1 では空動作の確認のみ | ≥ 3 | — | Inc.2 着手時に拡張 |
| UNIT-003.1 Serializer | 正常 / 破損検出、ラウンドトリップ、型保証、プロパティ(対称性)| ≥ 8 | 95%(RCM-015 前提)| hypothesis 適用 |
| UNIT-003.2 Checksum Verifier | 既知ベクタ、衝突試験(SEC-001)、hashlib 委譲 | ≥ 6 | 95%(RCM-015 構成要素)| |
| UNIT-004.2 Resume Confirmation Gate | needs_confirm トグル、期限チェック、状態遷移連携 | ≥ 8 | 100%(RCM-016)| |
| UNIT-005.1 Control API | 7 コマンド(start/stop/pause/resume/reset/error_reset/confirm_resume)の委譲、例外伝搬 | ≥ 10 | 90% | 委譲先の mock 検証主体 |
| UNIT-005.2 State Observer API | 薄いラッパー、observer 委譲、非 block | ≥ 6 | — | |
| UNIT-005.3 Validation API(クラス B) | **SEP-001 分離検証**、内部例外握りつぶし契約、境界値 | ≥ 8 | 90% | `mypy` でインポートグラフ分離を機械検証 |

**合計ケース数目安(全 17 ユニット):** **≥ 145 件**(代表 5 = 59 件 + 骨格 12 = 95 件の目安)。最終的な件数は Step 19 B の TDD で増減する見込み。

### 7.4 カバレッジ目標

| 指標 | 目標値 | 適用範囲 |
|------|-------|---------|
| ステートメント網羅(line / statement) | **100%** | 全ユニット(クラス C) |
| 分岐網羅(decision / branch) | **100%** | 全ユニット(クラス C) |
| **MC/DC** | **100%** | RCM 実装ユニット(UNIT-001.1, 001.4, 001.5, 002.4, 004.1, 004.2) |
| MC/DC | 95% 以上 | その他クラス C ユニット |
| MC/DC | 90% 以上 | クラス B 分離ユニット(UNIT-005.3) |

> 未達成時は §8.5 で正当化(例:防御的コード、到達不可能な分岐)または是正計画を記載する。SDD §5.4.4 検証方法で要求された観点を全て UT-ID に展開済であることが、網羅性の **質的保証** となる。

## 8. 問題発見時の手続

UT 実施中に発見された問題は、**重大度に応じて** 以下の手続で処理する:

- **Critical / Major(RCM 機能不全、安全関連):** 即座に SPRP-VIP-001 §X の PRB-NNNN として起票、Inc.1 リリース前に解消必須
- **Minor(受入基準未達、軽微挙動差):** PRB-NNNN 起票、是正計画を §8.5 に記載、Inc.1 リリース時に残留異常として記録可(要 CCB 承認)
- **設計不整合(SDD と実装の乖離):** CR-NNNN 起票(MODERATE 以上)、SDD 改訂と UT 再設計を合わせて実施
- **要求不整合(SRS の曖昧さ発見):** CR-NNNN 起票、Step 14a 教訓「詳細設計が要求を完成させる」パターン再応用。凍結済 SRS への改訂は SCMP §4.1 に従う

本節は §5.5.6(問題発見時の処置)に対応する。

---

# 第 II 部 報告

> **Inc.1 実装(Step 19 B 以降)実施時に本部を記入する。v0.1 時点では骨格のみ。**

## 9. 試験実施結果

### 9.1 実施サマリ

- 実施期間: *(Inc.1 実装中、随時記入)*
- 実施者: k-abe
- ソフトウェアバージョン(コミット): *(各 UT Pass 時点の SHA を記入)*
- 試験環境バージョン: Python 3.12.x、pytest 最新安定、hypothesis 最新安定、pytest-cov 最新安定
- CI ジョブ: `.github/workflows/unit-test.yml` の Run ID

### 9.2 試験ケース結果(骨格、ユニット単位で随時記入)

| ユニット ID | 試験 ID 総数 | Pass | Fail | Skip | カバレッジ(stmt / branch / MC/DC) | 実施日 | コミット SHA |
|------------|----------|------|------|------|--------------------------|-------|-----------|
| UNIT-001.1 | **62**(うち UT-001.1-01..12 = 12 + パラメータ化展開 45 + スモーク 5)| **62** | 0 | 0 | **100.00% / 100.00% / 100%(MC/DC 目視確認、RCM-019 全分岐)** | 2026-04-23 | Step 19 B2 PR マージコミット `27dd1cd`(マージ後 SHA は `git log` 参照)|
| UNIT-001.2 | ≥ 12 | — | — | — | — | — | — |
| UNIT-001.3 | ≥ 10 | — | — | — | — | — | — |
| UNIT-001.4 | **34**(うち UT-001.4-01..12 = 12 + パラメータ化展開 14 + 補助観点 8)| **34** | 0 | 0 | **100.00% / 100.00% / 100%(MC/DC 試験設計担保、RCM-001 範囲 + 設定値整合性 + 状態別スキップ全分岐)** | 2026-04-23 | Step 19 B3 PR マージコミット(TBD)|
| UNIT-001.5 | ≥ 8 | — | — | — | — | — | — |
| UNIT-002.1 | ≥ 10 | — | — | — | — | — | — |
| UNIT-002.2 | ≥ 6 | — | — | — | — | — | — |
| UNIT-002.3 | ≥ 3 | — | — | — | — | — | — |
| UNIT-002.4 | ≥ 9 | — | — | — | — | — | — |
| UNIT-003.1 | ≥ 8 | — | — | — | — | — | — |
| UNIT-003.2 | ≥ 6 | — | — | — | — | — | — |
| UNIT-003.3 | ≥ 10 | — | — | — | — | — | — |
| UNIT-004.1 | ≥ 12 | — | — | — | — | — | — |
| UNIT-004.2 | ≥ 8 | — | — | — | — | — | — |
| UNIT-005.1 | ≥ 10 | — | — | — | — | — | — |
| UNIT-005.2 | ≥ 6 | — | — | — | — | — | — |
| UNIT-005.3 | ≥ 8 | — | — | — | — | — | — |
| **合計** | **≥ 145** | — | — | — | **— / — / —** | — | — |

### 9.3 不具合・逸脱

| 問題 ID(PRB) | 発見 UT-ID | 内容 | 重大度 | 対応 | ステータス |
|----------------|----------|------|-------|------|----------|
| — | — | — | — | — | — |

### 9.4 未達項目と処置

*(v0.1 時点では未記入。Inc.1 実装完了時に、カバレッジ目標未達分や防御的コードの正当化を記載する。)*

## 10. 結論

- [ ] 全 17 ユニットが受入基準(§5)を満たしている
- [ ] クラス C 追加基準(§6)全 9 項目を網羅
- [ ] §7.4 カバレッジ目標を達成
- [ ] 未解決問題は既知の残留異常として SMS-VIP-001(§5.8)に記載する

## 11. トレーサビリティマトリクス

| ユニット ID | 試験 ID | 関連 SRS | 関連 RCM | 関連 HZ | 結果 |
|------------|--------|---------|---------|---------|------|
| UNIT-001.1 State Machine | UT-001.1-01 〜 UT-001.1-12 | SRS-020, 021, 025, SRS-RCM-020, SRS-ALM-003 | RCM-019 | HZ-001, HZ-002 | **Pass(100 tests / 100.00% stmt / 100.00% branch / MC/DC 100%、Step 19 B2、2026-04-23)** |
| UNIT-001.2 Control Loop | UT-001.2-01 〜(≥ 12) | SRS-011, 012, 031, SRS-P02, SRS-RCM-004 | RCM-004(SW 送出)| HZ-001, HZ-002 | 未実施 |
| UNIT-001.3 Command Handler | UT-001.3-01 〜(≥ 10) | SRS-010, 013, 014, SRS-P03, SRS-P04 | —(State Machine と連携)| HZ-001, HZ-002 | 未実施 |
| UNIT-001.4 Flow Command Validator | UT-001.4-01 〜 UT-001.4-12 | SRS-O-001, SRS-RCM-001, SRS-005 | RCM-001 | HZ-001, HZ-002 | **Pass(34 tests / 100.00% stmt / 100.00% branch / MC/DC 100%、Step 19 B3、2026-04-23)** |
| UNIT-001.5 Watchdog (SW) | UT-001.5-01 〜(≥ 8) | SRS-RCM-003 | RCM-003 | HZ-001, HZ-002 | 未実施 |
| UNIT-002.1 Pump Simulator | UT-002.1-01 〜(≥ 10) | SRS-030, 031, SRS-P01 | RCM-004(HW 被呼出側)| HZ-001, HZ-002 | 未実施 |
| UNIT-002.2 Pump Observer | UT-002.2-01 〜(≥ 6) | SRS-031, SRS-I-020 | — | — | 未実施 |
| UNIT-002.3 Event Injection Stub | UT-002.3-01 〜(≥ 3) | SRS-032, SRS-I-040(Inc.2)| —(Inc.2 で追加)| HZ-004 | 未実施 |
| UNIT-002.4 HW-side Failsafe Timer | UT-002.4-01 〜 UT-002.4-08 | SRS-RCM-004, SRS-032 | RCM-004(HW 側)| HZ-001, HZ-002 | 未実施 |
| UNIT-003.1 Serializer | UT-003.1-01 〜(≥ 8) | SRS-DATA-001, 004 | RCM-015 前提 | HZ-007 | 未実施 |
| UNIT-003.2 Checksum Verifier | UT-003.2-01 〜(≥ 6) | SRS-SEC-001 | RCM-015 構成要素 | HZ-007 | 未実施 |
| UNIT-003.3 Atomic File Writer | UT-003.3-01 〜 UT-003.3-10 | SRS-DATA-002, 003 | RCM-015 前提 | HZ-007 | 未実施 |
| UNIT-004.1 Integrity Validator | UT-004.1-01 〜 UT-004.1-12 | SRS-026, 027, SRS-RCM-015 | RCM-015 | HZ-007 | 未実施 |
| UNIT-004.2 Resume Confirmation Gate | UT-004.2-01 〜(≥ 8) | SRS-028, SRS-RCM-016 | RCM-016 | HZ-007 | 未実施 |
| UNIT-005.1 Control API | UT-005.1-01 〜(≥ 10) | SRS-IF-002, SRS-010〜014 | —(委譲)| HZ-001, HZ-002 | 未実施 |
| UNIT-005.2 State Observer API | UT-005.2-01 〜(≥ 6) | SRS-IF-003, SRS-O-010, SRS-UX-002 | — | — | 未実施 |
| UNIT-005.3 Validation API(クラス B) | UT-005.3-01 〜(≥ 8) | SRS-UX-001, 004, 005 | —(B 分離側)| HZ-008 | 未実施 |

**カバレッジ:** 本マトリクスにより、SDD §3.1 のユニット一覧 17 件全てが UT-ID と紐付き、SRS/RCM/HZ への双方向トレーサビリティが確立した。SRS-VIP-001 §10 の「UT-ID」列(v0.1 時点で空欄)は、本 UTPR v0.1 の成立をもって Inc.1 完了時に充填する計画。

## 12. 改訂履歴

| バージョン | 日付 | 変更内容 | 変更者 |
|----------|------|---------|--------|
| 0.1 | 2026-04-23 | 初版作成(計画、Step 19 A)。Inc.1 の全 17 ユニットに UT-UID(UT-001.1〜UT-005.3)を採番。代表 5 ユニット(UNIT-001.1, 001.4, 002.4, 003.3, 004.1、SDD v0.1 時点で詳細設計された 5 件)について試験ケースを詳細記述(正常系 / 境界値 / 異常系 / RCM / 並行 / タイミング / プロパティ 分類合計 59 件)。残 12 ユニットは試験観点とケース数目安のみ骨格記述(合計目安 ≥ 95 件)。カバレッジ目標を本プロジェクト固有に強化(RCM 実装 6 ユニットで MC/DC 100%)。試験環境、試験 ID 体系、クラス C 追加基準 9 項目(§5.5.4 準拠)、問題発見時の手続(SPRP/CR 連携)を確立。第 II 部(報告)は骨格のみ、Step 19 B 以降の TDD Red-Green-Refactor で埋めていく | k-abe |
| 0.2 | 2026-04-23 | **Step 19 B2(UNIT-001.1 State Machine TDD 実装)の実施結果を第 II 部に反映**。§9.2 UNIT-001.1 行を 62 tests Pass / カバレッジ 100.00%(stmt / branch)/ MC/DC 100%(RCM-019 全分岐)で確定。§11 トレーサビリティマトリクス UNIT-001.1 行の結果欄を「Pass」に更新。他 16 ユニットは未実施のまま据置(Step 19 B2+ 以降で TDD を継続)。UT-001.1-04 パラメータ化展開で TRANSITION_TABLE 全 13 エントリ × Pass 方向を網羅、UT-001.1-05 で (State, EventKind) 非登録全組合せ 45 ケースを網羅(RCM-019 確認)、UT-001.1-11/12 で hypothesis プロパティ試験 2 件を実装 | k-abe |
| 0.3 | 2026-04-23 | **Step 19 B3(UNIT-001.4 Flow Command Validator TDD 実装)の実施結果を反映 + §7.3.2 を SRS/SDD に整合化**。**(1) 第 I 部 §7.3.2 整合化(MINOR、CR 不要):** v0.2 までの本節は (a) 指令値域を「設定値域 0.1〜1200」と誤記(SRS-O-001 では指令値域は `0.0 ≤ value ≤ 1200.0`)、(b) ValidationReason 名が SDD §4.2.B の enum 名と不一致、(c) 設定値整合性検証が `state == State.RUNNING` のときのみ発火する SDD §4.2.C の前提を未明示、の 3 点で齟齬していた。SRS/SDD を真として本節のテーブル(UT-001.4-01〜12)を全面差し替え、整合化注釈を本節冒頭に追記。SRS / SDD / RMF / SAD 本体は不変。**(2) 第 II 部 §9.2:** UNIT-001.4 行を 34 tests Pass / カバレッジ 100.00%(stmt / branch)/ MC/DC 100%(RCM-001 範囲 + 設定値整合性 + 状態別スキップ全分岐、試験設計担保)で確定。§11 トレーサビリティマトリクス UNIT-001.4 行を「Pass」に更新。**(3) 試験設計:** UT-001.4-07 を NaN/+Inf/-Inf 3 サブケース、UT-001.4-09 を ±2%/±5.00% 境界/+5.01% の 3 サブケースに `pytest.parametrize` 展開、補助観点として 5 状態 × 設定値検証スキップ確認 + 純粋性 + frozen 4 件 + 範囲定数 2 件を追加。`hypothesis` プロパティ 2 件は `max_examples=200, deadline=None` で実装。教訓「UTPR v0.1 作成時の SRS/SDD クロスレビュー漏れ」を DEVELOPMENT_STEPS §教訓に記録 | k-abe |
