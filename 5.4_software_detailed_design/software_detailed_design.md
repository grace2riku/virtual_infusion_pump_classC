# ソフトウェア詳細設計書(SDD)

**ドキュメント ID:** SDD-VIP-001
**バージョン:** 0.2
**作成日:** 2026-04-18(v0.1)/ 2026-04-19(v0.2)
**対象製品:** 仮想輸液ポンプ(Virtual Infusion Pump) / VIP-SIM-001
**対象ソフトウェアバージョン:** 0.2.0(Inc.1 範囲、全 17 ユニット詳細記述)
**安全クラス:** C(IEC 62304)
**変更要求:** CR-0001(Issue #1、MODERATE)

| 役割 | 氏名 | 所属 | 日付 | 署名 |
|------|------|------|------|------|
| 作成者 | k-abe | — | 2026-04-19 | |
| レビュー者 | — | — | — | |
| 承認者 | — | — | — | |

> **本プロジェクトの位置づけ(注記)**
> 本ドキュメントは IEC 62304 に基づく医療機器ソフトウェア開発プロセスの学習・参考実装を目的とした **仮想プロジェクト** の成果物である。
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
| [2] | ソフトウェア要求仕様書(SRS-VIP-001) | 0.1 |
| [3] | ソフトウェアアーキテクチャ設計書(SAD-VIP-001) | 0.1 |
| [4] | リスクマネジメントファイル(RMF-VIP-001) | 0.2 |
| [5] | ソフトウェア開発計画書(SDP-VIP-001)§14 共通欠陥 | 0.1 |

## 3. ソフトウェア項目のソフトウェアユニットへの改良(箇条 5.4.1)

### 3.1 ユニット階層(Inc.1 範囲)

```
ARCH-001 Control Core (C)
├── UNIT-001.1  State Machine
├── UNIT-001.2  Control Loop
├── UNIT-001.3  Command Handler
├── UNIT-001.4  Flow Command Validator
└── UNIT-001.5  Watchdog (SW side)

ARCH-002 Virtual Hardware (C)
├── UNIT-002.1  Pump Simulator
├── UNIT-002.2  Pump Observer
├── UNIT-002.3  Event Injection Stub
└── UNIT-002.4  HW-side Failsafe Timer

ARCH-003 Persistence (C)
├── UNIT-003.1  Serializer
├── UNIT-003.2  Checksum Verifier
└── UNIT-003.3  Atomic File Writer

ARCH-004 Boot / Recovery (C)
├── UNIT-004.1  Integrity Validator
└── UNIT-004.2  Resume Confirmation Gate

ARCH-005 Public API Facade
├── UNIT-005.1  Control API               (C、本 SDD では骨格のみ)
├── UNIT-005.2  State Observer API        (C、薄いラッパー、SDD v0.2 で詳細化)
└── UNIT-005.3  Validation API            (B、分離対象、SDD v0.2 で詳細化)

ARCH-006 Logging Stub I/F(抽象 I/F のみ、本版実装なし)
ARCH-007 Alarm Reporter Stub I/F(抽象 I/F のみ、本版実装なし)
```

### 3.2 ユニット一覧

| ユニット ID | 名称 | 所属項目 | 安全クラス | 本 SDD v0.2 での扱い |
|-----------|------|---------|----------|-------------------|
| UNIT-001.1 | State Machine | ARCH-001 | C | 詳細(§4.1、v0.1) |
| UNIT-001.2 | Control Loop | ARCH-001 | C | **詳細(§4.6、v0.2)** |
| UNIT-001.3 | Command Handler | ARCH-001 | C | **詳細(§4.7、v0.2)** |
| UNIT-001.4 | Flow Command Validator | ARCH-001 | C | 詳細(§4.2、v0.1) |
| UNIT-001.5 | Watchdog (SW) | ARCH-001 | C | **詳細(§4.8、v0.2)** |
| UNIT-002.1 | Pump Simulator | ARCH-002 | C | **詳細(§4.9、v0.2)** |
| UNIT-002.2 | Pump Observer | ARCH-002 | C | **詳細(§4.10、v0.2)** |
| UNIT-002.3 | Event Injection Stub | ARCH-002 | C(本版スタブ) | **詳細(§4.11、v0.2)** |
| UNIT-002.4 | HW-side Failsafe Timer | ARCH-002 | C | 詳細(§4.3、v0.1) |
| UNIT-003.1 | Serializer | ARCH-003 | C | **詳細(§4.12、v0.2)** |
| UNIT-003.2 | Checksum Verifier | ARCH-003 | C | **詳細(§4.13、v0.2)** |
| UNIT-003.3 | Atomic File Writer | ARCH-003 | C | 詳細(§4.4、v0.1) |
| UNIT-004.1 | Integrity Validator | ARCH-004 | C | 詳細(§4.5、v0.1) |
| UNIT-004.2 | Resume Confirmation Gate | ARCH-004 | C | **詳細(§4.14、v0.2)** |
| UNIT-005.1 | Control API | ARCH-005 | C | **詳細(§4.15、v0.2)** |
| UNIT-005.2 | State Observer API | ARCH-005 | C | **詳細(§4.16、v0.2)** |
| UNIT-005.3 | Validation API | ARCH-005 | B(分離対象) | **詳細(§4.17、v0.2)** |

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
    self._sw_watchdog.heartbeat(now)
    self._hw_watchdog.heartbeat(now)
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
| `_validation_api` | ValidationApi | 注入(UNIT-005.3、分離 B) |

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

## 5. インタフェースの詳細設計(箇条 5.4.3 ― クラス C)

### 5.1 ユニット間インタフェース(Inc.1 範囲、SAD §5 の U 系 11 件の詳細化)

| IF ID | 呼出側 | 被呼出側 | シグネチャ(Python 型ヒント) | 同期 | エラー返却 |
|-------|-------|---------|-------------------------|------|----------|
| IF-U-001 | UNIT-005.1 | UNIT-001.3 | `enqueue(cmd: Command) -> AcceptResult` | 同期 | 戻り値 `AcceptResult` (`Accepted(token)` / `Rejected(reason)`) |
| IF-U-002 | UNIT-001.2 | UNIT-002.1 | `set_flow_rate(value: Decimal) -> None`(内部で UNIT-001.4 Validator 経由) | 同期 | Validator が失敗時 State Machine に ERROR イベント送信、本 I/F は戻り値なし |
| IF-U-003 | UNIT-001.2 / UNIT-005.2 | UNIT-002.2 | `observe() -> PumpSnapshot` | 同期、idempotent | 例外なし(スナップショットは常に取得可能) |
| IF-U-004 | UNIT-001.1 | ARCH-003 経由で UNIT-003.1/3.3 | `save_async(record: PersistedRecord) -> None`(キュー投入のみ) | 非同期、FIFO | キュー満杯: `queue.Full` を内部捕捉 → WDT 経由 ERROR |
| IF-U-005 | UNIT-004.1 | UNIT-003.1、UNIT-003.3 | `load() -> LoadResult` | 同期(起動時のみ) | `Ok(RawPersistedRecord)` / `Err(LoadError)` |
| IF-U-006 | UNIT-004 全般 | UNIT-001.1 | `set_initial(state: State, needs_confirm: bool) -> None` | 同期 | 事前条件違反で `InvalidInitializationError` |
| IF-U-007 | UNIT-001.1 | ARCH-007 Alarm Reporter Stub | `report_alarm(event: AlarmEvent) -> None`(本版 no-op、一方向) | 同期 | 実装側例外は呼出側で握りつぶしログ(分離境界) |
| IF-U-008 | 全コア UNIT | ARCH-006 Logging Stub | `log(record: LogRecord) -> None`(本版 no-op、一方向) | 同期 | 同上 |
| IF-U-009 | UNIT-001.5 | UNIT-001.1 | `request_transition(Event(WDT_TIMEOUT))` | 同期 | State Machine の戻り値 |
| IF-U-010 | UNIT-001.2 | UNIT-001.5 | `heartbeat(ts: Monotonic) -> None` | 同期 | 失敗なし |
| IF-U-011 | UNIT-001.2 | UNIT-002.4 | `heartbeat(ts: Monotonic) -> None` | 同期 | 失敗なし |

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

### 6.4 v0.2 で発見した SRS / RMF 整合性課題(申し送り)

v0.2 詳細化作業中に、以下の SRS 文言整合・実装上の判断点を発見した。**本 CR-0001 範囲外の対応**として、後続の SRS 改訂時(Inc.2 開始前を想定)にまとめて反映する。

| ID | 発見ユニット | 課題 | 提案対応 |
|----|------------|------|---------|
| ISS-V02-001 | UNIT-001.5(Watchdog SW) | SRS-RCM-003 のタイムアウト値が明示されていない。本 SDD v0.2 では制御周期 100 ms × 3 周期 = 300 ms と確定 | SRS 改訂で「SW Watchdog タイムアウト 300 ms 以下」を明示 |
| ISS-V02-002 | UNIT-002.1(Pump Simulator) | SRS-P01「±5% 精度」が定常時か過渡時かが不明確。一次遅れ τ=0.5 秒で過渡時は 5% を超え得る | SRS 改訂で「定常時 ±5%、過渡応答は τ=0.5 秒以内」を明示 |
| ISS-V02-003 | UNIT-001.3(Command Handler) | SRS-P04(stop ≤ 50 ms)は通常キュー方式では未達。本 SDD v0.2 で「STOP/ERROR_RESET ファストパス」を設計上採用 | SRS 改訂で「stop はファストパス必須」を明記、または現状文言を「通常コマンドは 100 ms、stop/error_reset は 50 ms」に分離 |
| ISS-V02-004 | UNIT-004.2(Resume Gate) | SRS-028「合理的時間内」の数値が未定義。本 SDD v0.2 で 60 分(EXPIRY_SEC=3600)と確定 | SRS 改訂で「再開確認の有効期限 60 分」を明示 |

**重要:** 上記いずれも RCM 論理は不変、SDD で実装値を確定したのみ。CR-0001 の影響範囲(MODERATE)は変えない。Inc.2 着手前に **新規 CR(SRS 改訂)** として起票する運用とする。

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

## 8. 改訂履歴

| バージョン | 日付 | 変更内容 | 変更者 |
|----------|------|---------|--------|
| 0.1 | 2026-04-18 | 初版作成(Inc.1 範囲):代表 5 ユニット(State Machine / Flow Command Validator / HW-side Failsafe Timer / Atomic File Writer / Integrity Validator)を §5.4.2 テンプレートに従って詳細記述、残 9 ユニットを骨格記述(責務・主要 API・依存・SDD v0.2 詳細化項目)、§5.4.3 I/F 詳細 13 件、§5.4.4 検証観点チェックリスト・レビュー記録。SDD v0.2 は CR 起票で追補予定、`inc1-design-frozen` タグは v0.2 完成後に付与 | k-abe |
| 0.2 | 2026-04-19 | **CR-0001(Issue #1、MODERATE)による改訂。** v0.1 で骨格記述に留めていた 12 ユニットを §5.4.2 詳細記述に展開:UNIT-001.2 Control Loop(§4.6)/ UNIT-001.3 Command Handler(§4.7)/ UNIT-001.5 Watchdog SW(§4.8)/ UNIT-002.1 Pump Simulator(§4.9)/ UNIT-002.2 Pump Observer(§4.10)/ UNIT-002.3 Event Injection Stub(§4.11)/ UNIT-003.1 Serializer(§4.12)/ UNIT-003.2 Checksum Verifier(§4.13)/ UNIT-004.2 Resume Confirmation Gate(§4.14)/ UNIT-005.1 Control API(§4.15)/ UNIT-005.2 State Observer API(§4.16)/ UNIT-005.3 Validation API(§4.17、分離対象 B)。§3.2 ユニット一覧を全 17 ユニット詳細状態に更新。§6.2 レビュー記録に v0.2 行追加。§6.3 を「骨格記述の解消(v0.2 で完了)」に書き換え、実装ブロックの解除を宣言。§6.4「v0.2 で発見した SRS / RMF 整合性課題」を新規追加(ISS-V02-001〜004 を後続 SRS 改訂 CR の対象として申し送り)。§7 トレーサビリティの「本 SDD での記述」列を全行「詳細(§x.y、vN)」形式に更新。RCM 論理不変、SOUP 追加なし、外部 I/F 変更なし(SRMP §7.3「RCM 非関連部の変更」相当) | k-abe |
