# ソフトウェアユニットテスト計画書/報告書

**ドキュメント ID:** UTPR-VIP-001
**バージョン:** 0.23
**作成日:** 2026-04-23
**最終更新日:** 2026-05-13
**対象製品:** 仮想輸液ポンプ(Virtual Infusion Pump)/ VIP-SIM-001
**対象ソフトウェアバージョン:** v0.2.0-inc2(予定、Inc.2 完了時)
**対象範囲:** Inc.1(流量制御コア、全 18 ソフトウェアユニット)+ Inc.2(アラーム管理、UNIT-006.1 詳細 + 残 7 ユニット骨格 + 既存 3 ユニット拡張節)= 合計 26 ユニット(Step 20 F、CR-0012 で骨格化 / Step 20 X3、CR-0017 で UNIT-006.1 詳細化)
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

本書は、IEC 62304 箇条 5.5(ソフトウェアユニットの実装)に基づき、本プロジェクトの **Inc.1(流量制御コア)で定義された全 18 ソフトウェアユニット + Inc.2(アラーム管理)範囲の 8 新規ユニット(骨格)+ 既存 3 ユニットの拡張節** の実装と検証(ユニット試験)の計画および結果を記録する。

**適用範囲:**

- **対象ユニット:**
  - **Inc.1 範囲(実施済、Step 19 B〜H1):** SDD-VIP-001 v0.4 §3 で改良された 18 ユニット(UNIT-001.1〜UNIT-005.4、Step 19 H1 で UNIT-005.4 CLI 追加)
  - **Inc.2 範囲(骨格、Step 20 F):** SDD-VIP-001 v0.5 §4.19〜§4.26 で骨格化された Inc.2 新規 8 ユニット(UNIT-006.1〜006.6 + UNIT-007.1〜007.2)+ SDD §4.1.G / §4.11.G / §4.15.G で骨格化された既存 3 ユニット拡張(UNIT-001.1 / 002.3 / 005.1)
- **対象 SRS 要求:**
  - **Inc.1:** SRS-VIP-001 v0.1 §9 Inc.1 受入基準に列挙された全必須要求(SRS-001〜032、P01〜P07、I-*、O-*、IF-001〜005、ALM-001〜003、SEC-001〜003、UX-001〜002、DATA-001〜004、OPS-001〜012、RCM-001〜020)
  - **Inc.2:** SRS-VIP-001 v0.3 で確定した SRS-040〜044(検知)+ SRS-ALM-004〜008(アラーム)+ SRS-RCM-006/009/010/011/012(RCM)+ SRS-IF-010(Alarm I/F)+ SRS-O-040(アラーム I/F 本実装)+ SRS-I-040(イベント注入 4 種)+ SRS-REG-002(IEC 60601-1-8 詳細化)
- **対象 RCM:**
  - **Inc.1(Verified、Step 19 H3):** RMF-VIP-001 v0.4 のうち Inc.1 範囲(RCM-001, 003, 004, 015, 016, 019)
  - **Inc.2(Designed、Step 20 C):** RMF-VIP-001 v0.4 §7.1 で Designed 状態の 5 RCM(RCM-006/009/010/011/012)+ RCM-020 候補(HZ-009 対応、SRS 正式登録は Step 20 B-3 候補申し送り中)
- **除外範囲:** Inc.3〜4 の要求(用量計算、UI / ロギング本体、対話 UI)+ Inc.4 で本実装予定の ARCH-009 Logging Stub(旧 ARCH-006)

**位置づけ:**

- 本書は結合試験(ITPR-VIP-001、§5.6 予定)と システム試験(STPR-VIP-001、§5.7 予定)の **土台** として機能する。UT Pass がない状態では結合試験に進まない(SDP §開発フロー)。
- 試験ケースは SDD §5.4.4 で規定された各ユニットの「検証方法」を具体的な UT-ID に展開したものである。
- 本プロジェクトは **TDD(Red-Green-Refactor)** を採用する(SDP v0.1)。したがって本書 v0.1(計画)の完成後、各ユニット実装(Step 19 B)は「UT を Red で先に書く → 実装で Green 化 → Refactor」の順に進める。

## 2. 参照文書

| ID | 文書名 | バージョン | 参照箇所 |
|----|--------|----------|---------|
| [1] | ソフトウェア開発計画書(SDP-VIP-001) | v0.1 | 実装ルール、TDD 採用、静的解析スタック |
| [2] | ソフトウェア要求仕様書(SRS-VIP-001) | v0.3 | §9 Inc.1 受入基準、機能/性能/RCM 要求、SRS-040〜044(Inc.2 検知)、SRS-ALM-004〜008(Inc.2 アラーム)、SRS-RCM-006/009/010/011/012(Inc.2 RCM)、SRS-IF-010(Alarm I/F)、SRS-O-040(本実装)、SRS-I-040(イベント注入 4 種) |
| [3] | ソフトウェアアーキテクチャ設計書(SAD-VIP-001) | v0.2 | ARCH-001〜005(Inc.1)+ ARCH-006 Detection 検知群(Inc.2 新設、UNIT-006.1〜006.6)+ ARCH-007 Alarm Reporter(Inc.2 本実装、UNIT-007.1〜007.2)+ ARCH-009 Logging Stub(Inc.4 予定、旧 ARCH-006 リネーム)、SEP-001〜003、SOUP |
| [4] | ソフトウェア詳細設計書(SDD-VIP-001) | v0.5 | §4.1〜§4.18 全 18 ユニット詳細(Inc.1)+ §4.19〜§4.26 Inc.2 新規 8 ユニット骨格 + §4.1.G / §4.11.G / §4.15.G 既存 3 ユニット拡張、検証方法、§5.1 IF-U 詳細(IF-U-007 + IF-U-012〜015) |
| [5] | ソフトウェアリスクマネジメント計画書(SRMP-VIP-001) | v0.2 | §3.2 独立性、§7.2 影響解析 |
| [6] | リスクマネジメントファイル(RMF-VIP-001) | v0.4 | RCM-001〜019 検証状態(Inc.1 Verified)+ HZ-009 識別 + RCM-006/009/010/011/012 Designed(Inc.2)|
| [7] | ソフトウェア構成管理計画書(SCMP-VIP-001) | v0.3 | §4.1 CR 区分、§5 ベースライン |
| [8] | CCB 運用規程(CCB-VIP-001) | v0.2 | §5.4 インターバル(1 分、学習プロジェクト特例) |
| [9] | ソフトウェア問題解決手順書(SPRP-VIP-001) | v0.2 | 試験中発見の不具合の PRB 起票運用 |
| [10] | Inc.2 範囲計画書(INC2-SCOPE-VIP-001) | v0.1 | §6 対象ユニット候補(Inc.2 新規 8 + 既存 3 拡張)、§9 Step 20 F 計画、§10 受入基準 |
| [11] | IEC 60601-1-8 | (規格)| §6.1 アラーム優先度分類(高 / 中 / 低)、§5.1.4 テクニカル / 生理アラーム区分、§6.4 アラーム確認・休止規定(高優先度 ≤ 120 秒消音時間制限)|

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
| UNIT-001.1 | State Machine | ARCH-001 | C | §4.1(v0.1)+ §4.1.G(v0.5、Inc.2 拡張)| `src/vip_ctrl/state_machine.py` |
| UNIT-001.2 | Control Loop | ARCH-001 | C | §4.6(v0.2) | `src/vip_ctrl/control_loop.py` |
| UNIT-001.3 | Command Handler | ARCH-001 | C | §4.7(v0.2) | `src/vip_ctrl/command_handler.py` |
| UNIT-001.4 | Flow Command Validator | ARCH-001 | C | §4.2(v0.1) | `src/vip_ctrl/flow_validator.py` |
| UNIT-001.5 | Watchdog (SW side) | ARCH-001 | C | §4.8(v0.2) | `src/vip_ctrl/watchdog.py` |
| UNIT-002.1 | Pump Simulator | ARCH-002 | C | §4.9(v0.2) | `src/vip_sim/pump.py` |
| UNIT-002.2 | Pump Observer | ARCH-002 | C | §4.10(v0.2) | `src/vip_sim/observer.py` |
| UNIT-002.3 | Event Injection Stub | ARCH-002 | C(本版スタブ → Inc.2 で no-op 解除) | §4.11(v0.2)+ §4.11.G(v0.5、Inc.2 拡張)| `src/vip_sim/event_injection.py` |
| UNIT-002.4 | HW-side Failsafe Timer | ARCH-002 | C | §4.3(v0.1) | `src/vip_sim/failsafe_timer.py` |
| UNIT-003.1 | Serializer | ARCH-003 | C | §4.12(v0.2) | `src/vip_persist/serializer.py` |
| UNIT-003.2 | Checksum Verifier | ARCH-003 | C | §4.13(v0.2) | `src/vip_persist/checksum.py` |
| UNIT-003.3 | Atomic File Writer | ARCH-003 | C | §4.4(v0.1) | `src/vip_persist/atomic_writer.py` |
| UNIT-004.1 | Integrity Validator | ARCH-004 | C | §4.5(v0.1) | `src/vip_integrity/validator.py` |
| UNIT-004.2 | Resume Confirmation Gate | ARCH-004 | C | §4.14(v0.2) | `src/vip_integrity/resume_gate.py` |
| UNIT-005.1 | Control API | ARCH-005 | C | §4.15(v0.2)+ §4.15.G(v0.5、Inc.2 拡張)| `src/vip_api/control.py` |
| UNIT-005.2 | State Observer API | ARCH-005 | C | §4.16(v0.2) | `src/vip_api/observer.py` |
| UNIT-005.3 | Validation API | ARCH-005 | **B(分離対象、SEP-001)** | §4.17(v0.2) | `src/vip_api_b/validation.py` |
| UNIT-005.4 | CLI Entry Point | ARCH-005 | C | §4.18(v0.4、Step 19 H1) | `src/vip_ctrl/cli.py` |
| UNIT-006.1 | Occlusion Detector(Inc.2 新規、詳細、Step 20 X1 実装済 + Step 20 X2 SDD 詳細化 + Step 20 X3 UTPR 詳細化)| ARCH-006 Detection | C | §4.19(v0.6) | `src/vip_detection/occlusion.py`(運用中、v0.1)|
| UNIT-006.2 | Air-Bubble Detector(Inc.2 新規、骨格)| ARCH-006 Detection | C | §4.20(v0.5) | `src/vip_detection/air_bubble.py`(予定)|
| UNIT-006.3 | Reservoir Empty Detector(Inc.2 新規、骨格)| ARCH-006 Detection | C | §4.21(v0.5) | `src/vip_detection/reservoir.py`(予定)|
| UNIT-006.4 | Alarm Task Watchdog(Inc.2 新規、骨格)| ARCH-006 Detection | C | §4.22(v0.5) | `src/vip_detection/alarm_task_watchdog.py`(予定)|
| UNIT-006.5 | Alarm Path Redundancy(Inc.2 新規、骨格)| ARCH-006 Detection | C | §4.23(v0.5) | `src/vip_detection/alarm_path_redundancy.py`(予定)|
| UNIT-006.6 | Battery Low Detector(Inc.2 新規、骨格、HZ-009 対応)| ARCH-006 Detection | C | §4.24(v0.5) | `src/vip_detection/battery.py`(予定)|
| UNIT-007.1 | Alarm Reporter Core(Inc.2 新規、骨格)| ARCH-007 Alarm Reporter | **B(分離対象、SEP-003)** | §4.25(v0.5) | `src/vip_alarm/reporter.py`(予定)|
| UNIT-007.2 | Alarm Priority Classifier(Inc.2 新規、骨格、純粋関数)| ARCH-007 Alarm Reporter | **B(分離対象、SEP-003)** | §4.26(v0.5) | `src/vip_alarm/priority_classifier.py`(予定)|

> **SEP-001(論理的分離):** UNIT-005.3 は物理分離不可(単一プロセス Python)のため、SAD §9 の定める **論理的分離**(抽象 I/F・一方向依存・frozen データ・静的解析ルール)で担保する。具体手段として本 UT 計画では `src/vip_api_b/` サブパッケージを分離境界とし、`mypy --strict` で相互依存の禁止を機械検証する。
>
> **SEP-003(Alarm Reporter 分離、Inc.2 で詳細化):** UNIT-007.1 + UNIT-007.2 は SAD v0.2 §9.2 SEP-003 に基づきクラス B 維持(検知ロジックなし、`AlarmEvent` を frozen 値型で受け取って分類 + 通知のみ)。本 UT 計画では `src/vip_alarm/` サブパッケージを分離境界とし、`vip_ctrl.*` / `vip_sim.*` / `vip_integrity.*` への戻り値書込み禁止 + 例外伝播禁止を AST 機械検証で担保(SEP-001 の検証手段の Inc.2 連動拡張、Step 20 X〜の TDD で実装)。

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

- **RCM 実装箇所の MC/DC(Inc.1):** RCM-001/003/004/015/016/019 が実装されるユニット(UNIT-001.1、001.4、001.5、002.4、004.1、004.2)は **MC/DC 100%** を目標(§7.4 参照)。
- **RCM 実装箇所の MC/DC(Inc.2、骨格):** RCM-006/009/010/011/012 が実装されるユニット(UNIT-006.1、006.2、006.3、006.4、006.5、006.6、007.1)は **MC/DC 100%** を目標(SDD v0.6 候補で各検知ロジック詳細化と並行で確認)。UNIT-007.2(クラス B 純粋関数、IEC 60601-1-8 優先度判定の表参照のみ)は **MC/DC ≥ 90%** を目標(分岐数が少なく、未知 cause_code フォールバック挙動の網羅性で担保)。
- **プロパティ試験の対象拡張:** UNIT-001.1 State Machine は宣言的遷移表を持つため、hypothesis により「任意のイベント列から到達可能な状態のみが出現する」ことをプロパティで検証。UNIT-004.1 Integrity Validator は破損注入に対する頑健性を hypothesis で広範に検証。Inc.2 では UNIT-007.2 Priority Classifier の cause_code → (priority, category) 写像を hypothesis で網羅検証(候補)。
- **並行性試験の必須化:** UNIT-001.1、001.2、001.5、002.4 は複数スレッドから呼出されうるため、`pytest` の `threading` を使った競合試験を必須化。Inc.2 では UNIT-006.4 Alarm Task Watchdog(別スレッド監視)、UNIT-006.5 Alarm Path Redundancy(主系 / 予備系並行発報)、UNIT-007.1 Alarm Reporter Core(主系 / 予備系 2 インスタンス対応)も並行性試験必須。
- **SEP-001 境界の静的検証:** UNIT-005.3(クラス B 分離)と他ユニット(クラス C)との依存方向を `mypy` インポートグラフで検証。B → C への上向き依存は許容、C → B は禁止。
- **SEP-003 境界の静的検証(Inc.2、骨格):** UNIT-007.1 / 007.2(クラス B 分離)と検知群 / 制御コア(クラス C)との依存方向を AST 機械検証で担保。`vip_alarm.*` から `vip_ctrl.*` / `vip_sim.*` / `vip_integrity.*` への戻り値書込み禁止 + 例外伝播禁止を確認(`AlarmEvent` の不変性 + 単方向通知契約)。実装は Step 20 X〜の TDD で詳細化。

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

#### 7.3.8 UNIT-001.5 SW Watchdog(実施済、詳細)

**関連 SRS:** SRS-RCM-003(SW Watchdog タイムアウト監視)、**関連 RCM:** RCM-003(SW 側、ハートビート監視)、**関連 HZ:** HZ-001, HZ-002

> **Step 19 B9 整合化(2026-04-24、本節 v0.9 新規詳細化):** v0.8 までは §7.3.8 残骨格表で「**500 ms** 判定(境界 499/500/501)」と誤記されていたが、SDD v0.2 §4.8 / SRS-RCM-003 / RMF RCM-003 のいずれも SW 側は **300 ms**(HW 側が 500 ms)と規定している。本節で詳細化する際に訂正(MINOR 区分・CR 不要、SRS / SDD / RMF / SAD 本体不変)。B9 着手前クロスレビュー(7 度目運用)で運用性 1 論点 + 専門性 5 論点を抽出、ユーザー合意のもと推奨方針で進行:**運用性:** ① `WatchdogReason` enum 名 — SDD §4.8.C 擬似コードの `SW_HEARTBEAT_TIMEOUT` は state_machine.py 実装の既存 `SW_WATCHDOG` を使う(state_machine.py 不変、SDD 擬似コードは参考名扱い。B7/B8 「add-only / 既存成果物不変」の継続)。**専門性:** ① クロック DI(`clock: Callable[[], float]`、B4 パターン踏襲で決定論試験)、② クロック逆転時は安全側 = Trip(B4 判断の継続)、③ `check_once` テストフック公開(B4 パターン)、④ Logger 据置(SDD §4.8.B に `_logger` なし、B4 判断)、⑤ MC/DC 目標 100%(RCM 実装ユニット規定)。**UT 申し送り:** なし(階層防御の時間順序試験は UT で fake_clock を使えば決定論的に可能、subprocess / 実時間は不要)。

| 試験 ID | 対象 API / 観点 | 入力 / 条件 | 期待結果 | 種別 |
|---------|---------------|-----------|---------|------|
| UT-001.5-01 | 正常ハートビート | 100 ms 周期 × 10 回 | `is_tripped == False`、`on_watchdog_timeout` 未呼出 | 正常系 |
| UT-001.5-02 | ハートビート途絶 | 301 ms 経過 + `check_once` | `is_tripped == True`、`on_watchdog_timeout(SW_WATCHDOG)` 1 回 | RCM(003) |
| UT-001.5-03a | 境界 299 ms(Trip しない) | heartbeat 後 299 ms | `is_tripped == False` | 境界値 |
| UT-001.5-03b | 境界 300 ms ちょうど(Trip しない、`>` 判定) | heartbeat 後 `HEARTBEAT_TIMEOUT` | `is_tripped == False` | 境界値 |
| UT-001.5-03c | 境界 300 ms + ε(Trip) | heartbeat 後 `HEARTBEAT_TIMEOUT + 0.0001` | `is_tripped == True` | 境界値 |
| UT-001.5-03d | 最大検出遅延 350 ms(Trip) | heartbeat 後 `HEARTBEAT_TIMEOUT + MONITOR_INTERVAL` | `is_tripped == True`(SDD §4.8.D 最大検出遅延) | 境界値 |
| UT-001.5-04 | 並行 heartbeat | 2 スレッド × 50 回 × 1 ms | データ競合なし、`last_heartbeat == fake_clock()` | 並行 |
| UT-001.5-05 | クロック逆転 → Trip(安全側) | heartbeat 後に `set_to(0.05)` | `is_tripped == True`、`on_watchdog_timeout(SW_WATCHDOG)` 1 回 | 安全側設計判断 |
| UT-001.5-06a | Tripped 後 heartbeat 無視 | Trip 後に heartbeat + 0.1 s | `last_heartbeat` 不変 | 異常系(自動復帰禁止) |
| UT-001.5-06b | `check_once` 冪等 | Trip 後 `check_once` × 3 | `on_watchdog_timeout` 1 回のみ | 冪等性 |
| UT-001.5-07a | start/stop 正常 | `start()` → `stop()` | `is_running` が True → False | ライフサイクル |
| UT-001.5-07b | 2 重 start | `start()` × 2 | `RuntimeError("already started")` | 異常系 |
| UT-001.5-07c | 2 重 stop | `start()` → `stop()` × 2 | no-op(例外なし) | ライフサイクル |
| UT-001.5-07d | stop before start | 初期状態で `stop()` | no-op(例外なし) | ライフサイクル |
| UT-001.5-08 | State Machine 例外耐性 | `on_watchdog_timeout` が `RuntimeError` | `is_tripped == True`、`check_once` 例外伝播なし(SDD §4.8.E) | 異常系 |
| UT-001.5-09 | 定数 `HEARTBEAT_TIMEOUT == 0.3` | — | 300 ms 一致 | 契約 |
| UT-001.5-10 | 定数 `MONITOR_INTERVAL == 0.05` | — | 50 ms 一致 | 契約 |
| UT-001.5-11 | 実時間スレッド統合スモーク | `time.monotonic` + `start()` + 1 秒境界 | 1 秒以内に Trip、`on_watchdog_timeout(SW_WATCHDOG)` 呼出 | 統合スモーク |
| UT-001.5-12 | 階層防御(SW < HW 時間順序) | 同一 fake_clock に SW/HW 並列、301 ms → 501 ms | 301 ms 時点で SW のみ Trip、501 ms で HW も Trip(SW が先) | 二重冗長独立性 |

**ケース数目安:** 正常系 1、境界値 4、並行 1、安全側 1、異常系 4、冪等 1、ライフサイクル 4、契約 2、スモーク 1、階層防御 1 = **合計 19 件**(展開後 **19**、v0.8 骨格の「≥ 8」を大幅超過)
**MC/DC 目標:** **100%**(v0.8 骨格 100% を維持、コード規模 78 stmt / 12 branch で網羅可能)

#### 7.3.9 UNIT-001.2 Control Loop(実施済、詳細)

**関連 SRS:** SRS-011(100 ms 周期送出)、SRS-012(dose 到達自動停止)、SRS-031(状態観測)、SRS-P02(100 ms ±10%)、SRS-RCM-004(ハートビート送出側)、**関連 RCM:** RCM-004(SW 送出側)、**関連 HZ:** HZ-001, HZ-002

> **Step 19 B10 整合化(2026-04-29、本節 v0.10 新規詳細化):** v0.9 までは §7.3.9 残骨格表で「`pytest-benchmark` でサイクル計測」とされていたが、**B4/B5/B8/B9 教訓「非決定論的試験は IT へ」**を継続適用し、SRS-P02 ±10% 実時間周期精度試験は **ITPR §5.6 申し送り**(新規カテゴリ「実時間スレッド統計試験」)とする。本節で詳細化する際に骨格を更新(MINOR 区分・CR 不要、SRS / SDD / RMF / SAD 本体不変)。B10 着手前クロスレビュー(8 度目運用)で運用性 4 論点 + 専門性 5 論点を抽出、ユーザー合意のもと推奨方針で進行:**運用性 4 件:** ① `WatchdogReason.CONTROL_LOOP_EXCEPTION`(SDD §4.6.C 擬似コード)→ 既存 `WatchdogReason.OTHER` を使用(state_machine.py 不変、B9 「add-only」継続)、② `EventKind.AUTO_STOP_DURATION_REACHED`(SDD §4.6.C 擬似コード)→ duration-based 自動停止は SRS-012/031 にも記載なし、本 B10 で実装せず、SDD §4.6.C 当該分岐は将来の CR で整理申し送り(dose-based のみ実装)、③ Pump / Observer の Protocol 定義位置 → control_loop.py 内に新 Protocol(`PumpFlowController` / `PumpSnapshotObserver` / `PumpSnapshot`)を定義(UNIT-002.1/002.2 が将来これを満たす)、④ `Settings` 型 → records.py の `Settings`(3 フィールド)を `settings_provider` 経由で受け取り、flow_validator に渡す際は `flow_rate` を取り出して flow_validator.Settings を作る(自然な変換)。**専門性 5 件(推奨):** ① クロック DI(B4/B9 パターン踏襲)、② `tick()` テストフック公開(B4/B9 `check_once` 同型)、③ Logger 据置(SDD §4.6.B に `_logger` なし、B4/B9 判断継続)、④ SRS-P02 実時間周期精度試験は ITPR §5.6 申し送り、⑤ MC/DC 目標 100%(UTPR §7.4 規定)。**UT 申し送り:** SRS-P02 ±10% 実時間周期精度統計試験(1000 周期 P95 測定)+ `pytest-benchmark` CPU 占有率測定 → ITPR §5.6 新規カテゴリ。

| 試験 ID | 対象 API / 観点 | 入力 / 条件 | 期待結果 | 種別 |
|---------|---------------|-----------|---------|------|
| UT-001.2-01 | State.RUNNING でない `tick()` は no-op | sm = IDLE で `tick()` | `set_flow_rate` / `observe` / `heartbeat` 全て未呼出 | 正常系(状態前提) |
| UT-001.2-02 | RUNNING で `tick()` の主処理ディスパッチ | settings.flow_rate = 100.0 | sw/hw heartbeat 各 1 回、`set_flow_rate(100.0)` 1 回、`observe` 1 回 | 正常系 |
| UT-001.2-03 | heartbeat は pump 例外より先に送出 | pump.set_flow_rate が `RuntimeError` | sw/hw heartbeat 各 1 回(送出済)、`current() == ERROR`(SDD §4.6 キーポイント) | 順序保証 |
| UT-001.2-04 | Validator Err → State Machine 遷移 | settings.flow_rate = -1.0(NEGATIVE) | `set_flow_rate` 未呼出、`current() == ERROR`(WDT_TIMEOUT 経路) | RCM(004 SW) |
| UT-001.2-05 | accumulated > dose で AUTO_STOP | accumulated = 500.1, dose = 500.0 | `current() == STOPPED`(SRS-012) | RCM(SRS-012) |
| UT-001.2-06a | 境界 — accumulated == dose で AUTO_STOP | accumulated = 500.0, dose = 500.0 | `current() == STOPPED`(`>=` 判定、SDD §4.6.C) | 境界値 |
| UT-001.2-06b | 境界 — accumulated < dose で 継続 | accumulated = 499.999 | `current() == RUNNING` | 境界値 |
| UT-001.2-07 | settings_provider 例外 → ERROR | settings_provider が `RuntimeError` | `current() == ERROR`、heartbeat は送出済(SDD §4.6.E) | 異常系 |
| UT-001.2-08 | tick 例外で `WatchdogReason.OTHER` 記録 | pump.set_flow_rate が `RuntimeError` | `error_reason() == WatchdogReason.OTHER`(SDD §4.6.C 擬似コード `CONTROL_LOOP_EXCEPTION` の既存 enum マップ) | 異常系・運用性 |
| UT-001.2-09 | start/stop ライフサイクル | `start()` → `stop()` | `is_running` が True → False | ライフサイクル |
| UT-001.2-10 | 2 重 start | `start()` × 2 | `RuntimeError("already started")` | 異常系 |
| UT-001.2-11 | 2 重 stop | `start()` → `stop()` × 2 | no-op | ライフサイクル |
| UT-001.2-12 | stop before start | 初期状態で `stop()` | no-op | ライフサイクル |
| UT-001.2-13 | 定数 `PERIOD_SEC == 0.1` | — | 100 ms 一致 | 契約 |
| UT-001.2-14a | `tick()` 戻り値 — RUNNING でない | sm = IDLE | `False` | 契約 |
| UT-001.2-14b | `tick()` 戻り値 — RUNNING | RUNNING fixture | `True` | 契約 |
| UT-001.2-15 | heartbeat 引数なし契約(CR-0005 (a) 解消後) | fake_clock を 1.234 に進める | `sw.heartbeat()` / `hw.heartbeat()` 各 1 回(引数なし、各 Watchdog が内部 clock で取得) | 契約(`_HeartbeatSink`) |
| UT-001.2-16 | Validator が ControlContext を受信 | settings.flow_rate = 50.0 | `set_flow_rate(50.0)`(間接的に validate 通過確認) | 統合 |
| UT-001.2-17 | 実時間スレッド統合スモーク | `period_sec=0.02` で `start()` + 1 秒境界 | tick が動作し `set_flow_rate` 1 回以上呼出 | 統合スモーク |
| UT-001.2-18 | `PumpSnapshot` Protocol 準拠 | accumulated/elapsed/current_flow を持つ dataclass | 全フィールド一致 | 契約 |
| UT-001.2-19 | 周期オーバーラン警告ログ | `period_sec=0.0` で `start()` + 50 ms 動作 | "overrun" を含む WARNING ログ(SDD §4.6.E) | ログ網羅 |

**ケース数目安:** 正常系 2、順序保証 1、RCM 2、境界値 2、異常系 3、ライフサイクル 4、契約 5、統合スモーク 1、ログ 1 = **合計 21 件**(展開後 **20 + ログ 1 = 21 件**、骨格「≥ 12」を大幅超過)
**MC/DC 目標:** **100%**(コード規模 94 stmt / 14 branch で網羅可能、tick の状態前提分岐 + validation 経路 + auto-stop 分岐 + 例外経路 + overrun 分岐 全網羅)

#### 7.3.10 UNIT-002.1 Pump Simulator(実施済、詳細)

**関連 SRS:** SRS-030(シミュレート)、SRS-031(状態観測)、SRS-P01(±5% 精度)、SRS-RCM-004 HW 側被呼出側、**関連 RCM:** RCM-004(HW 側被呼出側 `force_stop_failsafe`)、**関連 HZ:** HZ-001, HZ-002

> **Step 19 B11 整合化(2026-04-29、本節 v0.11 新規詳細化):** v0.10 までは §7.3.10 残骨格表で「指令反映、`force_stop_failsafe` 冪等、SRS-030/031 準拠、積算量計算 / ≥ 10 / 95%」として簡略記載されていたが、本 B11 の詳細化で 21 ケースに展開、MC/DC 目標を **95% → 100%** に引き上げ(B5/B7/B8/B10 前例継続、コード規模 89 stmt / 14 branch で網羅可能)。残骨格 8 → 7 ユニットに繰り下げ(§7.3.11)。MINOR 区分・CR 不要、SRS / SDD / RMF / SAD 本体不変。**B11 着手前クロスレビュー(9 度目運用)で運用性 3 + 専門性 5 論点を抽出、ユーザー合意のもと推奨方針で進行:** 運用性 — ① **SRS-031 観測契約の公開方法** → 5 つのスレッドセーフ getter (`current_flow` / `accumulated_volume` / `elapsed_min` / `is_failsafe_active` / `failsafe_reason`) を `RLock` 保護下で実装、UNIT-002.2 Pump Observer が将来これらをラップして frozen `PumpSnapshot` を返す(SDD §4.10 と整合)、② **積算量オーバーフロー処理** → SRS-I-020 上限 9999.9 mL を超えたら `logger.warning` のみ出力(初回のみ)、加算継続。クランプは行わない(over-detection は UI 層 Inc.4 で対応)、③ **`release_failsafe()` の用途** → public で実装、UT 単体検証(本番経路 UNIT-005.1 CMD_ERROR_RESET は将来接続)。専門性 — ① `Decimal` 精度(`math.exp` のみ float→Decimal 変換)、② `RLock`(SDD §4.9.D 別スレッド呼出に必須)、③ SRS-P01 過渡応答試験(τ で 63%、5τ で 99%)、④ MC/DC 100% 引き上げ、⑤ `force_stop_failsafe` 並行勝利試験。**UT 申し送りなし**(本ユニットは決定論的 Decimal 演算のみ、実時間試験は不要)。

| 試験 ID | 対象 API / 観点 | 入力 / 条件 | 期待結果 | 種別 |
|---------|---------------|-----------|---------|------|
| UT-002.1-01 | 初期状態 | コンストラクタ直後 | current_flow=0、accumulated=0、elapsed_min=0、is_failsafe_active=False、failsafe_reason=None | 正常系 |
| UT-002.1-02 | `set_flow_rate` で target 更新 | `set_flow_rate(500)` + `advance_time(0.001)` | current_flow > 0(漸近開始) | 正常系 |
| UT-002.1-03 | 過渡応答 τ で 63% | `set_flow_rate(500)` + `advance_time(0.5)` | current_flow ≈ 500 * 0.6321 ±25 | SRS-P01 過渡 |
| UT-002.1-04 | 過渡応答 5τ で 99% | `set_flow_rate(500)` + `advance_time(2.5)` | current_flow ≈ 500 * 0.9933 ±10 | SRS-P01 過渡 |
| UT-002.1-05 | `advance_time(0)` → ValueError | `dt_sec=0.0` | `ValueError("dt must be positive")` | 異常系 |
| UT-002.1-06 | `advance_time(負)` → ValueError | `dt_sec=-1.0` | 同上 | 異常系 |
| UT-002.1-07 | 1 時間積算 | `set_flow_rate(100)` + `advance_time(3600)` | accumulated ≈ 100 ±5(SRS-P01 ±5%) | SRS-P01 定常 |
| UT-002.1-08 | `force_stop_failsafe` で current/target=0 | 流量 99% 到達後に `force_stop_failsafe(reason="HEARTBEAT_TIMEOUT")` | current_flow=0、is_failsafe_active=True、failsafe_reason="HEARTBEAT_TIMEOUT" | RCM(004 HW 被呼出) |
| UT-002.1-09 | `force_stop_failsafe` 冪等(初発 reason 保持) | `force_stop_failsafe("R1")` × 2 で reason 変更 | failsafe_reason="REASON_FIRST"(2 回目以降は無視) | 冪等性 |
| UT-002.1-10 | failsafe 中の `set_flow_rate` は no-op | failsafe 後 `set_flow_rate(500)` + `advance_time(2.5)` | current_flow=0 | 異常系 |
| UT-002.1-11 | failsafe 中の `reset` は no-op | failsafe 後 `reset()` | is_failsafe_active=True 維持 | 異常系 |
| UT-002.1-12 | failsafe 中 `advance_time` は時間のみ | 流量到達 → failsafe → `advance_time(60)` | current=0 / accumulated 不変 / elapsed_min は進む | SDD §4.9.C 仕様 |
| UT-002.1-13 | `release_failsafe` で復帰 | failsafe 後 `release_failsafe()` + `set_flow_rate(500)` + `advance_time(2.5)` | is_failsafe_active=False、current_flow > 400 | 復帰契約 |
| UT-002.1-14 | `release_failsafe` 未発動時は no-op | 初期状態で `release_failsafe()` | is_failsafe_active=False(変化なし) | 契約 |
| UT-002.1-15 | `reset()` で全状態が初期値 | 流量到達後に `reset()` | current=0、accumulated=0、elapsed_min=0 | 契約 |
| UT-002.1-16 | 定数 `TIME_CONSTANT_SEC == 0.5` | — | 0.5 一致 | 契約 |
| UT-002.1-17 | 並行性 — failsafe が set_flow_rate に勝つ | 2 スレッド × `Barrier` で同時呼出、setter 100 回 + force_stop_failsafe 1 回 | is_failsafe_active=True、current_flow=0(failsafe 勝利、SDD §4.9.D RLock 整合性) | 並行 |
| UT-002.1-18 | 境界 — `set_flow_rate(0)` で 0 維持 | `set_flow_rate(0)` + `advance_time(5)` | current=0、accumulated=0 | 境界値 |
| UT-002.1-19 | 境界 — `set_flow_rate(1200)` 上限 | SRS-O-001 上限 + `advance_time(2.5)` | current ≈ 1200 * 0.9933 ±60 | 境界値 |
| UT-002.1-20 | 積算量オーバーフロー警告 | 1200 mL/h で 9 時間進行 → accumulated > 9999.9 | accumulated > MAX_ACCUMULATED_VOLUME、"overflow" を含む WARNING ログ | ログ網羅(SRS-I-020) |
| UT-002.1-21 | SRS-031 観測契約 | 各種操作後の 5 getter | current_flow:Decimal / accumulated:Decimal / elapsed_min:Decimal / is_failsafe_active:bool / failsafe_reason:str(None) の型整合 | SRS-031 契約 |

**ケース数目安:** 正常系 2、SRS-P01 過渡 2、異常系 5、SRS-P01 定常 1、RCM 1、冪等 1、復帰契約 1、契約 4、境界値 2、並行 1、ログ網羅 1、SRS-031 契約 1 = **合計 21 件**(展開後 **21**、骨格「≥ 10」を倍超)
**MC/DC 目標:** **100%**(v0.10 骨格 95% から引き上げ、コード規模 89 stmt / 14 branch で網羅可能、failsafe 経路 + advance_time 分岐 + overflow 一回限り分岐 全網羅)

#### 7.3.11 UNIT-002.2 Pump Observer(実施済、詳細)

**関連 SRS:** SRS-031(状態観測)、SRS-I-020(内部観測 I/F 仕様)、**関連 RCM:** —(観測のみ)、**関連 HZ:** —

> **Step 19 B12 整合化(2026-04-30、本節 v0.12 新規詳細化):** 骨格「観測 API の不変性(pure)、状態整合性 / ≥ 6 / —」を **10 ケース、100%** に詳細化、MC/DC 目標を骨格の「—」から **100%** に明示(B5/B7/B8/B10/B11 前例継続、コード規模 20 stmt / 0 branch で網羅可能)。残骨格 7 → 6 ユニットに繰り下げ(§7.3.12)。MINOR 区分・CR 不要、SRS / SDD / RMF / SAD 本体不変。**B12 着手前クロスレビュー(10 度目運用)で運用性 2 + 専門性 5 論点を抽出、ユーザー合意のもと推奨方針で進行:** 運用性 — ① **atomic 性確保の方法** → SDD §4.10.C 設計判断通り Pump Simulator の `_lock` を借用し private フィールドを直接読む(`# noqa: SLF001` で抑制 + docstring に SDD §4.10.C 引用)。Observer が独自 lock を持つと Pump 更新と二重ロック競合になるため。Pump 側の API 表面積を増やさず B11 完了状態を維持(二重整合化を避ける)、② **PumpSnapshot のフィールド構成** → SDD §4.10.B 通り 6 フィールド(`current_flow / target_flow / accumulated_volume / elapsed_min / failsafe_active / observed_at`)を `frozen=True, slots=True` で実装。Control Loop の `PumpSnapshot` Protocol(3 プロパティ)を structural typing で satisfies。専門性 — ① frozen+slots dataclass で `FrozenInstanceError`、② `time.monotonic()` で観測時刻記録(連続 observe 単調増加)、③ 6 フィールドを単一 lock 区間で読む(SDD §4.10.C 逐語実装)、④ Observer は stateless(`_pump` 参照のみ)、⑤ MC/DC 100% 引き上げ(コード規模 20 stmt で網羅可能)。**UT 申し送りなし**(本ユニットは Decimal 演算 + lock 借用のみ、実時間試験不要)。

| 試験 ID | 対象 API / 観点 | 入力 / 条件 | 期待結果 | 種別 |
|---------|---------------|-----------|---------|------|
| UT-002.2-01 | 初期状態の observe | コンストラクタ直後 | snap.current_flow=0 / target_flow=0 / accumulated=0 / elapsed_min=0 / failsafe_active=False、observed_at > 0 | 正常系 |
| UT-002.2-02 | target_flow 反映 | `set_flow_rate(500)` + observe | snap.target_flow == 500 | 正常系 |
| UT-002.2-03 | advance_time 後の observe | `set_flow_rate(500)` + `advance_time(2.5)` + observe | current_flow > 400(5τ で 99%)、accumulated > 0、elapsed_min > 0 | 正常系 |
| UT-002.2-04 | failsafe 状態反映 | failsafe 後 observe | snap.failsafe_active=True、current_flow=0、target_flow=0 | 状態整合 |
| UT-002.2-05 | PumpSnapshot は frozen | `snap.current_flow = Decimal(999)` | `FrozenInstanceError`(SDD §4.10.B frozen 契約) | 不変性 |
| UT-002.2-06 | observed_at の単調性 | 連続 observe 50 回 | `pairwise(timestamps)` で全 prev <= curr | 単調性(SDD §4.10.F) |
| UT-002.2-07 | atomic 性 — 並行 advance_time 中の observe | 別スレッドで advance_time(0.01) を回しつつ observe を 200 回 | observed_at > 0 / elapsed_min >= 0 / accumulated >= 0(テアリングなし) | atomic 性(SDD §4.10.F) |
| UT-002.2-08 | Observer が ControlLoop Protocol を満たす | `proto: ControlLoopObserverProto = observer` | proto.observe() が成功し snap が `accumulated_volume / elapsed_min / current_flow` を持つ | structural typing |
| UT-002.2-09 | PumpSnapshot が ControlLoop Protocol を満たす | `proto: ControlLoopPumpSnapshotProto = snap` | 3 プロパティが Decimal | structural typing |
| UT-002.2-10 | observe は副作用なし | `set_flow_rate + advance_time` 後に observe を 100 回 | Pump の current/accumulated/elapsed が変化なし | pure |

**ケース数目安:** 正常系 3、状態整合 1、不変性 1、単調性 1、atomic 性 1、structural typing 2、pure 1 = **合計 10 件**(展開後 **10**、骨格「≥ 6」を超過)
**MC/DC 目標:** **100%**(v0.11 骨格「—」から明示化、コード規模 20 stmt / 0 branch で網羅可能)

#### 7.3.12 UNIT-001.3 Command Handler(実施済、詳細)

**関連 SRS:** SRS-010(start)、SRS-013(stop ≤ 200 ms)、SRS-014(pause/resume)、SRS-P03(start ≤ 500 ms)、SRS-P04(stop ≤ 50 ms ファストパス)、**関連 RCM:** —(State Machine RCM-019 と連携)、**関連 HZ:** HZ-001, HZ-002

> **Step 19 B13 整合化(2026-04-30、本節 v0.13 新規詳細化):** 骨格「コマンドキュー、stop ファストパス、順次処理、境界値 / ≥ 10 / 95%」を **23 ケース、100%** に詳細化、MC/DC 目標を 95% → **100%** に引き上げ(B5/B7/B8/B10/B11/B12 前例継続)。残骨格 6 → 5 ユニットに繰り下げ(§7.3.13)。**B13 着手前クロスレビュー(11 度目運用)で運用性 4 + 専門性 5 論点を抽出、ユーザー合意のもと推奨方針で進行:** 運用性 — ① `Command` / `CommandKind` を command_handler.py 内に定義(UNIT-005.1 が将来 import)、② `_is_acceptable_in_state` は state_machine.py の既存 `TRANSITION_TABLE` を引用(DRY 原則、二重定義回避)、③ SRS-P03/P04 統計的時間試験(P95)は ITPR §5.6 申し送り(B4/B5/B8/B10 教訓 5 例目)、UT は緩い 200 ms 境界スモーク 1 件のみ、④ `Command(kind, payload)` シンプル構造で payload は opaque(検証は UNIT-005.1 責務)。専門性 — ① 値オブジェクト群 frozen dataclass(B11/B12 パターン継続)、② dispatch スレッド管理 B4/B9/B10 パターン、③ `uuid.uuid4()` token 一意性、④ MC/DC 100% 引き上げ、⑤ `mypy --strict src tests` を CI と同じ引数でローカル必須実行(B12 教訓継続)。**UT 申し送り:** SRS-P03/P04 P95 統計試験 → ITPR §5.6「実時間スレッド統計試験」カテゴリ(B10 既存)。MINOR 区分・CR 不要、SRS / SDD / RMF / SAD 本体不変。

| 試験 ID | 対象 API / 観点 | 入力 / 条件 | 期待結果 | 種別 |
|---------|---------------|-----------|---------|------|
| UT-001.3-01 | IDLE で START Accepted | `enqueue(START)` | `Accepted(token)`、token は非空 str | 正常系 |
| UT-001.3-02 | await_completion で State 遷移 | `enqueue(START)` + `await_completion(timeout_ms=1000)` | `Completed`、State Machine が RUNNING | 統合 |
| UT-001.3-03 | 不正状態で Rejected | IDLE で `enqueue(STOP)` | `Rejected(INVALID_FOR_CURRENT_STATE)` | 異常系 |
| UT-001.3-04 | キュー満杯で Rejected | dispatch 停止状態で `MAX_QUEUE_SIZE+5` 件 enqueue | 16 件 Accepted、17 件目で `Rejected(QUEUE_FULL)` | 境界(満杯) |
| UT-001.3-05 | stop ファストパス — 通常を破棄 | dispatch 未起動で PAUSE × 5 + STOP enqueue → 起動 | STOP が先に Completed、PAUSE × 5 は `Failed(SupersededByStopError)` | RCM(SRS-P04) |
| UT-001.3-06 | ERROR_RESET ファストパス | ERROR 状態で `enqueue(ERROR_RESET)` | `Completed`、State が IDLE | RCM(SRS-P04) |
| UT-001.3-07 | 不明 token への await | 任意 UUID で `await_completion` | `Failed(UnknownTokenError)` | 異常系 |
| UT-001.3-08 | timeout — TimedOut | dispatch 未起動で enqueue + `await_completion(timeout_ms=10)` | `TimedOut(elapsed_ms=10)` | 異常系 |
| UT-001.3-09 | token 一意性 — 並行 100 件 | 10 スレッド × 10 件 enqueue | 全 token がユニーク(set 重複なし) | 並行 |
| UT-001.3-10 | 順次処理(FIFO) | RUNNING で PAUSE | 1 件目完了後 State が PAUSED | 統合 |
| UT-001.3-11 | 完了通知 cleanup | 同 token で 2 回 await_completion | 1 回目 Completed、2 回目 `UnknownTokenError` | 契約 |
| UT-001.3-12 | task 例外でループ継続 | `request_transition` を例外 stub に差替、後に通常 enqueue | 1 件目 Failed(error)、ループ継続して 2 件目 Completed | 異常系(SDD §4.7.E) |
| UT-001.3-13 | start/stop ライフサイクル | `start()` → `stop()` | `is_running` True → False | ライフサイクル |
| UT-001.3-14 | 2 重 start | `start()` × 2 | `RuntimeError("already started")` | 異常系 |
| UT-001.3-15 | 2 重 stop | `start()` → `stop()` × 2 | no-op | ライフサイクル |
| UT-001.3-16 | stop before start | 初期状態で `stop()` | no-op | ライフサイクル |
| UT-001.3-17 | 定数 `MAX_QUEUE_SIZE == 16` | — | 16 一致 | 契約 |
| UT-001.3-18 | `STOP_KINDS` 契約 | — | `frozenset({STOP, ERROR_RESET})` | 契約 |
| UT-001.3-19 | stop ファストパス スモーク | RUNNING で `enqueue(STOP)` + `time.monotonic()` 計測 | 200 ms 以内に Completed(SRS-P04 機能スモーク、P95 統計は ITPR 申し送り) | 統合スモーク |
| UT-001.3-20 | コマンド種別マッピング | RUNNING で `enqueue(PAUSE)` | State が PAUSED(`CMD_PAUSE` event 経由) | 統合 |
| UT-001.3-21 | Command の不変性 | `cmd.kind = ...` | `dataclasses.FrozenInstanceError` | 不変性 |
| UT-001.3-22 | payload は opaque | `Command(kind=START, payload={"key": "value"})` | enqueue/await が正常完了(payload は検証されず透過) | 契約 |
| UT-001.3-23 | 未マップコマンド拒否 | `enqueue(CONFIRM_RESUME)` | `Rejected(INVALID_FOR_CURRENT_STATE)`(`_CMD_TO_EVENT` に未登録、UNIT-004.2 経由が将来) | 契約 |

**ケース数目安:** 正常系 1、統合 3、異常系 6、境界 1、RCM 2、並行 1、契約 5、ライフサイクル 4 = **合計 23 件**(展開後 **23**、骨格「≥ 10」を倍超)
**MC/DC 目標:** **100%**(v0.12 骨格 95% から引き上げ、コード規模 164 stmt / 24 branch、`# pragma: no cover` 4 件は race-window/防御コード分岐)

#### 7.3.13 UNIT-002.3 Event Injection Stub(実施済、詳細)

**関連 SRS:** SRS-032(Inc.2 イベント注入 I/F 受容性)、SRS-I-040(Inc.2 予定の入力 I/F、本 Inc.1 ではスタブのみ)、**関連 RCM:** —(Inc.2 で RCM-005/006/007 等が紐付く想定)、**関連 HZ:** HZ-004(将来連携)

> **Step 19 B14 整合化(2026-04-30、本節 v0.14 新規詳細化):** 骨格「Inc.2 以降のスタブ、本 Inc.1 では空動作の確認のみ / ≥ 3 / —」を **12 ケース、stmt 100% / branch 100%** に詳細化(MC/DC 目標は SDD §4.11 + UTPR §7.4 通り「—」据置、コード規模 33 stmt / 0 branch、Inc.2 正式機能化時に再評価)。残骨格 5 → 4 ユニットに繰り下げ(§7.3.14)。MINOR 区分・CR 不要、SRS / SDD / RMF / SAD 本体不変。**B14 着手前クロスレビュー(12 度目運用)で運用性 4 + 専門性 5 論点を抽出、ユーザー合意のもと推奨方針で進行:** 運用性 — ① 配置パッケージは `src/vip_sim/event_injection.py`(SDD §4.11.F + UTPR §3 / §11 パス整合、他 vip_sim/ ユニットと一貫)、② 命名は `VirtualHwEventKind`(`vip_ctrl.state_machine.EventKind` との名前衝突回避、import 時 alias 不要)、③ no-op 検証は Pump Simulator + Pump Observer 連携で「inject 後も observe 値不変」を契約試験化(SDD §4.11.F.2「Inc.1 では伝播なし」)、④ `metadata: Mapping[str, object]` で受領(Inc.2 で `types.MappingProxyType` 化検討の余地)。専門性 — ① 値オブジェクト `VirtualHwEvent` を `frozen=True, slots=True`(B11/B12/B13 パターン継続、`_empty_metadata` 専用 factory で `mypy --strict` 整合)、② `_buffer = collections.deque(maxlen=1000)` でリングバッファ自動破棄、③ `_lock = threading.Lock()`(再帰不要)、④ MC/DC 目標は SDD/UTPR §7.4 通り「—」据置、stmt/branch 100% で網羅、⑤ `mypy --strict src tests` を CI と同じ引数でローカル必須実行(B12/B13 教訓継続、本 B14 で `unused-ignore`(test 中の不要な `# type: ignore[arg-type]`)を CI 前ローカル mypy で検出・修正)。**UT 申し送りなし**(本ユニットは Inc.1 では no-op スタブのみ、Inc.2 で Pump 連動・閉塞圧力反映・気泡フラグ・薬液切れカットオフ等の追加 UT が `EventInjectionStub.inject` の Pump 副作用試験として加わる予定)。

| 試験 ID | 対象 API / 観点 | 入力 / 条件 | 期待結果 | 種別 |
|---------|---------------|-----------|---------|------|
| UT-002.3-01 | `inject` + `recent_events` 基本動作 | OCCLUSION イベント 1 件 `inject` + `recent_events(1)` | 同イベントが 1 件返る | 正常系 |
| UT-002.3-02 | FIFO 順序保持 | OCCLUSION → AIR_BUBBLE → RESERVOIR_EMPTY を順次 `inject` + `recent_events(10)` | 投入順で 3 件返る | 正常系 |
| UT-002.3-03 | `limit` による末尾切り出し | 5 件 `inject` + `recent_events(limit=2)` | 末尾 2 件のみ返る | 正常系 |
| UT-002.3-04 | `limit` がバッファ件数より大きい場合 | 3 件 `inject` + `recent_events()`(default=100) | 全 3 件返る | 境界 |
| UT-002.3-05 | リングバッファ満杯時の自動破棄 | 1001 件 `inject` + `recent_events(1000)` | 1000 件、最古破棄、最新が末尾(SDD §4.11.F.3) | 境界 |
| UT-002.3-06 | no-op 試験(SDD §4.11.F.2) | `inject` 3 件 + Pump.observe 比較 | observe 値(current/target/accumulated/elapsed/failsafe)が inject 前後で不変 | 統合 |
| UT-002.3-07 | 並行 `inject` の損失なし | 10 スレッド × 10 件 `inject` + `recent_events(100)` | 全 100 件記録、各 kind が出現 | 並行 |
| UT-002.3-08 | VirtualHwEvent frozen 契約 | `event.severity = 99` | `dataclasses.FrozenInstanceError`(B12 パターン) | 不変性 |
| UT-002.3-09 | VirtualHwEventKind 列挙網羅 | enum メンバ集合 | `{OCCLUSION, AIR_BUBBLE, RESERVOIR_EMPTY}`(SDD §4.11.B、3 値) | 契約 |
| UT-002.3-10 | `recent_events` 返却 list の独立性 | 返り値を `append` + `recent_events` 再取得 | 内部バッファ不変(エイリアスなし) | 契約 |
| UT-002.3-11 | severity / metadata 透過 | severity=7 / metadata={...} で `inject` + `recent_events(1)` | 同 severity/metadata/kind で観測 | 契約 |
| UT-002.3-12 | metadata 省略時のデフォルト | `VirtualHwEvent(kind=..., severity=..., occurred_at=...)`(metadata 省略) | `event.metadata == {}`(`_empty_metadata` factory パス網羅) | 契約 |

**ケース数目安:** 正常系 3、境界 2、統合 1、並行 1、不変性 1、契約 4 = **合計 12 件**(展開後 **12**、骨格「≥ 3」を 4 倍)
**MC/DC 目標:** **— 据置**(SDD §4.11 / UTPR §7.4 通り、コード規模 33 stmt / 0 branch、stmt 100% / branch 100% で網羅)

#### 7.3.14 UNIT-004.2 Resume Confirmation Gate(実施済、詳細)

**関連 SRS:** SRS-028(自動再開禁止)、SRS-RCM-016(再開確認ダイアログ)、**関連 RCM:** RCM-016(再開確認、HZ-007 保護手段)、**関連 HZ:** HZ-007(永続化データ破損 / 不安全な自動再開)

> **Step 19 B15 整合化(2026-04-30、本節 v0.15 新規詳細化):** 骨格「needs_confirm トグル、期限チェック、状態遷移連携 / ≥ 8 / 100%(RCM-016)」を **15 ケース、stmt 100% / branch 100% / MC/DC 100%** に詳細化。残骨格 4 → 3 ユニットに繰り下げ(§7.3.15)。MINOR 区分・CR 不要、SRS / SDD / RMF / SAD 本体不変。**B15 着手前クロスレビュー(13 度目運用)で運用性 4 + 専門性 5 論点を抽出、ユーザー合意のもと推奨方針で進行:** 運用性 — ① `ResumeDetail` 型は `resume_gate.py` 内に新規定義(関心分離、Inc.1 では UNIT-004.2 が唯一の consumer、Inc.4 で integrity_validator → resume_gate のデータパスが wire される際に `vip_persist.records` への移動を検討)、② `StateMachine` を constructor 注入(B9/B10 watchdog/control_loop パターン継続、UT で `unittest.mock.Mock(spec=StateMachine)` 化)、③ Logger 据置(B4/B9 パターン継続、SDD 擬似コードの `_logger.log_resume_*` は標準 `logging.Logger.info` / `warning` で実装)、④ `check_expiry` の定期呼出責任は外部(本ユニットでは API のみ提供、Inc.1 では UT で動作確認、Inc.4 UI で wire)。専門性 — ① 値オブジェクト群 `frozen=True, slots=True`(`PendingResume` / `ResumeDetail` / `Confirmed` / `WrongToken` / `NotPending` / `Expired`、B11/B12/B13/B14 パターン継続)、② `secrets.token_hex(16)` 128 ビット token(SDD §4.14 設計判断逐語実装)、③ `hmac.compare_digest` 定数時間比較(同上)、④ `time.monotonic()` でクロック逆転耐性(B9 watchdog パターン継続、`clock: Callable[[], float]` constructor 注入で UT が fake clock 注入可)、⑤ **MC/DC 100% 引き上げ + `mypy --strict src tests` ローカル必須実行**(B12/B13/B14 教訓継続、4 ステップ連続適用、本 B15 で fixture 戻り値型不整合(`yield` → `return` 変換に伴う `Iterator[X]` 注釈残存)を CI 前ローカル mypy で検出・修正)。**UT 申し送りなし**(本ユニットは決定論的 monotonic + secrets だけで完結、実時間試験不要)。

| 試験 ID | 対象 API / 観点 | 入力 / 条件 | 期待結果 | 種別 |
|---------|---------------|-----------|---------|------|
| UT-004.2-01 | `set_pending` token は 32 hex | `set_pending(detail)` | token は 32 桁 hex 文字列(128 bit エントロピー、SDD §4.14.A) | 正常系 |
| UT-004.2-02 | `is_pending` / `pending_detail` の遷移 | `set_pending` 前後 | `is_pending` は False → True、`pending_detail` は None → detail | 正常系 |
| UT-004.2-03 | 正 token confirm + State Machine 連携 | `set_pending(detail)` + `confirm(token)` | `Confirmed(detail)`、`request_transition(TransitionEvent(CMD_RESUME, meta={"resume_token": token}))` 呼出、`is_pending` False | 統合(SRS-RCM-016) |
| UT-004.2-04 | 誤 token は WrongToken、pending 維持 | `set_pending` + `confirm("0"*32)` | `WrongToken`、`is_pending` True、State Machine 不変 | 異常系 |
| UT-004.2-05 | 未 pending での confirm | `confirm("a"*32)` | `NotPending`、State Machine 不変 | 異常系 |
| UT-004.2-06 | 2 重 set_pending | `set_pending` × 2 回 | 2 回目で `RuntimeError("ResumeGate already pending")`(SDD §4.14.E) | 異常系 |
| UT-004.2-07 | 期限切れ後の confirm | `set_pending` + `clock.advance(EXPIRY_SEC+1)` + `confirm(token)` | `Expired`、pending 解除、State Machine 不変 | RCM-016 境界 |
| UT-004.2-08 | cancel で pending 解除 | `set_pending(token)` + `cancel()` + `confirm(token)` | cancel 後 `is_pending` False、再 confirm は `NotPending` | ライフサイクル |
| UT-004.2-09 | token ユニーク 1000 回 cycle | `set_pending` → `cancel` を 1000 回 | 全 token がユニーク(128 bit エントロピー試験) | RCM-016 セキュリティ |
| UT-004.2-10 | check_expiry で期限超過時警告 | `set_pending` + `clock.advance(EXPIRY_SEC+1)` + `check_expiry()` | `_logger.warning("resume_expir...")` 発火、pending は解除されない(明示的 confirm/cancel が必要) | RCM-016 監視 |
| UT-004.2-11 | check_expiry で期限内は静黙 | `set_pending` + `clock.advance(EXPIRY_SEC-1)` + `check_expiry()` | warning ログなし | 境界 |
| UT-004.2-12 | PendingResume frozen 契約 | `pending.token = "1"*32` | `dataclasses.FrozenInstanceError`(B12 パターン) | 不変性 |
| UT-004.2-13 | cancel 未 pending 時 no-op | 未 pending で `cancel()` × 2 回 | 例外なし、`is_pending` False、State Machine 不変(冪等) | ライフサイクル |
| UT-004.2-14 | check_expiry 未 pending 時静黙 | 未 pending で `check_expiry()` | warning ログなし | ライフサイクル |
| UT-004.2-15 | 並行 confirm の排他性 | 同一 token を 2 スレッド `Barrier` 同期で `confirm` | `Confirmed` × 1 + `NotPending` × 1、`request_transition` は 1 回のみ呼出 | 並行 |

**ケース数目安:** 正常系 2、統合 1、異常系 3、境界 2、RCM 3、不変性 1、ライフサイクル 3 = **合計 15 件**(展開後 **15**、骨格「≥ 8」を倍近く)
**MC/DC 目標:** **100%**(v0.14 骨格 100% 維持、コード規模 80 stmt / 12 branch、`confirm` 4 分岐 + `set_pending` 2 分岐 + `check_expiry` 3 分岐 + `is_pending` / `pending_detail` の 2 分岐 全網羅、RCM-016)

#### 7.3.15 UNIT-005.1 Control API(実施済、詳細)

**関連 SRS:** SRS-IF-002(外部コマンド I/F)、SRS-010(start)、SRS-011(`flow_rate`)、SRS-012(自動停止)、SRS-013(stop)、SRS-014(pause/resume)、**関連 RCM:** —(委譲先で実装、UNIT-001.3 経由 RCM-019 / UNIT-004.2 経由 RCM-016)、**関連 HZ:** HZ-001、HZ-002(委譲先で対応)

> **Step 19 B16 整合化(2026-04-30、本節 v0.16 新規詳細化):** 骨格「7 コマンド(start/stop/pause/resume/reset/error_reset/confirm_resume)の委譲、例外伝搬 / ≥ 10 / 90%」を **21 ケース、stmt 100% / branch 100% / MC/DC 100%(API 委譲層)** に詳細化(コード規模 75 stmt / 6 branch、骨格 MC/DC 90% を超過し 100% 達成、`start` の 3 分岐 + `confirm_resume` の 4 分岐 + 例外耐性 6 経路 + payload 透過 全網羅)。残骨格 3 → 2 ユニットに繰り下げ(§7.3.16)。MINOR 区分・CR 不要、SRS / SDD / RMF / SAD 本体不変。**B16 着手前クロスレビュー(14 度目運用)で運用性 4 + 専門性 5 論点を抽出、ユーザー合意のもと推奨方針で進行:** 運用性 — ① 配置パッケージは `src/vip_api/control_api.py`(SDD §4.15 + UTPR §3 既存パス整合)、② `ApiResult` は sealed hierarchy(`Ok` / `ValidationFailed` / `ApiRejected` を `vip_api/control_api.py` 内に定義 + Resume Gate の `Confirmed` / `WrongToken` / `Expired` / `NotPending` を re-export して useless mapping layer を回避)、③ `ValidationApi` は Protocol で structural typing 受け(`vip_api` が `vip_api_b` を import せず SEP-001 分離維持、UNIT-005.3 が将来 satisfy 予定、UT では `Mock(spec=ValidationApi)`)、④ `Settings(drug_name)` 乖離は本 B16 のスコープに含めず Inc.4 UI 着手時に整合化(B15 申し送りの再評価:`vip_persist.records.Settings` 改修は B6/B7 試験への波及が大きく、本 B16 では Control API 単体動作の試験で OK と判断)。専門性 — ① 値オブジェクト群 `frozen=True, slots=True`(`Ok` / `ValidationFailed` / `ApiRejected` / `ValidationError`、B11/B12/B13/B14/B15 パターン継続)、② 例外を投げない契約は `start` / `confirm_resume` / `_safe_enqueue` の各 try/except で `ApiRejected(InternalError.UNEXPECTED_EXCEPTION)` 復帰(SDD §4.15.E 逐語実装)、③ `Settings.model_dump()` で pydantic を `Mapping[str, object]` に変換し Command Handler の payload 契約に整合(pydantic を Handler に漏らさない)、④ Command Handler / Resume Gate / Validation API は constructor 注入(B9/B10/B15 パターン継続)、⑤ MC/DC 100% 引き上げ(コード規模 75 stmt / 6 branch で網羅可能)+ `mypy --strict src tests` ローカル必須実行(B12/B13/B14/B15 教訓継続、5 ステップ連続適用、本 B16 で防御コード `# pragma: no cover` の `Statement is unreachable` を CI 前ローカル mypy で検出 → 防御コード削除で代替、`AcceptResult` の sealed Union が将来変更されたら mypy が警告で気付ける運用に転換)。**UT 申し送りなし**(本ユニットは委譲層のみ、実装ロジックは委譲先の UT で網羅済)。

| 試験 ID | 対象 API / 観点 | 入力 / 条件 | 期待結果 | 種別 |
|---------|---------------|-----------|---------|------|
| UT-005.1-01 | start 正常フロー | Validator Pass + Handler `Accepted` | `Ok(token)`、`enqueue(Command(START, payload))`、payload は `Settings.model_dump()` 結果 | 正常系 |
| UT-005.1-02 | start 検証失敗 | Validator が `[ValidationError]` 返却 | `ValidationFailed(errors)`、Handler に enqueue されない | 異常系(SRS-IF-002) |
| UT-005.1-03 | start Handler Rejected | Handler が `Rejected(INVALID_FOR_CURRENT_STATE)` | `ApiRejected(reason)` 透過 | 異常系 |
| UT-005.1-04〜08 | stop / pause / resume / reset / error_reset | 各メソッド呼出 | `Ok(token)`、`enqueue(Command(<kind>, payload=None))` | 正常系 × 5 (parametrize) |
| UT-005.1-09 | confirm_resume Confirmed | Gate が `Confirmed(detail)` | `Ok(token)` | 正常系 |
| UT-005.1-10〜12 | confirm_resume WrongToken / Expired / NotPending | Gate が各失敗を返却 | 同型のまま透過(API 側で再ラップしない) | 異常系 × 3 (parametrize) |
| UT-005.1-13 | await_command 透過 | Handler.await_completion が `Completed(state)` | 戻り値 `Completed(state)` をそのまま透過 | 正常系 |
| UT-005.1-14 | await_command TimedOut / Failed 透過 | Handler が `TimedOut(elapsed_ms)` / `Failed(error)` | 同型のまま透過(API は変換しない) | 異常系 × 2 (parametrize) |
| UT-005.1-15 | start 例外耐性 | Handler.enqueue が RuntimeError raise | `ApiRejected(InternalError.UNEXPECTED_EXCEPTION)`、伝播なし | RCM(SDD §4.15.E) |
| UT-005.1-16 | start ValidationApi 例外耐性 | Validation API が ValueError raise | 同上、伝播なし | RCM |
| UT-005.1-17 | confirm_resume 例外耐性 | Resume Gate が RuntimeError raise | 同上、伝播なし | RCM |
| UT-005.1-18 | ApiResult 値オブジェクト frozen 契約 | `Ok` / `ApiRejected` / `ValidationFailed` / `ValidationError` の各代入 | `dataclasses.FrozenInstanceError`(B12 パターン) | 不変性 |
| UT-005.1-19 | ApiResult Union 網羅性 | 7 種戻り値型を `isinstance(s, Union)` 検査 | 全 True、命名・export 整合性 | 契約 |
| UT-005.1-20 | stop 系 5 メソッド例外耐性 | 5 メソッド × Handler.enqueue が RuntimeError | 全て `ApiRejected(InternalError.UNEXPECTED_EXCEPTION)` で復帰 | RCM(line 224-226 網羅) |

**ケース数目安:** 正常系 8(UT-005.1-01/04〜08/09/13)、異常系 6(UT-005.1-02/03/10〜12/14)、RCM 4(UT-005.1-15〜17/20)、不変性 1、契約 1 = 展開後 **21 件**(骨格「≥ 10」を倍超)
**MC/DC 目標:** **100%**(v0.15 骨格 90% から引き上げ、コード規模 75 stmt / 6 branch、`start` 3 分岐 + `confirm_resume` 4 分岐 + try/except 例外捕捉 3 経路 + `_safe_enqueue` 例外 1 経路 + Accepted/Rejected 分岐 全網羅)

**Step 19 F1.6 追加 — UT-005.1-bridge(`vip_api/_validation_bridge.py` Adapter、CR-0004 (b)):**

| 試験 ID | 対象 API / 観点 | 入力 / 条件 | 期待結果 | 種別 |
|---------|---------------|-----------|---------|------|
| UT-005.1-bridge-01 | 整合 Settings → 空 list(`Ok` パススルー) | flow=60, dose=60, duration=60(SRS-004 整合) | `validate_settings(settings) == []` | 正常系 |
| UT-005.1-bridge-02 | 範囲外単独 → ValidationError 1 件 | flow=1500.0(範囲外) | `len == 1`、`field=="flow_rate"`、`message` に `out_of_range` / `1500` / `0.0..1200.0` 含む | 変換契約(`OutOfRange`) |
| UT-005.1-bridge-03 | 多重失敗 → 集約変換 | flow=2000, dose=20000(2 つ範囲外 + 整合性違反) | `len >= 2`、fields に `flow_rate` / `dose_volume` 含む | 集約契約 |
| UT-005.1-bridge-04 | 整合性違反 → `settings_consistency` field | flow=60, dose=70, duration=60(diff>1%) | `field=="settings_consistency"`、`message.startswith("inconsistency:")` | 変換契約(`Inconsistency`) |
| UT-005.1-bridge-05 | factory + Protocol 適合 | `make_validation_api()` 戻り値 | `ValidationApi` Protocol 構造的整合、`validate_settings(consistent) == []` | 契約 |
| UT-005.1-bridge-06 | ControlApi 実体注入 | `ControlApi(validation_api=ClassBValidationApiAdapter())` で `start(consistent_settings)` | `Ok(token=...)`、Handler.enqueue 1 回呼出 | 統合契約(CR-0004 本質) |

**Adapter ケース数:** 6 件(`_validation_bridge.py` カバレッジ:25 stmt / 10 branch、`assert_never` 防御分岐 4 行を除き完全網羅、CR-0004 (b) 採用根拠の sealed hierarchy 完全網羅で実質到達不能)

#### 7.3.16 UNIT-005.2 State Observer API(実施済、詳細)

**関連 SRS:** SRS-IF-003(状態観測 API、読み取り専用)、SRS-O-010(machine_state 出力)、SRS-UX-002(副作用なし / idempotent)、**関連 RCM:** —(読み取り専用)、**関連 HZ:** —

> **Step 19 B17 整合化(2026-04-30、本節 v0.17 新規詳細化):** 骨格「薄いラッパー、observer 委譲、非 block / ≥ 6 / —」を **19 ケース、stmt 100% / branch 100%** に詳細化(MC/DC 目標は SDD §4.16 + UTPR §7.4 通り「—」据置、コード規模 30 stmt / 2 branch)。残骨格 2 → 1 ユニットに繰り下げ(§7.3.17)。MINOR 区分・CR 不要、SRS / SDD / RMF / SAD 本体不変。**B17 着手前クロスレビュー(15 度目運用)で運用性 4 + 専門性 5 論点を抽出、ユーザー合意のもと推奨方針で進行:** 運用性 — ① 配置 `src/vip_api/state_observer_api.py`(SDD §4.16 + UTPR §3 既存パス、Control API と同居)、② `StateSnapshot` は frozen+slots dataclass(SDD「frozen pydantic」より軽量、B12 PumpSnapshot パターン継続、出力値オブジェクトに pydantic 検証は不要)、③ 注入 3 種(StateMachine / PumpObserver / ResumeConfirmationGate)を constructor 注入(B9/B10/B15/B16 パターン継続、UT で `Mock(spec=...)` 化)、④ `observed_at` は `datetime.now(UTC)`(B15 Resume Gate パターン継続);専門性 — ① `StateSnapshot` を frozen+slots dataclass(B11〜B16 パターン継続、`dataclasses.FrozenInstanceError` を契約試験化)、② SDD §4.16.C 擬似コード逐語実装(4 回の独立 atomic 取得 + StateSnapshot 構築)、③ `error_reason` 文字列化(`reason.name` で SDD 設計判断「内部 enum 非露出」逐語実装)、④ **例外伝播**(SDD §4.16.E「例外なし、設計目標は例外なし。注入オブジェクトの例外は呼出側責任」逐語実装、B16 Control API と異なり try/except なし)、⑤ MC/DC 目標 — 据置 + stmt/branch 100% で網羅 + `mypy --strict src tests` ローカル必須実行(B12〜B16 教訓継続、6 ステップ連続適用、本 B17 で `PLC0415` 関数内 import を CI 前ローカル ruff で検出 → 関数外 top-level 化で対処)。**UT 申し送り(継続):** Inc.4 UI 着手時に Resume Gate API 拡張(`pending_set_at_wall() -> datetime | None` accessor 追加)で `resume_set_at` の `set_at_wall` 透過を実装予定(SDD §4.16.B `Optional[datetime]` 仕様の Inc.1 範囲では None 固定で合致、本 B17 で UT-005.2-05 が機能制約を契約試験化)。

| 試験 ID | 対象 API / 観点 | 入力 / 条件 | 期待結果 | 種別 |
|---------|---------------|-----------|---------|------|
| UT-005.2-01 | observe_state 基本観測 | 3 注入の Mock を初期値で配置 | StateSnapshot.machine_state=IDLE / pump.current_flow / resume_pending=False / observed_at>=now | 正常系 |
| UT-005.2-02 | idempotent / 副作用なし | 100 回連続呼出 | mutating API は一切呼ばれない、read-only API のみ各 100 回 | 契約(SRS-UX-002) |
| UT-005.2-03 | machine_state 集約(parametrize 5 状態) | StateMachine.current が IDLE/RUNNING/PAUSED/STOPPED/ERROR | StateSnapshot.machine_state がそのまま反映 | 正常系 × 5 |
| UT-005.2-04 | pump 集約 | PumpObserver.observe が任意の PumpSnapshot | StateSnapshot.pump がそのまま反映(`is` 同一性) | 正常系 |
| UT-005.2-05 | resume_pending=True で Inc.1 範囲では resume_set_at is None | is_pending=True + ResumeDetail 返却 | resume_pending=True、resume_set_at is None(Inc.1 では set_at_wall 非露出、Inc.4 で拡張予定) | 契約(SDD §4.16.B Inc.1 範囲) |
| UT-005.2-06 | resume_pending=False | is_pending=False + pending_detail=None | resume_pending=False、resume_set_at=None | 正常系 |
| UT-005.2-07 | ERROR 状態で error_reason 文字列化 | machine_state=ERROR + WatchdogReason.SW_WATCHDOG | error_reason に "SW_WATCHDOG" を含む文字列(内部 enum 非露出) | 契約(SDD §4.16 設計判断) |
| UT-005.2-08 | 非 ERROR 状態で error_reason=None(parametrize 4 状態) | IDLE/RUNNING/PAUSED/STOPPED | error_reason=None | 正常系 × 4 |
| UT-005.2-09 | observed_at 単調性 | 50 回連続観測 | pairwise(timestamps) で全 prev <= curr | 単調性(B12 パターン) |
| UT-005.2-10 | StateSnapshot frozen 契約 | snap.machine_state = ... を試行 | dataclasses.FrozenInstanceError(B12 パターン) | 不変性 |
| UT-005.2-11 | 注入オブジェクト例外の伝播 | StateMachine.current が RuntimeError raise | RuntimeError が呼出側まで伝播(SDD §4.16.E) | 契約(設計目標) |
| UT-005.2-12 | observed_at は UTC | snap.observed_at.tzinfo | tzinfo is datetime.UTC | 境界 |

**ケース数目安:** 正常系 11(UT-005.2-01/03×5/04/06/08×4)、契約 4(UT-005.2-02/05/07/11)、単調性 1、不変性 1、境界 1 + parametrize 展開 = **合計 19 件**(骨格「≥ 6」を 3 倍超)
**MC/DC 目標:** **— 据置**(SDD §4.16 / UTPR §7.4 通り、コード規模 30 stmt / 2 branch、stmt/branch 100% で網羅)

#### 7.3.17 UNIT-005.3 Validation API(実施済、詳細、クラス B)

**関連 SRS:** SRS-UX-001(validate_settings API surface)、SRS-004(整合性 ±1%)、SRS-005(範囲検証)、**関連 RCM:** —(クラス B 分離側)、**関連 HZ:** HZ-006(設定値整合性違反)

> **Step 19 B18 整合化(2026-04-30、本節 v0.18 新規詳細化):** 骨格「SEP-001 分離検証、内部例外握りつぶし契約、境界値 / ≥ 8 / 90%」を **16 ケース、stmt 100% / branch 100% / MC/DC 100%(クラス B 分離ユニット、骨格 90% を超過)** に詳細化。残骨格 1 → 0 ユニットに繰り下げ、**Inc.1 全 17 ユニット完成**。MINOR 区分・CR 不要、SRS / SDD / RMF / SAD 本体不変。**B18 着手前クロスレビュー(16 度目運用)で運用性 4 + 専門性 5 論点を抽出、ユーザー合意のもと推奨方針で進行:** 運用性 — ① 配置 `src/vip_api_b/validation_api.py`(SAD §9 SEP-001 + UTPR §3 既存パス整合)、② `Settings` は `vip_persist.records` から import(値オブジェクトのみ、SEP-001 は「副作用伝播禁止」が本旨で値オブジェクト共有は許容)、③ SEP-001 機械検証は AST で `vip_api_b/validation_api.py` が `vip_ctrl` / `vip_sim` / `vip_integrity` / `vip_api` を import しないことを確認(`vip_persist.records` のみ許容、UT-005.3-13 で機械検証)、④ **`drug_name` 検証は Inc.1 では削除して Inc.4 申し送り**(B15/B16/B17 で `vip_persist.records.Settings` に `drug_name` 不在を確認済、SDD §4.17.C drug_name MissingField チェックは Inc.4 で Settings 拡張時に追加予定);専門性 5 — ① `ValidationResult` sealed hierarchy(`Ok` / `Err`)+ `ValidationFailure` sealed hierarchy(`OutOfRange` / `Inconsistency` / `MissingField`)を frozen+slots dataclass(B11〜B17 パターン継続)、② SDD §4.17.C 擬似コード逐語実装(範囲 → 整合性、drug_name 部分は Inc.1 削除)、③ `TOLERANCE = Decimal("0.01")` 1% 許容差(SRS-004 逐語実装)、④ **例外握りつぶし契約**(SDD §4.17.E:try/except で `Err([Inconsistency("internal: ...")])` で復帰、B16 Control API と同じパターン、SEP-001 boundary を保証)、⑤ MC/DC 100% 引き上げ + `mypy --strict src tests` + `ruff` ローカル必須実行(B12〜B17 教訓継続、7 ステップ連続適用、本 B18 で RUF100 / FURB157 / RUF002 × 2 / FBT001 を CI 前ローカル ruff で検出 → 手動修正)。**UT 申し送り:** `drug_name` 検証は Inc.4 で Settings 拡張時に追加(B15/B16/B17/B18 chain)。

| 試験 ID | 対象 API / 観点 | 入力 / 条件 | 期待結果 | 種別 |
|---------|---------------|-----------|---------|------|
| UT-005.3-01 | 整合 Settings | flow_rate × duration_min / 60 == dose_volume | `Ok(settings)` | 正常系 |
| UT-005.3-02 | flow_rate 範囲外 | flow_rate=1500.0 (> 1200.0) | `Err` に `OutOfRange("flow_rate", ...)` | 異常系 |
| UT-005.3-03 | dose_volume 範囲外 | dose_volume=99999.0 (> 9999.9) | `Err` に `OutOfRange("dose_volume", ...)` | 異常系 |
| UT-005.3-04 | duration_min 範囲外 (parametrize 2) | duration_min=0 / 6000 | `Err` に `OutOfRange("duration_min", ...)` | 境界 × 2 |
| UT-005.3-05 | 整合性違反 SRS-004 | 500 mL/h × 60 min / 60 = 500 ≠ 800 | `Err` に `Inconsistency` | 異常系 |
| UT-005.3-06 | 整合性境界 ±1% (parametrize 3) | dose=500.00 (0%) / 504.99 (+0.998%) / 505.01 (+1.002%) | Pass / Pass / Fail | 境界 × 3 |
| UT-005.3-07 | 多重失敗の収集 | flow_rate=1500.0 + 整合 dose | `Err` に複数 failures が列挙 | 異常系 |
| UT-005.3-08 | 内部例外握りつぶし契約 SDD §4.17.E | `patch("Decimal")` で例外注入 | 例外伝播せず `Err([Inconsistency("internal:...")])` | RCM(SEP-001 boundary) |
| UT-005.3-09 | 純粋関数 / 副作用なし | 同じ入力で複数回呼出 | 戻り値の Ok / Err と内訳が一致 | 契約(SRS-UX-001) |
| UT-005.3-10 | ValidationFailure frozen 契約 | `OutOfRange` / `Inconsistency` / `MissingField` の各代入 | `dataclasses.FrozenInstanceError`(B12 パターン) | 不変性 |
| UT-005.3-11 | ValidationResult Union 網羅性 | `Ok` / `Err` の isinstance 検査 | 全 True、命名・export 整合性 | 契約 |
| UT-005.3-12 | ValidationFailure 基底型 整合性 | `OutOfRange` / `Inconsistency` / `MissingField` を `list[ValidationFailure]` に格納 | 全件型に整合(structural typing) | 契約 |
| UT-005.3-13 | **SEP-001 import グラフ機械検証** | `ast.parse` で `validation_api.py` を解析 | `{vip_ctrl, vip_sim, vip_integrity, vip_api}` の import が 0 件 | 契約(SAD §9 SEP-001) |

**ケース数目安:** 正常系 2(UT-005.3-01/09)、異常系 5(UT-005.3-02/03/05/07 + UT-005.3-08 RCM)、境界 5(UT-005.3-04 × 2 + UT-005.3-06 × 3)、不変性 1、契約 3 + parametrize 展開 = **合計 16 件**(骨格「≥ 8」を倍超)
**MC/DC 目標:** **100%**(v0.17 骨格 90% から引き上げ、コード規模 55 stmt / 12 branch、範囲 3 分岐 + 整合性 1 分岐 + 例外握りつぶし 1 経路 + 失敗集約 1 分岐 全網羅)

#### 7.3.18 UNIT-005.4 CLI Entry Point(実施済、詳細、Step 19 H1 で新規追加)

> **Step 19 H1 整合化(2026-05-07、本節 v0.20 新規追加):** Inc.1 全 17 ユニット完成(B18 = v0.18)後、Step 19 G STPR 骨格化完了を経て、Step 19 H1(STPR §6.2 ST-OPS の前提となる CLI エントリポイント実装)着手前のクロスレビューで **ISS-H-001 を発見** — SRS-OPS-002(必須、`vip-ctrl` CLI)が要求されているが Inc.1 全 17 ユニットに CLI が含まれていない計画文書間乖離。本 H1 で **UNIT-005.4 CLI として §3.2 ユニット一覧 + SDD §4.18 + 本 §7.3.18 を一括追加**(全 17 → 18 ユニット)。MINOR 区分・CR 不要(SCMP §4.1「軽微」、F1〜F7 で確立した「計画文書間整合化 → 同 PR 訂正」パターン継続)。

##### 7.3.18.A 試験方針

- 配置 `src/vip_ctrl/cli.py`(`vip_ctrl` パッケージ既存、SAD §3 ARCH-005 ファサード相当)
- pyproject.toml `[project.scripts]` で `vip-ctrl = "vip_ctrl.cli:main"` 登録(SRS-OPS-002 必須要求の実装)
- **対話 start/stop コマンド経路は Inc.4 で正式実装** — 本 H1 では `--version` / `--diagnose` / デフォルト 3 経路に限定(SDD §3 設計方針 + B17 申し送り = 対話 UI は Inc.4)
- **DI 駆動テスト容易化:** `main(argv, stdout, stderr)` で `IO[str]` を引数化し subprocess を使わずに in-memory `io.StringIO` 経由で出力検査
- **UT 15 ケース構成:** `--version` 2 件 + `--diagnose` 6 件 + デフォルト 2 件 + argparse エラー 2 件 + 構造契約 3 件
- **MC/DC 目標 100%:** コード規模 78 stmt / 10 branch、UT 15 ケースで全分岐網羅(Step 19 H1 達成)

##### 7.3.18.B 試験ケース表

| 試験 ID | 試験項目 | 入力 | 期待結果 | 種別 |
|---------|--------|------|---------|------|
| UT-005.4-01 | `--version` 1 行出力 | `["--version"]` | 1 行 stdout(`vip-ctrl <version>`)、stderr 空、return 0 | 正常系 |
| UT-005.4-02 | `--version` fallback | `patch("version", side_effect=PackageNotFoundError)` | `unknown` 出力 + return 0 | 異常系(契約)|
| UT-005.4-03 | `--diagnose` レコード不存在 | `--persist-path /tmp/no.json` | `record_present=false`, `integrity_ok=true`, `level=info` | 正常系(SRS-OPS-003)|
| UT-005.4-04 | `--diagnose` 整合レコード | atomic_writer.write 経由で good record 配置 | `record_present=true`, `integrity_ok=true`, SRS-OPS-010 必須 5 キー全件 | 正常系 |
| UT-005.4-05 | `--diagnose` checksum 不一致 | checksum 部を改竄したレコード | `integrity_ok=false`, `level=warning`, `failure_count >= 1`, `failures` に `Checksum*` を含む | RCM(HZ-007 検出)|
| UT-005.4-06 | `--diagnose` JSON 不正 | `b"not a valid json {"` | `record_present=true`, `integrity_ok=false`, `failure_count=0` | 異常系 |
| UT-005.4-07 | `--diagnose` UTF-8 デコード失敗 | `b"\\xff\\xfe..."` | `integrity_ok=false` | 異常系 |
| UT-005.4-08 | `--diagnose` `atomic_writer.read` ReadErr | `patch.object(atomic_writer, "read", return_value=ReadErr(OSError))` | `record_present=false`, `integrity_ok=false`, `level=warning` | 異常系(契約)|
| UT-005.4-09 | デフォルト レコード不存在 | `--persist-path /tmp/no.json` | stderr に Inc.1 / Inc.4 申し送りメッセージ、stdout に `boot_snapshot` JSON Lines、`default_state=IDLE` | 正常系(SRS-OPS-003)|
| UT-005.4-10 | デフォルト 整合レコード | atomic_writer.write 経由 | `record_present=true`, `integrity_ok=true` | 正常系 |
| UT-005.4-11 | argparse 相互排他違反 | `["--version", "--diagnose"]` | `SystemExit(2)` | 契約 |
| UT-005.4-12 | argparse 未知引数 | `["--unknown-flag"]` | `SystemExit(2)` | 契約 |
| UT-005.4-13 | `build_parser` 単独 | parser.parse_args([]) / `--persist-path` 指定 | デフォルト + カスタムパス両方を args として返却 | 契約(再利用性)|
| UT-005.4-14 | SRS-OPS-010 必須 5 キー網羅 | `--diagnose` + デフォルトの 2 行を取得 | 全行に `timestamp / level / component / event / details` を含む | 契約(SRS-OPS-010)|
| UT-005.4-15 | `_diagnose` ヘルパ契約 | 任意 path | `DiagnoseResult` 型 + `bool` 型保証 | 契約 |

**ケース数目安:** 正常系 5 + 異常系 4 + RCM 1(checksum 不一致 = HZ-007 検出)+ 契約 5 = **合計 15 件**(骨格基準なし、本 H1 が新規追加)
**MC/DC 目標:** **100%**(コード規模 78 stmt / 10 branch、`--version` fallback 1 経路 + `--diagnose` 5 分岐(不存在/ReadErr/decode 失敗/Ok/FailsafeRecommended)+ argparse 相互排他 + デフォルト 2 経路 全網羅)

##### 7.3.18.C 申し送り

- **対話 start/stop コマンドは Inc.4 で正式実装**(本 H1 では未提供、Inc.4 UI 層で Control Loop / Command Handler / Watchdog 等の既存スレッド lifecycle と統合)
- **STPR §6.2 ST-OPS.1-03 の対話 start/stop 要求は Inc.4 申し送り**(ISS-H-002、Step 19 H2 で STPR 修正予定)
- **CLI レベル試験(ST-OPS):** Step 19 H2 で `tests/system/test_ops_acceptance.py` を新規実装、subprocess.Popen + venv 隔離で SRS-OPS-001〜004 / 010〜012 を E2E 検証

**合計ケース数目安(全 18 ユニット):** **≥ 160 件**(B1〜B18 で 294 件実測 + UNIT-005.4 15 件 = **309 件実測 / 骨格 0**)。**Inc.1 全 18 ユニット完成、骨格残ゼロ**(Step 19 H1 で UNIT-005.4 追加によりユニット数が 17 → 18 に確定)。最終的な件数は実測値で確定。

#### 7.3.1.G UNIT-001.1 State Machine — Inc.2 拡張(骨格、v0.22、CR-0012 / Step 20 F)

> **Step 20 F 整合化(2026-05-10、本節 v0.22 新規追加):** SDD-VIP-001 v0.5 §4.1.G(Inc.2 拡張、CR-0009 / Step 20 E)で骨格化された UNIT-001.1 のアラーム発報経路 + ACK / SILENCE 状態遷移追加に対応する Inc.2 拡張試験観点を骨格記述。Inc.1 既存 UT-001.1-01〜12(展開後 62 件、Step 19 B2 完了)は据置、Inc.2 では UT-001.1-13〜 として追補(具体的 UT-UID は SDD v0.6 候補 + Step 20 X〜の TDD 着手前のクロスレビューで確定)。

**Inc.2 拡張の関連 SRS:** SRS-044(アラーム確認・消音、IEC 60601-1-8 §6.4)、SRS-ALM-008(確認・消音操作)、SRS-RCM-006(発報必達)
**Inc.2 拡張の関連 RCM:** RCM-006(発報必達 = 検知群が `request_state_transition` を発行できなかった場合の対処)、RCM-019 既存(状態遷移保護 + 新規アラーム経路の整合確認)
**Inc.2 拡張の関連 HZ:** HZ-004(検知失敗 → アラーム失敗の連鎖)、HZ-005(アラーム失敗単独)

**Inc.2 拡張の試験観点(骨格、Step 20 X〜の TDD で UT-UID 採番 + 詳細化):**

| 観点番号 | 観点 | 種別 | 関連 SDD |
|---------|------|------|---------|
| UT-001.1-G01〜 | `request_state_transition(target, reason)` API 受容契約(IF-U-013、検知群経路)| 正常系 + RCM | §4.1.G IF-U-013 |
| UT-001.1-G05〜 | `request_alarm_acknowledge(alarm_id)` API 経路(SRS-044 ACK)| 正常系 + 異常系 | §4.1.G ACK |
| UT-001.1-G09〜 | `request_alarm_silence(alarm_id, duration_sec)` API 経路 + 高優先度 ≤ 120 秒制限の State Machine 側非強制契約(Alarm Reporter Core 側で強制)| 正常系 + 契約 | §4.1.G SILENCE + IEC 60601-1-8 §6.4 |
| UT-001.1-G13〜 | 新規 EventKind(`ALARM_RAISED` / `ALARM_ACKED` / `ALARM_SILENCED` / `ALARM_CLEARED`)の状態遷移表追補(SDD v0.6 候補で確定後に詳細化)| RCM(RCM-019)| §4.1.G EventKind |
| UT-001.1-G17〜 | アラーム発報経路と既存 RCM-019 状態遷移保護の整合性(両系統の独立性 + 競合時の優先順位)| 並行 + RCM | §4.1.G + Inc.1 §4.1 |

**ケース数目安:** 5 観点 × 3〜4 サブケース = **≥ 15 件**(Inc.2 実装時に詳細化)
**MC/DC 目標:** **100%**(RCM-019 全分岐 = Inc.1 維持 + Inc.2 アラーム経路追加分の新規分岐)

**SDD v0.6 候補で詳細化する項目(SDD §4.1.G 申し送りと整合):**

- アラーム発報経路の状態遷移表(具体的状態名 + ALARM_RAISED/ACKED/SILENCED/CLEARED 各イベントとの対応)
- IF-U-013 / IF-U-007 呼出順序契約(検知群 → State Machine → Alarm Reporter Core の順)の試験設計
- ACK / SILENCE 状態の永続化要否(SRS-DATA-001 連携、Inc.2 範囲では非永続を仮置)に伴う UT スコープ確定

---

#### 7.3.13.G UNIT-002.3 Event Injection Stub — Inc.2 拡張(骨格、v0.22、CR-0012 / Step 20 F、no-op 解除)

> **Step 20 F 整合化(2026-05-10、本節 v0.22 新規追加):** SDD-VIP-001 v0.5 §4.11.G(Inc.2 拡張、CR-0009 / Step 20 E、no-op 解除方針確定)で骨格化された UNIT-002.3 の `VirtualHwEventKind` 4 種化(`BATTERY_LOW` 追加)+ Pump への伝播経路 + IF-U-015 `read_sensor` 新規に対応する Inc.2 拡張試験観点を骨格記述。Inc.1 既存 UT-002.3-01〜12(全 12 件 Pass、Step 19 B14 完了)は据置、Inc.2 では UT-002.3-13〜 として追補。**注:UT-002.3-06(no-op 退化検出試験)は Inc.2 で「inject 後 Pump 状態が変化する」契約に転換するため、Inc.2 実装時に UT-002.3-06 を破棄 → 代わりに UT-002.3-G01 系列の正の伝播試験を導入(SDD §4.11.G で予告済)**。

**Inc.2 拡張の関連 SRS:** SRS-I-040(イベント注入 4 種確定)、SRS-040(閉塞検知)、SRS-041(気泡検知)、SRS-042(薬液切れ検知)、SRS-043(バッテリ低下検知)
**Inc.2 拡張の関連 RCM:** RCM-009(閉塞冗長 2 系統)、RCM-010(気泡多段)、RCM-006(発報必達 = 残量切れ + バッテリ低下)
**Inc.2 拡張の関連 HZ:** HZ-004(閉塞 / 気泡 / 残量切れ事象シーケンス、EV-HZ004-002/003)、HZ-009(バッテリ低下、EV-HZ009-001、Inc.2 新規識別)

**Inc.2 拡張の試験観点(骨格):**

| 観点番号 | 観点 | 種別 | 関連 SDD |
|---------|------|------|---------|
| UT-002.3-G01〜 | `BATTERY_LOW` enum 値の `VirtualHwEventKind` 4 種化(SRS-I-040 確定)| 契約 | §4.11.G enum 拡張 |
| UT-002.3-G03〜 | `inject(OCCLUSION)` で Pump 内部閉塞フラグセット → IF-U-015 `read_sensor(OCCLUSION_PRIMARY/SECONDARY)` 経由で UNIT-006.1 検知群が異常値を読める(no-op 解除契約、Inc.1 UT-002.3-06 の真逆)| 統合 + RCM | §4.11.G no-op 解除 |
| UT-002.3-G07〜 | `inject(AIR_BUBBLE)` の警告 / 危険 2 段センサー(`AIR_BUBBLE_WARN` / `AIR_BUBBLE_CRITICAL`)経由 UNIT-006.2 連動 | 統合 | §4.11.G + UNIT-006.2 |
| UT-002.3-G09〜 | `inject(RESERVOIR_EMPTY)` の `RESERVOIR` センサー経由 UNIT-006.3 連動 | 統合 | §4.11.G + UNIT-006.3 |
| UT-002.3-G11〜 | `inject(BATTERY_LOW)` の `BATTERY` センサー経由 UNIT-006.6 連動(HZ-009 EV-HZ009-001 駆動)| 統合 + HZ-009 駆動 | §4.11.G + UNIT-006.6 |
| UT-002.3-G13〜 | `read_sensor(SensorKind)` 6 種 sealed enum の API 契約(SDD §5.1 IF-U-015 詳細化)+ 冗長 2 系統センサーの独立性(SRS-RCM-009 根拠)| 契約 + RCM | §5.1 IF-U-015 + SDD v0.6 候補 |
| UT-002.3-G17〜 | Inc.1 互換性確保(本 v0.5 の inject API 既存シグネチャを破壊しない、SDD §4.11.G 申し送り)| 契約(回帰)| §4.11.G 互換性 |

**ケース数目安:** 7 観点 × 2〜3 サブケース = **≥ 18 件**(Inc.2 実装時に詳細化)
**MC/DC 目標:** **100%**(SDD v0.5 の MC/DC「—」据置 → Inc.2 で正式機能化に伴い 100% に引き上げ、no-op 解除 + Pump 状態遷移ロジック網羅)

**SDD v0.6 候補で詳細化する項目(SDD §4.11.G 申し送りと整合):**

- `inject` が Pump 状態をどう変更するかの状態モデル(各 EventKind ごとの Pump 内部フラグセット規則)に伴う UT 設計
- `BATTERY_LOW` の severity 値と SRS-043 閾値判定アルゴリズムとの対応試験
- IF-U-015 `read_sensor` のシグネチャと SensorKind 6 種の Pump 側実装に伴う UT 設計

---

#### 7.3.15.G UNIT-005.1 Control API — Inc.2 拡張(骨格、v0.22、CR-0012 / Step 20 F)

> **Step 20 F 整合化(2026-05-10、本節 v0.22 新規追加):** SDD-VIP-001 v0.5 §4.15.G(Inc.2 拡張、CR-0009 / Step 20 E)で骨格化された UNIT-005.1 の `acknowledge_alarm` / `silence_alarm` API 追加(SRS-044、IEC 60601-1-8 §6.4)に対応する Inc.2 拡張試験観点を骨格記述。Inc.1 既存 UT-005.1-01〜20 + UT-005.1-bridge-01〜06(全 27 件 Pass、Step 19 B16 + F1.6 完了)は据置、Inc.2 では UT-005.1-G01〜 として追補。

**Inc.2 拡張の関連 SRS:** SRS-044(アラーム確認・消音、IEC 60601-1-8 §6.4)、SRS-ALM-008(確認・消音操作)
**Inc.2 拡張の関連 RCM:** —(委譲、UNIT-007.1 + UNIT-001.1 拡張で実装)
**Inc.2 拡張の関連 HZ:** HZ-005(アラーム失敗時の操作経路、間接)

**Inc.2 拡張の試験観点(骨格):**

| 観点番号 | 観点 | 種別 | 関連 SDD |
|---------|------|------|---------|
| UT-005.1-G01〜 | `acknowledge_alarm(alarm_id)` 正常転送(IF-U-014 経由 ARCH-007.1 + UNIT-001.1 ALARM_ACKED 遷移依頼)| 正常系 | §4.15.G |
| UT-005.1-G03〜 | `acknowledge_alarm` の例外耐性(Alarm Reporter Core 例外 → `Err(InternalError.UNEXPECTED_EXCEPTION)`、伝播なし、Inc.1 SDD §4.15.E 契約継続)| 異常系 + RCM | §4.15.G |
| UT-005.1-G05〜 | `silence_alarm(alarm_id, duration_sec)` 正常転送 | 正常系 | §4.15.G |
| UT-005.1-G07〜 | 高優先度 ≤ 120 秒制限の Control API 側非強制契約(ARCH-007.1 側で強制 = 本 UNIT は転送のみ、SDD §4.15.G 申し送り)| 契約 | §4.15.G + IEC 60601-1-8 §6.4 |
| UT-005.1-G09〜 | `silence_alarm(duration_sec > 120)` 高優先度時の `Err(SilenceTooLong)` 透過(ARCH-007.2 Priority Classifier 連携、SDD v0.6 候補)| 異常系 | §4.15.G + UNIT-007.2 |
| UT-005.1-G11〜 | 既存 Inc.1 7 メソッド(start / stop / pause / resume / reset / error_reset / confirm_resume)の Inc.1 互換性(シグネチャ + 戻り値型不変、Inc.1 既存 UT 全件 Pass 維持)| 契約(回帰)| §4.15.G 既存 API 不変 |

**ケース数目安:** 6 観点 × 2〜3 サブケース = **≥ 14 件**(Inc.2 実装時に詳細化)
**MC/DC 目標:** **100%**(API 委譲層、Inc.1 の 100% 維持 + 新 acknowledge_alarm / silence_alarm の try/except 例外捕捉 + Result 型 Ok/Err 分岐 全網羅)

**SDD v0.6 候補で詳細化する項目(SDD §4.15.G 申し送りと整合):**

- `acknowledge_alarm` / `silence_alarm` の戻り値型(`Ok(None)` / `Err(AlarmNotFound)` / `Err(SilenceTooLong)` 等)の確定に伴う UT 設計
- 同時複数アラーム時の優先順位(IEC 60601-1-8 §6.1 + ARCH-007.2 で集約 = Control API は転送のみ)に伴う UT スコープ確定

---

#### 7.3.19 UNIT-006.1 Occlusion Detector(Inc.2 新規、実施済、詳細、v0.23、CR-0017 / Step 20 X3)

**関連 SRS:** SRS-040(閉塞検知)、SRS-RCM-009(冗長 2 系統)、SRS-ALM-004(高優先度・テクニカル発報)、SRS-IF-010(Alarm I/F 本実装)
**関連 RCM:** RCM-009(閉塞検知冗長化、Designed → Verified 化目標、Inc.2 完了時)
**関連 HZ:** HZ-004(検知失敗 → アラーム失敗連鎖、EV-HZ004-001 駆動)
**安全クラス:** C(SAD §9 SEP-000、非分離)
**実装パッケージ:** `src/vip_detection/occlusion.py` v0.1(Step 20 X1 PR #67 マージ `551f862` で TDD 実装、84 stmt + 18 branch、stmt/branch 100%) + 共通 `src/vip_detection/protocols.py` v0.1(47 stmt、stmt/branch 100%)

> **Step 20 X3 整合化(2026-05-13、本節 v0.23 詳細化):** Step 20 X1(CR-0015 / PR #67 マージ `551f862`)で TDD 実装した `tests/unit/test_occlusion_detector.py`(19 ケース)と Step 20 X2(CR-0016 / PR #69 マージ `f42ed77`)で詳細化した SDD §4.19(11 サブセクション §4.19.A〜H + §4.19.G.x 申し送り 5 項目)に整合する形で、v0.22 までの骨格(8 観点表)を Inc.1 既存節同等粒度の個別 UT-006.1-NN 行詳細表に展開。**詳細化スコープは「実装した項目のみ」**(Step 20 X2 と同流儀):UT-006.1-01〜18 = 19 ケースのみを本 §7.3.19 で詳細化、未実装の UT-006.1-19+(並行 `tick` 耐性)+ 周期 `tick` 試験 + 片系故障内部ロジック詳細(タイムアウト・ノイズ閾値・連続エラーカウント)は本節末尾「UTPR v0.24 候補で詳細化する項目」に申し送り(SDD v0.7 §4.19.G.x + UNIT-002.3 拡張と並行詳細化予定)。

**試験ケース定義(実施済):**

| 試験 ID | 対象 API / 観点 | 入力 / 条件 | 期待結果 | 種別 |
|---------|---------------|-----------|---------|------|
| UT-006.1-01 | `_evaluate` OR 論理(両系下回り) | primary = secondary = threshold − 10 kPa | `Healthy` | 正常系 + RCM(parametrize) |
| UT-006.1-02 | `_evaluate` OR 論理(主系単独超過) | primary = threshold + 10、secondary = threshold − 10 | `Detected` | 正常系 + RCM(parametrize) |
| UT-006.1-03 | `_evaluate` OR 論理(副系単独超過) | primary = threshold − 10、secondary = threshold + 10 | `Detected` | 正常系 + RCM(parametrize) |
| UT-006.1-04 | `_evaluate` OR 論理(両系超過) | primary = secondary = threshold + 10 | `Detected` | 正常系 + RCM(parametrize) |
| UT-006.1-04b | `Detected.triggering_channels` 構成 | 主系単独超過(03 シナリオ) | `OCCLUSION_PRIMARY ∈ triggering_channels` かつ `OCCLUSION_SECONDARY ∉ triggering_channels` | 契約(SDD §4.19.D) |
| UT-006.1-05 | 閾値境界 inclusive(`>=`)主系 | primary == threshold、secondary < threshold | `Detected`(`>=` 採用、SDD §4.19.F.1) | 境界値 |
| UT-006.1-06 | 閾値境界 inclusive(`>=`)副系 | primary < threshold、secondary == threshold | `Detected`(`>=` 採用、SDD §4.19.F.1) | 境界値 |
| UT-006.1-07 | 片系故障 → `Degraded`(主系故障)| primary `healthy=False`(値超過)、secondary < threshold | `Degraded(failed_channel=OCCLUSION_PRIMARY)`(故障 channel 無視、SDD §4.19.F.1)| RCM(RCM-009 冗長性)|
| UT-006.1-08 | 片系故障 → `Degraded`(副系故障)| primary < threshold、secondary `healthy=False`(値超過) | `Degraded(failed_channel=OCCLUSION_SECONDARY)` | RCM(RCM-009 冗長性)|
| UT-006.1-09 | 片系故障 + 他系超過 → `Detected` 継続 | primary `healthy=False`(値下回り)、secondary > threshold | `Detected`、`OCCLUSION_SECONDARY ∈ triggering_channels`(故障側で他系の検出をマスクしない) | RCM(RCM-009 冗長性キーシナリオ)|
| UT-006.1-10 | 両系故障 → `Failed`(`_evaluate`)| primary = secondary 共に `healthy=False` | `Failed`(SDD §4.19.D、両系不信時の safe-side 表現) | RCM + 異常系 |
| UT-006.1-11 | 両系故障 tick → ERROR 遷移 + alarm なし | 両系 `healthy=False` で `tick()` | `state_machine.calls == [(ERROR, "occlusion_detection_unavailable")]` かつ `reporter.events == []`(SDD §4.19.F.5、safe-side 遷移のみ、Detected alarm の fabrication 禁止) | RCM + 異常系 |
| UT-006.1-12 | 発報 → 遷移依頼順序契約 | 主系単独超過で `tick()`、共有 `order: list[str]` を `_TracingReporter` + `_TracingStateMachine` で trace | `order == ["alarm", "transition"]` かつ `state_machine.calls == [(ERROR, "occlusion_detected")]`(SDD §4.19.F.4、IF-U-007 経由 → IF-U-013 経由の順序、SAD v0.2 §11.1)| 統合(順序契約)|
| UT-006.1-13 | `AlarmEvent` 内容契約 | 主系単独超過で `tick()`、`clock` lambda が 42.5 を返却 | `event.cause_code == "occlusion"`、`event.priority is HIGH`、`event.category.value == "technical"`、`event.occurred_at == approx(42.5)`(SDD §4.19.F.4、IEC 60601-1-8 §6.1 高優先度 / §5.1.4 テクニカル、`clock` 戻り値透過 = SRS-ALM-004 契約)| 契約(SRS-ALM-004)|
| UT-006.1-14 | Reporter 例外時の遷移継続(SEP-003)| `_RaisingReporter`(`report_alarm` で `RuntimeError` 送出)を注入、主系単独超過で `tick()` | `tick()` が例外伝播せず、`reporter.events == [送出済 1 件]` かつ `state_machine.calls == [(ERROR, "occlusion_detected")]`(SDD §4.19.F.4 例外吸収、SEP-003 例外伝播禁止契約)| 契約 + SEP-003 |
| UT-006.1-15 | 連続検知時の冪等性(armed 連動)| 主系単独超過のまま `tick()` × 2 回連続 | `reporter.events` 長 == 1 かつ `state_machine.calls` 長 == 1(armed フラグ False で発報 + 遷移依頼両方を抑制、SDD §4.19.F.4)| RCM 冪等(armed 連動)|
| UT-006.1-16 | `Healthy` 経由再 arm | `_StepReader` で 3 ステップ readings 切替(検知 → 健全 → 検知再発)、`tick()` × 3 | `reporter.events` 長 == 2 かつ `state_machine.calls` 長 == 2(Healthy 経由で armed = True に再 arm、SDD §4.19.F.3)| RCM 冪等(再 arm)|
| UT-006.1-17 | Sensor 全例外 → `Failed` 変換 | `_ScriptedSensorReader` の `raises` に primary + secondary 両系を指定、`tick()` | `tick()` が例外伝播せず、`reporter.events == []` かつ `state_machine.calls == [(ERROR, "occlusion_detection_unavailable")]`(SDD §4.19.F.2 `_safe_read` 例外吸収 → `Decimal(0) + healthy=False` プレースホルダ → `_evaluate` で両系故障扱い → `Failed`)| 契約 + RCM(SEP-003)|
| UT-006.1-18 | Sensor 片例外 → `Degraded`(他系下回り)| `raises = {OCCLUSION_PRIMARY}`(他系下回り)、`tick()` | `tick()` が例外伝播せず、`reporter.events == []` かつ `state_machine.calls == []`(片例外 → primary を `healthy=False` 化 → secondary 下回り → `Degraded`、Healthy / Degraded 系経路で alarm / 遷移なし)| 契約 + RCM(SEP-003)|

**ケース数目安:** 正常系 + RCM 4(parametrize 展開)+ 契約 1(triggering_channels)+ 境界値 2 + RCM 冗長性 3 + RCM 安全側 2 + 順序契約 1 + 契約(AlarmEvent)1 + SEP-003 例外耐性 3(Reporter 例外 + Sensor 全例外 + Sensor 片例外)+ RCM 冪等 2 = **合計 19 件**(実測、stmt 100% / branch 100% = MC/DC 100% 達成)
**MC/DC 目標:** **100%**(クラス C RCM 実装、§7.4 規定、冗長 2 系統 OR 論理 + 故障 channel 無視 + 両系故障安全側 + armed 連動冪等性 + SEP-003 例外吸収の全分岐網羅、Step 20 X1 達成済)

**Fake 実装(7 種、`tests/unit/test_occlusion_detector.py` 内):**

| Fake 名 | 役割 | 利用 UT |
|---------|------|---------|
| `_ScriptedSensorReader` | 事前 script に従って per-channel `SensorReading` を返却、`raises: set[SensorKind]` で例外注入(SEP-003 試験用)| UT-006.1-01〜04, 07〜09, 11, 17, 18 |
| `_RecordingReporter` | `@dataclass(slots=True)`、`report_alarm` 呼び出しを `events: list[AlarmEvent]` に蓄積 | UT-006.1-11, 13, 15, 16, 17, 18 |
| `_RaisingReporter` | `_RecordingReporter` 派生、`report_alarm` で `RuntimeError` 送出 = SEP-003 例外伝播禁止契約検証用 | UT-006.1-14 |
| `_RecordingStateMachine` | `@dataclass(slots=True)`、`request_state_transition` 呼び出しを `calls: list[tuple[TargetState, str]]` に蓄積 | UT-006.1-11, 14, 15, 16, 17, 18 |
| `_TracingReporter` | 共有 `trace: list[str]` に `"alarm"` を追記する Reporter(順序契約検証用、slots=True による method 動的差し替え不可問題の回避策)| UT-006.1-12 |
| `_TracingStateMachine` | 共有 `trace: list[str]` に `"transition"` を追記する StateMachine(`_TracingReporter` とペアで順序契約検証)| UT-006.1-12 |
| `_StepReader` | per-tick readings map を順送りする SensorReader(両 channel を 1 tick で読了後に index 進行)、`threading.Lock` で並行安全 | UT-006.1-16 |

**試験パラメータ化・trace 構造:**

- **`pytest.parametrize`(UT-006.1-01〜04):** `("primary", "secondary", "expected_cls")` を 4 ケース(`(below, below, Healthy)` / `(above, below, Detected)` / `(below, above, Detected)` / `(above, above, Detected)`)、ID は `UT-006.1-01_both_below` 等の人間可読 ID を `pytest.param(id=...)` で付与
- **共有 trace 構造(UT-006.1-12):** `order: list[str] = []` をローカル変数で生成し、`_TracingReporter(order)` と `_TracingStateMachine(order)` に注入 → 両者の発火順を実時間で記録(`@dataclass(slots=True)` では method 動的差し替えができない問題を、専用 trace 用 fake クラス + 共有 list 構造で回避)
- **`_StepReader` 構造(UT-006.1-16):** `steps: list[dict[SensorKind, SensorReading]]` を index 0 から順送り、両 channel(`OCCLUSION_PRIMARY` → `OCCLUSION_SECONDARY` の順で `read_sensor` 呼出)で 1 step を読了 → secondary 読了時に index +1 = tick 単位で readings 切替を実現

**試験設計の根拠:**

- **OR 論理(UT-006.1-01〜04):** SDD §4.19.F.1 = 片系超過でも `Detected` = 冗長 2 系統の RCM-009 設計趣旨(片系劣化でも検出継続)。
- **閾値境界 inclusive(UT-006.1-05/06):** SDD §4.19.F.1 = `>=` 採用 = 境界値ちょうども超過扱い(過量投与回避優先 = safe-side)。
- **片系故障 + 他系超過 → `Detected` 継続(UT-006.1-09):** RCM-009 冗長性の **キーシナリオ** = 片系故障時に他系の検出を機械的にマスクしない契約(検出能力の堅牢性検証)。
- **両系故障 → ERROR 遷移 + alarm なし(UT-006.1-11):** SDD §4.19.F.5 = 両系不信時の Detected alarm は fabrication(虚偽発報)= safe-side として ERROR 遷移依頼のみ実施(State Machine 側の安全停止に委ねる)。
- **発報 → 遷移順序契約(UT-006.1-12):** SAD v0.2 §11.1 + SDD §4.19.F.4 = alarm path がイベントを受信してから State Machine が制御ループを遮断する順序 = アラーム消失リスクの回避。
- **AlarmEvent 内容(UT-006.1-13):** IEC 60601-1-8 §6.1 高優先度 + §5.1.4 テクニカル区分 + SRS-ALM-004 契約 + SDD v0.5 §5.1.A `AlarmEvent` Python 実装契約(`MappingProxyType({})` factory)+ `clock` 戻り値透過。
- **Reporter / Sensor 例外吸収(UT-006.1-14, 17, 18):** SEP-003 例外伝播禁止契約 = Reporter / Sensor のいずれが故障しても State Machine への遷移依頼経路は維持(`_safe_read` + `_on_detected` 内 `try/except` で吸収、`noqa: BLE001` で catch-all 容認)。
- **armed 連動冪等性(UT-006.1-15):** SDD §4.19.F.4 = 連続検知時の発報 + 遷移依頼両方を armed フラグで抑制(State Machine 側の冪等性に依存しない設計 = 責務分離)。
- **Healthy 経由再 arm(UT-006.1-16):** SDD §4.19.F.3 = Healthy/Degraded で armed = True に再 arm = 再発検知時に新規 alarm を発火する契約(連続発生する閉塞を一度きりの alarm で silence させない)。

**UTPR v0.24 候補で詳細化する項目(SDD §4.19.G.x 申し送りと整合):**

- **UT-006.1-19+ 並行 `tick` 耐性(本 §7.3.19 スコープ外):** 別スレッドからのセンサー値読み取り + Pump センサー値の atomic 性(SDD v0.7 §4.19.G.x 並行性詳細化 = `_alarm_armed: bool` の lock 化と並行)
- **周期 `tick` 試験(本 §7.3.19 スコープ外):** Control Loop 拡張時の周期駆動契約(SDD v0.7 §4.19.G.x で確定)
- **片系故障内部ロジック詳細(本 §7.3.19 スコープ外):** タイムアウト・ノイズ閾値・連続エラーカウントの判定詳細(UNIT-002.3 拡張で実装側詳細化、`SensorReading.healthy` の具体的故障検出ロジック)
- **閾値値・単位の bench 整合性試験(本 §7.3.19 スコープ外):** SDD v0.7 で `OCCLUSION_PRESSURE_THRESHOLD_KPA` 正式確定後の境界値試験(現行は暫定 `Decimal(90)` kPa、bench data に基づく再評価)
- **検知後 self-test 動作(本 §7.3.19 スコープ外):** 誤検知抑制 vs 安全側即時停止のトレードオフ(現行は即時発報 N=1、SDD v0.7 §4.19.G.x で bench 後再評価)

---

#### 7.3.20 UNIT-006.2 Air-Bubble Detector(Inc.2 新規、骨格、v0.22、CR-0012 / Step 20 F)

> **Step 20 F 整合化(2026-05-10、本節 v0.22 新規追加):** SDD-VIP-001 v0.5 §4.20 で骨格化された UNIT-006.2(気泡多段判定、RCM-010)に対応する UT-UID を採番。骨格記述に留め、SDD v0.6 候補で詳細化予定。

**関連 SRS:** SRS-041(気泡検知)、SRS-RCM-010(多段判定)、SRS-ALM-005(高優先度・テクニカル発報)、SRS-IF-010
**関連 RCM:** RCM-010(気泡検知多段化)
**関連 HZ:** HZ-004(検知失敗 → アラーム失敗連鎖、EV-HZ004-002 駆動)
**安全クラス:** C(SAD §9 SEP-000、非分離)
**新規パッケージ予定:** `src/vip_detection/air_bubble.py`

**試験観点(骨格):**

| 観点番号 | 観点 | 種別 | 関連 SDD |
|---------|------|------|---------|
| UT-006.2-01〜 | 健全時(警告 / 危険両閾値下)| 正常系 | §4.20 `_evaluate` |
| UT-006.2-03〜 | 警告閾値のみ超過 → `Warning`(発報なし、ログのみ、SDD §4.20 設計)| 多段独立性 | §4.20 |
| UT-006.2-05〜 | 危険閾値のみ超過 → `Detected`(SRS-ALM-005 発報 + ERROR 遷移依頼)| RCM(RCM-010)| §4.20 + IF-U-007/013 |
| UT-006.2-07〜 | 両閾値超過 → `Detected`(危険優先、警告は副次)| 多段独立性 + RCM | §4.20 |
| UT-006.2-09〜 | 各段の判定独立性(警告段の判定が危険段の判定に影響しない、機械的に各段を個別注入)| RCM(独立性)| §4.20 |
| UT-006.2-11〜 | 警告閾値 / 危険閾値の境界値試験 | 境界値 | §4.20 + SDD v0.6 閾値具体値 |
| UT-006.2-13〜 | 警告状態の保持時間(継続警告から危険遷移する時間幅、SDD v0.6 候補で確定)| タイミング | §4.20 + SDD v0.6 |
| UT-006.2-15〜 | センサー値取得失敗時の例外伝播禁止契約 | 契約 | §4.20 |

**ケース数目安:** 8 観点 × 2〜3 サブケース = **≥ 18 件**(Inc.2 実装時に詳細化)
**MC/DC 目標:** **100%**(クラス C RCM 実装、多段判定の各段独立分岐 + 同時超過時の優先順位 全網羅)

**SDD v0.6 候補で詳細化する項目(SDD §4.20 申し送りと整合):** 警告閾値 / 危険閾値の値・単位確定、各段の判定独立性の機械的検証(UT で各段を個別注入)、警告状態の保持時間。

---

#### 7.3.21 UNIT-006.3 Reservoir Empty Detector(Inc.2 新規、骨格、v0.22、CR-0012 / Step 20 F)

> **Step 20 F 整合化(2026-05-10、本節 v0.22 新規追加):** SDD-VIP-001 v0.5 §4.21 で骨格化された UNIT-006.3(薬液切れ検知)に対応する UT-UID を採番。骨格記述に留め、SDD v0.6 候補で詳細化予定。

**関連 SRS:** SRS-042(薬液切れ検知)、SRS-ALM-006(中優先度・テクニカル発報)、SRS-IF-010
**関連 RCM:** RCM-006(発報必達)
**関連 HZ:** HZ-004(検知失敗 → アラーム失敗連鎖、EV-HZ004-003 駆動)、HZ-002(残量切れ未検出での過少投与継続、間接)
**安全クラス:** C(SAD §9 SEP-000、非分離)
**新規パッケージ予定:** `src/vip_detection/reservoir.py`

**試験観点(骨格):**

| 観点番号 | 観点 | 種別 | 関連 SDD |
|---------|------|------|---------|
| UT-006.3-01〜 | 健全時(残量 > 閾値)| 正常系 | §4.21 `_evaluate` |
| UT-006.3-03〜 | 残量降下 → 閾値跨ぎ → `Empty` 検知 → SRS-ALM-006 発報 + PAUSED 遷移依頼(SAD v0.2 §11.1 確定)| RCM + 統合 | §4.21 + IF-U-007/013 |
| UT-006.3-06〜 | 閾値境界値試験 | 境界値 | §4.21 + SDD v0.6 閾値具体値 |
| UT-006.3-08〜 | ヒステリシス(チャタリング防止、SDD v0.6 候補)| 境界値 + 連続検知 | §4.21 + SDD v0.6 |
| UT-006.3-10〜 | 復元(補充による残量回復)時の挙動(自動 RUNNING 復帰禁止 / オペレータ操作必須、Inc.2 範囲計画書 §3.1 + IEC 60601-1-8 §6.4 「健康ケアプロバイダの操作なしで自動復帰しない」整合)| RCM + 異常系 | §4.21 + UNIT-001.1 |
| UT-006.3-12〜 | センサー値取得失敗時の例外伝播禁止契約 | 契約 | §4.21 |

**ケース数目安:** 6 観点 × 2〜3 サブケース = **≥ 14 件**(Inc.2 実装時に詳細化)
**MC/DC 目標:** **100%**(クラス C RCM 実装、閾値判定 + ヒステリシス + 復元挙動 全網羅)

**SDD v0.6 候補で詳細化する項目(SDD §4.21 申し送りと整合):** 閾値 値・単位 + ヒステリシス検討、検知後の挙動(PAUSED 路線確定、SAD v0.2)。

---

#### 7.3.22 UNIT-006.4 Alarm Task Watchdog(Inc.2 新規、骨格、v0.22、CR-0012 / Step 20 F)

> **Step 20 F 整合化(2026-05-10、本節 v0.22 新規追加):** SDD-VIP-001 v0.5 §4.22 で骨格化された UNIT-006.4(アラームタスク監視 1 秒以内検知、RCM-011)に対応する UT-UID を採番。骨格記述に留め、SDD v0.6 候補で詳細化予定。Inc.1 UNIT-001.5 SW Watchdog(B9、UT-001.5-01〜12 / 19 件 Pass、300 ms 監視)+ UNIT-002.4 HW-side Failsafe Timer(B4、500 ms 監視)に続く 3 階層目の Watchdog として位置付け。

**関連 SRS:** SRS-044(アラームタスク監視 1 秒以内、SRS v0.3 で Inc.2 確定)、SRS-RCM-011(アラームタスク監視)、SRS-IF-010
**関連 RCM:** RCM-011(アラームタスク監視によるデッドロック検知)
**関連 HZ:** HZ-005(アラーム失敗単独、タスクデッドロック / 通知 I/F 不具合、EV-HZ005-001 駆動)
**安全クラス:** C(SAD §9 SEP-000、非分離)
**新規パッケージ予定:** `src/vip_detection/alarm_task_watchdog.py`

**試験観点(骨格、Inc.1 UNIT-001.5 / 002.4 試験設計を継承):**

| 観点番号 | 観点 | 種別 | 関連 SDD |
|---------|------|------|---------|
| UT-006.4-01〜 | 正常 heartbeat(規定周期内)で `is_tripped == False` | 正常系 | §4.22 `heartbeat` |
| UT-006.4-03〜 | アラームタスク模擬停止(heartbeat 途絶)→ タイムアウト境界(SRS-RCM-011「1 秒以内」を SDD v0.6 で具体値 = 800 ms 候補)で Trip + ERROR 遷移 + 独立アラーム発報路(UNIT-006.5)経由発報 | RCM(RCM-011)| §4.22 |
| UT-006.4-06〜 | 境界値試験(タイムアウト直前 / ちょうど / + ε / 最大検出遅延)、Inc.1 UNIT-001.5 / 002.4 境界 4 点試験パターン継承 | 境界値 | §4.22 + Inc.1 UT-001.5-03a/b/c/d |
| UT-006.4-10〜 | クロック逆転耐性(Inc.1 UNIT-001.5 UT-001.5-05 安全側設計判断継承 = 逆転は Trip)| 安全側 | §4.22 + Inc.1 SW Watchdog 教訓 |
| UT-006.4-12〜 | Tripped 後の heartbeat 無視(自動復帰禁止)+ check_once 冪等(Inc.1 UNIT-001.5 UT-001.5-06a/b 継承)| 異常系 + 冪等 | §4.22 + Inc.1 SW Watchdog 教訓 |
| UT-006.4-14〜 | UNIT-001.5 SW Watchdog との独立性(別スレッド / 別 timer / 異なる監視対象 = アラームタスク vs 制御ループ、SDD v0.6 候補で確定)| 並行 + 独立性 | §4.22 + UNIT-001.5 |
| UT-006.4-16〜 | 監視タスク自身の停止検知(誰が watchdog の watchdog をするか = self-check 機構、SDD v0.6 候補)| RCM | §4.22 + SDD v0.6 |

**ケース数目安:** 7 観点 × 2〜3 サブケース = **≥ 16 件**(Inc.2 実装時に詳細化)
**MC/DC 目標:** **100%**(クラス C RCM 実装、heartbeat 判定 + クロック逆転 + Tripped 状態分岐 + 階層防御 SW < 500 ms < ALARM(800 ms 候補)< HW(500 ms)時間順序 全網羅、Inc.1 UNIT-001.5 100% 達成パターン継承)

**SDD v0.6 候補で詳細化する項目(SDD §4.22 申し送りと整合):** タイムアウト値の具体化、UNIT-001.5 SW Watchdog との設計上の独立性、監視タスク自身の停止検知。

---

#### 7.3.23 UNIT-006.5 Alarm Path Redundancy(Inc.2 新規、骨格、v0.22、CR-0012 / Step 20 F)

> **Step 20 F 整合化(2026-05-10、本節 v0.22 新規追加):** SDD-VIP-001 v0.5 §4.23 で骨格化された UNIT-006.5(アラーム発報路冗長化、RCM-012)に対応する UT-UID を採番。骨格記述に留め、SDD v0.6 候補で詳細化予定。

**関連 SRS:** SRS-RCM-012(アラーム発報路冗長化)、SRS-IF-010
**関連 RCM:** RCM-012(アラーム発報路冗長化)
**関連 HZ:** HZ-005(アラーム失敗単独、発報路故障)
**安全クラス:** C(SAD §9 SEP-000、非分離)
**新規パッケージ予定:** `src/vip_detection/alarm_path_redundancy.py`

**試験観点(骨格):**

| 観点番号 | 観点 | 種別 | 関連 SDD |
|---------|------|------|---------|
| UT-006.5-01〜 | 主系健全時 → 主系発報のみ → `Ok` | 正常系 | §4.23 `report` |
| UT-006.5-03〜 | 主系故障(タイムアウト / 例外 / 戻り値 Err)+ 予備系健全 → 予備系フェイルオーバー → `PrimaryFailedSecondaryOk` | RCM(RCM-012)| §4.23 主系失敗検知 |
| UT-006.5-06〜 | 両系故障 → `BothFailed` + UNIT-001.1 ERROR 遷移依頼 + 制御停止 | RCM + 異常系 | §4.23 + IF-U-013 |
| UT-006.5-09〜 | 主系遅延(タイムアウト境界)時の予備系発報判断 | タイミング + RCM | §4.23 + SDD v0.6 タイムアウト値 |
| UT-006.5-11〜 | 主系 / 予備系の隔離性(プロセス分離 / スレッド分離 / 経路分離いずれか採用、SDD v0.6 候補)| 並行 + 独立性 | §4.23 + SDD v0.6 |
| UT-006.5-13〜 | 同時並行発報 vs 主系失敗確認後の逐次発報(SDD v0.6 候補で発報試行戦略確定)| 並行 + 設計判断 | §4.23 + SDD v0.6 |

**ケース数目安:** 6 観点 × 2〜3 サブケース = **≥ 14 件**(Inc.2 実装時に詳細化)
**MC/DC 目標:** **100%**(クラス C RCM 実装、主系健全 / 主系故障 / 両系故障 3 経路 + フェイルオーバー判定 + ERROR 遷移依頼 全網羅)

**SDD v0.6 候補で詳細化する項目(SDD §4.23 申し送りと整合):** 主系失敗の検知条件、予備系発報の試行戦略、主系 / 予備系の隔離手段。

---

#### 7.3.24 UNIT-006.6 Battery Low Detector(Inc.2 新規、骨格、v0.22、CR-0012 / Step 20 F、HZ-009 対応)

> **Step 20 F 整合化(2026-05-10、本節 v0.22 新規追加):** SDD-VIP-001 v0.5 §4.24 で骨格化された UNIT-006.6(バッテリ低下検知、HZ-009 対応)に対応する UT-UID を採番。骨格記述に留め、SDD v0.6 候補で詳細化予定。**HZ-009 は Inc.2 範囲計画書 §5.2 で SDP §3.2 vs Inc.1 RMF 未識別ギャップとして発見、RMF v0.4 §4.1 で正式登録(Step 20 C / CR-0010)** されたため、本 UNIT が安全機能要(HZ-009 を駆動する EV-HZ009-001 を検知する単一実装ユニット)。

**関連 SRS:** SRS-043(バッテリ低下検知)、SRS-ALM-007(中優先度・テクニカル発報)、SRS-IF-010
**関連 RCM:** RCM-006(発報必達)、**RCM-020 候補(HZ-009 対応、SRS 正式登録は Step 20 B-3 候補申し送り中、安全側遷移ロジックは SDD v0.6 候補)**
**関連 HZ:** **HZ-009(バッテリ低下によるソフトウェア機能喪失、Inc.2 新規識別)**、HZ-002 / HZ-007 連鎖
**安全クラス:** C(SAD §9 SEP-000、非分離)
**新規パッケージ予定:** `src/vip_detection/battery.py`

**試験観点(骨格):**

| 観点番号 | 観点 | 種別 | 関連 SDD |
|---------|------|------|---------|
| UT-006.6-01〜 | 健全時(残量 > 警告閾値)| 正常系 | §4.24 `_evaluate` |
| UT-006.6-03〜 | 警告閾値以下(SDD v0.6 候補:残量 < 15%)→ 検知 → SRS-ALM-007 中優先度発報 | RCM(RCM-006)| §4.24 + SRS-ALM-007 |
| UT-006.6-06〜 | 緊急閾値以下(SDD v0.6 候補:残量 < 5%)→ 検知 + 安全側遷移ロジック(RCM-020 候補:自動 PAUSED / 注入レート低下 / 制御停止のいずれか、SDD v0.6 候補)| RCM-020 候補 + 異常系 | §4.24 + SDD v0.6 |
| UT-006.6-09〜 | 閾値境界値試験(警告 / 緊急 各閾値) | 境界値 | §4.24 + SDD v0.6 閾値具体値 |
| UT-006.6-11〜 | バッテリ復帰(充電による残量回復)時の挙動 | 正常系(復元)| §4.24 + SDD v0.6 |
| UT-006.6-13〜 | `BATTERY_LOW` イベント注入連携(UNIT-002.3 → IF-U-015 経由)= EV-HZ009-001 駆動 | 統合(HZ-009 駆動)| §4.24 + UNIT-002.3 §4.11.G |
| UT-006.6-15〜 | ヒステリシス(電圧変動でのチャタリング防止、SDD v0.6 候補)| 連続検知 + 境界値 | §4.24 + SDD v0.6 |

**ケース数目安:** 7 観点 × 2〜3 サブケース = **≥ 16 件**(Inc.2 実装時に詳細化)
**MC/DC 目標:** **100%**(クラス C RCM 実装、警告 / 緊急 2 段判定 + ヒステリシス + 安全側遷移ロジック 全網羅)

**SDD v0.6 候補で詳細化する項目(SDD §4.24 申し送りと整合):** 閾値 値・単位、ヒステリシス、安全側遷移ロジック(RCM-020 候補)= バッテリ低下時の自動 PAUSED 遷移 / 注入レート低下 / 制御停止のいずれか + Inc.2 着手中の SRS 追加改訂(Step 20 B-3 候補)で SRS-RCM-020 として正式登録予定。

---

#### 7.3.25 UNIT-007.1 Alarm Reporter Core(Inc.2 新規、骨格、v0.22、CR-0012 / Step 20 F、SEP-003 分離継続、クラス B)

> **Step 20 F 整合化(2026-05-10、本節 v0.22 新規追加):** SDD-VIP-001 v0.5 §4.25 で骨格化された UNIT-007.1(`AlarmReportInterface` 本実装、SRS-IF-010、SEP-003 クラス B 維持)に対応する UT-UID を採番。骨格記述に留め、SDD v0.6 候補で詳細化予定。**SEP-003 詳細化(SAD v0.2 §9.2 + IEC 60601-1-8 整合確認 = 検知ロジックは ARCH-006 検知群クラス C で完結、ARCH-007.1 は通知 + 区分判定の純粋出力層に限定)** に基づき、本 UNIT は **検知ロジックを持たない** ことを AST 機械検証で担保(`vip_alarm/reporter.py` 内に閾値判定 / 数値比較がないことを確認)。

**関連 SRS:** SRS-IF-010(Alarm I/F 本実装)、SRS-O-040(本実装)、SRS-ALM-001(既存)、SRS-ALM-004〜008(Inc.2 アラーム)
**関連 RCM:** RCM-006(発報必達 + 1 秒以内発報)
**関連 HZ:** HZ-004 / HZ-005(アラーム発報路 + アラーム失敗、検知群経由で間接)
**安全クラス:** **B**(SAD §9 SEP-003、分離継続、本実装後も維持)
**新規パッケージ予定:** `src/vip_alarm/reporter.py`(クラス B、SEP-003 AST 機械検証あり)

**試験観点(骨格):**

| 観点番号 | 観点 | 種別 | 関連 SDD |
|---------|------|------|---------|
| UT-007.1-01〜 | `report_alarm(event: AlarmEvent)` 基本受領(IF-U-007 / IF-U-012)+ 内部キュー追加 + ログ出力(ARCH-009 経由)| 正常系 | §4.25 `report_alarm` |
| UT-007.1-04〜 | `acknowledge(alarm_id)` 正常受領(IF-U-014 経由 Control API)+ 状態 ACTIVE → ACKED 遷移 | 正常系 | §4.25 `acknowledge` + §5.3 状態遷移 |
| UT-007.1-07〜 | `silence(alarm_id, duration_sec)` 正常受領 + 状態 ACKED → SILENCED 遷移 + 高優先度 ≤ 120 秒制限の **本 UNIT 側強制**(`silence` 内部で `duration_sec` をクランプ or `Err` 返却、SDD v0.6 候補で確定、SAD §9.2 SEP-003 整合)| 正常系 + 規格制約 | §4.25 + IEC 60601-1-8 §6.4 |
| UT-007.1-10〜 | 状態遷移網羅(ACTIVE / ACKED / SILENCED / CLEARED 4 状態 × 各遷移 = SAD §5.3 の状態遷移を SDD で具体化)| RCM | §4.25 + §5.3 |
| UT-007.1-13〜 | **`AlarmEvent` の frozen + slots + `metadata` の `MappingProxyType` ラップ実装契約**(IF-U-007 詳細、不変性検証で `dataclasses.FrozenInstanceError` + `metadata` への代入失敗、Inc.1 B11/B12 frozen パターン継承)| 不変性 + 契約 | §4.25 + §5.1.A AlarmEvent |
| UT-007.1-16〜 | **例外契約 = SEP-003 違反検知**(ARCH-007.x からの例外を呼出元に伝播させない契約、内部 try/except + ログのみ、Inc.1 UNIT-005.3 例外握りつぶし契約継承)| 契約 + RCM | §4.25 + SEP-003 |
| UT-007.1-19〜 | 主系 / 予備系 2 インスタンス対応(UNIT-006.5 Alarm Path Redundancy が本 UNIT を 2 重化する前提のシングルトン回避設計)| 並行 + RCM | §4.25 + UNIT-006.5 |
| UT-007.1-22〜 | **SEP-003 import グラフ機械検証**(`ast.parse` で `vip_alarm/reporter.py` を解析、`{vip_ctrl, vip_sim, vip_integrity}` の戻り値書込み禁止 + 例外伝播禁止を確認、Inc.1 UNIT-005.3 SEP-001 AST 検証パターン継承)| 契約(SAD §9 SEP-003)| §4.25 + SAD §9.2 |
| UT-007.1-25〜 | UNIT-007.2 Priority Classifier 連動(`classify(cause_code) -> (priority, category)` 結果の表参照委譲、純粋関数性 + cause_code 範囲)| 統合 | §4.25 + §4.26 |

**ケース数目安:** 9 観点 × 2〜3 サブケース = **≥ 22 件**(Inc.2 実装時に詳細化)
**MC/DC 目標:** **100%**(クラス B 分離ユニット、Inc.2 RCM 実装の中核 = 4 状態遷移 + 高優先度消音時間制限 + 例外握りつぶし + SEP-003 機械検証 全網羅、Inc.1 UNIT-005.3 SEP-001 機械検証 + 例外握りつぶし契約 100% パターン継承)

**SDD v0.6 候補で詳細化する項目(SDD §4.25 申し送りと整合):** `AlarmEvent` の frozen + slots + `metadata` MappingProxyType ラップ実装契約、ACTIVE / ACKED / SILENCED / CLEARED 状態遷移本実装、高優先度 ≤ 120 秒消音時間制限の強制、例外契約、主系 / 予備系 2 インスタンス対応のシングルトン回避設計。

---

#### 7.3.26 UNIT-007.2 Alarm Priority Classifier(Inc.2 新規、骨格、v0.22、CR-0012 / Step 20 F、純粋関数、クラス B)

> **Step 20 F 整合化(2026-05-10、本節 v0.22 新規追加):** SDD-VIP-001 v0.5 §4.26 で骨格化された UNIT-007.2(IEC 60601-1-8 §6.1 優先度判定 + §5.1.4 区分判定、純粋関数、クラス B)に対応する UT-UID を採番。骨格記述に留め、SDD v0.6 候補で詳細化予定。本 UNIT は **副作用なし、内部状態なし、外部 I/O なし**(SEP-003 分離契約の根拠 = AST 機械検証で担保)。

**関連 SRS:** SRS-REG-002(IEC 60601-1-8 詳細化)、SRS-ALM-004〜008
**関連 RCM:** —(直接の RCM 実装ではなく、UNIT-007.1 + ARCH-006 検知群の支援ユニット)
**関連規格:** IEC 60601-1-8 §6.1(優先度分類)+ §5.1.4(テクニカル / 生理区分)
**関連 HZ:** —(分類のみで安全機能直接実装なし)
**安全クラス:** **B**(SAD §9 SEP-003、分離継続、純粋関数)
**新規パッケージ予定:** `src/vip_alarm/priority_classifier.py`(クラス B、純粋関数、AST 機械検証あり)

**試験観点(骨格):**

| 観点番号 | 観点 | 種別 | 関連 SDD |
|---------|------|------|---------|
| UT-007.2-01 | `classify("occlusion")` → `(HIGH, TECHNICAL)`(SRS-ALM-004 整合)| 正常系・パラメータ化 | §4.26 対応表 |
| UT-007.2-02 | `classify("air_bubble_critical")` → `(HIGH, TECHNICAL)`(SRS-ALM-005 整合)| 正常系・パラメータ化 | §4.26 対応表 |
| UT-007.2-03 | `classify("reservoir_empty")` → `(MEDIUM, TECHNICAL)`(SRS-ALM-006 整合)| 正常系・パラメータ化 | §4.26 対応表 |
| UT-007.2-04 | `classify("battery_low")` → `(MEDIUM, TECHNICAL)`(SRS-ALM-007 整合、HZ-009 駆動)| 正常系・パラメータ化 | §4.26 対応表 |
| UT-007.2-05 | `classify("alarm_task_failure")` → `(HIGH, TECHNICAL)`(RCM-011 経由、SRS-ALM 直接対応なし)| 正常系・パラメータ化 | §4.26 対応表 |
| UT-007.2-06 | `classify("control_error")` → `(HIGH, TECHNICAL)`(SRS-ALM-001、Inc.1 既存)| 正常系・パラメータ化 | §4.26 対応表 |
| UT-007.2-07〜 | 未知 `cause_code` 受領時の挙動(`raise ValueError` か `LOW + TECHNICAL` フォールバックか、SDD v0.6 候補で確定 + UNIT-007.1 例外契約整合)| 異常系 + 契約 | §4.26 申し送り |
| UT-007.2-09〜 | 戻り値型不変性(`AlarmPriority` enum + `AlarmCategory` enum + `ClassificationResult` frozen+slots)| 不変性 + 契約 | §4.26 + B11/B12 パターン |
| UT-007.2-11〜 | 純粋関数性(同一入力で複数回呼出 → 同一結果、副作用なし、Inc.1 UNIT-005.3 純粋関数試験パターン継承)| 契約(純粋性)| §4.26 |
| UT-007.2-13〜 | hypothesis ラウンドトリップ(任意の sealed `cause_code` で classify → 戻り値が `(AlarmPriority, AlarmCategory)` enum 値域内、対応表全網羅)| プロパティ | §4.26 + Inc.1 hypothesis 採用パターン |
| UT-007.2-15〜 | **SEP-003 import グラフ + 副作用 AST 機械検証**(`vip_alarm/priority_classifier.py` が `vip_ctrl` / `vip_sim` / `vip_integrity` / `vip_api` を import 0 件 + 関数内に I/O / global state がないことを AST 確認、Inc.1 UNIT-005.3 SEP-001 AST 検証パターン継承)| 契約(SAD §9 SEP-003)| §4.26 + SAD §9.2 |

**ケース数目安:** 11 観点 = **≥ 12 件**(Inc.2 範囲 6 種 cause_code パラメータ化 + 未知値 + 不変性 + 純粋関数 + プロパティ + SEP-003 機械検証)
**MC/DC 目標:** **≥ 90%**(クラス B 純粋関数、表参照のみで分岐数が少なく、未知 `cause_code` フォールバック挙動の網羅性で担保、§7.4 規定)

**SDD v0.6 候補で詳細化する項目(SDD §4.26 申し送りと整合):** `cause_code` の sealed enum 化、未知 `cause_code` 受領時の挙動、優先度 LOW の cause_code を Inc.4 で追加した場合の影響範囲(本 UNIT は表参照のみで拡張容易)。

---

**Inc.2 範囲合計ケース数目安(新規 8 ユニット骨格 + 既存 3 ユニット拡張節):** **≥ 180 件**(UT-006.1 = 19 件実測 Pass(Step 20 X1、stmt/branch 100% = MC/DC 100%、本 v0.23 で §7.3.19 詳細化済)+ UT-006.2〜006.6 計 ≥ 79 + UT-007.1 ≥ 22 + UT-007.2 ≥ 12 + UT-001.1-G ≥ 15 + UT-002.3-G ≥ 18 + UT-005.1-G ≥ 14 = 約 179 件)。最終的な件数は Inc.2 実装時(Step 20 X〜の TDD)に確定、Step 14 v0.1 流儀「v0.x 骨格化 → v0.x+1 で各ユニット詳細化」を Inc.2 では「ユニットごと TDD 実装(Step 20 X(3n+1))+ SDD 詳細化(Step 20 X(3n+2))+ UTPR 詳細化(Step 20 X(3n+3))」の 3 ステップサイクルへ進化(Step 20 X1〜X3 で UNIT-006.1 完結サイクル実証)。

---

### 7.4 カバレッジ目標

| 指標 | 目標値 | 適用範囲 |
|------|-------|---------|
| ステートメント網羅(line / statement) | **100%** | 全ユニット(クラス C + クラス B 分離) |
| 分岐網羅(decision / branch) | **100%** | 全ユニット(クラス C + クラス B 分離) |
| **MC/DC**(Inc.1)| **100%** | Inc.1 RCM 実装ユニット(UNIT-001.1, 001.4, 001.5, 002.4, 004.1, 004.2)|
| **MC/DC**(Inc.2、進行中)| **100%**(UNIT-006.1 = 達成済、Step 20 X1 で実装 + 本 v0.23 で §7.3.19 詳細化、stmt/branch 100% / MC/DC 100%。残ユニットは Step 20 X4〜の TDD で達成予定)| Inc.2 RCM 実装ユニット(UNIT-006.1 ✓ + UNIT-006.2, 006.3, 006.4, 006.5, 006.6, 007.1)|
| MC/DC | 95% 以上 | その他クラス C ユニット |
| MC/DC | 90% 以上 | クラス B 分離ユニット(UNIT-005.3、UNIT-007.2)|

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
| UNIT-001.2 | **21**(うち UT-001.2-01..19 展開後 21、内訳:正常系 2 + 順序保証 1 + RCM 2 + 境界値 2 + 異常系 3 + ライフサイクル 4 + 契約 5 + スモーク 1 + ログ 1)| **21** | 0 | 0 | **100.00% / 100.00% / 100%(MC/DC 試験設計担保、tick 状態前提 + validation 経路 + auto-stop 分岐 + 例外経路 + overrun 分岐 全網羅、RCM-004 SW 送出側)** | 2026-04-29 | Step 19 B10 PR #18 マージコミット `d02b336` |
| UNIT-001.3 | **23**(うち UT-001.3-01..23 展開後 23、内訳:正常系 1 + 統合 3 + 異常系 6 + 境界 1 + RCM 2 + 並行 1 + 契約 5 + ライフサイクル 4)| **23** | 0 | 0 | **100.00% / 100.00% / 100%(MC/DC 試験設計担保、stop ファストパス + 通常キュー + token 一意性 + dispatch 例外耐性、`# pragma: no cover` 4 件は race-window/防御コード分岐)** | 2026-04-30 | Step 19 B13 PR #21 マージコミット `6c1a374` |
| UNIT-001.4 | **34**(うち UT-001.4-01..12 = 12 + パラメータ化展開 14 + 補助観点 8)| **34** | 0 | 0 | **100.00% / 100.00% / 100%(MC/DC 試験設計担保、RCM-001 範囲 + 設定値整合性 + 状態別スキップ全分岐)** | 2026-04-23 | Step 19 B3 PR #11 マージコミット `72d474e` |
| UNIT-001.5 | **19**(うち UT-001.5-01..12 展開後 19、内訳:境界 4 + ライフサイクル 4 + 異常系 4 + その他 7) | **19** | 0 | 0 | **100.00% / 100.00% / 100%(MC/DC 試験設計担保、RCM-003 SW 側 + クロック逆転 + Tripped 分岐 + 階層防御 SW<HW)** | 2026-04-24 | Step 19 B9 PR #17 マージコミット `5f34148` |
| UNIT-002.1 | **21**(うち UT-002.1-01..21 展開後 21、内訳:正常系 2 + SRS-P01 過渡 2 + 異常系 5 + SRS-P01 定常 1 + RCM 1 + 冪等 1 + 復帰契約 1 + 契約 4 + 境界値 2 + 並行 1 + ログ 1 + SRS-031 契約 1)| **21** | 0 | 0 | **100.00% / 100.00% / 100%(MC/DC 試験設計担保、failsafe 経路 + advance_time 分岐 + overflow 一回限り分岐 全網羅、SRS-P01 過渡 / 定常両試験 + 並行勝利)** | 2026-04-29 | Step 19 B11 PR #19 マージコミット `cbc2578` |
| UNIT-002.2 | **10**(うち UT-002.2-01..10 展開後 10、内訳:正常系 3 + 状態整合 1 + 不変性 1 + 単調性 1 + atomic 性 1 + structural typing 2 + pure 1)| **10** | 0 | 0 | **100.00% / 100.00% / 100%(MC/DC 試験設計担保、frozen+slots dataclass + lock 借用 atomic 取得 + Control Loop Protocol structural typing 整合)** | 2026-04-30 | Step 19 B12 PR #20 マージコミット `28cc912` |
| UNIT-002.3 | **12**(うち UT-002.3-01..12 展開後 12、内訳:正常系 3 + 境界 2 + 統合 1 + 並行 1 + 不変性 1 + 契約 4)| **12** | 0 | 0 | **100.00% / 100.00% / —(MC/DC 目標 SDD/UTPR §7.4 通り「—」据置、stmt/branch 100% で網羅、コード規模 33 stmt / 0 branch、Inc.1 では Pump 影響なしの no-op スタブ、Inc.2 で正式機能化時に再評価)** | 2026-04-30 | Step 19 B14 PR #22 マージコミット `00093e1` |
| UNIT-002.4 | **18**(うち UT-002.4-01..08 展開後 10 + 補助観点 8)| **18** | 0 | 0 | **100.00% / 100.00% / 100%(MC/DC 試験設計担保、RCM-004 HW 側 + クロック逆転 + Tripped 分岐)** | 2026-04-23 | Step 19 B4 PR #12 マージコミット `3c7a933` |
| UNIT-003.1 | **26**(うち UT-003.1-01..17 展開後 22 + 補助観点 4 - State パラメータ化 6 + JSON 不正 4 含む)| **26** | 0 | 0 | **100.00% / 100.00% / 100%(MC/DC 試験設計担保、Decimal / State / bytes 3 種タグ往復 + 決定論性 + 不正 JSON / UTF-8 例外 + hypothesis ラウンドトリップ)** | 2026-04-24 | Step 19 B7 PR #15 マージコミット `982c568` |
| UNIT-003.2 | **32**(うち UT-003.2-01..15 展開後 28 + パラメータ化 4 セット + hypothesis 2)| **32** | 0 | 0 | **100.00% / 100.00% / 100%(MC/DC 試験設計担保、SHA-256 既知ベクタ + ラウンドトリップ + 不正 expected 8 サブケース + 大小 hex 正規化 + hypothesis 衝突・ラウンドトリップ)** | 2026-04-24 | Step 19 B8 PR #16 マージコミット `5c56cea` |
| UNIT-003.3 | **21**(うち UT-003.3-01..10 展開後 12 + 補助観点 9)| **21** | 0 | 0 | **100.00% / 100.00% / 100%(MC/DC 試験設計担保、write/read/rollback + bak 世代管理 + 例外経路 + 非 POSIX 早期リターン)** | 2026-04-23 | Step 19 B5 PR #13 マージコミット `0a1cc34` |
| UNIT-004.1 | **33**(うち UT-004.1-01..12 展開後 24 + 補助観点 9)| **33** | 0 | 0 | **100.00% / 100.00% / 100%(MC/DC 試験設計担保、§4.5.B 9 検証項目 + settings consistency tolerance 境界 + dose==0 分岐 + 列挙順序 + hypothesis 破損注入)** | 2026-04-23 | Step 19 B6 PR #14 マージコミット `faf743b` |
| UNIT-004.2 | **15**(うち UT-004.2-01..15 展開後 15、内訳:正常系 2 + 統合 1 + 異常系 3 + 境界 2 + RCM 3 + 不変性 1 + ライフサイクル 3)| **15** | 0 | 0 | **100.00% / 100.00% / 100%(MC/DC 試験設計担保、`confirm` 4 分岐 + `set_pending` 2 分岐 + `check_expiry` 3 分岐 + `is_pending`/`pending_detail` の 2 分岐 全網羅、RCM-016 SDD §4.14 逐語実装、`hmac.compare_digest` 定数時間 + `secrets.token_hex(16)` 128 bit エントロピー)** | 2026-04-30 | Step 19 B15 PR #23 マージコミット `e3a8b9d` |
| UNIT-005.1 | **21**(うち UT-005.1-01..20 展開後 21、内訳:正常系 8 + 異常系 6 + RCM 4 + 不変性 1 + 契約 1 + 並行/網羅性 1)| **21** | 0 | 0 | **100.00% / 100.00% / 100%(MC/DC 試験設計担保、骨格 90% から 100% に引き上げ、`start` 3 分岐 + `confirm_resume` 4 分岐 + try/except 例外耐性 3 経路 + `_safe_enqueue` 例外 1 経路 + Accepted/Rejected 分岐 全網羅、API 委譲層、`Settings.model_dump()` で pydantic を `Mapping[str, object]` に変換、ValidationApi Protocol で SEP-001 分離維持)** | 2026-04-30 | Step 19 B16 PR #24 マージコミット `92a3f19` |
| UNIT-005.2 | **19**(うち UT-005.2-01..12 を parametrize 展開して 19、内訳:正常系 11 + 契約 4 + 単調性 1 + 不変性 1 + 境界 1)| **19** | 0 | 0 | **100.00% / 100.00% / —(MC/DC 目標 SDD/UTPR §7.4 通り「—」据置、stmt/branch 100% で網羅、コード規模 30 stmt / 2 branch、SDD §4.16.C 擬似コード逐語実装 + 例外伝播契約 + idempotent 100 回試験 + frozen+slots dataclass)** | 2026-04-30 | Step 19 B17 PR #25 マージコミット `a9000d0` |
| UNIT-005.3 | **16**(うち UT-005.3-01..13 を parametrize 展開して 16、内訳:正常系 2 + 異常系 5 + 境界 5 + 不変性 1 + 契約 3)| **16** | 0 | 0 | **100.00% / 100.00% / 100%(MC/DC 試験設計担保、骨格 90% から 100% に引き上げ、範囲 3 分岐 + 整合性 1 分岐 + 例外握りつぶし 1 経路 + 失敗集約 1 分岐 全網羅、SAD §9 SEP-001 分離維持を AST import グラフ機械検証で担保、クラス B 純粋関数)** | 2026-04-30 | Step 19 B18 PR #26 マージコミット `bf9db71` |
| UNIT-005.4 | **15**(UT-005.4-01〜15、内訳:正常系 5 + 異常系 4 + RCM 1(checksum 不一致 = HZ-007 検出)+ 契約 5)| **15** | 0 | 0 | **100.00% / 100.00% / 100%(MC/DC 試験設計担保、コード規模 78 stmt / 10 branch、`--version` fallback 1 経路 + `--diagnose` 5 分岐(不存在/ReadErr/decode 失敗/Ok/FailsafeRecommended)+ argparse 相互排他 + デフォルト 2 経路 全網羅、`io.StringIO` DI で subprocess 不使用)** | 2026-05-07 | Step 19 H1 PR(本 PR マージコミット)|
| UNIT-001.1 G(Inc.2 拡張、骨格)| **未実施(目安 ≥ 15)**(UT-001.1-G01〜:アラーム発報経路 + ACK / SILENCE 状態遷移、SDD §4.1.G 連動)| — | — | — | **未実施(目標 stmt 100% / branch 100% / MC/DC 100%、Inc.1 既存 100% を維持しつつ Inc.2 アラーム経路追加分の新規分岐網羅)** | TBD(Step 20 X〜の TDD) | TBD |
| UNIT-002.3 G(Inc.2 拡張、骨格、no-op 解除)| **未実施(目安 ≥ 18)**(UT-002.3-G01〜:`BATTERY_LOW` enum + Pump 伝播 + IF-U-015 `read_sensor` 6 種 SensorKind、UT-002.3-06 no-op 退化検出は破棄予定、SDD §4.11.G 連動)| — | — | — | **未実施(目標 stmt 100% / branch 100% / MC/DC 100%、Inc.1 「—」据置 → Inc.2 で正式機能化に伴い 100% 引き上げ)** | TBD(Step 20 X〜の TDD) | TBD |
| UNIT-005.1 G(Inc.2 拡張、骨格)| **未実施(目安 ≥ 14)**(UT-005.1-G01〜:`acknowledge_alarm` / `silence_alarm` 転送 + 例外耐性 + Inc.1 既存 7 メソッド回帰、SDD §4.15.G 連動)| — | — | — | **未実施(目標 stmt 100% / branch 100% / MC/DC 100%、Inc.1 既存 100% 維持 + 新 API 分岐網羅)** | TBD(Step 20 X〜の TDD) | TBD |
| UNIT-006.1(Inc.2 新規、実施済) | **19**(うち UT-006.1-01..18 展開後 19、内訳:正常系 + RCM 4(parametrize)+ 契約 1(triggering_channels)+ 境界値 2 + RCM 冗長性 3 + RCM 安全側 2 + 順序契約 1 + 契約(AlarmEvent)1 + SEP-003 例外耐性 3 + RCM 冪等 2、SDD §4.19、RCM-009)| **19** | 0 | 0 | **100.00% / 100.00% / 100%(MC/DC 試験設計担保、冗長 2 系統 OR 論理 + 故障 channel 無視 + 両系故障安全側 Failed + armed 連動冪等性 + Healthy 経由再 arm + SEP-003 例外吸収(Reporter / Sensor 双方)+ 発報 → 遷移順序契約 全網羅、`src/vip_detection/occlusion.py` 84 stmt + 18 branch / `protocols.py` 47 stmt)** | 2026-05-13 | Step 20 X1 PR #67 マージコミット `551f862` |
| UNIT-006.2(Inc.2 新規、骨格)| **未実施(目安 ≥ 18)**(UT-006.2-01〜:気泡多段判定 + 各段独立性 + 警告 / 危険閾値、SDD §4.20、RCM-010)| — | — | — | **未実施(目標 stmt 100% / branch 100% / MC/DC 100%)** | TBD(Step 20 X〜の TDD) | TBD |
| UNIT-006.3(Inc.2 新規、骨格)| **未実施(目安 ≥ 14)**(UT-006.3-01〜:残量降下 + 閾値跨ぎ + 復元時オペレータ操作必須、SDD §4.21、RCM-006)| — | — | — | **未実施(目標 stmt 100% / branch 100% / MC/DC 100%)** | TBD(Step 20 X〜の TDD) | TBD |
| UNIT-006.4(Inc.2 新規、骨格)| **未実施(目安 ≥ 16)**(UT-006.4-01〜:アラームタスク監視 1 秒以内 + クロック逆転安全側 + UNIT-001.5 独立性、SDD §4.22、RCM-011)| — | — | — | **未実施(目標 stmt 100% / branch 100% / MC/DC 100%、Inc.1 UNIT-001.5 試験設計継承)** | TBD(Step 20 X〜の TDD) | TBD |
| UNIT-006.5(Inc.2 新規、骨格)| **未実施(目安 ≥ 14)**(UT-006.5-01〜:主系健全 / 主系故障 + 予備系 / 両系故障 + ERROR 遷移、SDD §4.23、RCM-012)| — | — | — | **未実施(目標 stmt 100% / branch 100% / MC/DC 100%)** | TBD(Step 20 X〜の TDD) | TBD |
| UNIT-006.6(Inc.2 新規、骨格、HZ-009 対応)| **未実施(目安 ≥ 16)**(UT-006.6-01〜:バッテリ警告 / 緊急閾値 + ヒステリシス + RCM-020 候補安全側遷移 + `BATTERY_LOW` イベント注入連携、SDD §4.24、RCM-006、HZ-009 駆動)| — | — | — | **未実施(目標 stmt 100% / branch 100% / MC/DC 100%)** | TBD(Step 20 X〜の TDD) | TBD |
| UNIT-007.1(Inc.2 新規、骨格、SEP-003 クラス B)| **未実施(目安 ≥ 22)**(UT-007.1-01〜:`report_alarm` / `acknowledge` / `silence` 本実装 + 4 状態遷移網羅 + 高優先度 ≤ 120 秒消音 + SEP-003 AST 機械検証、SDD §4.25、RCM-006)| — | — | — | **未実施(目標 stmt 100% / branch 100% / MC/DC 100%、Inc.1 UNIT-005.3 SEP-001 機械検証 + 例外握りつぶし契約パターン継承)** | TBD(Step 20 X〜の TDD) | TBD |
| UNIT-007.2(Inc.2 新規、骨格、純粋関数、クラス B)| **未実施(目安 ≥ 12)**(UT-007.2-01〜:Inc.2 範囲 6 種 cause_code パラメータ化 + 未知値挙動 + 純粋関数性 + hypothesis + SEP-003 副作用機械検証、SDD §4.26)| — | — | — | **未実施(目標 stmt 100% / branch 100% / MC/DC ≥ 90%、表参照のみで分岐少)** | TBD(Step 20 X〜の TDD) | TBD |
| **Inc.1 合計** | **309 件実測**(B1〜B18 で 294 件 + UNIT-005.4 15 件、Step 19 H1 完了)| **309** | 0 | 0 | **TOTAL 100.00% / 100.00% / クラス C MC/DC 100%(RCM 実装 6 ユニット)+ クラス B MC/DC 100%(UNIT-005.3、骨格 90% から引き上げ)** | 2026-04-23〜2026-05-07 | Step 19 B2〜H1 |
| **Inc.2 合計(進行中)** | **19 件実測 + 残 ≥ 161 件目安**(Step 20 X1 で UNIT-006.1 19 件 Pass、Inc.2 合計目安 ≥ 180 件、残 7 ユニット + 既存 3 拡張節は Step 20 X4〜の TDD で確定)| **19** | 0 | 0 | **UNIT-006.1 = 100.00% / 100.00% / MC/DC 100% 達成、残目標 TOTAL 100.00% / 100.00% / クラス C MC/DC 100%(RCM 実装 7 ユニット中 1 ユニット達成)+ クラス B MC/DC 100%(UNIT-007.1)+ クラス B MC/DC ≥ 90%(UNIT-007.2)** | 2026-05-13〜進行中 | Step 20 X1〜 |
| **Inc.1 + Inc.2 合計** | **328 件実測 + 残 ≥ 161 件目安**(Inc.1 309 件実測 + Inc.2 19 件実測 + Inc.2 残 ≥ 161 件目安) | **328** | 0 | 0 | **Inc.1 100% / Inc.2 UNIT-006.1 100%、残 Inc.2 は TBD** | — | — |

### 9.3 不具合・逸脱

| 問題 ID(PRB) | 発見 UT-ID | 内容 | 重大度 | 対応 | ステータス |
|----------------|----------|------|-------|------|----------|
| — | — | — | — | — | — |

### 9.4 未達項目と処置

*(v0.1 時点では未記入。Inc.1 実装完了時に、カバレッジ目標未達分や防御的コードの正当化を記載する。)*

## 10. 結論

- [ ] 全 18 ユニット(Step 19 H1 で UNIT-005.4 CLI 追加)が受入基準(§5)を満たしている
- [ ] クラス C 追加基準(§6)全 9 項目を網羅
- [ ] §7.4 カバレッジ目標を達成
- [ ] 未解決問題は既知の残留異常として SMS-VIP-001(§5.8)に記載する

## 11. トレーサビリティマトリクス

| ユニット ID | 試験 ID | 関連 SRS | 関連 RCM | 関連 HZ | 結果 |
|------------|--------|---------|---------|---------|------|
| UNIT-001.1 State Machine | UT-001.1-01 〜 UT-001.1-12 | SRS-020, 021, 025, SRS-RCM-020, SRS-ALM-003 | RCM-019 | HZ-001, HZ-002 | **Pass(100 tests / 100.00% stmt / 100.00% branch / MC/DC 100%、Step 19 B2、2026-04-23)** |
| UNIT-001.2 Control Loop | UT-001.2-01 〜 UT-001.2-19 | SRS-011, 012, 031, SRS-P02, SRS-RCM-004 | RCM-004(SW 送出)| HZ-001, HZ-002 | **Pass(21 tests / 100.00% stmt / 100.00% branch / MC/DC 100%、Step 19 B10、2026-04-29)** |
| UNIT-001.3 Command Handler | UT-001.3-01 〜 UT-001.3-23 | SRS-010, 013, 014, SRS-P03, SRS-P04 | —(State Machine と連携)| HZ-001, HZ-002 | **Pass(23 tests / 100.00% stmt / 100.00% branch / MC/DC 100%、Step 19 B13、2026-04-30)** |
| UNIT-001.4 Flow Command Validator | UT-001.4-01 〜 UT-001.4-12 | SRS-O-001, SRS-RCM-001, SRS-005 | RCM-001 | HZ-001, HZ-002 | **Pass(34 tests / 100.00% stmt / 100.00% branch / MC/DC 100%、Step 19 B3、2026-04-23)** |
| UNIT-001.5 Watchdog (SW) | UT-001.5-01 〜 UT-001.5-12 | SRS-RCM-003 | RCM-003 | HZ-001, HZ-002 | **Pass(19 tests / 100.00% stmt / 100.00% branch / MC/DC 100%、Step 19 B9、2026-04-24)** |
| UNIT-002.1 Pump Simulator | UT-002.1-01 〜 UT-002.1-21 | SRS-030, 031, SRS-P01 | RCM-004(HW 被呼出側)| HZ-001, HZ-002 | **Pass(21 tests / 100.00% stmt / 100.00% branch / MC/DC 100%、Step 19 B11、2026-04-29)** |
| UNIT-002.2 Pump Observer | UT-002.2-01 〜 UT-002.2-10 | SRS-031, SRS-I-020 | — | — | **Pass(10 tests / 100.00% stmt / 100.00% branch / MC/DC 100%、Step 19 B12、2026-04-30)** |
| UNIT-002.3 Event Injection Stub | UT-002.3-01 〜 UT-002.3-12 | SRS-032, SRS-I-040(Inc.2)| —(Inc.2 で追加)| HZ-004 | **Pass(12 tests / 100.00% stmt / 100.00% branch / MC/DC 「—」据置(Inc.1 no-op スタブ)、Step 19 B14、2026-04-30)** |
| UNIT-002.4 HW-side Failsafe Timer | UT-002.4-01 〜 UT-002.4-08 | SRS-RCM-004, SRS-032 | RCM-004(HW 側)| HZ-001, HZ-002 | **Pass(18 tests / 100.00% stmt / 100.00% branch / MC/DC 100%、Step 19 B4、2026-04-23)** |
| UNIT-003.1 Serializer | UT-003.1-01 〜 UT-003.1-17 | SRS-DATA-001, 004 | RCM-015 前提 | HZ-007 | **Pass(26 tests / 100.00% stmt / 100.00% branch / MC/DC 100%、Step 19 B7、2026-04-24)** |
| UNIT-003.2 Checksum Verifier | UT-003.2-01 〜 UT-003.2-15 | SRS-SEC-001 | RCM-015 構成要素 | HZ-007 | **Pass(32 tests / 100.00% stmt / 100.00% branch / MC/DC 100%、Step 19 B8、2026-04-24)** |
| UNIT-003.3 Atomic File Writer | UT-003.3-01 〜 UT-003.3-10 | SRS-DATA-002, 003 | RCM-015 前提 | HZ-007 | **Pass(21 tests / 100.00% stmt / 100.00% branch / MC/DC 100%、Step 19 B5、2026-04-23)** |
| UNIT-004.1 Integrity Validator | UT-004.1-01 〜 UT-004.1-12 | SRS-026, 027, SRS-RCM-015 | RCM-015 | HZ-007 | **Pass(33 tests / 100.00% stmt / 100.00% branch / MC/DC 100%、Step 19 B6、2026-04-23)** |
| UNIT-004.2 Resume Confirmation Gate | UT-004.2-01 〜 UT-004.2-15 | SRS-028, SRS-RCM-016 | RCM-016 | HZ-007 | **Pass(15 tests / 100.00% stmt / 100.00% branch / MC/DC 100%、Step 19 B15、2026-04-30)** |
| UNIT-005.1 Control API | UT-005.1-01 〜 UT-005.1-20 | SRS-IF-002, SRS-010〜014 | —(委譲、UNIT-001.3 経由 RCM-019 / UNIT-004.2 経由 RCM-016)| HZ-001, HZ-002(委譲先で対応)| **Pass(21 tests / 100.00% stmt / 100.00% branch / MC/DC 100%、Step 19 B16、2026-04-30)** |
| UNIT-005.2 State Observer API | UT-005.2-01 〜 UT-005.2-12 | SRS-IF-003, SRS-O-010, SRS-UX-002 | — | — | **Pass(19 tests / 100.00% stmt / 100.00% branch / MC/DC 「—」据置(読み取り専用 API)、Step 19 B17、2026-04-30)** |
| UNIT-005.3 Validation API(クラス B) | UT-005.3-01 〜 UT-005.3-13 | SRS-UX-001, 004, 005 | —(B 分離側)| HZ-006(設定値整合性違反)| **Pass(16 tests / 100.00% stmt / 100.00% branch / MC/DC 100%、SEP-001 AST import グラフ機械検証 Pass、Step 19 B18、2026-04-30)** |
| UNIT-005.4 CLI Entry Point | UT-005.4-01 〜 UT-005.4-15 | SRS-OPS-002, 003, 010, 011 | —(運用要求、SRS-027 フェイルセーフ起動と整合)| HZ-007(永続記録破損時の `--diagnose` 観測経路)| **Pass(15 tests / 100.00% stmt / 100.00% branch / MC/DC 100%、`io.StringIO` DI 駆動テスト + 5 経路網羅(`--version` fallback / `--diagnose` × 5 分岐 / argparse 相互排他 / デフォルト × 2)、Step 19 H1 で UNIT-005.4 新規追加 = ISS-H-001 解消、2026-05-07)** |
| UNIT-001.1 G(Inc.2 拡張、骨格) | UT-001.1-G01〜(目安 ≥ 15、TBD)| SRS-044, SRS-ALM-008, SRS-RCM-006(Inc.2 追補)| RCM-006(発報必達)、RCM-019 既存(状態遷移保護整合) | HZ-004(検知失敗連鎖)、HZ-005(アラーム失敗) | **未実施(TBD、Step 20 X〜の TDD で UT 詳細化 + 実装、目標 100% / 100% / MC/DC 100%、SDD §4.1.G 連動)** |
| UNIT-002.3 G(Inc.2 拡張、骨格、no-op 解除) | UT-002.3-G01〜(目安 ≥ 18、TBD、UT-002.3-06 破棄予定) | SRS-I-040(イベント注入 4 種)、SRS-040〜043(各検知) | RCM-009(冗長 2 系統)、RCM-010(多段)、RCM-006(発報必達) | HZ-004(EV-HZ004-002/003)、**HZ-009(EV-HZ009-001、Inc.2 新規)** | **未実施(TBD、SDD §4.11.G 連動、Inc.1 「—」据置 → Inc.2 で MC/DC 100% 引き上げ)** |
| UNIT-005.1 G(Inc.2 拡張、骨格) | UT-005.1-G01〜(目安 ≥ 14、TBD) | SRS-044(IEC 60601-1-8 §6.4)、SRS-ALM-008 | —(委譲、UNIT-007.1 + UNIT-001.1 拡張で実装) | HZ-005(アラーム失敗時の操作経路、間接) | **未実施(TBD、SDD §4.15.G 連動、Inc.1 既存 7 メソッド回帰維持 + 新 2 メソッド分岐網羅)** |
| UNIT-006.1 Occlusion Detector(Inc.2 新規、実施済) | UT-006.1-01 〜 UT-006.1-18(19 ケース、parametrize 展開含む) | SRS-040, SRS-RCM-009, SRS-ALM-004, SRS-IF-010 | RCM-009(冗長 2 系統、Step 20 X1 で検出能力実装 = Designed → Verified 化への前進、Inc.2 完了時に IT / ST 実測で総合判断)| HZ-004(EV-HZ004-001 駆動、検出側実装が完成)| **Pass(19 tests / 100.00% stmt / 100.00% branch / MC/DC 100%、SDD §4.19、Step 20 X1 PR #67 マージコミット `551f862`、2026-05-13)** |
| UNIT-006.2 Air-Bubble Detector(Inc.2 新規、骨格) | UT-006.2-01〜(目安 ≥ 18、TBD) | SRS-041, SRS-RCM-010, SRS-ALM-005, SRS-IF-010 | RCM-010(多段 Designed → Verified 化目標) | HZ-004(EV-HZ004-002 駆動) | **未実施(TBD、SDD §4.20、目標 100% / 100% / MC/DC 100%)** |
| UNIT-006.3 Reservoir Empty Detector(Inc.2 新規、骨格) | UT-006.3-01〜(目安 ≥ 14、TBD) | SRS-042, SRS-ALM-006, SRS-IF-010 | RCM-006(発報必達) | HZ-004(EV-HZ004-003 駆動)、HZ-002(間接) | **未実施(TBD、SDD §4.21、目標 100% / 100% / MC/DC 100%)** |
| UNIT-006.4 Alarm Task Watchdog(Inc.2 新規、骨格) | UT-006.4-01〜(目安 ≥ 16、TBD) | SRS-044, SRS-RCM-011, SRS-IF-010 | RCM-011(アラームタスク監視 Designed → Verified 化目標) | HZ-005(EV-HZ005-001 駆動) | **未実施(TBD、SDD §4.22、目標 100% / 100% / MC/DC 100%、Inc.1 UNIT-001.5 試験設計継承)** |
| UNIT-006.5 Alarm Path Redundancy(Inc.2 新規、骨格) | UT-006.5-01〜(目安 ≥ 14、TBD) | SRS-RCM-012, SRS-IF-010 | RCM-012(発報路冗長化 Designed → Verified 化目標) | HZ-005(発報路故障) | **未実施(TBD、SDD §4.23、目標 100% / 100% / MC/DC 100%)** |
| UNIT-006.6 Battery Low Detector(Inc.2 新規、骨格、HZ-009 対応) | UT-006.6-01〜(目安 ≥ 16、TBD) | SRS-043, SRS-ALM-007, SRS-IF-010 | RCM-006(発報必達)、**RCM-020 候補(HZ-009 対応、SRS 登録待ち)** | **HZ-009(バッテリ低下によるソフトウェア機能喪失、Inc.2 新規識別)**、HZ-002 / HZ-007 連鎖 | **未実施(TBD、SDD §4.24、目標 100% / 100% / MC/DC 100%、安全側遷移ロジックは SDD v0.6 候補で詳細化)** |
| UNIT-007.1 Alarm Reporter Core(Inc.2 新規、骨格、SEP-003 クラス B) | UT-007.1-01〜(目安 ≥ 22、TBD) | SRS-IF-010, SRS-O-040, SRS-ALM-001/004〜008 | RCM-006(発報必達 + 1 秒以内発報) | HZ-004 / HZ-005(検知群経由で間接) | **未実施(TBD、SDD §4.25、目標 100% / 100% / MC/DC 100%、SEP-003 AST 機械検証 = Inc.1 UNIT-005.3 SEP-001 検証パターン継承)** |
| UNIT-007.2 Alarm Priority Classifier(Inc.2 新規、骨格、純粋関数、クラス B) | UT-007.2-01〜(目安 ≥ 12、TBD) | SRS-REG-002(IEC 60601-1-8 §6.1 + §5.1.4)、SRS-ALM-004〜008 | —(支援ユニット) | —(分類のみ) | **未実施(TBD、SDD §4.26、目標 100% / 100% / MC/DC ≥ 90%、表参照のみで分岐少)** |

**カバレッジ:**
- **Inc.1(実施済):** 本マトリクスにより、SDD §3.1 のユニット一覧 18 件(Step 19 H1 で UNIT-005.4 追加後)全てが UT-ID と紐付き、SRS / RCM / HZ への双方向トレーサビリティが確立済(309 件 Pass、Step 19 H3 完了)。SRS-VIP-001 §10 の「UT-ID」列は Inc.1 完了タグ `v0.1.0-inc1`(`16ae385`)時点で充填済。
- **Inc.2(進行中、UNIT-006.1 詳細化完了):** v0.22(Step 20 F)で SDD v0.5 §4.19〜§4.26 + §4.1.G / §4.11.G / §4.15.G の Inc.2 範囲 8 新規ユニット + 既存 3 ユニット拡張を骨格として追加。SRS / RCM / HZ への双方向トレース(SRS-040〜044 / SRS-ALM-004〜008 / SRS-RCM-006/009/010/011/012 / SRS-IF-010 / SRS-O-040 / SRS-I-040 / SRS-REG-002 / HZ-004/005/009 / RCM-006/009/010/011/012)を確立。**本 v0.23(Step 20 X3)で UNIT-006.1 = §7.3.19 を骨格 → 詳細(19 ケース実測 Pass、stmt/branch 100% = MC/DC 100% 達成)+ §9.2 / §11 トレース結果欄を Step 20 X1 実測値で充填(Step 20 X1 PR #67 マージコミット `551f862`)= Inc.2 検知群 6 ユニットの 1 番目で RCM-009 検出能力実装が完成、Inc.2 完了時に IT(ITPR §6.12)/ ST(STPR §6.6 ST-ALM)実測 + RMF Verified 化判定で総合判断**。残 7 ユニット(UNIT-006.2〜006.6 + UNIT-007.1〜007.2)+ 既存 3 拡張節(UNIT-001.1 G / UNIT-002.3 G / UNIT-005.1 G)は Step 20 X4〜の TDD で UT-ID を詳細化 + Pass 化、Inc.2 完了タグ `v0.2.0-inc2` 時点で SRS-VIP-001 §10 「UT-ID」列を Inc.2 範囲分も充填予定。

## 12. 改訂履歴

| バージョン | 日付 | 変更内容 | 変更者 |
|----------|------|---------|--------|
| 0.23 | 2026-05-13 | **Step 20 X3(CR-0017 / Issue #70、Inc.2 連動詳細化の UTPR 部分 §7.3.19 UNIT-006.1 Occlusion Detector、MODERATE)**:Step 20 X1(CR-0015 / PR #67 マージ `551f862`)で TDD 実装した `tests/unit/test_occlusion_detector.py`(19 ケース、UT-006.1-01〜18、stmt/branch 100% = MC/DC 100%)+ Step 20 X2(CR-0016 / PR #69 マージ `f42ed77`)で詳細化した SDD §4.19(11 サブセクション)に整合する形で、v0.22 までの骨格 §7.3.19(8 観点表)を Inc.1 既存節同等粒度の個別 UT-006.1-NN 行詳細表へ展開。**(A) §7.3.19 を骨格 → 詳細(v0.23)に展開**:Step 20 X3 整合化 blockquote 追記 + 試験ケース詳細表 19 行(試験 ID / 対象 API・観点 / 入力・条件 / 期待結果 / 種別)+ Fake 実装 7 種(`_ScriptedSensorReader` / `_RecordingReporter` / `_RaisingReporter` / `_RecordingStateMachine` / `_TracingReporter` / `_TracingStateMachine` / `_StepReader`)の役割表 + parametrize / 共有 trace / `_StepReader` の構造説明 + 試験設計の根拠 9 項目(OR 論理 / 閾値境界 inclusive / 片系故障 + 他系超過のキーシナリオ RCM-009 / 両系故障 safe-side / 発報 → 遷移順序契約 / AlarmEvent 内容 IEC 60601-1-8 § 6.1 / Reporter + Sensor 例外吸収 SEP-003 / armed 連動冪等性 / Healthy 経由再 arm)+ 「UTPR v0.24 候補で詳細化する項目」申し送り 5 件(UT-006.1-19+ 並行 tick + 周期 tick + 片系故障内部ロジック + 閾値正式確定 + 検知後 self-test)。**(B) §3.2 ユニット一覧 UNIT-006.1 行を更新**:「骨格(§4.19 v0.5)」→「詳細(§4.19 v0.6、Step 20 X1 実装 + Step 20 X2 SDD 詳細化 + 本 X3 UTPR 詳細化)」+ 予定ソースファイル「`src/vip_detection/occlusion.py`(予定)」→「(運用中、v0.1)」。**(C) §9.2 試験ケース結果テーブル UNIT-006.1 行を確定化**:「未実施(目安 ≥ 20)」→「19 件 / 100.00% stmt / 100.00% branch / MC/DC 100% / 2026-05-13 / Step 20 X1 PR #67 マージコミット `551f862`」。**(D) §9.2 Inc.2 合計 + Inc.1 + Inc.2 合計集計行を更新**:Inc.2 合計を「進行中(19 件実測 + 残 ≥ 161 件目安)」、Inc.1 + Inc.2 合計を「328 件実測 + 残 ≥ 161 件目安」に更新。**(E) §11 トレース UT-006.1 行を充填**:「未実施(TBD、Step 20 X〜の TDD)」→「Pass(19 tests / 100.00% stmt / 100.00% branch / MC/DC 100%、SDD §4.19、Step 20 X1 PR #67 マージコミット `551f862`、2026-05-13)」+ §11 末尾の Inc.2 状態整理を「骨格」→「進行中、UNIT-006.1 詳細化完了」に更新。**(F) §7.3.26 末尾 Inc.2 合計目安**:UT-006.1 = 19 件実測を反映、3 ステップサイクル(TDD / SDD / UTPR)流儀を明記。**(G) §7.4 MC/DC 目標 Inc.2 行**:「骨格」→「進行中、UNIT-006.1 達成済」に更新。**(H) ヘッダ更新**:バージョン v0.22 → v0.23、最終更新日 2026-05-13、対象範囲記述更新(UNIT-006.1 詳細 + 残 7 骨格)。**(I) §12 改訂履歴 v0.23 行追加**(本行)。**詳細化スコープ「実装した項目のみ」**(Step 20 X1 着手前ユーザ確認で推奨案合意):UT-006.1-01〜18 = 19 ケースのみ詳細化、UT-006.1-19+ 並行 tick + 周期 tick + 片系故障内部ロジックは §7.3.19 末尾「UTPR v0.24 候補」に申し送り(SDD v0.7 §4.19.G.x + UNIT-002.3 拡張と並行詳細化)。**「単一文書 = 単一 CR」運用パターンの 11 度目適用**:CR-0008〜CR-0015 + CR-0016 = SDD のみ(X2)+ **CR-0017 = UTPR のみ(本 X3)** で分離 = **TDD 実装フェーズ後の SDD 詳細化 + UTPR 詳細化の 3 ステップサイクルでも単一文書 = 単一 CR の運用継続**。**「§4 CLOSED 一気通貫」運用パターンの 11 度目適用 = default 運用ルールとして完全確立**(Step 19 I 発見 → B-1 〜 X2 連続 10 + 本 X3 = 連続 11 回適用)。**Step 14 v0.1 流儀「v0.x 骨格化 → 後続改訂で詳細化」を Inc.2 で再実証 = 3 ステップサイクル(Step 20 X(3n+1) TDD 実装 → Step 20 X(3n+2) SDD 詳細化 → Step 20 X(3n+3) UTPR 詳細化)の第 1 サイクル(UNIT-006.1 = Step 20 X1〜X3)完結**:Inc.1 では Step 14 で SDD v0.1 → v0.2 を 12 ユニット一括展開(設計先行型)vs Inc.2 では UNIT 単位の 3 ステップサイクルで進化(実装先行型、TDD ループの即時フィードバック + 設計記述は実装で確定した内容を反映する従属的位置づけ)。**MODERATE 区分**(SCMP §4.1):骨格化 → 詳細化への枠組み拡張で実装は不変、UTPR 内記述の精度向上のみ、SDD v0.6(Step 20 X2 / CR-0016 MODERATE)と同区分・同性質、Inc.2 範囲計画書 §9 + Step 19 I 計画時点で「3 ステップサイクルの第 3 ステップ」として整合 | k-abe |
| 0.22 | 2026-05-10 | **Step 20 F(CR-0012 / Issue #59、Inc.2 連動改訂の UTPR 部分、骨格化、MODERATE)**:SDD-VIP-001 v0.5 で骨格化済の Inc.2 範囲を UTPR に骨格として反映。**(A) ヘッダ更新**:対象 SW v0.1.0-inc1 → v0.2.0-inc2(予定)、対象範囲 18 ユニット(Inc.1)→ 26 ユニット(Inc.1 18 + Inc.2 新規 8 + 既存 3 拡張節)、最終更新日 2026-05-10、バージョン v0.22。**(B) §1 適用範囲拡張**:Inc.2 範囲(SDD §4.19〜§4.26 + §4.1.G / §4.11.G / §4.15.G)+ 対象 SRS 要求(SRS-040〜044 / SRS-ALM-004〜008 / SRS-RCM-006/009/010/011/012 / SRS-IF-010 / SRS-O-040 / SRS-I-040 / SRS-REG-002)+ 対象 RCM(Inc.2 Designed = RCM-006/009/010/011/012)を追記。**(C) §2 参照文書更新**:SRS v0.1 → v0.3、SAD v0.1 → v0.2、SDD v0.4 → v0.5、RMF v0.2 → v0.4、INC2-SCOPE-VIP-001 v0.1 + IEC 60601-1-8 を追加(参照番号 [10]/[11])。**(D) §3.2 ユニット一覧拡張**:Inc.2 新規 8 ユニット(UNIT-006.1〜006.6 + UNIT-007.1〜007.2)を行追加 + 既存 UNIT-001.1 / 002.3 / 005.1 行に SDD §4.x.G(v0.5、Inc.2 拡張)追記、合計 26 ユニット、SEP-003(Alarm Reporter 分離)注記追加。**(E) §4.2 検証強化**:Inc.2 RCM 実装 7 ユニット(UNIT-006.1〜006.6 + UNIT-007.1)= MC/DC 100% 目標 + UNIT-007.2 = MC/DC ≥ 90%(クラス B 純粋関数)+ Inc.2 並行性試験対象(UNIT-006.4 / 006.5 / 007.1)+ SEP-003 境界 AST 機械検証(UNIT-007.1 / 007.2)を追加。**(F) §7.3.19〜§7.3.26 Inc.2 新規 8 ユニットの骨格節新設**:UT-006.1-NN〜UT-007.2-NN の UT-UID 採番、試験観点(8 観点 × 2〜3 サブケース)、ケース数目安、MC/DC 目標、SDD v0.6 候補で詳細化する項目を骨格記述。**(G) §7.3.1.G / §7.3.13.G / §7.3.15.G 既存 3 ユニット拡張サブセクション追補**:UT-001.1-G01〜(SDD §4.1.G、アラーム発報経路 + ACK / SILENCE)+ UT-002.3-G01〜(SDD §4.11.G、BATTERY_LOW + Pump 伝播 no-op 解除、UT-002.3-06 破棄予告)+ UT-005.1-G01〜(SDD §4.15.G、`acknowledge_alarm` / `silence_alarm`)を骨格記述。**(H) §7.4 カバレッジ目標表更新**:Inc.2 RCM 実装ユニット行追加 + クラス B 分離ユニット(UNIT-005.3 + UNIT-007.2)整理。**(I) §9.2 試験ケース結果テーブル拡張**:Inc.2 新規 8 ユニット行 + 既存 3 ユニット拡張行(計 11 行)を「未実施(TBD)」状態 + 目安ケース数 + 目標カバレッジで追加、Inc.1 / Inc.2 / 合計の 3 集計行を追加。**(J) §11 トレーサビリティマトリクス追補**:Inc.2 ユニット 8 + 既存 3 ユニット拡張 = 11 行追加。各 UT-UID へ SRS / RCM / HZ を割付け(SRS-040〜044 / SRS-ALM-004〜008 / SRS-RCM-006/009/010/011/012 / SRS-IF-010 / SRS-O-040 / SRS-I-040 / SRS-REG-002 / HZ-004/005/009 / RCM-006/009/010/011/012)、本節末尾の Inc.1 / Inc.2 状態整理を追記。**(K) §12 改訂履歴 v0.22 行追加**(本行)。**設計判断:** Step 14 v0.1 流儀(代表 N ユニット詳細 + 残骨格 → 後続改訂で詳細化)を Inc.2 でも踏襲、Inc.2 新規 8 ユニットは骨格 + UT-UID 採番に留め、Step 20 X〜の TDD 実装と並行する SDD v0.6 候補で各ユニット詳細化(UT-006.x-NN / UT-007.x-NN を Inc.1 と同等の詳細粒度に展開、Inc.1 では Step 19 B3 整合化以降で B4〜B18 連続 16 度の運用化を達成)。**「単一文書 = 単一 CR」運用パターンの 6 度目適用** = CR-0008 = SRS のみ(B-2)、CR-0010 = RMF のみ(C)、CR-0011 = SAD のみ(D)、CR-0009 = SDD のみ(E)、CR-0012 = UTPR のみ(本 F)で分離継続、Inc.1 流儀(CR-0001 = SDD のみ等)継続。**「§4 CLOSED 一気通貫」運用パターンの 6 度目適用 = default 運用ルールとして完全確立**(Step 19 I 発見 → B-1 導入 → B-2 / C / D / E / 本 F 連続適用)。MODERATE 区分(SCMP §4.1)= 骨格化 = 試験計画の枠組み追加、論理 / 安全機能 / 既存実装に影響しない、SDD v0.5 で確定した骨格を UTPR §7.3.x プレースホルダに反映する従属的改訂、Inc.2 範囲計画書 §9 + Step 19 I 計画時点で「Step 20 F は MODERATE、CR 起票」と整合 | k-abe |
| 0.1 | 2026-04-23 | 初版作成(計画、Step 19 A)。Inc.1 の全 17 ユニットに UT-UID(UT-001.1〜UT-005.3)を採番。代表 5 ユニット(UNIT-001.1, 001.4, 002.4, 003.3, 004.1、SDD v0.1 時点で詳細設計された 5 件)について試験ケースを詳細記述(正常系 / 境界値 / 異常系 / RCM / 並行 / タイミング / プロパティ 分類合計 59 件)。残 12 ユニットは試験観点とケース数目安のみ骨格記述(合計目安 ≥ 95 件)。カバレッジ目標を本プロジェクト固有に強化(RCM 実装 6 ユニットで MC/DC 100%)。試験環境、試験 ID 体系、クラス C 追加基準 9 項目(§5.5.4 準拠)、問題発見時の手続(SPRP/CR 連携)を確立。第 II 部(報告)は骨格のみ、Step 19 B 以降の TDD Red-Green-Refactor で埋めていく | k-abe |
| 0.2 | 2026-04-23 | **Step 19 B2(UNIT-001.1 State Machine TDD 実装)の実施結果を第 II 部に反映**。§9.2 UNIT-001.1 行を 62 tests Pass / カバレッジ 100.00%(stmt / branch)/ MC/DC 100%(RCM-019 全分岐)で確定。§11 トレーサビリティマトリクス UNIT-001.1 行の結果欄を「Pass」に更新。他 16 ユニットは未実施のまま据置(Step 19 B2+ 以降で TDD を継続)。UT-001.1-04 パラメータ化展開で TRANSITION_TABLE 全 13 エントリ × Pass 方向を網羅、UT-001.1-05 で (State, EventKind) 非登録全組合せ 45 ケースを網羅(RCM-019 確認)、UT-001.1-11/12 で hypothesis プロパティ試験 2 件を実装 | k-abe |
| 0.3 | 2026-04-23 | **Step 19 B3(UNIT-001.4 Flow Command Validator TDD 実装)の実施結果を反映 + §7.3.2 を SRS/SDD に整合化**。**(1) 第 I 部 §7.3.2 整合化(MINOR、CR 不要):** v0.2 までの本節は (a) 指令値域を「設定値域 0.1〜1200」と誤記(SRS-O-001 では指令値域は `0.0 ≤ value ≤ 1200.0`)、(b) ValidationReason 名が SDD §4.2.B の enum 名と不一致、(c) 設定値整合性検証が `state == State.RUNNING` のときのみ発火する SDD §4.2.C の前提を未明示、の 3 点で齟齬していた。SRS/SDD を真として本節のテーブル(UT-001.4-01〜12)を全面差し替え、整合化注釈を本節冒頭に追記。SRS / SDD / RMF / SAD 本体は不変。**(2) 第 II 部 §9.2:** UNIT-001.4 行を 34 tests Pass / カバレッジ 100.00%(stmt / branch)/ MC/DC 100%(RCM-001 範囲 + 設定値整合性 + 状態別スキップ全分岐、試験設計担保)で確定。§11 トレーサビリティマトリクス UNIT-001.4 行を「Pass」に更新。**(3) 試験設計:** UT-001.4-07 を NaN/+Inf/-Inf 3 サブケース、UT-001.4-09 を ±2%/±5.00% 境界/+5.01% の 3 サブケースに `pytest.parametrize` 展開、補助観点として 5 状態 × 設定値検証スキップ確認 + 純粋性 + frozen 4 件 + 範囲定数 2 件を追加。`hypothesis` プロパティ 2 件は `max_examples=200, deadline=None` で実装。教訓「UTPR v0.1 作成時の SRS/SDD クロスレビュー漏れ」を DEVELOPMENT_STEPS §教訓に記録 | k-abe |
| 0.4 | 2026-04-23 | **Step 19 B4(UNIT-002.4 HW-side Failsafe Timer TDD 実装)の実施結果を反映 + §7.3.3 整合化**。**(1) 第 I 部 §7.3.3 整合化(MINOR、CR 不要):** Step 19 B3 教訓を運用化し着手前クロスレビューを実施、(a) Logger 注入据置(SDD §4.3.B に `_logger` フィールドなし、UNIT-004+ で正式化、HW failsafe 識別子は `force_stop_failsafe(reason="HEARTBEAT_TIMEOUT")` で代替)、(b) クロック注入(DI)採用(`clock: Callable[[], float]` をコンストラクタ注入、UT-002.4-07 クロック逆転試験のため)、(c) クロック逆転時挙動を「安全側 = 発火」と設計判断(SDD §4.3 未定義、RCM-004 安全側原則 + UNIT-001.1 と整合)、の 3 件を整合化注釈に明記。SRS / SDD / RMF / SAD 本体は不変。**(2) §7.3.3 試験テーブル:** UT-002.4-04 を 04a(500 ms ちょうどで発火しない)/ 04b(500 ms + ε で発火)に分割、UT-002.4-06 を「ログ記録」から「`force_stop_failsafe(reason="HEARTBEAT_TIMEOUT")` 呼出識別」に整合化、UT-002.4-08 を 08a(heartbeat 無視)/ 08b(`check_once` 冪等)に分割、各ケースに `check_once` API 経由のテスト前提を明記。**(3) 第 II 部 §9.2:** UNIT-002.4 行を 18 tests Pass / カバレッジ 100.00% / MC/DC 100% で確定。§11 UNIT-002.4 行を「Pass」更新。UNIT-001.4 行のコミット欄を Step 19 B3 マージ SHA `72d474e` で確定。**(4) 試験設計:** 補助観点 8 件(start/stop ライフサイクル 4、pump 例外耐性 1、定数値 2、実時間スレッド統合スモーク 1)、連打側スモークは macOS sleep ジッタ flaky のため fake_clock UT-002.4-01/05 に委任(教訓記録)。教訓 2 件を DEVELOPMENT_STEPS §教訓に記録 | k-abe |
| 0.18 | 2026-04-30 | **Step 19 B18(UNIT-005.3 Validation API クラス B TDD 実装)の実施結果を反映 + §7.3.17 新規詳細化(残 1 → 0 骨格、Inc.1 全 17 ユニット完成)**。**(1) 第 I 部 §7.3.17 新規詳細化(MINOR、CR 不要):** 骨格「SEP-001 分離検証、内部例外握りつぶし契約、境界値 / ≥ 8 / 90%」を **16 ケース、stmt 100% / branch 100% / MC/DC 100%(クラス B 分離ユニット)** に詳細化(コード規模 55 stmt / 12 branch、骨格 90% を超過し 100% 達成、範囲 3 分岐 + 整合性 1 分岐 + 例外握りつぶし 1 経路 + 失敗集約 1 分岐 全網羅、SAD §9 SEP-001 分離維持を AST import グラフ機械検証で担保)。残骨格 1 → 0 ユニット、**Inc.1 全 17 ユニット完成**。本節冒頭に整合化注釈を追記。**(2) 判断論点(B18 着手前クロスレビュー、16 度目運用):** 運用性 4 — ① 配置 `src/vip_api_b/validation_api.py`(SAD §9 SEP-001 + UTPR §3 既存パス整合)、② `Settings` は `vip_persist.records` から import(値オブジェクトのみ、SEP-001 は副作用伝播禁止が本旨で値オブジェクト共有は許容)、③ SEP-001 機械検証は AST で `{vip_ctrl, vip_sim, vip_integrity, vip_api}` を import しないことを確認(`vip_persist` のみ許容、UT-005.3-13)、④ `drug_name` 検証は Inc.1 では削除して Inc.4 申し送り(B15/B16/B17 chain 継続);専門性 5 — ① `ValidationResult` / `ValidationFailure` sealed hierarchy frozen+slots dataclass(B11〜B17 パターン継続)、② SDD §4.17.C 擬似コード逐語実装(範囲 → 整合性、drug_name は Inc.1 削除)、③ `TOLERANCE = Decimal("0.01")` 1%(SRS-004 逐語実装)、④ **例外握りつぶし契約**(SDD §4.17.E、try/except で `Err([Inconsistency("internal: ...")])` で復帰、SEP-001 boundary 保証)、⑤ MC/DC 100% 引き上げ + `mypy --strict src tests` + `ruff` ローカル必須(B12〜B17 教訓継続、7 ステップ連続適用、本 B18 で RUF100 / FURB157 / RUF002×2 / FBT001 を CI 前ローカル ruff で検出 → 手動修正)。**UT 申し送り:** `drug_name` 検証は Inc.4 で Settings 拡張時に追加。SRS / SDD / RMF / SAD 本体不変。**(3) 第 II 部 §9.2:** UNIT-005.3 行を 16 tests Pass / カバレッジ 100% / MC/DC 100% で確定。§11 UNIT-005.3 行を「Pass」更新(関連 HZ-006 を明示)。UNIT-005.2 行のコミット欄を Step 19 B17 PR #25 マージ SHA `a9000d0` で確定。**(4) 試験設計:** UT-005.3-01 で SRS-004 整合確認、UT-005.3-02/03 で `flow_rate` / `dose_volume` 範囲外 OutOfRange、UT-005.3-04 を `pytest.parametrize` で 2 サブケース展開(0 / 6000)、UT-005.3-05 で SRS-004 整合性違反、UT-005.3-06 を `pytest.parametrize` で 3 サブケース展開(0%/+0.998%/+1.002% 境界)、UT-005.3-07 で多重失敗集約、UT-005.3-08 で `patch("Decimal")` 例外注入で SDD §4.17.E 内部例外握りつぶし契約、UT-005.3-10 で `dataclasses.FrozenInstanceError`、UT-005.3-13 で AST import グラフ機械検証(`vip_ctrl` / `vip_sim` / `vip_integrity` / `vip_api` の import が 0 件)。ruff 5 件(RUF100 不要 noqa / FURB157 `Decimal("60")` / RUF002 × 2 ambiguous `×` / FBT001 positional bool)→ 手動修正、未カバー branch line 163→184(`expected_dose > 0` の False 経路、外側 `flow_rate > 0 ∧ duration_min > 0` で保証済の防御コード)を削除(B16/B17 教訓「未到達コード削除」継続、3 ステップ連続適用)で stmt/branch 100% 達成、`mypy --strict src tests` 43 source files Pass、bandit 0、TOTAL カバレッジ **100.00%**(stmt 1275 + branch 180)、441 tests + 5 連続 stable で CI `fail_under=95` Pass。**Inc.1 全 17 ユニット完成 + V 字右側着手の節目** | k-abe |
| 0.19 | 2026-05-01 | **Step 19 D-1(過去 Step PR / マージコミット SHA 一括清算)の実施結果を反映**。§9.2 試験ケース結果テーブルで「コミット SHA 欄が `Step 19 BX PR マージコミット(TBD)` のまま残っていた **6 行**」を実 SHA で確定:UNIT-001.2(B10 PR #18 `d02b336`)、UNIT-001.5(B9 PR #17 `5f34148`)、UNIT-002.1(B11 PR #19 `cbc2578`)、UNIT-002.2(B12 PR #20 `28cc912`)、UNIT-003.2(B8 PR #16 `5c56cea`)、UNIT-005.3(B18 PR #26 `bf9db71`)。**経緯:** B14 着手時(Step 19 B14 採用根拠 6 で記録)に UNIT-001.2/001.3/001.5/002.1/002.2 の 5 行が TBD 残置になっている更新漏れを発見し、当時は関連の薄い UNIT-001.3 のみ確定 + 残 4 件は次ステップ申し送り。その後 B8 / B18 でも同種の更新漏れ(§11 トレーサビリティマトリクス側のコミット欄は確定していたが §9.2 側は TBD のまま)が累積し、Step 19 D 着手時に全 6 件を清算する形となった。**意義:** Inc.1 V 字右側着手(Step 19 D ITPR v0.1 骨格化)の前提として、§9.2 のトレーサビリティをマージコミット SHA レベルで完全閉路化(SRS / SDD / RMF / SAD 本体不変、MINOR 区分・CR 不要、計画変更ではなく報告セルの実 SHA 確定のみ) | k-abe |
| 0.21 | 2026-05-07 | **Step 19 H1(UNIT-005.4 CLI Entry Point 新規追加 = ISS-H-001 解消)の実施結果を反映 + §7.3.18 新規詳細化(全 17 → 18 ユニット、UNIT-005.4 追加)**。**(1) 第 I 部 §7.3.18 新規詳細化(MINOR、CR 不要):** F 系列(F1〜F7)+ Step 19 G STPR 骨格化完了後、Step 19 H1(STPR §6.2 ST-OPS の前提となる CLI エントリポイント実装)着手前のクロスレビューで **ISS-H-001 を発見** — SRS-OPS-002(必須、`vip-ctrl` CLI)が要求されているが Inc.1 全 17 ユニット(SDD v0.3 §3.2)に CLI ユニットが存在しない計画文書間乖離。本 H1 で UNIT-005.4 CLI として §3.2 ユニット一覧 + SDD §4.18 + 本 §7.3.18 を一括追加(全 17 → 18 ユニット)。試験ケース 15 件(UT-005.4-01〜15:正常系 5 + 異常系 4 + RCM 1(checksum 不一致 = HZ-007 検出)+ 契約 5)、stmt 100% / branch 100% / MC/DC 100%(コード規模 78 stmt / 10 branch、`--version` fallback 1 経路 + `--diagnose` 5 分岐(不存在/ReadErr/decode 失敗/Ok/FailsafeRecommended)+ argparse 相互排他 + デフォルト 2 経路 全網羅)。**(2) 判断論点(H1 着手前クロスレビュー、17 度目運用):** 運用性 4 — ① 配置 `src/vip_ctrl/cli.py`(SDD §4.18 + UTPR §3 既存パス整合、`vip_ctrl` パッケージ既存)、② `pyproject.toml [project.scripts]` で `vip-ctrl = "vip_ctrl.cli:main"` 登録(SRS-OPS-002 必須要求の実装)、③ **Inc.1 範囲では対話 start/stop コマンド経路は提供しない**(SDD §3 設計方針 + B17 申し送り = 対話 UI は Inc.4 で正式実装)、④ DI 駆動テスト容易化(`main(argv, stdout, stderr)` で `IO[str]` を引数化、subprocess を使わずに in-memory `io.StringIO` で出力検査);専門性 5 — ① `match` 文で `ValidationResult` sealed union(`Ok \| FailsafeRecommended`)を網羅(B11〜B18 frozen+slots パターン + bandit B101 / mypy 不到達警告の両方を回避)、② JSON Lines 出力で SRS-OPS-010 必須 5 キー(timestamp / level / component / event / details)を強制、③ `importlib.metadata.version` の `PackageNotFoundError` を捕捉して `unknown` で fallback、④ argparse mutually_exclusive_group で `--version` / `--diagnose` 排他、⑤ MC/DC 100% 引き上げ + `mypy --strict src tests` + `ruff` ローカル必須(B12〜B18 教訓継続、8 ステップ連続適用、本 H1 で TC003(pathlib.Path を TYPE_CHECKING へ)/ I001(import 整理)/ S101(assert_used → match に置換)/ S108(/tmp ハードコード → tmp_path fixture)/ TextIO vs IO[str] 型不整合を CI 前ローカル mypy/ruff で検出 → 手動修正)。**UT 申し送り:** **(a)** 対話 start/stop コマンドは Inc.4 で正式実装(本 H1 では未提供、Inc.4 UI 層で Control Loop / Command Handler / Watchdog 等の既存スレッド lifecycle と統合)、**(b)** STPR §6.2 ST-OPS.1-03 の対話 start/stop 要求は Inc.4 申し送り(ISS-H-002、Step 19 H2 で STPR 修正予定)、**(c)** CLI レベル試験(ST-OPS)は Step 19 H2 で `tests/system/test_ops_acceptance.py` を新規実装(subprocess.Popen + venv 隔離で SRS-OPS-001〜004 / 010〜012 を E2E 検証)。SRS / RMF / SAD 本体不変、SDD 本体は ISS-H-001 解消のため §3.2 + §4.18 + §7 + §8 を本 PR 同時改訂(SDD v0.3 → v0.4)。**(3) 第 II 部 §9.2:** UNIT-005.4 行を 15 tests Pass / カバレッジ 100% / MC/DC 100% で新規追加。§11 UNIT-005.4 行を「Pass」で新規追加(関連 SRS-OPS-002/003/010/011 + HZ-007 観測経路を明示)。**(4) 試験設計:** UT-005.4-01 で `--version` 1 行出力 + return 0、UT-005.4-02 で `PackageNotFoundError` fallback、UT-005.4-03〜08 で `--diagnose` の 6 経路(不存在 / 整合 / checksum 不一致 / JSON 不正 / UTF-8 デコード失敗 / `atomic_writer.read` ReadErr)、UT-005.4-09/10 でデフォルトの 2 経路、UT-005.4-11/12 で argparse SystemExit(2)、UT-005.4-13 で `build_parser` 単独動作、UT-005.4-14 で SRS-OPS-010 必須 5 キー網羅、UT-005.4-15 で `_diagnose` ヘルパ契約。`mypy --strict src tests` 58 source files Pass(`atomic_writer.os.replace = ...` 直接代入を避け `setattr(_os, "replace", ...)` 採用 / `IO[str]` 型統一)、`ruff check / format` All Pass(I001 import 整理 + TC003 Path を TYPE_CHECKING へ + S108 /tmp 排除)、bandit 0、TOTAL カバレッジ 99.46% → **99.49%**(stmt 1378 + branch 200、CLI 100% 達成で +0.03)、462 tests + 5 連続 stable で CI `fail_under=95` Pass。**Inc.1 全 18 ユニット完成 + Step 19 H1 = ISS-H-001 解消** | k-abe |
| 0.20 | 2026-05-01 | **Step 19 F1.6(CR-0004 (b) Adapter 層追加 + CR-0005 (a) `_HeartbeatSink` Protocol 引数なし化、一括実装)の実施結果を反映**。§7.3.9 表中 UT-001.2-15 を「heartbeat 引数なし契約(CR-0005 (a) 解消後)」に整合化(`sw.heartbeat()` / `hw.heartbeat()` 各 1 回、引数なし、各 Watchdog が内部 clock で取得)。§7.3.15 末尾に「Step 19 F1.6 追加 — UT-005.1-bridge」テーブル(6 ケース、UT-005.1-bridge-01〜06、`vip_api/_validation_bridge.py` Adapter)を新設、`tests/unit/test_validation_bridge.py` で UT を新規実装:01 整合 Settings → 空 list、02 範囲外単独 → ValidationError 1 件、03 多重失敗 → 集約変換、04 整合性違反 → `settings_consistency` field、05 factory + Protocol 適合、06 ControlApi 実体注入。Adapter 配下カバレッジは sealed hierarchy 完全網羅で `assert_never` 防御 4 行を除き 100%(stmt 25/branch 10)。MINOR 区分・CR 不要(本 v0.20 は CR-0004 + CR-0005 の試験範囲反映、SRS / SDD §4.6.C / SDD §4.15.B 本体は CR-0004/0005 で本改訂と同 PR で更新)| k-abe |
| 0.17 | 2026-04-30 | **Step 19 B17(UNIT-005.2 State Observer API TDD 実装)の実施結果を反映 + §7.3.16 新規詳細化(残 2 → 1 骨格)**。**(1) 第 I 部 §7.3.16 新規詳細化(MINOR、CR 不要):** 骨格「薄いラッパー、observer 委譲、非 block / ≥ 6 / —」を **19 ケース、stmt 100% / branch 100%** に詳細化(MC/DC 目標は SDD §4.16 + UTPR §7.4 通り「—」据置、コード規模 30 stmt / 2 branch)。残骨格 2 → 1 ユニットに繰り下げて §7.3.17 化、本節冒頭に整合化注釈を追記。**(2) 判断論点(B17 着手前クロスレビュー、15 度目運用):** 運用性 4 — ① 配置 `src/vip_api/state_observer_api.py`(SDD §4.16 + UTPR §3 既存パス整合)、② `StateSnapshot` は frozen+slots dataclass(SDD「frozen pydantic」より軽量、B12 パターン継続)、③ 注入 3 種を constructor 注入(B9/B10/B15/B16 パターン継続)、④ `observed_at` は `datetime.now(UTC)`(B15 パターン);専門性 5 — ① frozen+slots dataclass で `FrozenInstanceError` 契約試験、② SDD §4.16.C 擬似コード逐語実装(4 atomic 取得 + StateSnapshot 構築)、③ `error_reason` 文字列化(`reason.name`、SDD 設計判断「内部 enum 非露出」)、④ 例外伝播(SDD §4.16.E 設計目標通り、try/except なし、B16 Control API と異なる挙動)、⑤ MC/DC「—」据置 + `mypy --strict src tests` ローカル必須(B12〜B16 教訓継続、6 ステップ連続適用、本 B17 で `PLC0415` 関数内 import を CI 前ローカル ruff で検出 → top-level 化で対処)。**UT 申し送り(継続):** Inc.4 UI 着手時に Resume Gate API 拡張(`pending_set_at_wall` accessor 追加)で `resume_set_at` の `set_at_wall` 透過を実装予定。SRS / SDD / RMF / SAD 本体不変。**(3) 第 II 部 §9.2:** UNIT-005.2 行を 19 tests Pass / カバレッジ 100% / MC/DC 「—」据置で確定。§11 UNIT-005.2 行を「Pass」更新。UNIT-005.1 行のコミット欄を Step 19 B16 PR #24 マージ SHA `92a3f19` で確定。**(4) 試験設計:** UT-005.2-01 で 3 注入の集約、UT-005.2-02 で 100 回 idempotent + mutating API 不呼出契約、UT-005.2-03 を `pytest.parametrize` で 5 サブケース展開(IDLE/RUNNING/PAUSED/STOPPED/ERROR)、UT-005.2-05 で Inc.1 範囲の `resume_set_at is None` 契約(SDD §4.16.B Optional 仕様に合致)、UT-005.2-07 で `WatchdogReason.SW_WATCHDOG` の文字列化、UT-005.2-08 を 4 サブケース展開、UT-005.2-09 で `pairwise` 単調性(B12 パターン)、UT-005.2-10 で `dataclasses.FrozenInstanceError`、UT-005.2-11 で SDD §4.16.E 例外伝播契約、UT-005.2-12 で `observed_at.tzinfo is UTC`。ruff 1 件(PLC0415 関数内 import)→ 手動修正で top-level 化、未カバー line 106(`_resume_set_at` の不到達 return パス)を関数削除で代替(B16 教訓「未使用防御コードは削除」継続適用)、`mypy --strict src tests` 41 source files Pass、bandit 0、TOTAL カバレッジ **100.00%**(stmt 1220 + branch 168)、425 tests + 5 連続 stable で CI `fail_under=95` Pass。**API 層 2/3 完成 + 残 1 ユニット(UNIT-005.3 Validation API クラス B のみ)** | k-abe |
| 0.16 | 2026-04-30 | **Step 19 B16(UNIT-005.1 Control API TDD 実装)の実施結果を反映 + §7.3.15 新規詳細化(残 3 → 2 骨格)**。**(1) 第 I 部 §7.3.15 新規詳細化(MINOR、CR 不要):** 骨格「7 コマンド委譲、例外伝搬 / ≥ 10 / 90%」を **21 ケース、stmt 100% / branch 100% / MC/DC 100%(API 委譲層)** に詳細化(コード規模 75 stmt / 6 branch、骨格 90% を超過し 100% 達成、`start` 3 分岐 + `confirm_resume` 4 分岐 + try/except 3 経路 + `_safe_enqueue` 1 経路 全網羅)。残骨格 3 → 2 ユニットに繰り下げて §7.3.16 化、本節冒頭に整合化注釈を追記。**(2) 判断論点(B16 着手前クロスレビュー、14 度目運用):** 運用性 4 — ① 配置 `src/vip_api/control_api.py`(SDD §4.15 + UTPR §3 既存パス整合)、② `ApiResult` sealed hierarchy(`Ok` / `ValidationFailed` / `ApiRejected` を本ユニット内に定義 + Resume Gate の `Confirmed` / `WrongToken` / `Expired` / `NotPending` を re-export して useless mapping layer を回避)、③ `ValidationApi` Protocol で structural typing 受け(`vip_api` が `vip_api_b` を import せず SEP-001 分離維持、UNIT-005.3 が将来 satisfy)、④ `Settings(drug_name)` 乖離は B15 申し送りを再評価し本 B16 のスコープから除外(`vip_persist.records.Settings` 改修は B6/B7 試験への波及大、Inc.4 UI 着手時に整合化);専門性 5 — ① 値オブジェクト群 `frozen=True, slots=True`(B11/B12/B13/B14/B15 パターン継続)、② 例外を投げない契約は全メソッドの try/except で `ApiRejected(InternalError.UNEXPECTED_EXCEPTION)` 復帰(SDD §4.15.E 逐語実装)、③ `Settings.model_dump()` で pydantic を `Mapping[str, object]` に変換(Command Handler に pydantic を漏らさない)、④ Command Handler / Resume Gate / Validation API の constructor 注入(B9/B10/B15 パターン継続)、⑤ MC/DC 100% 引き上げ + `mypy --strict src tests` ローカル必須(B12/B13/B14/B15 教訓継続、5 ステップ連続適用、本 B16 で防御コード `# pragma: no cover` の `Statement is unreachable` を CI 前ローカル mypy で検出 → 防御コード削除で代替)。**UT 申し送りなし**(本ユニットは委譲層のみ、ロジックは委譲先の UT で網羅済)。SRS / SDD / RMF / SAD 本体不変。**(3) 第 II 部 §9.2:** UNIT-005.1 行を 21 tests Pass / カバレッジ 100% / MC/DC 100% で確定。§11 UNIT-005.1 行を「Pass」更新。UNIT-004.2 行のコミット欄を Step 19 B15 PR #23 マージ SHA `e3a8b9d` で確定。**(4) 試験設計:** UT-005.1-01 で `Settings.model_dump()` payload 透過 + `Mock(spec=ValidationApi)` 検証、UT-005.1-04〜08 を `pytest.parametrize` で 5 サブケース展開(stop/pause/resume/reset/error_reset)、UT-005.1-10〜12 を `pytest.parametrize` で 3 サブケース展開(WrongToken/Expired/NotPending)、UT-005.1-14 を 2 サブケース展開(TimedOut/Failed)、UT-005.1-15〜17 で 3 種例外注入耐性、UT-005.1-18 で `dataclasses.FrozenInstanceError`、UT-005.1-19 で `ApiResult` Union 網羅性 isinstance 検査、UT-005.1-20 で stop 系 5 メソッドの Handler 例外耐性(初回実装で line 224-226 未カバー → 追加で 100% 達成)。ruff 11 件(I001 × 2 / D102 / TRY300 / S105/S106 × 5 / E501 × 2)→ ruff --fix で 2 件 + 手動修正 9 件(`validate_settings` Protocol に docstring 追加 / `confirm_resume` の `return` を `else` ブロック化 / `pyproject.toml` `[tool.ruff.lint.per-file-ignores]` の `tests/**` に `S105` / `S106` 追加 / 長行改行 / 防御コード削除)、`pyproject.toml` の修正で test での `token=...` ハードコード文字列(bandit が password 誤検知)を恒久対応(将来の API 試験でも再発防止)、mypy `Statement is unreachable` を CI 前ローカル mypy で検出・防御コード削除で代替(B12/B13/B14/B15 教訓 5 ステップ連続適用)、`mypy --strict src tests` 39 source files Pass、bandit 0、TOTAL カバレッジ **100.00%**(stmt 1190 + branch 166)、406 tests + 5 連続 stable で CI `fail_under=95` Pass。**API 層着手 + 残ユニット 3 → 2(UNIT-005.2 / 005.3 のみ)** | k-abe |
| 0.15 | 2026-04-30 | **Step 19 B15(UNIT-004.2 Resume Confirmation Gate TDD 実装)の実施結果を反映 + §7.3.14 新規詳細化(残 4 → 3 骨格)**。**(1) 第 I 部 §7.3.14 新規詳細化(MINOR、CR 不要):** 骨格「needs_confirm トグル、期限チェック、状態遷移連携 / ≥ 8 / 100%(RCM-016)」を **15 ケース、stmt 100% / branch 100% / MC/DC 100%** に詳細化(コード規模 80 stmt / 12 branch、`confirm` 4 分岐 + `set_pending` 2 分岐 + `check_expiry` 3 分岐 全網羅、RCM-016 SDD §4.14 逐語実装)。残骨格 4 → 3 ユニットに繰り下げて §7.3.15 化、本節冒頭に整合化注釈を追記。**(2) 判断論点(B15 着手前クロスレビュー、13 度目運用):** 運用性 4 — ① `ResumeDetail` 型は `resume_gate.py` 内に新規定義(関心分離、Inc.4 で `vip_persist.records` への移動を検討)、② `StateMachine` を constructor 注入(B9/B10 watchdog/control_loop パターン継続、UT で `Mock(spec=StateMachine)`)、③ Logger 据置(B4/B9 パターン継続、SDD 擬似コードの `_logger.log_resume_*` は標準 `logging.Logger.info` / `warning` で実装)、④ `check_expiry` の定期呼出責任は外部(本ユニットでは API のみ提供、Inc.4 UI で wire);専門性 5 — ① 値オブジェクト群 `frozen=True, slots=True`(B11/B12/B13/B14 パターン継続)、② `secrets.token_hex(16)` 128 bit token、③ `hmac.compare_digest` 定数時間比較、④ `time.monotonic()` クロック逆転耐性 + `clock` constructor 注入、⑤ MC/DC 100% 引き上げ + `mypy --strict src tests` ローカル必須(B12/B13/B14 教訓継続、4 ステップ連続適用、本 B15 で fixture 戻り値型不整合(`yield` → `return` 変換に伴う `Iterator[X]` 注釈残存)を CI 前ローカル mypy で検出・修正)。**UT 申し送りなし**(本ユニットは決定論的 monotonic + secrets だけで完結、実時間試験不要)。SRS / SDD / RMF / SAD 本体不変。**(3) 第 II 部 §9.2:** UNIT-004.2 行を 15 tests Pass / カバレッジ 100% / MC/DC 100% で確定。§11 UNIT-004.2 行を「Pass」更新。UNIT-002.3 行のコミット欄を Step 19 B14 PR #22 マージ SHA `00093e1` で確定。**(4) 試験設計:** UT-004.2-01 で token 32 hex 検証、UT-004.2-03 で `request_transition(TransitionEvent(CMD_RESUME, meta={"resume_token": token}))` 呼出を `Mock` で検証(SRS-RCM-016 機械担保)、UT-004.2-04 で `WrongToken` 時 pending 維持 + State Machine 不変、UT-004.2-07 で `clock.advance(EXPIRY_SEC+1)` で fake clock 期限切れ判定、UT-004.2-09 で 1000 cycle token ユニーク(128 bit エントロピー試験)、UT-004.2-10 で `caplog` の "expir" warning 発火、UT-004.2-12 で `dataclasses.FrozenInstanceError`、UT-004.2-15 で 2 スレッド `Barrier` 同期 confirm の排他性(`Confirmed` × 1 + `NotPending` × 1)。ruff 6 件(TC003 / RUF022 / UP017 × 3 / PT022)→ ruff --fix で 5 件 + 手動修正 1 件(`Decimal` を TYPE_CHECKING ブロックに移動、`Iterator` 注釈削除)、mypy fixture 戻り値型(`yield` → `return` 後の `Iterator[ResumeConfirmationGate]` → `ResumeConfirmationGate`)を CI 前ローカル mypy で検出・修正(B12 教訓 4 ステップ連続適用)、`drug_name="saline"` を test fixture から削除(`Settings` モデルに該当フィールドなし、SDD §4.15 と `vip_persist.records` の差異は別ユニット責任、本 B15 のスコープ外)。`mypy --strict src tests` 37 source files Pass、bandit 0、TOTAL カバレッジ **100.00%**(stmt 1115 + branch 160)、385 tests + 5 連続 stable で CI `fail_under=95` Pass。**Inc.1 残 RCM(RCM-016)完了**(RCM-019 + RCM-001 + RCM-003 + RCM-004 + RCM-015 + RCM-016 で Inc.1 担当 6 RCM 全完成)| k-abe |
| 0.14 | 2026-04-30 | **Step 19 B14(UNIT-002.3 Event Injection Stub TDD 実装)の実施結果を反映 + §7.3.13 新規詳細化(残 5 → 4 骨格)**。**(1) 第 I 部 §7.3.13 新規詳細化(MINOR、CR 不要):** 骨格「Inc.2 以降のスタブ、本 Inc.1 では空動作の確認のみ / ≥ 3 / —」を **12 ケース、stmt 100% / branch 100%** に詳細化(MC/DC 目標は SDD §4.11 + UTPR §7.4 通り「—」据置、コード規模 33 stmt / 0 branch、Inc.1 no-op スタブ範囲)。残骨格 5 → 4 ユニットに繰り下げて §7.3.14 化、本節冒頭に整合化注釈を追記。**(2) 判断論点(B14 着手前クロスレビュー、12 度目運用):** 運用性 4 — ① 配置パッケージ `src/vip_sim/event_injection.py`(SDD §4.11.F + UTPR §3 / §11 パス整合、他 vip_sim/ ユニットと一貫)、② 命名 `VirtualHwEventKind`(`vip_ctrl.state_machine.EventKind` との衝突回避、import 時 alias 不要)、③ no-op 検証は Pump Simulator + Pump Observer 連携で「inject 後も observe 値不変」契約試験(SDD §4.11.F.2)、④ `metadata: Mapping[str, object]` で受領(Inc.2 で `types.MappingProxyType` 検討の余地);専門性 5 — ① 値オブジェクト `VirtualHwEvent` を `frozen=True, slots=True`(B11/B12/B13 パターン継続、`_empty_metadata` 専用 factory で `mypy --strict` 整合)、② `_buffer = collections.deque(maxlen=1000)` 自動破棄、③ `_lock = threading.Lock()`(再帰不要)、④ MC/DC 目標 — 据置 + stmt/branch 100% 網羅、⑤ `mypy --strict src tests` ローカル必須(B12/B13 教訓継続)。**UT 申し送りなし**(本ユニットは Inc.1 では no-op、Inc.2 正式機能化時に Pump 連動試験追加予定)。SRS / SDD / RMF / SAD 本体不変。**(3) 第 II 部 §9.2:** UNIT-002.3 行を 12 tests Pass / カバレッジ 100% / MC/DC 「—」据置で確定。§11 UNIT-002.3 行を「Pass」更新。UNIT-001.3 行のコミット欄を Step 19 B13 PR #21 マージ SHA `6c1a374` で確定。**(4) 試験設計:** UT-002.3-01〜04 で基本 + limit 動作、UT-002.3-05 で 1001 件投入のリングバッファ自動破棄(SDD §4.11.F.3 仕様)、UT-002.3-06 で Pump.observe 不変の no-op 契約(SDD §4.11.F.2)、UT-002.3-07 で 10 スレッド × 10 件 = 100 件の並行 inject 損失なし、UT-002.3-08 で `dataclasses.FrozenInstanceError`、UT-002.3-09 で 3 種 kind 列挙網羅、UT-002.3-10 で recent_events 返却 list の独立性(`append` で内部不変)、UT-002.3-11 で severity/metadata 透過、UT-002.3-12 で metadata 省略時の `_empty_metadata` factory 経路網羅(初回実装で line 72 未カバー → UT-002.3-12 追加で 100% 達成)。ruff 2 件(TC003 Mapping を TYPE_CHECKING ブロック移動 + RUF002 docstring 中の `×` を `x` に変換)、mypy `--strict src tests` 35 source files Pass(`unused-ignore` を CI 前ローカル実行で検出・修正、B12/B13 教訓継続)、bandit 0、TOTAL カバレッジ 100.00%(stmt 1035 + branch 148)、370 tests + 5 連続 stable で CI `fail_under=95` Pass。**Inc.2 接続点 UNIT-002.* 全 4 ユニット完成**(UNIT-002.1 Pump Simulator + UNIT-002.2 Pump Observer + UNIT-002.3 Event Injection Stub + UNIT-002.4 HW Failsafe Timer で仮想ハードウェア層が単体動作完結) | k-abe |
| 0.13 | 2026-04-30 | **Step 19 B13(UNIT-001.3 Command Handler TDD 実装)の実施結果を反映 + §7.3.12 新規詳細化(残 6 → 5 骨格)**。**(1) 第 I 部 §7.3.12 新規詳細化(MINOR、CR 不要):** 骨格「≥ 10 / 95%」を 23 ケース / 100% に展開、MC/DC 目標を 95% → **100%** に引き上げ(B5/B7/B8/B10/B11/B12 前例継続)、残骨格 6 → 5 ユニットに繰り下げて §7.3.13 化、本節冒頭に整合化注釈を追記。**(2) 判断論点(B13 着手前クロスレビュー、11 度目運用):** 運用性 4 — ① `Command` / `CommandKind` を command_handler.py 内で定義(UNIT-005.1 が将来 import)、② `_is_acceptable_in_state` は state_machine.py の既存 `TRANSITION_TABLE` を引用(DRY 原則)、③ SRS-P03/P04 統計的時間試験(P95)は ITPR §5.6 申し送り(B4/B5/B8/B10 教訓 5 例目)、UT は緩い 200 ms 境界スモーク 1 件のみ、④ `Command(kind, payload)` シンプル構造で payload は opaque(検証は UNIT-005.1 責務);専門性 5 — ① 値オブジェクト群 frozen dataclass、② dispatch スレッド管理 B4/B9/B10 パターン、③ `uuid.uuid4()` token 一意性、④ MC/DC 100% 引き上げ、⑤ `mypy --strict src tests` を CI と同じ引数でローカル実行(B12 教訓継続)。**UT 申し送り:** SRS-P03/P04 P95 統計試験 → ITPR §5.6 「実時間スレッド統計試験」カテゴリ(5 例目)。SRS / SDD / RMF / SAD 本体不変。**(3) 第 II 部 §9.2:** UNIT-001.3 行を 23 tests Pass / カバレッジ 100% / MC/DC 100% で確定。§11 UNIT-001.3 行を「Pass」更新。UNIT-002.2 行のコミット欄を Step 19 B12 PR #20 マージ SHA `28cc912` で確定。**(4) 試験設計:** UT-001.3-05 で stop ファストパス + 既存キュー全破棄(SupersededByStopError)、UT-001.3-08 で TimedOut(elapsed_ms 確認)、UT-001.3-09 で 10 スレッド並行 token 一意性、UT-001.3-12 で patch.object + 完全閉路(start/stop)で例外パス + ループ継続(2 セクションに分けて race 排除)、UT-001.3-19 で SRS-P04 機能スモーク 200 ms 境界、UT-001.3-21 で `dataclasses.FrozenInstanceError`、UT-001.3-23 で未マップ `CONFIRM_RESUME` 拒否(line 313 網羅)。`# pragma: no cover` 4 件:`_enqueue_fast_path` の queue.Empty race-window guard(line 324)、`if ev is not None` 防御コード(line 328 / 365)、`Failed(error=result.error)` else 分岐(`_is_acceptable_in_state` で事前 guard 済の理論的経路、line 358)。ruff 9 件(I001/RUF022/D401/RUF100/PLC0415/ARG001/F401)→ ruff --fix + 手動修正、mypy fixture 戻り値型 `Iterator[CommandHandler]` に修正(B12 「mypy --strict src tests」教訓継続で初回検出)、TOTAL カバレッジ 100%、358 tests 5 連続 stable | k-abe |
| 0.12 | 2026-04-30 | **Step 19 B12(UNIT-002.2 Pump Observer TDD 実装)の実施結果を反映 + §7.3.11 新規詳細化(残 7 → 6 骨格)**。**(1) 第 I 部 §7.3.11 新規詳細化(MINOR、CR 不要):** 骨格「≥ 6 / —」を 10 ケース / 100% に展開、MC/DC 目標を骨格「—」から **100%** に明示化(B5/B7/B8/B10/B11 前例継続)、残骨格 7 → 6 ユニットに繰り下げて §7.3.12 化、本節冒頭に整合化注釈を追記。**(2) 判断論点(B12 着手前クロスレビュー、10 度目運用):** 運用性 2 — ① atomic 性確保は SDD §4.10.C 通り Pump の `_lock` 借用 + private フィールド直接読み(`# noqa: SLF001` 抑制 + docstring に SDD 引用)、Pump 側 API 表面積を増やさず B11 完了状態を維持、② PumpSnapshot は SDD §4.10.B 通り 6 フィールド `frozen=True, slots=True`、Control Loop の `PumpSnapshot` Protocol(3 プロパティ)を structural typing で satisfies;専門性 5 — ① frozen+slots で `FrozenInstanceError`、② `time.monotonic()` で観測時刻、③ 6 フィールド単一 lock 区間、④ Observer stateless、⑤ MC/DC 100% 引き上げ。**UT 申し送りなし**(Decimal 演算 + lock 借用のみ)。SRS / SDD / RMF / SAD 本体不変。**(3) 第 II 部 §9.2:** UNIT-002.2 行を 10 tests Pass / カバレッジ 100% / MC/DC 100% で確定。§11 UNIT-002.2 行を「Pass」更新。UNIT-002.1 行のコミット欄を Step 19 B11 PR #19 マージ SHA `cbc2578` で確定。**(4) 試験設計:** UT-002.2-01〜04 で初期/target/advance/failsafe 状態反映、UT-002.2-05 で `dataclasses.FrozenInstanceError` 不変性検証、UT-002.2-06 で `pairwise(timestamps)` 単調性、UT-002.2-07 で別スレッド advance_time × 200 observe の atomic 性、UT-002.2-08/09 で Control Loop Protocol(`PumpSnapshotObserver` / `PumpSnapshot`)structural typing 適合、UT-002.2-10 で副作用なし(observe 100 回後 Pump 状態不変)。B11 と異なる設計問題(private アクセス + structural typing)に対処することで、ステートレス薄ラッパーユニットの試験パターン蓄積。ruff 6 件(I001 / TC001 × 3 / F401 / RUF007)→ TYPE_CHECKING ブロック移動 + `itertools.pairwise` 採用で全件解消、mypy `--strict` 18 source files Pass、bandit 0、pip-audit `pip` 自体は CI 経路で除外、TOTAL 100%、335 tests 3 連続 stable | k-abe |
| 0.11 | 2026-04-29 | **Step 19 B11(UNIT-002.1 Pump Simulator TDD 実装)の実施結果を反映 + §7.3.10 新規詳細化(残 8 → 7 骨格)**。**(1) 第 I 部 §7.3.10 新規詳細化(MINOR、CR 不要):** 骨格「≥ 10 / 95%」を 21 ケースに展開、MC/DC 目標を 95% → **100%** に引き上げ(B5/B7/B8/B10 前例継続)、残骨格 8 → 7 ユニットに繰り下げて §7.3.11 化、本節冒頭に整合化注釈を追記。**(2) 判断論点(B11 着手前クロスレビュー、9 度目運用):** 運用性 3 — ① SRS-031 観測契約 → 5 getter (current_flow / accumulated_volume / elapsed_min / is_failsafe_active / failsafe_reason) を `RLock` 保護下で公開(UNIT-002.2 が将来ラップ)、② 積算量オーバーフロー → `logger.warning` のみ初回出力、加算継続(クランプなし、Inc.4 UI で対応)、③ `release_failsafe()` を public 実装(UT 単体検証、本番 UNIT-005.1 接続は将来);専門性 5 — ① Decimal 精度、② RLock、③ SRS-P01 過渡応答(τ で 63%、5τ で 99%)、④ MC/DC 100% 引き上げ、⑤ 並行勝利試験。**UT 申し送りなし**(本ユニットは決定論的 Decimal 演算のみ)。SRS / SDD / RMF / SAD 本体不変。**(3) 第 II 部 §9.2:** UNIT-002.1 行を 21 tests Pass / カバレッジ 100% / MC/DC 100% で確定。§11 UNIT-002.1 行を「Pass」更新。UNIT-001.2 行のコミット欄を Step 19 B10 PR #18 マージ SHA `d02b336` で確定。**(4) 試験設計:** UT-002.1-03/04 で過渡応答(τ・5τ)、UT-002.1-07 で 1 時間定常積算 ±5%、UT-002.1-09 で `force_stop_failsafe` 冪等(初発 reason 保持)、UT-002.1-12 で failsafe 中の時間進行のみ仕様(SDD §4.9.C)、UT-002.1-17 で `Barrier` 同期 2 スレッド並行勝利、UT-002.1-20 で `caplog` で overflow 警告検証(B10 caplog パターン継続)、UT-002.1-21 で SRS-031 観測契約 5 項目型整合。B4/B9/B10 パターン継続で初回近傍 Pass(ruff 25 件 → 23 件 auto-fix + 2 件手動 RUF003 修正、mypy 17 source files Pass、bandit 0、TOTAL 100%、325 tests 3 連続 stable) | k-abe |
| 0.10 | 2026-04-29 | **Step 19 B10(UNIT-001.2 Control Loop TDD 実装)の実施結果を反映 + §7.3.9 新規詳細化(残 9 → 8 骨格)**。**(1) 第 I 部 §7.3.9 新規詳細化(MINOR、CR 不要):** v0.9 までは §7.3.9 残骨格表で「`pytest-benchmark` でサイクル計測」とされていたが、B4/B5/B8/B9 教訓「非決定論的試験は IT へ」の継続適用で SRS-P02 ±10% 実時間周期精度試験は ITPR §5.6 申し送り(新規カテゴリ)。新 §7.3.9 として詳細 UT テーブル(UT-001.2-01〜19、展開 21 ケース)を書き下ろし、既存 9 ユニット骨格は §7.3.10 に移動して 8 ユニットに繰り下げ。本節冒頭に整合化注釈を追記。**(2) 判断論点(B10 着手前クロスレビュー、8 度目運用):** 運用性 4 — ① `WatchdogReason.CONTROL_LOOP_EXCEPTION`(SDD §4.6.C 擬似コード)→ 既存 `WatchdogReason.OTHER` 使用(state_machine.py 不変、B9 「add-only」継続)、② `EventKind.AUTO_STOP_DURATION_REACHED`(SDD §4.6.C 擬似コード)→ duration-based 自動停止は SRS-012/031 にも記載なし、本 B10 で実装せず将来 CR で整理申し送り(dose-based のみ実装)、③ Pump / Observer Protocol を control_loop.py 内に新規定義(`PumpFlowController` / `PumpSnapshotObserver` / `PumpSnapshot`)、④ `Settings` 型は records.py を `settings_provider` 経由で受け取り flow_validator.Settings に変換;専門性 5 — ① クロック DI、② `tick()` テストフック、③ Logger 据置、④ SRS-P02 実時間試験 ITPR 申し送り、⑤ MC/DC 100%。SRS / SDD / RMF / SAD 本体不変。**(3) UT 申し送り:** SRS-P02 ±10% 実時間周期精度統計試験 + `pytest-benchmark` CPU 占有率測定 → ITPR §5.6 新規カテゴリ「実時間スレッド統計試験」(B4/B5/B8 の UT 申し送り 4 例目)。**(4) 第 II 部 §9.2:** UNIT-001.2 行を 21 tests Pass / カバレッジ 100% / MC/DC 100% で確定。§11 UNIT-001.2 行を「Pass」更新。UNIT-001.5 行のコミット欄を Step 19 B9 PR #17 マージ SHA `5f34148` で確定。**(5) 試験設計:** UT-001.2-02/03 で sw/hw heartbeat の順序保証(SDD §4.6 キーポイント「heartbeat は tick 先頭」)を検証、UT-001.2-04 で Validator NEGATIVE → ERROR 経路、UT-001.2-05/06a/06b で auto-stop 境界(>/=/<)、UT-001.2-08 で `WatchdogReason.OTHER` 記録、UT-001.2-15 で fake_clock タイムスタンプの heartbeat 引数透過、UT-001.2-19 で `period_sec=0.0` の overrun ログ網羅(初回実装で 1 ステートメント・1 分岐未カバー → caplog 戦略で追加し 100% 達成)。B9 に続き B4 パターン踏襲で初回近傍 Pass(ruff 5 件 / mypy 0 / bandit 0 / pip-audit `pip` 自体は CI の `--exclude-editable` 経由で除外され 0)| k-abe |
| 0.9 | 2026-04-24 | **Step 19 B9(UNIT-001.5 SW Watchdog TDD 実装)の実施結果を反映 + §7.3.8 新規詳細化(残 10 → 9 骨格)**。**(1) 第 I 部 §7.3.8 新規詳細化(MINOR、CR 不要):** v0.8 までは §7.3.8 残骨格表で「**500 ms** 判定(境界 499/500/501)」と誤記されていたが、SDD v0.2 §4.8 / SRS-RCM-003 / RMF RCM-003 のいずれも SW 側は **300 ms**(HW 側が 500 ms)。新 §7.3.8 として詳細 UT テーブル(UT-001.5-01〜12)を書き下ろし、既存の残 10 ユニット骨格は §7.3.9 に移動して 9 ユニットに繰り下げ。本節冒頭に整合化注釈を追記。**(2) 判断論点(B9 着手前クロスレビュー、7 度目運用):** 運用性 1 — `WatchdogReason` enum は state_machine.py 既存の `SW_WATCHDOG` を使う(SDD §4.8.C 擬似コード `SW_HEARTBEAT_TIMEOUT` は参考名扱い、state_machine.py 不変、B7/B8 「add-only / 既存成果物不変」継続);専門性 5 — ① クロック DI、② クロック逆転 → Trip(安全側、B4 判断継続)、③ `check_once` テストフック、④ Logger 据置(B4 判断継続)、⑤ MC/DC 目標 100%。SRS / SDD / RMF / SAD 本体不変。**(3) UT 申し送り:** なし(階層防御の時間順序試験 UT-001.5-12 は fake_clock で決定論的に可能、subprocess / 実時間不要)。**(4) 第 II 部 §9.2:** UNIT-001.5 行を 19 tests Pass / カバレッジ 100% / MC/DC 100% で確定。§11 UNIT-001.5 行を「Pass」更新。UNIT-003.2 行のコミット欄を Step 19 B8 PR #16 マージ SHA `5c56cea` で確定。**(5) 試験設計:** UT-001.5-02/05/06b で State Machine の `on_watchdog_timeout(WatchdogReason.SW_WATCHDOG)` 呼出を `assert_called_once_with` で検証、UT-001.5-03a/b/c/d で境界 299/300/300+ε/350 ms の 4 点網羅、UT-001.5-12 で SW(301 ms Trip)→ HW(501 ms Trip)の階層防御時間順序を同一 fake_clock に対して並列動作で検証、UT-001.5-08 で state_machine.on_watchdog_timeout 例外耐性(SDD §4.8.E)を検証。B4 パターン踏襲により一発 Pass 達成(ruff / mypy / bandit / pip-audit 追加修正 0 件) | k-abe |
| 0.8 | 2026-04-24 | **Step 19 B8(UNIT-003.2 Checksum Verifier TDD 実装)の実施結果を反映 + §7.3.7 新規詳細化(残 11 → 10 骨格)**。**(1) 第 I 部 §7.3.7 新規詳細化(MINOR、CR 不要):** B7 までは骨格のみの節を、着手前クロスレビュー(運用性 1 + 専門性 4)解消後に詳細 UT テーブル(UT-003.2-01〜15)として書き下ろし、既存の残 11 ユニット骨格は §7.3.8 に移動して 10 ユニットに繰り下げ。本節冒頭に整合化注釈を追記。**(2) 判断論点:** 運用性 — 既存の `compute_sha256` / `compute_payload_checksum` 重複は不変維持(B7 教訓「add-only 拡張」踏襲);専門性 — ① `hmac.compare_digest` 定数時間比較、② 大小 hex の `.lower()` 正規化、③ 不正 `expected` は例外なし `False`、④ MC/DC 目標 95% → **100%** 引き上げ。SRS / SDD / RMF / SAD 本体不変。**(3) UT 申し送り:** SDD §4.13.F 末尾「タイミング試験(参考)」は B4/B5 教訓(非決定論的試験は IT へ)に従い **ITPR §5.6 申し送り**。**(4) 第 II 部 §9.2:** UNIT-003.2 行を 32 tests Pass / カバレッジ 100% / MC/DC 100% で確定、§9.2 テーブル内の UNIT-003.1 行重複(骨格行と実績行の二重状態、B7 で発生)を整理して UNIT-003.2 正しい位置に配置。§11 UNIT-003.2 行を「Pass」更新。UNIT-003.1 行のコミット欄を Step 19 B7 PR #15 マージ SHA `982c568` で確定。**(5) 試験設計:** NIST 既知ベクタ 2 種、`pytest.parametrize` で UT-003.2-05/06/10/11 を 16 サブケースに展開、`hypothesis` プロパティ 2 種(`max_examples=200` のラウンドトリップ + 異なるバイト列の digest 相違)。専門性/運用性の論点分離により、5 論点中 4 論点を専門性に分類して提示を簡潔化できたことを実証(B7 教訓の運用化) | k-abe |
| 0.7 | 2026-04-24 | **Step 19 B7(UNIT-003.1 Serializer TDD 実装)の実施結果を反映 + §7.3.6 新規詳細化(残 12 → 11 骨格)**。**(1) 第 I 部 §7.3.6 新規詳細化(MINOR、CR 不要):** B6 までは骨格のみの節を、着手前クロスレビュー 7 論点(別途 1 論点を実装時発覚)解消後に詳細 UT テーブル(UT-003.1-01〜17)として書き下ろし、既存の残 12 ユニット骨格は §7.3.7 に移動して 11 ユニットに繰り下げ。本節冒頭に整合化注釈を追記(推奨方針全 7 + 8 論点を箇条書きで記録)。**(2) 判断論点:** ① `PersistedRecord`/`RawPersistedRecord` の別 pydantic モデル化、② `build_persisted_record` ファクトリを Serializer 側に配置、③ `State` 名前シリアライズ(auto() リファクタリングリスク回避)、④ records.py 不変(B6 スコープ境界維持)、⑤ hypothesis `max_examples=200`、⑥ `current_schema_version()` 関数実装、⑦ MC/DC 目標 95%→100% 引き上げ、⑧ `bytes` 型の `__bytes__` base64 タグ(実装時発覚、§4.12.C `_default` 擬似コード拡張 MINOR)。SRS / SDD / RMF / SAD 本体不変。**(3) 第 II 部 §9.2:** UNIT-003.1 行を 26 tests Pass / カバレッジ 100.00% / MC/DC 100% で確定。§11 UNIT-003.1 行を「Pass」更新。UNIT-004.1 行のコミット欄を Step 19 B6 PR #14 マージ SHA `faf743b` で確定。**(4) 試験設計:** Decimal / State / bytes の 3 種タグ(`__decimal__` / `__state__` / `__bytes__`)ラウンドトリップ、hypothesis `max_examples=200` で SRS-004 一貫 settings + 任意 runtime_state のラウンドトリップ網羅、決定論性 hypothesis `max_examples=50` で 5 回 `to_json` 全一致、Integrity Validator との統合試験で E2E 検証。教訓 1 件を DEVELOPMENT_STEPS §教訓に追記(「判断材料の抽象度調整 — ユーザーフィードバック『書いてもらってもよくわからくて判断できない』への応答」) | k-abe |
| 0.6 | 2026-04-23 | **Step 19 B6(UNIT-004.1 Integrity Validator TDD 実装)の実施結果を反映 + §7.3.5 整合化**。**(1) 第 I 部 §7.3.5 整合化(MINOR、CR 不要):** Step 19 B3 / B4 / B5 で定着した着手前クロスレビューで SDD §4.5 と v0.5 までの本節の間に 4 件の不整合を発見、ユーザー合意のもとで SDD を真として本節を整合化:(a) 戻り値型を `Err([...])` / `Ok(snapshot)` → SDD §4.5.A の `FailsafeRecommended(reasons: list[IntegrityFailure])` / `Ok(TrustedRecord)` に統一、(b) UT-004.1-03/04/08 を pydantic 管轄(§4.5.E 「本ユニット到達前に `ValidationError`」)から §4.5.B 未網羅項目(`SchemaVersionUnsupported` / `DoseVolumeOutOfRange` / `SettingsInconsistent`)に差し替え、(c) UT-004.1-09 `FutureTimestamp` を §4.5.B 非存在検証(SRS-026/027 にも未要求)から `AccumulationExceedsDose`(HZ-001 過量投与直結)に差し替え、(d) UT-004.1-10 `ERROR ∧ error_reason==None` を §4.5 非存在から `StateContradiction("RUNNING but current_flow=0")` に差し替え。SRS / SDD / RMF / SAD 本体は不変。**(2) §7.3.5 試験テーブル:** 12 行を SDD §4.5.B 擬似コード 9 検証項目に全整合化、補助観点 9 件(UT-004.1-13〜20 + hypothesis 2 件)を展開。MC/DC 目標 100% を維持(`validate` の複合条件 + `check_settings_consistency` の dose==0 分岐)。**(3) 第 II 部 §9.2:** UNIT-004.1 行を 33 tests Pass / カバレッジ 100.00% / MC/DC 100% で確定。§11 UNIT-004.1 行を「Pass」更新。UNIT-003.3 行のコミット欄を Step 19 B5 マージ SHA `0a1cc34` で確定。**(4) 試験設計:** hypothesis プロパティ 3 件(`_consistent_valid_settings` 戦略、1 bit 反転、2+ 破損)、`pytest.parametrize` で UT-004.1-03/04/05/17/19 を計 14 サブケースに展開、FrozenInstanceError / `SUPPORTED_SCHEMA_VERSIONS` 契約 / `compute_sha256` 既知ベクタで補助観点を実装。依存型(`Settings` / `RuntimeState` / `RawPersistedRecord` / `TrustedRecord`)は `src/vip_persist/records.py` に先行実装し UNIT-003.1 Serializer(Step 19 B7 以降予定)で再利用。教訓を DEVELOPMENT_STEPS §教訓に追記 | k-abe |
| 0.5 | 2026-04-23 | **Step 19 B5(UNIT-003.3 Atomic File Writer TDD 実装)の実施結果を反映 + §7.3.4 整合化**。**(1) 第 I 部 §7.3.4 整合化(MINOR、CR 不要):** Step 19 B3 / B4 教訓の運用継続で着手前クロスレビュー実施、4 件の不整合を発見:(a) API 名 `write_atomic(path, data)` → SDD §4.4.A の `write(data, target_path)` + `read` + `rollback` 3 API へ整合化、(b) UT-003.3-07 並行書込を「ロック機構動作」→ SDD §4.4.C「呼出側責任、本ユニットはロックしない」と整合な「ステートレス確認(異なる target_path への並行書込)」へ整合化、(c) UT-003.3-08 `Err(DiskFullError)` → SDD §4.4.E 整合の `WriteErr(OSError)` + `errno==ENOSPC` へ、(d) UT-003.3-10 subprocess + SIGKILL 電源断試験は CI 安定性 + SDD §4.4.E「原理的に検知不可能 / load 側で担保」により ITPR §5.6 申し送り、本 UT では内部ステップ観測 + `os.fsync` 呼出モック検証で代替(UT-003.3-10a/10b に分割)。SRS / SDD / RMF / SAD 本体は不変。**(2) §7.3.4 試験テーブル:** 12 行へ再整備(UT-003.3-02b bak 置換、UT-003.3-10a/10b 分割、引数順を SDD に統一)。MC/DC 目標を 95% → **100%** に引き上げ(コード規模 78 stmt / 6 branch、試験設計で完全網羅可能)。**(3) 第 II 部 §9.2:** UNIT-003.3 行を 21 tests Pass / カバレッジ 100.00% / MC/DC 100% で確定。§11 UNIT-003.3 行を「Pass」更新。UNIT-002.4 行のコミット欄を Step 19 B4 マージ SHA `3c7a933` で確定。**(4) 試験設計:** 補助観点 9 件(read 2 + rollback 3 + 往復 1 + bak 世代管理 1 + best-effort unlink 1 + 非 POSIX 1)、`tmp_path` fixture + `unittest.mock.patch` で `os.replace`/`os.fsync`/`Path.unlink` を注入して OSError 経路を網羅。教訓 2 件を DEVELOPMENT_STEPS §教訓に記録(着手前クロスレビューの運用 3 度目定着 + OSError 注入パターンの再利用性) | k-abe |
