# ソフトウェア詳細設計書(SDD)

**ドキュメント ID:** SDD-VIP-001
**バージョン:** 0.8
**作成日:** 2026-04-18(v0.1)/ 2026-04-19(v0.2)/ 2026-05-01(v0.3)/ 2026-05-07(v0.4)/ 2026-05-10(v0.5)/ 2026-05-13(v0.6 + v0.7)/ 2026-05-15(v0.8)
**最終更新日:** 2026-05-15
**対象製品:** 仮想輸液ポンプ(Virtual Infusion Pump) / VIP-SIM-001
**対象ソフトウェアバージョン:** 0.2.0(Inc.1 範囲全 18 ユニット詳細 + Inc.2 範囲 UNIT-006.1/006.2/006.3 詳細 + Inc.2 残 5 ユニット骨格 + 既存 3 ユニット Inc.2 拡張節、合計 26 ユニット、Step 14 v0.1 流儀の v0.x 骨格化 → 後続改訂で詳細化を継承)
**安全クラス:** C(IEC 62304)
**変更要求:** CR-0001(Issue #1、MODERATE)、CR-0004(Issue #32、MODERATE)、CR-0005(Issue #36、MODERATE)、CR-0009(Issue #57、MODERATE、Step 20 E)、CR-0016(MODERATE、Step 20 X2、Inc.2 連動詳細化の SDD 部分 §4.19)、CR-0019(Issue #74、MODERATE、Step 20 X5、Inc.2 連動詳細化の SDD 部分 §4.20)、CR-0022(Issue #80、MODERATE、Step 20 X8、Inc.2 連動詳細化の SDD 部分 §4.21)

| 役割 | 氏名 | 所属 | 日付 | 署名 |
|------|------|------|------|------|
| 作成者 | k-abe | — | 2026-04-19 | |
| レビュー者 | — | — | — | |
| 承認者 | — | — | — | |

> **本プロジェクトの位置づけ(注記)**
> 本ドキュメントは IEC 62304 に基づく医療機器ソフトウェア開発プロセスの学習・参考実装を目的とした **仮想プロジェクト** の成果物である。
>
> **本 SDD v0.5 の位置づけ(CR-0009 / Step 20 E、Inc.2 連動改訂の SDD 部分、骨格化):** SAD-VIP-001 v0.2(CR-0011 / Step 20 D)で確定した Inc.2 範囲のアーキテクチャ要素を、Step 14 v0.1 流儀(代表 5 ユニット詳細 + 骨格 N ユニット)を継承して **Inc.2 新規 8 ユニットを §4.x 骨格記述として追加** + **既存 3 ユニットに Inc.2 拡張サブセクション(§4.x.G)を追補** + **§5.1 IF-U-007 詳細化(`AlarmEvent` Python 実装契約)+ IF-U-012〜015 新規追加** + **§6.4 ISS-V02 解消済整合化** + **§6.5 v0.5 骨格化で発見した整合性課題(申し送り)新設**。詳細記述(各骨格 8 ユニット + 既存 3 ユニット拡張節の §4.x.A〜F 完全版)は Step 20 X〜の TDD 実装と並行する SDD 後続改訂(v0.6 候補)で展開する。本改訂は CR-0009(MODERATE)として CCB プロセスを経て承認される。
>
> **v0.5 で追加した Inc.2 新規 8 ユニット(§4.19〜§4.26、骨格):** UNIT-006.1 Occlusion Detector / UNIT-006.2 Air-Bubble Detector / UNIT-006.3 Reservoir Empty Detector / UNIT-006.4 Alarm Task Watchdog / UNIT-006.5 Alarm Path Redundancy / UNIT-006.6 Battery Low Detector / UNIT-007.1 Alarm Reporter Core / UNIT-007.2 Alarm Priority Classifier。
>
> **v0.5 で拡張した既存 3 ユニット(§4.x.G、Inc.2 追補):** UNIT-001.1 State Machine(アラーム発報経路 + ACK/SILENCE 状態遷移)/ UNIT-002.3 Event Injection(BATTERY_LOW + Pump 伝播経路、no-op 解除)/ UNIT-005.1 Control API(`acknowledge_alarm` / `silence_alarm`)。
>
> **本 SDD v0.2 の位置づけ:** v0.1 で骨格記述に留めていた 12 ユニット(残 9 ユニット + Public API Facade 3 ユニット)を §5.4.2 詳細記述に展開し、Inc.1 範囲の **全 17 ユニット** について公開 API・データ構造・アルゴリズム・資源使用量・例外/異常系・検証方法を確定した。これにより SDD v0.1 §6.3 で宣言した実装ブロックを解消し、Inc.1 実装着手準備を完了する。本改訂は CR-0001(MODERATE)として CCB プロセスを経て承認される。
>
> **v0.2 で追加詳細化した 12 ユニット:** Control Loop / Command Handler / Watchdog (SW) / Pump Simulator / Pump Observer / Event Injection Stub / Serializer / Checksum Verifier / Resume Confirmation Gate / Control API / State Observer API / Validation API。
>
> **v0.1 で詳細記述した 5 代表ユニット:** State Machine / Flow Command Validator / HW-side Failsafe Timer / Atomic File Writer / Integrity Validator(状態機械・バリデータ・並行タイマ・永続化・起動復元のアーキタイプ)。

---

## 1. 目的と適用範囲

本書は、SAD-VIP-001 v0.1 で定義された Inc.1 範囲のソフトウェア項目を、IEC 62304 箇条 5.4 に従ってソフトウェアユニットへ分解し、各ユニットの詳細設計を定義する。

**本書の対象:**

- クラス C ユニットの **詳細設計**(§5.4.2、必須)
- **インタフェースの詳細設計**(§5.4.3、必須)
- **詳細設計の検証**(§5.4.4、必須)

**代表 5 ユニットの選定根拠:**

| ユニット | 代表する設計アーキタイプ |
|---------|----------------------|
| UNIT-001.1 State Machine | 状態機械の形式化、不変条件、RCM-019 実装 |
| UNIT-001.4 Flow Command Validator | 境界値検証・事前/事後条件、RCM-001 実装 |
| UNIT-002.4 HW-side Failsafe Timer | 並行タイマ・競合・フェイルセーフ、RCM-004 HW 側実装 |
| UNIT-003.3 Atomic File Writer | OS 依存アルゴリズム・障害回復 |
| UNIT-004.1 Integrity Validator | 複合整合性検証・破損注入耐性、RCM-015 実装 |

## 2. 参照文書

| ID | 文書名 | バージョン |
|----|--------|----------|
| [1] | IEC 62304:2006+A1:2015 箇条 5.4 | — |
| [2] | ソフトウェア要求仕様書(SRS-VIP-001) | 0.3(Inc.2 SRS 追補確定、CR-0008 / Step 20 B-2) |
| [3] | ソフトウェアアーキテクチャ設計書(SAD-VIP-001) | 0.2(Inc.2 連動改訂、CR-0011 / Step 20 D) |
| [4] | リスクマネジメントファイル(RMF-VIP-001) | 0.4(HZ-009 識別 + RCM-006/009/010/011/012 Designed、CR-0010 / Step 20 C) |
| [5] | ソフトウェア開発計画書(SDP-VIP-001)§14 共通欠陥 | 0.1 |
| [6] | Inc.2 範囲計画書(INC2-SCOPE-VIP-001) | 0.1(Step 20 A 新設) |
| [7] | IEC 60601-1-8(アラームシステム) | — |

## 3. ソフトウェア項目のソフトウェアユニットへの改良(箇条 5.4.1)

### 3.1 ユニット階層(Inc.1〜2 範囲、v0.5 で Inc.2 拡張)

```
ARCH-001 Control Core (C)
├── UNIT-001.1  State Machine                (Inc.1 詳細 §4.1 + Inc.2 拡張 §4.1.G、v0.5)
├── UNIT-001.2  Control Loop
├── UNIT-001.3  Command Handler
├── UNIT-001.4  Flow Command Validator
└── UNIT-001.5  Watchdog (SW side)

ARCH-002 Virtual Hardware (C)
├── UNIT-002.1  Pump Simulator
├── UNIT-002.2  Pump Observer
├── UNIT-002.3  Event Injection             (Inc.1 スタブ §4.11 + Inc.2 拡張 §4.11.G、v0.5、no-op 解除)
└── UNIT-002.4  HW-side Failsafe Timer

ARCH-003 Persistence (C)
├── UNIT-003.1  Serializer
├── UNIT-003.2  Checksum Verifier
└── UNIT-003.3  Atomic File Writer

ARCH-004 Boot / Recovery (C)
├── UNIT-004.1  Integrity Validator
└── UNIT-004.2  Resume Confirmation Gate

ARCH-005 Public API Facade
├── UNIT-005.1  Control API                 (Inc.1 詳細 §4.15 + Inc.2 拡張 §4.15.G、v0.5)
├── UNIT-005.2  State Observer API          (C、薄いラッパー)
├── UNIT-005.3  Validation API              (B、分離対象)
└── UNIT-005.4  CLI Entry Point             (C、Step 19 H1 で新規追加)

# Inc.2 で新設(本 v0.5 で骨格化、CR-0009 / Step 20 E)
ARCH-006 Detection (C、新設)
├── UNIT-006.1  Occlusion Detector          (§4.19、骨格、RCM-009)
├── UNIT-006.2  Air-Bubble Detector         (§4.20、詳細 v0.7、RCM-010、Step 20 X4 実装 + X5 SDD 詳細化)
├── UNIT-006.3  Reservoir Empty Detector    (§4.21、詳細 v0.8、RCM-006、Step 20 X7 実装 + X8 SDD 詳細化)
├── UNIT-006.4  Alarm Task Watchdog         (§4.22、骨格、RCM-011)
├── UNIT-006.5  Alarm Path Redundancy       (§4.23、骨格、RCM-012)
└── UNIT-006.6  Battery Low Detector        (§4.24、骨格、RCM-006、HZ-009)

ARCH-007 Alarm Reporter (B、SEP-003 分離継続、Inc.2 で本実装化)
├── UNIT-007.1  Alarm Reporter Core         (§4.25、骨格、SRS-IF-010 本実装)
└── UNIT-007.2  Alarm Priority Classifier   (§4.26、骨格、IEC 60601-1-8 §6.1)

ARCH-009 Logging Stub I/F(B、旧 ARCH-006、SAD v0.2 でリネーム、Inc.4 で本実装予定)
ARCH-010(Inc.4 UI 用予約、SAD v0.2 で新規予約)
```

### 3.2 ユニット一覧(Inc.1〜2 範囲、v0.5 で Inc.2 行追加)

| ユニット ID | 名称 | 所属項目 | 安全クラス | 本 SDD での扱い |
|-----------|------|---------|----------|-------------------|
| UNIT-001.1 | State Machine | ARCH-001 | C | 詳細(§4.1、v0.1)+ **Inc.2 拡張(§4.1.G、v0.5):アラーム発報経路 + ACK/SILENCE 状態遷移、骨格** |
| UNIT-001.2 | Control Loop | ARCH-001 | C | **詳細(§4.6、v0.2)** |
| UNIT-001.3 | Command Handler | ARCH-001 | C | **詳細(§4.7、v0.2)** |
| UNIT-001.4 | Flow Command Validator | ARCH-001 | C | 詳細(§4.2、v0.1) |
| UNIT-001.5 | Watchdog (SW) | ARCH-001 | C | **詳細(§4.8、v0.2)** |
| UNIT-002.1 | Pump Simulator | ARCH-002 | C | **詳細(§4.9、v0.2)** |
| UNIT-002.2 | Pump Observer | ARCH-002 | C | **詳細(§4.10、v0.2)** |
| UNIT-002.3 | Event Injection | ARCH-002 | C | **詳細(§4.11、v0.2、Inc.1 スタブ)+ Inc.2 拡張(§4.11.G、v0.5):BATTERY_LOW 追加 + Pump 伝播経路、no-op 解除、骨格** |
| UNIT-002.4 | HW-side Failsafe Timer | ARCH-002 | C | 詳細(§4.3、v0.1) |
| UNIT-003.1 | Serializer | ARCH-003 | C | **詳細(§4.12、v0.2)** |
| UNIT-003.2 | Checksum Verifier | ARCH-003 | C | **詳細(§4.13、v0.2)** |
| UNIT-003.3 | Atomic File Writer | ARCH-003 | C | 詳細(§4.4、v0.1) |
| UNIT-004.1 | Integrity Validator | ARCH-004 | C | 詳細(§4.5、v0.1) |
| UNIT-004.2 | Resume Confirmation Gate | ARCH-004 | C | **詳細(§4.14、v0.2)** |
| UNIT-005.1 | Control API | ARCH-005 | C | **詳細(§4.15、v0.2)** + **Inc.2 拡張(§4.15.G、v0.5):`acknowledge_alarm` / `silence_alarm`、骨格** |
| UNIT-005.2 | State Observer API | ARCH-005 | C | **詳細(§4.16、v0.2)** |
| UNIT-005.3 | Validation API | ARCH-005 | B(分離対象) | **詳細(§4.17、v0.2)** |
| UNIT-005.4 | CLI Entry Point | ARCH-005 | C | **詳細(§4.18、v0.4、Step 19 H1 で新規追加)** |
| **UNIT-006.1** | **Occlusion Detector** | **ARCH-006** | **C** | **詳細(§4.19、v0.6、RCM-009、SRS-040、SRS-ALM-004、Step 20 X1 で実装 + Step 20 X2 で SDD 詳細化)** |
| **UNIT-006.2** | **Air-Bubble Detector** | **ARCH-006** | **C** | **詳細(§4.20、v0.7、RCM-010、SRS-041、SRS-ALM-005、Step 20 X4 で実装 + Step 20 X5 で SDD 詳細化、`src/vip_detection/air_bubble.py` 運用中 v0.1)** |
| **UNIT-006.3** | **Reservoir Empty Detector** | **ARCH-006** | **C** | **詳細(§4.21、v0.8、RCM-006、SRS-042、SRS-ALM-006、Step 20 X7 で実装 + Step 20 X8 で SDD 詳細化、`src/vip_detection/reservoir.py` 運用中 v0.1)** |
| **UNIT-006.4** | **Alarm Task Watchdog** | **ARCH-006** | **C** | **骨格(§4.22、v0.5、RCM-011、SRS-044)** |
| **UNIT-006.5** | **Alarm Path Redundancy** | **ARCH-006** | **C** | **骨格(§4.23、v0.5、RCM-012、SRS-IF-010)** |
| **UNIT-006.6** | **Battery Low Detector** | **ARCH-006** | **C** | **骨格(§4.24、v0.5、RCM-006、SRS-043、SRS-ALM-007、HZ-009)** |
| **UNIT-007.1** | **Alarm Reporter Core** | **ARCH-007** | **B(分離、SEP-003 継続)** | **骨格(§4.25、v0.5、RCM-006、SRS-IF-010、SRS-ALM-001/004〜008、SRS-O-040)** |
| **UNIT-007.2** | **Alarm Priority Classifier** | **ARCH-007** | **B(分離、SEP-003 継続)** | **骨格(§4.26、v0.5、SRS-REG-002、IEC 60601-1-8 §6.1/§5.1.4、純粋関数)** |

## 4. ソフトウェアユニットの詳細設計(箇条 5.4.2 ― クラス C)

---

### 4.1 UNIT-001.1: State Machine

- **目的 / 責務:** 流量制御ソフトウェアの内部状態(INITIALIZING / IDLE / RUNNING / PAUSED / STOPPED / ERROR)を保持し、SRS-VIP-001 §4.1.3 で定義された遷移規則のみを許可する。不正遷移要求を検出して拒否し(RCM-019)、正当な遷移時に永続化およびログ I/F へ通知する。
- **関連 SRS:** SRS-020, SRS-021, SRS-025, SRS-RCM-020, SRS-ALM-003
- **関連 RCM:** RCM-019(状態遷移保護)、RCM-015/016 の前提ゲート
- **安全クラス:** C

#### 4.1.1 公開 API

| 関数・メソッド | 引数 | 戻り値 | 事前条件 | 事後条件 | エラー処理 |
|----------------|------|-------|---------|---------|-----------|
| `current() -> State` | — | State(enum) | なし | 状態は不変 | なし(純粋関数) |
| `request_transition(event: TransitionEvent) -> TransitionResult` | TransitionEvent(frozen dataclass: 種別、メタデータ、タイムスタンプ) | TransitionResult(成功: `Ok(new_state)` / 失敗: `InvalidTransitionError`) | 呼出元は単一スレッド、または内部ロック経由 | 成功時のみ状態更新 + 永続化キュー投入 + ログ出力 | 不正遷移: 状態不変、エラーログ、`InvalidTransitionError` を返す |
| `set_initial(state: State, needs_confirm: bool) -> None` | 起動時の初期状態 | — | `current() == INITIALIZING` のみ許可 | 状態 = 引数、needs_confirm フラグ保持 | 事前条件違反: `InvalidInitializationError` |
| `on_watchdog_timeout(reason: WatchdogReason) -> None` | — | — | 任意の状態から呼び出し可 | `current() == ERROR`、理由記録 | 既に ERROR の場合は冪等(最初の理由を保持) |

#### 4.1.2 データ構造

| 名称 | 型 | 値域 | 意味 | スレッド安全性 |
|------|----|------|------|--------------|
| `_state` | `State` (Enum) | 6 値 | 現在の状態 | `_lock` による保護必須 |
| `_needs_resume_confirm` | `bool` | True/False | 復元時に再開確認待ちか | `_lock` 保護 |
| `_last_transition_ts` | `datetime` | ISO 8601 | 最終遷移時刻 | `_lock` 保護 |
| `_error_reason` | `Optional[WatchdogReason]` | None / enum | ERROR 時の原因 | `_lock` 保護 |
| `_lock` | `threading.RLock` | — | 状態全体の相互排他 | それ自体がスレッド安全 |
| `_persistence_queue` | `queue.Queue[RuntimeState]` | — | 非同期永続化キュー(SRS-P06) | Queue 自体がスレッド安全 |

#### 4.1.3 状態遷移表(SRS-VIP-001 §4.1.3 の実装詳細)

遷移表は **宣言的テーブル** として持ち、`request_transition` はテーブル参照のみで判定する(実装分岐を減らし検証可能性を高める)。

```python
# 擬似コード(実装の骨格)
TRANSITION_TABLE: Mapping[tuple[State, EventKind], tuple[State, Callable | None]] = {
    (INITIALIZING, BOOT_OK_NO_PENDING): (IDLE, None),
    (INITIALIZING, BOOT_OK_WITH_PENDING): (IDLE, set_needs_confirm),
    (INITIALIZING, BOOT_INTEGRITY_FAIL): (IDLE, set_failsafe_defaults),
    (INITIALIZING, BOOT_FATAL): (ERROR, None),
    (IDLE, CMD_START): (RUNNING, check_settings_valid),
    (RUNNING, AUTO_STOP_DOSE_REACHED): (STOPPED, None),
    (RUNNING, CMD_PAUSE): (PAUSED, None),
    (RUNNING, CMD_STOP): (STOPPED, None),
    (RUNNING, WDT_TIMEOUT): (ERROR, record_wdt_reason),
    (PAUSED, CMD_RESUME): (RUNNING, None),
    (PAUSED, CMD_STOP): (STOPPED, None),
    (STOPPED, CMD_RESET): (IDLE, clear_settings),
    (ERROR, CMD_ERROR_RESET): (IDLE, clear_error_after_check),
}
```

非対応の (状態, イベント) 組合せは **不正遷移** として拒否される(RCM-019)。

#### 4.1.4 アルゴリズム

```python
# request_transition の擬似コード
def request_transition(self, event: TransitionEvent) -> TransitionResult:
    with self._lock:
        key = (self._state, event.kind)
        if key not in TRANSITION_TABLE:
            self._logger.log_invalid_transition(self._state, event)
            return Err(InvalidTransitionError(self._state, event.kind))
        new_state, guard_or_action = TRANSITION_TABLE[key]
        if guard_or_action:
            guard_result = guard_or_action(event, self._context)
            if guard_result.is_err():  # 条件付き遷移のガード失敗
                self._logger.log_guard_failed(self._state, event, guard_result)
                return Err(guard_result.err)
        prev = self._state
        self._state = new_state
        self._last_transition_ts = now_utc()
        snapshot = self._build_snapshot()
        self._persistence_queue.put_nowait(snapshot)  # 非ブロック、満杯時は別経路
        self._logger.log_transition(prev, new_state, event)
        return Ok(new_state)
```

#### 4.1.5 資源使用量・タイミング制約

- **メモリ:** 状態機械自体は定数サイズ(数 KB 以内)。履歴・ログは別ユニット
- **実行時間:** `request_transition` は辞書参照 + ロック取得 + 小量の I/O キューイング = 100 μs オーダー(制御サイクル 100 ms に対し 0.1% 以下)
- **呼出コンテキスト:** 複数スレッドから呼ばれうる(制御ループ、API、WDT)— `_lock` による相互排他必須
- **永続化キュー満杯時:** `put_nowait` が失敗したら ERROR 遷移を試みる(SRS-025 の劣化を検知)

#### 4.1.6 例外・異常系

| 異常条件 | 検出方法 | 処置 |
|---------|---------|------|
| 不正遷移要求(RCM-019) | テーブル参照の失敗 | `InvalidTransitionError` を返す、ログ出力 |
| 同一状態への遷移(例: IDLE → IDLE) | テーブルに登録しない | 不正遷移として拒否 |
| ロック取得失敗(デッドロック疑い) | `RLock` を使用し自己再入は許可、取得タイムアウト 100 ms | タイムアウト時は `StateLockTimeout` 例外、呼出元で ERROR 誘発 |
| 永続化キュー満杯 | `queue.Full` | WDT 経由で ERROR 遷移、ログ記録 |
| 不整合な内部状態(例: ERROR なのに error_reason が None) | 定期的な内部不変条件チェック(ユニット試験でも検証) | アサーション失敗、プロセス終了(フェイルセーフ) |

#### 4.1.7 検証方法(§5.4.4 準拠)

- **ユニット試験:** 状態遷移表の全エントリを網羅(14 行 × 2 方向 = Pass/Fail 両方の試験ケース 28 以上)
- **境界試験:** 不正遷移を全 (状態, イベント) 組合せで注入、拒否されることを確認
- **プロパティ試験(hypothesis):** 任意のイベント列に対して、最終状態が TRANSITION_TABLE から到達可能な状態のみであること
- **並行性試験:** 複数スレッドから同時に `request_transition` を呼び出し、状態不整合が発生しないことを確認

#### 4.1.G Inc.2 拡張(v0.5、CR-0009 / Step 20 E、骨格)

**Inc.2 で UNIT-001.1 に追補する変更点(SAD v0.2 §4.3.1 + INC2-SCOPE-VIP-001 §6.2 連携):**

- **アラーム発報経路追加:** 検知群(ARCH-006)からの IF-U-013 `request_state_transition(target: StateKind, reason: DetectionReason)` を受け、ERROR / PAUSED 遷移を駆動。発報自体は ARCH-007.1 Alarm Reporter Core が IF-U-007 `report_alarm` 経由で行うため、本 UNIT は **状態遷移と発報依頼の橋渡し役**。
- **ACK / SILENCE 状態遷移追加:** SRS-044(アラーム確認・消音、IEC 60601-1-8 §6.4 準拠)に従い、状態機械にアラーム確認 / 消音状態 を追加。具体的状態名・遷移表は SDD 後続改訂(v0.6 候補)で詳細化。
- **新規イベント候補:** `ALARM_RAISED` / `ALARM_ACKED` / `ALARM_SILENCED` / `ALARM_CLEARED` 等を `EventKind` enum に追加。各イベントに対する状態遷移表エントリは SDD v0.6 候補で詳細化。
- **新規 RCM 関連:** RCM-006 アラーム発報必達 = 検知群が `request_state_transition` を発行できなかった場合の対処(本 UNIT の責務)、ALARM 経路と既存 RCM-019 状態遷移保護との整合確認。

**SDD v0.6 候補で詳細化する項目:**

- アラーム発報経路の状態遷移表(具体的状態名 + ALARM_RAISED/ACKED/SILENCED/CLEARED 各イベントとの対応)
- IF-U-013 / IF-U-007 呼出順序契約(検知群 → State Machine → Alarm Reporter Core の順)
- ACK / SILENCE 状態の永続化要否(SRS-DATA-001 連携、Inc.2 範囲では非永続を仮置)
- IEC 60601-1-8 §6.4 高優先度アラーム消音時間制限(≤ 120 秒)の State Machine 側強制(Alarm Reporter Core 側のみで強制 = State Machine 側は通知のみと役割分離)

**主要 API(候補、後続改訂で詳細化):**

| 関数・メソッド | 引数 | 戻り値 | 概要 |
|--------------|------|-------|------|
| `request_state_transition(target: StateKind, reason: DetectionReason) -> Result[None, StateMachineError]` | 検知群からの遷移依頼 | 成功: `Ok(None)` / 失敗: `Err(InvalidTransitionError)` | IF-U-013、検知時の ERROR / PAUSED 駆動 |
| `request_alarm_acknowledge(alarm_id: str) -> Result[None, StateMachineError]` | アラーム ID | 同上 | Control API 経由の ACK 受領 → ALARM_ACKED 遷移 |
| `request_alarm_silence(alarm_id: str, duration_sec: int) -> Result[None, StateMachineError]` | アラーム ID + 消音時間 | 同上 | 同上、ALARM_SILENCED 遷移 |

**依存:** ARCH-006 検知群(IF-U-013)、ARCH-005.1 Control API(IF-U-014 / SRS-044)、ARCH-007.1 Alarm Reporter Core(IF-U-007 経由通知)

**安全クラス:** C(非分離継続、SAD §9 SEP-000)

---

### 4.2 UNIT-001.4: Flow Command Validator

- **目的 / 責務:** Control Loop から Pump Simulator に送出される流量指令値を、送出直前に範囲検証・設定値一致検証する(RCM-001 実装)。検証失敗時は指令を中止し State Machine に ERROR を誘発させる。
- **関連 SRS:** SRS-O-001, SRS-RCM-001, SRS-005
- **関連 RCM:** RCM-001(流量指令範囲チェック)
- **安全クラス:** C

#### 4.2.A 公開 API

| 関数・メソッド | 引数 | 戻り値 | 事前条件 | 事後条件 | エラー処理 |
|----------------|------|-------|---------|---------|-----------|
| `validate(command: FlowCommand, context: ControlContext) -> ValidationResult` | FlowCommand(flow_rate, timestamp)、ControlContext(current_settings, current_state) | `Ok(validated: ValidatedFlowCommand)` / `Err(reason: ValidationReason)` | 引数は非 None、Decimal 型 | 副作用なし(純粋関数) | 全て戻り値で表現、例外は発生させない |

#### 4.2.B データ構造

| 名称 | 型 | 値域 | 意味 |
|------|----|------|------|
| `FlowCommand` | frozen dataclass | — | 入力。`flow_rate: Decimal`, `timestamp: Monotonic` |
| `ValidatedFlowCommand` | frozen dataclass | — | 出力(Ok 時のみ)。`flow_rate: Decimal`, `approved_at: Monotonic` |
| `ValidationReason` | Enum | 4 値: OUT_OF_RANGE / MISMATCH_WITH_SETTINGS / NEGATIVE / NAN_OR_INFINITE | 拒否理由 |

#### 4.2.C アルゴリズム

```python
# 擬似コード
MIN_FLOW = Decimal("0.0")
MAX_FLOW = Decimal("1200.0")
TOLERANCE = Decimal("0.05")  # 設定値との 5% 許容誤差(設定値 0 以外)

def validate(command: FlowCommand, context: ControlContext) -> ValidationResult:
    # 1. 特殊値の排除
    if command.flow_rate.is_nan() or command.flow_rate.is_infinite():
        return Err(NAN_OR_INFINITE)
    # 2. 範囲検証
    if command.flow_rate < MIN_FLOW:
        return Err(NEGATIVE)
    if command.flow_rate > MAX_FLOW:
        return Err(OUT_OF_RANGE)
    # 3. 設定値との整合性(RUNNING 状態のときのみ)
    if context.current_state == State.RUNNING:
        expected = context.current_settings.flow_rate
        if expected == Decimal("0.0"):
            if command.flow_rate != Decimal("0.0"):
                return Err(MISMATCH_WITH_SETTINGS)
        else:
            diff_ratio = abs(command.flow_rate - expected) / expected
            if diff_ratio > TOLERANCE:
                return Err(MISMATCH_WITH_SETTINGS)
    # 4. 合格
    return Ok(ValidatedFlowCommand(
        flow_rate=command.flow_rate,
        approved_at=command.timestamp
    ))
```

#### 4.2.D 資源使用量・タイミング制約

- 純粋関数、ステートレス、ロック不要
- 実行時間: 数 μs(Decimal 演算 3〜4 回 + 比較)
- 呼出頻度: 制御サイクルごと(10 Hz = 100 ms)
- スレッド安全: 完全にスレッドセーフ(共有状態なし)

#### 4.2.E 例外・異常系

| 異常条件 | 検出方法 | 処置 |
|---------|---------|------|
| NaN / Infinite | Decimal の `is_nan()` / `is_infinite()` | `Err(NAN_OR_INFINITE)` |
| 負数 | 比較演算 | `Err(NEGATIVE)` |
| 最大値超過 | 比較演算 | `Err(OUT_OF_RANGE)` |
| 設定値との不整合 | 比率計算 | `Err(MISMATCH_WITH_SETTINGS)` |
| 引数が None / 型違反 | Python 型ヒント + pydantic 段階で排除 | 本ユニットでは起きない前提、発生した場合は呼出側のバグ |

#### 4.2.F 検証方法(§5.4.4 準拠)

- **境界値試験:** `MIN_FLOW - ε`, `MIN_FLOW`, `MIN_FLOW + ε`, `MAX_FLOW - ε`, `MAX_FLOW`, `MAX_FLOW + ε` の 6 点 + NaN + Inf
- **設定値不一致試験:** 許容誤差 ±5% の境界(±4.99%, ±5.00%, ±5.01%)
- **hypothesis プロパティ試験:** 任意の FlowCommand に対して「戻り値は常に Ok または定義済み Err のいずれか」「Ok の場合 flow_rate は範囲内」
- **冪等性試験:** 同じ入力を 2 回呼び出して同じ結果が返ること

---

### 4.3 UNIT-002.4: HW-side Failsafe Timer

- **目的 / 責務:** 仮想ポンプ側で、Control Loop からのハートビート途絶(500 ms 以上未更新)を検知した場合、**仮想ポンプ自身が** 流量を 0 にフェイルセーフ停止する。これは制御側 Watchdog(UNIT-001.5)とは独立した **二重冗長** の HW 側 RCM(RCM-004 HW 側)である。
- **関連 SRS:** SRS-RCM-004, SRS-032(仮想 HW の能力)
- **関連 RCM:** RCM-004(ハートビート、HW 側)
- **安全クラス:** C

#### 4.3.A 公開 API

| 関数・メソッド | 引数 | 戻り値 | 事前条件 | 事後条件 | エラー処理 |
|----------------|------|-------|---------|---------|-----------|
| `heartbeat(ts: Monotonic) -> None` | 現在時刻(単調時計) | — | なし | 内部の `_last_heartbeat = ts` | なし(失敗しない) |
| `start(pump: PumpController) -> None` | 対象ポンプ | — | スレッド未起動 | 監視スレッド起動 | 2 重起動は `RuntimeError` |
| `stop() -> None` | — | — | — | 監視スレッド停止 | 未起動時は no-op |
| `is_tripped() -> bool` | — | bool | — | — | — |

#### 4.3.B データ構造

| 名称 | 型 | 値域 | 意味 | スレッド安全性 |
|------|----|------|------|--------------|
| `_last_heartbeat` | `float`(monotonic 秒) | — | 最終ハートビート時刻 | `_lock` 保護 |
| `_lock` | `threading.Lock` | — | `_last_heartbeat` 保護 | — |
| `_thread` | `threading.Thread` | — | 監視スレッド | start/stop で排他 |
| `_stop_event` | `threading.Event` | — | 停止シグナル | スレッド間通信 |
| `_tripped` | `bool` | — | フェイルセーフ発動済みフラグ | `_lock` 保護 |
| `_pump_ref` | `PumpController` | — | 停止対象 | 保持のみ |

#### 4.3.C アルゴリズム

```python
HEARTBEAT_TIMEOUT = 0.5  # 500 ms
MONITOR_INTERVAL = 0.1   # 100 ms で検査

def _monitor_loop(self):
    while not self._stop_event.is_set():
        now = time.monotonic()
        with self._lock:
            last = self._last_heartbeat
            tripped = self._tripped
        if not tripped and (now - last) > HEARTBEAT_TIMEOUT:
            # フェイルセーフ発動
            self._pump_ref.force_stop_failsafe(reason="HEARTBEAT_TIMEOUT")
            with self._lock:
                self._tripped = True
            self._logger.log_failsafe_trip(now, last)
        self._stop_event.wait(MONITOR_INTERVAL)

def heartbeat(self, ts):
    with self._lock:
        if not self._tripped:  # Tripped 後のハートビートは無視(復帰は明示操作)
            self._last_heartbeat = ts
```

**キーポイント:**

- 500 ms タイムアウトは制御サイクル 100 ms に対し 5 周期分の余裕
- Tripped 状態からの復帰は `ERROR_RESET` コマンド → State Machine 経由 → Watchdog/Failsafe の再初期化が必要(自動復帰しない、安全側)
- 監視ループは `wait()` で ブロックし CPU を無駄にしない

#### 4.3.D 資源使用量・タイミング制約

- スレッド 1 本(監視ループ)、メモリ数 KB
- 監視遅延: 最大 MONITOR_INTERVAL(100 ms)+ ロック競合(通常 μs オーダー)
- **実効フェイルセーフ検出時間:** HEARTBEAT_TIMEOUT + MONITOR_INTERVAL = 最大 600 ms(要件 500 ms にマージンを見込むなら HEARTBEAT_TIMEOUT を短くする必要あり → 本 SDD では仕様どおり 500 ms + 100 ms 検査 = 最大 600 ms を許容とする。SRS-RCM-004 の文言は「500 ms を超えて更新されない場合」なので、タイムアウト判定は `>` で 500 ms 境界自体は合格。検証で確認)
- 呼出コンテキスト: `heartbeat` は制御スレッド、監視は専用スレッド

#### 4.3.E 例外・異常系

| 異常条件 | 検出方法 | 処置 |
|---------|---------|------|
| ポンプ停止処理の例外 | `force_stop_failsafe` の例外 | ログして継続、次周期で再試行。プロセスを落とさない(残余ポンプが他スレッドで制御されている可能性を考慮) |
| 単調時計のロールオーバー | `time.monotonic()` は Python 仕様で単調増加保証、実用上問題なし | — |
| start/stop の 2 重呼び出し | `_thread.is_alive()` チェック | start: `RuntimeError`、stop: no-op |

#### 4.3.F 検証方法(§5.4.4 準拠)

- **ユニット試験:** `heartbeat` が正しく `_last_heartbeat` を更新する
- **結合試験(故障注入):** Control Loop のハートビートを 600 ms 停止 → Pump が stop 状態になる
- **境界試験:** ハートビート停止 499/500/501 ms のそれぞれで動作確認
- **並行性試験:** 高頻度ハートビートと監視スレッドの競合が発生しないこと
- **Tripped 後の挙動試験:** Tripped 状態でハートビート再開しても自動復帰しないこと

---

### 4.4 UNIT-003.3: Atomic File Writer

- **目的 / 責務:** 永続化データをファイルシステムに **atomic に** 書き込む。書き込み中の電源断・プロセス強制終了が発生しても、永続化ファイルが半端な状態にならないことを保証する。1 世代のバックアップを保持する。
- **関連 SRS:** SRS-DATA-002, SRS-DATA-003
- **関連 RCM:** RCM-015 の前提(整合性検証対象ファイルを壊さない)
- **安全クラス:** C

#### 4.4.A 公開 API

| 関数・メソッド | 引数 | 戻り値 | 事前条件 | 事後条件 | エラー処理 |
|----------------|------|-------|---------|---------|-----------|
| `write(data: bytes, target_path: Path) -> WriteResult` | 書き込みデータ、最終配置パス | `Ok(bytes_written)` / `Err(IOError cause)` | `target_path` の親ディレクトリが存在 | 成功: `target_path` 更新 + `target_path.bak` に旧データ / 失敗: target 不変 | すべて戻り値で表現 |
| `read(target_path: Path) -> ReadResult` | 最終配置パス | `Ok(bytes)` / `Err(FileNotFoundError, PermissionError, IOError)` | — | 副作用なし | 戻り値で表現 |
| `rollback(target_path: Path) -> RollbackResult` | 最終配置パス | `Ok(None)` / `Err(NoBackupError \| IOError)` | `.bak` が存在する | target = bak の内容 | 戻り値で表現 |

#### 4.4.B アルゴリズム(atomic 書き込み)

```python
# target_path = /path/to/state.json
# temp_path   = /path/to/state.json.tmp.<pid>.<ts>
# bak_path    = /path/to/state.json.bak

def write(data: bytes, target_path: Path) -> WriteResult:
    temp_path = target_path.with_suffix(target_path.suffix + f".tmp.{os.getpid()}.{int(time.time()*1000)}")
    bak_path = target_path.with_suffix(target_path.suffix + ".bak")
    try:
        # 1. temp に書き込み + fsync(クラッシュ時のデータ損失を避ける)
        with open(temp_path, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        # 2. target が既にあれば bak にリネーム(atomic)
        if target_path.exists():
            os.replace(target_path, bak_path)
        # 3. temp を target に atomic リネーム
        os.replace(temp_path, target_path)
        # 4. ディレクトリの fsync(ファイル名変更の永続化保証、POSIX のみ)
        if hasattr(os, "O_DIRECTORY"):
            dir_fd = os.open(target_path.parent, os.O_DIRECTORY)
            try:
                os.fsync(dir_fd)
            finally:
                os.close(dir_fd)
        return Ok(len(data))
    except OSError as e:
        # クリーンアップ(ベストエフォート)
        if temp_path.exists():
            try:
                temp_path.unlink()
            except OSError:
                pass
        return Err(e)
```

**鍵となる不変条件:**

- `os.replace` は POSIX で atomic、Windows でも Python 3.8+ で atomic(同一ボリューム上)
- fsync は OS による cache 失効前の耐障害性を担保
- target と bak は決して同時に不在にならない(2 ステップ目で target → bak は rename、3 ステップ目で temp → target は rename、間に target が無い時間は数 μs だが、その間に電源断しても bak は生きている)
- `.tmp` が中途で残ることはあるが、次回起動時に `load` は target を読むだけで temp は参照しない(temp のクリーンアップは別責務)

#### 4.4.C データ構造

本ユニットは状態を持たない(純粋関数的)。スレッドごと独立に動作する。同一 target_path への並行書き込みは **呼出側の責任**(上位ユニット ARCH-003 全体で直列化する)。

#### 4.4.D 資源使用量・タイミング制約

- 書き込み: データサイズに比例(本プロジェクトの永続化データは数 KB〜数十 KB 想定)
- fsync は OS に依存、SSD で数 ms、HDD で数十 ms
- SRS-P06(非ブロッキング)を守るため、**呼出は別スレッド/キュー経由**。本ユニット自体は同期 I/O。
- メモリ: `data` 引数分の一時参照のみ、追加の大きなバッファは確保しない

#### 4.4.E 例外・異常系

| 異常条件 | 検出方法 | 処置 |
|---------|---------|------|
| ディスク full | `OSError(ENOSPC)` | `Err(IOError)` を返却、temp 削除試行 |
| 権限エラー | `PermissionError` | 同上 |
| 親ディレクトリ不在 | `FileNotFoundError` | 同上、呼出元が事前条件を担保するはず |
| 書き込み中の電源断 | 原理的に検知不可能 | `load` 側で整合性検証(UNIT-004.1 Integrity Validator)が担保する |
| `.tmp` のクリーンアップ失敗 | 本ユニットでは許容(best effort) | 次回起動時に ARCH-003 全体で孤立 .tmp を検出・削除 |

#### 4.4.F 検証方法(§5.4.4 準拠)

- **基本試験:** write → read で同じデータが戻ること
- **耐障害試験:** write の各ステップ直後にプロセスを KILL → 起動 → load が成功すること(target か bak のいずれかが整合)
- **並行書き込み拒否試験:** 同一 target に複数スレッドから同時 write すると文書化された競合動作(最後勝ち or エラー)
- **fsync 検証:** mock した os.fsync が呼ばれていることを確認
- **ディスク full 試験:** ファイルシステムを満杯にし、`Err(IOError)` が返ること

---

### 4.5 UNIT-004.1: Integrity Validator

- **目的 / 責務:** 起動時に永続レコードの **チェックサム・値域・状態組合せの整合性** を検証する。失敗時は SRS-027 に従ったフェイルセーフデフォルトで起動する。RCM-015 実装の中核。
- **関連 SRS:** SRS-026, SRS-027, SRS-RCM-015
- **関連 RCM:** RCM-015(起動時状態検証)
- **安全クラス:** C

#### 4.5.A 公開 API

| 関数・メソッド | 引数 | 戻り値 | 事前条件 | 事後条件 | エラー処理 |
|----------------|------|-------|---------|---------|-----------|
| `validate(record: RawPersistedRecord) -> ValidationResult` | デシリアライズ済レコード | `Ok(trusted: TrustedRecord)` / `FailsafeRecommended(reasons: list[IntegrityFailure])` | なし | 副作用なし | 戻り値で表現 |

#### 4.5.B 整合性検証の段階的チェック

```python
def validate(record: RawPersistedRecord) -> ValidationResult:
    failures = []
    # 1. スキーマバージョン
    if record.schema_version not in SUPPORTED_SCHEMA_VERSIONS:
        failures.append(SchemaVersionUnsupported(record.schema_version))
    # 2. チェックサム
    recomputed = compute_sha256(record.payload_bytes)
    if recomputed != record.checksum:
        failures.append(ChecksumMismatch(expected=record.checksum, actual=recomputed))
    # 3. 個別フィールドの値域
    if not (Decimal("0.0") <= record.settings.flow_rate <= Decimal("1200.0")):
        failures.append(FlowRateOutOfRange(record.settings.flow_rate))
    if not (Decimal("0.0") <= record.settings.dose_volume <= Decimal("9999.9")):
        failures.append(DoseVolumeOutOfRange(record.settings.dose_volume))
    if not (1 <= record.settings.duration_min <= 5999):
        failures.append(DurationOutOfRange(record.settings.duration_min))
    # 4. Settings の一貫性(SRS-004)
    if not check_settings_consistency(record.settings, tolerance=Decimal("0.01")):
        failures.append(SettingsInconsistent(record.settings))
    # 5. 状態組合せの整合性
    if record.runtime_state.state == State.RUNNING and record.runtime_state.current_flow == Decimal("0.0"):
        failures.append(StateContradiction("RUNNING but current_flow=0"))
    if record.runtime_state.accumulated_volume > record.settings.dose_volume:
        failures.append(AccumulationExceedsDose(...))
    if record.runtime_state.state == State.INITIALIZING:  # 保存されるはずがない状態
        failures.append(UnsavableState(record.runtime_state.state))
    # 判定
    if failures:
        return FailsafeRecommended(reasons=failures)
    return Ok(TrustedRecord.from_raw(record))
```

#### 4.5.C データ構造

| 名称 | 型 | 意味 |
|------|----|------|
| `IntegrityFailure` | sealed hierarchy(Enum + dataclass) | 失敗理由の階層。各理由にメタデータ |
| `TrustedRecord` | frozen dataclass | 検証済レコード(後続処理で型で検証済を保証) |
| `SUPPORTED_SCHEMA_VERSIONS` | frozenset[int] | 互換マイグレーションを含むバージョン集合 |

#### 4.5.D 資源使用量・タイミング制約

- SHA-256 計算: 数十 KB データで ms 以下
- 純粋関数、スレッドセーフ
- 起動時 1 回のみ呼ばれる

#### 4.5.E 例外・異常系

| 異常条件 | 検出方法 | 処置 |
|---------|---------|------|
| record フィールドの型違反 | pydantic モデル事前検証 | 本ユニット到達前に ValidationError |
| SHA-256 計算失敗 | hashlib の例外 | 原理的に発生しない(ライブラリが保証)、発生時はプロセス終了(フェイルセーフ) |
| UNKNOWN 追加フィールド | pydantic で `strict=True` にすれば検出 | 失敗として記録 |

#### 4.5.F 検証方法(§5.4.4 準拠)

- **正常系試験:** 有効なレコードに対し `Ok` が返る
- **破損注入試験:** チェックサム・スキーマ・値域・状態組合せのそれぞれを単独で破損させ、対応する `IntegrityFailure` が返ることを全 10 種以上のケースで確認
- **多重破損試験:** 複数の失敗が同時に検出され、すべての理由が `failures` リストに含まれること
- **hypothesis プロパティ試験:** 任意のランダムバイト列を RawPersistedRecord に変換した場合、ValidationResult が必ず Ok または FailsafeRecommended のどちらか(例外を投げない)

---

### 4.6 UNIT-001.2: Control Loop

- **目的 / 責務:** 100 ms 周期(SRS-P02 ±10%)で仮想ポンプに流量指令を送出し、積算量・経過時間を更新、SW Watchdog(UNIT-001.5)および HW-side Failsafe Timer(UNIT-002.4)へハートビートを送出する。SRS-031 の自動停止条件(積算量 ≥ 設定量 / 経過時間 ≥ 設定時間)を判定し、State Machine に AUTO_STOP 系イベントを発行する。検証失敗時は ERROR 誘発。
- **関連 SRS:** SRS-011, SRS-012, SRS-031, SRS-P02, SRS-RCM-004
- **関連 RCM:** RCM-004(ハートビート、SW 送出側)
- **安全クラス:** C

#### 4.6.A 公開 API

| 関数・メソッド | 引数 | 戻り値 | 事前条件 | 事後条件 | エラー処理 |
|----------------|------|-------|---------|---------|-----------|
| `start() -> None` | — | — | スレッド未起動 | 周期スレッド起動 | 2 重起動: `RuntimeError` |
| `stop() -> None` | — | — | — | 周期スレッド停止(現周期完了後) | 未起動: no-op |
| `is_running() -> bool` | — | bool | — | — | — |

#### 4.6.B データ構造

| 名称 | 型 | 値域 | 意味 | スレッド安全性 |
|------|----|------|------|--------------|
| `_period_sec` | `float` | 0.1(定数) | 周期 | const |
| `_thread` | `threading.Thread` | — | 周期スレッド | start/stop で排他 |
| `_stop_event` | `threading.Event` | — | 停止シグナル | thread-safe |
| `_state_machine` | StateMachine | — | 状態照会・イベント発行先 | 注入依存 |
| `_validator` | FlowCommandValidator | — | UNIT-001.4 注入 | const ref |
| `_pump` | PumpController | — | UNIT-002.1 注入 | const ref |
| `_observer` | PumpObserver | — | UNIT-002.2 注入 | const ref |
| `_sw_watchdog` | Watchdog | — | UNIT-001.5 注入 | const ref |
| `_hw_watchdog` | HwSideFailsafeTimer | — | UNIT-002.4 注入 | const ref |
| `_settings_provider` | `Callable[[], Settings]` | — | 設定読み出し関数 | スレッドセーフ前提 |

#### 4.6.C アルゴリズム

```python
PERIOD_SEC = 0.1            # SRS-P02
PERIOD_TOLERANCE = 0.1      # ±10%

def _loop(self):
    next_deadline = time.monotonic() + PERIOD_SEC
    while not self._stop_event.is_set():
        try:
            self._tick()
        except Exception as e:
            # 制御ループの例外は致命的: ERROR 誘発 + ループ終了
            self._state_machine.on_watchdog_timeout(WatchdogReason.CONTROL_LOOP_EXCEPTION)
            self._logger.log_critical_loop_exception(e)
            return
        sleep_sec = next_deadline - time.monotonic()
        if sleep_sec > 0:
            self._stop_event.wait(sleep_sec)   # stop に即応
        else:
            self._logger.log_period_overrun(elapsed=PERIOD_SEC - sleep_sec)
        next_deadline += PERIOD_SEC

def _tick(self):
    if self._state_machine.current() != State.RUNNING:
        return
    now = time.monotonic()
    # 1. ハートビート(両 Watchdog)— 制御処理に先立つ
    # CR-0005 (a):各 Watchdog 実装(SDD §4.8.A / §4.3.A)が内部 clock で
    # timestamp を取得するため、ControlLoop は引数なしで呼出。両 Watchdog の
    # 受信 timestamp は数 μs 程度ずれるが RCM-003/004 への機能影響なし。
    self._sw_watchdog.heartbeat()
    self._hw_watchdog.heartbeat()
    # 2. Validator → 流量指令
    settings = self._settings_provider()
    cmd = FlowCommand(flow_rate=settings.flow_rate, timestamp=now)
    result = self._validator.validate(cmd, ControlContext(settings, State.RUNNING))
    if result.is_err():
        self._state_machine.request_transition(
            TransitionEvent(EventKind.WDT_TIMEOUT,
                            meta={"reason": "validation_failed", "detail": result.err}))
        return
    self._pump.set_flow_rate(result.ok.flow_rate)
    # 3. 自動停止判定(SRS-031)
    snap = self._observer.observe()
    if snap.accumulated_volume >= settings.dose_volume:
        self._state_machine.request_transition(TransitionEvent(EventKind.AUTO_STOP_DOSE_REACHED))
    elif snap.elapsed_min >= settings.duration_min:
        self._state_machine.request_transition(TransitionEvent(EventKind.AUTO_STOP_DURATION_REACHED))
```

**キーポイント:**

- **monotonic deadline 方式**:`time.sleep(0.1)` 累積誤差を回避。`next_deadline` を加算し続けることで長期 drift を防ぐ
- **`Event.wait()`** で停止要求への即応(`time.sleep` だと最大 100 ms 残る)
- **ハートビートは tick 先頭**:仮にこの後の処理で例外が発生しても、Watchdog からみた「生存」は記録される(逆順だと validator 例外時に Watchdog がタイムアウトして二重 ERROR になる)
- **指令送出 → 自動停止判定の順序**:同周期内に最新スナップショットで判定するため

#### 4.6.D 資源使用量・タイミング制約

- スレッド 1 本(専用周期スレッド)
- メモリ: 数 KB(注入依存のみ保持、I/O バッファなし)
- 周期精度: 100 ms ±10%(SRS-P02)。`next_deadline - time.monotonic()` を測定して評価
- CPU 負荷: tick 1 回あたり ≤ 1 ms(Validator 数 μs + Pump.set_flow_rate 数 μs + Observer 数 μs)、占有率 ≤ 1%

#### 4.6.E 例外・異常系

| 異常条件 | 検出方法 | 処置 |
|---------|---------|------|
| Validator が Err | `result.is_err()` | State Machine に `WDT_TIMEOUT` イベント送出、tick 終了(次周期で State.ERROR を確認しスキップ) |
| 制御ループ自体の例外 | try/except | ERROR 誘発、ループ終了。再起動は明示的 `start()` |
| 周期遅延(オーバーラン) | `sleep_sec <= 0` | ログのみ。連続発生時は別途 SW Watchdog がタイムアウト判定 |
| `_settings_provider` 例外 | `_tick` 内 try/except 範囲 | 上記制御ループ例外と同じ扱い |
| `_pump.set_flow_rate` 例外 | 同上 | 同上(致命的扱い) |

#### 4.6.F 検証方法(§5.4.4 準拠)

- **基本試験:** `start()` → 100 ms 経過後に `Pump.set_flow_rate` がモックで呼ばれる
- **周期精度試験:** 1000 周期分の `next_deadline - actual_tick_time` 統計を取り、P95 が ±10% 内
- **stop 応答性試験:** `stop()` 呼び出しから次周期完了までの遅延が PERIOD_SEC + 数 ms 以内
- **自動停止試験:** `accumulated_volume` を漸増させ、設定量到達時刻に AUTO_STOP_DOSE_REACHED が送出
- **Validator 失敗試験:** Validator モックが常に Err → State Machine に WDT_TIMEOUT 受信
- **致命的例外試験:** Pump モックが例外 → State Machine が ERROR、ループ終了
- **並行性試験:** start/stop 高速反復で 2 重起動例外が一貫して出ること、リソースリーク無し

---

### 4.7 UNIT-001.3: Command Handler

- **目的 / 責務:** Control API(UNIT-005.1)から受領した外部コマンド(start/stop/pause/resume/reset/error_reset/confirm_resume)を順次 State Machine に渡す。SRS-P03(start ≤ 100 ms)/ SRS-P04(stop ≤ 50 ms)を満たすため、**stop 系コマンドはファストパス**(キューをバイパス)で処理する。
- **関連 SRS:** SRS-010, SRS-013, SRS-014, SRS-P03, SRS-P04
- **関連 RCM:** —(直接実装なし。State Machine RCM-019 と連携)
- **安全クラス:** C

#### 4.7.A 公開 API

| 関数・メソッド | 引数 | 戻り値 | 事前条件 | 事後条件 | エラー処理 |
|----------------|------|-------|---------|---------|-----------|
| `enqueue(cmd: Command) -> AcceptResult` | Command(frozen) | `Accepted(token: str)` / `Rejected(reason: RejectReason)` | dispatch スレッド起動済 | 通常: キュー投入 / stop: ファストパスへ / 不正状態: 拒否 | 戻り値で表現、例外なし |
| `await_completion(token: str, timeout_ms: int) -> CompletionResult` | token、待機時間 | `Completed(state)` / `TimedOut` / `Failed(error)` | enqueue 済 token | 結果回収 + 内部 cleanup | timeout は TimedOut |
| `start() -> None` / `stop() -> None` | — | — | start: スレッド未起動 / stop: — | dispatch スレッドの起動/停止 | 2 重 start: `RuntimeError`、stop 未起動: no-op |

#### 4.7.B データ構造

| 名称 | 型 | 値域 | 意味 | スレッド安全性 |
|------|----|------|------|--------------|
| `_queue` | `queue.Queue[CommandTask]` | maxsize=16 | 通常キュー(FIFO) | thread-safe |
| `_pending_stop` | `Optional[CommandTask]` | None / 1 件 | stop 系ファストパス保持 | `_lock` 保護 |
| `_completions` | `dict[str, threading.Event]` | — | token → 完了通知 | `_lock` 保護 |
| `_results` | `dict[str, CompletionResult]` | — | 結果格納 | `_lock` 保護 |
| `_lock` | `threading.Lock` | — | 上記辞書群の保護 | — |
| `_wake_event` | `threading.Event` | — | dispatch ループ起こし(stop 即応) | thread-safe |
| `_state_machine` | StateMachine | — | 注入 | const ref |
| `_thread`, `_stop_event` | Thread/Event | — | dispatch スレッド管理 | start/stop で排他 |

#### 4.7.C アルゴリズム

```python
MAX_QUEUE_SIZE = 16
STOP_KINDS = {CommandKind.STOP, CommandKind.ERROR_RESET}  # ファストパス対象

def enqueue(self, cmd: Command) -> AcceptResult:
    if not _is_acceptable_in_state(cmd, self._state_machine.current()):
        return Rejected(RejectReason.INVALID_FOR_CURRENT_STATE)
    task = CommandTask(token=str(uuid4()), cmd=cmd, enqueued_at=time.monotonic())
    if cmd.kind in STOP_KINDS:
        # ファストパス: 既存キューを破棄し、pending_stop に格納
        with self._lock:
            self._pending_stop = task
            self._completions[task.token] = threading.Event()
            while not self._queue.empty():
                try:
                    discarded = self._queue.get_nowait()
                    self._results[discarded.token] = Failed(SupersededByStopError())
                    ev = self._completions.get(discarded.token)
                    if ev: ev.set()
                except queue.Empty:
                    break
        self._wake_event.set()
        return Accepted(task.token)
    # 通常パス
    try:
        self._queue.put_nowait(task)
    except queue.Full:
        return Rejected(RejectReason.QUEUE_FULL)
    with self._lock:
        self._completions[task.token] = threading.Event()
    return Accepted(task.token)

def _dispatch_loop(self):
    while not self._stop_event.is_set():
        # 1. ファストパス優先
        with self._lock:
            stop_task = self._pending_stop
            self._pending_stop = None
        if stop_task is not None:
            self._handle(stop_task)
            continue
        # 2. 通常キュー
        try:
            task = self._queue.get(timeout=0.05)  # 50 ms ごとに stop_event 再確認
        except queue.Empty:
            self._wake_event.wait(0.0)  # 即時クリア
            self._wake_event.clear()
            continue
        self._handle(task)

def _handle(self, task: CommandTask):
    try:
        event = self._cmd_to_event(task.cmd)
        result = self._state_machine.request_transition(event)
        completion = Completed(state=result.ok) if result.is_ok() else Failed(error=result.err)
    except Exception as e:
        completion = Failed(error=e)
    with self._lock:
        self._results[task.token] = completion
        ev = self._completions.get(task.token)
    if ev is not None:
        ev.set()

def await_completion(self, token, timeout_ms):
    with self._lock:
        ev = self._completions.get(token)
    if ev is None:
        return Failed(UnknownTokenError(token))
    if not ev.wait(timeout_ms / 1000):
        return TimedOut(elapsed_ms=timeout_ms)
    with self._lock:
        # cleanup: 1 度回収したら以降 UnknownToken 扱い
        self._completions.pop(token, None)
        return self._results.pop(token)
```

**SRS-P03/P04 への対応(設計上の重要判断):**

- start(SRS-P03 = 100 ms): 通常パス → put + dispatch ピックアップ(最大 50 ms get タイムアウト)+ State Machine 遷移(< 1 ms)= **通常 60 ms 以内**
- stop(SRS-P04 = 50 ms): **ファストパス** → enqueue で `_pending_stop` セット + `_wake_event.set()` + dispatch がロック取得 + State Machine 遷移 = **通常 5 ms 以内**

#### 4.7.D 資源使用量・タイミング制約

- スレッド 1 本(dispatch)
- メモリ: 通常キュー 16 + 辞書群 = 数 KB
- 応答時間: SRS-P03/P04 を満たすことを §4.7.F 試験で検証
- 呼出頻度: ユーザコマンドは秒に 1〜数回程度

#### 4.7.E 例外・異常系

| 異常条件 | 検出方法 | 処置 |
|---------|---------|------|
| キュー満杯 | `put_nowait` の `queue.Full` | `Rejected(QUEUE_FULL)` |
| 不正状態でのコマンド | `_is_acceptable_in_state` | `Rejected(INVALID_FOR_CURRENT_STATE)` |
| stop で破棄された未処理コマンド | ファストパス処理時 | 該当 token を `Failed(SupersededByStopError)` で完了通知 |
| 不明 token への await | `_completions` に存在しない | `Failed(UnknownTokenError)` |
| timeout | `Event.wait` の False | `TimedOut` |
| dispatch スレッド例外(個別 task) | `_handle` の try/except | 該当 task のみ Failed、ループ継続 |
| dispatch スレッド致命例外(ループ自体) | 上位 try/except 不在 → スレッド終了 | 監視は呼出側責務(検証で確認) |

#### 4.7.F 検証方法(§5.4.4 準拠)

- **基本試験:** `enqueue(START)` → State Machine に `CMD_START` 受信
- **応答時間試験(SRS-P03/P04):** `enqueue` 〜 `await_completion` 完了の **P95** を測定。start ≤ 100 ms、stop ≤ 50 ms
- **stop ファストパス試験:** キューに 10 件溜めた状態で STOP を enqueue → 50 ms 以内に State Machine が STOP 受信、他 10 件は `Failed(SupersededByStopError)`
- **キュー満杯試験:** 16 件投入後 17 件目で `Rejected(QUEUE_FULL)`
- **不正状態試験:** `RUNNING` 中に START → `Rejected(INVALID_FOR_CURRENT_STATE)`
- **token 一意性試験:** 並行 enqueue 1000 件で全 token がユニーク
- **start/stop 反復試験:** 100 回反復してリソースリーク無し、2 重 start 例外が一貫

---

### 4.8 UNIT-001.5: Watchdog (SW side)

- **目的 / 責務:** Control Loop(UNIT-001.2)からのハートビートを監視。**300 ms** 以上未更新で State Machine に ERROR 遷移を要求する(RCM-003 SW 側)。HW-side Failsafe Timer(UNIT-002.4、500 ms)とは独立した二重冗長の SW 側であり、**早めに(300 < 500)** 検知することで、まず State 機械的安全状態へ持ち込み、その後も復旧しなければ HW 側が物理的に停止する階層的防御を実現する。
- **関連 SRS:** SRS-RCM-003
- **関連 RCM:** RCM-003(ハートビート、SW 側監視)
- **安全クラス:** C

#### 4.8.A 公開 API

| 関数・メソッド | 引数 | 戻り値 | 事前条件 | 事後条件 | エラー処理 |
|----------------|------|-------|---------|---------|-----------|
| `heartbeat(ts: Monotonic) -> None` | 単調時計 | — | なし | `_last_heartbeat = ts`(Tripped 後は無視) | 失敗なし |
| `start() -> None` | — | — | スレッド未起動 | 監視スレッド起動 | 2 重起動 `RuntimeError` |
| `stop() -> None` | — | — | — | 監視スレッド停止 | 未起動: no-op |
| `is_tripped() -> bool` | — | bool | — | — | — |

#### 4.8.B データ構造

| 名称 | 型 | 値域 | 意味 | スレッド安全性 |
|------|----|------|------|--------------|
| `_last_heartbeat` | `float`(monotonic 秒) | — | 最終ハートビート時刻 | `_lock` 保護 |
| `_lock` | `threading.Lock` | — | フィールド保護 | — |
| `_thread` | `threading.Thread` | — | 監視スレッド | start/stop で排他 |
| `_stop_event` | `threading.Event` | — | 停止シグナル | thread-safe |
| `_tripped` | `bool` | — | 発動済みフラグ | `_lock` 保護 |
| `_state_machine` | StateMachine | — | ERROR 誘発先 | 注入 |

#### 4.8.C アルゴリズム

```python
HEARTBEAT_TIMEOUT = 0.3   # 300 ms (SW 側、HW 500 ms より早期)
MONITOR_INTERVAL = 0.05   # 50 ms

def _monitor(self):
    while not self._stop_event.is_set():
        now = time.monotonic()
        with self._lock:
            last = self._last_heartbeat
            tripped = self._tripped
        if not tripped and (now - last) > HEARTBEAT_TIMEOUT:
            # State Machine に WDT_TIMEOUT 通知 → ERROR 遷移
            self._state_machine.on_watchdog_timeout(WatchdogReason.SW_HEARTBEAT_TIMEOUT)
            with self._lock:
                self._tripped = True
            self._logger.log_sw_watchdog_trip(now, last)
        self._stop_event.wait(MONITOR_INTERVAL)

def heartbeat(self, ts):
    with self._lock:
        if not self._tripped:
            self._last_heartbeat = ts
```

**タイムアウト値の出典根拠(SDD v0.2 で確定):**

- 制御周期 100 ms × 3 周期 = 300 ms。1〜2 周期の遅延は許容、3 周期連続欠落で異常と判定
- HW 側 500 ms より 200 ms 早く発動 → SW で先に State 機械を ERROR にし、コマンド類を遮断した後、なお流量が継続する場合に HW がフィジカル停止
- SRS-RCM-003 の文言は「タイムアウト時間は 300 ms 以下」と読める想定(SRS 改訂提案として申し送り)

#### 4.8.D 資源使用量・タイミング制約

- スレッド 1 本、メモリ数 KB
- 検出遅延: 最大 HEARTBEAT_TIMEOUT + MONITOR_INTERVAL = **350 ms**
- 監視ループは `wait()` で sleep し CPU 浪費なし

#### 4.8.E 例外・異常系

| 異常条件 | 検出方法 | 処置 |
|---------|---------|------|
| State Machine `on_watchdog_timeout` 例外 | try/except | ログ + 次周期で再試行(状態遷移は冪等) |
| Tripped 後の heartbeat | `_tripped` チェック | 無視(自動復帰禁止、安全側) |
| start/stop 2 重 | `_thread.is_alive()` | start: `RuntimeError` / stop: no-op |
| 単調時計のロールオーバー | Python 仕様で単調増加保証 | 実用上問題なし |

#### 4.8.F 検証方法(§5.4.4 準拠)

- **基本試験:** `heartbeat(t)` で `_last_heartbeat` 更新
- **境界試験:** 停止後 299 ms / 300 ms / 301 ms / 350 ms それぞれで Trip 有無を確認
- **二重冗長の独立性試験:** UNIT-002.4(HW)と本 UNIT を同時動作させ、SW 側が先に Trip すること(時間順序)
- **State Machine 連携試験:** Trip 時に State Machine が ERROR 状態となること
- **Tripped 後の挙動試験:** Trip 後の heartbeat 再開でも自動復帰しないこと
- **並行性試験:** 高頻度 heartbeat(1 ms 間隔)と監視スレッドで競合しないこと

---

### 4.9 UNIT-002.1: Pump Simulator

- **目的 / 責務:** 流量指令を受け取り、時間経過に応じて積算量・経過時間・現在流量を更新する仮想ポンプモデル。SRS-P01「指示流量に対する実流量誤差 ±5% 以内」を達成する一次遅れモデルを内部に持つ。`force_stop_failsafe` でフェイルセーフ停止可能(UNIT-002.4 から呼び出される)。
- **関連 SRS:** SRS-030, SRS-031, SRS-P01
- **関連 RCM:** RCM-004 の HW 側被呼出側(`force_stop_failsafe`)
- **安全クラス:** C

#### 4.9.A 公開 API

| 関数・メソッド | 引数 | 戻り値 | 事前条件 | 事後条件 | エラー処理 |
|----------------|------|-------|---------|---------|-----------|
| `set_flow_rate(target: Decimal) -> None` | 目標流量(0〜1200 mL/h、Validator で検証済) | — | range 内、failsafe 未発動 | 内部目標値更新、次 advance_time で実流量が漸近 | failsafe 発動中: 無視(no-op、ログ) |
| `advance_time(dt_sec: float) -> None` | 経過時間(秒) | — | dt > 0 | 流量応答更新 + 積算量加算 + 経過時間加算 | dt ≤ 0: `ValueError` |
| `reset() -> None` | — | — | failsafe 未発動 | 全状態を初期値(流量 0、積算 0、時間 0) | failsafe 中: no-op |
| `force_stop_failsafe(reason: str) -> None` | 理由文字列 | — | なし | 流量目標 0、現在流量 0(瞬時)、failsafe フラグ ON、以降 set_flow_rate を無視 | 冪等(2 回目以降は最初の reason を保持) |
| `release_failsafe() -> None` | — | — | failsafe 中 | failsafe フラグ OFF(明示復帰、テスト/ERROR_RESET 経由) | 未発動: no-op |

#### 4.9.B データ構造

| 名称 | 型 | 値域 | 意味 | スレッド安全性 |
|------|----|------|------|--------------|
| `_target_flow` | `Decimal` | 0〜1200 | 目標流量 mL/h | `_lock` 保護 |
| `_current_flow` | `Decimal` | 0〜1200 | 現在流量(漸近値) | `_lock` 保護 |
| `_accumulated_volume` | `Decimal` | 0〜9999.9 | 積算量 mL | `_lock` 保護 |
| `_elapsed_min` | `Decimal` | 0〜5999 | 経過時間 分 | `_lock` 保護 |
| `_failsafe_active` | `bool` | — | フェイルセーフ発動中 | `_lock` 保護 |
| `_failsafe_reason` | `Optional[str]` | None / 文字列 | 発動理由(初発のみ保持) | `_lock` 保護 |
| `_lock` | `threading.RLock` | — | 全フィールド保護 | — |
| `_time_constant_sec` | `float` | 0.5(定数) | 一次遅れ τ | const |

#### 4.9.C アルゴリズム

```python
TIME_CONSTANT = 0.5  # 一次遅れ時定数 [秒]

def advance_time(self, dt_sec: float) -> None:
    if dt_sec <= 0:
        raise ValueError("dt must be positive")
    with self._lock:
        if self._failsafe_active:
            # failsafe 中は流量 0 を維持、時間進行のみ(積算は加算しない)
            self._elapsed_min += Decimal(dt_sec / 60)
            return
        # 一次遅れ応答: current += (target - current) * (1 - exp(-dt/tau))
        alpha = Decimal(1 - math.exp(-dt_sec / TIME_CONSTANT))
        delta = (self._target_flow - self._current_flow) * alpha
        self._current_flow = self._current_flow + delta
        # 積算量(現在流量 × dt、mL/h × 秒 → mL)
        increment = self._current_flow * Decimal(dt_sec) / Decimal(3600)
        self._accumulated_volume = self._accumulated_volume + increment
        self._elapsed_min += Decimal(dt_sec) / Decimal(60)

def force_stop_failsafe(self, reason: str) -> None:
    with self._lock:
        if not self._failsafe_active:
            self._failsafe_active = True
            self._failsafe_reason = reason
        self._target_flow = Decimal("0.0")
        self._current_flow = Decimal("0.0")
```

**SRS-P01 ±5% 精度の根拠:**

- 一次遅れ τ = 0.5 秒、ステップ応答で時定数 5τ = 2.5 秒で 99% 到達
- 制御周期 100 ms = 5 周期で τ 相当 → 1 周期目で約 18%、5 周期目で 63%、10 周期目で 86%
- 定常状態では target = current となり、誤差 0%。**過渡応答中は 5% を超え得る**。SRS-P01 は「定常時 ±5%」と解釈して試験で確認(SRS 注記の追加提案)
- Decimal を使い四捨五入誤差を抑制(float は使わず、`math.exp` のみ float→Decimal 変換)

#### 4.9.D 資源使用量・タイミング制約

- ステートフル、メモリ数 KB
- `set_flow_rate` / `advance_time`: ロック取得 + Decimal 演算 = 数十 μs
- `force_stop_failsafe`: 同上、即時(瞬時に流量 0)
- 呼出元: `set_flow_rate` は Control Loop(100 ms 周期)、`advance_time` も Control Loop(同周期)、`force_stop_failsafe` は HW Failsafe Timer(別スレッド)→ **`RLock` 必須**

#### 4.9.E 例外・異常系

| 異常条件 | 検出方法 | 処置 |
|---------|---------|------|
| `dt_sec <= 0` | 引数チェック | `ValueError` |
| set_flow_rate に範囲外値 | Validator で事前排除 | 本ユニットでは追加チェックせず(Validator の責務) |
| failsafe 中の set_flow_rate | `_failsafe_active` チェック | no-op + ログ |
| failsafe 中の reset | 同上 | no-op + ログ |
| 同一 thread から RLock 再入 | RLock により許可 | 正常動作 |

#### 4.9.F 検証方法(§5.4.4 準拠)

- **定常精度試験(SRS-P01):** target=500 mL/h で 10 秒経過後、current が ±5% (475〜525) 以内
- **過渡応答試験:** ステップ入力 0→500 mL/h、`advance_time(0.5)` 後に 63% 到達、`advance_time(2.5 計)` 後に 99% 到達
- **積算量試験:** 100 mL/h で 1 時間 → 100 mL ±5%
- **failsafe 試験:** `force_stop_failsafe` 後、`set_flow_rate(500)` を呼んでも current = 0
- **failsafe 解除試験:** `release_failsafe` 後、`set_flow_rate(500)` で過渡応答開始
- **境界試験:** target=0、target=1200 で安定、`accumulated_volume` の 9999.9 越えはオーバーフロー警告
- **並行性試験:** 別スレッドからの `force_stop_failsafe` と `set_flow_rate` の競合で failsafe が勝つこと

---

### 4.10 UNIT-002.2: Pump Observer

- **目的 / 責務:** Pump Simulator(UNIT-002.1)の内部状態を **不変スナップショット** として返す。読み取り専用、副作用なし。Control Loop(自動停止判定)と State Observer API(UNIT-005.2)から呼ばれる。
- **関連 SRS:** SRS-031, SRS-I-020
- **関連 RCM:** —
- **安全クラス:** C

#### 4.10.A 公開 API

| 関数・メソッド | 引数 | 戻り値 | 事前条件 | 事後条件 | エラー処理 |
|----------------|------|-------|---------|---------|-----------|
| `observe() -> PumpSnapshot` | — | frozen `PumpSnapshot` | なし | 副作用なし | 例外なし(常に取得可能) |

#### 4.10.B データ構造

| 名称 | 型 | 意味 |
|------|----|------|
| `_pump` | `PumpSimulator` | 注入(UNIT-002.1) |
| `PumpSnapshot` | frozen dataclass | `current_flow: Decimal`, `target_flow: Decimal`, `accumulated_volume: Decimal`, `elapsed_min: Decimal`, `failsafe_active: bool`, `observed_at: float`(monotonic) |

#### 4.10.C アルゴリズム

```python
def observe(self) -> PumpSnapshot:
    # PumpSimulator の内部 _lock を借りて atomic に全フィールド読み取り
    with self._pump._lock:
        snap = PumpSnapshot(
            current_flow=self._pump._current_flow,
            target_flow=self._pump._target_flow,
            accumulated_volume=self._pump._accumulated_volume,
            elapsed_min=self._pump._elapsed_min,
            failsafe_active=self._pump._failsafe_active,
            observed_at=time.monotonic(),
        )
    return snap
```

**読み取り atomic 性の判断:**

- Pump 側の `_lock`(RLock)を借りる方式を選択。Observer が独自ロックを持つと、Pump の更新と Observer の読み取りで二重ロック競合が発生
- フィールド毎に個別読み取りすると **テアリング**(current_flow と accumulated_volume が異なる時刻のもの)が発生し得る → 全フィールドを 1 ロック区間内で読む
- 戻り値は frozen dataclass のため、呼出側での意図せぬ書き換え不可

#### 4.10.D 資源使用量・タイミング制約

- ステートレス(`_pump` 参照のみ)
- `observe`: ロック取得 + 6 フィールド代入 = 数 μs
- 呼出頻度: Control Loop は 100 ms 周期、State Observer API は任意

#### 4.10.E 例外・異常系

| 異常条件 | 検出方法 | 処置 |
|---------|---------|------|
| `_pump._lock` 取得失敗 | RLock タイムアウト無し | 通常発生せず、デッドロック疑い時は呼出元責任 |
| `_pump` フィールド型変化(将来) | 型チェック | pydantic 経由でないため、Pump 側の変更時は Observer も追随更新する設計上の依存 |

#### 4.10.F 検証方法(§5.4.4 準拠)

- **基本試験:** Pump に target=500 設定 → observe で target_flow=500
- **atomic 性試験:** 別スレッドで Pump.advance_time を高頻度実行しつつ、observe で取得した snapshot のフィールド整合(`accumulated_volume / elapsed_min` が物理的に矛盾しない)
- **不変性試験:** `snap.current_flow = ...` で `FrozenInstanceError`
- **observed_at 単調性試験:** 連続 observe で `observed_at` が単調増加

---

### 4.11 UNIT-002.3: Event Injection Stub

- **目的 / 責務:** Inc.2 で実装される閉塞・気泡・薬液切れイベントの注入 I/F を Inc.1 段階で先出し(抽象 I/F のみ)。本版では受信したイベントを記録するだけの **no-op スタブ** とし、Inc.2 開始時に Pump Simulator への影響伝播を実装する。
- **関連 SRS:** SRS-032, SRS-I-040(Inc.2 想定)
- **関連 RCM:** —(Inc.2 で RCM-005/006/007 等が紐付く想定)
- **安全クラス:** C(本版スタブ、Inc.2 で正式機能化時に再評価)

#### 4.11.A 公開 API

| 関数・メソッド | 引数 | 戻り値 | 事前条件 | 事後条件 | エラー処理 |
|----------------|------|-------|---------|---------|-----------|
| `inject(event: VirtualHwEvent) -> None` | frozen event | — | なし | 内部リングバッファに記録(no-op、Pump への影響なし) | 例外なし |
| `recent_events(limit: int = 100) -> list[VirtualHwEvent]` | 上限 | list | — | 副作用なし(複製を返す) | 例外なし |

#### 4.11.B データ構造

| 名称 | 型 | 意味 |
|------|----|------|
| `VirtualHwEvent` | frozen dataclass + Enum kind | `kind: EventKind`(OCCLUSION / AIR_BUBBLE / RESERVOIR_EMPTY)、`severity: int`、`occurred_at: float`、`metadata: Mapping` |
| `_buffer` | `collections.deque[VirtualHwEvent]` | maxlen=1000(リングバッファ) |
| `_lock` | `threading.Lock` | バッファ保護 |

#### 4.11.C アルゴリズム

```python
def inject(self, event: VirtualHwEvent) -> None:
    with self._lock:
        self._buffer.append(event)
    # Inc.1 では Pump への影響伝播は行わない(no-op)
    # Inc.2 で次のような実装に拡張する:
    #   if event.kind == EventKind.OCCLUSION:
    #       self._pump.set_occlusion_pressure(event.severity)
    #   ...

def recent_events(self, limit=100) -> list[VirtualHwEvent]:
    with self._lock:
        return list(self._buffer)[-limit:]
```

#### 4.11.D 資源使用量・タイミング制約

- メモリ: deque(maxlen=1000)で上限管理、約 1000 × 100 bytes = 100 KB 上限
- `inject`: ロック + append = μs オーダー
- 呼出頻度: 試験ハーネスからのみ(運用時は呼ばれない)

#### 4.11.E 例外・異常系

| 異常条件 | 検出方法 | 処置 |
|---------|---------|------|
| 不正な event(未知 kind 等) | pydantic 型検証で事前排除 | 本ユニット到達前に弾かれる |
| バッファ満杯 | deque maxlen で自動削除 | 古いイベントから破棄、ログなし(性能優先) |

#### 4.11.F 検証方法(§5.4.4 準拠)

- **基本試験:** `inject(occlusion_event)` → `recent_events(1)` で同イベント取得
- **no-op 試験:** inject 後も Pump.observe の値が変化しないこと(Inc.1 では伝播なし)
- **リングバッファ試験:** 1001 件 inject → recent_events(1000) で最新 1000 件、最古は破棄
- **Inc.2 拡張点試験(将来):** Inc.2 で実装する際、本版の API シグネチャ互換であること

#### 4.11.G Inc.2 拡張(v0.5、CR-0009 / Step 20 E、骨格、no-op 解除方針確定)

**Inc.2 で UNIT-002.3 に追補する変更点(SAD v0.2 §4.3.2 + INC2-SCOPE-VIP-001 §6.2 連携):**

- **`VirtualHwEventKind` enum 拡張:** Inc.1 の 3 種(`OCCLUSION` / `AIR_BUBBLE` / `RESERVOIR_EMPTY`)に **`BATTERY_LOW` を追加して 4 種化**(SRS-I-040 確定、HZ-009 対応)。
- **no-op 解除 = Pump への伝播経路を実装:** Inc.1 では `inject()` がリングバッファに記録するのみで Pump.observe には影響しなかった(no-op スタブ)。Inc.2 では **inject されたイベントを Pump 状態に反映**(例:`OCCLUSION` 注入で Pump 内部の閉塞フラグをセット → センサー値経由で UNIT-006.1 Occlusion Detector が検知)。
- **検知群への単方向通知経路:** UNIT-002.3 → ARCH-006 検知群(IF-U-015 `read_sensor` 経由 = 検知群が pull で Pump センサー値を読みに行く設計、Inc.2 範囲計画書 §6.4 + SAD §5 IF-U-015 連携)。Push 通知ではなく Pull 設計を採用する根拠は SDD v0.6 候補で詳細化(SRS-P02 ジッタ要件と整合する周期駆動)。
- **新規依存:** UNIT-002.1 Pump Simulator(センサー入力提供、ARCH-002.1 拡張と連動)。

**SDD v0.6 候補で詳細化する項目:**

- `inject` が Pump 状態をどう変更するかの状態モデル(各 EventKind ごとの Pump 内部フラグセット規則)
- `BATTERY_LOW` の severity 値と SRS-043 閾値判定アルゴリズムとの対応
- IF-U-015 `read_sensor` のシグネチャと SensorKind 6 種(`OCCLUSION_PRIMARY` / `OCCLUSION_SECONDARY` / `AIR_BUBBLE_WARN` / `AIR_BUBBLE_CRITICAL` / `RESERVOIR` / `BATTERY`)の Pump 側実装
- Inc.1 互換性確保(本 v0.5 の inject API 既存シグネチャを破壊しない)

**主要 API(変更点候補):**

| 関数・メソッド | 引数 | 戻り値 | 概要(Inc.1 → Inc.2 差分) |
|--------------|------|-------|--------------------------|
| `inject(event: VirtualHwEvent) -> None` | `VirtualHwEvent`(`VirtualHwEventKind` enum 4 種に拡張) | `None`(Inc.1 と同) | Inc.1: リングバッファ記録のみ → Inc.2: 記録 + Pump 状態変更(BATTERY_LOW 含む) |
| `read_sensor(kind: SensorKind) -> SensorReading`(新規、IF-U-015) | センサー種別 enum | センサー値(冗長 2 系統独立性 = SRS-RCM-009 根拠) | Inc.2 で新設、検知群が pull で読み取り |

**依存:** UNIT-002.1 Pump Simulator(センサー入力源)、ARCH-006 検知群(IF-U-015 経由の pull 元)

**安全クラス:** C(非分離継続、SAD §9 SEP-000)

---

### 4.12 UNIT-003.1: Serializer

- **目的 / 責務:** `PersistedRecord`(Settings + RuntimeState + メタ情報)を JSON にシリアライズし、JSON から `RawPersistedRecord` を復元する。`Decimal` は **文字列表現** で永続化し精度を保つ。スキーマバージョンを必ず含める。
- **関連 SRS:** SRS-DATA-001, SRS-DATA-004
- **関連 RCM:** RCM-015 の前提(復元データの型保証)
- **安全クラス:** C

#### 4.12.A 公開 API

| 関数・メソッド | 引数 | 戻り値 | 事前条件 | 事後条件 | エラー処理 |
|----------------|------|-------|---------|---------|-----------|
| `to_json(record: PersistedRecord) -> bytes` | frozen record | `bytes`(UTF-8 JSON) | record は pydantic で型検証済 | 副作用なし、決定論的(同入力同出力) | 例外なし(型は事前担保) |
| `from_json(data: bytes) -> RawPersistedRecord` | 生バイト列 | frozen `RawPersistedRecord` | — | 副作用なし | 不正 JSON: `JSONDecodeError`(呼出側 Integrity Validator が処理) / スキーマ違反: pydantic `ValidationError` |
| `current_schema_version() -> int` | — | int(現行バージョン) | — | — | — |

#### 4.12.B データ構造

| 名称 | 型 | 意味 |
|------|----|------|
| `PersistedRecord` | pydantic frozen | `schema_version: int`, `settings: Settings`, `runtime_state: RuntimeState`, `payload_bytes: bytes`(自身を除く JSON), `checksum: str`, `saved_at: str`(ISO 8601 UTC) |
| `RawPersistedRecord` | pydantic frozen | from_json 直後の未検証構造 |
| `CURRENT_SCHEMA_VERSION` | int | 1(本版) |
| `SUPPORTED_SCHEMA_VERSIONS` | frozenset[int] | {1}(本版)、将来は {1, 2, ...} |

#### 4.12.C アルゴリズム

```python
CURRENT_SCHEMA_VERSION = 1

def to_json(record: PersistedRecord) -> bytes:
    # Decimal を文字列化する custom encoder
    def _default(obj):
        if isinstance(obj, Decimal):
            return {"__decimal__": str(obj)}
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Unsupported type: {type(obj)}")
    obj_dict = record.model_dump(mode="python")  # pydantic
    return json.dumps(obj_dict, default=_default,
                      sort_keys=True, ensure_ascii=False,
                      separators=(",", ":")).encode("utf-8")

def from_json(data: bytes) -> RawPersistedRecord:
    def _hook(obj):
        if "__decimal__" in obj:
            return Decimal(obj["__decimal__"])
        return obj
    raw = json.loads(data.decode("utf-8"), object_hook=_hook)
    return RawPersistedRecord.model_validate(raw)  # pydantic
```

**設計判断:**

- **Decimal 文字列化** + タグオブジェクト `{"__decimal__": "1.234"}` 方式 → JSON として valid、復元時に確実に Decimal に戻せる(naked string だと str/Decimal の判別不能)
- **`sort_keys=True`** → 同一データから常に同一バイト列(チェックサム検証の決定性)
- **`separators=(",", ":")`** → 空白を排除(チェックサム前後で空白差を生まない)
- **`ensure_ascii=False`** → 日本語エラーメッセージ等を直接保存可
- **スキーマバージョン**: `CURRENT_SCHEMA_VERSION` を必ず先頭に。Integrity Validator が `SUPPORTED_SCHEMA_VERSIONS` でチェック
- **マイグレーション戦略**: スキーマ変更時は `CURRENT_SCHEMA_VERSION` をインクリメント、`from_json` 後に `migrate_to_current(raw)` で逐次変換(本版では未実装、Inc.2 以降で必要時に追加)

#### 4.12.D 資源使用量・タイミング制約

- 純粋関数、ステートレス
- `to_json` / `from_json`: 数 KB データで ms 以下(json + pydantic)
- メモリ: 入力サイズ × 約 2(JSON 文字列 + 構造体)
- 呼出頻度: 永続化 1 秒以内(SRS 規定)+ 起動時 1 回

#### 4.12.E 例外・異常系

| 異常条件 | 検出方法 | 処置 |
|---------|---------|------|
| 不正 JSON | `JSONDecodeError` | 上位(Integrity Validator)で `ChecksumMismatch` 等とまとめて処理 |
| 未知 schema_version | pydantic + Integrity Validator | `SchemaVersionUnsupported` 失敗 |
| 不正 Decimal 文字列 | `decimal.InvalidOperation` | 上位で処理 |
| 未知 type の encode | `TypeError` | プログラムバグ(到達不可、テストで予防) |

#### 4.12.F 検証方法(§5.4.4 準拠)

- **ラウンドトリップ試験:** `from_json(to_json(r)) == r` がランダム record 1000 件で成立
- **決定論性試験:** 同じ record を 100 回 `to_json` して全バイト列が同一
- **Decimal 精度試験:** Decimal("0.1") + Decimal("0.2") を保存・復元しても `Decimal("0.3")` を維持
- **不正 JSON 試験:** truncated JSON / 不正 UTF-8 で `JSONDecodeError`
- **未知スキーマ試験:** `schema_version=999` を `from_json` → pydantic は通過するが、Integrity Validator で SchemaVersionUnsupported

---

### 4.13 UNIT-003.2: Checksum Verifier

- **目的 / 責務:** SHA-256 を用いて payload のチェックサムを生成・検証する。改ざんと偶発破損の両方を検出する。
- **関連 SRS:** SRS-SEC-001
- **関連 RCM:** RCM-015 の構成要素(Integrity Validator が呼ぶ)
- **安全クラス:** C

#### 4.13.A 公開 API

| 関数・メソッド | 引数 | 戻り値 | 事前条件 | 事後条件 | エラー処理 |
|----------------|------|-------|---------|---------|-----------|
| `compute(data: bytes) -> str` | 任意バイト列 | hex 64 文字 | なし | 副作用なし | 例外なし |
| `verify(data: bytes, expected: str) -> bool` | 同上 + 期待値 | bool | expected は 64 文字 hex | 副作用なし、**定数時間比較** | 形式不正 expected: `False`(例外を投げない) |

#### 4.13.B データ構造

なし(完全ステートレス、純粋関数)。

#### 4.13.C アルゴリズム

```python
import hashlib, hmac

def compute(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def verify(data: bytes, expected: str) -> bool:
    if len(expected) != 64 or not all(c in "0123456789abcdef" for c in expected.lower()):
        return False
    actual = compute(data)
    # 定数時間比較(タイミング攻撃耐性、医療機器でも将来の意図的改ざんへの備え)
    return hmac.compare_digest(actual, expected.lower())
```

**設計判断:**

- **SHA-256**: SRS-SEC-001 の規定。本版で十分(Inc.1 範囲は単独 PC ローカルファイル)
- **`hmac.compare_digest`**: 定数時間比較。秘匿鍵は使わないため HMAC ではなく純粋ハッシュだが、比較は HMAC 相当の安全性
- **HMAC への拡張余地:** Inc.4 以降で外部からのデータ取り込みが発生する場合、`hmac.new(secret, data, sha256)` への置換を検討(SDD v0.x で追加)

#### 4.13.D 資源使用量・タイミング制約

- 純粋関数、メモリは入力サイズ + ハッシュ状態(数百バイト)
- 数十 KB データで < 1 ms
- 呼出頻度: 永続化のたび 1 回 + 起動時 1 回

#### 4.13.E 例外・異常系

| 異常条件 | 検出方法 | 処置 |
|---------|---------|------|
| 不正形式の expected | 文字種・長さチェック | `False` を返却(例外なし) |
| `hashlib.sha256` の例外 | 原理的に発生せず | 万一発生時はライブラリバグ、フェイルセーフ(プロセス終了は呼出側責任) |

#### 4.13.F 検証方法(§5.4.4 準拠)

- **基本試験:** 既知ベクター(空文字列の SHA-256 = `e3b0c44...`)で一致
- **検証成功試験:** `verify(data, compute(data)) == True`
- **検証失敗試験:** 1 ビット改変したデータで `verify == False`
- **不正 expected 試験:** 長さ違い / 非 hex 文字で例外なし `False`
- **大文字 hex 試験:** `expected` が大文字 hex でも一致(`.lower()` で正規化)
- **タイミング試験(参考):** 一致と不一致で実行時間差が統計的有意でないこと(`hmac.compare_digest` の効果確認)

---

### 4.14 UNIT-004.2: Resume Confirmation Gate

- **目的 / 責務:** 起動時に永続記録から復元された PAUSED 状態(中断中の輸液)について、自動再開を禁止し、運用者の **明示的 confirm** を待つ(SRS-RCM-016、SRS-028)。トークン発行による「意図せぬ確認」防止。確認なく一定時間(60 分)経過時に警告ログ。
- **関連 SRS:** SRS-028, SRS-RCM-016
- **関連 RCM:** RCM-016(再開確認)
- **安全クラス:** C

#### 4.14.A 公開 API

| 関数・メソッド | 引数 | 戻り値 | 事前条件 | 事後条件 | エラー処理 |
|----------------|------|-------|---------|---------|-----------|
| `set_pending(detail: ResumeDetail) -> str` | 復元詳細(設定・直前状態) | token(secrets.token_hex(16)) | 既に pending でない | 内部に detail + token 保持、起票時刻記録 | 既に pending: `RuntimeError`(2 重設定不可) |
| `is_pending() -> bool` | — | bool | — | — | — |
| `pending_detail() -> Optional[ResumeDetail]` | — | detail or None | — | 副作用なし | — |
| `confirm(token: str) -> ConfirmResult` | token | `Confirmed(detail)` / `WrongToken` / `NotPending` / `Expired` | — | 成功時: pending 解除 + State Machine に CMD_RESUME 遷移要求 | 戻り値で表現 |
| `cancel() -> None` | — | — | — | pending 解除(CMD_STOP 相当) | 未 pending: no-op |

#### 4.14.B データ構造

| 名称 | 型 | 意味 | スレッド安全性 |
|------|----|------|--------------|
| `_pending` | `Optional[PendingResume]` | None / 1 件 | `_lock` 保護 |
| `PendingResume` | frozen dataclass | `token: str`(32 hex)、`detail: ResumeDetail`、`set_at: float`(monotonic)、`set_at_wall: datetime` | — |
| `_lock` | `threading.Lock` | — | — |
| `_state_machine` | StateMachine | — | 注入 |
| `EXPIRY_SEC` | int | 3600(60 分) | const |

#### 4.14.C アルゴリズム

```python
import secrets

EXPIRY_SEC = 3600  # 60 分(SRS-028 の運用要件として確定)

def set_pending(self, detail: ResumeDetail) -> str:
    with self._lock:
        if self._pending is not None:
            raise RuntimeError("ResumeGate already pending")
        token = secrets.token_hex(16)  # 32 hex chars, 128 bit entropy
        self._pending = PendingResume(
            token=token, detail=detail,
            set_at=time.monotonic(), set_at_wall=datetime.now(timezone.utc))
    self._logger.log_resume_pending(detail)
    return token

def confirm(self, token: str) -> ConfirmResult:
    with self._lock:
        pending = self._pending
        if pending is None:
            return NotPending()
        # 定数時間比較(token の漏洩を含むタイミング攻撃の理論的耐性)
        if not hmac.compare_digest(token, pending.token):
            return WrongToken()
        if (time.monotonic() - pending.set_at) > EXPIRY_SEC:
            self._pending = None
            self._logger.log_resume_expired(pending)
            return Expired()
        self._pending = None
    # ロック外で State Machine へ
    self._state_machine.request_transition(
        TransitionEvent(EventKind.CMD_RESUME, meta={"resume_token": token}))
    return Confirmed(pending.detail)

def check_expiry(self) -> None:
    """定期呼び出し(例: 1 分ごと)、期限切れ警告ログ"""
    with self._lock:
        if self._pending and (time.monotonic() - self._pending.set_at) > EXPIRY_SEC:
            self._logger.log_resume_expiry_warning(self._pending)
```

**設計判断:**

- **token 生成方式**: `secrets.token_hex(16)` = 128 ビットエントロピー。誤確認(別オペレータが推測で confirm する)を実用上不可能化
- **定数時間比較**: token 比較は `hmac.compare_digest`。意図しない情報漏洩を予防
- **EXPIRY_SEC = 60 分**: SRS-028 の「合理的時間内に確認」を「60 分超で警告 + 確認時には Expired 返却」と解釈。`cancel` で明示的に取り消す運用を併せて推奨
- **State Machine への遷移要求はロック外**: ロック内呼び出しはデッドロック誘発の可能性(逆方向呼び出しが将来発生した場合)

#### 4.14.D 資源使用量・タイミング制約

- メモリ: PendingResume 1 件分 = 数百 bytes
- `set_pending` / `confirm`: ロック + Decimal 演算 = μs
- 呼出頻度: 起動時 1 回 + ユーザ操作時 1 回 + check_expiry は分単位

#### 4.14.E 例外・異常系

| 異常条件 | 検出方法 | 処置 |
|---------|---------|------|
| 既に pending で set_pending | ガード | `RuntimeError`(プログラムバグ) |
| 期限切れ後の confirm | `time.monotonic() - set_at > EXPIRY_SEC` | `Expired` 返却 + pending 解除 |
| 不正 token | `compare_digest` False | `WrongToken` 返却 |
| 未 pending で confirm | ガード | `NotPending` |

#### 4.14.F 検証方法(§5.4.4 準拠)

- **正常フロー試験:** `set_pending` → `confirm(正token)` → `Confirmed`、State Machine が CMD_RESUME 受信
- **誤 token 試験:** `confirm("00...00")` → `WrongToken`、pending 維持
- **期限切れ試験:** `set_pending` 後 `time.monotonic` をモックで 3601 秒進める → `confirm` → `Expired`、pending 解除
- **2 重 pending 試験:** 連続 `set_pending` → 2 回目 `RuntimeError`
- **token エントロピー試験:** 1000 回 `set_pending`(間に confirm)で全 token がユニーク
- **cancel 試験:** `set_pending` → `cancel` → `is_pending == False`、`confirm(正token)` → `NotPending`

---

### 4.15 UNIT-005.1: Control API

- **目的 / 責務:** 外部呼出元(Inc.4 UI / 試験ハーネス)に対して、流量制御の意図(start/stop/pause/resume/reset/error_reset/confirm_resume)を公開する **薄い Facade**。pydantic スキーマで入力を検証し、Command Handler(UNIT-001.3)に委譲する。**例外を投げない**(全て返り値で表現)。
- **関連 SRS:** SRS-IF-002, SRS-010〜014
- **関連 RCM:** —(委譲先で実装)
- **安全クラス:** C

#### 4.15.A 公開 API

| 関数 | 引数 | 戻り値 | 事前条件 | 事後条件 | エラー処理 |
|------|------|-------|---------|---------|-----------|
| `start(settings: Settings) -> ApiResult` | pydantic Settings | `Ok(token)` / `ValidationFailed(errors)` / `Rejected(reason)` | settings は pydantic で型検証通過済 | Command Handler に enqueue | 例外を投げない |
| `stop() -> ApiResult` | — | 同上 | — | enqueue(STOP, ファストパス) | 同上 |
| `pause() -> ApiResult` | — | 同上 | — | enqueue(PAUSE) | 同上 |
| `resume() -> ApiResult` | — | 同上 | — | enqueue(RESUME) | 同上 |
| `reset() -> ApiResult` | — | 同上 | STOPPED 状態 | enqueue(RESET) | 同上 |
| `error_reset() -> ApiResult` | — | 同上 | ERROR 状態 | enqueue(ERROR_RESET、ファストパス) | 同上 |
| `confirm_resume(token: str) -> ApiResult` | resume token | `Ok(state)` / `WrongToken` / `Expired` / `NotPending` | — | Resume Gate.confirm 経由 | 同上 |
| `await_command(token: str, timeout_ms: int = 200) -> CompletionResult` | — | `Completed(state)` / `TimedOut` / `Failed(error)` | enqueue 済 token | — | 同上 |

#### 4.15.B データ構造

| 名称 | 型 | 意味 |
|------|----|------|
| `ApiResult` | sealed hierarchy | `Ok(token: str)` / `ValidationFailed(errors: list[ValidationError])` / `Rejected(reason: RejectReason)` |
| `Settings` | pydantic frozen | `flow_rate: Decimal` (0〜1200)、`dose_volume: Decimal` (0〜9999.9)、`duration_min: int` (1〜5999)、`drug_name: str` |
| `_command_handler` | CommandHandler | 注入(UNIT-001.3) |
| `_resume_gate` | ResumeConfirmationGate | 注入(UNIT-004.2) |
| `_validation_api` | ValidationApi(Protocol) | 注入。実体は `vip_api._validation_bridge.ClassBValidationApiAdapter`(または UT 用 Mock)。CR-0004 (b) の Adapter が `vip_api_b.validate_settings`(`Ok` / `Err`)を `list[ValidationError]` に変換し、SEP-001 越え経路を成立させる |

#### 4.15.C アルゴリズム

```python
def start(self, settings: Settings) -> ApiResult:
    # 1. 分離 B 経由のセマンティック検証(整合性、SRS-004 等)
    val = self._validation_api.validate_settings(settings)
    if val.is_err():
        return ValidationFailed(errors=val.err)
    # 2. Command Handler に enqueue
    cmd = Command(kind=CommandKind.START, payload=settings)
    accept = self._command_handler.enqueue(cmd)
    if isinstance(accept, Rejected):
        return Rejected(accept.reason)
    return Ok(token=accept.token)

def stop(self) -> ApiResult:
    cmd = Command(kind=CommandKind.STOP, payload=None)
    accept = self._command_handler.enqueue(cmd)  # Handler 内ファストパス
    return Ok(accept.token) if isinstance(accept, Accepted) else Rejected(accept.reason)

def confirm_resume(self, token: str) -> ApiResult:
    result = self._resume_gate.confirm(token)
    if isinstance(result, Confirmed):
        return Ok(token="<resume>")
    if isinstance(result, WrongToken):
        return WrongToken()
    if isinstance(result, Expired):
        return Expired()
    return NotPending()

def await_command(self, token, timeout_ms=200):
    return self._command_handler.await_completion(token, timeout_ms)
```

**設計判断:**

- **薄さの徹底**: 業務ロジックは Command Handler / Resume Gate / Validation API に委譲。本ユニットは合成のみ
- **例外を投げない契約**: API 利用者は `isinstance` で結果を分岐(MyPy で sealed hierarchy 網羅性検査)
- **start のみ Validation API を呼ぶ**: 他コマンドは settings を伴わないため
- **token 命名**: command_token と resume_token は別物だが API 利用者には区別不要(`Ok(token)` で抽象化)

#### 4.15.D 資源使用量・タイミング制約

- ステートレス(注入参照のみ)
- 各メソッド: 委譲分のみ(UNIT-001.3 SRS-P03/P04 を継承)
- 呼出頻度: ユーザ操作のたび

#### 4.15.E 例外・異常系

| 異常条件 | 検出方法 | 処置 |
|---------|---------|------|
| Settings 型違反 | pydantic 事前 | API 到達前に弾かれる |
| Validation API 失敗 | `val.is_err()` | `ValidationFailed(errors)` |
| Command Handler の Rejected | 戻り値判定 | `Rejected(reason)` を返却 |
| 委譲先の予期せぬ例外 | 全メソッド try/except | 戻り値 `Rejected(INTERNAL_ERROR)` + ログ |

#### 4.15.F 検証方法(§5.4.4 準拠)

- **start 正常フロー:** Validator Pass + Handler Accepted → `Ok(token)`
- **start 検証失敗:** Validator Err → `ValidationFailed`、Handler に enqueue されないこと
- **stop ファストパス:** stop 呼び出しから State Machine 受信までが SRS-P04 50 ms 以内(統合試験)
- **例外を投げない網羅試験:** 全メソッド × モックで例外注入 → 戻り値 Rejected で復帰、例外伝播なし
- **sealed hierarchy 網羅性:** mypy strict で `match` 文の全 case が網羅されているか静的検査

#### 4.15.G Inc.2 拡張(v0.5、CR-0009 / Step 20 E、骨格)

**Inc.2 で UNIT-005.1 に追補する変更点(SAD v0.2 §4.3.1 + INC2-SCOPE-VIP-001 §6.2 連携):**

- **`acknowledge_alarm` API 追加:** SRS-044(アラーム確認、IEC 60601-1-8 §6.4)に従い、外部呼出元(Inc.4 UI / 試験ハーネス)からのアラーム ACK 操作を受け、ARCH-007.1 Alarm Reporter Core(IF-U-014)へ転送。同時に UNIT-001.1 State Machine に ALARM_ACKED 遷移を依頼。
- **`silence_alarm` API 追加:** SRS-044(アラーム消音、IEC 60601-1-8 §6.4)に従い、消音操作を ARCH-007.1 へ転送。**高優先度アラームは ≤ 120 秒の消音時間制限を ARCH-007.1 側で強制**(本 UNIT は転送のみ)。
- **既存 API 不変:** start / stop / pause / resume / reset / confirm_resume は Inc.1 のシグネチャを維持(Inc.1 互換性)。
- **新規依存:** ARCH-007.1 Alarm Reporter Core(IF-U-014)+ UNIT-001.1 State Machine 拡張(`request_alarm_acknowledge` / `request_alarm_silence` 経路)。

**SDD v0.6 候補で詳細化する項目:**

- `acknowledge_alarm` / `silence_alarm` の戻り値型(`Ok(None)` / `Err(AlarmNotFound)` / `Err(SilenceTooLong)` 等)
- 高優先度消音時間制限のクライアント側ヒント(`silence_alarm` が `duration_sec > 120` のとき高優先度なら `Err`、ARCH-007.2 Priority Classifier 連携)
- 同時複数アラーム時の優先順位(IEC 60601-1-8 §6.1 + ARCH-007.2 で集約 = Control API は転送のみ)
- 例外契約(既存 Inc.1 メソッドと同様、戻り値 Rejected で復帰、例外伝播なし)

**主要 API(候補、後続改訂で詳細化):**

| 関数・メソッド | 引数 | 戻り値 | 概要 |
|--------------|------|-------|------|
| `acknowledge_alarm(alarm_id: str) -> Result[None, AlarmCommandError]` | アラーム ID | 成功: `Ok(None)` / 失敗: `Err(AlarmNotFound \| AlreadyAcked)` | IF-U-014、SRS-044 |
| `silence_alarm(alarm_id: str, duration_sec: int) -> Result[None, AlarmCommandError]` | アラーム ID + 消音時間(秒) | 同上 + `Err(SilenceTooLong)`(高優先度 ≤ 120 秒制限違反) | IF-U-014、SRS-044、IEC 60601-1-8 §6.4 |

**依存:** ARCH-007.1 Alarm Reporter Core(IF-U-014 転送先)、UNIT-001.1 State Machine(ACK/SILENCE 状態遷移依頼)

**安全クラス:** C(既存と同じ、SAD §9 SEP-000)

---

### 4.16 UNIT-005.2: State Observer API

- **目的 / 責務:** 外部呼出元に **読み取り専用** のスナップショットを提供する。State Machine + Pump Observer + Resume Gate の状態を集約した `StateSnapshot` を返す。idempotent。
- **関連 SRS:** SRS-IF-003, SRS-O-010, SRS-UX-002
- **関連 RCM:** —
- **安全クラス:** C

#### 4.16.A 公開 API

| 関数 | 引数 | 戻り値 | 事前条件 | 事後条件 | エラー処理 |
|------|------|-------|---------|---------|-----------|
| `observe_state() -> StateSnapshot` | — | frozen StateSnapshot | なし | 副作用なし、idempotent | 例外なし |

#### 4.16.B データ構造

| 名称 | 型 | 意味 |
|------|----|------|
| `StateSnapshot` | frozen pydantic | `machine_state: State`、`pump: PumpSnapshot`、`resume_pending: bool`、`resume_set_at: Optional[datetime]`、`error_reason: Optional[str]`、`observed_at: datetime` |
| `_state_machine` | StateMachine | 注入 |
| `_pump_observer` | PumpObserver | 注入 |
| `_resume_gate` | ResumeConfirmationGate | 注入 |

#### 4.16.C アルゴリズム

```python
def observe_state(self) -> StateSnapshot:
    # 各取得は独立した atomic 操作
    machine = self._state_machine.current()
    pump_snap = self._pump_observer.observe()
    resume_pending = self._resume_gate.is_pending()
    resume_detail = self._resume_gate.pending_detail()
    error_reason = self._state_machine.error_reason() if machine == State.ERROR else None
    return StateSnapshot(
        machine_state=machine, pump=pump_snap,
        resume_pending=resume_pending,
        resume_set_at=resume_detail.set_at_wall if resume_detail else None,
        error_reason=str(error_reason) if error_reason else None,
        observed_at=datetime.now(timezone.utc))
```

**設計判断:**

- **複数ロックを順次取得する非 atomic 集約**: Machine と Pump と Resume の状態は微小時間ズレが許容(UI 表示用)。**全ロックを 1 トランザクションにすると性能影響大** + State 遷移をブロック
- **観測時刻 `observed_at` を必ず付与**: 表示側で stale 判定可能
- **error_reason を文字列化**: 内部 enum を露出しない(API 安定性)

#### 4.16.D 資源使用量・タイミング制約

- ステートレス
- 数十 μs(各取得 + StateSnapshot 構築)
- 呼出頻度: UI / 試験ハーネスから任意(高頻度でも問題なし)

#### 4.16.E 例外・異常系

| 異常条件 | 検出方法 | 処置 |
|---------|---------|------|
| 注入オブジェクトの例外 | 通常発生せず | 万一発生時は呼出側で捕捉(本 API は例外伝播)— **ただし設計目標は例外なし**、観測対象が例外を投げる場合は呼出側責任 |

#### 4.16.F 検証方法(§5.4.4 準拠)

- **基本試験:** State Machine が IDLE のとき `observe_state().machine_state == IDLE`
- **idempotent 試験:** 連続 100 回呼出で状態に影響なし(Machine/Pump/Resume の各値が変化しないこと)
- **集約試験:** 各注入オブジェクトをモック化し、StateSnapshot の各フィールドが正しく集約されること
- **observed_at 単調性試験:** 連続観測で `observed_at` が単調増加

---

### 4.17 UNIT-005.3: Validation API(分離対象 — クラス B)

- **目的 / 責務:** Settings の **意味的整合性** を検証する純粋関数(SRS-004「flow_rate × duration_min/60 ≈ dose_volume」など)。SAD-VIP-001 §9 の **SEP-001(分離境界)** によりクラス B として分離。**例外を投げない**、副作用なし、決定論的。本ユニットの故障は流量制御本体に影響を与えない設計(分離保証)。
- **関連 SRS:** SRS-UX-001, SRS-004, SRS-005
- **関連 RCM:** —(クラス B 分離側)
- **安全クラス:** **B**(分離対象、SAD §9 SEP-001 準拠)

#### 4.17.A 公開 API

| 関数 | 引数 | 戻り値 | 事前条件 | 事後条件 | エラー処理 |
|------|------|-------|---------|---------|-----------|
| `validate_settings(settings: Settings) -> ValidationResult` | pydantic frozen | `Ok(settings)` / `Err(failures: list[ValidationFailure])` | 型検証は pydantic で済 | 副作用なし、純粋関数 | 例外を投げない |

#### 4.17.B データ構造

| 名称 | 型 | 意味 |
|------|----|------|
| `ValidationFailure` | sealed hierarchy | `OutOfRange(field, actual, range)` / `Inconsistency(detail)` / `MissingField(field)` |
| `TOLERANCE` | `Decimal` | 0.01(整合性誤差 1%) |

#### 4.17.C アルゴリズム

```python
TOLERANCE = Decimal("0.01")  # SRS-004 の許容差 1%

def validate_settings(settings: Settings) -> ValidationResult:
    failures: list[ValidationFailure] = []
    # 1. 範囲(pydantic でも検証されるが、二重)
    if not (Decimal("0.0") <= settings.flow_rate <= Decimal("1200.0")):
        failures.append(OutOfRange("flow_rate", settings.flow_rate, "0.0..1200.0"))
    if not (Decimal("0.0") <= settings.dose_volume <= Decimal("9999.9")):
        failures.append(OutOfRange("dose_volume", settings.dose_volume, "0.0..9999.9"))
    if not (1 <= settings.duration_min <= 5999):
        failures.append(OutOfRange("duration_min", settings.duration_min, "1..5999"))
    # 2. 整合性(SRS-004): flow * (duration/60) ≈ dose、許容差 1%
    if settings.flow_rate > Decimal("0.0") and settings.duration_min > 0:
        expected_dose = settings.flow_rate * Decimal(settings.duration_min) / Decimal("60.0")
        if expected_dose > Decimal("0.0"):
            diff_ratio = abs(expected_dose - settings.dose_volume) / expected_dose
            if diff_ratio > TOLERANCE:
                failures.append(Inconsistency(
                    detail=f"flow*duration/60={expected_dose}, dose={settings.dose_volume}, diff={diff_ratio:.4f}"))
    # 3. drug_name 非空
    if not settings.drug_name or len(settings.drug_name.strip()) == 0:
        failures.append(MissingField("drug_name"))
    return Ok(settings) if not failures else Err(failures)
```

**分離設計の遵守(SAD §9 SEP-001):**

- **戻り値による一方向**: 例外を投げない契約 → クラス B からクラス C への副作用伝播を遮断
- **frozen データのみ**: 入力 Settings は frozen、出力 failures も frozen → 共有可変状態なし
- **依存方向一方向**: Validation API は他のコア UNIT を一切呼ばない(注入も持たない)
- **静的解析保証**: `# isolation: B` コメント + ruff ルール(将来追加)で本ユニットからクラス C UNIT への import を禁止

#### 4.17.D 資源使用量・タイミング制約

- 純粋関数、ステートレス
- 数 μs(Decimal 演算 5〜10 回)
- 呼出頻度: Control API.start のたび 1 回

#### 4.17.E 例外・異常系

| 異常条件 | 検出方法 | 処置 |
|---------|---------|------|
| Settings 型違反 | pydantic 事前 | 本 API 到達前に弾かれる |
| Decimal 演算例外 | 通常発生せず | 万一発生時 → **クラス B 分離契約により例外を握りつぶし、`Err([Inconsistency("internal")])`** で復帰(クラス C 側は例外を見ない) |

#### 4.17.F 検証方法(§5.4.4 準拠)

- **正常試験:** 整合した Settings(500 mL/h × 60 min = 500 mL)で `Ok`
- **整合性違反試験:** 500 mL/h × 60 min = 500、ところが dose=800 → `Err(Inconsistency)`
- **境界試験:** 許容差 ±1.00% の 0.99/1.00/1.01% で判定境界を確認
- **多重失敗試験:** 範囲外 + 整合性違反 + drug_name 空欄を同時 → 全て failures に列挙
- **分離契約試験:** 内部例外注入(Decimal モック)で例外伝播せず `Err` で復帰
- **静的解析:** クラス C UNIT への import が無いこと(ruff/grep で機械的検証)

### 4.18 UNIT-005.4: CLI Entry Point(Step 19 H1 で新規追加、SDD v0.4)

> **本節は SDD v0.4(Step 19 H1)で新規追加。** ISS-H-001(SRS-OPS-002 必須要求にもかかわらず Inc.1 全 17 ユニットに CLI ユニットが存在しなかった計画文書間乖離)を解消するため、UNIT-005.4 CLI として §3.2 ユニット一覧に追加(全 17 → 18 ユニット)。MINOR 区分・CR 不要(SCMP §4.1 軽微、F1〜F7 で確立した「計画文書間整合化 → 同 PR 訂正」パターン継続。RCM 非関連 + 外部 API 変更なし、SAD §6 階層防御 / §9 SEP-001 設計不変)。

- **目的 / 責務:** SRS-OPS-002(必須)が要求する `vip-ctrl` コマンドラインエントリポイントを実装する。Inc.1 範囲では **対話的 start/stop コマンド経路は提供しない**(SDD §3 設計方針 + B17 申し送り = 対話 UI は Inc.4 で正式実装)。本 CLI は **3 経路を公開:**(i) `--version` でバージョン文字列を 1 行出力、(ii) `--diagnose` で永続レコードを `atomic_writer.read` + `from_json` + Integrity Validator(UNIT-004.1)で読込・検証 + JSON Lines snapshot を stdout 出力、(iii) デフォルトでは起動メッセージ(stderr)+ 初期 snapshot(stdout JSON Lines)を出力後 exit 0。引数解析エラーは argparse 標準動作(stderr + exit 2)に準じる。
- **関連 SRS:** SRS-OPS-002(必須、CLI 起動)、SRS-OPS-003(必須、初回起動デフォルト = IDLE / 流量 0 / 積算 0)、SRS-OPS-010(推奨、JSON Lines ログ)、SRS-OPS-011(推奨、`--diagnose` 出力)
- **関連 RCM:** —(運用要求のため RCM 直接対応なし、ただし SRS-OPS-003 の「IDLE / 流量 0 / 積算 0 デフォルト」は SRS-027 フェイルセーフ起動と整合)
- **関連 HZ:** HZ-007(永続記録破損時のフェイルセーフ起動経路を `--diagnose` で観測可能にする)
- **安全クラス:** **C**(Inc.1 範囲では UNIT-004.1 Integrity Validator + UNIT-003.* 永続化への単方向呼出のみ、状態変更経路を提供しない簡易ユニット)

#### 4.18.A 公開 API

| 関数 | 引数 | 戻り値 | 事前条件 | 事後条件 | エラー処理 |
|------|------|-------|---------|---------|-----------|
| `main(argv, stdout, stderr) -> int` | argv: `list[str] \| None`、stdout/stderr: `IO[str] \| None` | プロセス exit code(0 / 2)| なし(常時呼出可能)| stdout / stderr の DI に応じて出力先を切替、戻り値で exit code を返却 | argparse 例外は SystemExit に変換(標準動作)|
| `run_version(out) -> int` | out: `IO[str]` | 0 | なし | バージョン 1 行を `out` に書込 | なし(`importlib.metadata.version` の `PackageNotFoundError` は捕捉して `unknown` で fallback)|
| `run_diagnose(persist_path, out) -> int` | persist_path: `Path`, out: `IO[str]` | 0 | なし | 永続レコード状態の JSON Lines 1 行を `out` に書込 | 内部で `_diagnose` ヘルパが `OSError` / `UnicodeDecodeError` / `json.JSONDecodeError` / `pydantic.ValidationError` を捕捉、戻り値の `DiagnoseResult` で構造化伝播 |
| `run_default(persist_path, out, err) -> int` | persist_path: `Path`, out/err: `IO[str]` | 0 | なし | 起動メッセージ(`err`)+ 初期 snapshot JSON Lines(`out`)を書込 | 同上 |
| `build_parser() -> argparse.ArgumentParser` | なし | argparse パーサ | なし | CLI 引数定義済の parser を返す | なし |

#### 4.18.B データ構造

| 名称 | 型 | 意味 |
|------|----|------|
| `DiagnoseResult` | `@dataclass(frozen=True, slots=True)` | `_diagnose` ヘルパ戻り値:`persist_path: Path` / `record_present: bool` / `integrity_ok: bool` / `failures: list[IntegrityFailure]` |

#### 4.18.C アルゴリズム(`_diagnose` ヘルパ + 各 run_X 経路)

```python
# _diagnose: 永続レコード読込 + 整合性検証
def _diagnose(persist_path: Path) -> DiagnoseResult:
    if not persist_path.exists():
        return DiagnoseResult(persist_path, record_present=False, integrity_ok=True, failures=[])
    read_result = atomic_writer.read(persist_path)
    if not isinstance(read_result, atomic_writer.ReadOk):
        return DiagnoseResult(persist_path, record_present=False, integrity_ok=False, failures=[])
    try:
        raw = from_json(read_result.data)
    except (UnicodeDecodeError, JSONDecodeError, ValueError):
        return DiagnoseResult(persist_path, record_present=True, integrity_ok=False, failures=[])
    # SDD §4.5.A の sealed union(`ValidationResult = Ok | FailsafeRecommended`)を
    # `isinstance` で 2 分岐網羅(`match` の implicit fallthrough = branch coverage 不到達
    # を回避、bandit B101 は `assert isinstance` を使わないことで回避)。
    result = validate_integrity(raw)
    if isinstance(result, Ok):
        return DiagnoseResult(persist_path, record_present=True, integrity_ok=True, failures=[])
    # mypy は 2 分岐目で `FailsafeRecommended` に narrow 可能(sealed union)
    return DiagnoseResult(persist_path, record_present=True, integrity_ok=False, failures=list(result.reasons))
```

JSON Lines 出力(SRS-OPS-010 整合)は最低 5 キーを必須含有:`timestamp / level / component / event / details`。`level = "info"` は `integrity_ok=True`、`"warning"` は `integrity_ok=False`。

#### 4.18.D 並行性 / 状態

- **CLI は完全 stateless**(argparse + 関数呼出のみ、内部に永続状態を持たない)。
- `_diagnose` は `atomic_writer.read` + `from_json` + Integrity Validator を直列に呼び出すのみで、ロックや並行制御を必要としない。
- Inc.4 で対話モードを追加する際は、Control Loop / Command Handler / SwWatchdog / HwFailsafeTimer 等の既存スレッド lifecycle と統合する設計(本 v0.4 の Inc.1 範囲では未対応)。

#### 4.18.E エラー / 例外契約

- 引数エラー: argparse が `SystemExit(2)` を投げる(stderr に usage / error メッセージ)
- `run_version` の `PackageNotFoundError`: 捕捉して `"vip-ctrl unknown\n"` を出力 + return 0
- `_diagnose` の `OSError` / `UnicodeDecodeError` / `JSONDecodeError`: `DiagnoseResult` に integrity_ok=False で構造化、例外を呼出元へ伝播しない
- `pydantic.ValidationError`(from_json 内): `ValueError` 由来として `_diagnose` で捕捉(`ValueError` を except 句に含める)

#### 4.18.F 検証方法(§5.4.4 準拠)

- **`--version` 経路:** バージョン 1 行出力 + return 0(UT-005.4-01)
- **`--version` fallback 経路:** `PackageNotFoundError` 発生時 `unknown` 出力(UT-005.4-02)
- **`--diagnose` 全経路:** レコード不存在(UT-005.4-03)、整合レコード(UT-005.4-04)、checksum 不一致(UT-005.4-05)、JSON 不正(UT-005.4-06)、UTF-8 デコード失敗(UT-005.4-07)、`atomic_writer.read` ReadErr(UT-005.4-08)
- **デフォルト経路:** レコード不存在 + 整合レコード(UT-005.4-09 / 10)
- **argparse エラー:** 相互排他違反(UT-005.4-11)、未知の引数(UT-005.4-12)
- **構造契約:** `build_parser` 単独動作(UT-005.4-13)、SRS-OPS-010 必須 5 キー全行網羅(UT-005.4-14)、`_diagnose` ヘルパ契約(UT-005.4-15)
- **MC/DC 100% 目標:** 78 stmt / 10 branch、UT 15 ケースで全分岐網羅(Step 19 H1 で達成、UTPR §7.3.18)
- **CLI レベル試験(ST):** Step 19 H2 の `tests/system/test_ops_acceptance.py`(STPR §6.2 ST-OPS.1-01〜04 で `subprocess.Popen` 経由 CLI 検証予定)

---

### 4.19 UNIT-006.1: Occlusion Detector(Inc.2 新規、v0.6 詳細化、CR-0016 / Step 20 X2)

> **Step 20 X2 整合化(2026-05-13、本節 v0.6 詳細化):** Step 20 X1(CR-0015、PR #67 マージ `551f862`)で TDD 実装した `src/vip_detection/occlusion.py` v0.1 + `src/vip_detection/protocols.py` v0.1 の内容を本節に反映。v0.5 骨格 7 項目のうち実装で確定した 5 項目(閾値・API・依存 protocol・DetectionResult・冪等性 + SEP-003 例外契約)を詳細化、未確定 4 項目(周期 tick 呼出間隔、並行性 / 排他制御、片系故障検出ロジック詳細 = タイムアウト・ノイズ閾値・連続エラーカウント、検知後の self-test 動作)は §4.19.G(SDD v0.7 候補)へ申し送り。

#### 4.19.A 目的 / 責務

静脈ラインの閉塞を **冗長 2 系統(独立センサー入力)** に基づく閾値判定で検知する(SRS-040、RCM-009)。両系健全時はいずれか 1 系統が閾値を超えた時点で閉塞と判定し(OR 論理)、片系故障時(センサー断線・ノイズ等)も他系で検知を継続することでフェイルセーフを確保する。検知時は SRS-ALM-004 を ARCH-007.1 Alarm Reporter Core 経由で発報し、UNIT-001.1 State Machine に ERROR 遷移を依頼する。両系故障時(検知不能)は **alarm を発報せず**(根拠なき発報の回避)、ERROR 遷移依頼のみ発行することで安全側遷移を実現する。

- **関連 SRS:** SRS-040, SRS-RCM-009, SRS-ALM-004, SRS-IF-010
- **関連 RCM:** RCM-009(閉塞検知冗長化、Designed → Verified 化目標、Inc.2 完了時)
- **関連 HZ:** HZ-004(EV-HZ004-001 駆動経路の検出側実装)
- **安全クラス:** C(SAD §9 SEP-000、非分離)
- **パッケージ:** `src/vip_detection/occlusion.py`(Step 20 X1、84 stmt + 18 branch、stmt/branch 100%、MC/DC 100% 目標達成)+ 共通 `src/vip_detection/protocols.py`(Step 20 X1、47 stmt、stmt/branch 100%)

#### 4.19.B 定数

```python
# src/vip_detection/occlusion.py
OCCLUSION_PRESSURE_THRESHOLD_KPA: Final[Decimal] = Decimal(90)
# 暫定値(臨床的に代表的な下流閉塞アラーム閾値)、SDD v0.7 で bench data に基づき正式確定予定。
# 単位は SAD v0.2 §5 IF-U-015 規約に従い kPa。
```

| 定数 | 値 | 用途 | 確定状態 |
|------|---|------|---------|
| `OCCLUSION_PRESSURE_THRESHOLD_KPA` | `Decimal(90)` | センサー値が `>=` この値で閾値超過と判定 | **暫定**(SDD v0.7 で確定) |

#### 4.19.C 依存 protocol(`vip_detection/protocols.py`)

検知群共通の I/F 抽象化(UNIT-006.2〜006.6 で再利用予定)を `vip_detection/protocols.py` に集中配置する。各 Protocol は `@runtime_checkable` でテスト時の isinstance チェック可能。

```python
class SensorKind(Enum):
    OCCLUSION_PRIMARY = "occlusion_primary"
    OCCLUSION_SECONDARY = "occlusion_secondary"
    AIR_BUBBLE_WARN = "air_bubble_warn"
    AIR_BUBBLE_CRITICAL = "air_bubble_critical"
    RESERVOIR = "reservoir"
    BATTERY = "battery"

@dataclass(frozen=True, slots=True)
class SensorReading:
    kind: SensorKind
    value: Decimal
    healthy: bool = True   # 上流(UNIT-002.3 拡張)で検出した per-channel fault フラグ

@runtime_checkable
class SensorReader(Protocol):
    def read_sensor(self, kind: SensorKind) -> SensorReading: ...
    # 例外を投げ得る。Detector は SEP-003 のため例外を吸収する(§4.19.G.2 参照)。

@runtime_checkable
class AlarmReporter(Protocol):
    def report_alarm(self, event: AlarmEvent) -> None: ...
    # 例外伝播禁止契約(SEP-003)。実装が例外を投げた場合 Detector は吸収して状態遷移を続行。

class TargetState(Enum):
    ERROR = "error"
    PAUSED = "paused"

@runtime_checkable
class StateTransitionRequester(Protocol):
    def request_state_transition(self, target: TargetState, *, reason: str) -> None: ...
    # idempotent であることを実装側に要求。
```

- **`SensorReading.healthy` の役割:** 「使えるか / 使えないか」の boolean のみを Detector に提示する。**具体的な per-channel 故障検出ロジック**(タイムアウト・ノイズ閾値・連続エラーカウント等)は UNIT-002.3 EventInjection 拡張(SDD §4.11.G、Step 20 X+ で詳細化)で実装し、Detector からは抽象化する。これにより Detector の純粋関数性(`_evaluate`)が保たれる。

#### 4.19.D `DetectionResult` 型(sealed 4 種、frozen+slots)

```python
@dataclass(frozen=True, slots=True)
class Healthy: ...                       # 両系健全 & 両系下回り

@dataclass(frozen=True, slots=True)
class Detected:
    triggering_channels: frozenset[SensorKind]   # 閾値超過した channel(1 または 2 個)

@dataclass(frozen=True, slots=True)
class Degraded:
    failed_channel: SensorKind            # 故障 channel(他系は健全 & 下回り)

@dataclass(frozen=True, slots=True)
class Failed: ...                         # 両系故障(検知不能、safe-side ERROR 遷移)

DetectionResult = Healthy | Detected | Degraded | Failed
```

**SDD v0.5 骨格(3 種:Healthy / Detected / Degraded)からの拡張:** 両系故障を `Failed` 独立型として明示。骨格時点では Detected/Degraded の reason フィールドで表現する案だったが、Step 20 X1 着手前の設計判断で「両系故障は alarm なしの ERROR 遷移依頼のみ = Detected と異なる副作用なので独立型のほうが UT-006.1-10/11 観点を明示的に表現できる」と判断(B11/B12/B13 frozen+slots パターン継続)。

#### 4.19.E `OcclusionDetector` クラス(DI 駆動、armed 連動冪等性)

```python
class OcclusionDetector:
    def __init__(
        self,
        *,
        sensor_reader: SensorReader,
        alarm_reporter: AlarmReporter,
        state_machine: StateTransitionRequester,
        clock: Callable[[], float] = time.monotonic,
        threshold_kpa: Decimal = OCCLUSION_PRESSURE_THRESHOLD_KPA,
    ) -> None:
        self._sensor_reader = sensor_reader
        self._alarm_reporter = alarm_reporter
        self._state_machine = state_machine
        self._clock = clock
        self._threshold = threshold_kpa
        self._alarm_armed = True   # idempotency guard(§4.19.F.4)
```

**設計判断:**

- **DI 駆動 constructor**(全依存をキーワード引数で注入):UT で 7 種 fake(`_ScriptedSensorReader` / `_RecordingReporter` / `_RaisingReporter` / `_RecordingStateMachine` / `_TracingReporter` / `_TracingStateMachine` / `_StepReader`)を切り替え可能にし、Pump や State Machine 等の本物を起動せずに純粋判定 + 順序契約をテストできる。Step 19 B 系列で確立した DI 駆動 + frozen+slots パターンを継承(B11 PumpSimulator / B12 PumpObserver / B13 CommandHandler / B14 EventInjectionStub)。
- **`clock` 引数:** `AlarmEvent.occurred_at` のソース。テスト時は `lambda: 42.5` のような固定 clock を注入することで時刻に依存しない試験を実現(UT-006.1-13)。
- **`threshold_kpa` 引数:** デフォルトは `OCCLUSION_PRESSURE_THRESHOLD_KPA` 定数だが、UT では `_THRESHOLD = OCCLUSION_PRESSURE_THRESHOLD_KPA` を fixture 化して `_BELOW = _THRESHOLD - 10` / `_ABOVE = _THRESHOLD + 10` で境界値を生成。SDD v0.7 で本番閾値が変わっても UT は無影響。

#### 4.19.F 主要 API + 動作仕様

| 関数 | 引数 | 戻り値 | 概要 |
|------|------|-------|------|
| `tick()` | — | `None` | 周期駆動エントリ。`_safe_read` × 2 → `_evaluate` → `_apply` の順で 1 cycle 実行 |
| `_evaluate(primary, secondary)` | 2 件の `SensorReading` | `DetectionResult` | 純粋判定ロジック(§4.19.F.1) |
| `_safe_read(kind)` | `SensorKind` | `SensorReading` | SensorReader 例外を `healthy=False` の `SensorReading` に変換(§4.19.F.2) |
| `_apply(result)` | `DetectionResult` | `None` | 結果型に応じた副作用ディスパッチ(§4.19.F.3) |
| `_on_detected()` | — | `None` | armed=True なら発報 → 遷移依頼の順、armed=False は no-op(§4.19.F.4) |
| `_on_failed()` | — | `None` | ERROR 遷移依頼のみ(alarm なし)+ armed 再 arm(§4.19.F.5) |

##### 4.19.F.1 `_evaluate`(純粋関数、UT-006.1-01〜11)

```python
def _evaluate(self, primary: SensorReading, secondary: SensorReading) -> DetectionResult:
    primary_ok = primary.healthy
    secondary_ok = secondary.healthy
    if not primary_ok and not secondary_ok:
        return Failed()
    triggering: set[SensorKind] = set()
    if primary_ok and primary.value >= self._threshold:
        triggering.add(SensorKind.OCCLUSION_PRIMARY)
    if secondary_ok and secondary.value >= self._threshold:
        triggering.add(SensorKind.OCCLUSION_SECONDARY)
    if triggering:
        return Detected(triggering_channels=frozenset(triggering))
    if not primary_ok:
        return Degraded(failed_channel=SensorKind.OCCLUSION_PRIMARY)
    if not secondary_ok:
        return Degraded(failed_channel=SensorKind.OCCLUSION_SECONDARY)
    return Healthy()
```

**契約:**

- **副作用なし**(`self._threshold` 参照のみ、`_alarm_armed` には触れない)= UT で `_evaluate` を直接呼び出して判定結果を assertion 可能。
- **OR 論理:** 健全な channel のうち **いずれか 1 つでも** `value >= threshold` なら `Detected`(RCM-009 = 冗長 2 系統で片方の検知を他方が妨げない)。
- **境界 inclusive:** `value == threshold` ちょうども超過と判定(`>=` で境界包含)。
- **故障チャネルは無視:** `healthy=False` の channel の `value` は読まない(計測値が信頼できないため)。両系健全な側で判定するか、両系故障なら `Failed`。

##### 4.19.F.2 `_safe_read`(SEP-003 例外吸収、UT-006.1-17/18)

```python
def _safe_read(self, kind: SensorKind) -> SensorReading:
    try:
        return self._sensor_reader.read_sensor(kind)
    except Exception:
        _logger.warning("sensor read failed: kind=%s", kind.value, exc_info=True)
        return SensorReading(kind=kind, value=Decimal(0), healthy=False)
```

**契約:**

- **SEP-003 = 検知群がアラーム発報の resilience に寄与:** SensorReader の致命的故障(`RuntimeError` 等)で Detector の周期 `tick` が止まると、後続の検知も停止する = SEP-003 違反。よって例外を吸収し、`healthy=False` の `SensorReading` に変換することで `_evaluate` 側で適切に Degraded / Failed に倒す。
- **catch-all(`except Exception`):** `ruff: noqa: BLE001` を付与。SensorReader が投げる可能性のあるすべての例外を想定する(`RuntimeError` / `IOError` / 上流 stub 例外)。`SystemExit` / `KeyboardInterrupt` は `BaseException` 派生で catch されないため、致命的なシグナル系は通常通り伝播する。
- **`value=Decimal(0)` プレースホルダ:** `_evaluate` は `healthy=False` の `value` を読まないため意味を持たないが、`SensorReading` dataclass の型制約を満たすために `Decimal(0)` を入れる。

##### 4.19.F.3 `_apply`(ディスパッチ、UT-006.1-15/16)

```python
def _apply(self, result: DetectionResult) -> None:
    if isinstance(result, Detected):
        self._on_detected()
        return
    if isinstance(result, Failed):
        self._on_failed()
        return
    # Healthy or Degraded: re-arm the alarm so the next Detected fires anew.
    self._alarm_armed = True
```

**契約:**

- **`Healthy` / `Degraded` で再 arm:** 連続検知中(armed=False)に Detected が解除されて Healthy / Degraded に戻ったとき、armed フラグを True に戻すことで、後続で再度閉塞が起きた場合に新規 alarm として発報できる(UT-006.1-16 のキーシナリオ)。
- **`Detected` / `Failed` は専用ハンドラへ:** 副作用を 1 箇所に集約することで順序契約(発報 → 遷移依頼)とテスト容易性(`_TracingReporter` / `_TracingStateMachine` で共有 `order` list に append)を両立。

##### 4.19.F.4 `_on_detected`(armed 連動冪等性、UT-006.1-12〜15)

```python
def _on_detected(self) -> None:
    if not self._alarm_armed:
        return                          # idempotent: 連続検知では 1 回のみ
    event = AlarmEvent(
        alarm_id=_ALARM_ID_OCCLUSION,         # "ALM-OCC"
        priority=AlarmPriority.HIGH,           # IEC 60601-1-8 §6.1
        category=AlarmCategory.TECHNICAL,      # IEC 60601-1-8 §5.1.4
        occurred_at=self._clock(),
        cause_code=_CAUSE_CODE_OCCLUSION,      # "occlusion"
    )
    try:
        self._alarm_reporter.report_alarm(event)
    except Exception:                          # SEP-003 例外吸収
        _logger.warning(
            "alarm reporter raised; continuing to state-transition request",
            exc_info=True,
        )
    self._alarm_armed = False
    self._state_machine.request_state_transition(
        TargetState.ERROR,
        reason=_REASON_DETECTED,                # "occlusion_detected"
    )
```

**契約:**

- **発報 → 遷移依頼の順序:** 順序を守る理由 = State Machine 側で ERROR 遷移と同時に制御ループが停止する可能性があるため、alarm 経路が遷移開始前にイベントを受領していることを保証する(SAD v0.2 §11 + SDD §4.19 設計判断)。テストは `_TracingReporter.report_alarm` と `_TracingStateMachine.request_state_transition` で共有 `order: list[str]` に append し、`["alarm", "transition"]` を assert(UT-006.1-12)。
- **冪等性(連続検知 → 1 回):** armed=True のときだけ発報 + 遷移依頼、armed=False のときは早期 return = 連続周期で `Detected` が続いても発報・遷移依頼ともに 1 回(UT-006.1-15)。State Machine 側の冪等性に依存しない設計。
- **Reporter 例外吸収:** `_alarm_reporter.report_alarm` が例外を投げても **遷移依頼は実行する**(SEP-003、UT-006.1-14)。armed フラグも False に倒す = 「発報試行はした、結果は失敗だが状態遷移は不可逆に進める」というポリシー。
- **`AlarmEvent` 構築:** `alarm_id` / `priority` / `category` / `cause_code` は class 定数として固定(IEC 60601-1-8 §6.1 / §5.1.4 から HIGH / TECHNICAL に決定、SRS-ALM-004 整合)。`occurred_at` のみ `clock()` でテスト時に固定可能。`metadata` は default factory `_empty_metadata()` で `MappingProxyType({})` を返す(SDD §5.1.A 契約)。

##### 4.19.F.5 `_on_failed`(両系故障時の安全側遷移、UT-006.1-11/17)

```python
def _on_failed(self) -> None:
    self._state_machine.request_state_transition(
        TargetState.ERROR,
        reason=_REASON_UNAVAILABLE,             # "occlusion_detection_unavailable"
    )
    self._alarm_armed = True                    # 後続の sensor 復旧 + Detected で発報可能
```

**契約:**

- **alarm なし:** 両系故障時は計測値が信頼できないため、根拠なき発報を避けて ERROR 遷移依頼のみ。後続 IT-RCM006 / IT-ALM(ITPR v0.13 候補)で「両系故障 → ERROR 遷移は届く + 上位アラーム(UNIT-006.4 Alarm Task Watchdog 経由)で監視」を結合検証予定。
- **`reason` 区別:** Detected 時は `"occlusion_detected"`、Failed 時は `"occlusion_detection_unavailable"` で State Machine 側のログ上区別可能(運用時の故障原因切り分けに寄与)。
- **再 arm:** Failed → Sensor 復旧 → Healthy / Detected の sequence で alarm が遮断されないよう、armed フラグを True に戻す。

#### 4.19.G 依存

| 依存先 | 経路 | 用途 |
|--------|------|------|
| UNIT-002.1 Pump Simulator | IF-U-015 `read_sensor(SensorKind)` 経由(`SensorReader` Protocol) | センサー値の pull(冗長 2 系統独立) |
| UNIT-002.3 EventInjection 拡張(SDD §4.11.G、Step 20 X+) | 上記の `healthy=False` フラグ供給 | per-channel fault 検出(タイムアウト / ノイズ / 連続エラー) |
| UNIT-007.1 Alarm Reporter Core(SDD §4.25、Step 20 X+) | IF-U-007 + IF-U-012 `report_alarm(AlarmEvent)` 経由(`AlarmReporter` Protocol) | アラーム発報 |
| UNIT-001.1 State Machine 拡張(SDD §4.1.G、Step 20 X+) | IF-U-013 `request_state_transition(target, *, reason)` 経由(`StateTransitionRequester` Protocol) | ERROR 遷移依頼 |

**Step 20 X1 時点では依存先(UNIT-002.1 sensor 接続 / UNIT-007.1 / UNIT-001.1 拡張)は実装未完。** UT は protocol 抽象に依存する fake で代替し、結合は後続 IT(ITPR §6.12 RCM-009、Step 20 Y 系列)で実証する。

#### 4.19.G.x SDD v0.7 候補で詳細化する項目(本 v0.6 スコープ外)

本 v0.6 では Step 20 X1 で実装した範囲のみを詳細化した。以下は Inc.2 完了タグ前に確定が必要な項目で、SDD v0.7 候補(Step 20 X+ で連動 detector 実装と並行)で詳細化する。

1. **周期 tick 呼出間隔:** 制御ループ周期と整合(100 ms 候補)。Inc.2 中盤の Control Loop 拡張(UNIT-001.2 への detector tick 駆動経路追加)時に確定。
2. **並行性 / 排他制御:** 別スレッドからの `tick` 呼出耐性(UT-006.1-19+ 観点)。現実装は内部状態が `_alarm_armed: bool` のみで GIL の atomic 性に依存しているが、将来 `_history` 等の状態を追加する際は明示的な lock 化が必要。
3. **片系故障検出ロジック詳細:** タイムアウト・ノイズ閾値・連続エラーカウントの具体パラメータ。本 v0.6 では `SensorReading.healthy` boolean に抽象化済で UNIT-002.3 拡張(SDD §4.11.G、Step 20 X+)で実装側を詳細化。
4. **検知後の self-test 動作:** 誤検知抑制(N 周期連続 Detected で発報、N=1 が現状)vs 安全側即時発報(N=1)のトレードオフ評価。本 v0.6 では即時発報(N=1)を採用、bench データに基づき SDD v0.7 で再評価。
5. **閾値具体値:** `OCCLUSION_PRESSURE_THRESHOLD_KPA = Decimal(90)` の bench データ整合性確認、必要なら正式値に置換。

#### 4.19.H ユニット試験設計(UTPR §7.3.19 詳細化は CR-0017 / Step 20 X3 で実施)

Step 20 X1 で実装した UT 19 ケース(`tests/unit/test_occlusion_detector.py`、UT-006.1-01〜18、stmt/branch 100% = MC/DC 100% 目標達成)を UTPR §7.3.19 で詳細化する(別 PR 化、CR-0017 / Step 20 X3)。本 SDD v0.6 §4.19 では UT-006.1-NN 各ケースの設計意図は §4.19.F.x の各 API の **契約** 節で記述済(参照ガイド):

- §4.19.F.1 `_evaluate` 契約 ← UT-006.1-01〜11
- §4.19.F.2 `_safe_read` 契約 ← UT-006.1-17/18
- §4.19.F.3 `_apply` 契約 ← UT-006.1-15/16
- §4.19.F.4 `_on_detected` 契約 ← UT-006.1-12〜15
- §4.19.F.5 `_on_failed` 契約 ← UT-006.1-10/11/17

---

### 4.20 UNIT-006.2: Air-Bubble Detector(Inc.2 新規、v0.7 詳細化、CR-0019 / Step 20 X5)

#### 4.20.A 目的 / 責務

静脈ラインへの気泡混入を **多段判定**(警告閾値 + 危険閾値、各段独立)で検知する(SRS-041、RCM-010)。物理的に独立な 2 つのセンサーチャネル(`AIR_BUBBLE_WARN` / `AIR_BUBBLE_CRITICAL`)を周期的に読み取り、以下のいずれかの行動をとる:

- **危険閾値超過(critical >= threshold):** `SRS-ALM-005`(HIGH / TECHNICAL)を発報 + State Machine に ERROR 遷移を依頼。**段間優先(critical > warning)** = 危険閾値が超過していれば、警告閾値の状態を問わず Detected として扱う(`AlarmEvent.metadata` 内の `triggering_value` には危険センサーの読み値を載せる)。
- **警告閾値超過(warn >= threshold)かつ危険未達:** `WarningLogger` を経由した監視ログのみ(発報なし、状態遷移なし、Inc.4 で UI 通知化検討)。
- **両系故障時:** ERROR 遷移依頼のみ(`Failed` 独立型、alarm なし、safe-side)= 不確実な検出に基づく fabricated alarm を避ける(UNIT-006.1 §4.19 と同原則)。
- **片系故障時:** `Degraded(failed_channel)` で監視継続(警告系の喪失 = warning が出せないが critical 判定は維持、危険系の喪失 = warning は出せるが critical 判定不能のため Degraded で alarm / transition なし、SDD v0.8 で safe-side 議論)。

**段独立性(SDD §4.20 設計趣旨):** 警告センサーと危険センサーは物理的に独立 = ノイズの多い警告センサー読み値が危険判定をマスク / 偽造しない(UT-006.2-07 で機械検証)。

**関連 SRS:** SRS-041(気泡検知)、SRS-RCM-010(多段判定)、SRS-ALM-005(HIGH/TECHNICAL)、SRS-IF-010(Alarm I/F)
**関連 RCM:** RCM-010(気泡検知多段化、Designed → Verified 化目標、Inc.2 完了時)
**関連 HZ:** HZ-004(検知失敗 → アラーム失敗連鎖、EV-HZ004-002 駆動)
**安全クラス:** C(SAD §9 SEP-000、非分離)
**実装パッケージ:** `src/vip_detection/air_bubble.py` v0.1(Step 20 X4 PR #73 マージ `943230a` で TDD 実装、104 stmt + 20 branch、stmt/branch 100% = MC/DC 100% 目標達成)+ 共通 `src/vip_detection/protocols.py` v0.2(WarningLogger Protocol 追加)

**依存:** UNIT-002.1 Pump + UNIT-002.3 Event Injection 拡張(`AIR_BUBBLE_WARN` / `AIR_BUBBLE_CRITICAL` 2 種センサー)、UNIT-007.1 Alarm Reporter(SEP-003)、UNIT-001.1 State Machine、Inc.4 UI 通知コンポーネント(WarningLogger Protocol 経由、現 Inc. は記録 Fake で運用)

#### 4.20.B 定数

| 定数名 | 型 | 値(暫定) | 用途 |
|-------|----|----------|------|
| `AIR_BUBBLE_WARN_THRESHOLD` | `Final[Decimal]` | `Decimal(50)` | 警告閾値。`warn.value >= threshold` で `Warning` 候補(SDD v0.8 で bench data に基づき正式確定予定) |
| `AIR_BUBBLE_CRITICAL_THRESHOLD` | `Final[Decimal]` | `Decimal(150)` | 危険閾値。`critical.value >= threshold` で `Detected`(同上、`CRITICAL > WARN` の順序が構造的に保証) |

**単位:** 気泡体積センサー出力の **暫定無次元スケール**。SDD v0.8 で bench data の transfer function 確定後に再投影(mm^3 of entrained air または pump 正規化スケール)。docstring に「Placeholder scale pending SDD v0.8」と明記。

#### 4.20.C 依存 protocol(`vip_detection/protocols.py` v0.2)

UNIT-006.1 で確立した検知群共通 protocols を継承 + 本 X4 で **WarningLogger Protocol を新規追加**:

| Protocol | 役割 | SEP-003 契約 |
|----------|------|------------|
| `SensorReader` | IF-U-015 pull(`AIR_BUBBLE_WARN` / `AIR_BUBBLE_CRITICAL` 2 channel) | 例外は detector 側で吸収(`_safe_read`) |
| `AlarmReporter` | IF-U-007 push(`AlarmEvent`) | 例外伝播禁止(`_on_detected` で吸収) |
| `WarningLogger`(本 X4 新規) | sub-alarm 記録(警告閾値超過時) | 例外伝播禁止(`_on_warning` で吸収) |
| `StateTransitionRequester` | IF-U-013 push(ERROR target) | idempotent、例外伝播禁止 |

`WarningLogger.log_warning(detector_id: str, *, threshold_value: Decimal, observed_value: Decimal, occurred_at: float) -> None` シグネチャ:

- `detector_id`:`"UNIT-006.2"` 定数。複数ユニットが同一 Logger に書く場合の発信元識別子。
- `threshold_value` / `observed_value`:警告閾値と観測値の対(後続ログ集計で「閾値からどれだけ離れているか」を分析可能)。
- `occurred_at`:`clock()` の戻り値透過(monotonic seconds、AlarmEvent と同源)。

Inc.4 で UI 通知コンポーネントが本 Protocol を実装することで、警告 → 通知の経路を「Protocol 抽象化のまま」拡張可能。

#### 4.20.D `DetectionResult` 型(sealed 5 種、frozen+slots)

```python
DetectionResult = Healthy | Warning | Detected | Degraded | Failed
```

UNIT-006.1 の 4 種(Healthy / Detected / Degraded / Failed)に `Warning(triggering_value)` を加えた 5 種。**Warning と Detected を独立型として持つ理由**:

1. UTPR §7.3.20 UT-006.2-04b/04c で `triggering_value` が「警告センサー値」か「危険センサー値」かを契約検証可能(段間優先のテスト)。
2. `_apply` のディスパッチで `Warning` と `Detected` の副作用が異なる(log only vs alarm + transition)= 明示的に分岐できる sealed 型が読みやすい。
3. Inc.4 で UI 通知化する際の表示分岐(yellow vs red)を、結果型から直接得られる。

各バリアントの意味:

| バリアント | 条件 | `_apply` 副作用 |
|-----------|------|---------------|
| `Healthy()` | 両系健全 + `warn < WARN_T` + `critical < CRITICAL_T` | 両 armed を再 arm |
| `Warning(value)` | 両系健全 + `warn >= WARN_T` + `critical < CRITICAL_T` | `_on_warning`(warning_armed 連動で log)、alarm_armed 維持 |
| `Detected(value)` | 両系健全 + `critical >= CRITICAL_T`(警告の状態問わず段間優先)| `_on_detected`(alarm_armed 連動で発報 + ERROR 遷移、両 armed クリア) |
| `Degraded(failed)` | 片系 `healthy=False`、他系が下回り / 警告系のみ超過 | 両 armed を再 arm(detection 不能ではないが alarm/warning なし) |
| `Failed()` | 両系 `healthy=False` | `_on_failed`(ERROR 遷移依頼のみ、両 armed 再 arm) |

#### 4.20.E `AirBubbleDetector` クラス(DI 駆動、armed 連動冪等性)

```python
def __init__(
    self,
    *,
    sensor_reader: SensorReader,
    alarm_reporter: AlarmReporter,
    warning_logger: WarningLogger,
    state_machine: StateTransitionRequester,
    clock: Callable[[], float] = time.monotonic,
    warn_threshold: Decimal = AIR_BUBBLE_WARN_THRESHOLD,
    critical_threshold: Decimal = AIR_BUBBLE_CRITICAL_THRESHOLD,
) -> None: ...
```

内部状態は 2 つの armed フラグのみ:

- `_alarm_armed: bool` 初期値 `True`、`Detected` 発火時に `False`、`Healthy` / `Degraded` / `Failed` 経由で `True` に再 arm。
- `_warning_armed: bool` 初期値 `True`、`Warning` 発火時に `False`、`Detected` 発火時にも併せて `False`(検知昇格中の warning 重複防止)、`Healthy` / `Degraded` / `Failed` 経由で `True` に再 arm。

`_alarm_armed` と `_warning_armed` を **独立** に管理する理由:Warning → Detected の段間遷移時に `Detected` の alarm を発火可能にするため。`_warning_armed` のみ False の状態でも `_alarm_armed=True` なら新規 detected で alarm 発火 OK。

#### 4.20.F 主要 API + 動作仕様

##### 4.20.F.1 `_evaluate`(純粋関数、UT-006.2-01〜10)

```python
def _evaluate(self, warn: SensorReading, critical: SensorReading) -> DetectionResult:
    if not warn.healthy and not critical.healthy:
        return Failed()
    if critical.healthy and critical.value >= self._critical_threshold:
        return Detected(triggering_value=critical.value)
    if not critical.healthy:
        return Degraded(failed_channel=SensorKind.AIR_BUBBLE_CRITICAL)
    if not warn.healthy:
        return Degraded(failed_channel=SensorKind.AIR_BUBBLE_WARN)
    if warn.value >= self._warn_threshold:
        return Warning(triggering_value=warn.value)
    return Healthy()
```

**契約:**

- 副作用なし(self の状態を読みも書きもしない、`self._warn_threshold` / `self._critical_threshold` のみ参照)。
- 閾値境界は `>=`(inclusive)= 境界値ちょうども超過扱い(safe-side、過量投与回避と同パターン、UNIT-006.1 §4.19.F.1 と整合)。
- 段間優先(critical > warning):critical_ok かつ critical 超過なら、warn の状態を問わず Detected を返す(UT-006.2-04 = 両超過時 / UT-006.2-07 = 警告値が負値 / UT-006.2-03 = 警告下回り、すべて critical 単独で Detected)。
- 故障 channel の値は無視(`healthy=False` なら value を判定に使わない)= 故障 channel が偽の超過値を返しても判定に影響しない。
- 片系故障の方向性:critical 故障は **致命的**(代替不能 = warning は critical の代替にならない)だが、本 v0.7 ではシンプルに `Degraded` で扱い、alarm / transition なしで継続監視。SDD v0.8 で「critical 故障時の ERROR 遷移依頼」を再評価(申し送り §4.20.G.x)。

##### 4.20.F.2 `_safe_read`(SEP-003 例外吸収、UT-006.2-20)

UNIT-006.1 §4.19.F.2 と同実装:`sensor_reader.read_sensor(kind)` 呼出時の任意例外を `SensorReading(kind, Decimal(0), healthy=False)` プレースホルダに変換、`_logger.warning(...)` で記録。`noqa: BLE001` で catch-all を意図的に許容(SEP-003 = 検出経路が centralized でなくとも壊れない、UNIT-006.1 と同契約)。

##### 4.20.F.3 `_apply`(ディスパッチ、UT-006.2-19)

```python
def _apply(self, result: DetectionResult) -> None:
    if isinstance(result, Detected):
        self._on_detected(result)
        return
    if isinstance(result, Warning):
        self._on_warning(result)
        return
    if isinstance(result, Failed):
        self._on_failed()
        return
    # Healthy or Degraded
    self._alarm_armed = True
    self._warning_armed = True
```

`Healthy` / `Degraded` で両 armed を再 arm することで、再発する air bubble を毎回新規 alarm + warning として扱える(UT-006.2-19 で 6 step シーケンス検証)。

##### 4.20.F.4 `_on_detected`(armed 連動冪等性、UT-006.2-12〜17)

```python
def _on_detected(self, result: Detected) -> None:
    if not self._alarm_armed:
        return
    event = AlarmEvent(
        alarm_id=_ALARM_ID_AIR_BUBBLE,
        priority=AlarmPriority.HIGH,
        category=AlarmCategory.TECHNICAL,
        occurred_at=self._clock(),
        cause_code=_CAUSE_CODE_AIR_BUBBLE,
        metadata={"triggering_value": result.triggering_value},
    )
    try:
        self._alarm_reporter.report_alarm(event)
    except Exception:  # noqa: BLE001 — SEP-003 catch-all
        _logger.warning(...)
    self._alarm_armed = False
    self._warning_armed = False
    self._state_machine.request_state_transition(
        TargetState.ERROR,
        reason=_REASON_DETECTED,
    )
```

**契約:**

- armed 連動冪等性:`_alarm_armed=False` の間は何度 `tick()` を呼んでも alarm を重複発火しない(UT-006.2-17)。
- `_warning_armed` も併せて False に:Detected 中の Warning 重複を防ぐ(検知昇格中は警告ログ不要)。
- 発報 → 遷移順序契約:`report_alarm()` 呼出が `request_state_transition()` より厳密に先行(UT-006.2-12 で共有 trace 検証、SAD v0.2 §11.1)。
- Reporter 例外吸収:`report_alarm` が `RuntimeError` を上げても `_alarm_armed=False` セットと `request_state_transition` 呼出は実行(UT-006.2-15、SEP-003)。
- `AlarmEvent.metadata.triggering_value`:危険センサーの読み値(`Decimal`)を載せる。Inc.4 UI で「閾値からどれだけ離れているか」を可視化する用途を想定。

##### 4.20.F.5 `_on_warning`(warning_armed 連動冪等性、UT-006.2-13/16/18)

```python
def _on_warning(self, result: Warning) -> None:
    if not self._warning_armed:
        return
    try:
        self._warning_logger.log_warning(
            _DETECTOR_ID,
            threshold_value=self._warn_threshold,
            observed_value=result.triggering_value,
            occurred_at=self._clock(),
        )
    except Exception:  # noqa: BLE001 — SEP-003 catch-all
        _logger.warning(...)
    self._warning_armed = False
```

**契約:**

- warning_armed 連動冪等性:`_warning_armed=False` の間は何度 `tick()` を呼んでも logger を重複呼出しない(UT-006.2-18)。
- `_alarm_armed` は **触らない**:Warning → Detected 段間遷移時、`_on_detected` 側で alarm を出せるよう alarm_armed=True 維持。
- Logger 例外吸収:`log_warning` が `RuntimeError` を上げても `_warning_armed=False` セットは実行 = 次回 tick で重複 log 試行しない(UT-006.2-16)。
- 副作用は logger 呼出のみ(state transition なし、alarm なし)= SDD §4.20.A 設計趣旨に整合。

##### 4.20.F.6 `_on_failed`(両系故障時の安全側遷移、UT-006.2-11/20)

```python
def _on_failed(self) -> None:
    self._state_machine.request_state_transition(
        TargetState.ERROR,
        reason=_REASON_UNAVAILABLE,
    )
    self._alarm_armed = True
    self._warning_armed = True
```

**契約:**

- alarm なし(両系不信時の Detected alarm は fabrication = 不確実な事象に基づく虚偽発報を回避)、warning なし(同じ理由)。
- ERROR 遷移依頼のみ実施(State Machine 側の安全停止に委ねる、UNIT-001.1 §4.1)。
- `reason` 区別("air_bubble_detection_unavailable" vs Detected の "air_bubble_detected")= State Machine 側でログ / フォレンジック分析時に経路を区別可能。
- 両 armed 再 arm:故障から復帰した場合に新規 detection / warning を発火可能(復旧経路で alarm 漏れを防ぐ)。

#### 4.20.G 依存

| 依存 UNIT | 役割 | Step 20 X4 時点の代替 | 正式結合 |
|-----------|------|--------------------|---------|
| UNIT-002.1 Pump Simulator | センサー値供給(`AIR_BUBBLE_WARN`)| `_ScriptedSensorReader` Fake で代替 | ITPR §6.13 IT-RCM010(Inc.2 IT 実装フェーズ)|
| UNIT-002.3 Event Injection 拡張 | センサー値供給(`AIR_BUBBLE_CRITICAL` + per-channel healthy フラグ)| 同上 | UNIT-002.3 G 拡張(SDD §4.11.G、Step 20 X25〜)|
| UNIT-007.1 Alarm Reporter Core | `AlarmEvent` 配信 + ACK/SILENCE 状態管理 | `_RecordingReporter` Fake で代替 | UNIT-007.1 実装(Step 20 X22〜)|
| UNIT-001.1 State Machine 拡張 | ERROR 遷移受理 + アラーム経路統合 | `_RecordingStateMachine` Fake で代替 | UNIT-001.1 G 拡張(SDD §4.1.G、Step 20 X25〜)|
| Inc.4 UI 通知コンポーネント | `WarningLogger` 実装(yellow indicator) | `_RecordingWarningLogger` Fake で代替 | Inc.4(`WarningLogger` Protocol 互換実装) |

#### 4.20.G.x SDD v0.8 候補で詳細化する項目(本 v0.7 スコープ外)

1. **警告状態保持時間(継続警告から危険遷移する時間幅)**:現状は段間遷移を「次 tick で判定」する純粋関数 + step base モデル。bench data によっては「連続 N tick の Warning → 強制 Detected」のような時間ガード追加が必要(SDD v0.8 + Control Loop 拡張と並行)。
2. **並行 `tick` 耐性 + atomic 性**:`_alarm_armed` + `_warning_armed` の二系統 armed は現状 GIL atomic 性に依存。将来複数スレッドからの呼出が発生する場合、`threading.Lock` または `dataclass(slots=True)` + atomic CAS の検討が必要(UTPR v0.25 の並行 UT-006.2-21+ と並行)。
3. **周期 `tick` 呼出間隔**:Control Loop 拡張で確定。SDD v0.8 で `(tick_period_ms, max_consecutive_warning_ticks)` の対を明示。
4. **片系故障内部ロジック詳細**:タイムアウト / ノイズ閾値 / 連続エラーカウントの判定。UNIT-002.3 拡張で実装側詳細化、`SensorReading.healthy` の具体的故障検出ロジックは UNIT-006.2 から見ると黒箱。
5. **閾値具体値の bench 整合性**:`AIR_BUBBLE_WARN_THRESHOLD` / `AIR_BUBBLE_CRITICAL_THRESHOLD` 正式確定 + 単位の物理スケール明示(mm^3 / 正規化スケール / バーセル等)。
6. **critical 故障時の safe-side 評価**:現状は `Degraded(CRITICAL)` で alarm/transition なしだが、critical 機能の喪失は warning では代替不能 = SDD v0.8 で「critical 故障時の ERROR 遷移依頼」を再評価(UNIT-002.3 拡張で故障判定の信頼性が確定した後)。

#### 4.20.H ユニット試験設計(UTPR §7.3.20 詳細化は CR-0020 / Step 20 X6 で実施)

Step 20 X4 で実装した UT 22 ケース(`tests/unit/test_air_bubble_detector.py`、UT-006.2-01〜18 + UT-006.2-04b/04c、stmt/branch 100% = MC/DC 100% 目標達成)を UTPR §7.3.20 で詳細化する(別 PR 化、CR-0020 / Step 20 X6)。本 SDD v0.7 §4.20 では UT-006.2-NN 各ケースの設計意図は §4.20.F.x の各 API の **契約** 節で記述済(参照ガイド):

- §4.20.F.1 `_evaluate` 契約 ← UT-006.2-01〜10(parametrize + triggering_value 内容 + 境界 + 段独立 + 片系/両系故障)
- §4.20.F.2 `_safe_read` 契約 ← UT-006.2-20(Sensor 例外吸収)
- §4.20.F.3 `_apply` 契約 ← UT-006.2-19(Healthy 経由再 arm)
- §4.20.F.4 `_on_detected` 契約 ← UT-006.2-12〜17(順序契約 + AlarmEvent 内容 + Reporter 例外吸収 + 連続検知冪等性)
- §4.20.F.5 `_on_warning` 契約 ← UT-006.2-13/16/18(log のみ + Logger 例外吸収 + 連続警告冪等性)
- §4.20.F.6 `_on_failed` 契約 ← UT-006.2-11/20(ERROR 遷移のみ + alarm/warning なし + Sensor 全例外時の Failed 変換)

---

### 4.21 UNIT-006.3: Reservoir Empty Detector(Inc.2 新規、v0.8 詳細化、CR-0022 / Step 20 X8)

#### 4.21.A 目的 / 責務

薬液残量センサー入力の **単純閾値判定** で薬液切れを検知する(SRS-042、RCM-006)。単一のセンサーチャネル(`RESERVOIR`)を周期的に読み取り、以下のいずれかの行動をとる:

- **残量切れ(reservoir <= empty threshold):** `SRS-ALM-006`(MEDIUM / TECHNICAL)を発報 + State Machine に **PAUSED 遷移を依頼**。**ERROR ではなく PAUSED** = 薬液切れは機器故障ではなく消耗品の枯渇であり、オペレータが補充して復帰できる事象(SAD v0.2 §11.1 で PAUSED 路線確定)。`AlarmEvent.metadata` 内の `triggering_value` には残量センサーの読み値を載せる。
- **健全 + 残量あり(reservoir > empty threshold):** 何もしない(発報なし、遷移なし)。補充による残量回復(`Empty` → `Healthy`)は detector を **再 arm するのみ** で RUNNING 遷移は依頼しない = **自動復帰禁止**(IEC 60601-1-8 §6.4「健康ケアプロバイダの操作なしで自動復帰しない」整合)。
- **センサー故障時:** `Failed` で ERROR 遷移依頼のみ(alarm なし、safe-side)。残量を信頼できないセンサー不信は **検知不能 = 技術的故障** であり、既知の薬液切れ(PAUSED)より重篤 = ERROR 遷移で扱う(UNIT-006.1 §4.19 / UNIT-006.2 §4.20 の `Failed` → ERROR と同原則)。

**単一チャネル構成(SDD §4.21 設計趣旨):** UNIT-006.1(冗長 2 系統)/ UNIT-006.2(多段 2 系統)と異なり、UNIT-006.3 は単一の `RESERVOIR` チャネルのみを読む = 片系故障の概念がなく `Degraded` 状態を持たない(センサー故障は即 `Failed`)。`DetectionResult` は 3 種に簡素化される(§4.21.D)。

**閾値方向(`<=`):** occlusion / air_bubble は「閾値以上で異常」(`>=`)だが、reservoir は「閾値以下で異常」(`<=`)= 残量が少ない方が危険。境界値ちょうど(`value == threshold`)も `Empty` 扱い(inclusive、safe-side)。

**関連 SRS:** SRS-042(薬液切れ検知)、SRS-ALM-006(MEDIUM/TECHNICAL)、SRS-IF-010(Alarm I/F)
**関連 RCM:** RCM-006(発報必達、Designed → Verified 化目標、Inc.2 完了時)
**関連 HZ:** HZ-004(検知失敗 → アラーム失敗連鎖、EV-HZ004-003 駆動)、HZ-002(残量切れ未検出での過少投与継続、間接 = 本ユニットが検出側を担保)
**安全クラス:** C(SAD §9 SEP-000、非分離)
**実装パッケージ:** `src/vip_detection/reservoir.py` v0.1(Step 20 X7 PR #79 マージで TDD 実装、70 stmt + 10 branch、stmt/branch 100% = MC/DC 100% 目標達成)+ 共通 `src/vip_detection/protocols.py` v0.2(再利用、本 X7 では protocols.py 改訂なし)

**依存:** UNIT-002.1 Pump + UNIT-002.3 Event Injection 拡張(`RESERVOIR` 1 種センサー)、UNIT-007.1 Alarm Reporter(SEP-003)、UNIT-001.1 State Machine(PAUSED / ERROR 遷移)

#### 4.21.B 定数

| 定数名 | 型 | 値(暫定) | 用途 |
|-------|----|----------|------|
| `RESERVOIR_EMPTY_THRESHOLD` | `Final[Decimal]` | `Decimal(20)` | 薬液切れ閾値。`reading.value <= threshold` で `Empty`(SDD v0.9 で bench data に基づき正式確定予定) |

**単位:** 薬液残量センサー出力の **暫定無次元スケール**。SDD v0.9 で bench data の transfer function 確定後に再投影(mL of remaining fluid または pump 正規化スケール)。docstring に「Placeholder scale pending SDD v0.9」と明記。

#### 4.21.C 依存 protocol(`vip_detection/protocols.py` v0.2、再利用のみ)

UNIT-006.1 / UNIT-006.2 で確立した検知群共通 protocols を **再利用のみ**(本 X7 では `protocols.py` 改訂なし = 検知群ユニットで初の Protocol 改訂を伴わない実装):

| Protocol | 役割 | SEP-003 契約 |
|----------|------|------------|
| `SensorReader` | IF-U-015 pull(`RESERVOIR` 1 channel) | 例外は detector 側で吸収(`_safe_read`) |
| `AlarmReporter` | IF-U-007 push(`AlarmEvent`) | 例外伝播禁止(`_on_empty` で吸収) |
| `StateTransitionRequester` | IF-U-013 push(`PAUSED` / `ERROR` target) | idempotent、例外伝播禁止 |

`SensorKind.RESERVOIR`(protocols.py v0.1 で先見的に定義済)と `TargetState.PAUSED`(同上、`ERROR` と並ぶ 2 値の 1 つ)を使用 = **新規 Protocol / Enum メンバ追加なし**。`WarningLogger`(UNIT-006.2 で追加)は UNIT-006.3 では使用しない(単段判定のため警告段がない)。

#### 4.21.D `DetectionResult` 型(sealed 3 種、frozen+slots)

```python
DetectionResult = Healthy | Empty | Failed
```

UNIT-006.1 の 4 種(Healthy / Detected / Degraded / Failed)/ UNIT-006.2 の 5 種(+ Warning)から **3 種に簡素化**。**`Degraded` を持たない理由**:UNIT-006.3 は単一チャネルのため「片系故障で他系継続」の概念がなく、センサー故障は即 `Failed`。検知群ユニットの `DetectionResult` 種別数は **チャネル構成 + 段数に応じて変動** する(§4.21.A 設計趣旨)。

各バリアントの意味:

| バリアント | 条件 | `_apply` 副作用 |
|-----------|------|---------------|
| `Healthy()` | `healthy` + `value > EMPTY_T` | armed を再 arm(補充復元、RUNNING 遷移は依頼しない) |
| `Empty(triggering_value)` | `healthy` + `value <= EMPTY_T` | `_on_empty`(armed 連動で発報 + PAUSED 遷移、armed クリア) |
| `Failed()` | `not healthy` | `_on_failed`(ERROR 遷移依頼のみ、armed 再 arm) |

`Empty` の `triggering_value: Decimal` は残量センサーの読み値を搬送(UT-006.3-03b で契約検証、`AlarmEvent.metadata` 経由で Inc.4 UI が「閾値からどれだけ下回っているか」を可視化する用途を想定)。

#### 4.21.E `ReservoirEmptyDetector` クラス(DI 駆動、単一 armed 連動冪等性)

```python
def __init__(
    self,
    *,
    sensor_reader: SensorReader,
    alarm_reporter: AlarmReporter,
    state_machine: StateTransitionRequester,
    clock: Callable[[], float] = time.monotonic,
    empty_threshold: Decimal = RESERVOIR_EMPTY_THRESHOLD,
) -> None: ...
```

内部状態は **単一の armed フラグのみ**(UNIT-006.2 の二系統 armed から単段へ簡素化):

- `_armed: bool` 初期値 `True`、`Empty` 発火時に `False`、`Healthy`(補充復元)/ `Failed`(センサー故障)経由で `True` に再 arm。

`Healthy` と `Failed` の **双方** で再 arm する理由:補充による残量回復(`Healthy`)後の再度の薬液切れ、およびセンサー故障(`Failed`)からの復帰後の薬液切れを、いずれも新規 alarm として発火させる(復旧経路での alarm 漏れを防ぐ、UT-006.3-08 / UT-006.3-14 で検証)。

#### 4.21.F 主要 API + 動作仕様

##### 4.21.F.1 `_evaluate`(純粋関数、UT-006.3-01〜03 / 03b / 11)

```python
def _evaluate(self, reading: SensorReading) -> DetectionResult:
    if not reading.healthy:
        return Failed()
    if reading.value <= self._empty_threshold:
        return Empty(triggering_value=reading.value)
    return Healthy()
```

**契約:**

- 副作用なし(self の状態を読みも書きもしない、`self._empty_threshold` のみ参照)。
- decision order:`healthy` フラグを **最優先** で判定 = 故障センサーの `value` は判定に使わない(`_safe_read` がプレースホルダ `Decimal(0)` を載せても `healthy=False` なら `Failed` に分岐、UT-006.3-11 / UT-006.3-13)。
- 閾値境界は `<=`(inclusive)= 境界値ちょうど(`value == threshold`)も `Empty` 扱い(safe-side、薬液切れ見逃し回避、UT-006.3-02)。occlusion / air_bubble の `>=` とは方向が逆(残量は少ない方が危険)。
- `Empty.triggering_value` には観測値(`reading.value`)を載せる(UT-006.3-03b)。

##### 4.21.F.2 `_safe_read`(SEP-003 例外吸収、UT-006.3-13)

UNIT-006.1 §4.19.F.2 / UNIT-006.2 §4.20.F.2 と同実装:`sensor_reader.read_sensor(SensorKind.RESERVOIR)` 呼出時の任意例外を `SensorReading(RESERVOIR, Decimal(0), healthy=False)` プレースホルダに変換、`_logger.warning(...)` で記録。`noqa: BLE001` で catch-all を意図的に許容(SEP-003 = 検出経路が壊れても周期 tick は継続)。プレースホルダ値 `Decimal(0)` は「残量ゼロ = 非常に空」を意味するが、`healthy=False` のため `_evaluate` は `value` を見ずに `Failed` に分岐する(UT-006.3-13 で例外 → `Failed` → ERROR 遷移を検証)。

##### 4.21.F.3 `_apply`(ディスパッチ、UT-006.3-08/09)

```python
def _apply(self, result: DetectionResult) -> None:
    if isinstance(result, Empty):
        self._on_empty(result)
        return
    if isinstance(result, Failed):
        self._on_failed()
        return
    # Healthy
    self._armed = True
```

`Healthy`(補充による残量回復)で armed を再 arm することで、再発する薬液切れを毎回新規 alarm として扱える(UT-006.3-08)。**`Healthy` 経路では State Machine への遷移依頼を一切行わない** = 自動 RUNNING 復帰を依頼しない(UT-006.3-09、IEC 60601-1-8 §6.4 整合。`TargetState` enum が `ERROR` / `PAUSED` のみで `RUNNING` を構造的に持たないため、detector に「自動復帰させるコード経路が存在しない」ことが型レベルで保証される)。

##### 4.21.F.4 `_on_empty`(armed 連動冪等性、UT-006.3-04〜07 / 10)

```python
def _on_empty(self, result: Empty) -> None:
    if not self._armed:
        return
    event = AlarmEvent(
        alarm_id=_ALARM_ID_RESERVOIR,
        priority=AlarmPriority.MEDIUM,
        category=AlarmCategory.TECHNICAL,
        occurred_at=self._clock(),
        cause_code=_CAUSE_CODE_RESERVOIR_EMPTY,
        metadata={"triggering_value": result.triggering_value},
    )
    try:
        self._alarm_reporter.report_alarm(event)
    except Exception:  # noqa: BLE001 — SEP-003 catch-all
        _logger.warning(...)
    self._armed = False
    self._state_machine.request_state_transition(
        TargetState.PAUSED,
        reason=_REASON_EMPTY,
    )
```

**契約:**

- armed 連動冪等性:`_armed=False` の間は何度 `tick()` を呼んでも alarm を重複発火しない + PAUSED 遷移依頼も重複しない(UT-006.3-07)。
- `AlarmEvent` 内容:`priority=MEDIUM` / `category=TECHNICAL`(SRS-ALM-006、IEC 60601-1-8 §6.1 中優先度 / §5.1.4 テクニカル)、`cause_code='reservoir_empty'`、`occurred_at` は `clock()` 戻り値透過、`metadata.triggering_value` は残量読み値(UT-006.3-05)。
- 発報 → 遷移順序契約:`report_alarm()` 呼出が `request_state_transition()` より厳密に先行(UT-006.3-04 で共有 trace 検証、SAD v0.2 §11.1)。
- Reporter 例外吸収:`report_alarm` が `RuntimeError` を上げても `_armed=False` セットと `request_state_transition(PAUSED)` 呼出は実行(UT-006.3-10、SEP-003)。
- 遷移先は `PAUSED`(`reason='reservoir_empty'`)= 薬液切れは消耗品枯渇でありオペレータ復帰可能(§4.21.A)。

##### 4.21.F.5 `_on_failed`(センサー故障時の安全側遷移、UT-006.3-12/14)

```python
def _on_failed(self) -> None:
    self._state_machine.request_state_transition(
        TargetState.ERROR,
        reason=_REASON_UNAVAILABLE,
    )
    self._armed = True
```

**契約:**

- alarm なし(センサー不信時の `Empty` alarm は fabrication = 不確実な事象に基づく虚偽発報を回避、UNIT-006.1 / UNIT-006.2 の `_on_failed` と同原則)。
- 遷移先は `ERROR`(`reason='reservoir_detection_unavailable'`)= 検知不能は既知の薬液切れ(PAUSED)より重篤な技術的故障として扱う。`reason` 区別("reservoir_detection_unavailable" vs `_on_empty` の "reservoir_empty")= State Machine 側でログ / フォレンジック分析時に経路を区別可能。
- armed 再 arm:センサー故障から復帰した場合に新規 `Empty` を発火可能(復旧経路で alarm 漏れを防ぐ、UT-006.3-14 で `Empty` → `Failed` → `Empty` シーケンス検証)。

#### 4.21.G 依存

| 依存 UNIT | 役割 | Step 20 X7 時点の代替 | 正式結合 |
|-----------|------|--------------------|---------|
| UNIT-002.1 Pump Simulator | センサー値供給(`RESERVOIR`)| `_ScriptedSensorReader` Fake で代替 | ITPR §6.11 IT-RCM006(Inc.2 IT 実装フェーズ)|
| UNIT-002.3 Event Injection 拡張 | センサー値供給(`RESERVOIR` + healthy フラグ)| 同上 | UNIT-002.3 G 拡張(SDD §4.11.G、Step 20 X25〜)|
| UNIT-007.1 Alarm Reporter Core | `AlarmEvent` 配信 + ACK/SILENCE 状態管理 | `_RecordingReporter` Fake で代替 | UNIT-007.1 実装(Step 20 X22〜)|
| UNIT-001.1 State Machine 拡張 | PAUSED / ERROR 遷移受理 + アラーム経路統合 | `_RecordingStateMachine` Fake で代替 | UNIT-001.1 G 拡張(SDD §4.1.G、Step 20 X25〜)|

#### 4.21.G.x SDD v0.9 候補で詳細化する項目(本 v0.8 スコープ外)

1. **ヒステリシス(チャタリング防止の上下 2 閾値帯)**:現状は単一閾値 + `<=` の単純判定。残量センサー値が閾値近傍で振動すると `Empty` ↔ `Healthy` が頻繁に切り替わりうる(armed 連動冪等性で alarm 重複は防げるが、補充途中の微小な揺らぎで再 arm が起きる)。bench data によっては「`Empty` 判定の閾値 < `Healthy` 復帰の閾値」の 2 閾値帯(ヒステリシス)が必要(SDD v0.9 + Control Loop 拡張と並行)。
2. **並行 `tick` 耐性 + atomic 性**:`_armed` 単一フラグは現状 GIL atomic 性に依存。将来複数スレッドからの呼出が発生する場合、`threading.Lock` の検討が必要(UTPR v0.26 の並行 UT-006.3-15+ と並行)。
3. **周期 `tick` 呼出間隔**:Control Loop 拡張で確定。SDD v0.9 で `tick_period_ms` を明示。
4. **片系故障内部ロジック詳細**:タイムアウト / ノイズ閾値 / 連続エラーカウントの判定。UNIT-002.3 拡張で実装側詳細化、`SensorReading.healthy` の具体的故障検出ロジックは UNIT-006.3 から見ると黒箱。
5. **閾値具体値の bench 整合性**:`RESERVOIR_EMPTY_THRESHOLD` 正式確定 + 単位の物理スケール明示(mL / 正規化スケール等)。

#### 4.21.H ユニット試験設計(UTPR §7.3.21 詳細化は CR-0023 / Step 20 X9 で実施)

Step 20 X7 で実装した UT 15 ケース(`tests/unit/test_reservoir_empty_detector.py`、UT-006.3-01〜14、stmt/branch 100% = MC/DC 100% 目標達成)を UTPR §7.3.21 で詳細化する(別 PR 化、CR-0023 / Step 20 X9)。本 SDD v0.8 §4.21 では UT-006.3-NN 各ケースの設計意図は §4.21.F.x の各 API の **契約** 節で記述済(参照ガイド):

- §4.21.F.1 `_evaluate` 契約 ← UT-006.3-01〜03(閾値マトリクス parametrize)+ 03b(triggering_value 内容)+ 11(unhealthy → Failed)
- §4.21.F.2 `_safe_read` 契約 ← UT-006.3-13(Sensor 例外吸収 → Failed 変換)
- §4.21.F.3 `_apply` 契約 ← UT-006.3-08(Healthy 経由再 arm)+ 09(自動 RUNNING 復帰非依頼)
- §4.21.F.4 `_on_empty` 契約 ← UT-006.3-04〜07(発報 → PAUSED 順序契約 + AlarmEvent 内容 + Healthy 無作用 + armed 連動冪等性)+ 10(Reporter 例外吸収)
- §4.21.F.5 `_on_failed` 契約 ← UT-006.3-12(ERROR 遷移のみ + alarm なし + reason 区別)+ 14(Failed 経由再 arm)

---

### 4.22 UNIT-006.4: Alarm Task Watchdog(Inc.2 新規、骨格、v0.5、CR-0009 / Step 20 E)

- **目的 / 責務:** アラームタスクの実行を監視し、デッドロック・タスク停止を **1 秒以内に検知**(RCM-011)。検知時は ERROR 状態遷移 + 独立アラーム発報路(UNIT-006.5 Alarm Path Redundancy 経由 RCM-012)で発報を試みる。Inc.1 の UNIT-001.5 SW Watchdog(制御ループ監視)と独立した監視責務を持つ。
- **関連 SRS:** SRS-044, SRS-RCM-011, SRS-IF-010
- **関連 RCM:** RCM-011(アラームタスク監視)
- **安全クラス:** C(SAD §9 SEP-000、非分離)
- **新規パッケージ予定:** `src/vip_detection/alarm_task_watchdog.py`

**主要 API(候補):**

| 関数・メソッド | 引数 | 戻り値 | 概要 |
|--------------|------|-------|------|
| `heartbeat() -> None` | — | `None` | アラームタスク側から定期的に呼出し(タスク生存通知) |
| `tick() -> None` | — | `None` | 監視側で周期駆動、`heartbeat` 経過時間が閾値超過なら検知 |

**依存:** UNIT-007.1 Alarm Reporter Core(heartbeat 元 = アラームタスク自身)、UNIT-006.5 Alarm Path Redundancy(主系故障時の予備系発報経路)、UNIT-001.1 State Machine(ERROR 遷移依頼)

**SDD v0.6 候補で詳細化する項目:**

- タイムアウト値(SRS-RCM-011「1 秒以内」を SDD で具体値 = 例 800 ms 余裕付け)
- UNIT-001.5 SW Watchdog との設計上の独立性(別スレッド / 別 timer / 異なる監視対象)
- 監視タスク自身の停止検知(誰が watchdog の watchdog をするか = self-check 機構)
- ユニット試験設計(UT-006.4-01〜:正常 heartbeat / タイムアウト境界 / アラームタスク模擬停止)

---

### 4.23 UNIT-006.5: Alarm Path Redundancy(Inc.2 新規、骨格、v0.5、CR-0009 / Step 20 E)

- **目的 / 責務:** アラーム発報路を **主系 / 予備系の冗長化** で実装(RCM-012)。主系故障時(発報路故障・タスク停止)に予備系で発報を継続。両系故障時は ERROR 遷移 + 制御停止。本ユニットは UNIT-007.1 Alarm Reporter Core への発報依頼を主 / 予備の 2 経路で多重化し、主系失敗を検知して予備系へフェイルオーバーする。
- **関連 SRS:** SRS-RCM-012, SRS-IF-010
- **関連 RCM:** RCM-012(アラーム発報路冗長化)
- **安全クラス:** C(SAD §9 SEP-000、非分離)
- **新規パッケージ予定:** `src/vip_detection/alarm_path_redundancy.py`

**主要 API(候補):**

| 関数・メソッド | 引数 | 戻り値 | 概要 |
|--------------|------|-------|------|
| `report(event: AlarmEvent) -> ReportResult` | アラームイベント | `Ok` / `PrimaryFailedSecondaryOk` / `BothFailed` | 主系発報失敗を検知し予備系へフェイルオーバー |

**依存:** UNIT-007.1 Alarm Reporter Core(主系 / 予備系の 2 インスタンス)、UNIT-001.1 State Machine(両系故障時の ERROR 遷移)

**SDD v0.6 候補で詳細化する項目:**

- 主系失敗の検知条件(タイムアウト / 例外 / 戻り値)
- 予備系発報の試行戦略(同時並行発報 / 主系失敗確認後の逐次発報)
- 主系 / 予備系の隔離(プロセス分離 / スレッド分離 / 単純な経路分離のいずれか採用)
- ユニット試験設計(UT-006.5-01〜:主系健全 / 主系故障 + 予備系健全 / 両系故障 / 主系遅延)

---

### 4.24 UNIT-006.6: Battery Low Detector(Inc.2 新規、骨格、v0.5、CR-0009 / Step 20 E、HZ-009 対応)

- **目的 / 責務:** 電源電圧 / バッテリ残量センサー入力の閾値判定でバッテリ低下を検知する(SRS-043)。**HZ-009 対応**(RMF v0.4 で識別、Inc.2 範囲計画書 §5.2 で SDP §3.2 vs Inc.1 RMF 未識別ギャップを発見、本 v0.5 で UNIT 化)。閾値以下となった時点でバッテリ低下と判定し、SRS-ALM-007(中優先度・テクニカル)を発報。安全側遷移ロジック(RCM-020 候補:バッテリ管理ロジック / 安全側遷移)は **SRS への正式登録を Step 20 B-3 候補として申し送り中**、本 v0.5 では UNIT-001.1 State Machine への通知 + Alarm Reporter 経由発報まで設計確定。
- **関連 SRS:** SRS-043, SRS-ALM-007, SRS-IF-010
- **関連 RCM:** RCM-006(発報必達)、**RCM-020 候補(SRS 登録待ち)**
- **関連ハザード:** HZ-009(バッテリ低下によるソフトウェア機能喪失)
- **安全クラス:** C(SAD §9 SEP-000、非分離)
- **新規パッケージ予定:** `src/vip_detection/battery.py`

**主要 API(候補):** `tick()` + `_evaluate(reading: SensorReading) -> DetectionResult`

**依存:** UNIT-002.1 Pump + UNIT-002.3(`BATTERY` センサー、`VirtualHwEventKind.BATTERY_LOW` 経由注入)、UNIT-007.1 Alarm Reporter、UNIT-001.1 State Machine

**SDD v0.6 候補で詳細化する項目:**

- 閾値 値・単位(SRS-043 で定性指定、SDD で具体値 = 例 残量 < 15% を低下、< 5% を緊急、SRS-RCM-006 と整合)
- ヒステリシス検討(電圧変動でのチャタリング防止)
- 安全側遷移ロジック(RCM-020 候補):バッテリ低下時の自動 PAUSED 遷移 / 注入レート低下 / 制御停止のいずれか + Inc.2 着手中の SRS 追加改訂(Step 20 B-3 候補)で SRS-RCM-020 として正式登録予定
- ユニット試験設計(UT-006.6-01〜:正常 / 警告閾値 / 緊急閾値 / バッテリ復帰 / `BATTERY_LOW` イベント注入連携)

---

### 4.25 UNIT-007.1: Alarm Reporter Core(Inc.2 新規、骨格、v0.5、CR-0009 / Step 20 E、SEP-003 分離継続)

- **目的 / 責務:** `AlarmReportInterface` の本実装(SRS-IF-010)。`report_alarm` + `acknowledge` + `silence` の 3 メソッドを提供し、検知群 + State Machine + Control API からのアラーム関連呼出を集約する。**SEP-003 分離契約に基づきクラス B**(検知ロジックなし、`AlarmEvent` を frozen 値型で受け取って分類 + 通知のみ実施、制御コアへの逆方向データフロー禁止)。実装層はログ + 内部キュー(Inc.2 範囲)、Inc.4 で UI / 通知装置へ拡張予定。
- **関連 SRS:** SRS-IF-010, SRS-O-040, SRS-ALM-001/004〜008
- **関連 RCM:** RCM-006(発報必達 + 1 秒以内発報)
- **安全クラス:** **B**(SAD §9 SEP-003、分離継続、本実装後も維持)
- **新規パッケージ予定:** `src/vip_alarm/reporter.py`(クラス B、`vip_ctrl.*` / `vip_sim.*` への戻り値書込み禁止 + 例外伝播禁止を AST 機械検証)

**主要 API(候補):**

| 関数・メソッド | 引数 | 戻り値 | 概要 |
|--------------|------|-------|------|
| `report_alarm(event: AlarmEvent) -> None`(IF-U-007 / IF-U-012) | frozen+slots `AlarmEvent` | `None`(単方向、戻り値で制御フロー伝達なし) | 検知群 / State Machine からの発報受領 |
| `acknowledge(alarm_id: str) -> None`(IF-U-014) | アラーム ID | `None` | Control API からの ACK 受領 |
| `silence(alarm_id: str, duration_sec: int) -> None`(IF-U-014) | アラーム ID + 消音時間 | `None`(高優先度時 ≤ 120 秒制限を内部で強制) | Control API からの消音受領 |

**依存:** UNIT-007.2 Alarm Priority Classifier(優先度・区分判定)、ARCH-009 Logging Stub(ログ出力)、内部キュー(Inc.4 で UI 拡張用)

**SDD v0.6 候補で詳細化する項目:**

- `AlarmEvent` の frozen + slots + `metadata` の `MappingProxyType` ラップ実装契約(IF-U-007 詳細)
- ACTIVE / ACKED / SILENCED / CLEARED 状態遷移の本実装(SAD §5.3 の状態遷移を SDD で具体化)
- 高優先度アラーム ≤ 120 秒消音時間制限の強制(`silence` 内部で `duration_sec` をクランプ or `Err` 返却)
- 例外契約(SEP-003 違反検知 = ARCH-007.x からの例外を呼出元に伝播させない契約、内部 try/except + ログのみ)
- 主系 / 予備系 2 インスタンス対応(UNIT-006.5 Alarm Path Redundancy が本 UNIT を 2 重化する前提のシングルトン回避設計)
- ユニット試験設計(UT-007.1-01〜:基本発報 / ACK / SILENCE / 状態遷移網羅 / 高優先度消音制限 / 例外伝播禁止契約)

---

### 4.26 UNIT-007.2: Alarm Priority Classifier(Inc.2 新規、骨格、v0.5、CR-0009 / Step 20 E、純粋関数)

- **目的 / 責務:** IEC 60601-1-8 §6.1 優先度判定(高 / 中 / 低)+ §5.1.4 テクニカル / 生理アラーム区分判定。検知群からの `cause_code`(`occlusion` / `air_bubble_critical` / `reservoir_empty` / `battery_low` / `alarm_task_failure` / `control_error` 等の sealed 値)を入力に受け、`AlarmPriority` + `AlarmCategory` を決定する純粋関数。**副作用なし、内部状態なし、外部 I/O なし**(SEP-003 分離契約の根拠)。
- **関連 SRS:** SRS-REG-002, SRS-ALM-004〜008
- **関連 RCM:** —(直接の RCM 実装ではなく、UNIT-007.1 + ARCH-006 検知群の支援ユニット)
- **関連規格:** IEC 60601-1-8 §6.1(優先度分類)+ §5.1.4(テクニカル / 生理区分)
- **安全クラス:** **B**(SAD §9 SEP-003、分離継続)
- **新規パッケージ予定:** `src/vip_alarm/priority_classifier.py`(クラス B、純粋関数、AST 機械検証で内部状態 / 外部 I/O が無いことを担保)

**主要 API(候補):**

| 関数・メソッド | 引数 | 戻り値 | 概要 |
|--------------|------|-------|------|
| `classify(cause_code: str) -> ClassificationResult` | sealed `cause_code` 値 | `(AlarmPriority, AlarmCategory)` | IEC 60601-1-8 §6.1 + §5.1.4 整合 |

**Inc.2 範囲の対応表(SAD §5.2 / SRS §4.4.A 連携):**

| `cause_code` | `priority` | `category` | 関連 SRS-ALM |
|------------|-----------|-----------|------------|
| `occlusion` | HIGH | TECHNICAL | SRS-ALM-004 |
| `air_bubble_critical` | HIGH | TECHNICAL | SRS-ALM-005 |
| `reservoir_empty` | MEDIUM | TECHNICAL | SRS-ALM-006 |
| `battery_low` | MEDIUM | TECHNICAL | SRS-ALM-007 |
| `alarm_task_failure` | HIGH | TECHNICAL | (RCM-011 経由、SRS-ALM 直接対応なし) |
| `control_error` | HIGH | TECHNICAL | SRS-ALM-001(既存)|

**依存:** なし(純粋関数、外部依存なし、テスト容易性最大)

**SDD v0.6 候補で詳細化する項目:**

- `cause_code` の sealed enum 化(`Literal["occlusion", "air_bubble_critical", ...]` or `enum.StrEnum`)
- 未知 `cause_code` 受領時の挙動(`raise ValueError` か `LOW + TECHNICAL` でフォールバックか、UNIT-007.1 側との例外契約整合)
- 優先度 LOW の cause_code を Inc.4 で追加した場合の影響範囲(本 UNIT は表参照のみで拡張容易)
- ユニット試験設計(UT-007.2-01〜:Inc.2 範囲 6 種全網羅 + 未知値挙動 + 戻り値型不変性)

---

## 5. インタフェースの詳細設計(箇条 5.4.3 ― クラス C)

### 5.1 ユニット間インタフェース(Inc.1 範囲、SAD §5 の U 系 11 件の詳細化 + v0.5 で Inc.2 IF-U-007 詳細化 + IF-U-012〜015 追加)

| IF ID | 呼出側 | 被呼出側 | シグネチャ(Python 型ヒント) | 同期 | エラー返却 |
|-------|-------|---------|-------------------------|------|----------|
| IF-U-001 | UNIT-005.1 | UNIT-001.3 | `enqueue(cmd: Command) -> AcceptResult` | 同期 | 戻り値 `AcceptResult` (`Accepted(token)` / `Rejected(reason)`) |
| IF-U-002 | UNIT-001.2 | UNIT-002.1 | `set_flow_rate(value: Decimal) -> None`(内部で UNIT-001.4 Validator 経由) | 同期 | Validator が失敗時 State Machine に ERROR イベント送信、本 I/F は戻り値なし |
| IF-U-003 | UNIT-001.2 / UNIT-005.2 | UNIT-002.2 | `observe() -> PumpSnapshot` | 同期、idempotent | 例外なし(スナップショットは常に取得可能) |
| IF-U-004 | UNIT-001.1 | ARCH-003 経由で UNIT-003.1/3.3 | `save_async(record: PersistedRecord) -> None`(キュー投入のみ) | 非同期、FIFO | キュー満杯: `queue.Full` を内部捕捉 → WDT 経由 ERROR |
| IF-U-005 | UNIT-004.1 | UNIT-003.1、UNIT-003.3 | `load() -> LoadResult` | 同期(起動時のみ) | `Ok(RawPersistedRecord)` / `Err(LoadError)` |
| IF-U-006 | UNIT-004 全般 | UNIT-001.1 | `set_initial(state: State, needs_confirm: bool) -> None` | 同期 | 事前条件違反で `InvalidInitializationError` |
| **IF-U-007**(v0.5 詳細化)| UNIT-001.1 / ARCH-006 検知群 | **UNIT-007.1 Alarm Reporter Core**(Inc.2 で本実装、Inc.1 までは no-op) | `report_alarm(event: AlarmEvent) -> None`(`AlarmEvent` は frozen + slots dataclass、§5.1.A 詳細参照) | 同期、一方向 | **例外伝播禁止契約**(UNIT-007.1 内部で try/except + ログ、呼出元への伝播なし、SEP-003 違反検知の根拠) |
| IF-U-008 | 全コア UNIT | **ARCH-009 Logging Stub**(旧 ARCH-006、SAD v0.2 でリネーム) | `log(record: LogRecord) -> None`(本版 no-op、一方向) | 同期 | 例外伝播禁止契約(SEP-002) |
| IF-U-009 | UNIT-001.5 | UNIT-001.1 | `request_transition(Event(WDT_TIMEOUT))` | 同期 | State Machine の戻り値 |
| IF-U-010 | UNIT-001.2 | UNIT-001.5 | `heartbeat(ts: Monotonic) -> None` | 同期 | 失敗なし |
| IF-U-011 | UNIT-001.2 | UNIT-002.4 | `heartbeat(ts: Monotonic) -> None` | 同期 | 失敗なし |
| **IF-U-012**(v0.5 新規、Inc.2)| ARCH-006 検知群各ユニット(UNIT-006.1〜006.6)| UNIT-007.1 Alarm Reporter Core | `report_alarm(event: AlarmEvent) -> None`(IF-U-007 と同シグネチャ、検知群からの主呼出経路。検知群側で `cause_code` を生成し UNIT-007.2 Priority Classifier 経由で `AlarmEvent` を構築) | 同期、一方向 | 例外伝播禁止契約(IF-U-007 と同) |
| **IF-U-013**(v0.5 新規、Inc.2)| ARCH-006 検知群各ユニット | UNIT-001.1 State Machine | `request_state_transition(target: StateKind, reason: DetectionReason) -> Result[None, StateMachineError]` | 同期(検知群が周期駆動から呼出、State Machine 側で内部 lock 取得)| 戻り値 `Result[None, StateMachineError]`(`Ok(None)` / `Err(InvalidTransitionError)`)|
| **IF-U-014**(v0.5 新規、Inc.2)| UNIT-005.1 Control API | UNIT-007.1 Alarm Reporter Core | `acknowledge(alarm_id: str) -> None` / `silence(alarm_id: str, duration_sec: int) -> None`(IEC 60601-1-8 §6.4 確認・休止規定準拠、高優先度の消音時間制限あり)| 同期、一方向 | 例外伝播禁止契約(SEP-003) |
| **IF-U-015**(v0.5 新規、Inc.2)| ARCH-006 検知群各ユニット | UNIT-002.1 Pump Simulator / UNIT-002.3 Event Injection | `read_sensor(kind: SensorKind) -> SensorReading`(`SensorKind` = `OCCLUSION_PRIMARY` / `OCCLUSION_SECONDARY` / `AIR_BUBBLE_WARN` / `AIR_BUBBLE_CRITICAL` / `RESERVOIR` / `BATTERY` の sealed enum、冗長 2 系統独立性 = SRS-RCM-009 根拠)| 同期、idempotent | 例外なし(センサー値は常に取得可能、計測失敗は `SensorReading.healthy` フラグで表現)|

#### 5.1.A `AlarmEvent` 型構造の Python 実装契約(IF-U-007 / IF-U-012 詳細、v0.5 確定、SAD §5.2 連携)

`AlarmEvent` は ARCH-006 Detection 検知群 / UNIT-001.1 State Machine から UNIT-007.1 Alarm Reporter Core への単方向通知で渡される **frozen 値型**(SEP-003 分離契約に基づく不変性要求)。SRS-O-040 の正式構造として SAD v0.2 §5.2 で確定済、本 SDD v0.5 で **Python 実装契約** を確定する。

```python
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping
import enum

class AlarmPriority(enum.Enum):
    HIGH = "high"      # IEC 60601-1-8 §6.1 高優先度
    MEDIUM = "medium"  # 同 中優先度
    LOW = "low"        # 同 低優先度

class AlarmCategory(enum.Enum):
    TECHNICAL = "technical"        # IEC 60601-1-8 §5.1.4 テクニカル(機器自身の異常)
    PHYSIOLOGICAL = "physiological"  # 同 生理(患者の生理状態)

@dataclass(frozen=True, slots=True)
class AlarmEvent:
    alarm_id: str           # uuid4 ベース、ACK / Silence の対象指定に使用
    priority: AlarmPriority # UNIT-007.2 Priority Classifier が cause_code から決定
    category: AlarmCategory # 同上、Inc.2 範囲は全 TECHNICAL
    occurred_at: float      # Unix epoch 秒(`time.time` 値、`time.monotonic` との併用は SDD v0.6 候補で検討)
    cause_code: str         # sealed 値("occlusion" / "air_bubble_critical" / "reservoir_empty" / "battery_low" / "alarm_task_failure" / "control_error" 等)
    metadata: Mapping[str, object]  # frozen、MappingProxyType でラップ

# バリデーション規則(コンストラクタで検証):
# - alarm_id 非空 + uuid4 形式想定
# - cause_code は sealed 値のみ(UNIT-007.2 の対応表と整合)
# - occurred_at > 0
# - metadata は MappingProxyType でラップ済(直接 dict を渡す場合は __post_init__ で変換)
```

**不変性契約:**

- `dataclass(frozen=True, slots=True)`:全フィールドへの代入禁止 + メモリ効率化
- `metadata` は `__post_init__` で `MappingProxyType` ラップを強制(直接 `dict` が渡された場合も読み取り専用ビューに変換)、**境界を越えた変更を禁止**(SEP-003 違反検知の機械的根拠)
- `__hash__` 自動生成(frozen のため)、UNIT-007.1 内部の `dict[alarm_id, AlarmEvent]` 状態管理で利用可能

**例外契約(SEP-003 整合):**

- `AlarmEvent` 構築時のバリデーション失敗(`cause_code` が sealed 値外、`alarm_id` が空、等)は **構築側(検知群 / UNIT-007.2)で `ValueError`** を投げる(構築側はクラス C で、本ファイルではなく検知群側の責務)
- UNIT-007.1 Alarm Reporter Core 側では `AlarmEvent` を **そのまま受け取って処理**(再バリデーションしない、frozen 契約で不変性が保証されている)
- 構築失敗で `AlarmEvent` が作れなかった場合は、検知群側でログ + State Machine への ERROR 遷移依頼で対処(IF-U-013 経由)、Alarm Reporter には届かない

**SDD v0.6 候補で詳細化する項目:**

- `__post_init__` の具体実装(MappingProxyType ラップ + cause_code sealed 検証)
- `time.time` vs `time.monotonic` 併用ポリシー(walltime 表示と stopwatch 計測の使い分け)
- `metadata` 内部の object 型制約(JSON シリアライズ可能性 = ロギング連携)
- ハッシュ衝突 / 同一 alarm_id 重複検知時の挙動(UNIT-007.1 状態管理での扱い)

### 5.2 外部インタフェース(E 系 2 件の詳細化)

| IF ID | 相手 | プロトコル | データ形式 | タイミング |
|-------|------|---------|----------|-----------|
| IF-E-001 | 外部呼出元(Inc.4 UI / 試験ハーネス) | Python モジュール公開関数(`vip_ctrl.api.*`) | 入出力は pydantic モデル / dataclass / Decimal | コマンドは任意時刻、観測は任意時刻(idempotent) |
| IF-E-002 | OS ファイルシステム | POSIX(`os.open`, `os.fsync`, `os.replace`, `os.unlink`)/ Windows は `os.replace` 互換パス | ローカルファイル、JSON + SHA-256 | 永続化サイクル 1 秒以内 |

### 5.3 全 I/F の分離境界対応

SAD §9 の SEP-001/002/003 に従い、分離境界を越える I/F は **I/F-U-002/003/007/008** と **05.3 Validation API** である。これらは以下の要件を満たす:

- **データ型はすべて frozen**(dataclass/pydantic の `model_config = ConfigDict(frozen=True)`)
- **戻り値による一方向**(例外での制御移動を禁止、分離 I/F は例外を投げない契約)
- **ログ/アラーム実装側の例外は呼出側で握りつぶす**(分離の遵守)

## 6. 詳細設計の検証(箇条 5.4.4 ― クラス C)

### 6.1 検証観点チェックリスト

- [x] アーキテクチャ設計(SAD-VIP-001 v0.1)で定義された制約・インタフェースを実装している — SAD §5 の 12 I/F をすべて §5 で詳細化
- [x] SRS の要求事項を実装可能な形で具体化している — §4 の詳細 5 件 + 骨格 9 件で Inc.1 範囲 SRS を網羅(§7 トレーサビリティ)
- [x] リスクコントロール手段を正しく実現している — §4.1/§4.2/§4.3/§4.5 で RCM-019/001/004/015 の実装詳細を明示
- [x] ソフトウェアユニット単位で試験可能に記述されている — 詳細 5 件は「検証方法」節で試験方法を指定。骨格 9 件は SDD v0.2 で追補
- [x] 異常系・境界条件が網羅的に定義されている — 詳細 5 件の §x.E「例外・異常系」で個別記載
- [x] 資源制約(スタック、実行時間等)が守られる設計となっている — 詳細 5 件の §x.D「資源使用量・タイミング制約」で記載

### 6.2 レビュー記録

| 項目 | 結果 | レビュー日 | 記録 |
|------|------|----------|------|
| 代表 5 ユニットの §5.4.2 詳細記述の充足性 | Pass | 2026-04-18 | 本書 §4.1〜§4.5 |
| §5.4.3 I/F 詳細設計の網羅性 | Pass | 2026-04-18 | 本書 §5 |
| 骨格 9 ユニットの SDD v0.2 追補計画の妥当性 | Pass(v0.2 で詳細化する項目を各ユニットで明示) | 2026-04-18 | 本書 §4.2(v0.1 当時) |
| 分離境界(SEP-001/002/003)の詳細設計反映 | Pass | 2026-04-18 | §5.3 |
| **v0.2 追加 12 ユニット詳細記述の充足性** | Pass | 2026-04-19 | 本書 §4.6〜§4.17 |
| **v0.2 で発見した SRS 整合性課題の追跡可能性** | Pass(§6.4 申し送り表に集約) | 2026-04-19 | 本書 §6.4 |

### 6.3 骨格記述の解消(v0.2 で完了)

v0.1 で骨格記述に留めていた 12 ユニットを §5.4.2 詳細記述に展開した(本書 §4.6〜§4.17)。これにより:

- **実装ブロックの解除:** 全 17 ユニットが §5.4.2 要件を充足。Inc.1 実装着手の前提条件を満たした
- **CR-0001 を経た正式承認:** v0.2 化は CR-0001(MODERATE)として CCB プロセスを経て承認(CRR-VIP-001 v0.2 §4 にエントリ登録)
- **`inc1-design-frozen` タグ:** 本 SDD v0.2 マージ後に付与する(タグ命名は SCMP §3.1 準拠)

### 6.4 v0.2 で発見した SRS / RMF 整合性課題(**Step 20 B-1 で解消済、v0.5 で整合化**)

v0.2 詳細化作業中に発見した SRS 文言整合・実装上の判断点 4 件を以下に記録する。**Step 20 B-1(CR-0007 / SRS-VIP-001 v0.2 改訂、PR #50 マージ `8005c05`、2026-05-07)で全件解消済**。

| ID | 発見ユニット | 課題 | 提案対応 | 解消結果(SRS v0.2、CR-0007) |
|----|------------|------|---------|---------------------------|
| ISS-V02-001 | UNIT-001.5(Watchdog SW) | SRS-RCM-003 のタイムアウト値が明示されていない。本 SDD v0.2 では制御周期 100 ms × 3 周期 = 300 ms と確定 | SRS 改訂で「SW Watchdog タイムアウト 300 ms 以下」を明示 | **解消済**:SRS v0.2 §5 SRS-RCM-003 で「300 ms 以下」を時間値で明示 |
| ISS-V02-002 | UNIT-002.1(Pump Simulator) | SRS-P01「±5% 精度」が定常時か過渡時かが不明確。一次遅れ τ=0.5 秒で過渡時は 5% を超え得る | SRS 改訂で「定常時 ±5%、過渡応答は τ=0.5 秒以内」を明示 | **解消済**:SRS v0.2 §4.1.2 SRS-P01 で「過渡応答 τ ≤ 0.5 秒」を明示 |
| ISS-V02-003 | UNIT-001.3(Command Handler) | SRS-P04(stop ≤ 50 ms)は通常キュー方式では未達。本 SDD v0.2 で「STOP/ERROR_RESET ファストパス」を設計上採用 | SRS 改訂で「stop はファストパス必須」を明記、または現状文言を「通常コマンドは 100 ms、stop/error_reset は 50 ms」に分離 | **解消済**:SRS v0.2 §4.1.2 SRS-P04 で「STOP / ERROR_RESET ファストパス 50 ms、通常 100 ms」内訳分離明示 |
| ISS-V02-004 | UNIT-004.2(Resume Gate) | SRS-028「合理的時間内」の数値が未定義。本 SDD v0.2 で 60 分(EXPIRY_SEC=3600)と確定 | SRS 改訂で「再開確認の有効期限 60 分」を明示 | **解消済**:SRS v0.2 §4.1.1 SRS-028 で「60 分以内」明示 + token 失効再シーケンス追記 |

**重要:** 上記 4 件すべて RCM 論理は不変、SDD で実装値を確定したのみ。Step 20 B-1 で CR-0007(MAJOR、SRMP §7.3「RCM 関連部の追記化」相当)として CCB プロセスを経て承認済。

### 6.5 v0.5 骨格化で発見した整合性課題(申し送り、新設、CR-0009 / Step 20 E)

本 v0.5 骨格化作業中に発見した SRS / SAD / RMF 整合性課題を ISS-V03-XXX として記録し、**Step 20 F〜H(UTPR / ITPR / STPR Inc.2 拡張)+ Step 20 X〜(TDD 実装)+ SDD v0.6 候補(Inc.2 新規 8 ユニットの完全詳細化)** で順次反映する。

| ID | 発見ユニット | 課題 | 提案対応 |
|----|------------|------|---------|
| (本 v0.5 時点で発見なし、空欄として枠だけ用意) | — | — | — |

**運用方針:**

- 本セクションは Inc.2 着手中に発生する SRS / SAD / RMF / SDD 整合性課題の集約先(ISS-V02 と同パターン)。
- v0.5 骨格化時点では **新規発見なし**(SAD v0.2 で確定した内容を SDD §4.x プレースホルダに反映する従属的改訂のため、設計判断は SAD 側で完結している)。
- Step 20 F〜H で UTPR / ITPR / STPR を拡張する際、Step 20 X〜で TDD 実装する際、SDD v0.6 候補で詳細化する際に発見される課題を ISS-V03-001 から採番予定。
- ISS-V02 と同様、解消は **新規 CR(SRS / SAD / RMF / SDD 改訂)** で対応する運用。
- **RCM-020 候補(HZ-009 対応のバッテリ管理 / 安全側遷移)の SRS 正式登録は Step 20 B-3 候補として既に申し送り済**(本 §6.5 ではなく CR-0010 / RMF v0.4 の備考として記録、本 §6.5 はあくまで骨格化由来の SDD 中心課題用)。

## 7. トレーサビリティマトリクス

本 SDD v0.2 で全 17 ユニットを §5.4.2 詳細記述に展開した。UT/IT/ST 試験計画は未作成(箇条 5.5〜5.7)、UT ID 列は試験計画作成時に充填する。

| SRS ID | ARCH ID | UNIT ID | 本 SDD での記述 | UT ID(後続で充填) |
|--------|---------|---------|--------------|-------------------|
| SRS-020, SRS-RCM-020, SRS-ALM-003 | ARCH-001.1 | UNIT-001.1 | 詳細(§4.1、v0.1) | — |
| SRS-011, SRS-012, SRS-031, SRS-P02, SRS-RCM-004 | ARCH-001.2 | UNIT-001.2 | 詳細(§4.6、v0.2) | — |
| SRS-010, SRS-013, SRS-014, SRS-P03, SRS-P04 | ARCH-001.3 | UNIT-001.3 | 詳細(§4.7、v0.2) | — |
| SRS-O-001, SRS-RCM-001, SRS-005 | ARCH-001.4 | UNIT-001.4 | 詳細(§4.2、v0.1) | — |
| SRS-RCM-003 | ARCH-001.5 | UNIT-001.5 | 詳細(§4.8、v0.2) | — |
| SRS-030, SRS-031, SRS-P01 | ARCH-002.1 | UNIT-002.1 | 詳細(§4.9、v0.2) | — |
| SRS-031, SRS-I-020 | ARCH-002.2 | UNIT-002.2 | 詳細(§4.10、v0.2) | — |
| SRS-032, SRS-I-040(将来) | ARCH-002.3 | UNIT-002.3 | 詳細(§4.11、v0.2、本版スタブ) | — |
| SRS-RCM-004(HW 側) | ARCH-002.4 | UNIT-002.4 | 詳細(§4.3、v0.1) | — |
| SRS-DATA-001, SRS-DATA-004 | ARCH-003.1 | UNIT-003.1 | 詳細(§4.12、v0.2) | — |
| SRS-SEC-001 | ARCH-003.2 | UNIT-003.2 | 詳細(§4.13、v0.2) | — |
| SRS-DATA-002, SRS-DATA-003 | ARCH-003.3 | UNIT-003.3 | 詳細(§4.4、v0.1) | — |
| SRS-027, SRS-RCM-015 | ARCH-004.1 | UNIT-004.1 | 詳細(§4.5、v0.1) | — |
| SRS-028, SRS-RCM-016 | ARCH-004.2 | UNIT-004.2 | 詳細(§4.14、v0.2) | — |
| SRS-IF-002, SRS-010〜014 | ARCH-005.1 | UNIT-005.1 | 詳細(§4.15、v0.2) | — |
| SRS-IF-003, SRS-O-010, SRS-UX-002 | ARCH-005.2 | UNIT-005.2 | 詳細(§4.16、v0.2) | — |
| SRS-UX-001, SRS-004, SRS-005 | ARCH-005.3 | UNIT-005.3 | 詳細(§4.17、v0.2、分離対象 B) | — |
| SRS-OPS-002, SRS-OPS-003, SRS-OPS-010, SRS-OPS-011 | ARCH-005 | UNIT-005.4 | 詳細(§4.18、v0.4、Step 19 H1 で新規追加)| UT-005.4-01〜15(UTPR §7.3.18 で詳細化)|
| **SRS-044, SRS-ALM-008(Inc.2)** | **ARCH-001.1** | **UNIT-001.1**(Inc.2 拡張)| **詳細(§4.1、Inc.1 v0.1)+ Inc.2 拡張(§4.1.G、v0.5、骨格)** | **TBD(Step 20 F UTPR Inc.2 拡張で詳細化)** |
| **SRS-I-040(確定)、SRS-040〜043(Inc.2)** | **ARCH-002.3** | **UNIT-002.3**(Inc.2 拡張)| **詳細(§4.11、Inc.1 v0.2)+ Inc.2 拡張(§4.11.G、v0.5、骨格、no-op 解除)** | **TBD(Step 20 F)** |
| **SRS-IF-010(Inc.2)、SRS-044(Inc.2)** | **ARCH-005.1** | **UNIT-005.1**(Inc.2 拡張)| **詳細(§4.15、Inc.1 v0.2)+ Inc.2 拡張(§4.15.G、v0.5、骨格、`acknowledge_alarm` / `silence_alarm`)** | **TBD(Step 20 F)** |
| **SRS-040, SRS-RCM-009, SRS-ALM-004(Inc.2)** | **ARCH-006.1** | **UNIT-006.1** | **詳細(§4.19、v0.6、Step 20 X1 で実装 + Step 20 X2 で SDD 詳細化)** | **UT-006.1-01〜18(19 ケース、Step 20 X1 で実装、stmt/branch 100% = MC/DC 100%、UTPR §7.3.19 詳細化は CR-0017 / Step 20 X3)** |
| **SRS-041, SRS-RCM-010, SRS-ALM-005(Inc.2)** | **ARCH-006.2** | **UNIT-006.2** | **詳細(§4.20、v0.7、Step 20 X4 実装 + Step 20 X5 SDD 詳細化、`src/vip_detection/air_bubble.py` 運用中 v0.1)** | **UT-006.2-01〜18 + 04b/04c(22 ケース、Step 20 X4 で実装、stmt/branch 100% = MC/DC 100%、UTPR §7.3.20 詳細化は CR-0020 / Step 20 X6)** |
| **SRS-042, SRS-RCM-006(部分)、SRS-ALM-006(Inc.2)** | **ARCH-006.3** | **UNIT-006.3** | **詳細(§4.21、v0.8、Step 20 X7 実装 + Step 20 X8 SDD 詳細化、`src/vip_detection/reservoir.py` 運用中 v0.1)** | **UT-006.3-01〜14(15 ケース、Step 20 X7 で実装、stmt/branch 100% = MC/DC 100%、UTPR §7.3.21 詳細化は CR-0023 / Step 20 X9)** |
| **SRS-044, SRS-RCM-011(Inc.2)** | **ARCH-006.4** | **UNIT-006.4** | **骨格(§4.22、v0.5)** | **TBD(Step 20 F UT-006.4-01〜)** |
| **SRS-RCM-012, SRS-IF-010(Inc.2)** | **ARCH-006.5** | **UNIT-006.5** | **骨格(§4.23、v0.5)** | **TBD(Step 20 F UT-006.5-01〜)** |
| **SRS-043, SRS-RCM-006(部分)、SRS-ALM-007、HZ-009(Inc.2)** | **ARCH-006.6** | **UNIT-006.6** | **骨格(§4.24、v0.5、HZ-009 対応、RCM-020 候補は SRS 申し送り中)** | **TBD(Step 20 F UT-006.6-01〜)** |
| **SRS-IF-010, SRS-O-040, SRS-ALM-001/004〜008, SRS-RCM-006(Inc.2)** | **ARCH-007.1** | **UNIT-007.1**(クラス B、SEP-003 分離継続) | **骨格(§4.25、v0.5)** | **TBD(Step 20 F UT-007.1-01〜)** |
| **SRS-REG-002, SRS-ALM-004〜008(Inc.2)** | **ARCH-007.2** | **UNIT-007.2**(クラス B、純粋関数) | **骨格(§4.26、v0.5、IEC 60601-1-8 §6.1/§5.1.4)** | **TBD(Step 20 F UT-007.2-01〜)** |

## 8. 改訂履歴

| バージョン | 日付 | 変更内容 | 変更者 |
|----------|------|---------|--------|
| 0.8 | 2026-05-15 | **CR-0022(Issue #80、MODERATE、Step 20 X8 / Inc.2 連動詳細化の SDD 部分 §4.21、UNIT-006.3 完結サイクル(Step 20 X7〜X9)第 2 ステップ)による改訂。** Step 20 X7(CR-0021、PR #79 マージ)で TDD 実装した `src/vip_detection/reservoir.py` v0.1(70 stmt + 10 branch、stmt/branch 100% = MC/DC 100% 目標達成)の内容を SDD §4.21 に詳細化反映。**(A) §4.21 UNIT-006.3: Reservoir Empty Detector を骨格(v0.5)→ 詳細(v0.8)に展開:** §4.21.A 目的 / 責務(単純閾値判定 = 残量 `<=` 閾値で `Empty`、検知時 SRS-ALM-006(MEDIUM/TECHNICAL)発報 + PAUSED 遷移依頼(ERROR ではない = 消耗品枯渇、SAD v0.2 §11.1)、補充復元時 = 再 arm のみで自動 RUNNING 復帰非依頼(IEC 60601-1-8 §6.4 整合)、センサー故障時 = `Failed` で ERROR 遷移依頼のみ safe-side、単一チャネル構成のため `Degraded` なし、閾値方向 `<=` は occlusion/air_bubble の `>=` と逆)、§4.21.B 定数(`RESERVOIR_EMPTY_THRESHOLD = Decimal(20)` 暫定、SDD v0.9 で bench data 正式確定予定、単位は薬液残量センサー出力の暫定無次元スケール)、§4.21.C 依存 protocol(`vip_detection/protocols.py` v0.2 を **再利用のみ** = 検知群ユニットで初の Protocol 改訂を伴わない実装、`SensorKind.RESERVOIR` / `TargetState.PAUSED` は protocols.py v0.1 で先見的に定義済、`WarningLogger` は単段判定のため不使用)、§4.21.D `DetectionResult` 3 種 sealed frozen+slots(`Healthy` / `Empty(triggering_value)` / `Failed`、UNIT-006.1 の 4 種 / UNIT-006.2 の 5 種から単一チャネル構成に応じて 3 種へ簡素化 = `Degraded` なし、検知群ユニットの `DetectionResult` 種別数はチャネル構成 + 段数に応じて変動)、§4.21.E `ReservoirEmptyDetector` クラス DI 駆動 constructor(sensor_reader / alarm_reporter / state_machine / clock / empty_threshold)+ **単一 armed フラグ**(`_armed`、UNIT-006.2 の二系統 armed から単段へ簡素化、`Healthy`(補充復元)/ `Failed`(センサー故障)の双方で再 arm)、§4.21.F 主要 API + 動作仕様(F.1 `_evaluate` 純粋関数 + `healthy` 最優先判定 + 閾値境界 inclusive `<=` + 故障 channel 値無視 / F.2 `_safe_read` SEP-003 例外吸収 / F.3 `_apply` ディスパッチ + Healthy 経由再 arm + 自動 RUNNING 復帰非依頼(`TargetState` enum に RUNNING を持たない構造的保証)/ F.4 `_on_empty` armed 連動冪等性 + 発報 → PAUSED 遷移順序契約 + AlarmEvent 内容(MEDIUM/TECHNICAL/cause_code='reservoir_empty'/metadata.triggering_value)+ Reporter 例外吸収 / F.5 `_on_failed` ERROR 遷移依頼のみ + alarm なし safe-side + reason 区別 + armed 再 arm)、§4.21.G 依存先テーブル(UNIT-002.1 sensor / UNIT-002.3 拡張 / UNIT-007.1 / UNIT-001.1 拡張、Step 20 X7 時点では fake 代替)、§4.21.G.x SDD v0.9 候補で詳細化する項目 5 件(ヒステリシス = チャタリング防止の上下 2 閾値帯 / 並行 tick + atomic 性 / 周期 tick 呼出間隔 / 片系故障内部ロジック詳細 = UNIT-002.3 拡張 / 閾値具体値 bench 整合性 + 物理スケール)、§4.21.H ユニット試験設計参照ガイド(UT-006.3-NN ↔ §4.21.F.x 契約節のマッピング、UTPR §7.3.21 詳細化は CR-0023 / Step 20 X9 で別 PR)。**(B) §3.1 ユニット階層で UNIT-006.3 行を「骨格、RCM-006」→「詳細 v0.8、RCM-006、Step 20 X7 実装 + X8 SDD 詳細化」に更新。**(C) §3.2 ユニット一覧で UNIT-006.3 行の状態を「骨格(§4.21、v0.5、RCM-006、SRS-042、SRS-ALM-006)」→「詳細(§4.21、v0.8、RCM-006、SRS-042、SRS-ALM-006、Step 20 X7 で実装 + Step 20 X8 で SDD 詳細化、`src/vip_detection/reservoir.py` 運用中 v0.1)」に更新。**(D) §7 トレーサビリティマトリクスで SRS-042/SRS-RCM-006/SRS-ALM-006 → UNIT-006.3 行を「骨格(§4.21、v0.5)」→「詳細(§4.21、v0.8、Step 20 X7 実装 + Step 20 X8 SDD 詳細化、`src/vip_detection/reservoir.py` 運用中 v0.1)」+ UT-006.3-01〜14(15 ケース)を充填(stmt/branch 100% = MC/DC 100%、UTPR 詳細化は CR-0023 / Step 20 X9)。**(E) ヘッダ:** v0.7 → v0.8、対象 SW バージョン 0.2.0(Inc.1 全 18 詳細 + Inc.2 UNIT-006.1/006.2/006.3 詳細 + Inc.2 残 5 ユニット骨格 + 既存 3 ユニット拡張節、合計 26 ユニット)、最終更新日 2026-05-15、変更要求に CR-0022 を追加。**MODERATE 区分**(SCMP §4.1):骨格化 → 詳細化への枠組み拡張で実装は不変、SDD 内記述の精度向上のみ、SRS / SAD / RMF / 既存実装に影響しない、Step 20 X2 SDD v0.5 → v0.6(CR-0016 MODERATE)/ Step 20 X5 SDD v0.6 → v0.7(CR-0019 MODERATE)と同区分・同性質。**SRMP §7.3「RCM 関連部の追記化」相当**(RCM-006 実装ユニットの設計記述精度向上、検出能力不変)、**RMF 更新不要**(RMF v0.4 で既に Designed 状態反映済、Verified 化判定は Inc.2 完了時)、**本 CR-0022 は SDD 改訂のみで実装コード / SOUP / 試験への波及なし**(Step 20 X7 PR #79 で実装済 + 後続 Step 20 X9 で UTPR 連動)。**「単一文書 = 単一 CR」運用パターンの 16 度目適用**(CR-0008〜CR-0021 + 本 CR-0022 = SDD のみで分離継続)、**「§4 CLOSED 一気通貫」運用パターンの 16 度目適用**(Step 19 I 発見 → Step 20 B-1 〜本 X8 連続 16 回適用)、**Step 20 X2 / X5 SDD 詳細化テンプレート(11 サブセクション §4.x.A〜H + §4.x.G.x 申し送り)の継承**:UNIT-006.1 §4.19 / UNIT-006.2 §4.20 で確立したテンプレートを §4.21 で再利用、UNIT-006.3 は単一チャネルのため §4.21.F は 5 メソッド(`_on_warning` なし)= §4.19 occlusion 寄りの構成 = 後続 UNIT-006.4〜007.2 + 既存 3 拡張節も同テンプレートで展開予定(残 24 Step)。**詳細化スコープ判断:** 「実装した項目のみ」(Step 20 X8 着手前ユーザ確認で推奨案合意)。具体的には Step 20 X7 で実装した項目(暫定閾値・3 種 DetectionResult・単一 armed・PAUSED 遷移・補充復元再 arm・SEP-003 例外契約)を §4.21.A〜H に展開、未実装項目 5 件(ヒステリシス・並行 tick・周期 tick・片系故障内部ロジック・閾値 bench)は §4.21.G.x に申し送り = SDD v0.9 候補 + UNIT-002.3 拡張 + Control Loop 拡張と並行で詳細化予定。Step 20 X8 軽量化(派生 ~11 箇所):SDD ヘッダ + §3.1 + §3.2 UNIT-006.3 行 + §4.21 詳細化(本 v0.8 最大の改訂)+ §7 トレース UNIT-006.3 行 + §8 改訂履歴 + CRR §4 CR-0022 行 + §6 + §9 改訂履歴 + CIL CI-DOC-SDD v0.7 → v0.8 + §11 改訂履歴 + DEVSTEPS Step 20 X8 セクション + 改訂履歴 + 次ステップ計画 + GitHub Issue 起票 = 計約 11 箇所(Step 20 X2 / X5 と同等の軽量規模)| k-abe |
| 0.7 | 2026-05-13 | **CR-0019(Issue #74、MODERATE、Step 20 X5 / Inc.2 連動詳細化の SDD 部分 §4.20、UNIT-006.2 完結サイクル(Step 20 X4〜X6)第 2 ステップ)による改訂。** Step 20 X4(CR-0018、PR #73 マージ `943230a`)で TDD 実装した `src/vip_detection/air_bubble.py` v0.1 + `src/vip_detection/protocols.py` v0.2(`WarningLogger` Protocol 追加)の内容を SDD §4.20 に詳細化反映。**(A) §4.20 UNIT-006.2: Air-Bubble Detector を骨格(v0.5)→ 詳細(v0.7)に展開:** §4.20.A 目的 / 責務(多段判定 = critical > warning 段間優先、警告 = WarningLogger 経由監視ログのみ、両系故障 = `Failed` 独立型で alarm なし + ERROR 遷移依頼のみ、片系故障 = `Degraded(failed_channel)` で監視継続、段独立性 = ノイズの多い警告センサーが危険判定をマスク / 偽造しない契約)、§4.20.B 定数(`AIR_BUBBLE_WARN_THRESHOLD = Decimal(50)` + `AIR_BUBBLE_CRITICAL_THRESHOLD = Decimal(150)` 暫定、SDD v0.8 で bench data 正式確定予定、CRITICAL > WARN の順序は構造的に保証、単位は気泡体積センサー出力の暫定無次元スケール)、§4.20.C 依存 protocol(`vip_detection/protocols.py` v0.2、UNIT-006.1 で確立した SensorReader/AlarmReporter/StateTransitionRequester に加え本 X4 で **WarningLogger Protocol を新規追加**(`log_warning(detector_id, *, threshold_value, observed_value, occurred_at) -> None`、SEP-003 例外伝播禁止契約、後続 UNIT-006.3〜006.6 + Inc.4 UI 通知コンポーネントで再利用予定))、§4.20.D `DetectionResult` 5 種 sealed frozen+slots(`Healthy` / `Warning(triggering_value)` / `Detected(triggering_value)` / `Degraded(failed_channel)` / `Failed`、UNIT-006.1 の 4 種 + Warning 拡張の根拠 = UTPR §7.3.20 8 観点を表現可能 + UT-006.2-04b/04c で triggering_value 内容を契約検証可能 + Inc.4 UI 表示分岐(yellow vs red)に直接対応)、§4.20.E `AirBubbleDetector` クラス DI 駆動 constructor(sensor_reader / alarm_reporter / warning_logger / state_machine / clock / warn_threshold / critical_threshold)+ **二系統 armed フラグ**(`_alarm_armed` + `_warning_armed`、Warning → Detected 段間遷移時に alarm を発火可能にするため独立管理)、§4.20.F 主要 API + 動作仕様(F.1 `_evaluate` 純粋関数 + decision tree + 段間優先 critical > warning + 段独立性 + 故障 channel 値無視 + 閾値境界 inclusive >= / F.2 `_safe_read` SEP-003 例外吸収 / F.3 `_apply` ディスパッチ + Healthy/Degraded 両 armed 再 arm / F.4 `_on_detected` alarm_armed 連動冪等性 + 発報 → 遷移順序契約 + alarm/warning 両 armed クリア + Reporter 例外吸収 + metadata.triggering_value / F.5 `_on_warning` warning_armed 連動冪等性 + Logger 例外吸収 + alarm_armed 維持(段間遷移可能) / F.6 `_on_failed` ERROR 遷移依頼のみ + alarm/warning なし safe-side + reason 区別 + 両 armed 再 arm)、§4.20.G 依存先テーブル(UNIT-002.1 sensor / UNIT-002.3 拡張 / UNIT-007.1 / UNIT-001.1 拡張 / Inc.4 UI WarningLogger 実装、Step 20 X4 時点では fake 代替)、§4.20.G.x SDD v0.8 候補で詳細化する項目 6 件(警告状態保持時間 / 並行 tick + atomic 性 / 周期 tick 呼出間隔 / 片系故障内部ロジック詳細 = UNIT-002.3 拡張 / 閾値具体値 bench 整合性 + 物理スケール / critical 故障時の safe-side 評価)、§4.20.H ユニット試験設計参照ガイド(UT-006.2-NN ↔ §4.20.F.x 契約節のマッピング、UTPR §7.3.20 詳細化は CR-0020 / Step 20 X6 で別 PR)。**(B) §3.2 ユニット一覧で UNIT-006.2 行の状態を「骨格(§4.20、v0.5、RCM-010、SRS-041、SRS-ALM-005)」→「詳細(§4.20、v0.7、RCM-010、SRS-041、SRS-ALM-005、Step 20 X4 で実装 + Step 20 X5 で SDD 詳細化、`src/vip_detection/air_bubble.py` 運用中 v0.1)」に更新。**(C) §3.1 ユニット階層で UNIT-006.2 行を「骨格、RCM-010」→「詳細 v0.7、RCM-010、Step 20 X4 実装 + X5 SDD 詳細化」に更新。**(D) §7 トレーサビリティマトリクスで SRS-041/RCM-010/SRS-ALM-005 → UNIT-006.2 行を「骨格(§4.20、v0.5)」→「詳細(§4.20、v0.7、Step 20 X4 実装 + Step 20 X5 SDD 詳細化、`src/vip_detection/air_bubble.py` 運用中 v0.1)」+ UT-006.2-01〜18 + 04b/04c(22 ケース)を充填(stmt/branch 100% = MC/DC 100%、UTPR 詳細化は CR-0020 / Step 20 X6)。**(E) ヘッダ:** v0.6 → v0.7、対象 SW バージョン 0.2.0(Inc.1 全 18 詳細 + Inc.2 UNIT-006.1/006.2 詳細 + Inc.2 残 6 ユニット骨格 + 既存 3 ユニット拡張節、合計 26 ユニット)、最終更新日 2026-05-13、変更要求に CR-0019 を追加。**MODERATE 区分**(SCMP §4.1):骨格化 → 詳細化への枠組み拡張で実装は不変、SDD 内記述の精度向上のみ、SRS / SAD / RMF / 既存実装に影響しない、Step 20 X2 SDD v0.5 → v0.6(CR-0016 MODERATE)と同区分・同性質。**SRMP §7.3「RCM 関連部の追記化」相当**(RCM-010 実装ユニットの設計記述精度向上、検出能力不変)、**RMF 更新不要**(RMF v0.4 で既に Designed 状態反映済、Verified 化判定は Inc.2 完了時)、**本 CR-0019 は SDD 改訂のみで実装コード / SOUP / 試験への波及なし**(Step 20 X4 PR #73 で実装済 + 後続 Step 20 X6 で UTPR 連動)。**「単一文書 = 単一 CR」運用パターンの 13 度目適用**(CR-0008〜CR-0018 + 本 CR-0019 = SDD のみで分離継続)、**「§4 CLOSED 一気通貫」運用パターンの 13 度目適用**(Step 19 I 発見 → Step 20 B-1 〜本 X5 連続 13 回適用)、**Step 20 X2 SDD §4.19 詳細化テンプレート(11 サブセクション §4.x.A〜H + §4.x.G.x 申し送り)の継承**:UNIT-006.1 で確立したテンプレートを §4.20 で再利用 = 後続 UNIT-006.3〜007.2 + 既存 3 拡張節も同テンプレートで展開予定(残 27 Step)。**詳細化スコープ判断:** 「実装した項目のみ」(Step 20 X5 着手前ユーザ確認で推奨案合意)。具体的には Step 20 X4 で実装した 6 項目(暫定閾値 WARN/CRITICAL ペア・5 種 DetectionResult・二系統 armed フラグ・WarningLogger Protocol DI・段間優先 critical > warning・段独立性 + SEP-003 例外契約)を §4.20.A〜H に展開、未確定 6 項目(警告状態保持時間・並行 tick・周期 tick・片系故障内部ロジック・閾値 bench・critical 故障 safe-side 評価)は §4.20.G.x に申し送り = SDD v0.8 候補 + UNIT-002.3 拡張 + Control Loop 拡張と並行で詳細化予定。Step 20 X5 軽量化(派生 ~11 箇所):SDD ヘッダ + §3.1 + §3.2 UNIT-006.2 行 + §4.20 詳細化(本 v0.7 最大の改訂)+ §7 トレース UNIT-006.2 行 + §8 改訂履歴 + CRR §4 CR-0019 行 + §6 + §9 改訂履歴 + CIL CI-DOC-SDD v0.6 → v0.7 + §11 改訂履歴 + DEVSTEPS Step 20 X5 セクション + 改訂履歴 + 次ステップ計画 + GitHub Issue 起票 = 計約 11 箇所(Step 20 X2 と同等の軽量規模)| k-abe |
| 0.6 | 2026-05-13 | **CR-0016(MODERATE、Step 20 X2 / Inc.2 連動詳細化の SDD 部分 §4.19)による改訂。** Step 20 X1(CR-0015、PR #67 マージ `551f862`)で TDD 実装した `src/vip_detection/occlusion.py` v0.1 + `src/vip_detection/protocols.py` v0.1 の内容を SDD §4.19 に詳細化反映。**(A) §4.19 UNIT-006.1: Occlusion Detector を骨格(v0.5)→ 詳細(v0.6)に展開:** §4.19.A 目的 / 責務(両系故障時の挙動を `Failed` 独立型で明示、alarm なし + ERROR 遷移依頼のみ)、§4.19.B 定数(`OCCLUSION_PRESSURE_THRESHOLD_KPA = Decimal(90)` kPa = 暫定値、SDD v0.7 で正式確定)、§4.19.C 依存 protocol(`vip_detection/protocols.py` に集中配置、`SensorKind` 6 channels + `SensorReading` frozen+slots + `SensorReader` Protocol + `AlarmPriority` / `AlarmCategory` Enum + `AlarmEvent` frozen+slots + `MappingProxyType` + `AlarmReporter` Protocol + `TargetState` Enum + `StateTransitionRequester` Protocol、すべて `@runtime_checkable`)、§4.19.D `DetectionResult` 4 種 sealed frozen+slots(`Healthy` / `Detected(triggering_channels)` / `Degraded(failed_channel)` / `Failed`、v0.5 骨格 3 種からの拡張理由 = UT-006.1-10/11 観点明示)、§4.19.E `OcclusionDetector` クラス DI 駆動 constructor(sensor_reader / alarm_reporter / state_machine / clock / threshold_kpa)、§4.19.F 主要 API + 動作仕様(`tick` / `_evaluate` 純粋関数 + 契約 / `_safe_read` SEP-003 例外吸収 + 契約 / `_apply` ディスパッチ + 契約 / `_on_detected` armed 連動冪等性 + 発報 → 遷移依頼順序契約 + 契約 / `_on_failed` ERROR 遷移依頼のみ + 再 arm + 契約)、§4.19.G 依存先テーブル(UNIT-002.1 sensor / UNIT-002.3 拡張 / UNIT-007.1 / UNIT-001.1 拡張、Step 20 X1 時点では fake 代替)、§4.19.G.x SDD v0.7 候補で詳細化する項目(周期 tick / 並行性 / 片系故障検出ロジック詳細 / 検知後 self-test / 閾値具体値の bench 整合)、§4.19.H ユニット試験設計参照ガイド(UT-006.1-NN ↔ §4.19.F.x 契約節のマッピング、UTPR §7.3.19 詳細化は CR-0017 / Step 20 X3 で別 PR)。**(B) §3.2 ユニット一覧で UNIT-006.1 行の状態を「骨格(§4.19、v0.5、...)」→「詳細(§4.19、v0.6、RCM-009、SRS-040、SRS-ALM-004、Step 20 X1 で実装 + Step 20 X2 で SDD 詳細化)」に更新。**(C) §7 トレーサビリティマトリクスで SRS-040/RCM-009/SRS-ALM-004 → UNIT-006.1 行を「骨格(§4.19、v0.5)」→「詳細(§4.19、v0.6)」+ UT-006.1-01〜18 を充填(stmt/branch 100% = MC/DC 100%、UTPR 詳細化は CR-0017 / Step 20 X3)。**(D) ヘッダ:** v0.5 → v0.6、対象 SW バージョン 0.2.0(Inc.1 全 18 詳細 + Inc.2 UNIT-006.1 詳細 + Inc.2 残 7 ユニット骨格 + 既存 3 ユニット拡張節、合計 26 ユニット)、最終更新日 2026-05-13、変更要求に CR-0016 を追加。**MODERATE 区分**(SCMP §4.1):骨格化 → 詳細化への枠組み拡張で実装は不変、SDD 内記述の精度向上のみ、SRS / SAD / RMF / 既存実装に影響しない。**SRMP §7.3「RCM 関連部の追記化」相当**(RCM-009 実装ユニットの設計記述精度向上、検出能力不変)、**RMF 更新不要**(RMF v0.4 で既に Designed 状態反映済、Verified 化判定は Inc.2 完了時)、**本 CR-0016 は SDD 改訂のみで実装コード / SOUP / 試験への波及なし**(Step 20 X1 PR #67 で実装済 + 後続 Step 20 X3 で UTPR 連動)。**「単一文書 = 単一 CR」運用パターンの 10 度目適用**(CR-0008/0010/0011/0009/0012/0013/0014/0015 + 本 CR-0016 = SDD のみで分離)、**「§4 CLOSED 一気通貫」運用パターンの 10 度目適用**(Step 19 I 発見 → Step 20 B-1 〜本 X2 連続 10 回適用)、**Step 14 v0.1 流儀 / Step 19 B 系列流儀 / Inc.2 着手準備流儀の合流**:「v0.x 骨格化 → 後続改訂で詳細化」パターンを Inc.2 でも実証 = v0.5 骨格 → v0.6 §4.19 詳細化で第 1 ユニット完了、後続 UNIT-006.2〜007.2 + 既存 3 拡張節は v0.7+ で順次詳細化予定。**詳細化スコープ判断:** 「実装した項目のみ」(Step 20 X1 着手前ユーザ確認で推奨案合意)。具体的には Step 20 X1 で実装した 5 項目(閾値暫定値・API シグネチャ・依存 protocol・DetectionResult 型・armed 連動冪等性 + SEP-003 例外契約)を §4.19.A〜H に展開、未確定 4 項目(周期 tick 呼出間隔・並行性 / 排他制御・片系故障検出ロジック詳細・検知後 self-test 動作)は §4.19.G.x に申し送り = SDD v0.7 候補 + 連動 detector 実装(UNIT-006.2〜)と並行で詳細化予定。Step 20 X2 軽量化(派生 7 箇所程度):SDD ヘッダ + §3.2 UNIT-006.1 行 + §4.19 詳細化(本 v0.6 最大の改訂)+ §7 トレース UNIT-006.1 行 + §8 改訂履歴 + CRR §4 CR-0016 行 + §9 改訂履歴 + CIL CI-DOC-SDD v0.5 → v0.6 + §11 改訂履歴 + DEVSTEPS Step 20 X2 セクション + 改訂履歴 + 次ステップ計画 + GitHub Issue 起票 = 計約 10 箇所(Step 20 X1 と同等の軽量規模)| k-abe |
| 0.5 | 2026-05-10 | **CR-0009(Issue #57、MODERATE、Step 20 E / Inc.2 連動改訂の SDD 部分、骨格化)による改訂。** SAD-VIP-001 v0.2(CR-0011 / Step 20 D、PR #56 マージ `c06425a`)で確定した Inc.2 範囲のアーキテクチャ要素を、Step 14 v0.1 流儀(代表 5 ユニット詳細 + 骨格 N ユニット)を継承して **SDD §4.x 骨格記述** として反映。**(A) §3.1 ユニット階層拡張:** ARCH-006 Detection 検知群 + ARCH-007 Alarm Reporter + ARCH-009 Logging Stub(旧 ARCH-006、SAD v0.2 リネーム)+ ARCH-010(Inc.4 UI 用予約)を追加。**(B) §3.2 ユニット一覧拡張:** Inc.2 新規 8 ユニット行追加(状態 = 「骨格(§4.x、v0.5)」)+ 既存 UNIT-001.1 / UNIT-002.3 / UNIT-005.1 行に「Inc.2 拡張(§4.x.G、v0.5)」状態追記、合計 26 ユニット。**(C) §4.19〜§4.26 Inc.2 新規 8 ユニットの §5.4.2 骨格記述:** UNIT-006.1 Occlusion Detector(RCM-009、SRS-040、SRS-ALM-004)/ UNIT-006.2 Air-Bubble Detector(RCM-010、SRS-041、SRS-ALM-005)/ UNIT-006.3 Reservoir Empty Detector(RCM-006、SRS-042、SRS-ALM-006)/ UNIT-006.4 Alarm Task Watchdog(RCM-011、SRS-044)/ UNIT-006.5 Alarm Path Redundancy(RCM-012、SRS-IF-010)/ UNIT-006.6 Battery Low Detector(RCM-006、SRS-043、SRS-ALM-007、HZ-009)/ UNIT-007.1 Alarm Reporter Core(クラス B、SEP-003 継続、SRS-IF-010、SRS-O-040、SRS-ALM-001/004〜008)/ UNIT-007.2 Alarm Priority Classifier(クラス B、純粋関数、IEC 60601-1-8 §6.1/§5.1.4、SRS-REG-002)。各骨格で目的 / 責務・関連 SRS / RCM・安全クラス・新規パッケージ予定・主要 API 候補表・依存・SDD v0.6 候補で詳細化する項目を記述(Step 14 v0.1 流儀のテンプレート継承)。**(D) §4.1.G / §4.11.G / §4.15.G 既存 3 ユニット拡張サブセクション追補:** UNIT-001.1 State Machine(アラーム発報経路 + ACK / SILENCE 状態遷移、SRS-044 / SRS-ALM-008 / IEC 60601-1-8 §6.4)/ UNIT-002.3 Event Injection(BATTERY_LOW enum 追加 + Pump 伝播経路、SDD v0.2 §4.11.C で予告済の Inc.2 hooks 部分の正式確定、no-op 解除方針確定)/ UNIT-005.1 Control API(`acknowledge_alarm` / `silence_alarm`、IEC 60601-1-8 §6.4 準拠)。**(E) §5.1 ユニット間 I/F 詳細化:** **IF-U-007 詳細化**(`report_alarm(event: AlarmEvent) -> None` の Python 実装契約を §5.1.A で確定 = `dataclass(frozen=True, slots=True)` + `metadata` の `MappingProxyType` ラップ + バリデーション規則 + 例外契約 = 例外伝播禁止 = SEP-003 違反検知の根拠)、**IF-U-012〜015 新規追加**(検知群 → Alarm Reporter / 検知群 → State Machine / Control API → Alarm Reporter ACK・Silence / Pump → 検知群冗長 2 系統センサー入力)、IF-U-008 を「ARCH-009 Logging Stub」(旧 ARCH-006)に整合化。**(F) §6.4 ISS-V02 解消済整合化:** ISS-V02-001〜004 は Step 20 B-1(CR-0007 / SRS v0.2、PR #50 `8005c05`)で全件解消済を本 v0.5 で正式記録(各 ID の解消結果列を追加)。**(G) §6.5(新規)v0.5 骨格化で発見した整合性課題(申し送り):** ISS-V03-XXX 集約欄を新設、本 v0.5 時点では新規発見なし(SAD v0.2 で確定した内容を反映する従属的改訂のため設計判断は SAD 側で完結)、Step 20 F〜H + Step 20 X〜で発見される課題の集約先として枠を用意。**(H) §7 トレーサビリティマトリクス追補:** Inc.2 新規 8 ユニット行 + 既存 3 ユニット拡張行を追加(SRS-040〜044 / SRS-ALM-004〜008 / SRS-RCM-006/009/010/011/012 / SRS-IF-010 / SRS-O-040 / SRS-I-040 / SRS-REG-002 → ARCH-006/007 各 UNIT への割付け、UT/IT/ST 列は Step 20 F〜H で充填予定の TBD)。**(I) ヘッダ:** v0.4 → v0.5、対象 SW バージョン 0.2.0(Inc.2 範囲新規 8 ユニット骨格 + 既存 3 ユニット拡張節、合計 26 ユニット)、最終更新日 2026-05-10。**MODERATE 区分**(SCMP §4.1):骨格化 = 詳細設計の枠組み追加で、論理 / 安全機能 / 既存実装に影響しない、SAD v0.2 で確定した設計を SDD §4.x プレースホルダに反映する従属的改訂。**SRMP §7.3「RCM 関連部の追記化」相当**(新規 5 RCM の詳細設計枠組み追加)、**RMF 更新不要**(RMF v0.4 で既に Designed 状態反映済 = SDD は RMF と整合する形で詳細設計枠組みを記述するのみ)、**本 CR-0009 は SDD 改訂のみで実装コード / SOUP / 試験への波及なし**(後続 Step 20 F〜Z で連動)。**「単一文書 = 単一 CR」運用パターンの 5 度目適用**(CR-0008 = SRS / CR-0010 = RMF / CR-0011 = SAD / CR-0009 = SDD で分離継続)、**「§4 CLOSED 一気通貫」運用パターンの 5 度目適用**(Step 19 I 発見 → Step 20 B-1 / B-2 / C / D / 本 E で連続 5 回適用 = default 運用ルールとして完全確立)、**Step 14 v0.1 流儀の継承**(代表 N ユニット詳細 + 骨格 N ユニットの分離記述パターンを Inc.2 でも再利用、SDD v0.6 候補で詳細化展開する道筋を確保)| k-abe |
| 0.1 | 2026-04-18 | 初版作成(Inc.1 範囲):代表 5 ユニット(State Machine / Flow Command Validator / HW-side Failsafe Timer / Atomic File Writer / Integrity Validator)を §5.4.2 テンプレートに従って詳細記述、残 9 ユニットを骨格記述(責務・主要 API・依存・SDD v0.2 詳細化項目)、§5.4.3 I/F 詳細 13 件、§5.4.4 検証観点チェックリスト・レビュー記録。SDD v0.2 は CR 起票で追補予定、`inc1-design-frozen` タグは v0.2 完成後に付与 | k-abe |
| 0.2 | 2026-04-19 | **CR-0001(Issue #1、MODERATE)による改訂。** v0.1 で骨格記述に留めていた 12 ユニットを §5.4.2 詳細記述に展開:UNIT-001.2 Control Loop(§4.6)/ UNIT-001.3 Command Handler(§4.7)/ UNIT-001.5 Watchdog SW(§4.8)/ UNIT-002.1 Pump Simulator(§4.9)/ UNIT-002.2 Pump Observer(§4.10)/ UNIT-002.3 Event Injection Stub(§4.11)/ UNIT-003.1 Serializer(§4.12)/ UNIT-003.2 Checksum Verifier(§4.13)/ UNIT-004.2 Resume Confirmation Gate(§4.14)/ UNIT-005.1 Control API(§4.15)/ UNIT-005.2 State Observer API(§4.16)/ UNIT-005.3 Validation API(§4.17、分離対象 B)。§3.2 ユニット一覧を全 17 ユニット詳細状態に更新。§6.2 レビュー記録に v0.2 行追加。§6.3 を「骨格記述の解消(v0.2 で完了)」に書き換え、実装ブロックの解除を宣言。§6.4「v0.2 で発見した SRS / RMF 整合性課題」を新規追加(ISS-V02-001〜004 を後続 SRS 改訂 CR の対象として申し送り)。§7 トレーサビリティの「本 SDD での記述」列を全行「詳細(§x.y、vN)」形式に更新。RCM 論理不変、SOUP 追加なし、外部 I/F 変更なし(SRMP §7.3「RCM 非関連部の変更」相当) | k-abe |
| 0.4 | 2026-05-07 | **Step 19 H1(UNIT-005.4 CLI Entry Point 新規追加 = ISS-H-001 解消)による改訂。** F 系列(F1〜F7)+ Step 19 G STPR 骨格化完了後、Step 19 H1(STPR §6.2 ST-OPS の前提となる CLI エントリポイント実装)着手前のクロスレビューで **ISS-H-001 を発見**:SRS-OPS-002(必須)で `vip-ctrl` CLI が要求されているが、Inc.1 全 17 ユニット(SDD v0.3 §3.2)に CLI ユニットが存在しない計画文書間乖離。本 v0.4 で UNIT-005.4 CLI として §3.2 ユニット一覧に追加(全 17 → 18 ユニット)、§4.18 を新規詳細記述(目的・公開 API・データ構造・アルゴリズム・並行性・例外契約・検証方法、`--version` / `--diagnose` / デフォルトの 3 経路 + argparse + JSON Lines 出力 + Integrity Validator 連携)、§7 トレースに UNIT-005.4 行(SRS-OPS-002/003/010/011 + ARCH-005 + UT-005.4-01〜15)を追加。**Inc.1 範囲では対話 start/stop コマンド経路は未提供**(SDD §3 設計方針 + B17 申し送り = 対話 UI は Inc.4 で正式実装)。RCM 非関連 + 外部 API 変更なし + SAD §6 階層防御 / §9 SEP-001 設計不変、F1〜F7 で確立した「計画文書間整合化 → 同 PR 訂正」パターン継続。MINOR 区分・CR 不要(SCMP §4.1「軽微」、SRS / RMF / SAD 本体は不変、CIL の CI-DOC-SDD 行 + UTPR §7.3.18 + CIL §3 CI-SRC-001 + CIL §8 CI-TD 系を同 PR で整合化)| k-abe |
| 0.3 | 2026-05-01 | **CR-0004(Issue #32、MODERATE、修正候補 (b) Adapter 層追加)+ CR-0005(Issue #36、MODERATE、修正候補 (a) Protocol 引数なし化)による Step 19 F1.6 一括改訂。** §4.6.C `_tick` 擬似コードの heartbeat 呼出を `self._sw_watchdog.heartbeat(now)` → `self._sw_watchdog.heartbeat()`(同 hw)に修正(CR-0005 (a)、各 Watchdog 実装が内部 clock で timestamp を取得する設計に整合)。§4.15.B `_validation_api` 行を更新し、実体が `vip_api._validation_bridge.ClassBValidationApiAdapter`(`vip_api_b.validate_settings` の `Ok` / `Err` を `list[ValidationError]` に変換する Adapter)経由で SEP-001 越え経路が成立することを明記(CR-0004 (b))。RCM-001 / RCM-003 / RCM-004 検出能力不変、SAD §6 階層防御設計 + §9 SEP-001 分離設計不変、SOUP 追加なし、外部 I/F 変更なし(SRMP §7.3「RCM 非関連部の変更」相当)| k-abe |
