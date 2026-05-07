# ソフトウェアシステム試験計画書/報告書

**ドキュメント ID:** STPR-VIP-001
**バージョン:** 0.2
**作成日:** 2026-05-07
**最終更新日:** 2026-05-07
**対象製品:** 仮想輸液ポンプ(Virtual Infusion Pump) / VIP-SIM-001
**対象ソフトウェア:** Virtual Infusion Pump Control Software(VIP-CTRL)
**対象ソフトウェアバージョン:** v0.1.0-inc1(予定、Inc.1 完了時)
**安全クラス:** C(IEC 62304)

| 役割 | 氏名 | 所属 | 日付 | 署名 |
|------|------|------|------|------|
| 作成者 | k-abe | 単独開発 | 2026-05-07 | k-abe |
| レビュー者 | k-abe(自己レビュー、CCB-VIP-001 §5.4 1 分インターバル + PR 自己レビューチェックリスト適用)| 単独開発 | 2026-05-07 | k-abe |
| 承認者 | k-abe(セルフ承認、SRMP §3.2 単独開発下の独立性擬制)| 単独開発 | 2026-05-07 | k-abe |

---

> **本書はシステム試験の計画と実施結果(報告)を一体で管理する。**
>
> **本 v0.1 は「代表 3 観点詳細化 + 残骨格 6 観点」段階成熟方式を採る**(ITPR v0.1 = Step 19 D-2 と UTPR v0.1 = Step 19 A の確立パターンに整合)。詳細化対象は **§6.1 ST-PERF**(性能要求の全体予算)、**§6.2 ST-OPS**(受入試験 + 運用)、**§6.3 ST-RCM**(RCM 統合検証 + IEC 62304 §5.7.4 妥当性確認)— Inc.1 完了タグ `v0.1.0-inc1` 付与の前提となる代表観点 3 つ。残 6 観点(§6.4 ST-FUNC / §6.5 ST-IF / §6.6 ST-ALM / §6.7 ST-SEC / §6.8 ST-UX / §6.9 ST-DATA)は試験観点・ケース数目安・関連 SRS のみを記述する骨格。Step 19 H(Inc.1 完了タグ前の全 RCM 集約)で代表 3 観点の試験実施 + 報告、Inc.2〜4 で残骨格 6 観点を順次詳細化する。

## 1. 目的と適用範囲

本書は、IEC 62304 箇条 5.7 に基づき、結合済み Virtual Infusion Pump Control Software(以下、VIP-CTRL)が SRS-VIP-001 のすべての要求事項を満たすことを **試験により検証** するシステム試験の計画と結果を記録する。

### 1.1 STPR と ITPR / UTPR の責務分担

| ドキュメント | 主な責務 | 試験対象 | 試験軸 |
|------------|---------|---------|--------|
| UTPR-VIP-001(§5.5) | ソフトウェアユニット個別の機能正常性 + MC/DC 100% | UNIT-NNN.M(単一 Python モジュール)| 単体内部 |
| ITPR-VIP-001(§5.6) | ユニット間結合(IF-U / IF-E)+ RCM 結合検証 | 複数 UNIT 連携経路、subprocess 経由の電源断耐性、サイドチャネル | 結合 |
| **STPR-VIP-001(本書、§5.7)** | **SRS 要求網羅 100% + 全 RCM のシステム統合動作 + 性能全体予算 + 受入試験** | **VIP-CTRL 全体(`pip install` 後の `vip-ctrl` CLI 単位)** | **要求ベース、外部観点** |

### 1.2 SRS-P03/P04 の IT/ST 分散配置(Step 19 F5 で確立)

ITPR v0.8(Step 19 F5)で確立した方針:

- **IT(ITPR §6.8 IT-PERF):SDD §4.7 内訳予算で検証**(SRS-P03 = SDD §4.7.E 内訳 100 ms / SRS-P04 = SDD §4.7.A ファストパス 50 ms)
- **ST(本 STPR §6.1 ST-PERF):SRS の全体予算で検証**(SRS-P03 全体 500 ms / SRS-P04 全体 200 ms)

これにより、SRS の要求(全体予算)は ST で網羅、SDD 内訳予算は IT で網羅という二重保証構造を実現する。

## 2. 参照文書

| ID | 文書名 | バージョン | 参照箇所 |
|----|--------|----------|---------|
| [1] | ソフトウェア要求仕様書 (SRS-VIP-001) | v0.1 | §3 SRS 網羅性、§13 トレース |
| [2] | ソフトウェア開発計画書 (SDP-VIP-001) | v0.1 | §4 試験戦略 |
| [3] | ソフトウェアアーキテクチャ設計書 (SAD-VIP-001) | v0.1 | §5 試験環境(ARCH 構造の整合)|
| [4] | ソフトウェア詳細設計書 (SDD-VIP-001) | v0.2 | §6.1 IT/ST 分散配置(SDD 内訳 vs SRS 全体予算) |
| [5] | ソフトウェアユニット試験計画書/報告書 (UTPR-VIP-001) | v0.19 | §1.1 責務分担 |
| [6] | ソフトウェア結合試験計画書/報告書 (ITPR-VIP-001) | v0.10 | §1.1 責務分担、§6.3 ST-RCM(F1〜F7 結果集約)|
| [7] | リスクマネジメントファイル (RMF-VIP-001) | v0.1 | §6.3 ST-RCM(SRS-RCM-* との対応)|
| [8] | ソフトウェアリスクマネジメント計画書 (SRMP-VIP-001) | v0.1 | §3.2 単独開発下の独立性擬制 |
| [9] | ソフトウェア構成管理計画書 (SCMP-VIP-001) | v0.1 | §4.1 MINOR 区分 |
| [10] | CCB 運用規程 (CCB-VIP-001) | v0.2 | §5.4 1 分インターバル(CR-0003 以降適用)|
| [11] | ソフトウェア問題解決手順書 (SPRP-VIP-001) | v0.1 | §5.7.2 試験中の不具合解決 |
| [12] | 構成アイテム一覧 (CIL-VIP-001) | v0.41 | CI-DOC-STPR 自己参照 |

### 2.1 適用規格

| 規格 | 内容 | 本 STPR での参照箇所 |
|------|------|------------------|
| IEC 62304:2006+A1:2015 | 医療機器ソフトウェア — ソフトウェアライフサイクルプロセス、§5.7 ソフトウェアシステム試験 | 全節 |
| IEC 60601-2-24 | 輸液ポンプの個別要求事項 — 流量精度 | §6.1 ST-PERF.1-01(SRS-P01 ±5%)|
| IEC 60601-1-8 | アラームシステム | §6.6 ST-ALM(Inc.2 正式化、Inc.1 はスタブ)|
| IEC 62366-1 | ユーザビリティエンジニアリング | §6.8 ST-UX(Inc.4 正式化、Inc.1 は API レビュー)|
| ISO 14971 | 医療機器のリスクマネジメント | §6.3 ST-RCM(SRS-RCM-* との対応)|

---

# 第 I 部 計画

## 3. ソフトウェア要求事項を検証する試験の設定(箇条 5.7.1)

### 3.1 SRS 網羅性方針

SRS-VIP-001 の **すべての要求事項**(SRS-001〜032、SRS-P01〜P07、SRS-I-*、SRS-O-*、SRS-IF-*、SRS-ALM-*、SRS-SEC-*、SRS-UX-*、SRS-DATA-*、SRS-OPS-*、SRS-REG-*、SRS-RCM-*)に対して、検証方法(試験 / レビュー / 解析 / デモ)を §13 トレーサビリティマトリクスで明示し、試験(ST)が選定された要求は §6.x 観点単位で試験ケース ID(`ST-{プレフィックス}.{サブ番号}-{連番}`)を割り当てる。

### 3.2 試験以外の検証方法を採る要求の根拠

| 要求 ID | 検証方法 | 根拠 |
|---------|---------|------|
| SRS-SEC-002(機密情報非出力)| レビュー | Inc.1 範囲では患者情報自体を扱わない(§4 SRS-SEC-002 注記)— ログ実装(Inc.4)時に試験へ昇格予定 |
| SRS-IF-001〜005(内部 API)| レビュー + 試験 | API 設計の整合性はレビューで担保、動作試験は IT で網羅(§6.5 ST-IF はレビュー記録)|
| SRS-032(イベント注入 I/F スタブ)| レビュー | Inc.1 では設計レビュー、実機能は Inc.2 で正式化 |
| SRS-UX-001/002(API 設計)| レビュー + 試験(UT) | UT で機能検証済(UT-005.3、§5.5 UTPR)、UX 全体は Inc.4 IEC 62366-1 で正式化 |

### 3.3 試験 ID 体系

| プレフィックス | 観点 | 例 |
|--------------|------|-----|
| `ST-PERF` | 性能要求(全体予算)| `ST-PERF.1-01` |
| `ST-OPS`  | 受入試験 + 運用 | `ST-OPS.1-01` |
| `ST-RCM`  | RCM 統合 + §5.7.4 妥当性確認 | `ST-RCM.1-01` |
| `ST-FUNC` | 機能要求(SRS-001〜032 再確認) | `ST-FUNC.1-01`(骨格)|
| `ST-IF`   | 内部 I/F(レビュー記録)| `ST-IF.1-01`(骨格)|
| `ST-ALM`  | アラーム | `ST-ALM.1-01`(骨格、Inc.2)|
| `ST-SEC`  | セキュリティ | `ST-SEC.1-01`(骨格)|
| `ST-UX`   | ユーザビリティ | `ST-UX.1-01`(骨格、Inc.4)|
| `ST-DATA` | データ永続化 | `ST-DATA.1-01`(骨格)|

## 4. 試験方針

### 4.1 試験戦略 — 「代表 3 観点詳細化 + 残骨格 6 観点」段階成熟方式

ITPR v0.1(Step 19 D-2 で確立)/ UTPR v0.1(Step 19 A で確立)と同じ漸進パターンを採用:

1. **本 v0.1(Step 19 G):** 代表 3 観点(ST-PERF / ST-OPS / ST-RCM)を詳細化、試験ケース数目安と試験設計を確定。残 6 観点(ST-FUNC / ST-IF / ST-ALM / ST-SEC / ST-UX / ST-DATA)は試験観点・関連 SRS のみ記述する骨格。
2. **Step 19 H(Inc.1 完了タグ前):** 代表 3 観点の試験実施 + §11.2 報告 + §13 トレース確定 + §5.7.4 妥当性確認チェックリスト記録。Inc.1 範囲完結。
3. **Inc.2〜Inc.4(後続インクリメント):** 残 6 観点のうち各インクリメントで該当する観点を詳細化(Inc.2 で ST-ALM、Inc.4 で ST-UX、各 Inc 完了時に §11.2 / §13 確定)。
4. **M_final(全 Inc.統合):** 全 ST 観点の最終確認 + リリース判定への入力(SDP §4.4)。

### 4.2 試験種別と本 STPR のカバー

| 種別 | 目的 | 本 STPR の §6.x | Inc.1 範囲 |
|------|------|---------------|----------|
| 機能試験 | SRS-001〜032 機能要求 | §6.4 ST-FUNC(骨格)| UT/IT で網羅、ST 再確認 |
| 性能試験 | SRS-P01〜P07 全体予算 | §6.1 ST-PERF(代表)| **詳細化**(Inc.1 範囲 5 件)|
| 負荷・ストレス試験 | SRS-P07 24 時間連続運転 | §6.1 ST-PERF.1-05(代表 / 推奨要求)| 詳細化(SRS-P07 のみ Inc.1 範囲)|
| 異常系試験 | エラー時の安全動作(SRS-027 フェイルセーフ起動)| §6.3 ST-RCM(代表)| **詳細化**(RCM 統合)|
| ユーザビリティ試験 | SRS-UX-* + IEC 62366-1 | §6.8 ST-UX(骨格)| Inc.4 正式化 |
| セキュリティ試験 | SRS-SEC-* | §6.7 ST-SEC(骨格)| pip-audit 自動化済(IT 系)|
| RCM 試験 | 全 RCM の有効性(IEC 62304 §5.7.4 妥当性確認)| §6.3 ST-RCM(代表)| **詳細化**(Inc.1 全 6 RCM)|
| インストール・アップデート試験 | SRS-OPS-001〜004 受入試験 | §6.2 ST-OPS(代表)| **詳細化**(SRS-OPS-004 必須)|

### 4.3 試験環境

| 区分 | 内容 |
|------|------|
| ターゲット | 仮想輸液ポンプシミュレータ(VIP-SIM-001、`pip install` で導入された VIP-CTRL を CLI `vip-ctrl` で起動)|
| OS / ランタイム | Python 3.12、Linux runner(GitHub Actions `ubuntu-latest`)を主、ローカル macOS 開発用も検証 |
| 実機 / HILS | 本プロジェクトはシミュレータ実装のため実機なし(`vip_sim.PumpSimulator` が物理ポンプの数学モデル)|
| 計測機器 | `time.perf_counter_ns()`、`pytest-benchmark`(F5 で SOUP-012 採用)、`statistics.median` |
| ソフトウェアバージョン | Inc.1 完了タグ `v0.1.0-inc1`(予定、Step 19 H 付与時)、SHA で固定 |
| 試験者 | k-abe(単独開発、独立性擬制は CCB-VIP-001 §5.4 + SRMP §3.2 で機械的検証 + 1 分インターバルで担保)|

### 4.4 自動化方針

- **代表 3 観点(ST-PERF / ST-OPS / ST-RCM)はすべて pytest 自動化**(`tests/system/` 配下に新設予定、Step 19 H で実装)。
- ST-OPS は SRS-OPS-004 で「CI で自動実行」が必須要求のため、`.github/workflows/system-test.yml` を Step 19 H で新設(IT と同じ runner 戦略)。
- 実時間性能試験(ST-PERF)は **Linux nightly schedule + `linux_only` auto-skip hook**(Step 19 F5 で先取り実装、F6/F7 で再利用済の機構を STPR でも継続再利用)で安定性確保。
- ST-RCM は F1〜F6 IT の **システムレベル再現** が中心のため、CI 高速ジョブ(`integration-fast` 相当の `system-fast`)で実行。

## 5. ソフトウェア問題解決プロセスの使用(箇条 5.7.2)

- 試験中に発見された不具合は、**SPRP-VIP-001 §5(問題解決手順)** に従って `PRB-NNNN` で記録・分析・是正する(`PR-` ではなく `PRB-` を使用、CLAUDE.md「ID 体系の本プロジェクト固有規則」)。
- 是正に伴うソフトウェア変更は、**SCMP-VIP-001 §4.1(変更区分判定)+ CCB-VIP-001 §5.4(1 分インターバル)** に従い CR を起票し、影響範囲評価 → 該当試験再実行を行う。
- 変更管理記録(CR-NNNN ID、影響評価、再試験結果)は CRR-VIP-001 に記録、本 STPR §11.4 回帰試験結果欄に紐付ける。

## 6. 変更後の再試験(箇条 5.7.3)

### 6.1 ST-PERF — 性能要求(全体予算)— **詳細化(Step 19 G、代表観点 1)**

#### 6.1.1 試験観点

- **目的:** SRS-P01〜P07 のうち **必須要求**(SRS-P01 / P03 / P04)+ **推奨要求**(SRS-P05 / P07)の **全体予算** を、結合済み VIP-CTRL の **CLI `vip-ctrl` 起動 + シミュレータ全層動作状態** で測定する。F5 で確立した「IT は SDD 内訳 / ST は SRS 全体」分散配置に従い、本 §6.1 では SDD 内訳ではなく **SRS の最終的な全体予算で合否判定** する。
- **関連 SRS:** SRS-P01(流量精度 ±5%)、SRS-P03(start 全体 ≤ 500 ms)、SRS-P04(stop 全体 ≤ 200 ms)、SRS-P05(起動時間 ≤ 3 秒)、SRS-P07(24 時間連続運転、SRS-P01 維持)
- **関連 RCM:** RCM-004(送出間隔)— SRS-P02 ジッタは IT 検証(ITPR §6.3 / §6.8)、本 ST では SRS-P01 精度の 24 時間維持(SRS-P07)で RCM-004 の長期挙動を確認
- **関連 HZ:** HZ-001(過量投与 / 過少投与)、HZ-002(注入停止失敗)
- **環境制約:** SRS-P01 / P05 は CI 共有環境でも安定測定可能。SRS-P03 / P04 は実時間ジッタ影響あり → `linux_only` auto-skip hook(F5 / F6 / F7 から継続再利用)。SRS-P07(24 時間)は **Linux nightly + 専用 runner** で Inc.1 完了タグ後に実施(Step 19 H 申し送り)。

#### 6.1.2 試験ケース一覧(全 5 件、Inc.1 範囲)

| 試験 ID | 内容 | 入力 | 期待結果 | 合格基準 |
|---------|------|------|---------|---------|
| ST-PERF.1-01 | SRS-P01 流量精度 ±5%(IEC 60601-2-24 相当)| `vip-ctrl` で flow_rate=60.0 mL/h, dose=60.0 mL, duration=60 min を設定 + start | 30 サンプル(各 1 分間)の累積流量が ±5% 内 | median(累積流量誤差 / 期待値) ≤ 5% |
| ST-PERF.1-02 | SRS-P03 start 全体応答 ≤ 500 ms | IDLE 状態で `vip-ctrl --command start` を発行 | 30 サンプルの start コマンド受領 → RUNNING 遷移 + 第 1 回 dispatch までの経過時間 P95 ≤ 500 ms | P95 ≤ 500 ms(SDD §4.7.E 内訳 100 ms は IT、ST は SRS 全体)|
| ST-PERF.1-03 | SRS-P04 stop 全体応答 ≤ 200 ms | RUNNING 状態で `vip-ctrl --command stop` を発行 | 30 サンプルの stop コマンド受領 → STOPPED 遷移 + dispatch 停止までの経過時間 P95 ≤ 200 ms | P95 ≤ 200 ms(SDD §4.7.A ファストパス 50 ms は IT、ST は SRS 全体)|
| ST-PERF.1-04 | SRS-P05 起動時間 ≤ 3 秒 | `vip-ctrl` プロセス開始 → IDLE 状態到達まで | 10 サンプルの subprocess.Popen 起動時刻 → 内部 IDLE 到達時刻の経過 | median ≤ 3 秒 |
| ST-PERF.1-05 | SRS-P07 24 時間連続運転 + SRS-P01 維持(推奨)| 24 時間 RUNNING 連続運転、累積流量を全期間記録 | 24 時間時点で SRS-P01(±5%)を維持 | 全期間 median 流量精度 ≤ 5%、ERROR 状態への意図せぬ遷移なし(**Inc.1 完了タグ後の専用 runner で実施申し送り**)|

#### 6.1.3 試験技法

- **計測:** subprocess.Popen で `vip-ctrl` 起動 → CLI 標準入力でコマンド発行 → 標準出力(JSON Lines、SRS-OPS-010)で状態変化観測、`time.perf_counter_ns()` で経過時間記録
- **統計:** F5 IT-PERF パターン継続(median + P95 + ウォームアップ破棄、F7 で 200 サンプル × ウォームアップ 20 件、ST-PERF では 30 サンプル × ウォームアップ 5 件で経過時間計測)
- **マーカー:** `@pytest.mark.system` + `@pytest.mark.linux_only`(Step 19 H で `system` マーカーを `pyproject.toml` に追加予定)+ ST-PERF.1-05 のみ `@pytest.mark.nightly`

#### 6.1.4 設計判断(Step 19 G 着手中)

- **F5 確立分散配置の活用:** Step 19 F5 で「SRS-P03/P04 全体予算 vs SDD 内訳予算」の解釈差を発見し「IT は SDD 内訳 / ST は SRS 全体」と分散配置。本 §6.1 はこの分散配置の **「ST は SRS 全体」フェーズの正式実装**。F5 申し送り(STPR で明文化予定)を本 STPR §1.2 で明文化済。
- **Inc.1 範囲での性能必須要求の集中検証:** SRS-P01 / P03 / P04 は **必須**(SRS §4.3 性能要求テーブル)で Inc.1 完了タグ前に ST 検証必須。SRS-P02(ジッタ 10%)は IT 範疇(F5 IT-PERF.1-01)、SRS-P06(永続化非ブロッキング)は IT 範疇(F5 IT-PERF.3-02)で本 ST 範囲外。SRS-P05 / P07 は **推奨** だが Inc.1 範囲で実施可能 → 本 §6.1 に含める。
- **SRS-P07 24 時間試験の専用 runner 申し送り:** GitHub Actions 標準 runner は 6 時間 timeout、24 時間連続試験は実機環境または self-hosted runner が必要。Inc.1 完了タグ後の **Step 19 H 申し送り** として ITPR §6.10.5(F7 申し送り)と同じパターンで記録。

#### 6.1.5 申し送り(Step 19 H2 完了時点で更新)

- **Inc.1 範囲で実装済(`tests/system/test_perf_acceptance.py`、Step 19 H2):** ST-PERF.1-04(SRS-P05 起動時間 ≤ 3 秒)— `vip-ctrl --version` を 10 サンプル subprocess で起動 + `time.perf_counter` で wall-clock 経過時間を median 統計判定、`installed_venv` session fixture で venv 構築 + `pip install -e .` を 1 回償却。
- **Inc.4 申し送り(ISS-H-002 拡張、Step 19 H2 着手中の発見、`pytest.mark.skip`):** ST-PERF.1-01(SRS-P01 流量精度)/ ST-PERF.1-02(SRS-P03 start)/ ST-PERF.1-03(SRS-P04 stop)— **Inc.1 CLI は対話 flow_rate / start / stop コマンドを提供しない**(SDD §3 設計方針 + Step 19 H1 で確定:対話 UI は Inc.4 UI 層実装)。F5 IT-PERF で SDD 内訳予算(SDD §4.7.E 100 ms / §4.7.A 50 ms)を統計検証済 → ST 全体予算判定は Inc.4 で正式実装。本 H2 では `pytest.mark.skip(reason=…)` で 16 ケース構造を保持しつつ Inc.4 実装時の合流先を明示。
- **Inc.1 完了タグ後申し送り(`pytest.mark.skip`):** ST-PERF.1-05(SRS-P07 24 時間連続運転)— GitHub Actions 標準 runner の 6 時間 timeout を超えるため、self-hosted runner または別途実機環境で実施。`v0.1.0-inc1` タグ付与後の **Inc.1 後追い試験** として記録(SDP §4.4 リリース判定への遅延入力)。本ケースは Inc.4 でなく Inc.1 完了タグ後の即時実施対象。

### 6.2 ST-OPS — 受入試験 + 運用 — **詳細化(Step 19 G、代表観点 2)**

#### 6.2.1 試験観点

- **目的:** SRS-OPS-001〜004 の **インストール・起動・受入試験(必須)** + SRS-OPS-010〜012 の **運用・診断・アップデート(推奨)** が `pip install` 後の実環境で機能することを End-to-End で検証する。SRS-OPS-004 は「CI で自動実行」を必須要求としているため、本 §6.2 試験は **`.github/workflows/system-test.yml` で全 PR / push に対して自動実行** されることが要求される。
- **関連 SRS:** SRS-OPS-001(`pip install` で導入)、SRS-OPS-002(CLI `vip-ctrl` 起動)、SRS-OPS-003(初回起動デフォルト動作)、SRS-OPS-004(CI 自動受入試験)、SRS-OPS-010(JSON Lines ログ)、SRS-OPS-011(`--diagnose`)、SRS-OPS-012(`pip install --upgrade`)
- **関連 RCM:** —(運用要求のため RCM 直接対応なし、ただし SRS-OPS-003 の「IDLE / 流量 0 / 積算 0 デフォルト」は SRS-027 フェイルセーフ起動と整合)
- **関連 HZ:** HZ-007(永続記録破損時の SRS-OPS-003 デフォルト動作で安全側起動)

#### 6.2.2 試験ケース一覧(全 5 件、Inc.1 範囲)

| 試験 ID | 内容 | 入力 | 期待結果 | 合格基準 |
|---------|------|------|---------|---------|
| ST-OPS.1-01 | SRS-OPS-001 + 002 インストールから CLI 起動まで | クリーン venv → `pip install -e .` → `vip-ctrl --version` 実行 | 戻り値 0 + バージョン出力 | exit code 0 |
| ST-OPS.1-02 | SRS-OPS-003 初回起動時のデフォルト動作 | クリーン環境(永続レコードなし)で `vip-ctrl` 起動 | 状態 = IDLE / 流量 = 0 / 積算量 = 0 で起動 | `--diagnose` または初期出力で確認 |
| ST-OPS.1-03 | SRS-OPS-010 JSON Lines ログ最低項目(**Step 19 H2 で簡略化、ISS-H-002**)| 通常起動 + `--diagnose` の 2 経路を起動(対話 start / stop は Inc.4 申し送り)| 両経路の stdout が JSON Lines 形式、各行に `timestamp / level / component / event / details` を含む | 全行が `json.loads` 可、5 必須キー全件存在(対話シナリオは Inc.4 で網羅)|
| ST-OPS.1-04 | SRS-OPS-011 `--diagnose` 出力 | `vip-ctrl --diagnose` 実行(永続レコード存在状態)| 現在状態 / 積算量 / 永続レコード整合性が出力 | 標準出力が想定 schema を満たす(SRS-OPS-011 推奨)|
| ST-OPS.1-05 | SRS-OPS-012 アップデートインプレース | venv に v0.1.0-inc0(架空)→ `pip install --upgrade` で v0.1.0-inc1 → 永続レコード保持確認 | アップデート後も既存永続レコードが整合性維持で読込可能 | `--diagnose` で整合性 OK |

#### 6.2.3 試験技法

- **subprocess + venv 隔離:** 各試験ケースは `tempfile.TemporaryDirectory` で隔離 venv を構築 → `pip install -e .` → `subprocess.Popen([sys.executable, "-m", "vip_ctrl", ...])` で CLI 起動。F6 IT-PWR の subprocess パターン(`_pwr_child_helper.py` 経由の精密同期)とは異なり、本 §6.2 は「実 CLI 経由の正常動作」確認が目的のため標準 stdin / stdout 経路で対話。
- **CI 統合:** `.github/workflows/system-test.yml` を Step 19 H で新設、`integration-fast` 同等の Linux runner で全 PR / push 実行(SRS-OPS-004 必須要求)。

#### 6.2.4 設計判断

- **CLI エントリポイントの実装が前提:** 本 §6.2 試験は VIP-CTRL に CLI エントリポイント `vip-ctrl` が実装されていることを前提とする。Inc.1 範囲での CLI 実装は SRS-OPS-002 必須要求のため Step 19 H と並行して実装する(現時点では未実装、申し送り対象)。
- **CLI 未実装時の代替試験:** Step 19 H 着手時に CLI が未実装の場合、Inc.1 完了タグ前に **(a)** CLI 実装を Inc.1 完了の必須前提条件として追加、または **(b)** ST-OPS を Inc.1 後追い試験として申し送り(SDP §4.4 リリース判定遅延入力)、の判断を行う。

#### 6.2.5 申し送り(Step 19 H2 完了時点で更新)

- **CLI エントリポイント `vip-ctrl` 実装済(Step 19 H1):** `src/vip_ctrl/cli.py` 新規(78 stmt / 10 branch、`--version` / `--diagnose` / デフォルト 3 経路)+ `pyproject.toml` `[project.scripts]` 登録 + UNIT-005.4 UT 15 ケース(`tests/unit/test_cli.py`、CLI 100% カバレッジ + MC/DC 100%)。SDD v0.4 §4.18 で正式記載済、ISS-H-001 解消。
- **Inc.1 範囲で実装済(`tests/system/test_ops_acceptance.py`、Step 19 H2):** ST-OPS.1-01(クリーン venv → `pip install -e .` → `vip-ctrl --version`)/ ST-OPS.1-02(永続レコード不在で IDLE / 0 / 0 起動 = HZ-007 安全側起動)/ ST-OPS.1-03(JSON Lines 5 必須キー網羅、**ISS-H-002 で対話 start / stop 要求を非対話シナリオへ簡略化** = boot_snapshot + diagnose 2 経路で網羅、対話経路は Inc.4 で再評価)/ ST-OPS.1-04(整合レコードに対する `--diagnose` で `integrity_ok=true`)/ ST-OPS.1-05(`pip install --upgrade -e .` 再実行で永続レコード保持を簡略実証、Inc.2+ で旧 → 新版マイグレーション正式試験に拡張)。全 5 件 Pass。
- **CI ワークフロー `.github/workflows/system-test.yml` 新設済(Step 19 H2):** `system-fast`(PR / push)+ `system-nightly`(scheduled、`workflow_dispatch`)の 2 ジョブ構成、`pytest -m system` で本 §6.2 全 5 件を含む system テスト 16 ケース実行。SRS-OPS-004「CI で自動実行」必須要求を満たす。
- **`tests/system/` ディレクトリ新設済(Step 19 H2):** `__init__.py` + `conftest.py`(session-scoped `installed_venv` fixture + 永続レコードヘルパ)+ `test_perf_acceptance.py` + `test_ops_acceptance.py` + `test_rcm_acceptance.py`。

### 6.3 ST-RCM — RCM 統合検証 + IEC 62304 §5.7.4 妥当性確認 — **詳細化(Step 19 G、代表観点 3)**

#### 6.3.1 試験観点

- **目的:** Inc.1 範囲全 RCM(RCM-001 / RCM-003 / RCM-004 / RCM-015 / RCM-016 / RCM-019 = SRS-RCM-020)が **VIP-CTRL システム全体動作状態(`vip-ctrl` CLI 経由のシミュレータ全層統合)** で機能することを実証する。F1〜F6 ITPR §6.1〜§6.7 / §6.9 で各 RCM を結合状態で検証済 → 本 §6.3 は **システム統合状態での再現性 + IEC 62304 §5.7.4 妥当性確認**(クラス C 必須)を主目的とする。
- **関連 SRS:** SRS-RCM-001(指令範囲)、SRS-RCM-003(SW Watchdog)、SRS-RCM-004(送出間隔)、SRS-RCM-015(起動時整合性)、SRS-RCM-016(再開ガード)、SRS-RCM-020(状態遷移)
- **関連 RCM:** Inc.1 範囲全 6 件
- **関連 HZ:** HZ-001(過量投与)、HZ-002(注入停止失敗)、HZ-007(永続記録破損)

#### 6.3.2 試験ケース一覧(全 6 件、Inc.1 範囲、各 RCM 1 件)

| 試験 ID | 対応 RCM / SRS | 内容 | 期待結果 |
|---------|---------------|------|---------|
| ST-RCM.1-01 | RCM-001 / SRS-RCM-001 | システム動作状態で範囲外 flow_rate(例: -1.0)を CLI 経由で発行 | コマンド拒否 + ログ出力(SRS-ALM-003)、状態遷移なし、`vip-ctrl` プロセス継続(F1 IT-RCM001 の system 再現)|
| ST-RCM.1-02 | RCM-003 / SRS-RCM-003 | システム動作状態で SW Watchdog タイムアウト相当の状況(制御スレッド停止)を意図的に注入 | ERROR 状態遷移 + ログ出力(SRS-ALM-001)、注入停止(F2 IT-RCM003 の system 再現)|
| ST-RCM.1-03 | RCM-004 / SRS-RCM-004 | システム RUNNING で 100 ms ± 10 ms 制御サイクル維持(F5 IT-PERF.1-01 の SDD 内訳精度を ST では SRS-P02 全体精度で再確認)| ログから観測した 30 サイクルの jitter ≤ ±10%(F3 IT-RCM004 の system 再現)|
| ST-RCM.1-04 | RCM-015 / SRS-RCM-015 | 永続レコード(checksum 改ざん)を注入した状態で `vip-ctrl` を起動 | 整合性検証失敗 → SRS-027 フェイルセーフデフォルト起動、ログ出力(SRS-ALM-002)、F6 IT-PWR の system 再現 + IT で扱った subprocess + SIGKILL のシナリオを CLI 経由で再現 |
| ST-RCM.1-05 | RCM-016 / SRS-RCM-016 | 永続レコード(状態 = PAUSED + 積算量 > 0)を注入した状態で `vip-ctrl` を起動 | 自動再開せず、明示的 confirm 待ち状態で起動(SRS-028)、CLI で confirm コマンド発行 → 再開動作 |
| ST-RCM.1-06 | RCM-019 / SRS-RCM-020 | システム動作状態で状態遷移表に反するコマンド(例: STOPPED から start 発行)を発行 | コマンド拒否 + ログ出力(SRS-ALM-003)、状態 = STOPPED 維持 |

#### 6.3.3 IEC 62304 §5.7.4 妥当性確認(クラス C 必須)

| 確認項目 | 確認方法 | 確認結果記入欄(Step 19 H で確定)|
|---------|---------|-----------------------------|
| 試験ケースが SRS を網羅している | §13 トレーサビリティマトリクスで SRS-RCM-* 全件と ST-RCM.1-01〜06 の対応確認 | TBD |
| 試験手順・入力・期待結果が明確かつ再現可能である | §6.3.2 表で各試験 ID に明記、`tests/system/test_rcm_acceptance.py` で実装 | TBD |
| 試験環境が実使用環境を妥当に代表している | VIP-SIM-001 シミュレータは仮想ポンプとして「実使用環境」を代表(SAD §3 設計方針)| TBD |
| 測定機器は校正されており、精度が要求を満たす | `time.perf_counter_ns()` は OS タイマ依存(CI 環境ノイズあり、F5 / F6 / F7 で確立した `linux_only` + median 統計で運用)| TBD |
| 合否判定基準が客観的である | 各 ST-RCM ケースで具体的な数値 / 状態 / ログ出力の確認項目を §6.3.2 で明示 | TBD |
| 不具合検出能力が適切である | F1〜F6 IT で各 RCM の不具合検出能力を実証済(IT-RCM001〜003 / IT-PWR で機能異常を検出可能であることを証明)、ST-RCM はその system 再現 | TBD |

#### 6.3.4 設計判断

- **F1〜F6 IT 結果の system 再現方式採用:** F1〜F6 で各 RCM を結合状態で機能正常性検証済(ITPR §11.2 / §13)。本 §6.3 ST-RCM は **新規試験の詳細化ではなく、F1〜F6 の system レベル再現** を中心とする。これにより重複試験の回避 + IT/ST 分散配置の明確化を実現。
- **§5.7.4 妥当性確認チェックリストの構造化記録:** クラス C 必須要求のため、§6.3.3 のチェックリスト 6 項目を Step 19 H で全件記入することで監査トレーサビリティを担保。

#### 6.3.5 申し送り(Step 19 H2 完了時点で更新)

- **Inc.1 範囲で実装済(`tests/system/test_rcm_acceptance.py`、Step 19 H2):** ST-RCM.1-04(RCM-015 / SRS-RCM-015 起動時整合性 = HZ-007 検出)— `vip-ctrl --diagnose` 経由で破損永続レコード(checksum 改ざん)を Integrity Validator(UNIT-004.1)が `FailsafeRecommended` で検出することを system レベルで実証(JSON `level=warning` + `details.integrity_ok=false` + `details.failure_count >= 1`)。F6 IT-PWR の subprocess + SIGKILL シナリオを CLI 経由検出経路で再現。
- **Inc.4 申し送り(ISS-H-002 拡張、Step 19 H2 着手中の発見、`pytest.mark.skip`):** ST-RCM.1-01(RCM-001 範囲外コマンド)/ ST-RCM.1-02(RCM-003 SW Watchdog)/ ST-RCM.1-03(RCM-004 制御サイクル jitter)/ ST-RCM.1-05(RCM-016 再開ガード)/ ST-RCM.1-06(RCM-019 状態遷移違反)— **いずれも Inc.1 CLI に対話コマンド経路が無い**(start / stop / flow_rate / confirm)ため再現不可。**F1〜F6 IT で各 RCM の不具合検出能力は実証済**(IT-RCM001〜003 / IT-PWR / IT-SEP / IT-SIDE)、§5.7.4 妥当性確認(クラス C 必須)の「不具合検出能力が適切である」項目は IT 結果から transitive に満たす(§6.3.3 表で記録)。Inc.4 UI 層実装時に CLI 経由 system 再現を正式実装。
- **§5.7.4 妥当性確認の Inc.1 範囲完結:** Inc.1 範囲全 RCM(6 件)のうち RCM-015 を Step 19 H2 で system 再現済、残 5 RCM の system 再現は Inc.4 申し送り。Inc.2 以降の追加 RCM(RCM-017 / RCM-018 等)は該当 Inc 完了時に追記。**Step 19 H3** で §6.3.3 チェックリスト 6 項目を全件記入し Inc.1 完了タグ前の妥当性確認を確定する。

### 6.4 ST-FUNC — 機能要求(SRS-001〜032 再確認)— **骨格**

- **目的:** SRS-001〜032 の機能要求が VIP-CTRL システム全体動作で機能することを再確認する。SRS-001〜005(設定値受付)は UT で網羅、SRS-010〜014(コマンド処理)+ SRS-020(状態遷移)+ SRS-021(状態遷移ログ)+ SRS-025〜028(永続化)+ SRS-030〜032(仮想ポンプ)は IT で網羅済。
- **関連 SRS:** SRS-001〜032
- **試験ケース数目安:** ≥ 8 件(各機能カテゴリの代表 1 件、UT/IT で扱えなかった E2E シナリオ重視)
- **実装予定:** Inc.1 範囲は UT/IT で網羅済のため Inc.1 完了タグ前は申し送り。Inc.4(UI 層)で正式詳細化予定(UI 経由のシナリオ試験が中心となる)。
- **Step 19 H 申し送り:** §13 トレース確認(SRS-001〜032 全件が UT/IT/ST いずれかで網羅されていること)。

### 6.5 ST-IF — 内部 I/F(レビュー記録)— **骨格**

- **目的:** SRS-IF-001〜005 の内部 API がレビュー基準(IEC 62304 §5.7.1 で「試験以外の検証」を選定した要求)を満たすことを記録する。
- **関連 SRS:** SRS-IF-001(仮想 HW I/F)、SRS-IF-002(制御 API)、SRS-IF-003(状態観測 API)、SRS-IF-004(ロギング I/F)、SRS-IF-005(永続化 I/F)
- **試験ケース数目安:** レビュー記録 5 件(各 SRS-IF 1 件、レビュー実施日 + 確認者 + 結果のみ記録)
- **実装予定:** Inc.1 範囲は IT で各 IF-U 動作試験済、本 §6.5 はレビュー記録のみで Step 19 H で記入。

### 6.6 ST-ALM — アラーム(IEC 60601-1-8 連携)— **骨格**

- **目的:** SRS-ALM-001〜003 のアラーム要求 + IEC 60601-1-8 アラームシステム規格との整合性を検証する。
- **関連 SRS:** SRS-ALM-001(致命的内部エラー)、SRS-ALM-002(整合性検証失敗)、SRS-ALM-003(不正コマンド拒否)
- **試験ケース数目安:** ≥ 4 件(Inc.2 で詳細化、Inc.1 はスタブ I/F SRS-O-040 のレビュー)
- **実装予定:** **Inc.2 アラーム正式化時に詳細化**、Inc.1 はスタブ I/F のレビュー記録のみ(ST-ALM.1-01 として Step 19 H で記入)。

### 6.7 ST-SEC — セキュリティ — **骨格**

- **目的:** SRS-SEC-002(機密情報非出力)+ SRS-SEC-003(pip-audit による既知脆弱性検出)が機能することを検証する。SRS-SEC-001(チェックサム改ざん検知)は UT/IT で検証済(F7 IT-SIDE で定数時間性も検証済)。
- **関連 SRS:** SRS-SEC-002(機密情報非出力 / Inc.1 では患者情報非取扱のためレビュー)、SRS-SEC-003(pip-audit / `.github/workflows/integration-test.yml` で自動化済)
- **試験ケース数目安:** ≥ 2 件(レビュー 1 件 + CI 確認 1 件)
- **実装予定:** SRS-SEC-003 は CI ジョブ実行確認で済、SRS-SEC-002 は Inc.4 ロギング実装時に詳細化(Inc.1 はレビュー記録)。

### 6.8 ST-UX — ユーザビリティ(IEC 62366-1 連携)— **骨格**

- **目的:** SRS-UX-001(`validate(settings)` 提供)+ SRS-UX-002(状態観測 API 副作用なし)+ IEC 62366-1 ユーザビリティエンジニアリングとの整合性を検証する。Inc.1 範囲では UI が存在しないため API 設計レビュー中心、Inc.4(UI 層)で IEC 62366-1 正式試験を実施する。
- **関連 SRS:** SRS-UX-001、SRS-UX-002
- **試験ケース数目安:** ≥ 4 件(Inc.4 で詳細化、Inc.1 は API レビュー 2 件 + UT 既存試験参照 2 件)
- **実装予定:** **Inc.4 UI 層実装時に詳細化**、Inc.1 は SRS-UX-001/002 の API 設計レビュー記録のみ(SRS-UX-001 = UNIT-005.3 Validation API / SRS-UX-002 = UNIT-005.2 State Observer API、UTPR §7.3.16 / §7.3.17 で既に試験済)。

### 6.9 ST-DATA — データ永続化 — **骨格**

- **目的:** SRS-DATA-001〜004(永続レコードのスキーマ + atomic write + 1 世代 backup + schema version)が VIP-CTRL システム全体動作で機能することを検証する。UT(UNIT-003.* + UNIT-004.1)+ IT(F6 IT-PWR / F7 IT-SIDE)で各構成要素を検証済。
- **関連 SRS:** SRS-DATA-001(JSON + checksum)、SRS-DATA-002(atomic write)、SRS-DATA-003(1 世代 backup)、SRS-DATA-004(schema version)
- **試験ケース数目安:** ≥ 4 件(各 SRS-DATA 1 件、F6 IT-PWR の system 再現)
- **実装予定:** Step 19 H で `tests/system/test_data_persistence.py` を新規実装、F6 IT-PWR の `subprocess.Popen + SIGKILL` シナリオを `vip-ctrl` CLI 経由で再現する system レベル試験。

## 7. ソフトウェアシステム試験の妥当性確認(箇条 5.7.4 ― クラス C)

クラス C 必須要求のため、本 §7 は試験自体の妥当性を独立に確認する記録を残す。

### 7.1 計画レビューチェックリスト

- [ ] 計画が SRS / SAD / SDD / RMF / ITPR / UTPR と整合している(§2 参照文書、§6 試験観点)
- [ ] 各試験ケースが期待結果・合格基準を明示している(§6.1〜§6.3 詳細化済 + §6.4〜§6.9 骨格、Inc.1 範囲は §6.1〜§6.3 で代表 3 観点詳細化)
- [ ] 試験が再現可能である(§4.4 自動化方針、`pytest` ベース、CI 自動実行)
- [ ] リスクコントロール手段(全 RCM 6 件)を検証するケースが含まれている(§6.3 ST-RCM)
- [ ] SRS 必須要求が試験対象として網羅されている(§13 トレーサビリティマトリクス)
- [ ] 試験環境が実使用環境を妥当に代表している(§4.3、VIP-SIM-001 シミュレータ)
- [ ] 合否判定基準が客観的である(各 §6.x.2 試験ケース表に明記)
- [ ] §5.7.4 妥当性確認チェックリスト(§6.3.3)が記入されている(**Step 19 H で記入予定**)

### 7.2 妥当性確認の記録

| 項目 | 結果 | 確認者 | 日付 |
|------|------|-------|------|
| §6.3.3 §5.7.4 チェックリスト 6 項目 | TBD(Step 19 H で記入)| k-abe | TBD |

## 8. 試験対象および試験 ID 体系

### 8.1 自動化方針(再掲、§4.4 詳細)

- 結合試験 ITPR と独立して、本システム試験は `tests/system/` 配下に配置(Step 19 H で新設)
- `pytest -m system` マーカー指定で他試験と分離実行
- CI ワークフロー `.github/workflows/system-test.yml` を Step 19 H で新設(`system-fast` ジョブ + `system-nightly` ジョブで F5 / F6 / F7 と同パターン)
- ST-PERF.1-05(SRS-P07 24 時間)は self-hosted runner または別途実機環境を申し送り(Step 19 H で詳細決定)

### 8.2 試験 ID 体系(§3.3 再掲)

| プレフィックス | 観点 | 例 | 状態 |
|--------------|------|-----|------|
| `ST-PERF` | 性能要求(全体予算)| `ST-PERF.1-01〜05` | **詳細化済** |
| `ST-OPS`  | 受入試験 + 運用 | `ST-OPS.1-01〜05` | **詳細化済** |
| `ST-RCM`  | RCM 統合 + §5.7.4 妥当性確認 | `ST-RCM.1-01〜06` | **詳細化済** |
| `ST-FUNC` | 機能要求 | `ST-FUNC.1-XX` | 骨格(Inc.4 詳細化)|
| `ST-IF`   | 内部 I/F | `ST-IF.1-XX` | 骨格(Step 19 H 記入)|
| `ST-ALM`  | アラーム | `ST-ALM.1-XX` | 骨格(Inc.2 詳細化)|
| `ST-SEC`  | セキュリティ | `ST-SEC.1-XX` | 骨格(Inc.4 詳細化)|
| `ST-UX`   | ユーザビリティ | `ST-UX.1-XX` | 骨格(Inc.4 詳細化)|
| `ST-DATA` | データ永続化 | `ST-DATA.1-XX` | 骨格(Step 19 H 詳細化)|

## 9. 文書化方針(箇条 5.7.5)

各試験記録(§11.2)には以下を含める:

1. 試験 ID、名称
2. 対象ソフトウェアバージョン / コミット SHA
3. 試験環境(OS / Python / SOUP バージョン / 計測機器)
4. 手順、入力、期待結果(§6.x.2 試験ケース表参照)
5. 実行日、実施者
6. 実測値・観測値、合否
7. 逸脱時の処置、是正(SPRP §5、`PRB-NNNN`)
8. §5.7.4 妥当性確認チェックリスト(§6.3.3)結果

---

# 第 II 部 報告

> **本 v0.1 時点では報告は骨格のみ、実施結果は Step 19 H(Inc.1 完了タグ前)で代表 3 観点(ST-PERF / ST-OPS / ST-RCM)を実施 + 記入する。**

## 10. システム試験記録の内容(箇条 5.7.5)

### 10.1 実施サマリ

- 実施期間: *(Step 19 H 開始時に記入)*
- 実施者: k-abe
- ソフトウェアバージョン(コミット): *(各 ST 実施時点の SHA、Inc.1 完了タグ `v0.1.0-inc1` 付与時に確定)*
- 試験環境バージョン: Python 3.12.x、pytest / pytest-cov / pytest-benchmark 最新安定、Linux runner(`ubuntu-latest`)、self-hosted runner(SRS-P07 24 時間試験用、Step 19 H で決定)
- CI ジョブ: `.github/workflows/system-test.yml` の Run ID(Step 19 H で新設予定)

## 11. 試験実施結果

### 11.1 実施サマリ(§10.1 と同じ)

### 11.2 試験ケース結果(Step 19 H2 で代表 3 観点 16 ケース実装、Pass / Skip 内訳確定)

| カテゴリ | 試験 ID 総数 | Pass | Fail | Skip | 実施日 | コミット SHA |
|---------|----------|------|------|------|-------|-----------|
| ST-PERF(性能、§6.1 詳細化済)| **5**(ST-PERF.1-01〜05)| **1**(ST-PERF.1-04 SRS-P05 起動時間)| 0 | **4**(ST-PERF.1-01/02/03 = Inc.4 申し送り、ST-PERF.1-05 = Inc.1 完了タグ後申し送り)| 2026-05-07 | (Step 19 H2 PR マージコミットで確定)|
| ST-OPS(受入試験、§6.2 詳細化済、SRS-OPS-004 必須)| **5**(ST-OPS.1-01〜05)| **5**(全 Pass:venv インストール + 起動 + JSON Lines + diagnose + upgrade)| 0 | 0 | 2026-05-07 | (Step 19 H2 PR マージコミットで確定)|
| ST-RCM(RCM 統合 + §5.7.4 妥当性確認、§6.3 詳細化済)| **6**(ST-RCM.1-01〜06)| **1**(ST-RCM.1-04 HZ-007 検出)| 0 | **5**(ST-RCM.1-01/02/03/05/06 = Inc.4 申し送り、F1〜F6 IT で機能検証済 → Inc.4 で CLI 経由 system 再現)| 2026-05-07 | (Step 19 H2 PR マージコミットで確定)|
| ST-FUNC(機能要求、§6.4 骨格)| **≥ 8**(Inc.4 詳細化)| TBD | TBD | TBD | TBD | TBD |
| ST-IF(内部 I/F、§6.5 骨格 = レビュー)| **5**(レビュー記録、Step 19 H3 記入)| TBD | TBD | TBD | TBD | TBD |
| ST-ALM(アラーム、§6.6 骨格、Inc.2)| **≥ 4**(Inc.2 詳細化)| TBD | TBD | TBD | TBD | TBD |
| ST-SEC(セキュリティ、§6.7 骨格)| **≥ 2**(Step 19 H3 レビュー + CI 確認)| TBD | TBD | TBD | TBD | TBD |
| ST-UX(ユーザビリティ、§6.8 骨格、Inc.4)| **≥ 4**(Inc.4 詳細化)| TBD | TBD | TBD | TBD | TBD |
| ST-DATA(データ永続化、§6.9 骨格)| **≥ 4**(Step 19 H 詳細化、ST-RCM.1-04 で SRS-DATA-001 部分網羅済)| TBD | TBD | TBD | TBD | TBD |
| **合計**(Inc.1 範囲、§6.1〜§6.3 のみ集計)| **16**(Step 19 G 詳細化 + Step 19 H2 実装)| **7**(Step 19 H2 で確定)| **0** | **9**(Inc.4 申し送り 8 + Inc.1 完了タグ後 1)| 2026-05-07 | (Step 19 H2 PR マージコミット)|

### 11.3 不具合・逸脱

| 問題 ID(PRB) | 発見 ST-ID | 内容 | 重大度 | 対応 | ステータス |
|----------------|-----------|------|-------|------|----------|
| — | — | — | — | — | — |

### 11.4 回帰試験の結果

| 変更 ID(CR / PRB)| 影響を受けた ST | 結果 | 実施日 |
|-------------------|---------------|------|-------|
| — | — | — | — |

## 12. システム試験の総括評価(リリース判定への入力)

> 箇条 5.7 には「試験の総合評価」の独立項は存在しないが、リリース判定(SDP §4.4)への入力として以下を記録する。

以下を評価し、Step 19 H で記録する:

- [ ] 試験計画(本 STPR 第 I 部)に従って試験が実行された
- [ ] すべての試験ケースが合格または正当化されている(§5.7.2 SPRP に従う)
- [ ] 試験で発見された問題は ISO 14971 リスクマネジメントへ入力され評価された
- [ ] 未解決問題は既知の残留異常として SMS-VIP-001(§5.8 リリース)に記載されている

評価結論(Step 19 H で記入):

```text
{{合格 / 条件付き合格 / 不合格}}
{{条件付き合格の場合、条件内容を記載}}
```

## 13. トレーサビリティマトリクス(SRS 網羅性、Inc.1 範囲)

> 本 v0.1 時点では §6.1〜§6.3 詳細化分の試験 ID と SRS / RCM / HZ / IT-ID 申し送りの対応を表形式で記録する。骨格 6 観点(§6.4〜§6.9)は試験 ID 範囲のみ示し、Step 19 H 以降のサブステップで具体 ST-ID を充填する。

| 観点 | 試験 ID | 関連 SRS | 関連 RCM | 関連 HZ | 関連 IT-ID(F1〜F7 申し送り)| 検証方法 | 結果 |
|------|--------|---------|---------|---------|----------------------------|---------|------|
| 性能(全体予算)| ST-PERF.1-01〜05(§6.1 詳細化済 Step 19 G + 実装 Step 19 H2)| SRS-P01 / P03 / P04 / P05 / P07 | RCM-004(SRS-P07 経由で長期挙動)| HZ-001、HZ-002 | F5 IT-PERF.1-01/02、2-01/02、3-01/02(SDD 内訳) | 試験(自動)| **Step 19 H2 で 1/5 Pass(ST-PERF.1-04 SRS-P05 起動時間)+ 4/5 Skip(.01/02/03 = ISS-H-002 Inc.4 申し送り、.05 = Inc.1 完了タグ後 self-hosted runner 申し送り)** |
| 受入試験 + 運用 | ST-OPS.1-01〜05(§6.2 詳細化済 Step 19 G + 実装 Step 19 H2)| SRS-OPS-001〜004(必須)、SRS-OPS-010〜012(推奨)| —(運用要求)| HZ-007(SRS-OPS-003 デフォルトで安全側起動)| —(IT で扱わない)| 試験(自動、SRS-OPS-004 「CI で自動実行」必須)| **Step 19 H2 で 5/5 Pass(全件、subprocess + venv 隔離 + CLI 起動経路、`system-test.yml` 新設で SRS-OPS-004 必須要求満足、ST-OPS.1-03 は ISS-H-002 で対話シナリオを非対話シナリオへ簡略化)** |
| RCM 統合(§5.7.4 妥当性確認)| ST-RCM.1-01〜06(§6.3 詳細化済 Step 19 G + 実装 Step 19 H2)| SRS-RCM-001/003/004/015/016/020(Inc.1 全 6 件)| RCM-001/003/004/015/016/019 | HZ-001、HZ-002、HZ-007 | F1 IT-RCM001 / F2 IT-RCM003 / F3 IT-RCM004 / F4 IT-SEP / F5 IT-PERF / F6 IT-PWR | 試験(自動)+ §5.7.4 妥当性確認チェックリスト | **Step 19 H2 で 1/6 Pass(ST-RCM.1-04 RCM-015 / HZ-007 system 再現 = 改ざんレコード `--diagnose` 検出)+ 5/6 Skip(.01/02/03/05/06 = ISS-H-002 Inc.4 申し送り、F1〜F6 IT で機能検証済 → Inc.4 で CLI 経由 system 再現)、§5.7.4 チェックリスト記入は Step 19 H3** |
| 機能要求(再確認)| ST-FUNC.1-XX(§6.4 骨格)| SRS-001〜032 | —(機能要求のため)| —(機能要求のため)| 全 IT カテゴリ | 試験(自動)| 骨格(Inc.4 UI 層詳細化)|
| 内部 I/F | ST-IF.1-01〜05(§6.5 骨格)| SRS-IF-001〜005 | —(I/F 設計)| —(I/F 設計)| —(IT で動作試験済)| レビュー記録 | 骨格(Step 19 H レビュー記録)|
| アラーム | ST-ALM.1-XX(§6.6 骨格)| SRS-ALM-001〜003 + IEC 60601-1-8 | RCM-003、RCM-004 | HZ-002 | —(Inc.1 はスタブ)| 試験(Inc.2 で詳細化)| 骨格(Inc.2 アラーム正式化)|
| セキュリティ | ST-SEC.1-XX(§6.7 骨格)| SRS-SEC-002 / SRS-SEC-003 | —(性能 / 副次品質)| —(Inc.1 脅威モデル外)| F7 IT-SIDE(SRS-SEC-001 関連)| レビュー(SEC-002)+ CI 確認(SEC-003)| 骨格(Step 19 H 記入)|
| ユーザビリティ | ST-UX.1-XX(§6.8 骨格)| SRS-UX-001 / SRS-UX-002 + IEC 62366-1 | RCM-017、RCM-018(Inc.4)| HZ-008(Inc.4)| UT-005.2 / UT-005.3(API 検証済)| レビュー(Inc.1)+ 試験(Inc.4)| 骨格(Inc.4 UI 層詳細化)|
| データ永続化 | ST-DATA.1-XX(§6.9 骨格)| SRS-DATA-001〜004 | RCM-015 | HZ-007 | F6 IT-PWR、F7 IT-SIDE | 試験(自動、F6 IT-PWR の system 再現)| 骨格(Step 19 H 詳細化)|

**カバレッジ:** 本マトリクスにより、Inc.1 範囲の SRS 必須要求(SRS-001〜032、SRS-P01〜P07 のうち必須、SRS-OPS-001〜004、SRS-RCM-* 全件、SRS-SEC-001〜003、SRS-DATA-001〜004)と RCM(全 6 件)が ST 試験 ID と紐付き、SRS / RCM / HZ への双方向トレーサビリティが確立した(v0.1 では §6.1 / §6.2 / §6.3 詳細化分が試験 ID レベル、残骨格は Step 19 H 以降 + Inc.2〜4 で完成)。

## 14. 改訂履歴

| バージョン | 日付 | 変更内容 | 変更者 |
|----------|------|---------|--------|
| 0.2 | 2026-05-07 | **Step 19 H2(代表 3 観点 16 ケース実装 + `system-test.yml` 新設 + ISS-H-002 拡張解消)を反映。** **(1) `tests/system/` 新設**(`__init__.py` + `conftest.py` + `test_perf_acceptance.py` + `test_ops_acceptance.py` + `test_rcm_acceptance.py`、計 16 ケース、`session`-scoped `installed_venv` fixture で venv 構築 + `pip install -e .` を 1 回償却)。**(2) Inc.1 範囲で 7 件 Pass 確定**(ST-PERF.1-04 SRS-P05 起動時間 ≤ 3 秒 / ST-OPS.1-01 venv インストール + `vip-ctrl --version` / ST-OPS.1-02 SRS-OPS-003 デフォルト起動 = HZ-007 安全側起動 / ST-OPS.1-03 SRS-OPS-010 JSON Lines 5 必須キー = boot_snapshot + diagnose 2 経路網羅 / ST-OPS.1-04 SRS-OPS-011 整合レコード `--diagnose` / ST-OPS.1-05 SRS-OPS-012 `pip install --upgrade -e .` 永続レコード保持簡略実証 / ST-RCM.1-04 RCM-015 改ざん永続レコード `--diagnose` 検出 = HZ-007 system 再現)。**(3) Inc.4 申し送り 8 件 + Inc.1 完了タグ後申し送り 1 件 = `pytest.mark.skip` で骨格保持**(ST-PERF.1-01/02/03 + ST-RCM.1-01/02/03/05/06 = ISS-H-002 拡張、Inc.1 CLI が対話 start / stop / flow_rate / confirm を提供しない構造的乖離を H2 着手中に発見、F1〜F6 IT で機能検証済 → Inc.4 UI 層実装時に CLI 経由 system 再現を正式実装 / ST-PERF.1-05 SRS-P07 24 時間連続運転 = self-hosted runner 申し送り、SDP §4.4 リリース判定遅延入力)。**(4) `.github/workflows/system-test.yml` 新設**(`system-fast`(PR / push)+ `system-nightly`(scheduled、`workflow_dispatch`)の 2 ジョブ構成、`integration-test.yml` と同パターン、SRS-OPS-004「CI で自動実行」必須要求満足)。**(5) `pyproject.toml` 拡張**(`system` マーカー新規登録、`addopts` を `not integration and not system` に拡張で UT 実行から system テストを除外、IT / system 分離マトリクスを `pytest -m system` で明示選択)。**(6) ISS-H-002 解消(拡張版):** Step 19 H1 計画時点では ST-OPS.1-03 のみが対話 start / stop 要求の問題と特定されたが、Step 19 H2 着手中の網羅レビューで ST-PERF.1-01/02/03 + ST-RCM.1-01/02/03/05/06 にも同じ構造的乖離(対話コマンド非対応)が存在することを発見 → ISS-H-002 を **計 9 件**(ST-PERF 3 + ST-RCM 5 + ST-OPS.1-03 簡略化 1)に拡張、各ケースで `pytest.mark.skip(reason=…)` に DEVELOPMENT_STEPS.md Step 19 H2 セクションへの相互参照を埋め込んで監査トレーサビリティを担保。**(7) §6.1.5 / §6.2.5 / §6.3.5 申し送りを「Step 19 G 完了時点」 → 「Step 19 H2 完了時点」に更新**、各 ID の Inc.1 範囲実装済 / Inc.4 申し送り / Inc.1 完了タグ後申し送り 3 区分を明示。**(8) §11.2 試験ケース結果テーブルを Pass / Fail / Skip 内訳で確定**(ST-PERF: 1 Pass / 4 Skip、ST-OPS: 5 Pass / 0 Skip、ST-RCM: 1 Pass / 5 Skip = 16 ID 合計 7 Pass / 0 Fail / 9 Skip)。**(9) §13 トレーサビリティマトリクス**(§6.1〜§6.3 詳細化分の 3 行)を「設計確定」 → 「Step 19 H2 で n/m Pass + n/m Skip + 申し送り根拠」に更新、SRS / RCM / HZ への双方向トレーサビリティを実施結果まで延伸。**(10) §5.7.4 妥当性確認チェックリスト**(§6.3.3、6 項目)は Step 19 H3 で全件記入する申し送りを §6.3.5 で明示。**(11) ローカル CI 等価検証 全 Pass:** `pytest -m system` 7 passed / 9 skipped / 501 deselected(macOS local + venv 1 回償却で 45.96 秒)、`mypy --strict` Success(60 source files、+2 = `tests/system/conftest.py` + `test_*.py` 群、CLI session venv ヘルパ追加)、`ruff check . / ruff format --check .` All Pass、UT non-system 462 passed 維持(+system 除外 hook で UT timing 影響なし)、IT non-nightly 27 passed 維持(IT 系列影響なし)。**Step 19 H2 著しい教訓:** (1) **計画フェーズ移行点でのクロスレビューによる ISS 拡張発見**(H1 → H2 移行で ISS-H-002 が 1 件 → 9 件に拡張、Step 19 G 計画時の「対話 UI Inc.4 申し送り」設計判断と Step 19 G STPR §6.x の対話コマンド前提が設計時点では整合確認漏れだった構造的乖離を H2 着手中に網羅レビューで発見、後続プロジェクトでは「フェーズ移行点で全試験ケースの CLI surface 整合を網羅レビュー」運用ルール化推奨)、(2) **`pytest.mark.skip(reason=…)` で 16 ID 構造保持 + Inc.4 合流先明示パターン**(全 skip ケースに F 系列 IT-ID + ISS-H-002 + DEVELOPMENT_STEPS.md セクション + Inc.4 実装時の合流先を埋め込み、監査トレーサビリティを Inc.4 まで延伸)、(3) **session-scoped `installed_venv` fixture による venv 構築 1 回償却**(各テスト個別 venv では合計 5 分超 → session 1 回で 45 秒、F6 IT-PWR の精密 subprocess 同期パターンとは別系統の system test 独自最適化)、(4) **CLI 経由 ST と Python API 経由 IT の分散配置確立**(IT は import 経路の契約整合 / ST は subprocess 経路の SRS 要求網羅、Inc.1 範囲では「CLI surface = 観測可能な system boundary」が小さいため Inc.4 申し送りで対話拡張)。MINOR 区分・CR 不要(SCMP §4.1「軽微」、SRS / SDD / RMF 本体不変、外部 API 変更なし、`system` マーカー追加と `addopts` 拡張は CI 機械化 = 試験運用層の変更で実装には影響しない)| k-abe |
| 0.1 | 2026-05-07 | **初版作成(計画、Step 19 G、F 系列完了 = ITPR §6.1〜§6.10 全 10 観点詳細化済を受けた節目)。** Inc.1 全 17 ユニット UT 完了(UTPR v0.19)+ Inc.1 全 RCM 6 件 IT 検証完了(ITPR v0.10)を前提に、システム試験戦略(SRS 要求網羅 100% + 全 RCM のシステム統合動作 + 性能全体予算 + 受入試験)を確立。**「代表 3 観点詳細化 + 残骨格 6 観点」段階成熟方式**(ITPR v0.1 = Step 19 D-2 / UTPR v0.1 = Step 19 A の確立パターンに整合)で **§6.1 ST-PERF**(性能要求の全体予算、5 ケース、F5 で確立した「IT は SDD 内訳 / ST は SRS 全体」分散配置の正式実装)、**§6.2 ST-OPS**(受入試験 + 運用、5 ケース、SRS-OPS-004 必須要求の CI 自動化)、**§6.3 ST-RCM**(RCM 統合 + IEC 62304 §5.7.4 妥当性確認(クラス C 必須)、6 ケース + チェックリスト 6 項目、F1〜F6 IT 結果の system 再現)を詳細化。残 6 観点(§6.4 ST-FUNC / §6.5 ST-IF / §6.6 ST-ALM / §6.7 ST-SEC / §6.8 ST-UX / §6.9 ST-DATA、合計目安 ≥ 27)は試験観点・関連 SRS のみ記述する骨格(Inc.2 で ST-ALM、Inc.4 で ST-UX、Step 19 H で ST-IF / ST-SEC / ST-DATA を順次詳細化、ST-FUNC は Inc.4 UI 層実装時)。試験 ID 体系(`ST-{プレフィックス}.{サブ番号}-{連番}`)、試験種別 8 区分、自動化方針(`tests/system/` 配下 + `system-test.yml` 新設は Step 19 H)、§5.7.4 妥当性確認チェックリスト(クラス C 必須、§6.3.3 + §7.2)、トレーサビリティマトリクス(SRS / RCM / HZ / IT-ID 申し送り、§13)を確立。**F5 申し送り回収:** ITPR v0.8 §6.8.4 で「IT は SDD 内訳予算 / ST は SRS 全体予算」の分散配置を確立 → STPR で明文化(本 STPR §1.2)、SRS-P03/P04 全体予算は ST-PERF.1-02/03 で SRS 値そのもので合否判定。**Inc.1 完了タグ前申し送り:** Step 19 H で代表 3 観点(ST-PERF / ST-OPS / ST-RCM)の試験実装 + CI ワークフロー新設 + §5.7.4 妥当性確認チェックリスト記入、SRS-P07(24 時間連続運転)は self-hosted runner または別途実機環境で Inc.1 完了タグ後実施申し送り、CLI エントリポイント `vip-ctrl` の実装は Step 19 H と並行(現時点では未実装)。**設計判断:** F1〜F6 IT 結果の system 再現方式採用(重複試験回避 + IT/ST 分散配置の明確化)、CLI 経由 subprocess + venv 隔離方式採用(F6 IT-PWR の精密同期方式とは異なり ST-OPS は実 CLI 経路の正常動作確認が目的)。第 II 部(報告)は骨格のみ、Step 19 H の試験実施で埋めていく(UTPR / ITPR と同じ「代表 + 骨格」段階成熟方式) | k-abe |
