# ソフトウェア結合試験計画書/報告書

**ドキュメント ID:** ITPR-VIP-001
**バージョン:** 0.2
**作成日:** 2026-05-01
**対象製品:** 仮想輸液ポンプ(Virtual Infusion Pump)/ VIP-SIM-001
**対象ソフトウェアバージョン:** v0.2.0-inc1(予定、Inc.1 完了時)
**対象範囲:** Inc.1(流量制御コア、全 17 ソフトウェアユニットの結合)
**安全クラス:** C(IEC 62304)

| 役割 | 氏名 | 所属 | 日付 | 署名 |
|------|------|------|------|------|
| 作成者 | k-abe | — | 2026-05-01 | (セルフ) |
| レビュー者 | k-abe(単独開発下の独立性擬制 — CCB-VIP-001 §4.1.1 / SRMP-VIP-001 §3.2 準拠) | — | 2026-05-01 | (セルフ) |
| 承認者 | k-abe(CCB 兼任、軽微区分のためインターバル対象外) | — | 2026-05-01 | (セルフ) |

---

> 本書は結合試験の **計画**(第 I 部)と **実施結果**(第 II 部、報告)を一体で管理する。v0.1 時点では計画のみを記述する。Inc.1 全 17 ユニットの UT 完了(Step 19 B18 時点、UTPR-VIP-001 v0.19)を前提に、結合試験の戦略・観点・代表ケースを骨格化する。詳細試験ケースは Step 19 F(ITPR 完了)で第 II 部とともに完成させる段階成熟方式を採る(UTPR v0.1 採用根拠 L804「代表 5 + 骨格 12」と同パターン)。

## 用語と略語(本書で初出のもの)

| 略語 | フルネーム | 意味 |
|------|-----------|------|
| IT | Integration Test | 結合試験 |
| IF-U | Internal Inter-Unit Interface | ユニット間内部インタフェース |
| IF-E | External Interface | 外部インタフェース |
| E2E | End to End | 端対端(永続化 ↔ 整合性検証の往復など、複数ユニットを跨ぐシナリオ) |
| RCM | Risk Control Measure | リスクコントロール手段 |
| SEP | Separation(SAD §9 / IEC 62304 §5.3.5)| クラス C / B 分離設計識別子 |
| MC/DC | Modified Condition/Decision Coverage | 改良条件分岐網羅 |
| SOUP | Software of Unknown Provenance | 素性不明のソフトウェア |
| AST | Abstract Syntax Tree | 抽象構文木(SEP-001 機械検証で使用) |
| HZ | Hazard | ハザード(ISO 14971) |
| PRB | Problem Report | 問題報告(本プロジェクトでは `PRB-NNNN`) |
| CR | Change Request | 変更要求 |

## 1. 目的と適用範囲

### 1.1 目的

本書は IEC 62304:2006+A1:2015 箇条 5.6(ソフトウェア結合および結合試験)の要求事項を満たし、本プロジェクトの安全クラス C 要求(箇条 5.6.x)に従って、Inc.1 全 17 ソフトウェアユニットの結合戦略・結合検証・結合試験計画と試験実施結果を記録する。本書の到達目標は次のとおり。

1. **構造的検証(箇条 5.6.2):** UT 完了済 17 ユニットが SAD 設計どおりに結合されていることをレビューと AST 静的解析で検証する。
2. **機能的検証(箇条 5.6.3 / 5.6.4):** ユニット間 IF-U / 外部 IF-E 動作、リスクコントロール手段(RCM-001 / 003 / 004 / 015 / 016 / 019、Inc.1 担当 6 件)が結合状態で機能すること、SRS-P02 / P03 / P04 など UT で検証不能な実時間/統計挙動、SEP-001 ランタイム分離、外乱(電源断・サイドチャネル)耐性を検証する。
3. **回帰試験基盤(箇条 5.6.6):** 結合試験を `pytest` ベースで CI に組み込み、Step 19 F 以降の実装変更に対して継続的に Pass/Fail 判定する。

### 1.2 適用範囲

| 区分 | 範囲 | 備考 |
|------|------|------|
| ソフトウェアユニット | UNIT-001.1 〜 UNIT-005.3 全 17 件(SDD §3.1 / UTPR §11) | UT 完了済(UTPR v0.19 §11)|
| パッケージ | `src/vip_ctrl/` `src/vip_sim/` `src/vip_persist/` `src/vip_integrity/` `src/vip_api/` `src/vip_api_b/` 全 6 パッケージ | SAD §3 階層構造 |
| RCM | Inc.1 担当 6 件:RCM-001 / RCM-003 / RCM-004 / RCM-015 / RCM-016 / RCM-019 | RMF v0.2 / SAD §6 |
| 分離(SEP) | SEP-001(クラス C ↔ クラス B 分離) | SAD §9 / IEC 62304 §5.3.5 |
| 試験対象外 | Inc.2 以降のスタブ機能(UNIT-002.3 inject 副作用、UNIT-005.3 `drug_name` 検証、UNIT-005.2 `resume_set_at` 透過)、UI / 永続化スケジューラ | Inc.2〜4 ITPR 改訂で順次追加 |

### 1.3 第 I 部 / 第 II 部の関係

- **第 I 部(計画、§3〜§10):** Step 19 D-2(本ステップ)で v0.1 として骨格化、UT 完了状況を踏まえた結合戦略・観点・代表ケースを記述する。代表 3 観点(RCM-015 永続化 E2E / RCM-019 状態遷移結合 / RCM-016 再開ガード)を詳細化、残 7 観点(RCM-001 / RCM-003 / RCM-004 + 分散 4 カテゴリ)は骨格(観点・ケース数目安・関連 UT-ID のみ)。
- **第 II 部(報告、§11〜§13):** Step 19 F(ITPR 完了)で実施結果を記入。骨格化のみ v0.1 で実施。

## 2. 参照文書

| ID | 文書名 | バージョン | 参照箇所 |
|----|--------|----------|---------|
| [1] | ソフトウェア要求仕様書(SRS) | 0.1 | SRS-010〜014, SRS-020〜032, SRS-O-*, SRS-P02〜P04, SRS-DATA-*, SRS-SEC-*, SRS-RCM-*, SRS-IF-002/003, SRS-UX-001/002/004/005, SRS-004/005 |
| [2] | ソフトウェアアーキテクチャ設計書(SAD) | 0.1 | SAD §3(階層構造)、§6(リスクコントロール)、§9(SEP-001 分離) |
| [3] | ソフトウェア詳細設計書(SDD) | 0.2 | SDD §3.1(ユニット一覧)、§4.1〜4.17(各ユニット仕様)|
| [4] | ユニットテスト計画書/報告書(UTPR) | 0.19 | UTPR §7.3.1〜§7.3.17(全 17 ユニットの試験詳細)、§9.2(試験結果)、§11(トレーサビリティ)|
| [5] | リスクマネジメントファイル(RMF / ISO 14971) | 0.2 | RCM-001 / RCM-003 / RCM-004 / RCM-015 / RCM-016 / RCM-019 |
| [6] | ソフトウェア構成管理計画書(SCMP) | 0.3 | §4.1(変更区分)、§5(ベースライン)|
| [7] | 構成アイテム一覧(CIL) | 0.27(本 Step 19 D-2 で更新) | §3 ソースコード、§4 ドキュメント、§5 SOUP、§8 試験資産 |
| [8] | ソフトウェア問題解決手順書(SPRP) | 0.2 | §5(問題報告 PRB-NNNN)|
| [9] | DEVELOPMENT_STEPS.md | 0.29(本 Step 19 D-2 で更新) | Step 19 D-2 採用根拠 |

---

# 第 I 部 計画

## 3. ソフトウェアユニットの結合(箇条 5.6.1)

### 3.1 結合戦略

**採用戦略:ボトムアップ + サンドイッチ要素**

**採用理由:**

1. **UT 完了済 17 ユニットを下層から積み上げ可能(ボトムアップ性):** UTPR v0.19 で全 17 ユニットの単独動作が UT レベルで検証済(stmt/branch 100%、MC/DC 100% on RCM 実装ユニット)。UT で確立した API 境界を起点として、永続化 → 制御系コア → 仮想 HW → API 層の順に層を積み上げる戦略が、検証済 UT を最大限再利用できる。
2. **API 層が制御系コア + 整合性検証層を集約(サンドイッチ性):** UNIT-005.1 Control API は Command Handler / Flow Validator / Resume Confirmation Gate / Validation API を集約。最上層 API のテストは委譲先全層を一斉に駆動するため、サンドイッチ統合に近い結合特性を持つ。
3. **ビッグバン戦略を回避する根拠:** 17 ユニット同時結合の試験は失敗時の原因特定が困難。SDD §3.1 の階層構造に従って段階的に結合し、各段階で IF-U(内部インタフェース)動作を確認する。

### 3.2 結合ステップ

| ステップ | 結合対象ユニット | 前提 | 使用スタブ・ドライバ | 検証観点 |
|---------|---------------|------|------------------|---------|
| **IS-1** | **永続化パイプライン**:UNIT-003.1 Serializer + UNIT-003.2 Checksum Verifier + UNIT-003.3 Atomic File Writer + UNIT-004.1 Integrity Validator + 共通データモデル `records.py` | UT 全 5 ユニット完了 | `tmpfile` / `tempfile.TemporaryDirectory` / 破損注入 fixture | E2E ラウンドトリップ(write→read→verify→validate)、原子性、電源断耐性、改ざん検知 |
| **IS-2** | **制御系コア**:UNIT-001.1 State Machine + UNIT-001.2 Control Loop + UNIT-001.3 Command Handler + UNIT-001.4 Flow Validator + UNIT-001.5 SW Watchdog | UT 全 5 ユニット完了 | `_FakeClock`、`Mock(spec=PumpController)` | 状態遷移整合性(RCM-019)、指令範囲(RCM-001)、SW Watchdog(RCM-003)、コマンド経路 |
| **IS-3** | **仮想ハードウェア層**:UNIT-002.1 Pump Simulator + UNIT-002.2 Pump Observer + UNIT-002.3 Event Injection Stub + UNIT-002.4 HW Failsafe Timer | UT 全 4 ユニット完了 | `_FakeClock`、`Barrier` 同期 | SRS-P01 過渡応答、観測契約、HW Watchdog(RCM-004 HW 側)、Inc.1 no-op 契約 |
| **IS-4** | **API 層**:UNIT-005.1 Control API + UNIT-005.2 State Observer API + UNIT-005.3 Validation API クラス B | UT 全 3 ユニット完了 | UNIT-005.3 を本物として注入(Mock 不要) | 全コマンド経路、観測経路、SEP-001 import グラフ(クラス B が C を import しない) |
| **IS-5** | **全層統合(E2E)**:IS-1 + IS-2 + IS-3 + IS-4 を全結合 | IS-1〜IS-4 完了 | 全実装ユニット(SOUP のみ外部) | RCM 6 件全結合検証、SEP-001 ランタイム検証、SRS-P02 / P03 / P04 統計時間試験、外乱(電源断・サイドチャネル)耐性 |

### 3.3 SDD §3.1 ユニットマップとの対応

下記対応により SDD で定義された 17 ユニット全件が 5 ステップに割り当てられている(網羅性)。

| パッケージ | UNIT-ID | 結合ステップ |
|-----------|--------|-----------|
| `src/vip_ctrl/` | 001.1 / 001.2 / 001.3 / 001.4 / 001.5 | IS-2 |
| `src/vip_sim/` | 002.1 / 002.2 / 002.3 / 002.4 | IS-3 |
| `src/vip_persist/` | 003.1 / 003.2 / 003.3 + records.py | IS-1 |
| `src/vip_integrity/` | 004.1 / 004.2 | IS-1(004.1)+ IS-2 / IS-4(004.2)|
| `src/vip_api/` | 005.1 / 005.2 | IS-4 |
| `src/vip_api_b/` | 005.3 | IS-4 |

> **注:** UNIT-004.2 Resume Confirmation Gate は永続化(IS-1)・制御系コア(IS-2)・API 層(IS-4)に跨る。RCM-016(再開ガード)結合観点として **IS-4 完了時** に統合検証する(§6.5 RCM-016 結合)。

## 4. ソフトウェア結合の検証(箇条 5.6.2)

### 4.1 構造的検証

結合されたソフトウェアが SAD §3(階層構造)・§9(SEP-001 分離)で定義した構造どおりに組み上がっていることを **レビュー + 静的解析(AST)** で検証する。

**チェックリスト(各結合ステップ完了時):**

- [ ] ユニット間インタフェース(IF-U-NNN、§4.3 一覧)の接続が SDD §3.2 の依存図どおりである
- [ ] 外部インタフェース(IF-E-NNN、§4.3 一覧)の接続が SAD §3.4 と整合している
- [ ] 構成管理下にある正しいバージョンのユニットが結合されている(CIL §3 の SHA で照合)
- [ ] SEP-001 分離が AST import グラフで保たれている(`src/vip_api_b/` が `vip_ctrl / vip_sim / vip_integrity / vip_api` を import していない、UT-005.3-13 と同手法を IS-4 / IS-5 で再実行)

### 4.2 検証記録テーブル

第 II 部(§11.1)で記入。v0.1 時点では骨格のみ。

| 結合ステップ | 検証日 | 検証者 | 結果 | 記録 ID |
|------------|-------|-------|------|---------|
| IS-1 | TBD | TBD | TBD | TBD |
| IS-2 | TBD | TBD | TBD | TBD |
| IS-3 | TBD | TBD | TBD | TBD |
| IS-4 | TBD | TBD | TBD | TBD |
| IS-5 | TBD | TBD | TBD | TBD |

### 4.3 ユニット間 IF-U / 外部 IF-E 一覧(Inc.1 範囲)

> **本一覧は SDD §3.2 / SAD §3.4 と一対一に対応する。** Inc.1 範囲では IF-E は CLI 起動 / `pytest` ハーネス経由のみで、UI / ネットワーク IF は Inc.2 以降。

**IF-U(内部、結合試験対象):**

| IF ID | 起点ユニット | 終点ユニット | 種類 | 関連 SRS |
|-------|------------|------------|------|---------|
| IF-U-001 | Control API(005.1)| Command Handler(001.3)| `enqueue` / `await_completion` | SRS-IF-002, SRS-010〜014 |
| IF-U-002 | Command Handler(001.3)| State Machine(001.1)| `request_transition(TransitionEvent)` | SRS-020/021/025 |
| IF-U-003 | Control Loop(001.2)| Pump Simulator(002.1)| `set_target_flow` / observation getters | SRS-031, SRS-P02 |
| IF-U-004 | Control Loop(001.2)| SW Watchdog(001.5)| `heartbeat()` | SRS-RCM-003 |
| IF-U-005 | Control Loop(001.2)| HW Failsafe Timer(002.4)| `heartbeat()` | SRS-RCM-004 |
| IF-U-006 | SW Watchdog(001.5)| State Machine(001.1)| `on_watchdog_timeout(WatchdogReason.SW_WATCHDOG)` | SRS-RCM-003 |
| IF-U-007 | HW Failsafe Timer(002.4)| Pump Simulator(002.1)| `force_stop_failsafe(reason="HEARTBEAT_TIMEOUT")` | SRS-RCM-004 |
| IF-U-008 | State Machine(001.1)| Persistence Pipeline(IS-1)| `drain_persistence_queue()` | SRS-DATA-002 |
| IF-U-009 | Persistence(003.1〜003.3)| Integrity Validator(004.1)| `TrustedRecord.from_raw(raw)` | SRS-026/027 |
| IF-U-010 | Resume Gate(004.2)| State Machine(001.1)| `request_transition(CMD_RESUME, meta={"resume_token": ...})` | SRS-028, SRS-RCM-016 |
| IF-U-011 | Control API(005.1)| Validation API(005.3)| `validate_settings(Settings) -> ValidationResult`(structural typing 経由)| SRS-UX-001/004/005 |
| IF-U-012 | State Observer API(005.2)| Pump Observer / State Machine / Resume Gate | 3 注入での `observe_state` 集約 | SRS-IF-003, SRS-O-010, SRS-UX-002 |
| IF-U-013 | Flow Validator(001.4)| Settings / Control Context | `validate(command, context)` | SRS-O-001, SRS-RCM-001 |
| IF-U-014 | Pump Observer(002.2)| Pump Simulator(002.1) | `_lock` 借用 + private フィールド読取(SDD §4.10.C)| SRS-031, SRS-I-020 |

**IF-E(外部、Inc.1 範囲):**

| IF ID | 起点 | 終点 | 種類 | 備考 |
|-------|------|------|------|------|
| IF-E-001 | OS ファイルシステム | Atomic Writer(003.3)| `write` / `read` / `os.replace` / `os.fsync` | SRS-DATA-002/003 |
| IF-E-002 | Python ロギング | 全ユニット | `logging.Logger` 標準出力 | Inc.1 では stdout のみ、Inc.4 でファイル出力追加 |
| IF-E-003 | Python `time.monotonic` / `time.time` | Watchdog 系 + Resume Gate + Pump Simulator | クロック注入(DI)| `_FakeClock` で UT は決定論化、IT では実時間検証あり |

## 5. ソフトウェア結合試験(箇条 5.6.3)

### 5.1 試験方針

1. **UT で検証不能な観点のみを IT で扱う**(Step 19 B4 / B5 / B8 / B10 / B13 教訓「非決定論的試験は IT へ」継続適用):
   - 実時間スレッド統計挙動(SRS-P02 / P03 / P04)
   - 環境依存(subprocess + SIGKILL 電源断)
   - サイドチャネル(Checksum タイミング攻撃耐性、SDD §4.13.F)
   - SEP-001 ランタイム分離(クラス B が import 経由でクラス C 副作用を観測しないこと)
   - 複数ユニット結合 E2E(永続化パイプライン / 観測経路 / Resume Gate API 経路)
2. **UT で 100% カバレッジ達成済の論理は重複試験しない:** 各ユニット内部分岐は UT が網羅済。IT は **ユニット境界での契約整合**(IF-U 動作)と **複数ユニット結合時の創発挙動** に焦点。
3. **試験 ID 体系:** `IT-{結合観点番号}.{サブ番号}-{ケース連番 2 桁}`。例:`IT-RCM015.1-01`(RCM-015 永続化 E2E カテゴリ §6.4.1 のケース 1)、`IT-SEP.1-01`(SEP-001 ランタイム検証カテゴリ §6.7 のケース 1)。
4. **トレーサビリティ:** 各 IT-ID は SRS / RCM / HZ / 元 UT-ID(該当する場合)に紐づける(§13)。

### 5.2 試験 ID 体系の詳細

| プレフィックス | 対象結合観点 | 元 UT 申し送り |
|------------|-----------|------------|
| IT-RCM001 | RCM-001 結合(指令範囲、Validator + Control API + Validation API)| — |
| IT-RCM003 | RCM-003 結合(SW Watchdog + 階層防御 SW<HW)| — |
| IT-RCM004 | RCM-004 結合(送出間隔、Control Loop + Pump + HW Failsafe)| UT-001.2-19、UT-002.4(タイマ精度) |
| IT-RCM015 | RCM-015 結合(永続化 E2E + 整合性検証)| UT-003.3-10(SIGKILL 電源断、§5.6 §6.9 へ移管)|
| IT-RCM016 | RCM-016 結合(再開ガード、Resume Gate + State Machine + Control API)| — |
| IT-RCM019 | RCM-019 結合(状態遷移整合性、State Machine + Command Handler + Control API)| UT-001.3-19(SRS-P03/P04 統計、§6.8 へ移管)|
| IT-SEP | SEP-001 ランタイム分離 | UT-005.3-13(AST 静的検証 → ランタイム拡張)|
| IT-PERF | SRS-P02 制御周期 / SRS-P03 / SRS-P04 統計時間 | UT-001.2、UT-001.3、UT-002.4(統計時間)|
| IT-PWR | 電源断耐性(subprocess + SIGKILL)| UT-003.3-10 |
| IT-SIDE | サイドチャネル(Checksum タイミング攻撃)| UT-003.2(SDD §4.13.F)|

### 5.3 試験環境

| 区分 | 内容 | バージョン / 設定 |
|------|------|-----------------|
| OS | Ubuntu Linux(CI)+ macOS(ローカル開発)| Ubuntu 22.04 LTS / macOS 14+ |
| Python | 公式 cpython | 3.12.x |
| 試験フレームワーク | pytest + pytest-cov + pytest-timeout + hypothesis | UTPR §5 SOUP 一覧と同(CI-SOUP-001〜011)|
| 並行制御 | `threading.Barrier` / `threading.Event` / `_FakeClock` | UT で確立済の test util 継続使用 |
| 電源断シミュレーション | `subprocess.Popen` + `os.kill(pid, signal.SIGKILL)` | IT-PWR 専用、CI Linux runner では `signal.SIGKILL` 利用可、CI macOS / Windows は IT-PWR 対象外 |
| 統計試験 | `pytest-benchmark`(Inc.1 では SOUP 候補、Step 19 F で正式 SOUP 採用判断)| `--benchmark-only` モードで分離実行 |
| AST 解析 | `ast` 標準ライブラリ | UT-005.3-13 と同手法を IS-5 全層に拡張 |

### 5.4 受入基準

1. **§3.2 の全結合ステップ(IS-1 〜 IS-5)が §4.1 構造的検証チェックリスト 4 項目を満たす。**
2. **§6 の試験ケース全件が Pass、または逸脱が SPRP §5 で正当化されている。**
3. **トレーサビリティマトリクス(§13)で SDD 17 ユニット × IF-U 14 件 × RCM 6 件 × 申し送り元 UT-ID の双方向リンクが確立している。**
4. **クラス C 追加要求(箇条 5.6.x、特に 5.6.4 g)で求められる「予想される運用条件下での挙動」「資源使用量」が試験ケースで確認されている。**
5. **回帰試験基盤(§8)が CI で動作し、Step 19 F 以降の実装変更で `pytest -m integration` が自動実行される。**

### 5.5 SOUP / 試験データ

| カテゴリ | アイテム | CI ID | 備考 |
|---------|---------|------|------|
| 既存 SOUP(UT 流用) | pytest / pytest-cov / pytest-timeout / hypothesis | CI-SOUP-002〜005 | UTPR v0.1 で正式登録済 |
| 新規 SOUP 候補 | pytest-benchmark | CI-SOUP-012(候補) | IT-PERF 統計試験用、Step 19 F で正式採用判断 |
| 試験データ | `tests/integration/` 配下を新設 | CI-TD-002a 〜 002j(予定) | UT の `tests/unit/` と同階層に作成、Step 19 F で正式登録 |

### 5.6 UT からの申し送り集約と分散配置(§6 への配置案)

UT 完了時に各 UNIT で申し送られた試験種別を、性質ごとに §6 の以下サブカテゴリに分散配置する(Step 19 D 採用根拠 Q2 「分散配置」採用)。

| 申し送り元 UT | 申し送り内容 | 配置先 | 種別 |
|------------|-----------|-------|------|
| UT-003.3-10 | subprocess + SIGKILL 電源断試験 | §6.9 IT-PWR | 環境依存 |
| UT-001.2(SRS-P02)| ±10% 実時間周期精度 + CPU 占有率 | §6.8 IT-PERF | 統計時間 |
| UT-001.3(SRS-P03/P04)| コマンド応答 P95 統計 | §6.8 IT-PERF | 統計時間 |
| UT-002.4(参考)| タイマ精度の長時間連続観察 | §6.8 IT-PERF | 統計時間 |
| UT-003.2(SDD §4.13.F)| Checksum タイミング攻撃耐性 | §6.10 IT-SIDE | サイドチャネル |
| UT-005.3-13(拡張)| SEP-001 ランタイム分離 | §6.7 IT-SEP | アーキテクチャ検証 |

> **設計判断:** 6 件を 1 カテゴリに集約せず、(電源断 / 統計時間 / サイドチャネル / アーキテクチャ検証)の 4 サブカテゴリに分散することで、レビュー視点と後続実装の責任分離が明確化する(Step 19 D 採用根拠 Q2)。

## 6. 結合試験の内容(箇条 5.6.4)

> **本節は v0.1 時点で「代表 3 観点詳細化 + 残 7 観点骨格」の段階成熟方式を採る(UTPR v0.1 採用根拠 L804「代表 5 + 骨格 12」と同パターン)。** 詳細化対象は **§6.4 RCM-015 永続化 E2E**、**§6.6 RCM-019 状態遷移結合**、**§6.5 RCM-016 再開ガード**(Inc.1 で SAD 全層を駆動する代表観点 3 つ)。残 7 観点(§6.1 / §6.2 / §6.3 / §6.7 / §6.8 / §6.9 / §6.10)は試験観点・ケース数目安・関連 IF-U / SRS / RCM のみを記述する骨格。Step 19 F(ITPR 完了)で残骨格を詳細化する。

### 6.1 RCM-001 結合(指令範囲チェック、Validator + Control API + Validation API クラス B)— **骨格**

- **目的:** RCM-001(指令範囲チェック、HZ-001/002 過量投与・流量異常)が **API 層 → Validation API クラス B(SEP-001 越え)→ Flow Validator(クラス C)** の経路で結合状態でも維持されることを検証する。
- **関連 IF-U:** IF-U-001 / IF-U-011 / IF-U-013
- **関連 SRS:** SRS-O-001、SRS-RCM-001、SRS-UX-001/004/005、SRS-005
- **関連 HZ:** HZ-001、HZ-002
- **関連 RCM:** RCM-001
- **元 UT:** UT-001.4-01〜12(34 ケース)、UT-005.1-01〜20(21 ケース)、UT-005.3-01〜13(16 ケース)
- **試験ケース数目安:** ≥ 8 件(SEP-001 越え経路、Validation API クラス B → Control API クラス C 経路、範囲外指令の 3 段階拒否、`drug_name` Inc.1 削除契約)
- **MC/DC 目標:** UT 側で 100% 達成済のため IT は契約検証中心(MC/DC 据置「—」)
- **Step 19 F で詳細化予定**

### 6.2 RCM-003 結合(SW Watchdog + 階層防御 SW<HW)— **骨格**

- **目的:** RCM-003(SW Watchdog 300 ms)と RCM-004(HW Watchdog 500 ms)の **階層防御時間順序** が結合状態でも維持され、SW Watchdog 発火後に HW Watchdog が発火しないこと(SW 優先 → State Machine ERROR 遷移 → Pump 停止)を検証する。
- **関連 IF-U:** IF-U-004 / IF-U-005 / IF-U-006 / IF-U-007
- **関連 SRS:** SRS-RCM-003、SRS-RCM-004
- **関連 HZ:** HZ-001、HZ-002
- **関連 RCM:** RCM-003、RCM-004(階層防御の SW 側)
- **元 UT:** UT-001.5-12(SW 301 ms Trip → HW 501 ms Trip、fake_clock で UT 完結)、UT-002.4-01〜08(18 ケース)
- **試験ケース数目安:** ≥ 6 件(実時間スレッド連動、UT は fake_clock のみ → IT は実時間 `time.monotonic` 連動で同シナリオを再実行)
- **MC/DC 目標:** UT で達成済、IT は実時間連動契約検証
- **Step 19 F で詳細化予定**

### 6.3 RCM-004 結合(送出間隔、Control Loop + Pump Simulator + HW Failsafe Timer)— **骨格**

- **目的:** RCM-004(送出間隔 200 ms ± 10%、SRS-P02)が結合状態で維持され、Control Loop の周期性 + Pump への heartbeat 送出 + HW Failsafe Timer の監視 が時間整合していることを検証する。
- **関連 IF-U:** IF-U-003 / IF-U-005 / IF-U-007
- **関連 SRS:** SRS-031、SRS-P02、SRS-RCM-004
- **関連 HZ:** HZ-001、HZ-002
- **関連 RCM:** RCM-004(送出 SW 側 + HW 側)
- **元 UT:** UT-001.2-01〜19(21 ケース)、UT-002.1-01〜21(21 ケース)、UT-002.4-01〜08(18 ケース)
- **試験ケース数目安:** ≥ 5 件(SRS-P02 統計時間試験は §6.8 IT-PERF に分散配置、本節は機能整合性のみ)
- **Step 19 F で詳細化予定**

### 6.4 RCM-015 結合(永続化 E2E + 整合性検証)— **詳細化(代表 1)**

#### 6.4.1 試験目的

RCM-015(永続化整合性、HZ-007 改ざん・破損)が **永続化パイプライン全体(Serializer → Atomic Writer → Checksum Verifier → Integrity Validator → records.py 共通モデル)** の E2E で機能すること、および UT で扱えなかった環境依存外乱(電源断・破損注入)に対して期待挙動を示すことを検証する。

#### 6.4.2 結合パイプライン

```
[書込側]  RuntimeState/Settings → build_persisted_record(Serializer §4.12)
            → compute_payload_checksum(Checksum §4.13)
            → to_json(Serializer §4.12.C、Decimal/State/bytes 3 種タグ)
            → write(Atomic Writer §4.4、tempfile→os.replace、bak 1 世代)
            → ファイルシステム永続化

[読込側]  ファイル → read(Atomic Writer §4.4) → from_json(Serializer §4.12)
            → verify(Checksum §4.13、hmac.compare_digest 定数時間)
            → validate(Integrity Validator §4.5、9 検証項目)
            → TrustedRecord(成功)/ FailsafeRecommended(失敗)
```

#### 6.4.3 試験ケース(詳細)

| 試験 ID | 観点 | 入力・操作 | 期待結果 | 関連 IF-U | 関連 UT |
|--------|------|-----------|---------|----------|--------|
| IT-RCM015.1-01 | E2E ラウンドトリップ正常系 | 1) 任意 RuntimeState/Settings(SRS-004 整合)を `tmp_path / "record.json"` へ write、2) 同 path から read → verify → validate、3) `TrustedRecord` を取得 | (1)〜(3) 成功、`TrustedRecord` の値が入力 RuntimeState/Settings と field 等価 | IF-U-009、IF-E-001 | UT-003.1-01〜17(26)、UT-004.1-01〜12(33)|
| IT-RCM015.1-02 | hypothesis E2E ラウンドトリップ | `_consistent_valid_settings` strategy(UT-004.1-11 流用)で 200 サンプルの Settings + RuntimeState を生成し write→read→verify→validate ループ | 全サンプルで `TrustedRecord` 取得、入力との field 等価 | IF-U-009、IF-E-001 | UT-003.1-12 / UT-004.1-11(hypothesis)|
| IT-RCM015.1-03 | bak 世代を用いた読込フェイルオーバ | 1) write A、2) write B(A は bak へ世代化)、3) `record.json` を破損(1 byte 反転)、4) read で `record.json.bak` から正常読込 | bak 世代から B 直前の A が読み込め、verify+validate Pass | IF-U-009、IF-E-001 | UT-003.3-02b(bak 置換)|
| IT-RCM015.1-04 | Checksum 不一致による拒否 | 1) write、2) `record.json` の payload 部 1 byte 反転、3) read → verify | `verify` が False を返し、Integrity Validator は `FailsafeRecommended([ChecksumMismatch])` を返す | IF-U-009 | UT-003.2-04(改ざん検出)、UT-004.1-01 |
| IT-RCM015.1-05 | スキーマバージョン不整合 | 1) `current_schema_version()` 以外の値で persisted record を生成、2) read → validate | `FailsafeRecommended([SchemaVersionUnsupported])` を返す | IF-U-009 | UT-003.1-15(schema)、UT-004.1-03 |
| IT-RCM015.1-06 | hypothesis 1 bit 反転耐性 | hypothesis で 200 サンプルの正常 record に対し、payload 部 1 bit 反転を全て注入 | 全反転で `verify` False または validate `FailsafeRecommended`、TrustedRecord に昇格させない | IF-U-009 | UT-004.1-12(hypothesis 破損注入)|
| IT-RCM015.1-07 | 並行 read 安全性 | 10 スレッドで同一 `record.json` を read → verify → validate | 全スレッドで成功、結果が一致(read は readonly のため lock 不要を確認)| IF-U-009 | UT-003.3 並行(IT で実時間化)|
| IT-RCM015.1-08 | UNIT-004.2 Resume Gate との結合 | 1) Pause 状態を永続化、2) 再起動シミュレーション(プロセス再生成)、3) read → validate → Resume Gate に渡す → `set_pending(token)` | `set_pending` が成功、token 32 hex を返す | IF-U-009、IF-U-010 | UT-004.2-01〜15、Resume Gate API 経路 |

#### 6.4.4 申し送り(本観点と関連カテゴリ)

- **subprocess + SIGKILL 電源断試験は §6.9 IT-PWR へ分散配置**(SDD §4.4.E「原理的に検知不可能 / load 側で担保」+ Step 19 B5 教訓「環境依存試験は IT へ」)。本 §6.4 では電源断の論理的等価試験(read 経路で破損ファイルを与える IT-RCM015.1-04 / 06)で代替する。
- **Checksum タイミング攻撃耐性は §6.10 IT-SIDE へ分散配置**(SDD §4.13.F「タイミング試験(参考)」、Step 19 B8 教訓)。本 §6.4 では `hmac.compare_digest` の機能正常性のみ検証(IT-RCM015.1-04)。

### 6.5 RCM-016 結合(再開ガード、Resume Gate + State Machine + Control API)— **詳細化(代表 2)**

#### 6.5.1 試験目的

RCM-016(再開時の確認ガード、HZ-007 不適切な再開)が、**Resume Confirmation Gate(004.2)→ State Machine(001.1)→ Control API(005.1)** の経路で結合状態でも機能することを検証する。

#### 6.5.2 結合経路

```
[Pause 経路]  ControlApi.pause() → CommandHandler → StateMachine(RUNNING→PAUSED) → ResumeGate.set_pending(token)
[Resume 経路] ControlApi.confirm_resume(token) → ResumeGate.confirm(token)
              → 成功時 StateMachine.request_transition(CMD_RESUME, meta={"resume_token": token})
              → 失敗時 ApiResult として WrongToken / Expired / NotPending を返す
[期限切れ]    時間経過 60 分超 → ResumeGate.check_expiry() → pending 解除 + 警告ログ
```

#### 6.5.3 試験ケース(詳細)

| 試験 ID | 観点 | 入力・操作 | 期待結果 | 関連 IF-U | 関連 UT |
|--------|------|-----------|---------|----------|--------|
| IT-RCM016.1-01 | 正常 Resume 経路 | 1) `ControlApi.pause()`、2) `ControlApi.confirm_resume(token)` | StateMachine が PAUSED→RUNNING、ApiResult.Ok | IF-U-001/002/010 | UT-004.2-01〜04、UT-005.1-09 |
| IT-RCM016.1-02 | 不正 token 拒否 | 1) `pause()`、2) `confirm_resume("bad")` | ApiResult.WrongToken、StateMachine PAUSED 維持 | IF-U-010 | UT-004.2-04、UT-005.1-10 |
| IT-RCM016.1-03 | 期限切れ拒否 | 1) `pause()`、2) `_FakeClock.advance(EXPIRY_SEC+1)`、3) `confirm_resume(token)` | ApiResult.Expired、warning ログ | IF-U-010 | UT-004.2-07、UT-005.1-11 |
| IT-RCM016.1-04 | NotPending(重複 confirm)| 1) `pause()` → `confirm_resume(token)`(成功)、2) 再度 `confirm_resume(token)` | ApiResult.NotPending | IF-U-010 | UT-004.2-08、UT-005.1-12 |
| IT-RCM016.1-05 | 並行 confirm の排他性 | 2 スレッドで同 token を `Barrier` 同期 confirm | 1 つだけ Confirmed、もう 1 つは NotPending | IF-U-010 | UT-004.2-15(UT で確立済 → IT で API 層経由を確認)|
| IT-RCM016.1-06 | StateMachine 不変(WrongToken)| WrongToken 時に StateMachine.request_transition が呼ばれないこと | `Mock(spec=StateMachine).request_transition.assert_not_called()` | IF-U-010 | UT-004.2-04 |
| IT-RCM016.1-07 | token 一意性(1000 cycle)| 1000 回 pause→confirm を繰り返し token 値を収集 | 全 token 値が一意(128 bit エントロピー実証)| IF-U-010 | UT-004.2-09(UT で確立)|
| IT-RCM016.1-08 | API 層 SEP-001 越え(なし)| `ControlApi` 経由の Resume が `ValidationApi` クラス B を介さないこと(本観点はクラス C のみで完結)| `ast.parse` で `vip_api/control_api.py` の `confirm_resume` 経路に `vip_api_b` import がないことを確認 | — | UT-005.3-13(SEP-001 静的検証)|

#### 6.5.4 申し送り

- **`pending_set_at_wall` accessor の Inc.4 拡張**(B17 で発見、UTPR §9.4 残異常):本 IT v0.1 時点では `StateObserverApi.observe_state().resume_set_at` は Inc.1 None 固定のまま、Inc.4 UI 着手時に Resume Gate API 拡張で透過予定。

### 6.6 RCM-019 結合(状態遷移整合性、State Machine + Command Handler + Control API)— **詳細化(代表 3)**

#### 6.6.1 試験目的

RCM-019(状態遷移整合性、HZ-001/002 不正状態遷移による誤動作)が、**Control API(005.1)→ Command Handler(001.3)→ State Machine(001.1)** の主要コマンド経路で結合状態でも機能し、TRANSITION_TABLE 13 エントリに登録されていない (state, event) 組合せが全て拒否されることを検証する。

#### 6.6.2 結合経路と参照テーブル

- **TRANSITION_TABLE(SDD §4.1.B、UNIT-001.1):** 13 登録エントリ × 状態 5 種(IDLE / RUNNING / PAUSED / STOPPED / ERROR)× イベント種別 8 種 = 40 通りのうち 13 が許可、27 が拒否(45 件と UT-001.1-05 で記述された数は EventKind 拡張で更新済、本 IT は最新版 13/40 を基準)。
- 本観点は **Control API → Command Handler → State Machine 経路 で 13 許可と 27 拒否を機械的に網羅** する(UT-001.1-04 / UT-001.1-05 が State Machine 単独で確立した網羅性を、API 層経由でも維持されるかを再確認する観点)。

#### 6.6.3 試験ケース(詳細)

| 試験 ID | 観点 | 入力・操作 | 期待結果 | 関連 IF-U | 関連 UT |
|--------|------|-----------|---------|----------|--------|
| IT-RCM019.1-01 | 13 登録経路 parametrize 網羅 | 13 登録エントリ全件を `pytest.parametrize` で展開、各経路で `ControlApi` 適切メソッドを呼出 | 全件 ApiResult.Ok、StateMachine の `current` 期待状態 | IF-U-001/002 | UT-001.1-04(13 登録)、UT-001.3-01〜23 |
| IT-RCM019.1-02 | 27 非登録経路拒否 | 27 非登録エントリ全件を parametrize 展開、各経路で `ControlApi` 適切メソッドを呼出 | 全件 ApiResult.ApiRejected(InvalidStateTransition)、StateMachine の `current` 不変 | IF-U-001/002 | UT-001.1-05(45/40 非登録)|
| IT-RCM019.1-03 | STOP ファストパス + 既存キュー破棄 | 1) `ControlApi.start()` を非同期で発行、2) 即座に `ControlApi.stop()` | start 結果が SupersededByStopError、State 最終 STOPPED | IF-U-001/002 | UT-001.3-05 |
| IT-RCM019.1-04 | ERROR 経路 + ERROR_RESET | 1) Watchdog タイムアウト → ERROR、2) `ControlApi.error_reset()` → IDLE | StateMachine が ERROR → IDLE、ResumeGate も `cancel()` 呼出される(整合性)| IF-U-001/002/006 | UT-001.1-08、UT-001.3-04 |
| IT-RCM019.1-05 | Watchdog 経路統合 | 1) RUNNING、2) Control Loop heartbeat 停止、3) SW Watchdog 300 ms 経過 → ERROR | StateMachine ERROR、`error_reason="SW_WATCHDOG"` | IF-U-004/006 | UT-001.5-12(階層防御、IT は実時間)|
| IT-RCM019.1-06 | 並行 start 一意性 | 10 スレッドで同時 `ControlApi.start(settings)`、token 衝突確認 | 1 token のみ Accepted、他は ApiResult.ApiRejected(AlreadyRunning)| IF-U-001 | UT-001.3-09(token 一意性)|
| IT-RCM019.1-07 | API 層例外耐性 | Command Handler の dispatch 内で人為的 RuntimeError を 1 回注入 | ApiResult.ApiRejected(InternalError.UNEXPECTED_EXCEPTION)、State Machine 不変、CommandHandler ループは継続 | IF-U-001/002 | UT-001.3-12(`patch.object`)、UT-005.1-15〜17(例外注入)|
| IT-RCM019.1-08 | 状態遷移ログ記録 | 全 13 登録経路実行後、`logging` で記録された遷移行が 13 行(または期待数)| `caplog` で行数と内容検証 | IF-E-002 | UT-001.1-09(ログ)|

#### 6.6.4 申し送り

- **SRS-P03 / SRS-P04 統計時間試験(P95 応答時間)は §6.8 IT-PERF へ分散配置**(Step 19 B13 教訓「非決定論的試験は IT へ」)。本 §6.6 では機能整合性のみ検証(タイミング契約は IT-PERF)。

### 6.7 SEP-001 ランタイム分離(アーキテクチャ検証)— **骨格**

- **目的:** SAD §9 SEP-001(クラス C ↔ クラス B 分離)が **AST 静的検証(UT-005.3-13 で確立済)に加えてランタイムでも維持** されること、すなわち、クラス B モジュール(`src/vip_api_b/`)実行時にクラス C 副作用(state mutation / I/O / threading)が観測されないことを検証する。
- **関連 IF-U:** —(クラス C / B 境界そのものを検証)
- **関連 SAD:** §9 SEP-001
- **関連 SRS:** SRS-UX-001/004/005、SRS-005
- **試験ケース数目安:** ≥ 4 件(AST import グラフ ランタイム拡張、`vip_api_b/validation_api.py` 実行中の `sys.modules` 監視、クラス C 副作用観測なし契約、純粋関数性プロパティ)
- **元 UT:** UT-005.3-13(`ast.parse` で import 機械検証)
- **Step 19 F で詳細化予定**

### 6.8 SRS-P02 / P03 / P04 統計時間試験(IT-PERF)— **骨格**

- **目的:** UT で決定論化により扱えない実時間挙動を、**実時間 + 統計**(P95 / 平均 / 標準偏差)で検証する。
- **対象:** SRS-P02(Control Loop 制御周期 200 ms ± 10%、CPU 占有率)、SRS-P03(コマンド受領 → State Machine 反映 P95 ≤ 50 ms)、SRS-P04(コマンド受領 → 完了応答 P95 ≤ 200 ms)
- **関連 IF-U:** IF-U-001 / IF-U-002 / IF-U-003 / IF-U-005
- **関連 SRS:** SRS-P02、SRS-P03、SRS-P04
- **試験ケース数目安:** ≥ 6 件(各 SRS 性能要求につき 1〜2 件 + 連続稼働中の劣化観察 1 件)
- **元 UT 申し送り:** UT-001.2-19(SRS-P02 周期精度)、UT-001.3-19(SRS-P03/P04 200 ms 機能スモーク)、UT-002.4(タイマ精度)
- **試験技法:** `pytest-benchmark`(SOUP 候補)+ `time.perf_counter` 実測、5 連続実行の中央値判定で flake 抑制
- **Step 19 F で詳細化予定**

### 6.9 環境依存試験 — subprocess + SIGKILL 電源断耐性(IT-PWR)— **骨格**

- **目的:** SDD §4.4.E「原理的に検知不可能 / load 側で担保」の前提で、永続化パイプラインの **真の電源断シミュレーション**(`subprocess.Popen` で書込中プロセスを生成 → `os.kill(pid, signal.SIGKILL)`)に対して、再起動後の read 経路で破損 / 中間状態が検出され `FailsafeRecommended` を返すことを検証する。
- **関連 IF-U:** IF-U-009、IF-E-001
- **関連 SRS:** SRS-DATA-002、SRS-DATA-003、SRS-RCM-015
- **試験ケース数目安:** ≥ 4 件(write 中 SIGKILL、bak 世代化中 SIGKILL、fsync 完了直前 SIGKILL、bak からのリカバリ)
- **元 UT 申し送り:** UT-003.3-10(SDD §4.4.E 申し送り)
- **環境制約:** Linux のみ(macOS は SIGKILL 動作差異、Windows は subprocess 動作差異)。CI Linux runner で実行、ローカル macOS 開発時はスキップマーク。
- **試験技法:** `pytest.mark.skipif(sys.platform != "linux")` + `subprocess.Popen` + `os.kill`、`tmp_path` で隔離
- **Step 19 F で詳細化予定**

### 6.10 サイドチャネル — Checksum タイミング攻撃耐性(IT-SIDE)— **骨格**

- **目的:** SDD §4.13.F「タイミング試験(参考)」の参考要求に対し、**`hmac.compare_digest` 定数時間比較が結合状態でも維持されている** ことを **統計的に検証** する(差分タイミングが標準偏差内に収まる)。
- **関連 IF-U:** —(`compute_payload_checksum` / `verify_payload_checksum` 内部実装契約)
- **関連 SRS:** SRS-SEC-001(本要求は Inc.5 セキュリティ拡張時に正式化、Inc.1 は参考扱い)
- **試験ケース数目安:** ≥ 2 件(全長一致 vs 1 byte 不一致 / 末尾不一致 vs 先頭不一致 の経過時間統計)
- **元 UT 申し送り:** UT-003.2(B8 教訓、SDD §4.13.F 末尾)
- **環境制約:** CI 共有環境では実時間ノイズが大きい(他 job との CPU 競合)。本観点は **「明らかに有意な差(例:10x 以上)が出ないこと」** という弱判定に留め、強判定(< 1σ)はローカル安定環境または専用 runner で実施(Inc.5 で再評価)。
- **Step 19 F で詳細化予定**

## 7. 結合試験手順の評価(箇条 5.6.5)

### 7.1 計画レビューチェックリスト

- [ ] 計画が SRS / SAD / SDD と整合している(§2 参照文書、§6 試験観点)
- [ ] 各試験ケースが期待結果・合格基準を明示している(§6.4 / §6.5 / §6.6 詳細化済 + §6.1〜§6.3 / §6.7〜§6.10 骨格)
- [ ] 試験が再現可能である(§5.3 試験環境、`pytest` ベース、CI 自動実行)
- [ ] リスクコントロール手段(RCM-001/003/004/015/016/019)を検証するケースが含まれている(§6.1〜§6.6)
- [ ] SEP-001 分離(クラス C / B)を検証するケースが含まれている(§6.7)
- [ ] UT で扱えない外乱・統計挙動が IT で扱われている(§6.8 / §6.9 / §6.10)

### 7.2 IF-U / IF-E 網羅性

- [ ] §4.3 の IF-U 14 件全てが §6 のいずれかの試験ケースで駆動される
- [ ] IF-E 3 件全てが §6 のいずれかの試験ケースで駆動される

> v0.1 時点では §6.4 / §6.5 / §6.6 詳細化分のみで IF-U-001 / 002 / 003 / 009 / 010 / 011 が駆動済。残 IF-U(004 / 005 / 006 / 007 / 008 / 012 / 013 / 014)は Step 19 F の §6.1〜§6.3 / §6.7 詳細化で網羅予定。

## 8. 回帰試験の実施(箇条 5.6.6)

### 8.1 自動化方針

- 結合試験は `tests/integration/` 配下に配置(UT は `tests/unit/`、本 PR ではディレクトリ作成のみで個別 IT ファイルは Step 19 F)
- `pytest -m integration` マーカー指定で UT と分離実行可能
- CI(`.github/workflows/unit-test.yml`)は **デフォルトで UT のみ実行**、`integration` マーカーは別 job で実行(Step 19 F で `.github/workflows/integration-test.yml` を新設)
- 統計時間試験(IT-PERF)/ 電源断試験(IT-PWR)/ サイドチャネル試験(IT-SIDE)は **Linux runner 限定 + nightly schedule** での実行(全 PR で実行すると CI 時間と非決定性ノイズが増大)

### 8.2 影響範囲解析ルール

- ソースコード変更時:変更ユニットの IF-U に紐づく IT ケースを再実行(§13 トレーサビリティから逆引き)
- IF-U / IF-E 仕様変更時:該当 IT カテゴリ全件を再実行
- SOUP バージョンアップ時:全 IT を再実行
- RCM 関連変更時:該当 RCM カテゴリ + RCM-019(状態遷移経路全般)を再実行

### 8.3 自動化状況

- **v0.2(Step 19 F0)時点:骨格整備済。** `tests/integration/{__init__.py, conftest.py, test_smoke.py}` 配置 + `pyproject.toml` に `integration` / `linux_only` / `nightly` / `perf` マーカー登録 + `addopts = ["-m", "not integration"]` で UT 実行時の自動排除 + `.github/workflows/integration-test.yml` 新設(`integration-fast` job:PR / push の `-m "integration and not nightly"` + `integration-nightly` job:cron `0 2 * * *` UTC で `-m integration` 全実行)+ `pytest-benchmark` を SOUP-012 として正式登録(IT-PERF §6.8 用)+ スモーク 2 件で CI 経路の動作確認済(`pytest -m "integration and not nightly"` で 2 collected / 441 deselected、UT 側は 441 passed / 2 deselected)。
- **v0.3 以降(Step 19 F1〜F7):** 各観点(§6.1〜§6.10 のうち骨格 7 件)の `tests/integration/test_X.py` を順次追加し、§11.2 試験ケース結果テーブルに実施結果を記入していく(B2〜B18 と同じ漸進パターン)。

## 9. 結合試験記録の内容(箇条 5.6.7)

各試験記録(§11.2)には以下を含める:

1. 試験 ID(`IT-{プレフィックス}.{サブ番号}-{ケース連番}`)と名称
2. 試験対象のソフトウェアバージョン・コミット SHA
3. 試験環境(OS / Python バージョン / SOUP バージョン / `pytest` 出力 ID)
4. 手順、入力、期待結果(§6 から引用)
5. 実行日、実施者、CI ジョブ Run ID(該当時)
6. 実結果・合否判定(Pass / Fail / Skip)
7. 逸脱時の処置(SPRP §5 への PRB-NNNN リンク)

## 10. ソフトウェア問題解決プロセスの使用(箇条 5.6.8)

- 試験で発見した問題は IEC 62304 箇条 9(SPRP-VIP-001)に従い `PRB-NNNN` を起票して記録・分析・是正する。
- 問題はリスクマネジメント(RMF v0.2)へ入力し、安全性への影響を評価する。重大度 Major 以上は CCB(CCB-VIP-001)で CR を起票する判断を取る。
- 是正措置を計画・実施し、修正後の回帰試験(§8)で再確認する。

---

# 第 II 部 報告

> **Inc.1 結合試験実施(Step 19 F 以降)時に本部を記入する。v0.1 時点では骨格のみ。**

## 11. 試験実施結果

### 11.1 実施サマリ

- 実施期間: *(Step 19 F 開始時に記入)*
- 実施者: k-abe
- ソフトウェアバージョン(コミット): *(各 IT Pass 時点の SHA)*
- 試験環境バージョン: Python 3.12.x、pytest / pytest-cov / hypothesis 最新安定、Linux runner(IT-PWR / IT-SIDE 限定)
- CI ジョブ: `.github/workflows/integration-test.yml` の Run ID(Step 19 F で新設予定)

### 11.2 試験ケース結果(骨格、カテゴリ単位で随時記入)

| カテゴリ | 試験 ID 総数 | Pass | Fail | Skip | 実施日 | コミット SHA |
|---------|----------|------|------|------|-------|-----------|
| IT-RCM015(永続化 E2E、§6.4)| **8**(目安、IT-RCM015.1-01〜08)| TBD | TBD | TBD | TBD | TBD |
| IT-RCM016(再開ガード、§6.5)| **8**(目安、IT-RCM016.1-01〜08)| TBD | TBD | TBD | TBD | TBD |
| IT-RCM019(状態遷移結合、§6.6)| **8**(目安、IT-RCM019.1-01〜08)| TBD | TBD | TBD | TBD | TBD |
| IT-RCM001(指令範囲、§6.1 骨格)| **≥ 8**(Step 19 F で詳細化)| TBD | TBD | TBD | TBD | TBD |
| IT-RCM003(SW/HW Watchdog、§6.2 骨格)| **≥ 6**(Step 19 F で詳細化)| TBD | TBD | TBD | TBD | TBD |
| IT-RCM004(送出間隔、§6.3 骨格)| **≥ 5**(Step 19 F で詳細化)| TBD | TBD | TBD | TBD | TBD |
| IT-SEP(SEP-001 ランタイム、§6.7 骨格)| **≥ 4**(Step 19 F で詳細化)| TBD | TBD | TBD | TBD | TBD |
| IT-PERF(統計時間、§6.8 骨格)| **≥ 6**(Step 19 F で詳細化)| TBD | TBD | TBD | TBD | TBD |
| IT-PWR(電源断、§6.9 骨格)| **≥ 4**(Step 19 F で詳細化)| TBD | TBD | TBD | TBD | TBD |
| IT-SIDE(サイドチャネル、§6.10 骨格)| **≥ 2**(Step 19 F で詳細化)| TBD | TBD | TBD | TBD | TBD |
| **合計** | **≥ 59** | — | — | — | — | — |

### 11.3 不具合・逸脱

| 問題 ID(PRB) | 発見 IT-ID | 内容 | 重大度 | 対応 | ステータス |
|----------------|----------|------|-------|------|----------|
| — | — | — | — | — | — |

### 11.4 回帰試験の結果

| 変更 ID(CR / PRB)| 影響を受けた IT | 結果 | 実施日 |
|-----------------|---------------|------|-------|
| — | — | — | — |

## 12. 結論

- [ ] 全結合ステップ(IS-1 〜 IS-5)が §4.1 構造的検証を満たしている
- [ ] §6 の試験ケース全件が Pass、または逸脱が SPRP §5 で正当化されている
- [ ] §13 トレーサビリティマトリクスで SDD 17 ユニット × IF-U 14 件 × RCM 6 件 × 申し送り元 UT-ID の双方向リンクが確立している
- [ ] 未解決問題は既知の残留異常として SMS-VIP-001(§5.8)に記載する

## 13. トレーサビリティマトリクス

> v0.1 時点では §6 詳細化分(RCM-015 / RCM-016 / RCM-019)の試験 ID と SRS / RCM / HZ / 元 UT-ID の対応を表形式で記録する。骨格カテゴリは Step 19 F で同マトリクスに追記する。

| 結合観点 | 試験 ID | 関連 SRS | 関連 RCM | 関連 HZ | 関連 IF-U | 関連 UT | 結果 |
|---------|--------|---------|---------|---------|----------|--------|------|
| RCM-015 永続化 E2E | IT-RCM015.1-01 〜 08(§6.4)| SRS-DATA-002/003、SRS-026/027、SRS-RCM-015、SRS-SEC-001 | RCM-015 | HZ-007 | IF-U-009、IF-E-001 | UT-003.1〜003.3、UT-004.1 | TBD |
| RCM-016 再開ガード | IT-RCM016.1-01 〜 08(§6.5)| SRS-028、SRS-RCM-016 | RCM-016 | HZ-007 | IF-U-001/002/010 | UT-004.2、UT-005.1 | TBD |
| RCM-019 状態遷移 | IT-RCM019.1-01 〜 08(§6.6)| SRS-010〜014、SRS-020/021/025、SRS-RCM-020、SRS-ALM-003 | RCM-019 | HZ-001、HZ-002 | IF-U-001/002/004/006、IF-E-002 | UT-001.1、UT-001.3、UT-005.1 | TBD |
| RCM-001 指令範囲 | IT-RCM001.* (§6.1 骨格)| SRS-O-001、SRS-RCM-001、SRS-UX-001/004/005、SRS-005 | RCM-001 | HZ-001、HZ-002 | IF-U-001/011/013 | UT-001.4、UT-005.1、UT-005.3 | TBD |
| RCM-003 SW Watchdog 階層 | IT-RCM003.* (§6.2 骨格)| SRS-RCM-003、SRS-RCM-004 | RCM-003、RCM-004 | HZ-001、HZ-002 | IF-U-004/005/006/007 | UT-001.5、UT-002.4 | TBD |
| RCM-004 送出間隔 | IT-RCM004.* (§6.3 骨格)| SRS-031、SRS-P02、SRS-RCM-004 | RCM-004 | HZ-001、HZ-002 | IF-U-003/005/007 | UT-001.2、UT-002.1、UT-002.4 | TBD |
| SEP-001 ランタイム | IT-SEP.* (§6.7 骨格)| SRS-UX-001/004/005、SRS-005 | — | — | — | UT-005.3 | TBD |
| 統計時間 | IT-PERF.* (§6.8 骨格)| SRS-P02、SRS-P03、SRS-P04 | — | — | IF-U-001/002/003/005 | UT-001.2、UT-001.3、UT-002.4 | TBD |
| 電源断耐性 | IT-PWR.* (§6.9 骨格)| SRS-DATA-002/003、SRS-RCM-015 | RCM-015 | HZ-007 | IF-U-009、IF-E-001 | UT-003.3 | TBD |
| サイドチャネル | IT-SIDE.* (§6.10 骨格)| SRS-SEC-001 | — | HZ-007 | — | UT-003.2 | TBD |

**カバレッジ:** 本マトリクスにより、Inc.1 全 RCM 6 件 / SDD 17 ユニットからの UT 申し送り 6 件 / SAD §9 SEP-001 が IT カテゴリと紐付き、SRS / RCM / HZ / IF-U への双方向トレーサビリティが確立した(v0.1 では §6.4 / §6.5 / §6.6 詳細化分が試験 ID レベル、残骨格は Step 19 F で完成)。

## 14. 改訂履歴

| バージョン | 日付 | 変更内容 | 変更者 |
|----------|------|---------|--------|
| 0.2 | 2026-05-01 | **Step 19 F0(自動化骨格整備)を反映。** §8.3 自動化状況を「未着手」→「骨格整備済」に更新(`tests/integration/{__init__.py, conftest.py, test_smoke.py}` + `pyproject.toml` markers / `addopts = ["-m", "not integration"]` + `pytest-benchmark` SOUP-012 採用 + `.github/workflows/integration-test.yml` の `integration-fast` / `integration-nightly` 2 ジョブ構成)。スモーク 2 件で CI 経路の動作確認済(UT 441 / IT 2 / coverage 100% / mypy `--strict` / ruff Pass)。Step 19 F1 以降の各観点詳細化の前提整備が完了 | k-abe |
| 0.1 | 2026-05-01 | **初版作成(計画、Step 19 D-2)。** Inc.1 全 17 ユニット UT 完了(UTPR v0.19)を前提に、結合戦略(IS-1 永続化 → IS-2 制御系コア → IS-3 仮想 HW → IS-4 API 層 → IS-5 全層統合)を確立。**RCM 軸での代表 3 観点詳細化**(§6.4 RCM-015 永続化 E2E 8 ケース / §6.5 RCM-016 再開ガード 8 ケース / §6.6 RCM-019 状態遷移結合 8 ケース、合計 24 詳細化ケース)+ **残 7 観点骨格**(§6.1 RCM-001 / §6.2 RCM-003 / §6.3 RCM-004 / §6.7 SEP ランタイム / §6.8 IT-PERF 統計時間 / §6.9 IT-PWR 電源断 / §6.10 IT-SIDE サイドチャネル、合計目安 ≥ 35 件)。**UT 申し送り 6 件を性質別に分散配置**(電源断 → §6.9、統計時間 → §6.8、サイドチャネル → §6.10、SEP ランタイム → §6.7、E2E ラウンドトリップ → §6.4、Resume API → §6.5)。試験 ID 体系(`IT-{プレフィックス}.{サブ番号}-{連番}`)、IF-U 14 件 + IF-E 3 件一覧、結合戦略チェックリスト、受入基準 5 項目、回帰試験基盤計画を確立。第 II 部(報告)は骨格のみ、Step 19 F の試験実施で埋めていく(UTPR v0.1 と同じ「代表 + 骨格」段階成熟方式) | k-abe |
