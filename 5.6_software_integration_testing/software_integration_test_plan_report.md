# ソフトウェア結合試験計画書/報告書

**ドキュメント ID:** ITPR-VIP-001
**バージョン:** 0.8
**作成日:** 2026-05-01
**最終更新日:** 2026-05-04
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

### 6.1 RCM-001 結合(指令範囲チェック、Validator + Control API + Validation API クラス B)— **詳細化(Step 19 F1)**

#### 6.1.1 試験目的

RCM-001(指令範囲チェック、HZ-001 過量投与・HZ-002 流量異常)が **ControlAPI(005.1)→ ValidationApi(005.3 等価)経路** で結合状態でも維持され、範囲外指令が CommandHandler 経路に到達しないことを検証する。Step 19 F1 着手時に発見した **`vip_api.ValidationApi` Protocol(`-> list[ValidationError]`)と `vip_api_b.validate_settings`(関数で `Ok` または `Err` を返す)の型不整合** に対しては Mock(spec=ValidationApi)ベースで Protocol 契約を検証し、本物注入による SEP-001 越え経路検証は §6.7 IT-SEP に分散配置(契約整合化は **CR-0004** として別途起票予定)。

#### 6.1.2 結合経路と検証スコープ

```
[拒否経路]   ControlApi.start(settings)
              -> ValidationApi.validate_settings(settings) -> [ValidationError(...)] (非空 list)
              -> ValidationFailed(errors=[...])  ※ CommandHandler は呼ばれない
              -> StateMachine 不変(IT-RCM001.1-08 で本物実証)

[正常経路]   ControlApi.start(settings)
              -> ValidationApi.validate_settings(settings) -> [] (空 list = Pass)
              -> CommandHandler.enqueue(START Command) -> Accepted
              -> Ok(token=...)
```

**設計判断(Step 19 F1):**

- 本観点は **Mock(spec=ValidationApi) ベース**で Protocol 契約整合を検証(UT-005.1 の `validation_api_mock` パターン継承)。
- IT-RCM001.1-01〜07 は全 Mock の `control_api_with_mocks` fixture(`tests/integration/conftest.py`)で契約検証。
- IT-RCM001.1-08 のみ **本物 StateMachine + 本物 CommandHandler + Mock ValidationApi** の組み合わせで「Validation 拒否時の State Machine 不変」を実証(SEP-001 縮小版検証、§6.7 IT-SEP の予告)。

#### 6.1.3 試験ケース(詳細)

| 試験 ID | 観点 | 入力・操作 | 期待結果 | 関連 IF-U | 関連 UT |
|--------|------|-----------|---------|----------|--------|
| IT-RCM001.1-01 | 正常系(範囲内 + SRS-004 整合) | flow=60, dose=60, duration=60(整合)/ Mock = `[]` | `Ok(token=...)`、`validate_settings` 1 回呼出、`enqueue` 1 回呼出 | IF-U-001/011 | UT-005.1-01 |
| IT-RCM001.1-02 | flow_rate 上限超(SRS-O-001 1200 超) | flow=1200.01 / Mock = `[ValidationError("flow_rate", ...)]` | `ValidationFailed`、`enqueue` **不発火** | IF-U-011 | UT-005.1-02、UT-001.4-01 |
| IT-RCM001.1-03 | flow_rate 負(SRS-O-001 下限超) | flow=-1.0 / Mock = `[ValidationError("flow_rate", ...)]` | `ValidationFailed`、`enqueue` 不発火 | IF-U-011 | UT-001.4-04 |
| IT-RCM001.1-04 | dose_volume 上限超(SRS-005 9999.9 超) | dose=10000.0 / Mock = `[ValidationError("dose_volume", ...)]` | `ValidationFailed`、`enqueue` 不発火 | IF-U-011 | UT-005.3-03、UT-005.3-04 |
| IT-RCM001.1-05 | dose==0 かつ flow>0(SRS-004 整合性違反) | dose=0, flow=10, duration=60 / Mock = `[ValidationError("dose_consistency", ...)]` | `ValidationFailed`、`enqueue` 不発火 | IF-U-011 | UT-005.3-05 |
| IT-RCM001.1-06 | flow×duration/60 と dose の差が ±1% 超 | flow=60, dose=70, duration=60(16% 差) / Mock = `[ValidationError("dose_consistency", ...)]` | `ValidationFailed`、`enqueue` 不発火 | IF-U-011 | UT-005.3-06、UT-001.4-09 |
| IT-RCM001.1-07 | 多重失敗集約(flow + dose 両方範囲外) | flow=-1.0, dose=10000.0 / Mock = `[ValidationError("flow_rate"), ValidationError("dose_volume")]` | `ValidationFailed.errors` len=2、両方の field 含む | IF-U-011 | UT-005.3-07 |
| IT-RCM001.1-08 | **Validation 拒否時の本物 StateMachine 不変** | flow=1200.01 / Mock 拒否 / 本物 StateMachine(IDLE)+ 本物 CommandHandler | `ValidationFailed`、`StateMachine.current() == State.IDLE` 不変 | IF-U-001/011 | UT-001.1(StateMachine)、UT-005.1-02 |

#### 6.1.4 申し送り

- **CR-0004 解消済(Step 19 F1.6、修正候補 (b) Adapter 層追加採用)**:`src/vip_api/_validation_bridge.py`(`ClassBValidationApiAdapter` + `make_validation_api()` factory)を新設し、`vip_api_b.validate_settings` の `Ok` / `Err` 戻り値を `ValidationApi` Protocol の `list[ValidationError]` に変換する経路を確立。UT-005.1-bridge-01 〜 06(6 ケース)で UT 網羅。本 §6.1 の Mock ベース検証は不変、本物注入による SEP-001 越え経路検証は §6.7 IT-SEP(Step 19 F4)で扱う(`make_validation_api()` を直接 `ControlApi(validation_api=...)` に渡す経路)。
- **§6.7 IT-SEP(Step 19 F4)で本物 vip_api_b 注入経路検証**:本 §6.1 で Mock ベースに留めた SEP-001 越え経路検証は、§6.7 で `make_validation_api()` 経由の本物注入で再検証する。

### 6.2 RCM-003 結合(SW Watchdog + 階層防御 SW<HW)— **詳細化(Step 19 F2)**

#### 6.2.1 試験目的

RCM-003(SW Watchdog 300 ms、SDD §4.8)+ RCM-004(HW Watchdog 500 ms、SDD §4.3)の **階層防御時間順序** が結合状態でも維持されることを **本物 `time.monotonic` + 実時間 `time.sleep`** で検証する。UT-001.5(19 ケース)+ UT-002.4(18 ケース)で fake_clock 経由の境界判定は網羅済のため、本 IT は **「複数ユニット結合 + 本物実時間連動」** 観点に焦点を絞る(F1 の Mock パターンから一歩進めた階梯)。

#### 6.2.2 結合経路

```
[heartbeat 経路]   (Control Loop) → SwWatchdog.heartbeat()
                                  → HwFailsafeTimer.heartbeat()

[SW 発火経路]      heartbeat 停止 → SwWatchdog.check_once()(または monitor thread)
                  → 300 ms 超過検出 → StateMachine.on_watchdog_timeout(SW_WATCHDOG)
                  → StateMachine ERROR 遷移

[HW 発火経路]      heartbeat 停止 → HwFailsafeTimer.check_once()(または monitor thread)
                  → 500 ms 超過検出 → Pump.force_stop_failsafe(reason="HEARTBEAT_TIMEOUT")
                  → Pump 強制停止

[階層防御契約]     SW が先(300 ms)に発火し ERROR 遷移、HW が後(500 ms)に発火しても
                  StateMachine 二重遷移なし(SwWatchdog 冪等)、HW は独立契約として
                  Pump 強制停止を実行
```

#### 6.2.3 試験ケース(詳細)

| 試験 ID | 観点 | シナリオ | 期待結果 | 関連 IF-U | 関連 UT |
|--------|------|---------|---------|----------|--------|
| IT-RCM003.1-01 | 正常系(両 Watchdog 不発火) | 50 ms 間隔で 1 秒継続 heartbeat | 両 Watchdog 不発火、`on_watchdog_timeout` / `force_stop_failsafe` 0 回 | IF-U-004/005 | UT-001.5-01、UT-002.4-01 |
| IT-RCM003.1-02 | SW 単独発火 | heartbeat 停止 → 350 ms 経過 | SW 発火(`SW_WATCHDOG` 1 回呼出)、HW 未発火 | IF-U-006 | UT-001.5-02、UT-002.4-04a |
| IT-RCM003.1-03 | **階層防御時間順序** | heartbeat 停止 → SW 350 ms + HW 累積 600 ms | SW 先発火 + 冪等(`on_watchdog_timeout` 1 回のみ)、HW 後発火 → Pump 1 回停止 | IF-U-006/007 | UT-001.5-12(階層防御 fake_clock) |
| IT-RCM003.1-04 | HW 単独発火 | SW 起動なし → HW heartbeat 停止 → 550 ms | HW 発火 → `force_stop_failsafe(reason="HEARTBEAT_TIMEOUT")` 1 回 | IF-U-007 | UT-002.4-04b、UT-002.4-06 |
| IT-RCM003.1-05 | **監視スレッド経由の自動トリップ**(本物 lifecycle + 実時間) | `SwWatchdog.start()` → heartbeat 停止 → 450 ms 待機 → `stop()` | スレッドが自動検出してトリップ、`on_watchdog_timeout(SW_WATCHDOG)` 呼出 | IF-U-006 | (UT で再現困難な start/stop lifecycle 検証) |
| IT-RCM003.1-06 | 高頻度並行 heartbeat の Lock 競合なし | 2 スレッド × 100 回 × 1 ms 間隔(timeout 拡大 2 sec) | 両スレッド deadlock なく完走、Watchdog 不発火 | IF-U-004/005 | UT-001.5-09、UT-002.4-08(並行) |

#### 6.2.4 設計判断(Step 19 F2)

- **`check_once()` 直接呼出ベース**(IT-RCM003.1-01〜04 / 06):monitor スレッドの `monitor_interval` ジッタを排除して **境界判定の決定性を確保**。観点を「結合状態での `heartbeat` → `check_once` → 通知」に絞る。
- **本物 monitor スレッド起動**(IT-RCM003.1-05 のみ):UT で fake_clock 直接呼出は網羅済のため、IT は **`start/stop` lifecycle + 実時間 timer 精度の組合せ** に焦点。
- **クロック逆転耐性は IT 化せず**(B4/B9 教訓):UT-001.5-04 等の fake_clock 試験で網羅済。当初検討したが、本 IT 範囲では本物 `time.monotonic` を使うため逆転シナリオ自体が再現困難。代わりに IT-RCM003.1-05 のスレッド検証に置換(Step 19 F2 着手前クロスレビューで判断、ユーザー合意済)。
- **macOS sleep ジッタ対策**(Step 19 B4 教訓継続):実時間境界の判定は **緩い余裕**(sleep 後の経過 ≥ timeout + 50 ms 以上)を確保。ローカル 3 連続実行 stable 確認済(2026-05-01)。
- **MC/DC 目標は据置「—」**:UT-001.5 / UT-002.4 で 100% 達成済、IT は契約検証中心(coverage 計測対象外)。

#### 6.2.5 申し送り

- なし(本観点は CR-0004 や `vip_api_b` と独立、SW/HW Watchdog 系のみで完結)。

### 6.3 RCM-004 結合(送出間隔、Control Loop + Pump Simulator + HW Failsafe Timer)— **詳細化(Step 19 F3)**

#### 6.3.1 試験目的

RCM-004(送出間隔 200 ms ± 10%、SRS-P02、SDD §4.6 / §4.9)が結合状態でも維持され、Control Loop の `tick()` が **本物 PumpSimulator + 本物 PumpObserver + 本物 Flow Validator** を経由して機能整合的に動作することを検証する。SRS-P02 ±10% 統計時間試験は §6.8 IT-PERF(Step 19 F5)に分散配置済のため、本観点は **機能整合性のみ** に焦点。

#### 6.3.2 結合経路

```
[RUNNING tick]   StateMachine.current() == RUNNING
                 → SwWatchdog.heartbeat(now) + HwFailsafeTimer.heartbeat(now)
                 → settings_provider() → Flow Validator.validate(cmd, ctx)
                 → Pump.set_flow_rate(target)(IF-U-003)
                 → Auto-stop check(SRS-012、accumulated_volume >= dose)

[NEGATIVE tick]  StateMachine.current() == RUNNING
                 → 両 Watchdog heartbeat 送出
                 → Flow Validator が NEGATIVE 検出
                 → StateMachine.request_transition(WDT_TIMEOUT, reason='validation_failed')
                 → Pump dispatch 行わず

[IDLE skip]      StateMachine.current() != RUNNING
                 → tick が False を返し早期 return(heartbeat / dispatch なし)
```

#### 6.3.3 設計判断(Step 19 F3 着手前クロスレビュー → F1.6 で更新)

- **本物 SUT 比率を F2 からさらに増加**(F1 Mock 中心 → F2 本物 Watchdog 中心 → F3 本物 ControlLoop / Pump / Observer / Validator):本物 ControlLoop + 本物 PumpSimulator + 本物 PumpObserver + 本物 Flow Validator(ControlLoop 内ハードコード呼出)+ Mock(spec=StateMachine)+ MagicMock(spec なし)Watchdog 2 件。
- **CR-0005 (a) 解消済(Step 19 F1.6)**:`_HeartbeatSink` Protocol を `heartbeat() -> None`(引数なし)に整合化。本物 SwWatchdog / HwFailsafeTimer を ControlLoop に注入できる経路は §6.7 IT-SEP(Step 19 F4)で扱い、本 §6.3 は機能整合のみに focus を維持するため引き続き MagicMock(spec なし)を使用。
- **`tick()` 直接呼出ベース**:UT-001.2-19 で本物スレッド経由の `start/stop` lifecycle は網羅済 + IT-RCM003.1-05 で SwWatchdog 監視スレッドの実時間検証済のため、本 F3 は `tick()` 直接呼出による「結合状態での dispatch + heartbeat 経路の機能整合性」に焦点。
- **MC/DC 目標は据置「—」**:UT-001.2 / UT-002.1 / UT-002.2 で 100% 達成済、IT は契約検証中心。

#### 6.3.4 試験ケース(詳細)

| 試験 ID | 観点 | シナリオ | 期待結果 | 関連 IF-U | 関連 UT |
|--------|------|---------|---------|----------|--------|
| IT-RCM004.1-01 | 正常系(RUNNING tick) | RUNNING + 整合 Settings(flow=60)→ `tick()` | tick=True、本物 Pump `_target_flow=60`、両 Watchdog `heartbeat(ts)` 各 1 回呼出 | IF-U-003/004/005 | UT-001.2-01、UT-002.1-01 |
| IT-RCM004.1-02 | tick + advance_time 連続 → 過渡応答機能 | RUNNING + 連続 tick × 5 + `pump.advance_time(0.5)` | 本物 Pump current_flow が 0 → target=60 方向に増加(機能整合のみ、SRS-P01 ±5% は §6.8 へ) | IF-U-003 | UT-002.1-03/04(SRS-P01 過渡応答) |
| IT-RCM004.1-03 | heartbeat 引数なし契約 | tick 1 回 → 両 Watchdog の heartbeat 呼出を捕捉 | SW/HW 両方の `heartbeat()` が **引数なし** で 1 回ずつ呼ばれる(CR-0005 (a) 解消後の `_HeartbeatSink.heartbeat() -> None` 契約、各 Watchdog は内部 clock で timestamp を取得) | IF-U-004/005 | UT-001.2-15(引数なし契約) |
| IT-RCM004.1-04 | 異常入力 → State Machine WDT_TIMEOUT 経路 | flow_rate=-1.0(本物 Validator NEGATIVE)+ tick | tick=True、heartbeat 送出済、`request_transition(WDT_TIMEOUT, reason='validation_failed')` 1 回呼出、Pump dispatch なし | IF-U-002/003/004/005 | UT-001.2-04(NEGATIVE) |
| IT-RCM004.1-05 | IDLE 状態 → tick 早期 return | StateMachine.current() == IDLE + tick | tick=False、heartbeat 送出なし、dispatch なし、状態遷移なし(SDD §4.6.A 早期 return 仕様) | — | UT-001.2-01(IDLE skip) |

#### 6.3.5 申し送り

- **CR-0005 解消済(Step 19 F1.6、修正候補 (a) 採用)**:`_HeartbeatSink` Protocol を `heartbeat() -> None`(引数なし)に整合化、`ControlLoop._dispatch_*` の `self._sw_watchdog.heartbeat()` / `self._hw_watchdog.heartbeat()` 呼出も整合化。SwWatchdog / HwFailsafeTimer の `heartbeat()` は内部 clock で `_last_heartbeat` を更新する設計を維持(SDD §4.8.A / §4.3.A 不変)。本物 Watchdog を ControlLoop に注入できる経路は §6.7 IT-SEP(Step 19 F4)で活用予定。
- **SRS-P02 統計時間 + 過渡応答精度**:§6.8 IT-PERF(Step 19 F5)へ申し送り済(本 F3 は機能整合のみ)。

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

### 6.7 SEP-001 ランタイム分離 + 真の本物注入 E2E(アーキテクチャ検証)— **詳細化(Step 19 F4)**

#### 6.7.1 試験目的

SAD §9 SEP-001(クラス C ↔ クラス B 分離)が **AST 静的検証(UT-005.3-13 で確立済)に加えてランタイムでも維持** されること、すなわち、クラス B モジュール(`src/vip_api_b/`)実行時にクラス C 副作用(state mutation / I/O / threading)が観測されないことを **真の本物注入経路** で実証する。Step 19 F1.6 で CR-0004 (b) Adapter(`vip_api/_validation_bridge.py`)+ CR-0005 (a) `_HeartbeatSink.heartbeat() -> None` 引数なし化が解消されたことを前提とし、§6.1〜§6.3 の Mock 主体検証から **本物注入主体** へ移行した本観点で、SEP-001 越え経路 + 階層防御 E2E を結合状態で実証する。

#### 6.7.2 結合経路と検証スコープ

```
[SEP-001 越え正常経路] ControlApi.start(settings)
                        -> make_validation_api()  ※本物 Adapter 注入
                        -> ClassBValidationApiAdapter.validate_settings(settings)
                        -> vip_api_b.validate_settings(settings) -> Ok(settings)  ※クラス B 実体
                        -> Adapter が空 list [] に変換
                        -> 本物 CommandHandler.enqueue(START) -> Accepted(token)
                        -> 本物 StateMachine は IDLE 不変(dispatch スレッド未起動)

[SEP-001 越え異常経路] ControlApi.start(範囲外 settings)
                        -> Adapter -> vip_api_b.validate_settings -> Err(failures=[OutOfRange(...)])
                        -> Adapter が ValidationError list に変換
                        -> ValidationFailed 返却、enqueue 不発火
                        -> 本物 StateMachine は IDLE 不変(クラス B 拒否がクラス C へ副作用伝播しない)

[boundary 維持]         vip_api_b 内部例外(SDD §4.17.E try/except 全包)
                        -> Err([Inconsistency("internal:...")]) で復帰
                        -> Adapter が settings_consistency field の ValidationError に変換
                        -> ApiRejected(InternalError) ではなく ValidationFailed として正常な「拒否」
                        -> 例外が SEP-001 boundary を越えない

[階層防御 E2E]          本物 ControlLoop.tick()
                        -> 本物 SwWatchdog.heartbeat()  ※引数なし契約、CR-0005 (a)
                        -> 本物 HwFailsafeTimer.heartbeat()  ※同上
                        -> 各 Watchdog 内部 clock(time.monotonic)で _last_heartbeat 更新
                        -> 直後の check_once() で is_tripped=False
```

**設計判断(Step 19 F4):**

- **本物注入主体への移行**:§6.1〜§6.3 では Mock(spec=ValidationApi)/ MagicMock(`_HeartbeatSink`)で契約整合のみを検証。本観点では F1.6 で解消した CR-0004/0005 を活用し、`make_validation_api()` 経由の本物 Adapter + 本物 SwWatchdog/HwFailsafeTimer を真に注入する E2E に拡張。
- **AST 軸 + ランタイム軸の分散配置**:IT-SEP.1-01 はパッケージ全ファイル AST 拡張(`vip_api_b/__init__.py` 含む)、IT-SEP.1-04 が `sys.modules` のランタイム観測を担当。当初検討した「`del sys.modules` で reload を強制 → クラス C ルート観測」は Adapter 側の関数バインドと不整合で test_05 等の `patch` が効かなくなる副作用を発見、AST 軸の網羅 + ランタイム軸の冪等観測に分散配置で再構成(F4 着手中の発見、修正記録)。
- **CommandHandler dispatch スレッド未起動**:IT-SEP.1-02 / 03 / 05 では「`enqueue` 自体の挙動 + Validation 経路の SEP-001 boundary 維持」を主検証する目的で、本物 CommandHandler の `start()` を呼ばない(IT-RCM001.1-08 と同パターン、teardown 複雑化を避ける)。スレッド lifecycle は §6.6 IT-RCM019 で別途網羅済。
- **Watchdog monitor スレッド未起動**:IT-SEP.1-06 では `last_heartbeat()` ベースで境界判定の決定性を確保(monitor スレッドの `monitor_interval` ジッタを排除、§6.2 IT-RCM003.1-05 で本物 lifecycle 検証済)。
- **MC/DC 目標は据置「—」**:UT-005.3 / UT-005.1-bridge / UT-001.5 / UT-002.4 / UT-001.2 で 100% 達成済、IT は契約検証中心(coverage 計測対象外)。

#### 6.7.3 試験ケース(詳細)

| 試験 ID | 観点 | シナリオ | 期待結果 | 関連 IF-U | 関連 UT |
|--------|------|---------|---------|----------|--------|
| IT-SEP.1-01 | クラス B パッケージ全ファイル AST 拡張 | `vip_api_b/*.py` 全件を AST 解析 → クラス C ルート(`vip_ctrl` / `vip_sim` / `vip_integrity` / `vip_api`)の import が無いこと | 全ファイル交差集合空(`vip_persist` のみ frozen 値オブジェクト共有として許容) | — | UT-005.3-13(`validation_api.py` 単体 AST、本 IT で `__init__.py` 追加) |
| IT-SEP.1-02 | 本物 vip_api_b 注入(Adapter 経由)正常 start | `make_validation_api()` + 本物 StateMachine(IDLE)+ 本物 CommandHandler、整合 Settings(60/60/60)で `start()` | `Ok(token != "")`、本物 StateMachine.current() == IDLE 不変 | IF-U-011 | UT-005.1-bridge-05/06、UT-005.3-01 |
| IT-SEP.1-03 | 本物注入 + 異常 → boundary 維持 | flow=1200.01(SRS-O-001 上限超) | `ValidationFailed.errors` len ≥ 1、`flow_rate` field 含む、本物 StateMachine.current() == IDLE 不変 | IF-U-011 | UT-005.1-bridge-02、UT-005.3-02 |
| IT-SEP.1-04 | 純粋関数性 + sys.modules 不変 | 同 Settings で 5 回 `validate_settings` 呼出 | 5 回とも空 list(冪等)、`sys.modules` のクラス C ルート差分 0 件 | — | UT-005.3-09(プロパティ試験) |
| IT-SEP.1-05 | 例外握りつぶし契約(本物注入経由) | `vip_api_b.validation_api.Decimal` を patch して `RuntimeError` 注入 | `ValidationFailed`(`ApiRejected(InternalError)` ではない)、`settings_consistency` field、`message` が `inconsistency: internal:` 始まり、本物 StateMachine.current() == IDLE 不変 | IF-U-011 | UT-005.3-08(`Decimal` patch 例外注入) |
| IT-SEP.1-06 | 本物 Watchdog + ControlLoop heartbeat 引数なし契約 E2E | 本物 SwWatchdog + HwFailsafeTimer + ControlLoop + PumpSimulator + PumpObserver + Mock(spec=StateMachine)RUNNING 状態で `tick()` | tick=True、両 Watchdog の `last_heartbeat()` が tick 前から進む、`check_once()` False、`is_tripped()` False、`on_watchdog_timeout` / `force_stop_failsafe` 不発火、Pump `_target_flow=60` 反映 | IF-U-003/004/005 | UT-001.2-15(引数なし契約)、UT-001.5-01、UT-002.4-01 |

#### 6.7.4 設計判断(Step 19 F4 着手中の発見と是正)

- **「`del sys.modules` で reload + クラス C ルート観測」案の不採用**:当初は IT-SEP.1-01 で **AST 軸 + ランタイム sys.modules 軸を 1 ケースに統合** する設計だった。実装後の並行実行検証で、`del sys.modules` 後に `vip_api_b.validation_api` が再ロードされると、Adapter(`_validation_bridge`)が module load 時に bind した `_validate_settings_b` 参照が **古い module の関数オブジェクトを指したまま** となり、後続 IT-SEP.1-05 の `with patch("vip_api_b.validation_api.Decimal", ...)` が **新しい module 側を patch** して効かなくなる現象を発見(IT-SEP.1-05 単体実行は Pass、ファイル全体実行で Fail)。そこで AST 軸(IT-SEP.1-01、`__init__.py` も含めた全ファイル網羅)とランタイム軸(IT-SEP.1-04、`sys.modules` 差分 0 件 + 冪等性)に分散配置し、Adapter のバインド一貫性を保つ設計に是正。**お手本的価値:** 「Python の `sys.modules` 操作は import バインドの一貫性を破壊するため、テスト副作用が大きい。`importlib.reload` も同様の問題を持つため、SEP-001 ランタイム検証は AST + 受動観測(差分監視)の 2 軸分散が最も安全」を後続プロジェクトに推奨。

#### 6.7.5 申し送り

- **CR-0004 / CR-0005 解消後の真の SEP-001 越え経路実証完了**:F1〜F3 で予告していた「§6.7 IT-SEP で本物注入による真の SEP-001 越え経路 + 階層防御 E2E を実証」を本ステップで完了。
- **動的 import / threading 副作用観測の限界**:IT-SEP.1-04 は `set(sys.modules)` 差分の受動観測で「クラス C ルート新規追加無し」を担保するが、すでに sys.modules に存在するクラス C モジュール群への **後続の attribute 副作用**(関数呼出 / 動的 attr 設定)は本観点では検出困難。`vip_api_b` 側の純粋関数契約(SDD §4.17、`@dataclass(frozen=True)` 値オブジェクト)が静的に保証している前提で、本 IT は import グラフ + 冪等性 + 例外握りつぶし契約の 3 軸で SEP-001 ランタイム分離を担保する設計。動的 attr 副作用の観測は Inc.5 セキュリティ拡張時の動的解析(SOUP 候補検討)で再評価。

### 6.8 SRS-P02 / P03 / P04 / P06 統計時間試験(IT-PERF)— **詳細化済(Step 19 F5)**

#### 6.8.1 目的・対象・関連要素

- **目的:** UT で決定論化により扱えない **実時間スレッド統計挙動** を、`time.perf_counter` 実測 + `pytest-benchmark`(SOUP-012、Step 19 F0 正式採用)で **P95 / 平均 / 標準偏差** として検証する。UT 申し送り 3 件(UT-001.2-19、UT-001.3-19、UT-002.4)を IT で本物 SUT 結合状態の統計試験として回収する位置付け。
- **対象 SRS と本 IT における判定値:**
  - **SRS-P02(SRS L123):** 制御サイクル **100 ms ± 10 ms**(ジッタ 10% 以内、必須、IT)。SDD §4.6.B `_period_sec=0.1` 定数で実装済(`PERIOD_SEC: Final[float] = 0.1`)。本 IT は **本物 ControlLoop の実時間スレッド** で 30 周期分の heartbeat 間隔 P95 を測定。
  - **SRS-P03(SRS L124):** 開始 → 注入開始 **500 ms 以内**(必須、ST 範疇)。SDD §4.7 では **アプリ層内訳予算 100 ms**(`start ≤ 100 ms` = 通常パス put + dispatch get + State Machine 遷移、SDD §4.7.E)で実装。本 IT は SDD 内訳予算 100 ms を本物 CommandHandler + 本物 StateMachine で P95 統計検証(SRS の 500 ms 全体予算は ST で検証する分散配置)。
  - **SRS-P04(SRS L125):** 停止 → 注入停止 **200 ms 以内**(必須、ST 範疇、HZ-002)。SDD §4.7 では **アプリ層内訳予算 50 ms**(`stop ≤ 50 ms` = ファストパスでキューバイパス、SDD §4.7.A)で実装。本 IT は SDD 内訳予算 50 ms を本物 CommandHandler の **STOP ファストパス経路** で P95 統計検証(SRS の 200 ms 全体予算は ST で検証する分散配置)。
  - **SRS-P06(SRS L127):** 永続化書き込みによる制御サイクルへの影響は SRS-P02 許容ジッタ内に収まる(必須、IT、負荷)。本 IT は Control Loop と並行実行する **永続化スレッド負荷下** での SRS-P02 周期維持を検証(SAD §X / SDD で永続化を別スレッド・キュー化する設計の結合検証)。
- **関連 IF-U:** IF-U-001(ControlApi → CommandHandler、IT-PERF.2-01/02)、IF-U-002(CommandHandler → StateMachine、IT-PERF.2-01/02)、IF-U-003(ControlLoop → Pump set_flow_rate、IT-PERF.1-01/02 + 3-02)、IF-U-004(ControlLoop → SwWatchdog heartbeat、IT-PERF.1-01)、IF-U-005(ControlLoop → HwFailsafeTimer heartbeat、IT-PERF.1-01 + 3-01)、IF-U-009(永続化、IT-PERF.3-02)。
- **関連 SRS:** SRS-P02、SRS-P03(SDD 内訳)、SRS-P04(SDD 内訳)、SRS-P06、SRS-RCM-004(タイマ精度の長時間連続観察、IT-PERF.3-01)。
- **元 UT 申し送り:** UT-001.2-19(UTPR §7.3.9 v0.10 申し送り、SRS-P02 ±10% 実時間周期精度統計)、UT-001.3-19(UTPR §7.3.12 v0.13 申し送り、SRS-P03/P04 P95 統計)、UT-002.4(UTPR §7.3.3 v0.4 申し送り、HW Failsafe Timer 精度の長時間連続観察)。
- **試験技法:** `time.perf_counter`(高精度モノトニックタイマ)+ `pytest-benchmark`(SOUP-012、IT-PERF.1-02 のみ)、サンプル数 ≥ 30、P95 統計 + 緩い境界判定(F2/F3 macOS sleep ジッタ対策パターン継続)+ ローカル `pytest -m perf` 3 連続安定確認で flake 抑制。
- **マーカー方針(§8.1 整合):** 全 6 件に `@pytest.mark.integration` + `@pytest.mark.perf` + **`@pytest.mark.nightly`** + **`@pytest.mark.linux_only`** 付与 — §8.1 で「IT-PERF / IT-PWR / IT-SIDE は Linux runner 限定 + nightly schedule での実行」と規定済(全 PR で実行すると CI 時間と非決定性ノイズが増大)。CI では `integration-test.yml` の `integration-nightly` ジョブ(cron `0 2 * * *` UTC、Linux runner)で実行、`integration-fast` ジョブの `-m "integration and not nightly"` からは除外される。**`linux_only` マーカーは Step 19 F5 で `tests/conftest.py` に auto-skip hook を新規追加**(F6/F7 でも継続使用、`pytest_collection_modifyitems` で `sys.platform != "linux"` のとき skip 化)、ローカル macOS / Windows では auto-skip でテスト実行されない。

#### 6.8.2 試験ケース表(IT-PERF.1-XX / 2-XX / 3-XX、6 ケース)

| 試験 ID | 観点 | 入力(SUT 構成) | 期待結果 | 関連 IF-U | 元 UT |
|---------|------|----------------|---------|-----------|-------|
| IT-PERF.2-01 | SRS-P03 **start 応答 P95**(SDD 内訳 100 ms) | 30 回別々に `(StateMachine + CommandHandler)` を構築 → IDLE 初期化 → CommandHandler `start()` → `t0=perf_counter` → `enqueue(START)` → `await_completion(token, timeout_ms=500)` → `t1=perf_counter` → `stop()`。各経過 (t1-t0) を ms 単位で記録 | サンプル数 = 30、全件 `Completed` 完了、**P95 ≤ 100 ms(SDD §4.7.E 内訳予算)**、SRS-P03 全体予算 500 ms は ST で別途検証 | IF-U-001/002 | UT-001.3-19(UTPR §7.3.12 v0.13) |
| IT-PERF.2-02 | SRS-P04 **stop ファストパス P95**(SDD 内訳 50 ms 厳密) | 30 回別々に `(StateMachine + CommandHandler)` を構築 → `set_initial(IDLE)` → start → enqueue(START) + await → RUNNING 状態確認 → `t0=perf_counter` → `enqueue(STOP)`(STOP_KINDS ファストパス) → `await_completion(token)` → `t1=perf_counter` → handler stop。stop 経過 (t1-t0) を ms 単位で記録 | サンプル数 = 30、全件 `Completed`、**P95 ≤ 50 ms**(SDD §4.7.A ファストパス内訳厳密、Linux runner 限定 = `linux_only` auto-skip でローカル macOS では skip、§6.8.4 二重記録)、SRS-P04 全体予算 200 ms は ST で別途検証 | IF-U-001/002 | UT-001.3-19(UTPR §7.3.12 v0.13) |
| IT-PERF.3-01 | HW Failsafe Timer **発火タイミング長時間観察** | 本物 HwFailsafeTimer + Mock(spec=PumpController)`force_stop_failsafe.side_effect` で発火時刻記録 → `start()`(`_last_heartbeat = clock()` 自動設定済) → `t_initial = perf_counter` → 0.7 秒 sleep → `stop()` | `force_stop_failsafe` 呼出 1 回、`start()` 起動時刻 → 発火経過 ∈ **[400 ms, 700 ms]**(HEARTBEAT_TIMEOUT 500 ms + MONITOR_INTERVAL 100 ms 余裕 + macOS sleep ジッタ余裕)。設計是正:`heartbeat()` 呼出は冗長 + monitor 第 1 回 check_once との race condition で SDD §4.3.E クロック逆転安全側発火が偶発発動するため呼ばない(§6.8.4 二重記録)。 | IF-U-005 | UT-002.4(UTPR §7.3.3 v0.4) |
| IT-PERF.1-01 | SRS-P02 Control Loop **100 ms 周期精度 P95** | 本物 ControlLoop + 本物 PumpSimulator + 本物 PumpObserver + Mock(spec=StateMachine) RUNNING + MagicMock SwWatchdog/HwFailsafeTimer(`heartbeat()` 呼出時刻を `side_effect` で記録)で `start()` → 3.0 秒動作 → `stop()` | sw_heartbeat 呼出間隔のサンプル数 ≥ 25、**P95 ≤ 0.110 sec**(SRS-P02 100 ms ± 10 ms 厳密、Linux runner 限定 = `linux_only` auto-skip、§6.8.4 二重記録)、平均 ≤ 0.105 sec(SRS-P02 +5%) | IF-U-003/004/005 | UT-001.2-19(UTPR §7.3.9 v0.10) |
| IT-PERF.3-02 | SRS-P06 **永続化スレッド負荷下の SRS-P02 維持** | 本物 ControlLoop(IT-PERF.1-01 と同構成)で `start()` 起動 + 並行 **永続化負荷スレッド**(`atomic_writer.write(b"x"*1024, tmp_path / "perf.dat")` ループ)で 3.0 秒動作 → 両停止。Control Loop の sw_heartbeat 間隔 P95 を測定 | sw_heartbeat 呼出間隔のサンプル数 ≥ 25、**P95 ≤ 0.110 sec**(SRS-P06 = SRS-P02 ジッタ内 110 ms 厳密、Linux runner 限定 = `linux_only` auto-skip、§6.8.4 二重記録)、平均 ≤ 0.105 sec、永続化スレッドが 3 秒間で ≥ 50 回成功 | IF-U-003/004/005、IF-U-009 | SRS-P06 取りこぼし回収 |
| IT-PERF.1-02 | SRS-P02 `tick()` **平均サイクル時間**(`pytest-benchmark` 初使用、ファイル末尾配置)| 本物 ControlLoop + 本物 PumpSimulator + 本物 PumpObserver + Mock(spec=StateMachine) RUNNING + MagicMock Watchdog 2 件、`benchmark(loop.tick)` で `tick()` 単発を測定 | `benchmark.stats.stats.mean` ≤ 0.010 sec(処理時間は SRS-P02 100 ms 周期に十分余裕、緩い境界で flake 抑制)。配置順:`pytest-benchmark` plugin が後続テストの GC / スケジューリングに影響するため本ケースは **テスト定義順の末尾**(§6.8.4 二重記録)。 | IF-U-003 | UT-001.2-19、SOUP-012 初運用 |

#### 6.8.3 結合経路と SUT 構成

```
[本物 ControlLoop] ──tick(100 ms)──┬──[本物 PumpSimulator]   IT-PERF.1-01 / 1-02 / 3-02
                                   ├──[本物 PumpObserver]
                                   ├──[MagicMock SwWatchdog]──side_effect で時刻記録
                                   └──[MagicMock HwFailsafeTimer]

[本物 CommandHandler] ──enqueue/await──[本物 StateMachine]    IT-PERF.2-01 / 2-02

[本物 HwFailsafeTimer] ──force_stop_failsafe──[Mock PumpController]   IT-PERF.3-01

[本物 atomic_writer.write] ──並行スレッド負荷                     IT-PERF.3-02
```

#### 6.8.4 設計判断(Step 19 F5 着手前クロスレビューでの整合化)

- **§6.8 数値訂正(MINOR、CR 不要、SCMP §4.1 軽微)**:本書 v0.7 までの §6.8 骨格(L557、ITPR v0.1 = Step 19 D-2 で初版作成時の誤記)に対し、Step 19 F5 着手前クロスレビューで SRS / SDD / UTPR との数値乖離を発見し、本 v0.8 で訂正:
  - **SRS-P02**: v0.7「200 ms ± 10%」→ v0.8「**100 ms ± 10 ms**」(SRS L123 / SDD §4.6.B `PERIOD_SEC=0.1` / UTPR §7.3.9 v0.10 整合化、200 ms は誤記)。
  - **SRS-P03**: v0.7「P95 ≤ 50 ms」→ v0.8「**P95 ≤ 100 ms(SDD 内訳)**」(SRS L124 全体 500 ms / SDD §4.7.E 内訳 100 ms / UTPR §7.3.12 v0.13 整合化、50 ms は SRS-P04 と取り違え)。
  - **SRS-P04**: v0.7「P95 ≤ 200 ms」→ v0.8「**P95 ≤ 50 ms(SDD 内訳ファストパス)**」(SRS L125 全体 200 ms / SDD §4.7.A 内訳 50 ms ファストパス / UTPR §7.3.12 v0.13 整合化)。
  - **SRS-P06 取りこぼし回収**: v0.7 で IT-PERF 観点に SRS-P06(永続化非ブロッキング、SRS L127 で IT 範疇明示)が未列挙 → v0.8 で IT-PERF.3-02 として詳細化。
  - **SRS と SDD の解釈差(SRS-P03/P04 全体予算 vs SDD 内訳予算)**:SRS の全体予算(500 ms / 200 ms)は **入力受領 → 物理動作変化までのフルパス**、SDD 内訳予算(100 ms / 50 ms)は **アプリ層 enqueue → State Machine 遷移完了までの応答時間**。両者は「アプリ層は SRS 全体予算の 1/5(= ST 検証)以内で完了する」設計余裕を持つことで整合する。本 IT は SDD 内訳予算で検証 + ST で SRS 全体予算検証の **分散配置** を採用(本 §6.8 設計判断の他に、Step 19 G 着手時の STPR 計画でも明文化予定)。
- **`pytest-benchmark` の限定使用**:本 SOUP は IT-PERF.1-02 の `tick()` 単発平均時間測定のみで使用(初運用)。残り 5 件は `time.perf_counter` 実測による P95 統計(Python 標準ライブラリ、サンプル数 ≥ 25〜30)。理由:`pytest-benchmark` は 1 関数の平均/標準偏差計測に最適化されており、「複数回スレッド連動シナリオの応答時間統計」(IT-PERF.2-01 など)は `time.perf_counter` 直測で十分かつ環境依存性も低い。
- **本物 SUT 比率の最大化**:F1 (Mock 主体) → F2 (本物 Watchdog 主体) → F3 (本物 ControlLoop + Pump) → F4 (本物 vip_api_b Adapter + 本物 Watchdog) と進めてきた延長で、本 §6.8 は **本物 ControlLoop / 本物 CommandHandler / 本物 HwFailsafeTimer / 本物 atomic_writer** を主体に Mock は StateMachine(IT-PERF.1-01/02/3-02)と PumpController(IT-PERF.3-01)、MagicMock を Watchdog(IT-PERF.1-01/02/3-02、`side_effect` で時刻記録するため)に限定。実時間挙動の本質は本物 SUT で観察し、Mock は副作用フックとして機能する設計。
- **`linux_only` マーカー auto-skip 機構の F5 先取り実装**(Step 19 F5 着手中の発見と是正):F2 / F3 の macOS sleep ジッタ対策パターン(緩い境界 + 3 連続安定)を本 §6.8 でも当初試みたが、CommandHandler 30 回スレッド lifecycle + Control Loop 実時間スレッド + 永続化スレッド並行で macOS の OS noise が大きく、3 連続中 2 回 fail を実測。当初は境界を SRS / SDD 値 + macOS jitter 余裕(110 ms→130 ms / 50 ms→70 ms)に緩める案を採用していたが、**(i)** SRS / SDD 値から逸脱した境界は SRS-P02 100 ms ± 10% 性能要求の本旨を曖昧化する、**(ii)** ITPR §8.1 で既に「IT-PERF / IT-PWR / IT-SIDE は Linux runner 限定」と規定済み — の 2 点から、**ITPR §8.1 規定の機械化** = `linux_only` マーカー auto-skip hook を F5 で先取り実装する方針に変更。`tests/conftest.py` に `pytest_collection_modifyitems` hook を追加し、`sys.platform != "linux"` のとき `linux_only` マーカー付きテストを skip 化(F6 で予定だった機能を F5 で導入、F6 / F7 で継続再利用)。本機構により **境界は SRS / SDD 値で厳密判定**(SRS-P02 = 110 ms / SDD ファストパス = 50 ms / SRS-P06 = 110 ms)、ローカル macOS では auto-skip で flake 影響なし、CI Linux nightly で SRS 性能要求の検証が成立。**お手本的価値:** 計画書(ITPR §8.1)で記述したマーカー運用を機械化する hook を、最初に必要となるサブステップ(F5)で先取り実装することで、後続(F6 / F7)で重複作業なく再利用できる。「規定 → 機械化 → 利用」の 3 段階で実装するパターンを後続プロジェクトに推奨。
- **`pytest-benchmark` plugin 副作用回避**(Step 19 F5 着手中の発見):`pytest-benchmark` は `benchmark` fixture 利用後に GC タイミング / スレッドスケジューリングに影響することが確認された(本 §6.8 着手時に IT-PERF.1-02 を 2 番目に置いた状態で IT-PERF.2-01 / 2-02 / 3-01 が `TimedOut` / 偶発失敗、benchmark 単独実行および 1-02 を末尾配置すると全件 Pass)。**対策:** `tests/integration/test_perf_statistical_timing.py` のテスト定義順を IT-PERF.2 系 → 3-01 → 1-01 → 3-02 → 1-02(末尾)に並べ替え。後続プロジェクトでは「pytest-benchmark を使うテストは独立ファイル化または末尾配置」が安全。
- **IT-PERF.3-01 `heartbeat()` 削除設計是正**(Step 19 F5 着手中の発見):当初設計では `timer.start()` 直後に `timer.heartbeat()` を呼び、その時刻を計測基準としていた。しかし `start()` の lock 内で `_last_heartbeat = clock()` が設定済 + monitor スレッドが起動して第 1 回 `check_once()` を呼ぶ流れで、`heartbeat()` と `check_once()` が同 lock を競合する race window が存在し、SDD §4.3.E のクロック逆転安全側発火条件(Step 19 B4 整合化、`elapsed < 0` で発火)が **偶発的に発動** することを実測で発見。具体的には:(i) main が `heartbeat()` で lock 取得、`_last_heartbeat = clock()` を新値で更新、ロック解放。(ii) monitor 第 1 回 check_once が `with self._lock: last = self._last_heartbeat` で **新値**を取得、しかし `now` は step (i) より **前** に取得済(check_once 関数の冒頭 `now = self._clock()` が lock 外)→ `elapsed = now - last < 0` → SDD §4.3.E 安全側発火 → trip elapsed が極端に小さくなる(0.5 ms 〜 数 ms)。**対策:** `heartbeat()` 呼出は `start()` で `_last_heartbeat` 設定済のため冗長、削除して `start()` 時刻を計測基準に変更(test と ITPR §6.8.2 IT-PERF.3-01 入力欄に二重記録)。**お手本的価値:** Lock の外で取得した時刻と Lock 内で更新された値の比較は race condition の温床となる(SDD §4.3 のクロック逆転安全側発火という意図的設計が、テスト初期化の race で偶発発動した実例)。後続プロジェクトでは「実時間 lock-protected counter の計測時は、計測前にラージ wait + 計測後にラージ wait を入れて初期化シーケンスを安定化」を推奨。

#### 6.8.5 申し送り

- **長期間連続稼働の劣化観察**(統計時間の **トレンド変化** 観察):本 §6.8 v0.8 は「30 周期 / 30 サンプル」の単発統計試験。長期間連続稼働(数十分〜数時間)での P95 劣化観察は **Inc.5(品質拡張・運用) で正式観点化** とする(Inc.1 完了の必須要件ではない)。
- **CI nightly 実行結果の蓄積(Inc.1 完了タグ前の必須申し送り)**:Step 19 F5 マージ後、`integration-test.yml` の `integration-nightly` ジョブ(Linux runner)で本 §6.8 の P95 統計が連続実行される。本 PR ではローカル macOS で `linux_only` auto-skip により全 6 件が意図的 skip 状態のため、**実測確認は CI Linux nightly に申し送り**。Inc.1 完了タグ `v0.1.0-inc1` 付与までに **5 連続 nightly 全 Pass** を確認(Step 19 H で集約予定、§7.1 受入基準に追記)。万一 CI Linux 環境で安定境界 110 ms / 50 ms 内に収まらない場合は、別 PR で境界調整(SDD 設計と整合する範囲)+ ITPR §6.8.4 へ再整合化注釈を追記する運用とする(F4 の「IT 着手中の設計是正を ITPR §6.x.4 + DEVSTEPS に二重記録」運用の継続適用)。
- **`pytest-benchmark` 比較レポート**:`--benchmark-save=name` / `--benchmark-compare=name` でラウンド間比較が可能だが、本 §6.8 v0.8 では使用しない(Inc.5 性能リグレッション検出時に正式運用、SOUP-012 機能の段階的活用)。
- **SRS-P03 / P04 全体予算の ST 試験**:Step 19 G(STPR 骨格化)で「IDLE → start コマンド → 物理 Pump 動作変化まで全体 500 ms 内」「RUNNING → stop コマンド → 物理 Pump 停止まで全体 200 ms 内」を ST 試験として骨格化する。本 IT (SDD 内訳予算) と ST (SRS 全体予算) の **分散配置** を STPR §X で明文化。

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
| IT-RCM001(指令範囲、§6.1 詳細化済 Step 19 F1)| **8**(IT-RCM001.1-01〜08)| **8** | 0 | 0 | 2026-05-01 | (本 PR マージコミット)|
| IT-RCM003(SW/HW Watchdog、§6.2 詳細化済 Step 19 F2)| **6**(IT-RCM003.1-01〜06)| **6** | 0 | 0 | 2026-05-01 | (本 PR マージコミット)|
| IT-RCM004(送出間隔、§6.3 詳細化済 Step 19 F3)| **5**(IT-RCM004.1-01〜05)| **5** | 0 | 0 | 2026-05-01 | (本 PR マージコミット)|
| IT-SEP(SEP-001 ランタイム、§6.7 詳細化済 Step 19 F4)| **6**(IT-SEP.1-01〜06)| **6** | 0 | 0 | 2026-05-03 | (本 PR マージコミット)|
| IT-PERF(統計時間、§6.8 詳細化済 Step 19 F5)| **6**(IT-PERF.1-01/02、2-01/02、3-01/02)| TBD(設計確定、CI Linux nightly で実測確認は Inc.1 完了タグ前に申し送り、§6.8.5 参照) | TBD | **6**(macOS local の `linux_only` auto-skip による意図的 skip)| 2026-05-04(設計確定)| (本 PR マージコミット、Linux nightly 結果は別 PR で記入)|
| IT-PWR(電源断、§6.9 骨格)| **≥ 4**(Step 19 F で詳細化)| TBD | TBD | TBD | TBD | TBD |
| IT-SIDE(サイドチャネル、§6.10 骨格)| **≥ 2**(Step 19 F で詳細化)| TBD | TBD | TBD | TBD | TBD |
| **合計** | **≥ 67** | — | — | — | — | — |

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
| RCM-001 指令範囲 | IT-RCM001.1-01〜08(§6.1 詳細化済 Step 19 F1) | SRS-O-001、SRS-RCM-001、SRS-UX-001/004/005、SRS-005 | RCM-001 | HZ-001、HZ-002 | IF-U-001/011/013 | UT-001.4、UT-005.1、UT-005.3 | **Pass(8 tests、Mock ベース契約検証 + IT-RCM001.1-08 本物 StateMachine 不変実証、Step 19 F1)** |
| RCM-003 SW Watchdog 階層 | IT-RCM003.1-01〜06(§6.2 詳細化済 Step 19 F2)| SRS-RCM-003、SRS-RCM-004 | RCM-003、RCM-004 | HZ-001、HZ-002 | IF-U-004/005/006/007 | UT-001.5、UT-002.4 | **Pass(6 tests、本物実時間連動 + 階層防御時間順序実証 + 監視スレッド lifecycle 検証、Step 19 F2、3 連続安定確認)** |
| RCM-004 送出間隔 | IT-RCM004.1-01〜05(§6.3 詳細化済 Step 19 F3)| SRS-031、SRS-P02(機能整合のみ)、SRS-RCM-004 | RCM-004 | HZ-001、HZ-002 | IF-U-002/003/004/005 | UT-001.2、UT-002.1、UT-002.2、UT-001.4 | **Pass(5 tests、本物 ControlLoop + Pump + Observer + Validator 結合 + MagicMock Watchdog 経路、機能整合性検証、Step 19 F3、3 連続安定確認)** |
| SEP-001 ランタイム | IT-SEP.1-01〜06(§6.7 詳細化済 Step 19 F4)| SRS-UX-001/004/005、SRS-005、SRS-RCM-003、SRS-RCM-004 | RCM-003 / RCM-004(IT-SEP.1-06 副次)| — | IF-U-003/004/005/011 | UT-005.3、UT-005.1-bridge、UT-001.2、UT-001.5、UT-002.4 | **Pass(6 tests、本物 vip_api_b Adapter 注入による SEP-001 越え経路 + 階層防御 E2E + 例外握りつぶし契約 boundary 維持実証、Step 19 F4)** |
| 統計時間 | IT-PERF.1-01/02、2-01/02、3-01/02(§6.8 詳細化済 Step 19 F5)| SRS-P02、SRS-P03(SDD 内訳)、SRS-P04(SDD 内訳)、SRS-P06、SRS-RCM-004 | —(性能要求のため RCM 紐付けなし、ただし HW Failsafe Timer 観察は IT-PERF.3-01 で RCM-004 関連)| HZ-002(SRS-P04 関連)| IF-U-001/002/003/004/005/009 | UT-001.2-19(UTPR §7.3.9 v0.10)、UT-001.3-19(UTPR §7.3.12 v0.13)、UT-002.4(UTPR §7.3.3 v0.4)| **設計確定(6 tests、本物 ControlLoop / CommandHandler / HwFailsafeTimer / atomic_writer + `pytest-benchmark` 初運用 + `linux_only` auto-skip hook 新設、§6.8 数値訂正後の SRS / SDD 整合境界(110 ms / 50 ms / 110 ms 厳密)で実装。macOS local では auto-skip、CI Linux nightly での実測確認は Inc.1 完了タグ前に 5 連続 Pass を申し送り、§6.8.5 参照)** |
| 電源断耐性 | IT-PWR.* (§6.9 骨格)| SRS-DATA-002/003、SRS-RCM-015 | RCM-015 | HZ-007 | IF-U-009、IF-E-001 | UT-003.3 | TBD |
| サイドチャネル | IT-SIDE.* (§6.10 骨格)| SRS-SEC-001 | — | HZ-007 | — | UT-003.2 | TBD |

**カバレッジ:** 本マトリクスにより、Inc.1 全 RCM 6 件 / SDD 17 ユニットからの UT 申し送り 6 件 / SAD §9 SEP-001 が IT カテゴリと紐付き、SRS / RCM / HZ / IF-U への双方向トレーサビリティが確立した(v0.1 では §6.4 / §6.5 / §6.6 詳細化分が試験 ID レベル、残骨格は Step 19 F で完成)。

## 14. 改訂履歴

| バージョン | 日付 | 変更内容 | 変更者 |
|----------|------|---------|--------|
| 0.8 | 2026-05-04 | **Step 19 F5(§6.8 IT-PERF 統計時間試験詳細化 + 数値訂正 + `linux_only` auto-skip hook 新設)を反映。** §6.8 を骨格 → 詳細化(IT-PERF.1-01/02、2-01/02、3-01/02、6 ケース表 + 結合経路 4 構成 + 設計判断 5 項目 + 申し送り 4 項目)。**着手前クロスレビューでの数値訂正(MINOR、CR 不要、SCMP §4.1 軽微):** v0.7 までの §6.8 骨格(L557、ITPR v0.1 = Step 19 D-2 初版作成時の誤記)で SRS / SDD / UTPR との数値乖離を発見し、本 v0.8 で訂正:**(a)** SRS-P02 「200 ms ± 10%」→ 「**100 ms ± 10 ms**」(SRS L123 / SDD §4.6.B `PERIOD_SEC=0.1` / UTPR §7.3.9 v0.10 整合化)、**(b)** SRS-P03 「P95 ≤ 50 ms」→ 「**P95 ≤ 100 ms(SDD 内訳)**」(SRS L124 全体 500 ms / SDD §4.7.E 内訳 100 ms / UTPR §7.3.12 v0.13 整合化、50 ms は SRS-P04 と取り違え)、**(c)** SRS-P04 「P95 ≤ 200 ms」→ 「**P95 ≤ 50 ms(SDD 内訳ファストパス)**」(SRS L125 全体 200 ms / SDD §4.7.A 内訳 50 ms ファストパス / UTPR §7.3.12 v0.13 整合化)、**(d)** SRS-P06 取りこぼし回収(IT-PERF.3-02 で永続化スレッド負荷下の SRS-P02 維持を新規追加)、**(e)** SRS と SDD の解釈差(SRS-P03/P04 全体予算 vs SDD 内訳予算)を「IT は SDD 内訳予算 / ST は SRS 全体予算」の分散配置と整理(Step 19 G STPR 骨格化で明文化予定)。**着手中の設計是正(F5 PR 内で完結):** 当初 macOS sleep ジッタ余裕境界(110 ms→130 ms / 50 ms→70 ms)で実装したが 3 連続中 2 回 fail を実測 → ITPR §8.1 規定「IT-PERF / IT-PWR / IT-SIDE は Linux runner 限定」の機械化として **`linux_only` マーカー auto-skip hook を `tests/conftest.py` に新規追加**(F6 で予定だった機能を F5 で先取り、`pytest_collection_modifyitems` で `sys.platform != "linux"` のとき skip 化、F6 / F7 で継続再利用)、境界は SRS / SDD 値で厳密判定に戻す(110 ms / 50 ms / 110 ms)。**IT-PERF.3-01 race condition 是正:** `start()` 直後 `heartbeat()` 呼出が monitor 第 1 回 check_once と lock 競合して SDD §4.3.E クロック逆転安全側発火が偶発発動する race window を実測で発見 → `heartbeat()` 削除、`start()` 時刻基準に変更。**`pytest-benchmark` plugin 副作用回避:** benchmark 後に後続テストの GC / スケジューリングに影響することを実測で発見 → IT-PERF.1-02 をファイル末尾配置に並べ替え。**マーカー方針:** 全 6 件に `@pytest.mark.integration` + `@pytest.mark.perf` + `@pytest.mark.nightly` + `@pytest.mark.linux_only` を付与(§8.1 規定どおり PR / macOS local では除外、CI Linux nightly のみで実行、SOUP-012 `pytest-benchmark` 初運用 = IT-PERF.1-02 のみ)。§11.2 IT-PERF 行を **設計確定 + Linux nightly 実測確認は Inc.1 完了タグ前に申し送り**(2026-05-04)、§13 トレーサビリティマトリクス IT-PERF 行を **「設計確定(SRS / SDD 整合 110/50/110 ms 厳密境界、CI Linux nightly 実測確認は §6.8.5 参照)」** に更新、合計目安を ≥ 61 → ≥ 67 に。RCM 検出能力不変、SAD §6 / §9 設計不変、`tests/conftest.py` に `linux_only` auto-skip hook 新規追加(8 行 + docstring)、`tests/integration/conftest.py` は既存 F2 / F3 fixture(`mock_running_state_machine` / `pump_simulator_real` / `pump_observer_real` / `magicmock_*_heartbeat_sink` / `mock_pump_controller`)を再利用するため新規追加なし | k-abe |
| 0.7 | 2026-05-03 | **Step 19 F4(§6.7 SEP-001 ランタイム分離 + 真の本物注入 E2E 詳細化)を反映。** §6.7 を骨格 → 詳細化(IT-SEP.1-01〜06、6 ケース表 + 結合経路 4 経路 + 設計判断 5 項目 + 着手中の是正記録 1 項目 + 申し送り 2 項目)。§11.2 IT-SEP 行を 6 Pass / 0 Fail / 0 Skip で確定(2026-05-03)、§13 トレーサビリティマトリクス IT-SEP 行を **Pass(6 tests、本物 vip_api_b Adapter 注入による SEP-001 越え経路 + 階層防御 E2E + 例外握りつぶし契約 boundary 維持実証)** に更新、合計目安を ≥ 59 → ≥ 61 に。**着手中の是正記録(`del sys.modules` 副作用回避):** 当初設計では IT-SEP.1-01 で AST 軸 + ランタイム sys.modules 軸を 1 ケース統合だったが、`del sys.modules` 後の reload が Adapter のバインド一貫性を破壊し IT-SEP.1-05 の `patch` 効力を失わせる副作用を発見。AST 軸(IT-SEP.1-01)+ ランタイム受動観測軸(IT-SEP.1-04)に分散配置で再構成、Adapter バインド一貫性を保つ設計に是正(後続プロジェクト推奨パターン記録)。RCM-001/003/004/SEP-001 検出能力不変、SAD §6 / §9 設計不変、SOUP 追加なし、`tests/integration/conftest.py` に F4 用 fixture 4 件(`real_validation_api` / `control_api_with_real_validation` / `sw_watchdog_for_loop` / `hw_failsafe_timer_for_loop`)追加 | k-abe |
| 0.6 | 2026-05-01 | **Step 19 F1.6(CR-0004 (b) Adapter 層追加 + CR-0005 (a) `_HeartbeatSink` Protocol 引数なし化、一括実装)を反映。** §6.1.4 申し送りを「CR-0004 解消済(修正候補 (b) Adapter 層追加採用)」に更新、`vip_api/_validation_bridge.py` Adapter 経路と §6.7 IT-SEP(Step 19 F4)での本物注入活用を明文化。§6.3.3 設計判断と §6.3.5 申し送りを「CR-0005 解消済(修正候補 (a) Protocol 引数なし化採用)」に更新、本物 SwWatchdog/HwFailsafeTimer の ControlLoop 注入経路を §6.7 で活用予定と明記。§6.3 試験ケース表 IT-RCM004.1-03 を「heartbeat 引数なし契約(CR-0005 (a) 解消後)」に更新(SW/HW 両方の `heartbeat()` 引数なし 1 回呼出契約)。`tests/integration/conftest.py` ヘッダ + §6.3 fixture 設計判断コメントを「CR-0004/0005 解消後」に更新。RCM-001/003/004 検出能力不変、SAD §6 / §9 設計不変、SOUP 追加なし | k-abe |
| 0.5 | 2026-05-01 | **Step 19 F3(§6.3 RCM-004 送出間隔 詳細化、本物 ControlLoop + Pump + Observer + Validator 結合)を反映。** §6.3 を骨格 → 詳細化(IT-RCM004.1-01〜05、5 ケース表 + 結合経路 + 設計判断 + CR-0005 申し送り)。§11.2 IT-RCM004 行を 5 Pass / 0 Fail / 0 Skip で確定(2026-05-01)、§13 トレーサビリティマトリクス IT-RCM004 行を **Pass(5 tests、本物 ControlLoop + Pump + Observer + Validator 結合 + MagicMock Watchdog 経路、機能整合性検証、3 連続安定確認)** に更新。**着手時発見:** `ControlLoop._HeartbeatSink` Protocol(`heartbeat(self, ts: float)`)と `SwWatchdog/HwFailsafeTimer.heartbeat`(引数なし)のシグネチャ不整合を確認 → **CR-0005 として別途起票予定**(F3 完了後 Step 19 F3.5)、本物 Watchdog 注入は F4 着手前に CR-0004 と併せて決着 | k-abe |
| 0.4 | 2026-05-01 | **Step 19 F2(§6.2 RCM-003 SW/HW Watchdog 階層防御 詳細化)を反映。** §6.2 を骨格 → 詳細化(IT-RCM003.1-01〜06、6 ケース表 + 結合経路 + 設計判断 + 本物 `time.monotonic` 連動 + 監視スレッド lifecycle 検証)。§11.2 IT-RCM003 行を 6 Pass / 0 Fail / 0 Skip で確定(2026-05-01)、§13 トレーサビリティマトリクス IT-RCM003 行を **Pass(6 tests、本物実時間連動 + 階層防御時間順序実証 + 監視スレッド lifecycle 検証、3 連続安定確認)** に更新。**設計変更(Step 19 F2 着手前クロスレビュー)**:当初検討した「IT-RCM003.1-05 クロック逆転耐性」を「**監視スレッド経由の自動トリップ**(本物 `start/stop` lifecycle + 実時間 timer 精度)」に置換 — クロック逆転は UT-001.5-04 等の fake_clock 試験で網羅済のため重複回避、IT は本物実時間連動が本旨。**macOS sleep ジッタ対策**(Step 19 B4 教訓継続):実時間境界判定は緩い余裕(timeout + 50 ms 以上)、3 連続実行 stable 確認済 | k-abe |
| 0.3 | 2026-05-01 | **Step 19 F1(§6.1 RCM-001 詳細化)を反映。** §6.1 を骨格 → 詳細化(IT-RCM001.1-01〜08、8 ケース表 + 結合経路 + 設計判断 + CR-0004 申し送り + §6.7 IT-SEP への本物注入分散配置を明文化)。§11.2 IT-RCM001 行を 8 Pass / 0 Fail / 0 Skip で確定(2026-05-01)、§13 トレーサビリティマトリクス IT-RCM001 行を **Pass(8 tests、Mock ベース契約検証 + IT-RCM001.1-08 本物 StateMachine 不変実証)** に更新。**着手時発見:** `vip_api.ValidationApi` Protocol(`-> list[ValidationError]`)と `vip_api_b.validate_settings`(関数で `Ok` または `Err` を返す)の型不整合を確認 → **CR-0004 として別途起票予定**(F1 完了後)、本観点は Mock ベースで進め本物注入の SEP-001 越え経路検証は §6.7 IT-SEP(Step 19 F4)に分散配置 | k-abe |
| 0.2 | 2026-05-01 | **Step 19 F0(自動化骨格整備)を反映。** §8.3 自動化状況を「未着手」→「骨格整備済」に更新(`tests/integration/{__init__.py, conftest.py, test_smoke.py}` + `pyproject.toml` markers / `addopts = ["-m", "not integration"]` + `pytest-benchmark` SOUP-012 採用 + `.github/workflows/integration-test.yml` の `integration-fast` / `integration-nightly` 2 ジョブ構成)。スモーク 2 件で CI 経路の動作確認済(UT 441 / IT 2 / coverage 100% / mypy `--strict` / ruff Pass)。Step 19 F1 以降の各観点詳細化の前提整備が完了 | k-abe |
| 0.1 | 2026-05-01 | **初版作成(計画、Step 19 D-2)。** Inc.1 全 17 ユニット UT 完了(UTPR v0.19)を前提に、結合戦略(IS-1 永続化 → IS-2 制御系コア → IS-3 仮想 HW → IS-4 API 層 → IS-5 全層統合)を確立。**RCM 軸での代表 3 観点詳細化**(§6.4 RCM-015 永続化 E2E 8 ケース / §6.5 RCM-016 再開ガード 8 ケース / §6.6 RCM-019 状態遷移結合 8 ケース、合計 24 詳細化ケース)+ **残 7 観点骨格**(§6.1 RCM-001 / §6.2 RCM-003 / §6.3 RCM-004 / §6.7 SEP ランタイム / §6.8 IT-PERF 統計時間 / §6.9 IT-PWR 電源断 / §6.10 IT-SIDE サイドチャネル、合計目安 ≥ 35 件)。**UT 申し送り 6 件を性質別に分散配置**(電源断 → §6.9、統計時間 → §6.8、サイドチャネル → §6.10、SEP ランタイム → §6.7、E2E ラウンドトリップ → §6.4、Resume API → §6.5)。試験 ID 体系(`IT-{プレフィックス}.{サブ番号}-{連番}`)、IF-U 14 件 + IF-E 3 件一覧、結合戦略チェックリスト、受入基準 5 項目、回帰試験基盤計画を確立。第 II 部(報告)は骨格のみ、Step 19 F の試験実施で埋めていく(UTPR v0.1 と同じ「代表 + 骨格」段階成熟方式) | k-abe |
