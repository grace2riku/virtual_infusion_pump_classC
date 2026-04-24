# ソフトウェアユニットテスト計画書/報告書

**ドキュメント ID:** UTPR-VIP-001
**バージョン:** 0.8
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

> **Step 19 B4 整合化(2026-04-23、本節 v0.4):** v0.3 までの本節に対し、SDD §4.3 と並べ読みした結果として 2 件の設計判断と 1 件の表記整合化を行った。**(1) Logger 注入の据置:** SDD §4.3.C 擬似コードに `self._logger.log_failsafe_trip(...)` の呼出があるが §4.3.B データ構造表に `_logger` フィールドが宣言されていないため、本 Inc.1 段階では Logger 注入を行わず、HW 側フェイルセーフ識別子は `force_stop_failsafe(reason="HEARTBEAT_TIMEOUT")` の reason 引数で代替する。Logger 注入は UNIT-004+ で正式化予定。**(2) クロック注入(DI)の採用:** SDD §4.3.B には `_clock` フィールドがないが、UT-002.4-07(クロック逆転試験)を実現するため `clock: Callable[[], float]` をコンストラクタ注入可能にした(本番デフォルトは `time.monotonic`)。**(3) クロック逆転時の挙動:** SDD §4.3.E は `time.monotonic()` の単調増加保証を根拠に未定義としているが、注入クロック経由で逆転が起きた場合の挙動を「安全側 = 発火」と実装判断(RCM-004 の安全側原則 + Step 19 B2 State Machine 「不正は ERROR」と整合)。SRS / SDD / RMF / SAD 本体は不変、教訓は DEVELOPMENT_STEPS §教訓に記録(MINOR 区分・CR 不要)。

| 試験 ID | 対象 API / 観点 | 入力 / 条件 | 期待結果 | 種別 |
|---------|---------------|-----------|---------|------|
| UT-002.4-01 | `heartbeat()` 正常受信 | 100 ms 間隔で 10 回呼出 | `is_tripped() is False` | 正常系 |
| UT-002.4-02 | ハートビート途絶検知 | 最終 heartbeat から 501 ms 経過後 `check_once()` | `is_tripped() is True`、`force_stop_failsafe(reason="HEARTBEAT_TIMEOUT")` 呼出 | RCM(RCM-004 HW 側) |
| UT-002.4-03 | 境界:499 ms | 499 ms 経過後 `check_once()` | 発火しない | 境界値 |
| UT-002.4-04a | 境界:500 ms ちょうど | `(now - last) > timeout` の `>` 判定で発火しない | 発火しない | 境界値 |
| UT-002.4-04b | 境界:500 ms + ε | 500.0001 ms 経過後 `check_once()` | 発火する | 境界値 |
| UT-002.4-05 | 複数スレッドからの heartbeat | 2 スレッドが同時に 50 回ずつ呼出(`Barrier` で同期スタート) | データ競合なし、`last_heartbeat() == fake_clock()` | 並行 |
| UT-002.4-06 | HW failsafe 識別子 | `force_stop_failsafe` がモックで呼出された際の reason 引数を検証 | `reason="HEARTBEAT_TIMEOUT"` で 1 回呼出 | RCM・識別 |
| UT-002.4-07 | クロック逆転(安全側) | 注入 fake_clock で時刻を 0.2 → 0.05 に後退 | 発火する(設計判断:逆転は安全側) | 異常系 |
| UT-002.4-08a | Tripped 後の heartbeat 無視 | `force_stop_failsafe` 後に `heartbeat()` を呼出 | `last_heartbeat()` 不変(無視) | 冪等 |
| UT-002.4-08b | 重複 `check_once()` 冪等 | Tripped 後に `check_once()` を 3 回連続呼出 | `force_stop_failsafe` の呼出回数は 1 回 | 冪等 |

**展開実装(Step 19 B4 時点、`tests/unit/test_failsafe_timer.py`):**

- 上記 10 試験ケースに加え、補助観点として:
  - **start / stop ライフサイクル**: 4 件(start→stop / 二重 start→`RuntimeError` / 二重 stop→no-op / start 前 stop→no-op)
  - **pump 例外時のロバスト性**: 1 件(`force_stop_failsafe` が例外を投げてもタイマ自身はクラッシュせず、`is_tripped()=True` を維持)
  - **定数値**: 2 件(`HEARTBEAT_TIMEOUT == 0.5`、`MONITOR_INTERVAL == 0.1`)
  - **実時間スレッド統合スモーク**: 1 件(発火側、`time.monotonic` + 監視スレッド経由で 1 秒以内に発火することを確認)
- 連打側スモークは macOS の `time.sleep` ジッタで本質的に flaky と判明したため fake_clock 試験(UT-002.4-01 / 05)に委任(教訓 DEVELOPMENT_STEPS §教訓に記録)
- **実測ケース数 18 件、全 Pass(2026-04-23、3 連続実行で stable 確認)**

**ケース数目安:** 正常系 2、境界値 2、異常系 1、RCM 2、並行 1、タイミング 1 = **合計 ≥ 9**(展開後 18)
**MC/DC 目標:** 100%(RCM-004 HW 側、ハートビート判定 + クロック逆転分岐 + Tripped 状態分岐の複合条件)

#### 7.3.4 UNIT-003.3 Atomic File Writer(代表・詳細)

**関連 SRS:** SRS-DATA-002, SRS-DATA-003、**関連 RCM:** RCM-015 前提、**関連 HZ:** HZ-007(永続化破損)

> **Step 19 B5 整合化(2026-04-23、本節 v0.5):** Step 19 B3 / B4 教訓を運用化した着手前クロスレビューで、SDD §4.4 と v0.4 までの本節の間に 4 件の不整合を発見、ユーザー合意のもとで SRS / SDD を真として本節を整合化(MINOR 区分・CR 不要、SRS / SDD / RMF / SAD 本体は不変)。**(1) API 名と引数順:** SDD §4.4.A の `write(data, target_path)` / `read(target_path)` / `rollback(target_path)` の 3 API に統一(UTPR v0.4 までの `write_atomic(path, data)` 単独記述から変更)。**(2) UT-003.3-07 並行書込の前提:** SDD §4.4.C 「並行書き込みは呼出側責任、本ユニットはロックしない」に整合化し、本節では **異なる target_path への並行書込が独立して成功しデッドロック/内部状態破壊が起きない** ことを検証する「ステートレス確認」に変更(UTPR v0.4 までの「ロック機構動作」表現は撤回)。**(3) UT-003.3-08 戻り値型:** 独自型 `Err(DiskFullError)` ではなく SDD §4.4.E 整合の `WriteErr(OSError)` + `error.errno == ENOSPC` で検出するパターンに統一。**(4) UT-003.3-10 電源断シミュレーション:** subprocess + SIGKILL は本 UT 段階では行わず(ファイルシステム挙動差 + プロセス管理 flake のリスク、SDD §4.4.E「原理的に検知不可能 / load 側で整合性検証が担保」にも整合)、ITPR §5.6(将来 Step 19 D)に申し送り。本 UT では SDD §4.4.B の不変条件「target か bak のどちらかが旧データを保持」を内部ステップ観測で検証 + `os.fsync` 呼出をモック記録で検証する形に整合化。

| 試験 ID | 対象 API / 観点 | 入力 / 条件 | 期待結果 | 種別 |
|---------|---------------|-----------|---------|------|
| UT-003.3-01 | `write(data, target_path)` 新規書込 | 存在しないパス | `WriteOk(bytes_written)`、ファイル生成、内容一致 | 正常系 |
| UT-003.3-02 | 上書き(原子性 + 旧データ → bak 退避) | 既存ファイル `target` | `target` 最新内容、`target.bak` に旧内容(SRS-DATA-003 1 世代) | 正常系 |
| UT-003.3-02b | 既存の古い bak は新しい bak に置換 | `target` と `target.bak` の両方が既存 | 新 bak は旧 target 内容に更新、2 世代は保持しない | 正常系 |
| UT-003.3-03 | `.tmp` 残存しない | 正常終了時 | temp サフィックスを持つ兄弟ファイル 0 件 | 正常系 |
| UT-003.3-04 | リネーム失敗時、target 不変 + `.tmp` クリーンアップ | 2 回目の `os.replace`(temp → target)に `OSError(EIO)` 注入 | `WriteErr`、target か bak に旧データ「original」保持、`.tmp` 残存なし | 異常系 |
| UT-003.3-05 | 空データ書込 | `data = b""` | `WriteOk(bytes_written=0)`、空ファイル生成 | 境界値 |
| UT-003.3-06 | 1 MB 大容量書込 | `data = b"x" * 10**6` | `WriteOk(bytes_written=10**6)`、ファイルサイズ一致 | 境界値・資源 |
| UT-003.3-07 | ステートレス確認(並行書込は呼出側責任) | **異なる** target_path への 2 スレッド × 20 回 write | デッドロックなし、各 target は最後の書込内容を保持 | 並行 |
| UT-003.3-08 | ディスクフル(ENOSPC) | `os.fsync` が `OSError(ENOSPC)` を投げる | `WriteErr`、`error.errno == ENOSPC`、target 不在、`.tmp` 残存なし | 異常系 |
| UT-003.3-09 | 読込専用ディレクトリ(PermissionError) | 親ディレクトリを `chmod 0o500` | `WriteErr(OSError)`、元 target 不変 | 異常系 |
| UT-003.3-10a | `os.fsync` 呼出検証 | 通常 write のモック記録 | `os.fsync` が ≥ 1 回呼ばれる(temp fd、POSIX ならディレクトリ fd も) | RCM 前提 |
| UT-003.3-10b | 不変条件(target or bak 常在) | 2 回目の `os.replace` 失敗注入後の状態観測 | target か bak のいずれかから旧データ「original」が復元可能 | RCM 前提・異常系 |

**展開実装(Step 19 B5 時点、`tests/unit/test_atomic_writer.py`):**

- 上記 12 試験ケースに加え、補助観点として:
  - **`read` API**: 2 件(正常読込 / `FileNotFoundError`)
  - **`rollback` API**: 3 件(bak から target 復元 / bak なし `NoBackupError` / `os.replace` 失敗)
  - **write → read 往復 + バイナリデータ保持**: 1 件(`\x00\x01\x02binary\xff\xfe`)
  - **連続 2 回書込で 1 世代のみ保持**: 1 件(SRS-DATA-003 実地確認、3 回書込で v1 が失われ v2 が bak)
  - **`_best_effort_unlink` の OSError 握りつぶし**: 1 件(SDD §4.4.E「temp クリーンアップ失敗は許容」の分岐検証)
  - **非 POSIX(`hasattr(os, "O_DIRECTORY") is False`)の早期リターン**: 1 件(Windows 相当環境の `_try_fsync_directory` 不実行)
- **実測ケース数 21 件、全 Pass(2026-04-23、3 連続実行 173 tests stable 確認)**
- subprocess + SIGKILL 電源断試験は ITPR §5.6(将来 Step 19 D)に申し送り

**ケース数目安:** 正常系 3、境界値 2、異常系 3、並行 1、RCM 前提 1 = **合計 ≥ 10**(展開後 21)
**MC/DC 目標:** **100%** に引き上げ(v0.4 の 95% から強化、コード規模 78 stmt / 6 branch で網羅可能、試験設計で完全担保)

#### 7.3.5 UNIT-004.1 Integrity Validator(代表・詳細)

**関連 SRS:** SRS-026, SRS-027, SRS-RCM-015、**関連 RCM:** RCM-015、**関連 HZ:** HZ-007

> **Step 19 B6 整合化(2026-04-23、本節 v0.6):** Step 19 B3 / B4 / B5 で定着した着手前クロスレビューで、SDD §4.5 と v0.5 までの本節の間に 4 件の不整合を発見し、ユーザー合意のもと SDD を真として本節を整合化(MINOR 区分・CR 不要、SRS / SDD / RMF / SAD 本体不変)。**(1) 戻り値型:** SDD §4.5.A の `Ok(trusted: TrustedRecord)` / `FailsafeRecommended(reasons: list[IntegrityFailure])` に統一(v0.5 までの `Err([...])` / `Ok(snapshot)` 表記から変更)。`Err` ではなく `FailsafeRecommended` とする型設計は、本ユニットの成功戻りが「例外の置き換え」ではなく「SRS-027 フェイルセーフ起動の推奨」を型で表現するため(SDD §4.5.C 整合)。**(2) UT-004.1-03 / 04 / 08:** 型違反 / 必須フィールド欠落 / 空 `b""` / `None` は SDD §4.5.E により `RawPersistedRecord` 構築時点で pydantic `ValidationError` となり本ユニット責務外。SDD §4.5.B 擬似コードの未網羅項目(`SchemaVersionUnsupported` / `DoseVolumeOutOfRange` 境界 / `SettingsInconsistent`(SRS-004、tolerance 1 %))に差し替え。**(3) UT-004.1-09:** `FutureTimestamp`(タイムスタンプ未来)は SDD §4.5.B 擬似コード 9 項目に存在しない。SRS-026/027 要求文にも timestamp 検証は含まれない(「チェックサム・値域・状態組合せ」のみ)。`AccumulationExceedsDose`(積算量 > 設定量、HZ-001 過量投与直結)に差し替え。**(4) UT-004.1-10:** `InvariantViolation("ERROR ∧ error_reason==None")` は SDD §4.5 に該当検証項目なし、かつ `error_reason` フィールドの定義は SDD §4.12.B `RuntimeState` にも存在しない。`StateContradiction("RUNNING but current_flow=0")`(§4.5.B 擬似コード最初の状態組合せ、制御不能兆候検出)に差し替え。

| 試験 ID | 対象 API / 観点 | 入力 / 条件 | 期待結果 | 種別 |
|---------|---------------|-----------|---------|------|
| UT-004.1-01 | `validate(record)` 正常 | SRS-004 一貫な `RawPersistedRecord`、checksum 一致、state=IDLE | `Ok(TrustedRecord)` | 正常系 |
| UT-004.1-02 | checksum 不一致 | 同一 `payload_bytes` で checksum のみ改竄 | `FailsafeRecommended([ChecksumMismatch])`(reasons 長 1) | RCM(RCM-015) |
| UT-004.1-03 | `SchemaVersionUnsupported` | schema_version ∉ SUPPORTED_SCHEMA_VERSIONS(0 / 2 / 999 / -1) | `FailsafeRecommended([SchemaVersionUnsupported])` | 異常系 |
| UT-004.1-04 | dose_volume / duration_min 境界外 | dose=-0.1, dose=10000.0, duration=0, duration=6000 | それぞれ `DoseVolumeOutOfRange` / `DurationOutOfRange` | 境界値・異常系 |
| UT-004.1-05 | flow_rate 値域外 | -0.1 / -1.0 / 1200.1 / 2000.0 | `FailsafeRecommended([FlowRateOutOfRange])` | 境界値・異常系 |
| UT-004.1-06 | 複数エラーの列挙 | checksum 改竄 + flow_rate 超過 | `reasons` に `ChecksumMismatch` と `FlowRateOutOfRange` の両方、`len >= 2` | RCM |
| UT-004.1-07 | 破損注入(1 bit 反転) | hypothesis:payload_bytes 32 bytes の任意 1 bit を XOR 反転 | `reasons` に `ChecksumMismatch` を必ず含む(256 パターン全 Pass) | プロパティ・RCM |
| UT-004.1-08 | `SettingsInconsistent`(SRS-004) | flow=100 × 600/60 = 1000 だが dose=1100(10 % 差、tolerance 1 %) | `FailsafeRecommended([SettingsInconsistent])` | 異常系 |
| UT-004.1-09 | `AccumulationExceedsDose`(HZ-001) | accumulated_volume=1000.1 > dose_volume=1000.0 | `FailsafeRecommended([AccumulationExceedsDose])`、メタデータに両値 | RCM(HZ-001) |
| UT-004.1-10 | `StateContradiction` | state=RUNNING かつ current_flow=0.0 | `FailsafeRecommended([StateContradiction])`、detail に "RUNNING" 含む | RCM |
| UT-004.1-11 | プロパティ:正常値域 → 常に `Ok` | hypothesis の `_consistent_valid_settings`(flow × duration / 60 = dose を厳密生成) | `Ok(TrustedRecord)`(偽陽性 0 件) | プロパティ |
| UT-004.1-12 | プロパティ:2+ 破損 → 常に Failsafe | hypothesis:flow 範囲外 ∧ dose 範囲外 | `FailsafeRecommended`、`reasons` の長さ ≥ 2 | プロパティ・RCM |

**展開実装(Step 19 B6 時点、`tests/unit/test_integrity_validator.py`):**

- 上記 12 試験ケースに加え、補助観点として:
  - **UT-004.1-13 `UnsavableState`**: state=INITIALIZING 保存(§4.5.B 9 番目の状態組合せ、保存されるはずがない状態)
  - **UT-004.1-14 純粋関数性**: 同一レコードで `validate` を 2 回呼び、`Ok.trusted` が equal(副作用なし)
  - **UT-004.1-15 `TrustedRecord` の frozen 性**: 属性代入で `FrozenInstanceError`
  - **UT-004.1-16 `SUPPORTED_SCHEMA_VERSIONS` の契約**: `CURRENT_SCHEMA_VERSION` を含み、`frozenset` 型
  - **UT-004.1-17 `check_settings_consistency` tolerance 境界**: 0 % / 1 %(境界) / 1.1 %(境界外) / 5 % 許容の 4 パラメータ
  - **UT-004.1-18 §4.5.B 列挙順序の保証**: schema → checksum → flow → dose → duration の順に `reasons` に追加されること
  - **UT-004.1-19 `dose_volume == 0` 分岐**: flow×duration=0(一致)/ flow×duration>0(不一致)の 2 パラメータ
  - **UT-004.1-20 `compute_sha256` の契約**: `hashlib.sha256(payload).hexdigest()` 同値、決定性、空 payload の既知ダイジェスト
- **実測ケース数 33 件、全 Pass(2026-04-23、3 連続実行 206 tests stable 確認)**
- 本 UT で依存する共通型(`Settings` / `RuntimeState` / `RawPersistedRecord` / `TrustedRecord`)は `src/vip_persist/records.py` に先行実装(SDD §4.12.B 整合)。UNIT-003.1 Serializer(Step 19 B7 以降予定)で再利用される。

**ケース数目安:** 正常系 1、境界値 0、異常系 4、RCM 3、プロパティ 3 = **合計 ≥ 12**(展開後 33)
**MC/DC 目標:** **100%**(RCM-015、整合性検証の 9 複合条件、試験設計で全分岐網羅を担保)

#### 7.3.6 UNIT-003.1 Serializer(実施済、詳細)

**関連 SRS:** SRS-DATA-001, SRS-DATA-004、**関連 RCM:** RCM-015 前提(復元データの型保証)、**関連 HZ:** HZ-007

> **Step 19 B7 整合化(2026-04-24、本節 v0.7 新規詳細化):** B6 までは骨格記述のみだったが、B7 着手前クロスレビューで 7 論点(別途 1 論点を実装時発覚)を SDD §4.12 + SRS-DATA + B6 の `records.py` と突き合わせて検討、ユーザー合意のもと推奨方針(MINOR 区分・CR 不要、SRS / SDD / RMF / SAD 本体不変)で進行:**(1) `PersistedRecord` / `RawPersistedRecord` を別 pydantic モデルで定義**(フィールド同一、SDD §4.12.B の意味論分離を型で表現)、**(2) `build_persisted_record` ファクトリ関数**を Serializer 側に置き payload_bytes + SHA-256 checksum を生成(SDD §4.12 で責務が未明示だった、生成は Serializer / 検証は UNIT-003.2 の分離)、**(3) `State` enum は名前シリアライズ**(`auto()` の値は enum メンバ追加順序で変わるため永続レコード互換性を破壊するリスク、`{"__state__": "<name>"}` タグで回避)、**(4) records.py 不変**(B6 スコープ境界維持、`extra="forbid"` 等の挙動変更は B8 以降で再検討)、**(5) hypothesis `max_examples=200`** でラウンドトリップ + 決定論性検証(SDD「1000 件 / 100 回」の目安は hypothesis 多様性で代替)、**(6) `current_schema_version()` は関数**(§4.12.A 署名整合、将来マイグレーション時の柔軟性)、**(7) MC/DC 目標 95% → 100%** に引き上げ(B5 Atomic Writer 前例、RCM-015 前提の位置付け)。**(8、実装時発覚)`bytes` 型のタグ付け:**SDD §4.12.C 擬似コードの `_default` は Decimal / datetime のみ扱う。`payload_bytes: bytes` を JSON 化するため `{"__bytes__": "<base64>"}` タグを追加(既存の Decimal / State タグ戦略と一貫)。

| 試験 ID | 対象 API / 観点 | 入力 / 条件 | 期待結果 | 種別 |
|---------|---------------|-----------|---------|------|
| UT-003.1-01 | `build_persisted_record` + `to_json` 正常 | SRS-004 一貫な有効 record | `bytes`(UTF-8 JSON)、`schema_version` が JSON 先頭ソートで読める | 正常系 |
| UT-003.1-02 | `from_json` 正常 → `RawPersistedRecord` | `to_json` 出力を復元 | 全フィールド等価(schema_version / settings / runtime_state / payload_bytes / checksum / saved_at) | 正常系 |
| UT-003.1-03 | 決定論性(同レコード 20 回) | 同じ record で 20 回 `to_json` | 全バイト列同一 | RCM 前提(SDD §4.12.F) |
| UT-003.1-04 | Decimal 精度保持 | `Decimal("0.1") + Decimal("0.2") = Decimal("0.3")` を保存・復元 | 復元値が `Decimal("0.3")`、型も `Decimal` | RCM 前提(SDD §4.12.F) |
| UT-003.1-05 | 不正 JSON → 例外 | truncated / 空 / 配列 / null | `JSONDecodeError` または `ValidationError` | 異常系 |
| UT-003.1-05b | 不正 UTF-8 → 例外 | `b"\xff\xfe\xfd"` | `UnicodeDecodeError` | 異常系 |
| UT-003.1-06 | 必須フィールド欠落 | `{"schema_version": 1}` だけ | pydantic `ValidationError` | 異常系 |
| UT-003.1-07 | 未知 schema_version は通過 | `schema_version=999` で to→from | `RawPersistedRecord.schema_version == 999`、Integrity Validator 側で拒否 | 責務分離 |
| UT-003.1-08 | hypothesis ラウンドトリップ | `max_examples=200`、SRS-004 一貫 settings + 任意 runtime_state | 全フィールド等価(型保証 + プロパティ) | プロパティ |
| UT-003.1-09 | State 名前シリアライズ | 全 6 State(INITIALIZING / IDLE / RUNNING / PAUSED / STOPPED / ERROR) | JSON 中に enum 名が現れ、`State[...]` で復元一致 | RCM 前提・パラメータ化 |
| UT-003.1-10 | `payload_bytes` の base64 ラウンドトリップ | `build_persisted_record` 出力の `payload_bytes` | 復元バイト列が完全一致、JSON 中に `__bytes__` タグ出現 | 正常系 |
| UT-003.1-11 | `current_schema_version()` | 関数呼び出し | `CURRENT_SCHEMA_VERSION == 1` の int | 契約 |
| UT-003.1-12 | 統合(Serializer → Integrity Validator) | `build → to_json → from_json → validate` | `Ok(TrustedRecord)` | 統合 |
| UT-003.1-13 | `compute_payload_checksum` 決定論性 | 同一入力を 2 回 | `(payload_bytes, checksum)` ペアが同一、checksum が 64 文字 hex | 決定論 |
| UT-003.1-14 | JSON キーが sort_keys=True でソート済 | `to_json` 出力 | トップレベルキーが辞書順 | RCM 前提(SDD §4.12.C) |
| UT-003.1-15 | `_default` 未知型で TypeError | 任意クラスのインスタンスを渡す | `TypeError` | 異常系(SDD §4.12.E) |
| UT-003.1-16 | `_hook` パススルー | タグなし dict | 同一オブジェクト(identity 保存) | 正常系 |
| UT-003.1-17 | hypothesis 決定論性プロパティ | `max_examples=50`、任意有効 record で 5 回 `to_json` | 全バイト列同一 | プロパティ |

**ケース数目安:** 正常系 4、境界値 0、異常系 3、RCM 前提 3、プロパティ 2、契約 1、統合 1 = **合計 ≥ 14**(展開後 **26**、State パラメータ化 6 + JSON 不正 4 + 補助観点 4 を含む)
**MC/DC 目標:** **100%**(v0.6 の 95% から引き上げ、B5 Atomic Writer 前例、RCM-015 前提の位置付け、規模 47 stmt / 12 branch で網羅可能)

#### 7.3.7 UNIT-003.2 Checksum Verifier(実施済、詳細)

**関連 SRS:** SRS-SEC-001(SHA-256 改ざん検知)、**関連 RCM:** RCM-015 構成要素(Integrity Validator が将来呼ぶ)、**関連 HZ:** HZ-007

> **Step 19 B8 整合化(2026-04-24、本節 v0.8 新規詳細化):** B7 までは骨格記述のみだったが、B8 着手前クロスレビューで運用性 1 論点(既存重複実装の整理タイミング)+ 専門性 4 論点を抽出、ユーザー合意のもと推奨方針で進行(MINOR 区分・CR 不要、SRS / SDD / RMF / SAD 本体不変):**運用性:** 既存の `vip_integrity/validator.py:compute_sha256` と `vip_persist/serializer.py:compute_payload_checksum` は不変維持(B7 教訓「add-only 拡張」踏襲、統合リファクタは別ステップに委任)。**専門性:** ① SDD §4.13.C 通り `hmac.compare_digest` で定数時間比較、② 大文字 / 混合 hex の `expected` は `.lower()` で正規化、③ 不正形式 `expected`(長さ違い / 非 hex)は例外なし `False` 返却、④ MC/DC 目標 95% → **100%** に引き上げ(B5/B6/B7 前例)。**UT 申し送り:** SDD §4.13.F 末尾の「タイミング試験(参考、一致/不一致の実行時間差が統計的有意でない)」は、B4/B5 の「実時間スレッド試験・SIGKILL 電源断 UT 申し送り」教訓に従い **ITPR §5.6(将来 Step 19 D)** に申し送り。決定論性を UT の第一原則とする運用パターン継続。

| 試験 ID | 対象 API / 観点 | 入力 / 条件 | 期待結果 | 種別 |
|---------|---------------|-----------|---------|------|
| UT-003.2-01 | `compute(b"")` 既知ベクタ | NIST SHA-256 empty input | `"e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"` | 基本 |
| UT-003.2-02 | `compute(b"abc")` 既知ベクタ | NIST SHA-256('abc') | `"ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"` | 基本 |
| UT-003.2-03 | `verify(data, compute(data))` 成功 | 5 種のバイト列(空 / ASCII / 長文 / バイナリ / 1000 null) | `True`(全件) | ラウンドトリップ・パラメータ化 |
| UT-003.2-04 | 1 bit 改変で検証失敗 | `data` 先頭バイトを XOR 0x01 | `verify` が `False` | RCM(SEC-001) |
| UT-003.2-05 | 長さ違い `expected` → False(例外なし)| 0 / 63 / 65 / 128 文字 | `verify` が `False`(4 サブケース)| 異常系・パラメータ化 |
| UT-003.2-06 | 非 hex 文字 `expected` → False(例外なし)| `g....` / `z...` / `-...` / 末尾 `Z` | `verify` が `False`(4 サブケース)| 異常系・パラメータ化 |
| UT-003.2-07 | 大文字 hex `expected` も受理 | `_SHA256_ABC.upper()` | `verify` が `True` | 正規化 |
| UT-003.2-07b | 混合大小 hex も受理 | 一文字おきに大小変換 | `verify` が `True` | 正規化 |
| UT-003.2-08 | `compute` 決定論性 | 同一入力で 100 回 | 全て同一 digest | 決定論 |
| UT-003.2-09 | 1 MB 入力で動作 | `b"x" * 1048576` | `verify` が `True`、digest 長 64 | 資源・正常系 |
| UT-003.2-10 | `compute` 出力長 == 64 | 4 種のバイト列 | 全件 `len == 64` | 契約・パラメータ化 |
| UT-003.2-11 | `compute` 出力が小文字 hex のみ | 4 種のバイト列 | 全件 `[0-9a-f]` のみ | 契約・パラメータ化 |
| UT-003.2-12 | hypothesis ラウンドトリップ | `max_examples=200`、任意バイト列(max 4 KB)| 常に `verify == True` | プロパティ |
| UT-003.2-13 | hypothesis 衝突試験 | `max_examples=200`、異なる 2 バイト列 | 異なる digest(小規模での衝突なし) | プロパティ・SEC-001 |
| UT-003.2-14 | 正しい digest を 1 文字短く | `_SHA256_ABC[:-1]` | `verify` が `False` | 境界(長さ) |
| UT-003.2-15 | 空白混入 `expected` | `f" {_SHA256_ABC} "`(長さ 66) | `verify` が `False` | 異常系 |

**ケース数目安:** 基本 2、ラウンドトリップ 5、境界値・異常系 7(パラメータ化展開後)、正規化 2、決定論 1、資源 1、契約 2、プロパティ 2 = **合計 ≥ 10**(展開後 **32**)
**MC/DC 目標:** **100%**(v0.7 骨格の 95% から引き上げ、コード規模 17 stmt / 4 branch で網羅可能)

#### 7.3.8 残 10 ユニット骨格(Step 19 B の TDD Red で詳細化)

| ユニット ID | 主要試験観点 | ケース数目安 | MC/DC 目標 | 備考 |
|------------|-----------|-----------|-----------|------|
| UNIT-001.2 Control Loop | タイミング(100 ms 周期 ±10%、SRS-P02)、heartbeat 送出、SRS-031 自動停止判定、ERROR 誘発、並行 | ≥ 12 | 100%(RCM-004 SW 側送出)| `pytest-benchmark` でサイクル計測 |
| UNIT-001.3 Command Handler | コマンドキュー、stop ファストパス(SRS-P04 ≤ 50 ms)、順次処理、境界値 | ≥ 10 | 95% | stop ファストパスの応答時間計測必須 |
| UNIT-001.5 Watchdog (SW side) | 500 ms 判定(境界 499/500/501)、冪等、並行、クロック逆転 | ≥ 8 | 100%(RCM-003)| |
| UNIT-002.1 Pump Simulator | 指令反映、`force_stop_failsafe` 冪等、SRS-030/031 準拠、積算量計算 | ≥ 10 | 95% | `force_stop_failsafe` は RCM-004 HW 側の被呼出側 |
| UNIT-002.2 Pump Observer | 観測 API の不変性(pure)、状態整合性 | ≥ 6 | — | 観測のみ、RCM なし |
| UNIT-002.3 Event Injection Stub | Inc.2 以降のスタブ、本 Inc.1 では空動作の確認のみ | ≥ 3 | — | Inc.2 着手時に拡張 |
| UNIT-004.2 Resume Confirmation Gate | needs_confirm トグル、期限チェック、状態遷移連携 | ≥ 8 | 100%(RCM-016)| |
| UNIT-005.1 Control API | 7 コマンド(start/stop/pause/resume/reset/error_reset/confirm_resume)の委譲、例外伝搬 | ≥ 10 | 90% | 委譲先の mock 検証主体 |
| UNIT-005.2 State Observer API | 薄いラッパー、observer 委譲、非 block | ≥ 6 | — | |
| UNIT-005.3 Validation API(クラス B) | **SEP-001 分離検証**、内部例外握りつぶし契約、境界値 | ≥ 8 | 90% | `mypy` でインポートグラフ分離を機械検証 |

**合計ケース数目安(全 17 ユニット):** **≥ 145 件**(代表 5 + UNIT-003.1 + UNIT-003.2 = 117 件実測 + 骨格 10 = 73 件の目安)。最終的な件数は Step 19 B の TDD で増減する見込み。

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
| UNIT-001.4 | **34**(うち UT-001.4-01..12 = 12 + パラメータ化展開 14 + 補助観点 8)| **34** | 0 | 0 | **100.00% / 100.00% / 100%(MC/DC 試験設計担保、RCM-001 範囲 + 設定値整合性 + 状態別スキップ全分岐)** | 2026-04-23 | Step 19 B3 PR #11 マージコミット `72d474e` |
| UNIT-001.5 | ≥ 8 | — | — | — | — | — | — |
| UNIT-002.1 | ≥ 10 | — | — | — | — | — | — |
| UNIT-002.2 | ≥ 6 | — | — | — | — | — | — |
| UNIT-002.3 | ≥ 3 | — | — | — | — | — | — |
| UNIT-002.4 | **18**(うち UT-002.4-01..08 展開後 10 + 補助観点 8)| **18** | 0 | 0 | **100.00% / 100.00% / 100%(MC/DC 試験設計担保、RCM-004 HW 側 + クロック逆転 + Tripped 分岐)** | 2026-04-23 | Step 19 B4 PR #12 マージコミット `3c7a933` |
| UNIT-003.1 | **26**(うち UT-003.1-01..17 展開後 22 + 補助観点 4 - State パラメータ化 6 + JSON 不正 4 含む)| **26** | 0 | 0 | **100.00% / 100.00% / 100%(MC/DC 試験設計担保、Decimal / State / bytes 3 種タグ往復 + 決定論性 + 不正 JSON / UTF-8 例外 + hypothesis ラウンドトリップ)** | 2026-04-24 | Step 19 B7 PR #15 マージコミット `982c568` |
| UNIT-003.2 | **32**(うち UT-003.2-01..15 展開後 28 + パラメータ化 4 セット + hypothesis 2)| **32** | 0 | 0 | **100.00% / 100.00% / 100%(MC/DC 試験設計担保、SHA-256 既知ベクタ + ラウンドトリップ + 不正 expected 8 サブケース + 大小 hex 正規化 + hypothesis 衝突・ラウンドトリップ)** | 2026-04-24 | Step 19 B8 PR マージコミット(TBD)|
| UNIT-003.3 | **21**(うち UT-003.3-01..10 展開後 12 + 補助観点 9)| **21** | 0 | 0 | **100.00% / 100.00% / 100%(MC/DC 試験設計担保、write/read/rollback + bak 世代管理 + 例外経路 + 非 POSIX 早期リターン)** | 2026-04-23 | Step 19 B5 PR #13 マージコミット `0a1cc34` |
| UNIT-004.1 | **33**(うち UT-004.1-01..12 展開後 24 + 補助観点 9)| **33** | 0 | 0 | **100.00% / 100.00% / 100%(MC/DC 試験設計担保、§4.5.B 9 検証項目 + settings consistency tolerance 境界 + dose==0 分岐 + 列挙順序 + hypothesis 破損注入)** | 2026-04-23 | Step 19 B6 PR #14 マージコミット `faf743b` |
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
| UNIT-002.4 HW-side Failsafe Timer | UT-002.4-01 〜 UT-002.4-08 | SRS-RCM-004, SRS-032 | RCM-004(HW 側)| HZ-001, HZ-002 | **Pass(18 tests / 100.00% stmt / 100.00% branch / MC/DC 100%、Step 19 B4、2026-04-23)** |
| UNIT-003.1 Serializer | UT-003.1-01 〜 UT-003.1-17 | SRS-DATA-001, 004 | RCM-015 前提 | HZ-007 | **Pass(26 tests / 100.00% stmt / 100.00% branch / MC/DC 100%、Step 19 B7、2026-04-24)** |
| UNIT-003.2 Checksum Verifier | UT-003.2-01 〜 UT-003.2-15 | SRS-SEC-001 | RCM-015 構成要素 | HZ-007 | **Pass(32 tests / 100.00% stmt / 100.00% branch / MC/DC 100%、Step 19 B8、2026-04-24)** |
| UNIT-003.3 Atomic File Writer | UT-003.3-01 〜 UT-003.3-10 | SRS-DATA-002, 003 | RCM-015 前提 | HZ-007 | **Pass(21 tests / 100.00% stmt / 100.00% branch / MC/DC 100%、Step 19 B5、2026-04-23)** |
| UNIT-004.1 Integrity Validator | UT-004.1-01 〜 UT-004.1-12 | SRS-026, 027, SRS-RCM-015 | RCM-015 | HZ-007 | **Pass(33 tests / 100.00% stmt / 100.00% branch / MC/DC 100%、Step 19 B6、2026-04-23)** |
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
| 0.4 | 2026-04-23 | **Step 19 B4(UNIT-002.4 HW-side Failsafe Timer TDD 実装)の実施結果を反映 + §7.3.3 整合化**。**(1) 第 I 部 §7.3.3 整合化(MINOR、CR 不要):** Step 19 B3 教訓を運用化し着手前クロスレビューを実施、(a) Logger 注入据置(SDD §4.3.B に `_logger` フィールドなし、UNIT-004+ で正式化、HW failsafe 識別子は `force_stop_failsafe(reason="HEARTBEAT_TIMEOUT")` で代替)、(b) クロック注入(DI)採用(`clock: Callable[[], float]` をコンストラクタ注入、UT-002.4-07 クロック逆転試験のため)、(c) クロック逆転時挙動を「安全側 = 発火」と設計判断(SDD §4.3 未定義、RCM-004 安全側原則 + UNIT-001.1 と整合)、の 3 件を整合化注釈に明記。SRS / SDD / RMF / SAD 本体は不変。**(2) §7.3.3 試験テーブル:** UT-002.4-04 を 04a(500 ms ちょうどで発火しない)/ 04b(500 ms + ε で発火)に分割、UT-002.4-06 を「ログ記録」から「`force_stop_failsafe(reason="HEARTBEAT_TIMEOUT")` 呼出識別」に整合化、UT-002.4-08 を 08a(heartbeat 無視)/ 08b(`check_once` 冪等)に分割、各ケースに `check_once` API 経由のテスト前提を明記。**(3) 第 II 部 §9.2:** UNIT-002.4 行を 18 tests Pass / カバレッジ 100.00% / MC/DC 100% で確定。§11 UNIT-002.4 行を「Pass」更新。UNIT-001.4 行のコミット欄を Step 19 B3 マージ SHA `72d474e` で確定。**(4) 試験設計:** 補助観点 8 件(start/stop ライフサイクル 4、pump 例外耐性 1、定数値 2、実時間スレッド統合スモーク 1)、連打側スモークは macOS sleep ジッタ flaky のため fake_clock UT-002.4-01/05 に委任(教訓記録)。教訓 2 件を DEVELOPMENT_STEPS §教訓に記録 | k-abe |
| 0.8 | 2026-04-24 | **Step 19 B8(UNIT-003.2 Checksum Verifier TDD 実装)の実施結果を反映 + §7.3.7 新規詳細化(残 11 → 10 骨格)**。**(1) 第 I 部 §7.3.7 新規詳細化(MINOR、CR 不要):** B7 までは骨格のみの節を、着手前クロスレビュー(運用性 1 + 専門性 4)解消後に詳細 UT テーブル(UT-003.2-01〜15)として書き下ろし、既存の残 11 ユニット骨格は §7.3.8 に移動して 10 ユニットに繰り下げ。本節冒頭に整合化注釈を追記。**(2) 判断論点:** 運用性 — 既存の `compute_sha256` / `compute_payload_checksum` 重複は不変維持(B7 教訓「add-only 拡張」踏襲);専門性 — ① `hmac.compare_digest` 定数時間比較、② 大小 hex の `.lower()` 正規化、③ 不正 `expected` は例外なし `False`、④ MC/DC 目標 95% → **100%** 引き上げ。SRS / SDD / RMF / SAD 本体不変。**(3) UT 申し送り:** SDD §4.13.F 末尾「タイミング試験(参考)」は B4/B5 教訓(非決定論的試験は IT へ)に従い **ITPR §5.6 申し送り**。**(4) 第 II 部 §9.2:** UNIT-003.2 行を 32 tests Pass / カバレッジ 100% / MC/DC 100% で確定、§9.2 テーブル内の UNIT-003.1 行重複(骨格行と実績行の二重状態、B7 で発生)を整理して UNIT-003.2 正しい位置に配置。§11 UNIT-003.2 行を「Pass」更新。UNIT-003.1 行のコミット欄を Step 19 B7 PR #15 マージ SHA `982c568` で確定。**(5) 試験設計:** NIST 既知ベクタ 2 種、`pytest.parametrize` で UT-003.2-05/06/10/11 を 16 サブケースに展開、`hypothesis` プロパティ 2 種(`max_examples=200` のラウンドトリップ + 異なるバイト列の digest 相違)。専門性/運用性の論点分離により、5 論点中 4 論点を専門性に分類して提示を簡潔化できたことを実証(B7 教訓の運用化) | k-abe |
| 0.7 | 2026-04-24 | **Step 19 B7(UNIT-003.1 Serializer TDD 実装)の実施結果を反映 + §7.3.6 新規詳細化(残 12 → 11 骨格)**。**(1) 第 I 部 §7.3.6 新規詳細化(MINOR、CR 不要):** B6 までは骨格のみの節を、着手前クロスレビュー 7 論点(別途 1 論点を実装時発覚)解消後に詳細 UT テーブル(UT-003.1-01〜17)として書き下ろし、既存の残 12 ユニット骨格は §7.3.7 に移動して 11 ユニットに繰り下げ。本節冒頭に整合化注釈を追記(推奨方針全 7 + 8 論点を箇条書きで記録)。**(2) 判断論点:** ① `PersistedRecord`/`RawPersistedRecord` の別 pydantic モデル化、② `build_persisted_record` ファクトリを Serializer 側に配置、③ `State` 名前シリアライズ(auto() リファクタリングリスク回避)、④ records.py 不変(B6 スコープ境界維持)、⑤ hypothesis `max_examples=200`、⑥ `current_schema_version()` 関数実装、⑦ MC/DC 目標 95%→100% 引き上げ、⑧ `bytes` 型の `__bytes__` base64 タグ(実装時発覚、§4.12.C `_default` 擬似コード拡張 MINOR)。SRS / SDD / RMF / SAD 本体不変。**(3) 第 II 部 §9.2:** UNIT-003.1 行を 26 tests Pass / カバレッジ 100.00% / MC/DC 100% で確定。§11 UNIT-003.1 行を「Pass」更新。UNIT-004.1 行のコミット欄を Step 19 B6 PR #14 マージ SHA `faf743b` で確定。**(4) 試験設計:** Decimal / State / bytes の 3 種タグ(`__decimal__` / `__state__` / `__bytes__`)ラウンドトリップ、hypothesis `max_examples=200` で SRS-004 一貫 settings + 任意 runtime_state のラウンドトリップ網羅、決定論性 hypothesis `max_examples=50` で 5 回 `to_json` 全一致、Integrity Validator との統合試験で E2E 検証。教訓 1 件を DEVELOPMENT_STEPS §教訓に追記(「判断材料の抽象度調整 — ユーザーフィードバック『書いてもらってもよくわからくて判断できない』への応答」) | k-abe |
| 0.6 | 2026-04-23 | **Step 19 B6(UNIT-004.1 Integrity Validator TDD 実装)の実施結果を反映 + §7.3.5 整合化**。**(1) 第 I 部 §7.3.5 整合化(MINOR、CR 不要):** Step 19 B3 / B4 / B5 で定着した着手前クロスレビューで SDD §4.5 と v0.5 までの本節の間に 4 件の不整合を発見、ユーザー合意のもとで SDD を真として本節を整合化:(a) 戻り値型を `Err([...])` / `Ok(snapshot)` → SDD §4.5.A の `FailsafeRecommended(reasons: list[IntegrityFailure])` / `Ok(TrustedRecord)` に統一、(b) UT-004.1-03/04/08 を pydantic 管轄(§4.5.E 「本ユニット到達前に `ValidationError`」)から §4.5.B 未網羅項目(`SchemaVersionUnsupported` / `DoseVolumeOutOfRange` / `SettingsInconsistent`)に差し替え、(c) UT-004.1-09 `FutureTimestamp` を §4.5.B 非存在検証(SRS-026/027 にも未要求)から `AccumulationExceedsDose`(HZ-001 過量投与直結)に差し替え、(d) UT-004.1-10 `ERROR ∧ error_reason==None` を §4.5 非存在から `StateContradiction("RUNNING but current_flow=0")` に差し替え。SRS / SDD / RMF / SAD 本体は不変。**(2) §7.3.5 試験テーブル:** 12 行を SDD §4.5.B 擬似コード 9 検証項目に全整合化、補助観点 9 件(UT-004.1-13〜20 + hypothesis 2 件)を展開。MC/DC 目標 100% を維持(`validate` の複合条件 + `check_settings_consistency` の dose==0 分岐)。**(3) 第 II 部 §9.2:** UNIT-004.1 行を 33 tests Pass / カバレッジ 100.00% / MC/DC 100% で確定。§11 UNIT-004.1 行を「Pass」更新。UNIT-003.3 行のコミット欄を Step 19 B5 マージ SHA `0a1cc34` で確定。**(4) 試験設計:** hypothesis プロパティ 3 件(`_consistent_valid_settings` 戦略、1 bit 反転、2+ 破損)、`pytest.parametrize` で UT-004.1-03/04/05/17/19 を計 14 サブケースに展開、FrozenInstanceError / `SUPPORTED_SCHEMA_VERSIONS` 契約 / `compute_sha256` 既知ベクタで補助観点を実装。依存型(`Settings` / `RuntimeState` / `RawPersistedRecord` / `TrustedRecord`)は `src/vip_persist/records.py` に先行実装し UNIT-003.1 Serializer(Step 19 B7 以降予定)で再利用。教訓を DEVELOPMENT_STEPS §教訓に追記 | k-abe |
| 0.5 | 2026-04-23 | **Step 19 B5(UNIT-003.3 Atomic File Writer TDD 実装)の実施結果を反映 + §7.3.4 整合化**。**(1) 第 I 部 §7.3.4 整合化(MINOR、CR 不要):** Step 19 B3 / B4 教訓の運用継続で着手前クロスレビュー実施、4 件の不整合を発見:(a) API 名 `write_atomic(path, data)` → SDD §4.4.A の `write(data, target_path)` + `read` + `rollback` 3 API へ整合化、(b) UT-003.3-07 並行書込を「ロック機構動作」→ SDD §4.4.C「呼出側責任、本ユニットはロックしない」と整合な「ステートレス確認(異なる target_path への並行書込)」へ整合化、(c) UT-003.3-08 `Err(DiskFullError)` → SDD §4.4.E 整合の `WriteErr(OSError)` + `errno==ENOSPC` へ、(d) UT-003.3-10 subprocess + SIGKILL 電源断試験は CI 安定性 + SDD §4.4.E「原理的に検知不可能 / load 側で担保」により ITPR §5.6 申し送り、本 UT では内部ステップ観測 + `os.fsync` 呼出モック検証で代替(UT-003.3-10a/10b に分割)。SRS / SDD / RMF / SAD 本体は不変。**(2) §7.3.4 試験テーブル:** 12 行へ再整備(UT-003.3-02b bak 置換、UT-003.3-10a/10b 分割、引数順を SDD に統一)。MC/DC 目標を 95% → **100%** に引き上げ(コード規模 78 stmt / 6 branch、試験設計で完全網羅可能)。**(3) 第 II 部 §9.2:** UNIT-003.3 行を 21 tests Pass / カバレッジ 100.00% / MC/DC 100% で確定。§11 UNIT-003.3 行を「Pass」更新。UNIT-002.4 行のコミット欄を Step 19 B4 マージ SHA `3c7a933` で確定。**(4) 試験設計:** 補助観点 9 件(read 2 + rollback 3 + 往復 1 + bak 世代管理 1 + best-effort unlink 1 + 非 POSIX 1)、`tmp_path` fixture + `unittest.mock.patch` で `os.replace`/`os.fsync`/`Path.unlink` を注入して OSError 経路を網羅。教訓 2 件を DEVELOPMENT_STEPS §教訓に記録(着手前クロスレビューの運用 3 度目定着 + OSError 注入パターンの再利用性) | k-abe |
