# ソフトウェア詳細設計書(SDD)

**ドキュメント ID:** SDD-VIP-001
**バージョン:** 0.1
**作成日:** 2026-04-18
**対象製品:** 仮想輸液ポンプ(Virtual Infusion Pump) / VIP-SIM-001
**対象ソフトウェアバージョン:** 0.1.0(Inc.1 範囲、代表 5 ユニット詳細 + 他 9 ユニット骨格)
**安全クラス:** C(IEC 62304)

| 役割 | 氏名 | 所属 | 日付 | 署名 |
|------|------|------|------|------|
| 作成者 | k-abe | — | 2026-04-18 | |
| レビュー者 | — | — | — | |
| 承認者 | — | — | — | |

> **本プロジェクトの位置づけ(注記)**
> 本ドキュメントは IEC 62304 に基づく医療機器ソフトウェア開発プロセスの学習・参考実装を目的とした **仮想プロジェクト** の成果物である。本 SDD v0.1 では、お手本としての多様な設計パターンを示すため **5 つの代表ユニットを §5.4.2 テンプレートに従って詳細記述** し、残る 9 ユニットは **骨格記述**(責務・主要 API・依存関係・引用 SRS/ARCH/RCM)に留める。**SDD v0.2** で残りユニットを詳細化し、Inc.1 実装着手前に全ユニットの詳細設計を完了させる運用とする(SCMP §4.1 MODERATE CR として起票予定)。
>
> **代表 5 ユニット(詳細記述対象):** State Machine / Flow Command Validator / HW-side Failsafe Timer / Atomic File Writer / Integrity Validator — 状態機械・バリデータ・並行タイマ・永続化・起動復元という詳細設計のアーキタイプを網羅する選定。

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

| ユニット ID | 名称 | 所属項目 | 安全クラス | 本 SDD v0.1 での扱い |
|-----------|------|---------|----------|-------------------|
| UNIT-001.1 | State Machine | ARCH-001 | C | **詳細記述**(§4.1) |
| UNIT-001.2 | Control Loop | ARCH-001 | C | 骨格(§4.2.1) |
| UNIT-001.3 | Command Handler | ARCH-001 | C | 骨格(§4.2.2) |
| UNIT-001.4 | Flow Command Validator | ARCH-001 | C | **詳細記述**(§4.2) |
| UNIT-001.5 | Watchdog (SW) | ARCH-001 | C | 骨格(§4.2.3) |
| UNIT-002.1 | Pump Simulator | ARCH-002 | C | 骨格(§4.2.4) |
| UNIT-002.2 | Pump Observer | ARCH-002 | C | 骨格(§4.2.5) |
| UNIT-002.3 | Event Injection Stub | ARCH-002 | C(本版スタブ) | 骨格(§4.2.6) |
| UNIT-002.4 | HW-side Failsafe Timer | ARCH-002 | C | **詳細記述**(§4.3) |
| UNIT-003.1 | Serializer | ARCH-003 | C | 骨格(§4.2.7) |
| UNIT-003.2 | Checksum Verifier | ARCH-003 | C | 骨格(§4.2.8) |
| UNIT-003.3 | Atomic File Writer | ARCH-003 | C | **詳細記述**(§4.4) |
| UNIT-004.1 | Integrity Validator | ARCH-004 | C | **詳細記述**(§4.5) |
| UNIT-004.2 | Resume Confirmation Gate | ARCH-004 | C | 骨格(§4.2.9) |
| UNIT-005.1〜.3 | Public API Facade 各 API | ARCH-005 | C/C/B | 骨格(§4.2.10、SDD v0.2 で詳細化) |

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

## 4.2 骨格記述ユニット(SDD v0.2 で詳細化予定)

以下 9 ユニットは **責務・主要 API・依存関係** のみ記述。完全な §5.4.2 詳細(アルゴリズム擬似コード・資源使用量・全異常系・全検証方法)は **SDD v0.2** で追補する。実装着手は SDD v0.2 完成後に行う(クラス C 要求の遵守)。

### 4.2.1 UNIT-001.2: Control Loop

- **責務:** 100 ms 周期で仮想ポンプに流量指令を送出、積算量更新、ハートビート送出、自動停止判定
- **主要 API:** `start()`, `stop()`, `tick()`(内部、周期コール)
- **依存:** UNIT-001.4 Validator、UNIT-002.1 Pump Simulator、UNIT-002.4 HW-side Failsafe Timer、UNIT-001.5 Watchdog、UNIT-001.1 State Machine(状態照会・自動停止イベント送信)
- **関連 SRS:** SRS-011, SRS-012, SRS-P02, SRS-RCM-004
- **SDD v0.2 で詳細化する項目:** 周期精度の実装方法(`threading.Timer` vs monotonic loop)、自動停止閾値判定、RCM 連携のエラーパス

### 4.2.2 UNIT-001.3: Command Handler

- **責務:** Control API から受領した外部コマンドをキュー化し、State Machine へ遷移イベントとして順次渡す
- **主要 API:** `enqueue(cmd: Command) -> AcceptResult`、内部 `_dispatch_loop()`
- **依存:** UNIT-001.1 State Machine、UNIT-005.1 Control API(呼出元)
- **関連 SRS:** SRS-010/013/014, SRS-P03/P04
- **SDD v0.2 詳細化項目:** キュー満杯時の扱い、同期待機の応答時間保証

### 4.2.3 UNIT-001.5: Watchdog (SW side)

- **責務:** Control Loop のハートビートを監視。300 ms 以上未更新で State Machine に ERROR 遷移を要求(RCM-003)
- **主要 API:** `heartbeat(ts)`, `trigger_on_timeout()`, `start()`, `stop()`
- **依存:** UNIT-001.1 State Machine(ERROR 遷移誘発)
- **関連 SRS:** SRS-RCM-003
- **SDD v0.2 詳細化項目:** タイムアウト値の出典根拠、UNIT-002.4 との二重冗長の非同期性確認

### 4.2.4 UNIT-002.1: Pump Simulator

- **責務:** 仮想的な流量指令を受け取り、時間経過に応じて積算量・経過時間・現在流量を更新
- **主要 API:** `set_flow_rate(value)`, `advance_time(dt)`, `reset()`, `force_stop_failsafe(reason)`
- **依存:** なし(最下層)
- **関連 SRS:** SRS-030, SRS-031
- **SDD v0.2 詳細化項目:** 流量応答の過渡特性(立上り時間、オーバーシュート)、SRS-P01 ±5% 精度を達成する内部モデル

### 4.2.5 UNIT-002.2: Pump Observer

- **責務:** 仮想ポンプの内部状態を読み取り、PumpSnapshot として返す(純粋関数、読み取りのみ)
- **主要 API:** `observe() -> PumpSnapshot`
- **依存:** UNIT-002.1(内部データへの読み取りアクセス)
- **関連 SRS:** SRS-031, SRS-I-020
- **SDD v0.2 詳細化項目:** 読み取りの atomic 性(`threading.Lock` を使うか、不変スナップショットか)

### 4.2.6 UNIT-002.3: Event Injection Stub

- **責務:** Inc.2 向けの閉塞・気泡・薬液切れイベント注入 I/F。本版では呼び出し記録のみ保持(スタブ)
- **主要 API:** `inject(event: VirtualHwEvent) -> None`(no-op/記録のみ)
- **依存:** なし
- **関連 SRS:** SRS-032, SRS-I-040(将来)
- **SDD v0.2 での扱い:** 本版は no-op のまま、Inc.2 開始時に本格実装する(ARCH-002.3 のクラス C 再評価も同時)

### 4.2.7 UNIT-003.1: Serializer

- **責務:** Settings + RuntimeState を JSON にシリアライズ、および JSON から復元
- **主要 API:** `to_json(record: PersistedRecord) -> bytes`, `from_json(data: bytes) -> RawPersistedRecord`
- **依存:** `pydantic`(SOUP-002)、`json`(標準ライブラリ)、`decimal`(標準ライブラリ)
- **関連 SRS:** SRS-DATA-001/004
- **SDD v0.2 詳細化項目:** Decimal のシリアライズ方法(文字列 vs 文字列+スキーマタグ)、スキーママイグレーション戦略

### 4.2.8 UNIT-003.2: Checksum Verifier

- **責務:** SHA-256 による payload のチェックサム生成・検証
- **主要 API:** `compute(data: bytes) -> str`, `verify(data: bytes, expected: str) -> bool`
- **依存:** `hashlib`(標準ライブラリ)
- **関連 SRS:** SRS-SEC-001
- **SDD v0.2 詳細化項目:** 簡潔なので v0.2 でも大きく膨らまない想定。`hmac` 方式への拡張余地を注記する

### 4.2.9 UNIT-004.2: Resume Confirmation Gate

- **責務:** 起動時に検出した中断注入(PAUSED 復元 or 未完了 RUNNING 履歴)の自動再開を禁止し、`confirm_resume(token)` の明示呼び出しを待つ
- **主要 API:** `set_pending(token: str, detail: ResumeDetail) -> None`, `is_pending() -> bool`, `confirm(token: str) -> ConfirmResult`
- **依存:** UNIT-001.1 State Machine(遷移イベント発行)
- **関連 SRS:** SRS-028, SRS-RCM-016
- **SDD v0.2 詳細化項目:** token の生成方式(乱数)、タイムアウト(確認なく一定時間経過したら警告記録)

### 4.2.10 UNIT-005.1〜.3: Public API Facade 各ユニット

- **UNIT-005.1 Control API**(C):Command Handler への薄いラッパー。`start/stop/pause/resume/reset/error_reset/confirm_resume` を公開
- **UNIT-005.2 State Observer API**(C、読み取り専用):`observe_state() -> StateSnapshot`、idempotent
- **UNIT-005.3 Validation API**(B、分離対象):`validate_settings(settings) -> ValidationResult`、純粋関数、pydantic モデル経由
- **SDD v0.2 詳細化項目:** 例外ポリシー(原則的に返り値で表現)、型シグネチャ確定、pydantic スキーマの提供範囲

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
| 骨格 9 ユニットの SDD v0.2 追補計画の妥当性 | Pass(v0.2 で詳細化する項目を各ユニットで明示) | 2026-04-18 | 本書 §4.2 |
| 分離境界(SEP-001/002/003)の詳細設計反映 | Pass | 2026-04-18 | §5.3 |

### 6.3 骨格記述のリスク管理

骨格記述段階では §5.4.2 要求を完全には満たさない。このリスクを以下で管理:

- **実装ブロック:** 骨格ユニットは SDD v0.2 完成まで実装に進まない(CCB 規程の運用ルール)
- **CR 起票予定:** SDD v0.2 作成は「CR-0001 = MODERATE 区分」として CCB プロセス経由で起票予定(CRR-VIP-001 初回エントリ)
- **SDD v0.1 凍結タイミング:** 本 SDD v0.1 は「詳細設計パターン提示の参考実装」として位置づけ、`inc1-design-frozen` タグは SDD v0.2 完成後に付与する

## 7. トレーサビリティマトリクス

本 SDD v0.1 時点で UT/IT/ST 試験計画は未作成(箇条 5.5〜5.7)。UT ID 列は試験計画作成時に充填する。

| SRS ID | ARCH ID | UNIT ID | 本 SDD での記述 | UT ID(後続で充填) |
|--------|---------|---------|--------------|-------------------|
| SRS-020, SRS-RCM-020, SRS-ALM-003 | ARCH-001.1 | UNIT-001.1 | **詳細(§4.1)** | — |
| SRS-011, SRS-012, SRS-P02, SRS-RCM-004 | ARCH-001.2 | UNIT-001.2 | 骨格(§4.2.1) | — |
| SRS-010/013/014, SRS-P03/P04 | ARCH-001.3 | UNIT-001.3 | 骨格(§4.2.2) | — |
| SRS-O-001, SRS-RCM-001, SRS-005 | ARCH-001.4 | UNIT-001.4 | **詳細(§4.2)** | — |
| SRS-RCM-003 | ARCH-001.5 | UNIT-001.5 | 骨格(§4.2.3) | — |
| SRS-030 | ARCH-002.1 | UNIT-002.1 | 骨格(§4.2.4) | — |
| SRS-031, SRS-I-020 | ARCH-002.2 | UNIT-002.2 | 骨格(§4.2.5) | — |
| SRS-032, SRS-I-040(将来) | ARCH-002.3 | UNIT-002.3 | 骨格(§4.2.6) | — |
| SRS-RCM-004(HW 側) | ARCH-002.4 | UNIT-002.4 | **詳細(§4.3)** | — |
| SRS-DATA-001, SRS-DATA-004 | ARCH-003.1 | UNIT-003.1 | 骨格(§4.2.7) | — |
| SRS-SEC-001 | ARCH-003.2 | UNIT-003.2 | 骨格(§4.2.8) | — |
| SRS-DATA-002, SRS-DATA-003 | ARCH-003.3 | UNIT-003.3 | **詳細(§4.4)** | — |
| SRS-027, SRS-RCM-015 | ARCH-004.1 | UNIT-004.1 | **詳細(§4.5)** | — |
| SRS-028, SRS-RCM-016 | ARCH-004.2 | UNIT-004.2 | 骨格(§4.2.9) | — |
| SRS-IF-002、SRS-010〜014 | ARCH-005.1 | UNIT-005.1 | 骨格(§4.2.10) | — |
| SRS-IF-003, SRS-O-010, SRS-UX-002 | ARCH-005.2 | UNIT-005.2 | 骨格(§4.2.10) | — |
| SRS-UX-001, SRS-004, SRS-005 | ARCH-005.3 | UNIT-005.3 | 骨格(§4.2.10、分離対象 B) | — |

## 8. 改訂履歴

| バージョン | 日付 | 変更内容 | 変更者 |
|----------|------|---------|--------|
| 0.1 | 2026-04-18 | 初版作成(Inc.1 範囲):代表 5 ユニット(State Machine / Flow Command Validator / HW-side Failsafe Timer / Atomic File Writer / Integrity Validator)を §5.4.2 テンプレートに従って詳細記述、残 9 ユニットを骨格記述(責務・主要 API・依存・SDD v0.2 詳細化項目)、§5.4.3 I/F 詳細 13 件、§5.4.4 検証観点チェックリスト・レビュー記録。SDD v0.2 は CR 起票で追補予定、`inc1-design-frozen` タグは v0.2 完成後に付与 | k-abe |
