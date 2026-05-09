# ソフトウェアアーキテクチャ設計書

**ドキュメント ID:** SAD-VIP-001
**バージョン:** 0.2
**作成日:** 2026-04-18
**最終更新日:** 2026-05-09
**対象製品:** 仮想輸液ポンプ(Virtual Infusion Pump) / VIP-SIM-001
**対象ソフトウェアバージョン:** 0.2.0(Inc.2 範囲、アラーム管理を含む)
**安全クラス:** C(IEC 62304)

| 役割 | 氏名 | 所属 | 日付 | 署名 |
|------|------|------|------|------|
| 作成者 | k-abe | — | 2026-05-09 | |
| レビュー者 | — | — | — | |
| 承認者 | — | — | — | |

> **本プロジェクトの位置づけ(注記)**
> 本ドキュメントは IEC 62304 に基づく医療機器ソフトウェア開発プロセスの学習・参考実装を目的とした **仮想プロジェクト** の成果物である。本 SAD は V字モデル(インクリメンタル方式)に従い、v0.1 で **Inc.1(流量制御コア)範囲のアーキテクチャを確定**、v0.2 で **Inc.2(アラーム管理)範囲を追補**(本改訂、CR-0011 / Step 20 D)する。Inc.3〜4 範囲のアーキテクチャ要素(用量計算・UI・ロギング本実装)は、各インクリメント開始時に本書を改訂して追補する。

---

## 1. 目的と適用範囲

本書は、SRS-VIP-001 v0.3 に定められた Inc.1〜2 範囲の要求事項を実現するためのソフトウェアアーキテクチャを IEC 62304 箇条 5.3 に基づいて定義する。本書で定義するアーキテクチャは以下の判断の基礎となる:

- 詳細設計(SDD、箇条 5.4)
- ユニット試験計画(箇条 5.5)
- 結合試験計画(箇条 5.6)
- システム試験計画(箇条 5.7)
- 分離設計による項目別安全クラスの決定(§5.3.5)
- SOUP の選定と要求事項指定(§5.3.3 / §5.3.4)

## 2. 参照文書

| ID | 文書名 | バージョン |
|----|--------|----------|
| [1] | IEC 62304:2006+A1:2015 箇条 5.3 | — |
| [2] | ISO 14971:2019 | — |
| [3] | ソフトウェア要求仕様書(SRS-VIP-001) | 0.3(Inc.2 SRS 追補確定、CR-0008 / Step 20 B-2) |
| [4] | ソフトウェア開発計画書(SDP-VIP-001) | 0.1 |
| [5] | ソフトウェア安全クラス決定記録(SSC-VIP-001) | 0.1 |
| [6] | リスクマネジメントファイル(RMF-VIP-001) | 0.4(HZ-009 識別済 + RCM-006/009/010/011/012 Designed、CR-0010 / Step 20 C) |
| [7] | ソフトウェアリスクマネジメント計画書(SRMP-VIP-001) | 0.2 |
| [8] | 構成アイテム一覧(CIL-VIP-001) | 0.49(本 SAD v0.2 連動) |
| [9] | Inc.2 範囲計画書(INC2-SCOPE-VIP-001) | 0.1(Step 20 A 新設、本 SAD 改訂計画は §6) |
| [10] | IEC 60601-1-8(アラームシステム) | — |

## 3. ソフトウェア要求事項のソフトウェアアーキテクチャへの変換(箇条 5.3.1)

SRS の Inc.1〜2 範囲全 要求事項を、本書で定義するアーキテクチャ要素(ソフトウェア項目 ARCH-NNN)に割付ける。割付けは §11 トレーサビリティマトリクスで網羅性を検証可能とする。割付けの原則:

1. **単一責務**: 各 ARCH は原則 1 つの機能領域に責任を持つ(制御コア / 仮想 HW / 永続化 / 検知 / アラーム通知 等)。
2. **安全クリティカル分離**: RCM を実装する項目と非 RCM 項目を可能な限り分離し、§9 で分離根拠を明示する。
3. **テスタビリティ**: 項目間 I/F は依存性注入(DI)で差し替え可能にし、仮想 HW や永続化をテスト用スタブに置換できるようにする。
4. **インクリメンタル追補**: Inc.3〜4 で追加する項目(用量計算・UI・ロギング本実装)が既存項目に破壊的変更を強いない契約を設計する(SRS-IF-004/020 のスタブ戦略)。Inc.2 で SRS-IF-010(アラーム I/F)+ SRS-I-040(仮想 HW イベント注入)+ SRS-O-040(アラーム通知)を **スタブ → 本実装** に発展させた事実は §4.3 / §5 / §11 に明示する。

## 4. ソフトウェアアーキテクチャの概要

### 4.1 アーキテクチャ方針

- **スタイル:** レイヤード + イベント駆動の複合
  - **レイヤード**: 外部 API → 制御コア → 仮想ハードウェアの 3 レイヤ構造に加え、Inc.2 で **検知層 → アラーム通知層** を追補
  - **イベント駆動**: 制御コマンド(START/STOP/PAUSE/RESUME/CONFIRM_RESUME)+ Inc.2 で追加する **アラーム確認・消音操作(`acknowledge` / `silence`)** はイベントとしてキューイング、制御ループ(100 ms サイクル)は定期駆動。Inc.2 で追加する **検知ループ**(検知群 ARCH-006)は制御ループから独立した周期で動作し、検知時に Alarm Reporter(ARCH-007)へ単方向通知する
- **採用理由:**
  - レイヤードは IEC 60601 系機器で広く採用され、監査対応が容易
  - イベント駆動は制御ループとコマンド処理の時間的デカップリングに適合(SRS-P02 ジッタ要件・SRS-P06 非ブロッキング要件を同時に満たす)
  - Inc.2(アラーム)・Inc.4(UI)の追加時も、最上位 API 層 + 検知層 + アラーム通知層にアダプタを追加するだけで済む(本 v0.2 で Inc.2 範囲を実証)
  - Inc.2 アラーム機能は **IEC 60601-1-8** に基づき、優先度分類(高/中/低)+ テクニカル/生理アラーム区分 + §6.4 確認・休止規定 を ARCH-007(UNIT-007.2 Priority Classifier)で集約実装

### 4.2 全体構成図(Inc.1〜2 範囲)

```
      外部呼び出し元(試験ハーネス / 将来の Inc.4 UI)
                        │
                        ▼
      ┌─────────────────────────────────────────────┐
      │ ARCH-005: Public API Facade                  │
      │  ├─ 005.1 Control API (start/stop/pause/     │
      │  │        resume/reset/confirm_resume +       │
      │  │        acknowledge_alarm/silence_alarm)    │
      │  ├─ 005.2 State Observer API (read-only)     │
      │  └─ 005.3 Validation API (pure function)     │
      └─────────────────────────────────────────────┘
          │              │                      ▲
          │              │ (observe)            │ (validate: 副作用なし)
          ▼              │                      │
      ┌─────────────────────────────────────────────┐
      │ ARCH-001: Control Core (クラス C)             │
      │  ├─ 001.1 State Machine (RCM-019)            │
      │  │       + アラーム発報経路 + ACK/SILENCE 状態  │
      │  ├─ 001.2 Control Loop (100 ms、RCM-004 HB) │
      │  ├─ 001.3 Command Handler                    │
      │  ├─ 001.4 Flow Cmd Validator (RCM-001)       │
      │  └─ 001.5 Watchdog (RCM-003)                 │
      └─────────────────────────────────────────────┘
          │ (flow cmd / observe)          │ (save/load)
          │                                │
          │       ┌───────────── (alarm event) ─────────┐
          │       │                                      │
          ▼       │                                      ▼
      ┌──────────────────────┐    ┌──────────────────────┐
      │ ARCH-002: Virtual    │    │ ARCH-003:           │
      │ Hardware (クラス C)  │    │ Persistence (C)      │
      │ ├─ 002.1 Pump Sim    │    │ ├─ 003.1 Serializer │
      │ ├─ 002.2 Observer    │    │ ├─ 003.2 Checksum   │
      │ ├─ 002.3 Event Inj   │    │ │        (SRS-SEC)  │
      │ │   (BATTERY_LOW 含)  │    │ └─ 003.3 Atomic Wr  │
      │ └─ 002.4 HW-side FS  │    └──────────────────────┘
      │    Timer (RCM-004)   │             ▲
      └──────────────────────┘             │ (load)
          │ (sensor input)                  │
          ▼                          ┌────────────────────────────────┐
      ┌─────────────────────────┐   │ ARCH-004: Boot / Recovery (C)  │
      │ ARCH-006: Detection (C) │   │  ├─ 004.1 Integrity Validator  │
      │ (Inc.2 新設)            │   │  │        (RCM-015)            │
      │  ├─ 006.1 Occlusion     │   │  └─ 004.2 Resume Confirmation  │
      │  │        (RCM-009)     │   │           Gate (RCM-016)       │
      │  ├─ 006.2 Air-Bubble    │   └────────────────────────────────┘
      │  │        (RCM-010)     │
      │  ├─ 006.3 Reservoir     │
      │  │        Empty(RCM-006) │
      │  ├─ 006.4 Alarm Task    │
      │  │        Watchdog(RCM-011)
      │  ├─ 006.5 Alarm Path    │
      │  │        Redundancy(RCM-012)
      │  └─ 006.6 Battery Low   │
      │           (RCM-006、HZ-009)
      └─────────────────────────┘
            │ (report_alarm)
            ▼
    --- 分離境界(SEP-002/003)以下は低安全クラス候補 ---
      ┌────────────────────────┐    ┌──────────────────────┐
      │ ARCH-007: Alarm        │    │ ARCH-009: Logging    │
      │ Reporter (B、Inc.2     │    │ Stub I/F (B候補、    │
      │ 本実装)                │    │ 旧 ARCH-006、Inc.4 で│
      │ ├─ 007.1 Reporter Core │    │ 本実装)              │
      │ │  (SRS-IF-010 本実装) │    └──────────────────────┘
      │ └─ 007.2 Priority      │
      │    Classifier          │
      │    (IEC 60601-1-8 §6.1)│
      └────────────────────────┘
```

**図の凡例(v0.2 改訂点):**

- **新設項目(Inc.2、CR-0011 / Step 20 D):** ARCH-006 Detection 検知群(クラス C、6 ユニット)、ARCH-007 Alarm Reporter 本実装(クラス B、2 ユニット)
- **拡張項目(Inc.2):** UNIT-001.1 State Machine にアラーム発報経路 + 確認 / 消音状態遷移を追加、UNIT-002.3 Event Injection は no-op スタブから `BATTERY_LOW` enum 追加 + Pump 伝播経路を実装する方針(本 SAD では設計確定、実装は Step 20 X〜の TDD)、UNIT-005.1 Control API に `acknowledge_alarm` / `silence_alarm` 追加
- **ID リネーム:** SAD v0.1 の `ARCH-006 Logging Stub I/F` を `ARCH-009` にリネーム(Inc.4 で本実装予定、機能内容は不変)。ARCH-006 を Detection 検知群へ再割当て。Inc.3 用量計算 = ARCH-008(維持)、Inc.4 UI = ARCH-010(新規予約)
- **データフロー:** Pump → 検知群(センサー入力)、検知群 → Alarm Reporter(`report_alarm`)、検知群 → State Machine(状態遷移依頼、ERROR / PAUSED)、Control API ↔ Alarm Reporter(`acknowledge` / `silence`)。検知群はクラス C、Alarm Reporter は SEP-003 でクラス B 維持(通知 I/F が単方向出力 + frozen 値型渡し)

### 4.3 ソフトウェア項目一覧

#### 4.3.1 Inc.1 範囲の ARCH 項目

| 項目 ID | 名称 | 分類 | 安全クラス(分離後) | 概要 | 主担当 SRS |
|---------|------|------|-------------------|------|-----------|
| ARCH-001 | Control Core | 項目 | C | 流量制御の中核。状態機械・制御ループ・コマンド処理・範囲チェック・WDT。**Inc.2 で UNIT-001.1 にアラーム発報経路 + 確認 / 消音状態遷移を追加**(下記 §4.3.2 参照)| SRS-010〜014, 020, RCM 全般 |
| ARCH-001.1 | State Machine | ユニット | C | 状態遷移表の強制、不正遷移の拒否(RCM-019)。**Inc.2 拡張**:アラーム発報経路 + ACK / SILENCE 状態遷移(SRS-044、SRS-ALM-008、IEC 60601-1-8 §6.4)| SRS-020, SRS-RCM-020, **SRS-044(Inc.2)** |
| ARCH-001.2 | Control Loop | ユニット | C | 100ms サイクルで流量指令発行、積算量更新、ハートビート送出 | SRS-011, SRS-P02, RCM-004 |
| ARCH-001.3 | Command Handler | ユニット | C | 外部コマンドをキュー受信し、妥当性を検証して状態機械に渡す。**Inc.2 拡張**:`acknowledge` / `silence` コマンドの受け渡し | SRS-010/013/014, **SRS-044(Inc.2)** |
| ARCH-001.4 | Flow Command Validator | ユニット | C | 流量指令値の範囲・設定値一致を検証(RCM-001) | SRS-O-001, SRS-RCM-001 |
| ARCH-001.5 | Watchdog | ユニット | C | 制御ループのハートビート監視、タイムアウト時に ERROR 遷移 | SRS-RCM-003 |
| ARCH-002 | Virtual Hardware | 項目 | C | 仮想ポンプ機構のシミュレーション。実機代替として注入実行・状態観測・フェイルセーフ | SRS-030/031/032 |
| ARCH-002.1 | Pump Simulator | ユニット | C | 流量指令に応じた積算量・流量を時間進行でシミュレート。**Inc.2 拡張**:検知群(ARCH-006)へのセンサー入力提供 | SRS-030, **SRS-040〜043(Inc.2)** |
| ARCH-002.2 | Pump Observer | ユニット | C | 現在流量・積算量・経過時間・機構状態を読み取り公開 | SRS-031 |
| ARCH-002.3 | Event Injection | ユニット | C | 閉塞・気泡・薬液切れ・**バッテリ低下**(Inc.2 で `BATTERY_LOW` 追加)のイベント注入 I/F。**v0.2 で no-op 解除方針確定**:`VirtualHwEventKind` enum を 4 種に拡張 + Pump への伝播経路を実装(SDD §4.11.C で予告済、本 SAD で正式確定、実装は Step 20 X〜の TDD) | SRS-032, **SRS-I-040(Inc.2 で確定)** |
| ARCH-002.4 | HW-side Failsafe Timer | ユニット | C | ハートビート途絶(500 ms)で仮想ポンプ側から流量 0 へ自発停止 | SRS-RCM-004 |
| ARCH-003 | Persistence | 項目 | C | 設定・状態・積算量の永続化と整合性担保 | SRS-025, SRS-SEC-001 |
| ARCH-003.1 | Serializer | ユニット | C | JSON ベースのスキーマ付きシリアライズ/デシリアライズ | SRS-DATA-001/004 |
| ARCH-003.2 | Checksum Verifier | ユニット | C | SHA-256 チェックサムの生成・検証 | SRS-SEC-001 |
| ARCH-003.3 | Atomic File Writer | ユニット | C | temp → rename パターンの atomic 書き込み、1 世代バックアップ | SRS-DATA-002/003 |
| ARCH-004 | Boot / Recovery | 項目 | C | 起動時の整合性検証と状態復元、中断注入の再開確認ゲート | SRS-026〜028 |
| ARCH-004.1 | Integrity Validator | ユニット | C | チェックサム・値域・状態組合せの整合性検証、失敗時フェイルセーフ(RCM-015) | SRS-027, SRS-RCM-015 |
| ARCH-004.2 | Resume Confirmation Gate | ユニット | C | 中断注入の自動再開を禁止し `confirm_resume(token)` を待つ(RCM-016) | SRS-028, SRS-RCM-016 |
| ARCH-005 | Public API Facade | 項目 | C(分離後 005.3 のみ B 候補) | 外部呼出しへのファサード。Inc.4 UI / 試験ハーネスからの入口 | SRS-I-010, SRS-O-010 |
| ARCH-005.1 | Control API | ユニット | C | 制御コマンドを Command Handler に転送、同期応答。**Inc.2 拡張**:`acknowledge_alarm(alarm_id)` / `silence_alarm(alarm_id, duration_sec)` を ARCH-007 へ転送(IEC 60601-1-8 §6.4 準拠)| SRS-010〜014, SRS-IF-002, **SRS-IF-010(Inc.2)** |
| ARCH-005.2 | State Observer API | ユニット | C(読み取り専用、副作用なし) | 現在状態のスナップショット取得、idempotent | SRS-O-010, SRS-IF-003, SRS-UX-002 |
| ARCH-005.3 | Validation API | ユニット | **B**(分離、純粋関数) | 設定値の妥当性検証のみ、状態変更なし | SRS-UX-001 |

#### 4.3.2 Inc.2 範囲で追加・拡張される ARCH 項目(本 v0.2 で新設・確定、CR-0011 / Step 20 D)

**設計判断の要約:** Inc.2 範囲では (i) **検知層 ARCH-006**(クラス C 維持、6 ユニット)を新設、(ii) **アラーム通知層 ARCH-007**(クラス B 維持、SEP-003 で分離継続、2 ユニット)を本実装化、(iii) **既存 UNIT-001.1 / UNIT-001.3 / UNIT-002.1 / UNIT-002.3 / UNIT-005.1 を拡張**。検知ロジックはクラス C(状態遷移と直結する安全機能)、通知 I/F のみクラス B(単方向出力 + frozen 値型渡し)とする分離は IEC 60601-1-8(アラーム機能はクラス C 相当)との整合確認済(§9.2 SEP-003 で詳細化)。

| 項目 ID | 名称 | 分類 | 安全クラス(分離後) | 概要 | 主担当 SRS |
|---------|------|------|-------------------|------|-----------|
| ARCH-006 | Detection(検知群)| 項目 | **C**(SEP-001 違反なし) | Inc.2 で新設。閉塞・気泡・薬液切れ・バッテリ低下の各検知 + アラームタスク監視 + アラーム発報路冗長化を集約。Pump からのセンサー入力を受け、検知時に Alarm Reporter(ARCH-007)へ単方向通知し、必要に応じて State Machine(UNIT-001.1)へ ERROR / PAUSED 遷移を依頼 | SRS-040〜043, SRS-RCM-006/009/010/011/012, HZ-004/005/009 |
| ARCH-006.1 | Occlusion Detector | ユニット | C | **冗長 2 系統(独立センサー入力)** に基づく閾値判定で閉塞を検知。片系故障時のフェイルセーフ確保(RCM-009)。検知時は SRS-ALM-004 を Alarm Reporter 経由で発報 | SRS-040, SRS-RCM-009, SRS-ALM-004 |
| ARCH-006.2 | Air-Bubble Detector | ユニット | C | **多段判定**(警告閾値 + 危険閾値、各段独立判定)で気泡を検知(RCM-010)。危険閾値超過時は SRS-ALM-005 を発報 | SRS-041, SRS-RCM-010, SRS-ALM-005 |
| ARCH-006.3 | Reservoir Empty Detector | ユニット | C | 残量センサー入力の閾値判定で薬液切れを検知。SRS-ALM-006(中優先度・テクニカル)を発報、PAUSED 遷移を State Machine へ依頼 | SRS-042, SRS-RCM-006, SRS-ALM-006 |
| ARCH-006.4 | Alarm Task Watchdog | ユニット | C | アラームタスクの実行を監視し、デッドロック・タスク停止を **1 秒以内に検知**(RCM-011)。検知時は ERROR 状態遷移 + 独立アラーム発報路(ARCH-006.5 経由 RCM-012)で発報を試みる | SRS-044, SRS-RCM-011 |
| ARCH-006.5 | Alarm Path Redundancy | ユニット | C | アラーム発報路の **主系 / 予備系の冗長化**(RCM-012)。主系故障時(発報路故障・タスク停止)に予備系で発報を継続。両系故障時は ERROR 遷移 + 制御停止 | SRS-RCM-012, SRS-IF-010 |
| ARCH-006.6 | Battery Low Detector | ユニット | C | 電源電圧 / バッテリ残量センサー入力の閾値判定でバッテリ低下を検知。SRS-ALM-007(中優先度・テクニカル)を発報。**HZ-009 対応**(RMF v0.4 で識別)。安全側遷移ロジック(RCM-020 候補)は SRS への正式登録を Step 20 B-3 候補として申し送り中で、本 SAD では「閾値超過時に State Machine へ通知 + Alarm Reporter 経由で発報」までを設計確定 | SRS-043, SRS-RCM-006, SRS-ALM-007, HZ-009 |
| ARCH-007 | Alarm Reporter | 項目 | **B**(SEP-003 で分離継続、本実装後も維持) | Inc.2 で本実装化(v0.1 ではスタブ)。アラーム通知の単方向出力 I/F + IEC 60601-1-8 §6.1 優先度分類 + §5.1.4 テクニカル / 生理アラーム区分 + §6.4 アラーム確認・休止規定 を集約 | SRS-IF-010, SRS-O-040, SRS-ALM-001/004〜008, SRS-REG-002 |
| ARCH-007.1 | Alarm Reporter Core | ユニット | B | `AlarmReportInterface` の本実装(`report_alarm` + `acknowledge` + `silence`)。`AlarmEvent`(frozen 値型)を入力に受け、副作用なしの一方向出力(現状はログ + 内部キュー、Inc.4 で UI / 通知装置へ拡張予定)。検知群からの呼出 + Control API からの ack/silence 呼出を併合 | SRS-IF-010, SRS-ALM-001/004〜008, SRS-O-040 |
| ARCH-007.2 | Alarm Priority Classifier | ユニット | B | IEC 60601-1-8 §6.1 優先度判定(高 / 中 / 低)+ §5.1.4 テクニカル / 生理区分判定。検知群からの `cause_code` を入力に受け、`AlarmPriority` + `AlarmCategory` を決定する純粋関数 | SRS-REG-002, SRS-ALM-004〜008 |
| ARCH-009 | Logging Stub I/F | 項目 | **B**(分離候補、Inc.4 で本実装) | **v0.2 で旧 ARCH-006 をリネーム**。構造化ログ I/F。読み取り側への一方向出力のみ。本実装(構造化ログ + 配布)は Inc.4 で実施、本 v0.2 では Inc.1 と同じスタブ I/F を維持 | SRS-021, SRS-IF-004, SRS-OPS-010 |

**備考(v0.2 改訂時点):**

- **ARCH ID リネーム履歴:** SAD v0.1 の `ARCH-006 Logging Stub I/F` を本 v0.2 で `ARCH-009` にリネーム(理由:Inc.2 で検知群を ARCH-006 に集約する判断 = INCREMENT_PLANS / RMF v0.4 / CRR v0.12 の前提と整合)。**ARCH-009 の機能内容は不変**(Inc.4 で本実装、構造化ログ I/F)。
- **将来予約 ID:** Inc.3 用量計算 = ARCH-008(維持)、Inc.4 UI = **ARCH-010**(新規予約、v0.1 ではこの位置に ARCH-009 と書いていたが本 v0.2 で番号繰下げ)。
- **ARCH-006 / ARCH-007 の Inc.1 → Inc.2 推移:** v0.1 では ARCH-006(現 ARCH-009)= Logging スタブ、ARCH-007 = Alarm Reporter スタブのみだったが、v0.2 で ARCH-006 = Detection 検知群を新設 + ARCH-007 = Alarm Reporter 本実装に発展。
- **既存 RCM(Inc.1 範囲、6 件)の状態:** 本 v0.2 改訂で実装変更なし(Step 19 H3 で Verified 状態に到達済、Inc.1 完了タグ `v0.1.0-inc1` 付与済)。
- **新規 RCM(Inc.2 範囲、5 件):** RCM-006(発報必達、UNIT-007.1)/ RCM-009(冗長検知、UNIT-006.1)/ RCM-010(多段検知、UNIT-006.2)/ RCM-011(タスク監視、UNIT-006.4)/ RCM-012(発報路冗長、UNIT-006.5)を本 SAD で **設計レベルでの実装先確定** = RMF v0.4 の `Designed` 状態と整合。
- **継続申し送り:** Inc.3 で用量計算 ARCH-008 を追加予定、Inc.4 で UI 層 ARCH-010 + ロギング実装 ARCH-009 本体を追加予定。RCM-020 候補(HZ-009 対応、バッテリ管理ロジック / 安全側遷移)の SRS 正式登録は Step 20 B-3 候補として申し送り、本 v0.2 では UNIT-006.6 + ARCH-007 経由のアラーム発報まで設計確定。

## 5. ソフトウェア項目間のインタフェース(箇条 5.3.2)

### 5.1 内部 I/F + 外部 I/F 一覧(Inc.1〜2 範囲)

| IF ID | 呼出側 | 被呼出側 | 種別 | 仕様概要 | 関連 SRS |
|-------|--------|---------|------|---------|---------|
| IF-U-001 | ARCH-005.1 Control API | ARCH-001.3 Command Handler | 関数呼出(同期) | `enqueue_command(cmd: Command) -> Result` | SRS-I-010 |
| IF-U-002 | ARCH-001.2 Control Loop | ARCH-002.1 Pump Simulator | 関数呼出(同期) | `set_flow_rate(value: Decimal) -> None`(バリデータ経由) | SRS-O-001 |
| IF-U-003 | ARCH-001.2 / ARCH-005.2 | ARCH-002.2 Pump Observer | 関数呼出(同期) | `observe() -> PumpSnapshot`(idempotent) | SRS-I-020, SRS-O-010 |
| IF-U-004 | ARCH-001.1 State Machine | ARCH-003 Persistence | 関数呼出(非同期 / キュー) | `save_async(state: RuntimeState) -> None`(≤ 1 秒サイクル、SRS-P06 のため非ブロック) | SRS-025 |
| IF-U-005 | ARCH-004.1 Integrity Validator | ARCH-003 Persistence | 関数呼出(同期、起動時のみ) | `load() -> PersistedRecord \| LoadError` | SRS-026 |
| IF-U-006 | ARCH-004 Boot | ARCH-001.1 State Machine | 関数呼出(起動時のみ) | `initialize(initial_state: RuntimeState, needs_confirm: bool) -> None` | SRS-027/028 |
| IF-U-007 | ARCH-006 Detection / ARCH-001.1 State Machine | ARCH-007.1 Alarm Reporter Core | I/F(単方向通知) | `report_alarm(event: AlarmEvent) -> None`(**v0.2 でシグネチャ確定**、§5.2 参照、Inc.2 で本実装、Inc.1 までは no-op) | SRS-ALM-001, SRS-O-040, SRS-IF-010 |
| IF-U-008 | 全 ARCH-001〜007 | ARCH-009 Logging Stub | I/F(単方向出力) | `log(record: LogRecord) -> None`(本版は no-op、Inc.4 で本実装) | SRS-021, SRS-O-030 |
| IF-U-009 | ARCH-001.5 Watchdog | ARCH-001.1 State Machine | 関数呼出(非同期) | `trigger_error(reason: WatchdogReason) -> None` | SRS-RCM-003 |
| IF-U-010 | ARCH-001.2 Control Loop | ARCH-001.5 Watchdog | 関数呼出(同期) | `heartbeat(ts: Monotonic) -> None`(サイクルごと) | SRS-RCM-003/004 |
| IF-U-011 | ARCH-001.2 Control Loop | ARCH-002.4 HW-side FS Timer | 関数呼出(同期) | `heartbeat(ts: Monotonic) -> None`(サイクルごと、RCM-004) | SRS-RCM-004 |
| IF-U-012(**v0.2 新規**)| ARCH-006 Detection 各ユニット | ARCH-007.1 Alarm Reporter Core | I/F(単方向通知、IF-U-007 経由) | `report_alarm(event: AlarmEvent) -> None`(検知群からの主呼出経路、IF-U-007 と同じシグネチャ。検知群側で `cause_code` を生成し ARCH-007.2 Priority Classifier 経由で `AlarmEvent` を構築) | SRS-RCM-006, SRS-ALM-004〜007, SRS-IF-010 |
| IF-U-013(**v0.2 新規**)| ARCH-006 Detection 各ユニット | ARCH-001.1 State Machine | 関数呼出(非同期) | `request_state_transition(target: StateKind, reason: DetectionReason) -> None`(検知時の ERROR / PAUSED 遷移依頼。`DetectionReason` は `OCCLUSION` / `AIR_BUBBLE` / `RESERVOIR_EMPTY` / `BATTERY_LOW` / `ALARM_TASK_FAILURE` の sealed enum) | SRS-040〜043, SRS-RCM-006, SRS-RCM-011 |
| IF-U-014(**v0.2 新規**)| ARCH-005.1 Control API | ARCH-007.1 Alarm Reporter Core | 関数呼出(同期) | `acknowledge(alarm_id: str) -> None` / `silence(alarm_id: str, duration_sec: int) -> None`(IEC 60601-1-8 §6.4 確認・休止規定準拠、高優先度の消音時間制限あり)| SRS-044, SRS-ALM-008, SRS-IF-010 |
| IF-U-015(**v0.2 新規**)| ARCH-002.1 Pump Simulator / ARCH-002.3 Event Injection | ARCH-006 Detection 各ユニット | I/F(センサー入力受信、polling または callback) | `read_sensor(kind: SensorKind) -> SensorReading`(冗長 2 系統独立性 = SRS-RCM-009 の根拠 I/F、`SensorKind` は `OCCLUSION_PRIMARY` / `OCCLUSION_SECONDARY` / `AIR_BUBBLE_WARN` / `AIR_BUBBLE_CRITICAL` / `RESERVOIR` / `BATTERY` の sealed enum)| SRS-040〜043, SRS-I-040, SRS-RCM-009/010 |
| IF-E-001 | 外部(UI / 試験ハーネス) | ARCH-005 Public API | 外部 API | Python モジュール公開関数(`vip_ctrl.api.*`、Inc.2 で `acknowledge_alarm` / `silence_alarm` を追加)| SRS-IF-002/003, **SRS-IF-010(Inc.2)** |
| IF-E-002 | ARCH-003.3 Atomic Writer | OS ファイルシステム | OS システムコール | `os.rename`(POSIX atomic) | SRS-DATA-002 |

### 5.2 `AlarmEvent` 型構造の確定(IF-U-007 / IF-U-012、Inc.2 範囲、本 v0.2 で確定)

`AlarmEvent` は ARCH-006 Detection / ARCH-001.1 State Machine から ARCH-007.1 Alarm Reporter Core への単方向通知で渡される **frozen 値型**(SEP-003 分離契約に基づく不変性要求)。SRS-O-040 の正式構造として本 v0.2 で確定する。

| フィールド | 型 | 説明 | 由来 |
|---------|----|------|------|
| `alarm_id` | `str` | アラーム発生ごとに一意な識別子(`uuid4` ベース)。Acknowledge / Silence 時の対象指定に使用 | SRS-IF-010, SRS-044 |
| `priority` | `AlarmPriority`(enum: `HIGH` / `MEDIUM` / `LOW`) | IEC 60601-1-8 §6.1 優先度。ARCH-007.2 Priority Classifier が `cause_code` から決定 | SRS-REG-002, SRS-ALM-004〜007 |
| `category` | `AlarmCategory`(enum: `TECHNICAL` / `PHYSIOLOGICAL`) | IEC 60601-1-8 §5.1.4 区分。Inc.2 範囲の SRS-ALM-004〜008 はすべて TECHNICAL(機器自身の異常)| SRS-REG-002 |
| `occurred_at` | `float`(Unix epoch 秒、`time.monotonic` 系を併用検討) | アラーム発生時刻 | SRS-O-040 |
| `cause_code` | `str`(`"occlusion"` / `"air_bubble_critical"` / `"reservoir_empty"` / `"battery_low"` / `"alarm_task_failure"` / `"control_error"` 等の sealed 値)| 発報原因識別子。ARCH-007.2 が優先度・区分の決定根拠とする | SRS-O-040, SRS-RCM-006 |
| `metadata` | `Mapping[str, object]`(frozen) | 任意の補足情報(検知系統 ID、閾値超過量、計測値等)| SRS-O-040 |

**不変性契約:** `AlarmEvent` は `dataclasses.dataclass(frozen=True, slots=True)` で実装(SDD §5.1 で詳細化予定)、`metadata` も `MappingProxyType` でラップして **境界を越えた変更を禁止**(SEP-003 違反検知の機械的根拠)。

### 5.3 IEC 60601-1-8 §6.4 アラーム確認・休止の状態遷移(IF-U-014)

`acknowledge` / `silence` 呼出後の Alarm Reporter 側状態遷移は以下に従う(SRS-044 + IEC 60601-1-8 §6.4 整合):

- **ACTIVE**(発報中)→ **ACKED**(`acknowledge(alarm_id)` 受領、操作者が認知済、ただし原因が継続している間は表示継続)
- **ACTIVE** → **SILENCED**(`silence(alarm_id, duration_sec)` 受領、聴覚信号一時休止、視覚信号は継続。**高優先度アラームは消音時間 ≤ 120 秒 の制限**(IEC 60601-1-8 §6.4)を ARCH-007.1 が強制)
- **ACKED / SILENCED** → **CLEARED**(原因解消で自動クリア、または操作者の明示クリア)
- **SILENCED**(時間経過後)→ **ACTIVE**(原因継続なら自動再発報)

詳細状態遷移表は SDD §5.x(Step 20 E 骨格化で UNIT-007.1 詳細設計時に確定)。

## 6. SOUP の識別

Inc.1 範囲で実行時に使用する SOUP を識別する。開発ツール(pytest / ruff / mypy 等)は CIL §6 で管理し、ここでは運用成果物に組み込まれる SOUP のみを挙げる。

| SOUP ID | 名称 | バージョン | 用途 | 入手元 | ライセンス |
|---------|------|----------|------|--------|----------|
| SOUP-001 | CPython | 3.12.x(固定: uv.lock で特定マイナー) | Python 実行環境 | <https://www.python.org/>(公式バイナリまたはディストリビューション) | PSF |
| SOUP-002 | pydantic | 2.x 系最新(uv.lock で固定) | データバリデーション(SRS-004 一貫性検証、SRS-DATA-004 スキーマ検証、SRS-UX-001 Validation API) | <https://pypi.org/project/pydantic/> | MIT |

**SOUP 採用方針:**

- 本 Inc.1 では **実行時依存を最小化** する方針とし、標準ライブラリ(`decimal`, `hashlib`, `json`, `dataclasses`, `enum`, `threading`, `queue`)で代替可能なものは SOUP 扱いしない。
- Decimal(SRS-RCM-013 相当を Inc.3 で本格適用予定)・hashlib(SRS-SEC-001)・json(SRS-DATA-001)はすべて Python 標準ライブラリに含まれる。
- pydantic の採用は **SRS-UX-001**(Validation API を純粋関数として提供)と **SRS-RCM-020 間接支援**(入力境界で型を強制することで不正状態入力を早期拒否)のため。
- Inc.2 以降で SOUP 追加を検討する場合、本 SAD §6〜§8 を追補し RMF §4.3 の評価を実施する。

## 7. SOUP の機能的及び性能的要求事項の指定(箇条 5.3.3 ― クラス B, C)

| SOUP ID | 機能要求 | 性能要求 |
|---------|---------|---------|
| SOUP-001(CPython) | - PEP 484 型ヒントの標準準拠<br>- `decimal.Decimal` による IEEE 754 を使わない十進演算<br>- `threading` によるプリエンプティブ並行処理<br>- `hashlib.sha256` による暗号学的強度のハッシュ | - 制御ループ 100 ms サイクルを 10% 以内のジッタで実行できる GIL 下のタスクスケジューリング性能<br>- `threading.Event`/`queue.Queue` の待機解除遅延 ≤ 10 ms |
| SOUP-002(pydantic) | - フィールド型・範囲・制約の宣言的定義(`BaseModel`, `Field`)<br>- 入力バリデーション失敗時に例外として詳細情報を提供<br>- JSON シリアライズ/デシリアライズ(Decimal 対応)<br>- pure validation(副作用なし、スレッドセーフ) | - 単一モデルのバリデーションが制御ループサイクル(100 ms)に対し十分高速(1 ms 未満を目標)<br>- メモリフットプリント: 本ソフトウェアの運用メモリ要求(§8)に収まる |

**検証方法:**

- SOUP-001 の機能要求は、ユニット試験で標準ライブラリの想定動作を確認する契約試験で検証。
- SOUP-002 の機能要求は、Validation API(ARCH-005.3)のユニット試験で検証。境界値・異常系を網羅。
- 性能要求は結合試験(IT)で時間測定し合格判定する。
- 脆弱性は `pip-audit` で継続監視(SMP §7.1、SRS-SEC-003)。

## 8. SOUP に必要なシステム上のハードウェア及びソフトウェアの指定(箇条 5.3.4 ― クラス B, C)

| SOUP ID | 必要なハードウェア | 必要なソフトウェア | 根拠 |
|---------|------------------|-----------------|------|
| SOUP-001(CPython) | - 64 bit CPU(x86_64 または ARM64)<br>- RAM 最小 256 MB(本ソフトウェアの運用に対し十分な余裕)<br>- ストレージ: 永続化用に 10 MB 以上の書き込み可能領域 | - OS: macOS 13+ / Linux(kernel 5.x+、glibc 2.31+)/ Windows 10+。本プロジェクトでの動作検証対象は macOS / Linux。<br>- 時刻同期: `time.monotonic()` が利用可能な OS(POSIX 準拠または Windows) | 制御ループの時間要求(SRS-P02)、永続化書き込み(SRS-025)、並行処理(WDT)を満たすため |
| SOUP-002(pydantic) | - 上記 CPython 要件を継承 | - CPython 3.12 以上(pydantic v2 の最低要件) | pydantic v2 は v1 と非互換。本プロジェクトは v2 系 API のみ使用する前提 |

## 9. リスクコントロール手段のためのソフトウェア項目の分離(箇条 5.3.5 ― クラス C)

高クラス(C)の RCM を実装する項目と、他の項目とを分離することで、非 RCM 項目の安全クラスを下げる検討・決定を記録する。

### 9.1 分離設計の概要

本プロジェクトは Python 単一プロセスで実装されるため、ハードウェア分離(MPU, 物理プロセス分離)は本質的に使えない。代わりに以下の **論理的分離** を採用する:

1. **インタフェース分離(ABC / Protocol):** 抽象クラス・プロトコルで I/F を定義し、具象実装と呼出側の直接依存を排除
2. **依存方向の一方向性:** 低クラス項目は高クラス項目から一方向に呼び出されるのみで、低→高の逆方向データフローを禁止(例外: エラー情報は値のみで制御影響なし)
3. **パッケージ境界:** Python パッケージを分け、`__init__.py` の公開シンボルを明示的に制限
4. **データ複製/イミュータブル化:** 分離境界を越えるデータは **コピーまたはイミュータブル型**(frozen dataclass / tuple / Decimal)で渡し、参照共有による副作用を排除
5. **静的解析による違反検知:** mypy の strict モード + ruff ルールで依存ルール違反を CI 段階で検出する(例: `from vip_ctrl.core.*` を `vip_ctrl.logging.*` からインポートする行を禁止する)

### 9.2 分離記録

| 分離 ID | 対象項目(分離後クラス) | 分離手段 | 分離の根拠・検証方法 |
|--------|----------------------|---------|--------------------|
| SEP-001 | ARCH-005.3 Validation API(C → B) | 純粋関数化・イミュータブル入出力・状態アクセス禁止 | **根拠:** Validation API は読み取りも書き込みも行わず、設定値の形式検証のみを行う純粋関数(pydantic モデル)。制御コアへの副作用経路が存在せず、誤動作時も制御結果に影響し得ない。<br>**検証方法:** ユニット試験で「連続呼び出しでも内部状態が変化しないこと」を確認、mypy で `Control Core` パッケージへの import が存在しないことを静的確認 |
| SEP-002 | ARCH-009 Logging Stub I/F(C → B、**v0.2 で旧 ARCH-006 をリネーム**) | 抽象 I/F + 一方向出力 + 値型渡し(LogRecord は frozen) | **根拠:** ログは出力のみで制御へのフィードバック経路が無い。ログ実装の失敗(例外)は呼出元でガード(try/except)し制御に伝播させない設計とする。<br>**検証方法:** 結合試験でログ実装が例外を投げても制御ループが継続することを確認、mypy + ruff で Control Core からの参照が抽象 I/F にのみ向かうことを静的確認 |
| SEP-003 | ARCH-007 Alarm Reporter(C → B、**v0.2 で本実装後も維持**) | 抽象 I/F + 一方向出力 + 値型渡し(AlarmEvent は frozen + slots、metadata は MappingProxyType で frozen 化) | **根拠(v0.2 詳細化):** SAD v0.1 では Alarm Reporter は no-op スタブだったため分離が形式的だった。Inc.2 で ARCH-007.1 Reporter Core + ARCH-007.2 Priority Classifier を本実装するが、**(i) 検知ロジック(発報判定 = 閾値判定・冗長検知・多段判定)はすべて ARCH-006 検知群(クラス C)で実施**、**(ii) ARCH-007 は検知済の `AlarmEvent` を受け取って分類 + 通知するだけ**(`acknowledge` / `silence` も状態遷移命令を受けるだけで、検知 / 制御の判定はしない)、**(iii) `AlarmEvent` の不変性契約 + ARCH-007 から制御コアへの逆方向データフロー禁止**(IF-U-007 / IF-U-014 とも単方向 + 戻り値 None または非制御値)、により制御への影響経路を排除。**(iv) IEC 60601-1-8 整合確認**:同規格は「アラーム機能はクラス C 相当」とするが、本プロジェクトでは **発報判定(検知 + 状態遷移依頼)を ARCH-006 + UNIT-001.1(クラス C)で完結** させ、ARCH-007 は **通知 + 区分判定の純粋出力層** に限定することで、規格の意図(誤検知・誤発報の防止)を ARCH-006 側で担保。Inc.2 範囲計画書 §11.1 の事前識別リスクは本判断で解消。<br>**検証方法:** AST 分離検証(`vip_alarm.*` から `vip_ctrl.*` / `vip_sim.*` への戻り値書込み禁止 + 例外伝播禁止を mypy + ruff で機械検証)、結合試験で Alarm Reporter が例外を投げても制御ループ + 検知群が継続することを確認(SEP-002 と同様契約)、UT で `AlarmEvent` の `frozen=True` 違反検出、ARCH-007.2 Priority Classifier の純粋関数性を契約試験で確認 |
| SEP-000(非分離) | ARCH-001〜004(C 維持)+ **ARCH-006 Detection 検知群(C 維持、Inc.2 新設)** | — | **根拠:** 流量制御・仮想 HW・永続化・起動 + **検知群** は、いずれも RCM の一次実装または安全に直結する機能を含むため、クラス C を維持する。**ARCH-006 検知群は SRS-RCM-006/009/010/011/012(発報必達 + 冗長検知 + 多段判定 + タスク監視 + 発報路冗長)の主実装** = ハザード HZ-004 / HZ-005 / HZ-009 への保護機能のため非分離。分離しない方針を明示的に記録 |

### 9.3 分離が成立しない場合の帰結

本プロジェクトの分離(SEP-001/002/003)は **論理的分離** のみに依存する。以下のいずれかが崩れた場合、対象項目は再びクラス C として扱い、以降の試験・検証を再実施する:

- mypy / ruff の静的ルールが無効化された、または違反が検出されたまま修正されずマージされた
- 分離境界を越えた可変オブジェクトの共有が発生した(frozen 属性の回避等)
- ログ I/F やアラーム I/F の実装から制御コアへコールバックが追加された
- **(v0.2 追加)** ARCH-007 Alarm Reporter から ARCH-006 検知群 / ARCH-001 制御コアへ戻り値・例外・コールバックを介した制御フロー逆流が発生した(SEP-003 違反)
- **(v0.2 追加)** ARCH-007.2 Priority Classifier が純粋関数性を喪失した(内部状態を持つ、外部 I/O を行う等)

これらは SRMP §7.4.2「既存 RCM への影響の解析」の対象となる。

## 10. ソフトウェアアーキテクチャの検証(箇条 5.3.6)

本アーキテクチャは以下を満たすことを設計レビュー(セルフ)で確認する:

- [x] **SRS のすべての Inc.1〜2 要求事項を実装可能である** — §11 トレーサビリティマトリクスで SRS-001〜SRS-RCM-020 の全項目に ARCH-NNN を割付け済(v0.2 で SRS-040〜044 / SRS-ALM-004〜008 / SRS-RCM-006/009/010/011/012 / SRS-IF-010 / SRS-I-040 / SRS-O-040 / SRS-REG-002 を追補)
- [x] **ソフトウェア項目間・外部システムとのインタフェースが一貫している** — §5 IF 表に **17 件** の I/F を定義(v0.1:13 件、v0.2 で IF-U-012/013/014/015 + `AlarmEvent` 型構造を追加)、呼出方向・種別・仕様を明示
- [x] **医療機器のリスクコントロール手段の実装を支援する** — RCM-001/003/004/015/016/019(Inc.1 Verified)+ **RCM-006/009/010/011/012(Inc.2 範囲、本 v0.2 で実装先 Designed 確定)** それぞれを実装する ARCH-NNN を §4.3 で明示
- [x] **安全クラスに応じた分離が適切に設計されている** — §9 で SEP-001/002/003 を定義、**v0.2 で SEP-003 を Alarm Reporter 本実装後の契約として詳細化**、ARCH-006 検知群はクラス C 維持(SEP-000 非分離)
- [x] **SOUP の仕様(機能・性能要求)が記述されている** — §7 で SOUP-001/002 の機能・性能要求を指定、§8 で動作要件を指定。**v0.2 で SOUP 追加なし**(IEC 60601-1-8 準拠は内部実装、標準ライブラリで対応可能、Inc.2 範囲計画書 §7 確定)

レビュー記録:

| 項目 | 結果 | レビュー日 | 記録 |
|------|------|----------|------|
| SRS 全要求 → ARCH 割付 網羅性 | Pass(§11) | 2026-04-18 | v0.1 作成 + §11 |
| I/F 定義の一貫性 | Pass(§5) | 2026-04-18 | v0.1 作成 |
| RCM → ARCH 実装先の明示(Inc.1)| Pass(§4.3、§11) | 2026-04-18 | v0.1 作成 |
| 分離設計(§5.3.5)の妥当性 | Pass(§9) | 2026-04-18 | v0.1 作成 |
| SOUP 要求の完全性 | Pass(§6〜§8) | 2026-04-18 | v0.1 作成 |
| **Inc.2 範囲 SRS 追補 → ARCH 割付 網羅性** | Pass(§11) | 2026-05-09 | **v0.2(本改訂、CR-0011 / Step 20 D)**、SRS-040〜044 / SRS-ALM-004〜008 / SRS-RCM-006/009/010/011/012 を ARCH-006/007 / UNIT-001.1 拡張 / UNIT-002.3 拡張 / UNIT-005.1 拡張に割付け |
| **Inc.2 範囲 I/F 追加(IF-U-007 確定 + 012/013/014/015 新規)の一貫性** | Pass(§5) | 2026-05-09 | **v0.2**、§5.2 `AlarmEvent` 型構造確定、§5.3 IEC 60601-1-8 §6.4 状態遷移整理 |
| **Inc.2 範囲 RCM(5 件)→ ARCH 実装先の明示** | Pass(§4.3.2、§11.5) | 2026-05-09 | **v0.2**、RMF v0.4 の `Designed` 状態と整合 |
| **SEP-003 詳細化(Alarm Reporter 本実装後の契約)の妥当性** | Pass(§9.2、§9.3) | 2026-05-09 | **v0.2**、Inc.2 範囲計画書 §11.1 リスク事前識別を解消 |
| **SOUP 追加なし判定** | Pass(§6) | 2026-05-09 | **v0.2**、IEC 60601-1-8 準拠は標準ライブラリで対応可能 |

**単独開発下の独立性担保:** CCB-VIP-001 §5.4 に基づき、本 SAD 作成開始から PR 作成までに **CCB §5.4 で規定されるインターバル**(本プロジェクトでは 1 分以上、学習プロジェクト特例。実機適用時は 24 時間以上)を経てセルフレビューを実施し、CI 全 Pass を確認する。本 v0.2 改訂(Step 20 D / CR-0011)は、Step 20 C PR #54 マージ `b8eff10`(2026-05-08)から本 PR 起案(2026-05-09)まで日付変更線跨ぎ経過 = 1 分超遵守。

## 11. トレーサビリティマトリクス(SRS → ARCH)

Inc.1〜2 範囲の SRS 要求をアーキテクチャ要素に割付ける。SDD(箇条 5.4)作成時に「SDD 列」、試験計画(5.5〜5.7)作成時に「UT/IT/ST 列」を充填する。**v0.2 で Inc.2 範囲(SRS-040〜044 / SRS-ALM-004〜008 / SRS-RCM-006/009/010/011/012 + 確定化された SRS-I-040 / SRS-IF-010 / SRS-O-040 / SRS-REG-002)を追補。**

### 11.1 機能要求

| SRS ID | ARCH | 備考 |
|--------|------|------|
| SRS-001 / SRS-002 / SRS-003 | ARCH-001.3 Command Handler、ARCH-001.1 State Machine(Settings 保持) | 設定値の受領・検証・保持 |
| SRS-004 | ARCH-005.3 Validation API | pydantic モデルによる一貫性制約チェック |
| SRS-005 | ARCH-005.3 Validation API、ARCH-001.3 | 範囲検証 |
| SRS-010 | ARCH-005.1、ARCH-001.3、ARCH-001.1 | START コマンド → RUNNING 遷移 |
| SRS-011 | ARCH-001.2 Control Loop、ARCH-001.4 Validator | 100 ms サイクル指令 |
| SRS-012 | ARCH-001.2、ARCH-001.1 | 積算量による自動停止 |
| SRS-013 | ARCH-001.3、ARCH-001.1 | STOP 応答時間 |
| SRS-014 | ARCH-001.3、ARCH-001.1 | PAUSE/RESUME 状態遷移 |
| SRS-020 | ARCH-001.1 State Machine | 状態機械本体(Inc.2 でアラーム経路 + ACK / SILENCE 状態遷移を拡張) |
| SRS-021 | ARCH-009 Logging Stub I/F(旧 ARCH-006)、ARCH-001.1(遷移時ログ呼出) | ログ I/F 経由 |
| SRS-025 | ARCH-003 全ユニット、ARCH-001.1(save 呼出) | 非同期永続化 |
| SRS-026 | ARCH-004.1、ARCH-003 | 起動時復元 |
| SRS-027 | ARCH-004.1、ARCH-001.1(初期化受入) | フェイルセーフ起動 |
| SRS-028 | ARCH-004.2 Resume Gate、ARCH-005.1(confirm_resume) | 再開確認 |
| SRS-030 | ARCH-002.1 Pump Simulator | 仮想ポンプ機構 |
| SRS-031 | ARCH-002.2 Pump Observer | 状態観測 I/F |
| SRS-032 | ARCH-002.3 Event Injection | Inc.1 ではスタブ I/F 契約、**Inc.2 で本実装方針確定**(BATTERY_LOW 追加 + Pump 伝播)|
| **SRS-040(Inc.2)** | ARCH-006.1 Occlusion Detector + ARCH-002.1 Pump(センサー入力)+ ARCH-007.1 Alarm Reporter | 閉塞検知冗長 2 系統(RCM-009 連携)|
| **SRS-041(Inc.2)** | ARCH-006.2 Air-Bubble Detector + ARCH-002.1 + ARCH-007.1 | 気泡検知多段判定(RCM-010 連携)|
| **SRS-042(Inc.2)** | ARCH-006.3 Reservoir Empty Detector + ARCH-002.1 + ARCH-007.1 + ARCH-001.1(PAUSED 遷移)| 薬液切れ検知 |
| **SRS-043(Inc.2)** | ARCH-006.6 Battery Low Detector + ARCH-002.3(BATTERY_LOW)+ ARCH-007.1 | バッテリ低下検知(HZ-009)|
| **SRS-044(Inc.2)** | ARCH-005.1 Control API(`acknowledge_alarm` / `silence_alarm`)+ ARCH-007.1 Alarm Reporter Core + ARCH-001.1 State Machine(ACK / SILENCE 状態遷移)| アラーム確認・消音(IEC 60601-1-8 §6.4 準拠)|

### 11.2 性能要求

| SRS ID | ARCH | 備考 |
|--------|------|------|
| SRS-P01(±5% 精度) | ARCH-001.2、ARCH-002.1 | 制御ループと仮想ポンプの協調 |
| SRS-P02(ジッタ 10%) | ARCH-001.2、SOUP-001(CPython スケジューリング) | §7 SOUP 性能要求で担保 |
| SRS-P03(START 応答 500 ms) | ARCH-005.1、ARCH-001.3、ARCH-001.1 | 同期パス |
| SRS-P04(STOP 応答 200 ms) | 同上 | 同期パス、制御ループ 2 サイクル以内 |
| SRS-P05(起動 3 秒) | ARCH-004 全体、ARCH-003 | 起動パス |
| SRS-P06(永続化非ブロック) | ARCH-003(非同期キュー) | SRS-025 と両立 |
| SRS-P07(24h 耐久) | 全 ARCH-001〜004 | 結合試験で検証 |

### 11.3 I/O・I/F 要求

| SRS ID | ARCH | 備考 |
|--------|------|------|
| SRS-I-001〜003, SRS-I-010 | ARCH-005.1 Control API | 入力 API |
| SRS-I-020 | ARCH-002.2 Pump Observer | 仮想 HW 観測 |
| SRS-I-030 | ARCH-003 | 起動時復元 |
| **SRS-I-040(Inc.2 で確定)** | ARCH-002.3 Event Injection(`OCCLUSION` / `AIR_BUBBLE` / `RESERVOIR_EMPTY` / **`BATTERY_LOW`** 4 種 enum) → ARCH-006 検知群 | v0.2 で確定、Pump 伝播経路を実装方針として明記 |
| SRS-O-001 | ARCH-001.2 → ARCH-002.1(IF-U-002) | 流量指令 |
| SRS-O-010 | ARCH-005.2 State Observer API | 状態出力 |
| SRS-O-020 | ARCH-003 | 永続化書き込み |
| SRS-O-030 | ARCH-009 Logging Stub I/F(旧 ARCH-006) | ログ出力 |
| **SRS-O-040(Inc.2 で確定)** | ARCH-007.1 Alarm Reporter Core(`AlarmEvent` 構造は §5.2 で確定) | エラー通知(本実装、IEC 60601-1-8 整合)|
| SRS-IF-001 | ARCH-002 全体 | 仮想 HW I/F |
| SRS-IF-002 | ARCH-005.1 | 制御 API |
| SRS-IF-003 | ARCH-005.2 | 状態観測 API |
| SRS-IF-004 | ARCH-009 Logging Stub I/F(旧 ARCH-006) | ロギング I/F |
| SRS-IF-005 | ARCH-003 | 永続化 I/F |
| **SRS-IF-010(Inc.2 で確定)** | ARCH-007.1 Alarm Reporter Core(`report_alarm` + `acknowledge` + `silence` 3 メソッド)+ ARCH-007.2 Priority Classifier | `AlarmReportInterface` 本実装契約(IEC 60601-1-8 §6.4 準拠)|
| SRS-IF-020(Inc.3 予定) | (ARCH-008 Inc.3 で新設予定) | 予約、現時点未割付 |

### 11.4 アラーム・セキュリティ・UX・データ・運用・規制要求

| SRS ID | ARCH | 備考 |
|--------|------|------|
| SRS-ALM-001 | ARCH-001.1 → ARCH-007.1 Alarm Reporter Core | ERROR 遷移通知(Inc.2 で本実装に接続)|
| SRS-ALM-002 | ARCH-004.1、ARCH-009 Logging Stub | 起動時ログ |
| SRS-ALM-003 | ARCH-001.1、ARCH-009 Logging Stub | 不正遷移ログ(RCM-019 連携) |
| **SRS-ALM-004(Inc.2)** | ARCH-006.1 → ARCH-007.1 / 007.2(優先度 高 / TECHNICAL)| 閉塞検知発報 |
| **SRS-ALM-005(Inc.2)** | ARCH-006.2 → ARCH-007.1 / 007.2(優先度 高 / TECHNICAL)| 気泡検知発報 |
| **SRS-ALM-006(Inc.2)** | ARCH-006.3 → ARCH-007.1 / 007.2(優先度 中 / TECHNICAL)| 薬液切れ発報 |
| **SRS-ALM-007(Inc.2)** | ARCH-006.6 → ARCH-007.1 / 007.2(優先度 中 / TECHNICAL)| バッテリ低下発報(HZ-009)|
| **SRS-ALM-008(Inc.2)** | ARCH-005.1(`acknowledge_alarm` / `silence_alarm`)→ ARCH-007.1 + ARCH-001.1(ACK / SILENCE 状態遷移)| アラーム確認・消音操作 |
| SRS-SEC-001 | ARCH-003.2 Checksum Verifier | SHA-256 |
| SRS-SEC-002 | ARCH-009 Logging Stub | ログ I/F 契約でポリシー遵守 |
| SRS-SEC-003 | (CI 側 pip-audit、本 SAD の運用側要求) | SMP §7.1 |
| SRS-UX-001 | ARCH-005.3 Validation API(分離対象) | 純粋関数 |
| SRS-UX-002 | ARCH-005.2 State Observer API | idempotent |
| SRS-DATA-001〜004 | ARCH-003 全ユニット | 永続化ポリシー |
| SRS-OPS-001〜004 | ARCH-005 / パッケージング設定(CI-CFG-009 予定) | 配布・インストール |
| SRS-OPS-010〜012 | ARCH-009 Logging Stub / ARCH-005 | 運用 I/F |
| SRS-NET-001 | (全 ARCH、ネットワーク未使用) | — |
| SRS-REG-001 | SRS-P01 ↔ §11.2 経由で ARCH-001.2 / ARCH-002.1 | IEC 60601-2-24 相当 |
| **SRS-REG-002(Inc.2 で確定)** | ARCH-007.1 Alarm Reporter Core + ARCH-007.2 Priority Classifier(IEC 60601-1-8 §6.1 優先度 + §5.1.4 区分 + §6.4 確認・休止)+ ARCH-005.1(SRS-ALM-008 経由)| IEC 60601-1-8 適用詳細化(Inc.4 で §5.1.5 視覚信号 + §5.1.6 聴覚信号 を追補予定)|

### 11.5 リスクコントロール要求(SRS §5 → ARCH)

| SRS ID(RCM) | 対応 RCM | 実装 ARCH | 分離(§9) |
|--------------|---------|-----------|---------|
| SRS-RCM-001 | RCM-001 | ARCH-001.4 Flow Command Validator | クラス C(非分離) |
| SRS-RCM-003 | RCM-003 | ARCH-001.5 Watchdog | クラス C(非分離) |
| SRS-RCM-004 | RCM-004 | ARCH-001.2 + ARCH-002.4(HW-side FS Timer) | クラス C(非分離、二重冗長) |
| SRS-RCM-015 | RCM-015 | ARCH-004.1 Integrity Validator | クラス C(非分離) |
| SRS-RCM-016 | RCM-016 | ARCH-004.2 Resume Gate | クラス C(非分離) |
| SRS-RCM-020 | RCM-019 | ARCH-001.1 State Machine | クラス C(非分離) |
| **SRS-RCM-006(Inc.2)** | RCM-006 | ARCH-007.1 Alarm Reporter Core(発報必達 + 1 秒以内)+ ARCH-006.5 Alarm Path Redundancy(主系故障時の予備系切替)| ARCH-007.1 = クラス B(SEP-003)、ARCH-006.5 = クラス C(非分離)|
| **SRS-RCM-009(Inc.2)** | RCM-009 | ARCH-006.1 Occlusion Detector(冗長 2 系統独立性)+ ARCH-002.1 / IF-U-015(2 系統独立センサー入力)| クラス C(非分離)|
| **SRS-RCM-010(Inc.2)** | RCM-010 | ARCH-006.2 Air-Bubble Detector(多段判定独立性)+ ARCH-002.1 / IF-U-015(警告 / 危険閾値独立センサー)| クラス C(非分離)|
| **SRS-RCM-011(Inc.2)** | RCM-011 | ARCH-006.4 Alarm Task Watchdog(タスク監視 + 1 秒以内検知)| クラス C(非分離)|
| **SRS-RCM-012(Inc.2)** | RCM-012 | ARCH-006.5 Alarm Path Redundancy(主系 / 予備系冗長化)+ ARCH-007.1(発報路の最終出力)| ARCH-006.5 = クラス C(非分離)、ARCH-007.1 = クラス B(SEP-003)|

**Inc.2 範囲 RCM 5 件の状態(本 v0.2 改訂時点):** RMF-VIP-001 v0.4(CR-0010 / Step 20 C)で `Designed` 状態に到達済 + 本 SAD v0.2(CR-0011 / Step 20 D)で実装先 ARCH を確定。Inc.2 SDD v0.5 骨格(Step 20 E 予定)で詳細設計、Step 20 X〜の TDD 実装 + Step 20 Y / Z の試験(IT-RCM006/009/010/011/012 + ST-ALM)+ Linux nightly 5 連続 Pass を経て Verified 化(`v0.2.0-inc2` 付与時)目標。RCM-020 候補(HZ-009 対応のバッテリ管理 / 安全側遷移)は SRS への正式登録を Step 20 B-3 候補として申し送り、本 SAD では UNIT-006.6 + UNIT-007.1 経由のアラーム発報まで設計確定。

## 12. 改訂履歴

| バージョン | 日付 | 変更内容 | 変更者 |
|----------|------|---------|--------|
| 0.2 | 2026-05-09 | **CR-0011(MAJOR、Step 20 D / Inc.2 連動改訂の SAD 部分)による改訂。** Step 20 B-2(CR-0008、SRS-VIP-001 v0.2 → v0.3、PR #52 マージ `6bf66e3`)で SRS に追加した Inc.2 範囲要求 + Step 20 C(CR-0010、RMF-VIP-001 v0.3 → v0.4、PR #54 マージ `b8eff10`)で RMF に反映したハザード(HZ-009 新規)+ RCM 5 件(Designed)を本 SAD v0.2 で正式反映。**(A) §4.3.2 Inc.2 範囲 ARCH 項目の新設・拡張:** ARCH-006 Detection 検知群を新設(クラス C、UNIT-006.1〜006.6 = Occlusion / Air-Bubble / Reservoir Empty / Alarm Task Watchdog / Alarm Path Redundancy / Battery Low Detector)、ARCH-007 Alarm Reporter を本実装化(クラス B 維持、UNIT-007.1 Reporter Core + UNIT-007.2 Priority Classifier、SEP-003 詳細化済)、UNIT-001.1 State Machine 拡張(アラーム発報経路 + ACK / SILENCE 状態遷移、SRS-044 / SRS-ALM-008 連携)、UNIT-002.3 Event Injection の no-op 解除方針確定(BATTERY_LOW enum 追加 + Pump 伝播経路、SDD §4.11.C 予告分を本 SAD で正式確定)、UNIT-005.1 Control API 拡張(`acknowledge_alarm` / `silence_alarm`)。**(B) ARCH ID リネーム(衝突解消):** 旧 ARCH-006 Logging Stub I/F を ARCH-009 にリネーム(機能内容不変、Inc.4 で本実装予定)、ARCH-006 を Detection 検知群へ再割当て、Inc.4 UI 用予約を ARCH-010 に繰下げ(Inc.3 用量計算 = ARCH-008 維持)。INCREMENT_PLANS / RMF v0.4 / CRR v0.12 / SRS v0.3 が前提とする ID 体系(ARCH-006 = 検知群 / ARCH-007 = Alarm Reporter 本実装)と整合化。**(C) §4.2 全体構成図更新:** ARCH-006 検知群 + ARCH-007 本実装 + アラーム発報経路 + 確認 / 消音状態遷移を含む新図に置換。**(D) §5 ソフトウェア項目間 I/F 追加・確定:** IF-U-007 シグネチャ確定(`report_alarm(event: AlarmEvent) -> None`、§5.2 で `AlarmEvent` 型構造を確定 = `alarm_id` + `priority: AlarmPriority` + `category: AlarmCategory` + `occurred_at: float` + `cause_code: str` + `metadata: Mapping[str, object]` の frozen + slots、SRS-O-040 整合)、IF-U-012 検知群 → Alarm Reporter、IF-U-013 検知群 → State Machine(`request_state_transition`)、IF-U-014 Control API → Alarm Reporter(`acknowledge` / `silence`、IEC 60601-1-8 §6.4 準拠)、IF-U-015 Pump → 検知群(冗長 2 系統センサー入力、SRS-RCM-009 根拠)を新規追加。§5.3 IEC 60601-1-8 §6.4 アラーム確認・休止の状態遷移整理(ACTIVE / ACKED / SILENCED / CLEARED + 高優先度 ≤ 120 秒消音時間制限)。**(E) §9.2 SEP-003 詳細化:** Alarm Reporter 本実装後の分離契約を再記述(検知ロジックは ARCH-006 クラス C で完結 + ARCH-007 は通知 + 区分判定の純粋出力層に限定 + AlarmEvent 不変性 + 制御コアへの逆方向データフロー禁止)、IEC 60601-1-8(アラーム機能はクラス C 相当)との整合確認(Inc.2 範囲計画書 §11.1 リスク事前識別を解消)。SEP-002 を「ARCH-009 Logging Stub」(旧 ARCH-006)に整合化。**(F) §11 トレーサビリティマトリクス追補:** §11.1 機能要求に SRS-040〜044 行追加(検知群 + Alarm Reporter)、§11.3 I/O・I/F 要求の SRS-I-040 / SRS-IF-010 / SRS-O-040 を確定化(Inc.2 で本実装)、§11.4 アラーム要求に SRS-ALM-004〜008 行追加 + SRS-REG-002 確定化、§11.5 RCM に SRS-RCM-006/009/010/011/012 行追加(各 ARCH-006.x / 007.x へ実装先確定 + 分離(§9)列で SEP-003 整合明記)。**(G) ヘッダ:** v0.1 → v0.2、対象ソフトウェアバージョン 0.1.0 → 0.2.0(Inc.2 範囲)、最終更新日 2026-05-09。**MAJOR 区分**(新規 ARCH 項目 = 検知群 6 ユニット + Alarm Reporter 本実装 2 ユニット + UNIT-001.1 / 002.3 / 005.1 拡張 + I/F 4 件新規 + IF-U-007 シグネチャ確定 + ARCH ID リネーム = SCMP §4.1 規定該当)、**SRMP §7.3「RCM 関連部の追加」相当**(新規 5 RCM の実装先確定 + HZ-009 対応設計を SAD に反映)、ただし **本 CR-0011 は SAD 改訂のみで実装コード / SOUP / 試験への波及なし**(後続 Step 20 E〜Z で連動)。**SOUP 追加なし**(IEC 60601-1-8 準拠は内部実装、標準ライブラリで対応可能の見込み、Inc.2 範囲計画書 §7 確定)。**「単一文書 = 単一 CR」運用パターンの 4 度目適用**(CR-0008 = SRS / CR-0010 = RMF / CR-0011 = SAD / CR-0009 = SDD で分離継続)、**「§4 CLOSED 一気通貫」運用パターンの 4 度目適用**(Step 20 B-1 / B-2 / C 連続適用に続く)| k-abe |
| 0.1 | 2026-04-18 | 初版作成(Inc.1 範囲):ARCH-001〜007 の 7 項目 + 下位ユニット 14 件を定義、I/F 12 件(内部 U 系 11 件、外部 E 系 2 件)を明示、SOUP-001/002 の機能・性能要求と動作要件を指定、分離 SEP-001/002/003 を定義(Validation API / Logging / Alarm を B へ分離)、SRS 全要求 → ARCH トレーサビリティを §11 で網羅。Inc.2 以降で ARCH-007 本実装、ARCH-008(Inc.3 用量計算)、ARCH-009(Inc.4 UI)を追補予定 | k-abe |
