# ソフトウェアアーキテクチャ設計書

**ドキュメント ID:** SAD-VIP-001
**バージョン:** 0.1
**作成日:** 2026-04-18
**対象製品:** 仮想輸液ポンプ(Virtual Infusion Pump) / VIP-SIM-001
**対象ソフトウェアバージョン:** 0.1.0(Inc.1 範囲)
**安全クラス:** C(IEC 62304)

| 役割 | 氏名 | 所属 | 日付 | 署名 |
|------|------|------|------|------|
| 作成者 | k-abe | — | 2026-04-18 | |
| レビュー者 | — | — | — | |
| 承認者 | — | — | — | |

> **本プロジェクトの位置づけ(注記)**
> 本ドキュメントは IEC 62304 に基づく医療機器ソフトウェア開発プロセスの学習・参考実装を目的とした **仮想プロジェクト** の成果物である。本 SAD は V字モデル(インクリメンタル方式)に従い **Inc.1(流量制御コア)範囲のアーキテクチャのみを確定** する。Inc.2〜4 範囲のアーキテクチャ要素(アラーム管理・用量計算・UI・ロギング)は、各インクリメント開始時に本書を改訂して追補する。

---

## 1. 目的と適用範囲

本書は、SRS-VIP-001 v0.1 に定められた Inc.1 範囲の要求事項を実現するためのソフトウェアアーキテクチャを IEC 62304 箇条 5.3 に基づいて定義する。本書で定義するアーキテクチャは以下の判断の基礎となる:

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
| [3] | ソフトウェア要求仕様書(SRS-VIP-001) | 0.1(Inc.1 範囲確定) |
| [4] | ソフトウェア開発計画書(SDP-VIP-001) | 0.1 |
| [5] | ソフトウェア安全クラス決定記録(SSC-VIP-001) | 0.1 |
| [6] | リスクマネジメントファイル(RMF-VIP-001) | 0.2(RCM-019 登録済) |
| [7] | ソフトウェアリスクマネジメント計画書(SRMP-VIP-001) | 0.1 |
| [8] | 構成アイテム一覧(CIL-VIP-001) | 0.2 |

## 3. ソフトウェア要求事項のソフトウェアアーキテクチャへの変換(箇条 5.3.1)

SRS の Inc.1 範囲全 要求事項を、本書で定義するアーキテクチャ要素(ソフトウェア項目 ARCH-NNN)に割付ける。割付けは §11 トレーサビリティマトリクスで網羅性を検証可能とする。割付けの原則:

1. **単一責務**: 各 ARCH は原則 1 つの機能領域に責任を持つ(制御コア / 仮想 HW / 永続化 等)。
2. **安全クリティカル分離**: RCM を実装する項目と非 RCM 項目を可能な限り分離し、§9 で分離根拠を明示する。
3. **テスタビリティ**: 項目間 I/F は依存性注入(DI)で差し替え可能にし、仮想 HW や永続化をテスト用スタブに置換できるようにする。
4. **インクリメンタル追補**: Inc.2〜4 で追加する項目が既存項目に破壊的変更を強いない契約を設計する(SRS-IF-001/004/010/020 のスタブ戦略)。

## 4. ソフトウェアアーキテクチャの概要

### 4.1 アーキテクチャ方針

- **スタイル:** レイヤード + イベント駆動の複合
  - **レイヤード**: 外部 API → 制御コア → 仮想ハードウェアの 3 レイヤ構造
  - **イベント駆動**: 制御コマンド(START/STOP/PAUSE/RESUME)はイベントとしてキューイング、制御ループ(100 ms サイクル)は定期駆動
- **採用理由:**
  - レイヤードは IEC 60601 系機器で広く採用され、監査対応が容易
  - イベント駆動は制御ループとコマンド処理の時間的デカップリングに適合(SRS-P02 ジッタ要件・SRS-P06 非ブロッキング要件を同時に満たす)
  - Inc.2(アラーム)・Inc.4(UI)の追加時も、最上位 API 層にアダプタを追加するだけで済む

### 4.2 全体構成図(Inc.1 範囲)

```
      外部呼び出し元(試験ハーネス / 将来の Inc.4 UI)
                        │
                        ▼
      ┌─────────────────────────────────────────────┐
      │ ARCH-005: Public API Facade                  │
      │  ├─ 005.1 Control API (start/stop/pause/     │
      │  │        resume/reset/confirm_resume)       │
      │  ├─ 005.2 State Observer API (read-only)     │
      │  └─ 005.3 Validation API (pure function)     │
      └─────────────────────────────────────────────┘
          │              │                      ▲
          │              │ (observe)            │ (validate: 副作用なし)
          ▼              │                      │
      ┌─────────────────────────────────────────────┐
      │ ARCH-001: Control Core (クラス C)             │
      │  ├─ 001.1 State Machine (RCM-019)            │
      │  ├─ 001.2 Control Loop (100 ms、RCM-004 HB) │
      │  ├─ 001.3 Command Handler                    │
      │  ├─ 001.4 Flow Cmd Validator (RCM-001)       │
      │  └─ 001.5 Watchdog (RCM-003)                 │
      └─────────────────────────────────────────────┘
          │ (flow cmd / observe)          │ (save/load)
          ▼                                ▼
      ┌──────────────────────┐    ┌──────────────────────┐
      │ ARCH-002: Virtual    │    │ ARCH-003:           │
      │ Hardware (クラス C)  │    │ Persistence (C)      │
      │ ├─ 002.1 Pump Sim    │    │ ├─ 003.1 Serializer │
      │ ├─ 002.2 Observer    │    │ ├─ 003.2 Checksum   │
      │ ├─ 002.3 Event Stub  │    │ │        (SRS-SEC)  │
      │ │     (Inc.2 向け)   │    │ └─ 003.3 Atomic Wr  │
      │ └─ 002.4 HW-side FS  │    └──────────────────────┘
      │    Timer (RCM-004)   │             ▲
      └──────────────────────┘             │ (load)
                                           │
                         ┌────────────────────────────────┐
                         │ ARCH-004: Boot / Recovery (C)  │
                         │  ├─ 004.1 Integrity Validator  │
                         │  │        (RCM-015)            │
                         │  └─ 004.2 Resume Confirmation  │
                         │           Gate (RCM-016)       │
                         └────────────────────────────────┘

    --- 分離境界(SEP-001/002)以下は低安全クラス候補 ---
      ┌──────────────────────┐    ┌──────────────────────┐
      │ ARCH-006: Logging    │    │ ARCH-007: Alarm      │
      │ Stub I/F (B候補)     │    │ Reporter Stub I/F    │
      │ (Inc.4 で実装)       │    │ (B候補、Inc.2 実装)  │
      └──────────────────────┘    └──────────────────────┘
```

### 4.3 ソフトウェア項目一覧

#### 4.3.1 Inc.1 範囲の ARCH 項目

| 項目 ID | 名称 | 分類 | 安全クラス(分離後) | 概要 | 主担当 SRS |
|---------|------|------|-------------------|------|-----------|
| ARCH-001 | Control Core | 項目 | C | 流量制御の中核。状態機械・制御ループ・コマンド処理・範囲チェック・WDT | SRS-010〜014, 020, RCM 全般 |
| ARCH-001.1 | State Machine | ユニット | C | 状態遷移表の強制、不正遷移の拒否(RCM-019) | SRS-020, SRS-RCM-020 |
| ARCH-001.2 | Control Loop | ユニット | C | 100ms サイクルで流量指令発行、積算量更新、ハートビート送出 | SRS-011, SRS-P02, RCM-004 |
| ARCH-001.3 | Command Handler | ユニット | C | 外部コマンドをキュー受信し、妥当性を検証して状態機械に渡す | SRS-010/013/014 |
| ARCH-001.4 | Flow Command Validator | ユニット | C | 流量指令値の範囲・設定値一致を検証(RCM-001) | SRS-O-001, SRS-RCM-001 |
| ARCH-001.5 | Watchdog | ユニット | C | 制御ループのハートビート監視、タイムアウト時に ERROR 遷移 | SRS-RCM-003 |
| ARCH-002 | Virtual Hardware | 項目 | C | 仮想ポンプ機構のシミュレーション。実機代替として注入実行・状態観測・フェイルセーフ | SRS-030/031/032 |
| ARCH-002.1 | Pump Simulator | ユニット | C | 流量指令に応じた積算量・流量を時間進行でシミュレート | SRS-030 |
| ARCH-002.2 | Pump Observer | ユニット | C | 現在流量・積算量・経過時間・機構状態を読み取り公開 | SRS-031 |
| ARCH-002.3 | Event Injection Stub | ユニット | C(Inc.2 で詳細化) | 閉塞・気泡・薬液切れのイベント注入 I/F(本版ではスタブ) | SRS-032, SRS-I-040 |
| ARCH-002.4 | HW-side Failsafe Timer | ユニット | C | ハートビート途絶(500 ms)で仮想ポンプ側から流量 0 へ自発停止 | SRS-RCM-004 |
| ARCH-003 | Persistence | 項目 | C | 設定・状態・積算量の永続化と整合性担保 | SRS-025, SRS-SEC-001 |
| ARCH-003.1 | Serializer | ユニット | C | JSON ベースのスキーマ付きシリアライズ/デシリアライズ | SRS-DATA-001/004 |
| ARCH-003.2 | Checksum Verifier | ユニット | C | SHA-256 チェックサムの生成・検証 | SRS-SEC-001 |
| ARCH-003.3 | Atomic File Writer | ユニット | C | temp → rename パターンの atomic 書き込み、1 世代バックアップ | SRS-DATA-002/003 |
| ARCH-004 | Boot / Recovery | 項目 | C | 起動時の整合性検証と状態復元、中断注入の再開確認ゲート | SRS-026〜028 |
| ARCH-004.1 | Integrity Validator | ユニット | C | チェックサム・値域・状態組合せの整合性検証、失敗時フェイルセーフ(RCM-015) | SRS-027, SRS-RCM-015 |
| ARCH-004.2 | Resume Confirmation Gate | ユニット | C | 中断注入の自動再開を禁止し `confirm_resume(token)` を待つ(RCM-016) | SRS-028, SRS-RCM-016 |
| ARCH-005 | Public API Facade | 項目 | C(分離後 005.3 のみ B 候補) | 外部呼出しへのファサード。Inc.4 UI / 試験ハーネスからの入口 | SRS-I-010, SRS-O-010 |
| ARCH-005.1 | Control API | ユニット | C | 制御コマンドを Command Handler に転送、同期応答 | SRS-010〜014, SRS-IF-002 |
| ARCH-005.2 | State Observer API | ユニット | C(読み取り専用、副作用なし) | 現在状態のスナップショット取得、idempotent | SRS-O-010, SRS-IF-003, SRS-UX-002 |
| ARCH-005.3 | Validation API | ユニット | **B**(分離、純粋関数) | 設定値の妥当性検証のみ、状態変更なし | SRS-UX-001 |
| ARCH-006 | Logging Stub I/F | 項目 | **B**(分離候補、Inc.4 で実装) | 構造化ログ I/F。読み取り側への一方向出力のみ | SRS-021, SRS-IF-004, SRS-OPS-010 |
| ARCH-007 | Alarm Reporter Stub I/F | 項目 | **B**(分離候補、Inc.2 で実装) | アラーム通知の一方向出力 I/F | SRS-ALM-001, SRS-IF-010, SRS-O-040 |

**備考:**

- ARCH-006 / ARCH-007 は本 Inc.1 では **インタフェース(抽象クラス/プロトコル)のみ** を定義し、実装はスタブで単純に no-op または固定値を返す。
- Inc.2 でアラーム管理本体(ARCH-007 実装 + 閉塞/気泡/薬液切れ検知)を追加する予定。
- Inc.3 で用量計算 ARCH-008 を追加予定(CLI ID 予約済、§11 参照)。
- Inc.4 で UI 層 ARCH-009 + ロギング実装 ARCH-006 本体を追加予定。

## 5. ソフトウェア項目間のインタフェース(箇条 5.3.2)

| IF ID | 呼出側 | 被呼出側 | 種別 | 仕様概要 | 関連 SRS |
|-------|--------|---------|------|---------|---------|
| IF-U-001 | ARCH-005.1 Control API | ARCH-001.3 Command Handler | 関数呼出(同期) | `enqueue_command(cmd: Command) -> Result` | SRS-I-010 |
| IF-U-002 | ARCH-001.2 Control Loop | ARCH-002.1 Pump Simulator | 関数呼出(同期) | `set_flow_rate(value: Decimal) -> None`(バリデータ経由) | SRS-O-001 |
| IF-U-003 | ARCH-001.2 / ARCH-005.2 | ARCH-002.2 Pump Observer | 関数呼出(同期) | `observe() -> PumpSnapshot`(idempotent) | SRS-I-020, SRS-O-010 |
| IF-U-004 | ARCH-001.1 State Machine | ARCH-003 Persistence | 関数呼出(非同期 / キュー) | `save_async(state: RuntimeState) -> None`(≤ 1 秒サイクル、SRS-P06 のため非ブロック) | SRS-025 |
| IF-U-005 | ARCH-004.1 Integrity Validator | ARCH-003 Persistence | 関数呼出(同期、起動時のみ) | `load() -> PersistedRecord \| LoadError` | SRS-026 |
| IF-U-006 | ARCH-004 Boot | ARCH-001.1 State Machine | 関数呼出(起動時のみ) | `initialize(initial_state: RuntimeState, needs_confirm: bool) -> None` | SRS-027/028 |
| IF-U-007 | ARCH-001.1 State Machine | ARCH-007 Alarm Reporter Stub | I/F(単方向通知) | `report_alarm(event: AlarmEvent) -> None`(本版は no-op) | SRS-ALM-001, SRS-O-040 |
| IF-U-008 | 全 ARCH-001〜004 | ARCH-006 Logging Stub | I/F(単方向出力) | `log(record: LogRecord) -> None`(本版は no-op) | SRS-021, SRS-O-030 |
| IF-U-009 | ARCH-001.5 Watchdog | ARCH-001.1 State Machine | 関数呼出(非同期) | `trigger_error(reason: WatchdogReason) -> None` | SRS-RCM-003 |
| IF-U-010 | ARCH-001.2 Control Loop | ARCH-001.5 Watchdog | 関数呼出(同期) | `heartbeat(ts: Monotonic) -> None`(サイクルごと) | SRS-RCM-003/004 |
| IF-U-011 | ARCH-001.2 Control Loop | ARCH-002.4 HW-side FS Timer | 関数呼出(同期) | `heartbeat(ts: Monotonic) -> None`(サイクルごと、RCM-004) | SRS-RCM-004 |
| IF-E-001 | 外部(UI / 試験ハーネス) | ARCH-005 Public API | 外部 API | Python モジュール公開関数(`vip_ctrl.api.*`) | SRS-IF-002/003 |
| IF-E-002 | ARCH-003.3 Atomic Writer | OS ファイルシステム | OS システムコール | `os.rename`(POSIX atomic) | SRS-DATA-002 |

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
| SEP-002 | ARCH-006 Logging Stub I/F(C → B) | 抽象 I/F + 一方向出力 + 値型渡し(LogRecord は frozen) | **根拠:** ログは出力のみで制御へのフィードバック経路が無い。ログ実装の失敗(例外)は呼出元でガード(try/except)し制御に伝播させない設計とする。<br>**検証方法:** 結合試験でログ実装が例外を投げても制御ループが継続することを確認、mypy + ruff で Control Core からの参照が抽象 I/F にのみ向かうことを静的確認 |
| SEP-003 | ARCH-007 Alarm Reporter Stub I/F(C → B) | 抽象 I/F + 一方向出力 + 値型渡し(AlarmEvent は frozen) | **根拠:** 本 Inc.1 では Alarm Reporter は no-op スタブ。Inc.2 以降でアラーム管理本体が接続されるが、**アラーム判定ロジック(検知)はクラス C(Inc.2 で ARCH-007 本体はクラス C を維持)**、通知 I/F のみが分離対象。通知 I/F 自体は出力専用で制御への影響経路がない。<br>**検証方法:** SEP-002 と同様 |
| SEP-000(非分離) | ARCH-001〜004(C 維持) | — | **根拠:** 流量制御・仮想 HW・永続化・起動は、いずれも RCM の一次実装または安全に直結する機能を含むため、クラス C を維持する。分離しない方針を明示的に記録 |

### 9.3 分離が成立しない場合の帰結

本プロジェクトの分離(SEP-001/002/003)は **論理的分離** のみに依存する。以下のいずれかが崩れた場合、対象項目は再びクラス C として扱い、以降の試験・検証を再実施する:

- mypy / ruff の静的ルールが無効化された、または違反が検出されたまま修正されずマージされた
- 分離境界を越えた可変オブジェクトの共有が発生した(frozen 属性の回避等)
- ログ I/F やアラーム I/F の実装から制御コアへコールバックが追加された

これらは SRMP §7.4.2「既存 RCM への影響の解析」の対象となる。

## 10. ソフトウェアアーキテクチャの検証(箇条 5.3.6)

本アーキテクチャは以下を満たすことを設計レビュー(セルフ)で確認する:

- [x] **SRS のすべての Inc.1 要求事項を実装可能である** — §11 トレーサビリティマトリクスで SRS-001〜SRS-RCM-020 の全項目に ARCH-NNN を割付け済
- [x] **ソフトウェア項目間・外部システムとのインタフェースが一貫している** — §5 IF 表に 12 件の I/F を定義、呼出方向・種別・仕様を明示
- [x] **医療機器のリスクコントロール手段の実装を支援する** — RCM-001/003/004/015/016/019 それぞれを実装する ARCH-NNN を §4.3 で明示(ARCH-001.4/1.5/2.4/4.1/4.2/1.1 等)
- [x] **安全クラスに応じた分離が適切に設計されている** — §9 で SEP-001/002/003 を定義、分離根拠・検証方法を明示
- [x] **SOUP の仕様(機能・性能要求)が記述されている** — §7 で SOUP-001/002 の機能・性能要求を指定、§8 で動作要件を指定

レビュー記録:

| 項目 | 結果 | レビュー日 | 記録 |
|------|------|----------|------|
| SRS 全要求 → ARCH 割付 網羅性 | Pass(§11) | 2026-04-18 | 本書作成自体 + §11 |
| I/F 定義の一貫性 | Pass(§5) | 2026-04-18 | 同上 |
| RCM → ARCH 実装先の明示 | Pass(§4.3、§11) | 2026-04-18 | 同上 |
| 分離設計(§5.3.5)の妥当性 | Pass(§9) | 2026-04-18 | 同上 |
| SOUP 要求の完全性 | Pass(§6〜§8) | 2026-04-18 | 同上 |

**単独開発下の独立性担保:** CCB-VIP-001 §5.4 に基づき、本 SAD 作成開始から PR 作成までに **CCB §5.4 で規定されるインターバル**(本プロジェクトでは 1 分以上、学習プロジェクト特例。実機適用時は 24 時間以上)を経てセルフレビューを実施し、CI 全 Pass を確認する。

## 11. トレーサビリティマトリクス(SRS → ARCH)

Inc.1 範囲の SRS 要求をアーキテクチャ要素に割付ける。SDD(箇条 5.4)作成時に「SDD 列」、試験計画(5.5〜5.7)作成時に「UT/IT/ST 列」を充填する。

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
| SRS-020 | ARCH-001.1 State Machine | 状態機械本体 |
| SRS-021 | ARCH-006 Logging Stub I/F、ARCH-001.1(遷移時ログ呼出) | ログ I/F 経由 |
| SRS-025 | ARCH-003 全ユニット、ARCH-001.1(save 呼出) | 非同期永続化 |
| SRS-026 | ARCH-004.1、ARCH-003 | 起動時復元 |
| SRS-027 | ARCH-004.1、ARCH-001.1(初期化受入) | フェイルセーフ起動 |
| SRS-028 | ARCH-004.2 Resume Gate、ARCH-005.1(confirm_resume) | 再開確認 |
| SRS-030 | ARCH-002.1 Pump Simulator | 仮想ポンプ機構 |
| SRS-031 | ARCH-002.2 Pump Observer | 状態観測 I/F |
| SRS-032 | ARCH-002.3 Event Injection Stub | Inc.2 向けスタブ I/F 契約 |

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
| SRS-I-040(Inc.2 予定) | ARCH-002.3 Event Injection Stub | 予約 |
| SRS-O-001 | ARCH-001.2 → ARCH-002.1(IF-U-002) | 流量指令 |
| SRS-O-010 | ARCH-005.2 State Observer API | 状態出力 |
| SRS-O-020 | ARCH-003 | 永続化書き込み |
| SRS-O-030 | ARCH-006 Logging Stub I/F | ログ出力 |
| SRS-O-040 | ARCH-007 Alarm Reporter Stub I/F | エラー通知(Inc.2 で本実装) |
| SRS-IF-001 | ARCH-002 全体 | 仮想 HW I/F |
| SRS-IF-002 | ARCH-005.1 | 制御 API |
| SRS-IF-003 | ARCH-005.2 | 状態観測 API |
| SRS-IF-004 | ARCH-006 | ロギング I/F |
| SRS-IF-005 | ARCH-003 | 永続化 I/F |
| SRS-IF-010(Inc.2 予定) | ARCH-007 | 予約 |
| SRS-IF-020(Inc.3 予定) | (ARCH-008 Inc.3 で新設予定) | 予約、現時点未割付 |

### 11.4 アラーム・セキュリティ・UX・データ・運用・規制要求

| SRS ID | ARCH | 備考 |
|--------|------|------|
| SRS-ALM-001 | ARCH-001.1 → ARCH-007 | ERROR 遷移通知 |
| SRS-ALM-002 | ARCH-004.1、ARCH-006 | 起動時ログ |
| SRS-ALM-003 | ARCH-001.1、ARCH-006 | 不正遷移ログ(RCM-019 連携) |
| SRS-SEC-001 | ARCH-003.2 Checksum Verifier | SHA-256 |
| SRS-SEC-002 | ARCH-006 | ログ I/F 契約でポリシー遵守 |
| SRS-SEC-003 | (CI 側 pip-audit、本 SAD の運用側要求) | SMP §7.1 |
| SRS-UX-001 | ARCH-005.3 Validation API(分離対象) | 純粋関数 |
| SRS-UX-002 | ARCH-005.2 State Observer API | idempotent |
| SRS-DATA-001〜004 | ARCH-003 全ユニット | 永続化ポリシー |
| SRS-OPS-001〜004 | ARCH-005 / パッケージング設定(CI-CFG-009 予定) | 配布・インストール |
| SRS-OPS-010〜012 | ARCH-006 / ARCH-005 | 運用 I/F |
| SRS-NET-001 | (全 ARCH、ネットワーク未使用) | — |
| SRS-REG-001 | SRS-P01 ↔ §11.2 経由で ARCH-001.2 / ARCH-002.1 | IEC 60601-2-24 相当 |
| SRS-REG-002(Inc.2 予定) | ARCH-007 本実装(Inc.2) | IEC 60601-1-8 |

### 11.5 リスクコントロール要求(SRS §5 → ARCH)

| SRS ID(RCM) | 対応 RCM | 実装 ARCH | 分離(§9) |
|--------------|---------|-----------|---------|
| SRS-RCM-001 | RCM-001 | ARCH-001.4 Flow Command Validator | クラス C(非分離) |
| SRS-RCM-003 | RCM-003 | ARCH-001.5 Watchdog | クラス C(非分離) |
| SRS-RCM-004 | RCM-004 | ARCH-001.2 + ARCH-002.4(HW-side FS Timer) | クラス C(非分離、二重冗長) |
| SRS-RCM-015 | RCM-015 | ARCH-004.1 Integrity Validator | クラス C(非分離) |
| SRS-RCM-016 | RCM-016 | ARCH-004.2 Resume Gate | クラス C(非分離) |
| SRS-RCM-020 | RCM-019 | ARCH-001.1 State Machine | クラス C(非分離) |

## 12. 改訂履歴

| バージョン | 日付 | 変更内容 | 変更者 |
|----------|------|---------|--------|
| 0.1 | 2026-04-18 | 初版作成(Inc.1 範囲):ARCH-001〜007 の 7 項目 + 下位ユニット 14 件を定義、I/F 12 件(内部 U 系 11 件、外部 E 系 2 件)を明示、SOUP-001/002 の機能・性能要求と動作要件を指定、分離 SEP-001/002/003 を定義(Validation API / Logging / Alarm を B へ分離)、SRS 全要求 → ARCH トレーサビリティを §11 で網羅。Inc.2 以降で ARCH-007 本実装、ARCH-008(Inc.3 用量計算)、ARCH-009(Inc.4 UI)を追補予定 | k-abe |
