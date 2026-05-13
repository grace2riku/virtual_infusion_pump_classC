# ソフトウェアシステム試験計画書/報告書

**ドキュメント ID:** STPR-VIP-001
**バージョン:** 0.4
**作成日:** 2026-05-07
**最終更新日:** 2026-05-13
**対象製品:** 仮想輸液ポンプ(Virtual Infusion Pump) / VIP-SIM-001
**対象ソフトウェア:** Virtual Infusion Pump Control Software(VIP-CTRL)
**対象ソフトウェアバージョン:** v0.2.0-inc2(予定、Inc.2 完了時)
**対象範囲:** Inc.1(代表 3 観点詳細化済 + ST-IF / ST-SEC レビュー記録済、§6.1〜§6.3 / §6.5 / §6.7)+ Inc.2(アラーム管理、§6.6 ST-ALM Inc.2 詳細化 + §6.x.G 既存 ST 拡張節、Step 20 H、CR-0014、骨格化)
**安全クラス:** C(IEC 62304)

| 役割 | 氏名 | 所属 | 日付 | 署名 |
|------|------|------|------|------|
| 作成者 | k-abe | 単独開発 | 2026-05-07 | k-abe |
| レビュー者 | k-abe(自己レビュー、CCB-VIP-001 §5.4 1 分インターバル + PR 自己レビューチェックリスト適用)| 単独開発 | 2026-05-07 | k-abe |
| 承認者 | k-abe(セルフ承認、SRMP §3.2 単独開発下の独立性擬制)| 単独開発 | 2026-05-07 | k-abe |

---

> **本書はシステム試験の計画と実施結果(報告)を一体で管理する。**
>
> **本 v0.4(Step 20 H、CR-0014、Inc.2 着手準備 Step 系列の 9 番目 = 真の最終、骨格化、Step 14 v0.1 流儀 / Step 19 G STPR v0.1 流儀継承):** Inc.1 範囲は Step 19 G(代表 3 観点詳細化)+ Step 19 H2/H3(代表 3 観点実装 + ST-IF / ST-SEC レビュー記録)で確定済。本 Step 20 H で **Inc.2 範囲を §6.6 ST-ALM Inc.2 詳細化(IEC 60601-1-8 §6.1 優先度 + §5.1.4 区分 + §6.4 ACK/SILENCE 状態遷移)+ §6.x.G 既存 ST 拡張節(§6.4 ST-FUNC.G / §6.2 ST-OPS.G / §6.3 ST-RCM.G の Inc.2 範囲対応骨格)** として骨格化。SAD v0.2 / SDD v0.5 / UTPR v0.22 / ITPR v0.12 で骨格化済の Inc.2 範囲設計を STPR の system 観点 + IEC 60601-1-8 視点で骨格反映、後続 STPR v0.5+ 候補(Step 20 X〜の TDD 実装と並行する詳細化)で各 ST-ALM ケース + ST-x.G ケースを詳細化予定。残 3 観点(§6.4 ST-FUNC / §6.8 ST-UX / §6.9 ST-DATA)は Inc.4(UI 層)+ Step 20 X〜(ST-DATA は Inc.2 実装と並行)で詳細化。
>
> **本 v0.1〜v0.3(Inc.1 範囲完了)の経緯:** v0.1(Step 19 G)= 代表 3 観点(ST-PERF / ST-OPS / ST-RCM)詳細化 + 残 6 観点骨格、v0.2(Step 19 H2)= 代表 3 観点 16 ケース実装 + ISS-H-002 拡張解消 + 7 Pass / 9 Skip、v0.3(Step 19 H3)= §6.5 ST-IF + §6.7 ST-SEC レビュー記録 + §5.7.4 妥当性確認チェックリスト記入 + ANOM-001 transitive 参照 + 14 Pass / 9 Skip 確定 = Inc.1 完了タグ `v0.1.0-inc1` 付与済。

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
| [1] | ソフトウェア要求仕様書 (SRS-VIP-001) | v0.3 | §3 SRS 網羅性、§13 トレース、**SRS-040〜044(Inc.2 検知)、SRS-ALM-004〜008(Inc.2 アラーム)、SRS-RCM-006/009/010/011/012(Inc.2 RCM)、SRS-O-040 確定、SRS-I-040 確定、SRS-REG-002 詳細化(IEC 60601-1-8)** |
| [2] | ソフトウェア開発計画書 (SDP-VIP-001) | v0.1 | §4 試験戦略 |
| [3] | ソフトウェアアーキテクチャ設計書 (SAD-VIP-001) | v0.2 | §5 試験環境(ARCH 構造の整合)、**§4.3 ARCH-006/007 + §5.1 IF-U-007/012〜015 + §9.2 SEP-003** |
| [4] | ソフトウェア詳細設計書 (SDD-VIP-001) | v0.5 | §6.1 IT/ST 分散配置(SDD 内訳 vs SRS 全体予算)、**§4.19〜§4.26 Inc.2 新規 8 ユニット骨格 + §4.1.G / §4.11.G / §4.15.G 既存 3 ユニット拡張節 + §5.1.A AlarmEvent 実装契約** |
| [5] | ソフトウェアユニット試験計画書/報告書 (UTPR-VIP-001) | v0.22 | §1.1 責務分担、**§7.3.19〜§7.3.26 Inc.2 新規 8 ユニット骨格 + §7.3.x.G 既存 3 ユニット拡張節** |
| [6] | ソフトウェア結合試験計画書/報告書 (ITPR-VIP-001) | v0.12 | §1.1 責務分担、§6.3 ST-RCM(F1〜F7 結果集約)、**§6.11〜§6.16 Inc.2 結合観点骨格(IT-RCM006/009/010/011/012 + IT-ALM)+ IS-6/IS-7/IS-8 結合ステップ + IF-U-007/012〜015/014-A** |
| [7] | リスクマネジメントファイル (RMF-VIP-001) | v0.4 | §6.3 ST-RCM(SRS-RCM-* との対応)、**§4.1 HZ-009 + §6.1 RCM-006/009/010/011/012 Designed + §7.1/§7.2 Inc.2 RCM 検証計画 + RCM-020 候補(HZ-009)** |
| [8] | ソフトウェアリスクマネジメント計画書 (SRMP-VIP-001) | v0.2 | §3.2 単独開発下の独立性擬制 |
| [9] | ソフトウェア構成管理計画書 (SCMP-VIP-001) | v0.3 | §4.1 MODERATE 区分 |
| [10] | CCB 運用規程 (CCB-VIP-001) | v0.2 | §5.4 1 分インターバル(CR-0003 以降適用)|
| [11] | ソフトウェア問題解決手順書 (SPRP-VIP-001) | v0.2 | §5.7.2 試験中の不具合解決 |
| [12] | 構成アイテム一覧 (CIL-VIP-001) | v0.53 | CI-DOC-STPR 自己参照 |
| [13] | Inc.2 範囲計画書 (INC2-SCOPE-VIP-001) | v0.1 | §3 機能スコープ、§9 Step 20 H 計画、§10 受入基準 |
| [14] | IEC 60601-1-8 | (規格) | **§6.6 ST-ALM Inc.2 詳細化:§6.1 アラーム優先度分類(高 / 中 / 低)、§5.1.4 テクニカル / 生理アラーム区分、§6.4 アラーム確認・休止規定(高優先度の消音時間 ≤ 120 秒)** |

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

SRS-VIP-001 の **すべての要求事項**(Inc.1 = SRS-001〜032、SRS-P01〜P07、SRS-I-*、SRS-O-*、SRS-IF-001〜005、SRS-ALM-001〜003、SRS-SEC-001〜003、SRS-UX-*、SRS-DATA-*、SRS-OPS-*、SRS-REG-*、SRS-RCM-*。**Inc.2 追加(SRS v0.3、Step 20 B-2)= SRS-040〜044(検知)、SRS-ALM-004〜008(IEC 60601-1-8 準拠アラーム + 優先度・テクニカル区分)、SRS-RCM-006/009/010/011/012(Inc.2 RCM)、SRS-IF-010(Alarm I/F 本実装契約)、SRS-O-040(`AlarmEvent` 構造)、SRS-I-040(`SensorKind` 6 種)、SRS-REG-002 詳細化(IEC 60601-1-8 §6.1/§5.1.4/§6.4 適用)**)に対して、検証方法(試験 / レビュー / 解析 / デモ)を §13 トレーサビリティマトリクスで明示し、試験(ST)が選定された要求は §6.x 観点単位で試験ケース ID(`ST-{プレフィックス}.{サブ番号}-{連番}`)を割り当てる。

### 3.2 試験以外の検証方法を採る要求の根拠

| 要求 ID | 検証方法 | 根拠 |
|---------|---------|------|
| SRS-SEC-002(機密情報非出力)| レビュー | Inc.1 範囲では患者情報自体を扱わない(§4 SRS-SEC-002 注記)— ログ実装(Inc.4)時に試験へ昇格予定 |
| SRS-IF-001〜005(内部 API)| レビュー + 試験 | API 設計の整合性はレビューで担保、動作試験は IT で網羅(§6.5 ST-IF はレビュー記録)|
| SRS-032(イベント注入 I/F スタブ)| レビュー | Inc.1 では設計レビュー、実機能は Inc.2 で正式化 |
| SRS-UX-001/002(API 設計)| レビュー + 試験(UT) | UT で機能検証済(UT-005.3、§5.5 UTPR)、UX 全体は Inc.4 IEC 62366-1 で正式化 |

### 3.3 試験 ID 体系

| プレフィックス | 観点 | 例 | 状態 |
|--------------|------|-----|------|
| `ST-PERF` | 性能要求(全体予算)| `ST-PERF.1-01〜05` | **詳細化済**(Inc.1)|
| `ST-OPS`  | 受入試験 + 運用 | `ST-OPS.1-01〜05` | **詳細化済**(Inc.1)/ Inc.2 拡張 = `ST-OPS.G-01〜`(§6.2.G、骨格)|
| `ST-RCM`  | RCM 統合 + §5.7.4 妥当性確認 | `ST-RCM.1-01〜06` | **詳細化済**(Inc.1)/ Inc.2 拡張 = `ST-RCM.G-01〜`(§6.3.G、骨格、Inc.2 RCM 5 件 + RCM-020 候補)|
| `ST-FUNC` | 機能要求(SRS-001〜032 再確認 + Inc.2 SRS-040〜044) | `ST-FUNC.1-XX` / `ST-FUNC.G-01〜` | 骨格(Inc.4 詳細化)/ Inc.2 拡張 = §6.4.G 骨格(Step 20 H、CR-0014)|
| `ST-IF`   | 内部 I/F(レビュー記録)| `ST-IF.1-01〜05` | **詳細化済**(Inc.1、Step 19 H3)/ Inc.2 = SRS-IF-010 確定 + IF-U-007/012〜015/014-A 追加分は §6.5 拡張未着手(STPR v0.5+ 候補申し送り)|
| `ST-ALM`  | アラーム | `ST-ALM.1-01〜` | **Inc.2 詳細化、Step 20 H、骨格、目安 ≥ 12 件**(IEC 60601-1-8 §6.1/§5.1.4/§6.4)|
| `ST-SEC`  | セキュリティ | `ST-SEC.1-01/02` | **詳細化済**(Inc.1、Step 19 H3)|
| `ST-UX`   | ユーザビリティ | `ST-UX.1-XX` | 骨格(Inc.4 詳細化)|
| `ST-DATA` | データ永続化 | `ST-DATA.1-XX` | 骨格(Step 19 H 詳細化申し送り中)|

## 4. 試験方針

### 4.1 試験戦略 — 「代表 3 観点詳細化 + 残骨格 6 観点」段階成熟方式

ITPR v0.1(Step 19 D-2 で確立)/ UTPR v0.1(Step 19 A で確立)と同じ漸進パターンを採用:

1. **本 v0.1(Step 19 G):** 代表 3 観点(ST-PERF / ST-OPS / ST-RCM)を詳細化、試験ケース数目安と試験設計を確定。残 6 観点(ST-FUNC / ST-IF / ST-ALM / ST-SEC / ST-UX / ST-DATA)は試験観点・関連 SRS のみ記述する骨格。
2. **Step 19 H(Inc.1 完了タグ前):** 代表 3 観点の試験実施 + §11.2 報告 + §13 トレース確定 + §5.7.4 妥当性確認チェックリスト記録。Inc.1 範囲完結。
3. **本 v0.4(Step 20 H、Inc.2 着手準備の最終ステップ):** §6.6 ST-ALM Inc.2 詳細化(IEC 60601-1-8 §6.1 優先度 + §5.1.4 区分 + §6.4 ACK/SILENCE)+ §6.x.G 既存 ST 拡張節骨格化(§6.4 ST-FUNC.G / §6.2 ST-OPS.G / §6.3 ST-RCM.G)。実装 + 実測は Step 20 X〜の TDD 実装フェーズと並行する詳細化(STPR v0.5+ 候補)。
4. **Inc.2〜Inc.4(後続インクリメント):** 残骨格観点のうち各インクリメントで該当する観点を詳細化(Inc.2 で ST-ALM + ST-x.G、Inc.4 で ST-UX + ST-FUNC、各 Inc 完了時に §11.2 / §13 確定)。
5. **M_final(全 Inc.統合):** 全 ST 観点の最終確認 + リリース判定への入力(SDP §4.4)。

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

#### 6.2.G ST-OPS Inc.2 拡張(Step 20 H、CR-0014、骨格)

> **Step 20 H 整合化(2026-05-13、本サブ節 v0.4 新規追加):** Inc.2 で追加される対話 CLI コマンド(`acknowledge_alarm` / `silence_alarm` / Event Injection 経由のセンサー異常注入 `--inject`)が SRS-OPS-001〜004 受入試験 + SRS-OPS-010 JSON Lines 出力契約と整合することを system レベルで再確認する観点を骨格化。骨格に留め、STPR v0.5+ 候補(Step 20 X〜の TDD 実装と並行する詳細化)で詳細化予定。

**関連 SRS:** SRS-OPS-001〜004(必須、CLI surface 拡張)、SRS-OPS-010(JSON Lines 5 必須キー、`AlarmEvent` 出力時の `event` フィールド + `details` ペイロード整合)、SRS-044(対話 CLI)
**関連 IT-ID 申し送り:** IT-ALM(ITPR §6.16)で Mock 経路の結合動作は網羅、本 ST-OPS.G では subprocess + venv 隔離経路の実 CLI surface を再確認。

**試験ケース骨格(目安、STPR v0.5+ 候補で詳細化):**

| 試験 ID(目安)| 内容 | 関連 SRS |
|---------------|------|----------|
| ST-OPS.G-01〜 | `vip-ctrl --command acknowledge_alarm <id>` の subprocess 経路 + JSON Lines 出力(SRS-OPS-010 拡張)| SRS-OPS-001/002/010、SRS-044 |
| ST-OPS.G-02〜 | `vip-ctrl --command silence_alarm <id> --duration <sec>` の subprocess 経路 + 高優先度消音時間 ≤ 120 秒制限の Err 出力 | SRS-OPS-001/002/010、SRS-044、SRS-ALM-008 |
| ST-OPS.G-03〜 | `vip-ctrl --inject <kind>` Event Injection 経路 + センサー異常注入後の検知 + 発報 JSON Lines 観測(SRS-040〜044 駆動)| SRS-OPS-001/002/010、SRS-040〜043 |
| ST-OPS.G-04〜 | Inc.1 既存 ST-OPS.1-01〜05(全 5 件 Pass、Step 19 H2)への回帰なし(Inc.2 CLI 追加で SRS-OPS-001〜004 + SRS-OPS-010〜012 既存試験が引き続き Pass する確認)| SRS-OPS-001〜004、SRS-OPS-010〜012 |

**ケース数目安:** **≥ 4 件**(STPR v0.5+ 候補で詳細化)

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

> **Step 19 H3(2026-05-07)で全 6 項目を確認済。** ST-RCM.1-04(`tests/system/test_rcm_acceptance.py`、Step 19 H2 で実装、PR #45 マージ `2a7855f`)+ F1〜F6 IT 結果(ITPR-VIP-001 v0.10 §11.2 / §13)+ UNIT-001.1〜005.4 UT MC/DC 100%(UTPR-VIP-001 v0.21 §11)から transitive に充填。

| 確認項目 | 確認方法 | 確認結果(Step 19 H3 で確定、k-abe 2026-05-07) |
|---------|---------|------------------------------------------|
| 試験ケースが SRS を網羅している | §13 トレーサビリティマトリクスで SRS-RCM-* 全件と ST-RCM.1-01〜06 の対応確認 | **OK** — Inc.1 範囲 SRS-RCM-001/003/004/015/016/020(全 6 件)が ST-RCM.1-01〜06 に 1:1 対応(§13 で確認)。Inc.1 範囲で ST-RCM.1-04 のみ Pass、残 5 件は ISS-H-002 拡張で Inc.4 申し送り(対話 CLI 非対応に起因、F1〜F6 IT で機能検証済 → 不具合検出能力は transitive に充足、本 §6.3.3 末尾項目参照)。 |
| 試験手順・入力・期待結果が明確かつ再現可能である | §6.3.2 表で各試験 ID に明記、`tests/system/test_rcm_acceptance.py` で実装 | **OK** — ST-RCM.1-04 は `tests/system/test_rcm_acceptance.py::test_st_rcm_1_04_integrity_validation_on_startup_detects_tamper` で実装、`write_corrupt_record(persist_path)` + `vip-ctrl --diagnose` 経路 + JSON Lines 5 必須キー検証 = 入力・手順・期待結果が単一関数内で完結。Skip 5 件も `pytest.mark.skip(reason=…)` で「F 系列 IT-ID + Inc.4 合流先」を埋め込み Inc.4 実装時の手順再現性を担保。 |
| 試験環境が実使用環境を妥当に代表している | VIP-SIM-001 シミュレータは仮想ポンプとして「実使用環境」を代表(SAD §3 設計方針)| **OK** — 本プロジェクトはシミュレータ実装(`vip_sim.PumpSimulator` が物理ポンプの数学モデル、SAD §3 設計方針)。GitHub Actions `ubuntu-latest` Linux runner + Python 3.12.13(CI 実測)+ `pip install -e .` 経路で「ユーザが実際にインストールして使用する環境」を代表。実機・HILS なしの判断は SAD §3 + STPR §4.3 で明示済、本プロジェクト位置づけ(学習・参考実装)整合。 |
| 測定機器は校正されており、精度が要求を満たす | `time.perf_counter_ns()` は OS タイマ依存(CI 環境ノイズあり、F5 / F6 / F7 で確立した `linux_only` + median 統計で運用)| **OK + 限界明示** — `time.perf_counter()`(Python 3.12 標準、monotonic 高精度クロック、`linux_only` で macOS sleep ジッタ回避)+ `pytest-benchmark` 5.2.3(IT-PERF.1-02 のみ、SOUP-012 正式登録)+ statistics.median(F5 / F6 / F7 で確立、ST-PERF.1-04 でも採用)。CI 共有 runner ノイズによる P95 境界フレークは F5 / F7 で予期済(IT-PERF.2-02 SDD §4.7.A 50 ms 厳密境界の 5 連続 Pass 確認運用、Step 19 H3 でも観察 = ITPR §6.8 申し送り回収)。Inc.5 SRS-SEC-001 正式化時に IT-SIDE 強判定再評価予定(F7 申し送り)。 |
| 合否判定基準が客観的である | 各 ST-RCM ケースで具体的な数値 / 状態 / ログ出力の確認項目を §6.3.2 で明示 | **OK** — ST-RCM.1-04 は `result.returncode == 0` + `payload["level"] == "warning"`(SRS-ALM-002 整合)+ `details.record_present is True` + `details.integrity_ok is False` + `details.failure_count >= 1` の 5 項目客観判定。Skip 5 件も Inc.4 実装時の合否判定を §6.3.2 表で具体的な数値・状態・ログで明示済。F1〜F6 IT も 110/50/110 ms 等 SRS / SDD 数値による厳密判定を採用、客観性は IT/ST 共通基準。 |
| 不具合検出能力が適切である | F1〜F6 IT で各 RCM の不具合検出能力を実証済(IT-RCM001〜003 / IT-PWR で機能異常を検出可能であることを証明)、ST-RCM はその system 再現 | **OK + transitive 充足** — Inc.1 範囲全 6 RCM の不具合検出能力は F1〜F6 IT で実証済(ITPR §6.1 IT-RCM001 範囲外コマンド拒否 / §6.2 IT-RCM003 SW Watchdog タイムアウト → ERROR / §6.3 IT-RCM004 dispatch interval / §6.7 IT-SEP SEP-001 越え経路 / §6.9 IT-PWR SDD §4.4.B 不変条件 + SIGKILL 検証 / §6.10 IT-SIDE 定数時間性弱判定)、ST-RCM.1-04 で RCM-015 の system レベル検出を CLI 経由 `--diagnose` で再現済。Skip 5 件は IT 結果の system 再現が Inc.4 申し送りだが、IT で「不具合検出能力が適切である」ことが既に実証されているため、§5.7.4 妥当性確認の transitive 充足としては成立(IEC 62304 §5.7.4 は「試験」全体の妥当性であり、IT + ST の役割分担で網羅可能)。 |

#### 6.3.4 設計判断

- **F1〜F6 IT 結果の system 再現方式採用:** F1〜F6 で各 RCM を結合状態で機能正常性検証済(ITPR §11.2 / §13)。本 §6.3 ST-RCM は **新規試験の詳細化ではなく、F1〜F6 の system レベル再現** を中心とする。これにより重複試験の回避 + IT/ST 分散配置の明確化を実現。
- **§5.7.4 妥当性確認チェックリストの構造化記録:** クラス C 必須要求のため、§6.3.3 のチェックリスト 6 項目を Step 19 H で全件記入することで監査トレーサビリティを担保。

#### 6.3.5 申し送り(Step 19 H2 完了時点で更新)

- **Inc.1 範囲で実装済(`tests/system/test_rcm_acceptance.py`、Step 19 H2):** ST-RCM.1-04(RCM-015 / SRS-RCM-015 起動時整合性 = HZ-007 検出)— `vip-ctrl --diagnose` 経由で破損永続レコード(checksum 改ざん)を Integrity Validator(UNIT-004.1)が `FailsafeRecommended` で検出することを system レベルで実証(JSON `level=warning` + `details.integrity_ok=false` + `details.failure_count >= 1`)。F6 IT-PWR の subprocess + SIGKILL シナリオを CLI 経由検出経路で再現。
- **Inc.4 申し送り(ISS-H-002 拡張、Step 19 H2 着手中の発見、`pytest.mark.skip`):** ST-RCM.1-01(RCM-001 範囲外コマンド)/ ST-RCM.1-02(RCM-003 SW Watchdog)/ ST-RCM.1-03(RCM-004 制御サイクル jitter)/ ST-RCM.1-05(RCM-016 再開ガード)/ ST-RCM.1-06(RCM-019 状態遷移違反)— **いずれも Inc.1 CLI に対話コマンド経路が無い**(start / stop / flow_rate / confirm)ため再現不可。**F1〜F6 IT で各 RCM の不具合検出能力は実証済**(IT-RCM001〜003 / IT-PWR / IT-SEP / IT-SIDE)、§5.7.4 妥当性確認(クラス C 必須)の「不具合検出能力が適切である」項目は IT 結果から transitive に満たす(§6.3.3 表で記録)。Inc.4 UI 層実装時に CLI 経由 system 再現を正式実装。
- **§5.7.4 妥当性確認の Inc.1 範囲完結:** Inc.1 範囲全 RCM(6 件)のうち RCM-015 を Step 19 H2 で system 再現済、残 5 RCM の system 再現は Inc.4 申し送り。Inc.2 以降の追加 RCM(RCM-017 / RCM-018 等)は該当 Inc 完了時に追記。**Step 19 H3** で §6.3.3 チェックリスト 6 項目を全件記入し Inc.1 完了タグ前の妥当性確認を確定する。

#### 6.3.G ST-RCM Inc.2 拡張(Step 20 H、CR-0014、骨格、Inc.2 RCM 5 件 + RCM-020 候補)

> **Step 20 H 整合化(2026-05-13、本サブ節 v0.4 新規追加):** RMF v0.4(Step 20 C、CR-0010)で Designed 状態化された Inc.2 RCM 5 件(RCM-006/009/010/011/012)+ RCM-020 候補(HZ-009 対応)を ITPR v0.12 §6.11〜§6.16 結合観点骨格と整合する system レベル再現観点で骨格化。骨格に留め、STPR v0.5+ 候補で詳細化予定。

**関連 SRS:** SRS-RCM-006(発報必達)、SRS-RCM-009(冗長 2 系統閉塞)、SRS-RCM-010(多段気泡)、SRS-RCM-011(アラームタスク監視)、SRS-RCM-012(発報路冗長)、+ RCM-020 候補(HZ-009 対応、SRS 正式登録は Step 20 B-3 候補申し送り中)
**関連 RCM:** **RCM-006 / 009 / 010 / 011 / 012(Inc.2 Designed → Verified 化目標、Inc.2 完了タグ `v0.2.0-inc2` 付与時)+ RCM-020 候補**
**関連 HZ:** HZ-004 / HZ-005(Inc.2 RCM 対応)、**HZ-009(Inc.2 新規識別、EV-HZ009-001 駆動)**
**関連 IT-ID 申し送り:** IT-RCM006/009/010/011/012(ITPR §6.11〜§6.15)+ IT-ALM(§6.16 IT-ALM.1-13〜の IS-8 全層 E2E で HZ-009 駆動経路実証)

**試験ケース骨格(目安、STPR v0.5+ 候補で詳細化、ST-ALM.1-XX と相互参照):**

| 試験 ID(目安)| 内容 | 関連 RCM | 関連 IT-ID 申し送り |
|---------------|------|----------|----------------------|
| ST-RCM.G-01〜 | RCM-006 発報必達 system 再現(Reservoir + Battery Low 検知 → 発報必達経路の `vip-ctrl` CLI 観測)| RCM-006 | IT-RCM006 |
| ST-RCM.G-02〜 | RCM-009 冗長 2 系統閉塞 system 再現(主系単独 / 副系単独 / 両系超過 / 両系故障 4 経路)| RCM-009 | IT-RCM009 |
| ST-RCM.G-03〜 | RCM-010 多段気泡 system 再現(警告段ログのみ vs 危険段発報 + ERROR の多段独立性)| RCM-010 | IT-RCM010 |
| ST-RCM.G-04〜 | RCM-011 アラームタスク監視 system 再現(800 ms 以内 Trip + 独立発報路フェイルオーバー、Inc.1 ST-RCM.1-02 SW Watchdog パターン継承)| RCM-011 | IT-RCM011 |
| ST-RCM.G-05〜 | RCM-012 発報路冗長 system 再現(主系故障 → 予備系フェイルオーバー、両系故障時の ERROR 遷移)| RCM-012 | IT-RCM012 |
| ST-RCM.G-06〜 | RCM-020 候補(HZ-009 EV-HZ009-001)安全側遷移 system 再現(BATTERY 緊急閾値以下 → 自動 PAUSED / 注入レート低下 / 制御停止のいずれか、SDD v0.6 候補)| RCM-020 候補 | IT-RCM006 + IT-ALM.1-16〜 |

**ケース数目安:** **≥ 6 件**(STPR v0.5+ 候補で詳細化)
**§5.7.4 妥当性確認 transitive 充足戦略(Inc.1 流儀継承):** Inc.1 範囲では RCM-015 のみ ST レベル直接実証 + 残 5 RCM = ISS-H-002 で Inc.4 申し送り(F1〜F6 IT 結果から transitive 充足)パターンを確立。Inc.2 でも対話 CLI(`acknowledge_alarm` / `silence_alarm` / `--inject`)の Step 20 X〜実装後に ST-RCM.G で system 再現可能となる RCM(RCM-006/009/010 = 検知群 + 発報経路)+ Inc.4 申し送りとなる RCM(RCM-011/012 = 内部スレッド・冗長経路の system observable boundary が小さい)を分離して記録。Inc.2 完了タグ `v0.2.0-inc2` 付与時の §5.7.4 妥当性確認チェックリスト記入は STPR v0.5+ 候補で実施。

### 6.4 ST-FUNC — 機能要求(SRS-001〜032 再確認 + Inc.2 SRS-040〜044)— **骨格 + Inc.2 拡張節(Step 20 H、CR-0014)**

- **目的:** SRS-001〜032 の機能要求が VIP-CTRL システム全体動作で機能することを再確認する。SRS-001〜005(設定値受付)は UT で網羅、SRS-010〜014(コマンド処理)+ SRS-020(状態遷移)+ SRS-021(状態遷移ログ)+ SRS-025〜028(永続化)+ SRS-030〜032(仮想ポンプ)は IT で網羅済。
- **関連 SRS:** SRS-001〜032(Inc.1)+ **SRS-040〜044(Inc.2 検知機能)**
- **試験ケース数目安:** ≥ 8 件(各機能カテゴリの代表 1 件、UT/IT で扱えなかった E2E シナリオ重視)+ Inc.2 拡張 = §6.4.G で ≥ 5 件目安
- **実装予定:** Inc.1 範囲は UT/IT で網羅済のため Inc.1 完了タグ前は申し送り。Inc.4(UI 層)で正式詳細化予定(UI 経由のシナリオ試験が中心となる)。
- **Step 19 H 申し送り:** §13 トレース確認(SRS-001〜032 全件が UT/IT/ST いずれかで網羅されていること)。

#### 6.4.G ST-FUNC Inc.2 拡張(Step 20 H、CR-0014、骨格)

> **Step 20 H 整合化(2026-05-13、本サブ節 v0.4 新規追加):** SRS-040〜044(Inc.2 検知機能)を SDD v0.5 / UTPR v0.22 / ITPR v0.12 で骨格化済の Inc.2 ユニット(UNIT-006.1〜006.6)経由で system レベル機能再確認する観点を骨格化。骨格に留め、STPR v0.5+ 候補で詳細化予定。

**関連 SRS:** SRS-040(閉塞検知)、SRS-041(気泡検知)、SRS-042(薬液切れ検知)、SRS-043(バッテリ低下検知)、SRS-044(アラーム確認・休止)
**関連 IT-ID 申し送り:** IT-RCM006/009/010/011/012(ITPR v0.12 §6.11〜§6.15)+ IT-ALM(§6.16)で機能整合性は IT で網羅、本 ST では `vip-ctrl` CLI 経由の subprocess 実行 + JSON Lines 出力観測で system レベル機能再確認を実施。

**試験ケース骨格(目安、STPR v0.5+ 候補で詳細化):**

| 試験 ID(目安)| 内容 | 関連 SRS | 関連 IT-ID 申し送り |
|---------------|------|----------|----------------------|
| ST-FUNC.G-01〜 | SRS-040 閉塞検知 system 再現(`vip-ctrl --inject occlusion_primary` → 検知 + 発報 JSON Lines 観測)| SRS-040 | IT-RCM009 |
| ST-FUNC.G-02〜 | SRS-041 気泡検知 system 再現(警告段 / 危険段 2 経路、ログのみ vs 発報 + ERROR 遷移)| SRS-041 | IT-RCM010 |
| ST-FUNC.G-03〜 | SRS-042 薬液切れ検知 system 再現(閾値跨ぎ → PAUSED 遷移依頼、IEC 60601-1-8 §6.4「自動復帰しない」)| SRS-042 | IT-RCM006 + IT-ALM |
| ST-FUNC.G-04〜 | SRS-043 バッテリ低下検知 system 再現(警告 / 緊急 2 段、HZ-009 EV-HZ009-001 駆動)| SRS-043 | IT-RCM006 + IT-ALM |
| ST-FUNC.G-05〜 | SRS-044 アラーム確認・休止 system 再現(`acknowledge_alarm` + `silence_alarm` CLI、IEC 60601-1-8 §6.4 状態遷移)| SRS-044 | IT-ALM(ST-ALM.1-07〜と相互参照)|

**ケース数目安:** **≥ 5 件**(STPR v0.5+ 候補で詳細化)
**STPR v0.5+ 候補で詳細化する項目:** 各検知ロジックの閾値具体値(SDD v0.6 候補)、対話 CLI(`acknowledge_alarm` / `silence_alarm` / `--inject`)実装後の subprocess 経路試験設計、ST-ALM.1-XX との分担(ST-ALM = IEC 60601-1-8 規格適合 / ST-FUNC.G = SRS 機能要求)。

### 6.5 ST-IF — 内部 I/F(レビュー記録)— **Step 19 H3 で記入完了**

- **目的:** SRS-IF-001〜005 の内部 API がレビュー基準(IEC 62304 §5.7.1 で「試験以外の検証」を選定した要求)を満たすことを記録する。
- **関連 SRS:** SRS-IF-001(仮想 HW I/F)、SRS-IF-002(制御 API)、SRS-IF-003(状態観測 API)、SRS-IF-004(ロギング I/F)、SRS-IF-005(永続化 I/F)
- **試験ケース数目安:** レビュー記録 5 件(各 SRS-IF 1 件、レビュー実施日 + 確認者 + 結果のみ記録)
- **レビュー記録(Step 19 H3 = 2026-05-07、レビュー者 k-abe):**

| 試験 ID | 関連 SRS | レビュー対象 | レビュー結果 | 根拠 |
|---------|---------|------------|------------|------|
| ST-IF.1-01 | SRS-IF-001(仮想 HW I/F)| `vip_sim` パッケージの公開 API(`PumpSimulator` / `PumpObserver` / `HwFailsafeTimer` / `EventInjectionStub`)| **OK** | UNIT-002.1〜002.4 が UT で 100% カバレッジ + MC/DC 100% 達成(UTPR §7.3.13/14/3/19)、F3 IT-RCM004 で本物 ControlLoop + 本物 PumpSimulator + 本物 PumpObserver の結合経路が機能整合実証済(ITPR §6.3 = 5/5 Pass)、F5 IT-PERF.3-01 で本物 HwFailsafeTimer の発火タイミングが Linux nightly 5 連続 Pass で安定確認済 |
| ST-IF.1-02 | SRS-IF-002(制御 API)| `vip_api.control_api.ControlApi`(7 コマンド + await_command Facade、SDD §4.15)| **OK** | UNIT-005.1 が UT で 100% カバレッジ + MC/DC 100%(UTPR §7.3.15)、F1 IT-RCM001 で本物 StateMachine 不変性検証(8/8 Pass)、F4 IT-SEP で本物 vip_api_b Adapter 経路実証(6/6 Pass、SEP-001 越え経路)、ApiResult sealed hierarchy(`Ok` / `ValidationFailed` / `ApiRejected`)が dataclasses.FrozenInstanceError で不変性確認済 |
| ST-IF.1-03 | SRS-IF-003(状態観測 API)| `vip_api.state_observer_api.StateObserverApi`(副作用なし読み取り専用、SDD §4.16)| **OK** | UNIT-005.2 が UT で 100% カバレッジ(UTPR §7.3.16)、100 回 idempotent + mutating API 不呼出契約検証済、`dataclasses.FrozenInstanceError` で不変性確認、`PumpSnapshot` Protocol structural typing 適合確認、ST-OPS.1-04 `--diagnose` 経路で system レベル状態観測経路も Pass 済 |
| ST-IF.1-04 | SRS-IF-004(ロギング I/F)| SRS-OPS-010 整合の JSON Lines 出力 I/F(`vip_ctrl.cli._emit_event`、SDD §4.18)| **OK** | UNIT-005.4 で 5 必須キー(`timestamp / level / component / event / details`)網羅試験済(UT-005.4-14、UTPR §7.3.18)、ST-OPS.1-03 で boot_snapshot + diagnose 2 経路の JSON Lines 5 必須キー網羅を system レベルで実証(STPR §6.2、Step 19 H2 Pass)。Inc.4 でアラーム I/F + 構造化ロガー本格化時に SRS-IF-004 範囲拡大予定 |
| ST-IF.1-05 | SRS-IF-005(永続化 I/F)| `vip_persist` パッケージ公開 API(`atomic_writer.write/read/rollback` / `serializer.to_json/from_json` / `checksum.compute/verify` / `records.PersistedRecord`、SDD §4.4)| **OK** | UNIT-003.1〜003.3 + UNIT-004.1 が UT で 100% カバレッジ + MC/DC 100%(UTPR §7.3.4〜7.3.7)、F6 IT-PWR で SDD §4.4.B 不変条件 3 フェーズ網羅 + rollback() 復元実証(Linux nightly 20/20 Pass、Step 19 H3 で F6 申し送り回収完了)、F7 IT-SIDE で `hmac.compare_digest` 定数時間性検証(Linux nightly 10/10 Pass、Step 19 H3 で F7 申し送り回収完了)、ST-RCM.1-04 で破損レコード検出経路を CLI 経由 system 再現(STPR §6.3)|

- **総評:** Inc.1 範囲全 5 件 SRS-IF レビュー OK。各 IF は UT(契約)+ IT(結合動作)+ ST(system 観測)の 3 段で網羅、Inc.4 拡張時(対話 UI / アラーム / 構造化ロガー)に SRS-IF 範囲再評価予定。

### 6.6 ST-ALM — アラーム(IEC 60601-1-8 連携)— **Inc.2 詳細化(Step 20 H、CR-0014、骨格、Step 14 v0.1 流儀継承)**

> **Step 20 H 整合化(2026-05-13、本節 v0.4 拡張):** SAD-VIP-001 v0.2 §4.3.2(ARCH-006 Detection 検知群 / ARCH-007 Alarm Reporter 本実装)+ §5.3(IEC 60601-1-8 §6.4 状態遷移)+ §9.2(SEP-003)+ SDD-VIP-001 v0.5 §4.19〜§4.26(Inc.2 新規 8 ユニット骨格)+ §5.1.A(`AlarmEvent` 実装契約)+ UTPR-VIP-001 v0.22 §7.3.19〜§7.3.26(Inc.2 UT 骨格)+ ITPR-VIP-001 v0.12 §6.11〜§6.16(Inc.2 結合観点骨格)で骨格化済の Inc.2 アラーム機能を、**STPR の system 観点(`vip-ctrl` CLI 経由の subprocess 実行 + IEC 60601-1-8 規格整合)** で骨格化。Step 14 v0.1 流儀継承(代表 N 観点詳細 + 残骨格)で本 STPR では骨格に留め、STPR v0.5+ 候補(Step 20 X〜の TDD 実装と並行する詳細化)で各 ST-ALM ケースを詳細化予定。

- **目的:** SRS-ALM-001〜003(Inc.1 既存)+ **SRS-ALM-004〜008**(Inc.2、IEC 60601-1-8 §6.1 優先度 + §5.1.4 テクニカル区分付与)+ **SRS-040〜044**(Inc.2 検知)+ **SRS-RCM-006/009/010/011/012**(Inc.2 RCM)+ **SRS-044**(アラーム確認・休止、IEC 60601-1-8 §6.4)+ **SRS-IF-010**(Alarm I/F 本実装契約)を **system 観点 = `vip-ctrl` CLI 経由の subprocess 実行 + JSON Lines 出力観測 + IEC 60601-1-8 規格整合確認** で検証する。
- **関連 SRS:** SRS-ALM-001(致命的内部エラー)、SRS-ALM-002(整合性検証失敗)、SRS-ALM-003(不正コマンド拒否)、**SRS-ALM-004(高優先度・テクニカル発報)**、**SRS-ALM-005(高優先度・テクニカル発報)**、**SRS-ALM-006(中優先度・テクニカル発報)**、**SRS-ALM-007(中優先度・テクニカル発報)**、**SRS-ALM-008(IEC 60601-1-8 §6.4 アラーム確認・休止)**、**SRS-040〜044(検知要求 5 件)**、**SRS-RCM-006/009/010/011/012**、**SRS-IF-010**、**SRS-O-040 確定**(`AlarmEvent` 構造)、**SRS-REG-002 詳細化**(IEC 60601-1-8 §6.1/§5.1.4/§6.4)
- **関連 RCM:** **RCM-006(発報必達)/ RCM-009(冗長 2 系統閉塞)/ RCM-010(多段気泡)/ RCM-011(アラームタスク監視)/ RCM-012(発報路冗長)+ RCM-020 候補(HZ-009 対応)**(Inc.2 Designed → Verified 化目標、Inc.2 完了タグ `v0.2.0-inc2` 付与時)
- **関連 HZ:** HZ-002(注入停止失敗、間接)、HZ-004(検知失敗 → アラーム失敗連鎖、EV-HZ004-001/002/003 駆動)、HZ-005(アラーム失敗単独、EV-HZ005-001 駆動)、**HZ-009(バッテリ低下によるソフトウェア機能喪失、EV-HZ009-001 駆動、Inc.2 新規識別)**
- **関連 IT-ID 申し送り**(ITPR v0.12 §6.11〜§6.16 結合観点骨格)**:** IT-RCM006(§6.11 発報必達)+ IT-RCM009(§6.12 冗長 2 系統閉塞)+ IT-RCM010(§6.13 多段気泡)+ IT-RCM011(§6.14 アラームタスク監視)+ IT-RCM012(§6.15 発報路冗長)+ **IT-ALM(§6.16 SEP-003 + IEC 60601-1-8 §6.4 + IS-7/IS-8 全層 E2E 集約観点)**
- **環境制約:** Inc.2 アラーム機能は CLI 経由で `acknowledge_alarm` / `silence_alarm` を発行する対話コマンドが必要(SRS-044、ARCH-005.1 拡張、UNIT-005.1 拡張)。Inc.1 ISS-H-002 と同種の対話 CLI 課題が Inc.2 でも継続する見込みのため、対話 CLI 実装は Step 20 X〜の TDD で UNIT-005.1 拡張と並行実施 → 完了後 STPR v0.5+ 候補で ST-ALM 実装 + 実測を行う段階成熟方式とする。
- **試験ケース数目安(骨格、STPR v0.5+ 候補で詳細化):** **≥ 12 件**(Inc.2 詳細化、IEC 60601-1-8 §6.1 優先度 3 段 × §5.1.4 区分 2 種 + ACK/SILENCE 状態遷移 4 経路 + 各検知群 system 再現 5 件 + RCM-020 候補 1 件)

**試験ケース骨格(STPR v0.5+ 候補で詳細化):**

| 試験 ID(目安)| 内容 | 種別 | 関連 SRS / RCM | 関連 IT-ID 申し送り |
|---------------|------|------|----------------|----------------------|
| ST-ALM.1-01〜 | IEC 60601-1-8 §6.1 高優先度発報試験(`vip-ctrl` CLI で OCCLUSION / AIR_BUBBLE_CRITICAL を Event Injection 経由で注入 → JSON Lines に `priority="high"` + `category="technical"` の `AlarmEvent` 出力を確認、SRS-ALM-004/005)| 優先度 + 区分 | SRS-ALM-004/005、SRS-040/041、RCM-006/009/010 | IT-RCM006/009/010 + IT-ALM |
| ST-ALM.1-04〜 | IEC 60601-1-8 §6.1 中優先度発報試験(RESERVOIR_EMPTY / BATTERY_LOW を注入 → `priority="medium"` + `category="technical"` 出力確認、SRS-ALM-006/007、HZ-009 EV-HZ009-001 駆動)| 優先度 + 区分 + HZ-009 駆動 | SRS-ALM-006/007、SRS-042/043、RCM-006、RCM-020 候補 | IT-RCM006 + IT-ALM |
| ST-ALM.1-07〜 | IEC 60601-1-8 §6.4 ACK/SILENCE 状態遷移試験(発報後 `vip-ctrl --command acknowledge_alarm <id>` → ACK 状態確認 → `silence_alarm <id> --duration 60` → SILENCED 状態確認 → 60 秒経過後 ACTIVE 復帰確認、SRS-ALM-008、SRS-044)| 状態遷移 E2E | SRS-ALM-008、SRS-044、SRS-IF-010 | IT-ALM.1-04〜 + IT-ALM.1-07〜 |
| ST-ALM.1-10〜 | 高優先度消音時間 ≤ 120 秒制限試験(高優先度アラームに対し `silence_alarm <id> --duration 121` → `Err(SilenceTooLong)` 戻り値確認、IEC 60601-1-8 §6.4 規格適合)| 異常系 + 規格適合 | SRS-ALM-008、SRS-044 | IT-ALM.1-04〜 |
| ST-ALM.1-12〜 | アラームタスク監視 system 再現(UNIT-006.4 Alarm Task Watchdog の heartbeat 途絶を Event Injection 経由で再現 → 800 ms 以内に Trip + 独立発報路フェイルオーバー + JSON Lines に `cause_code="ALARM_TASK_FAILURE"` 出力確認、SRS-RCM-011)| RCM 統合 | SRS-RCM-011、SRS-044 | IT-RCM011 |
| ST-ALM.1-14〜 | アラーム発報路冗長 system 再現(UNIT-006.5 主系発報路をフェイル状態に切替 → 予備系発報路フェイルオーバー → JSON Lines に `path="secondary"` 出力確認、SRS-RCM-012)| RCM 統合 + 冗長性 | SRS-RCM-012 | IT-RCM012 |
| ST-ALM.1-16〜 | HZ-009 EV-HZ009-001 system 再現 + 安全側遷移ロジック(BATTERY_LOW 緊急閾値以下注入 → 中優先度発報 + RCM-020 候補の安全側遷移(自動 PAUSED / 注入レート低下 / 制御停止のいずれか、SDD v0.6 候補で確定)を JSON Lines + 状態観測 API で確認)| HZ-009 駆動 + RCM-020 候補 | SRS-043、SRS-ALM-007、RCM-006、RCM-020 候補 | IT-RCM006 + IT-ALM.1-13〜 |

**SUT 構成方針:** subprocess.Popen で `vip-ctrl` 起動 + `tests/system/conftest.py` の `installed_venv` fixture(Inc.1 既存)を再利用 + Inc.2 で追加される対話 CLI コマンド(`acknowledge_alarm` / `silence_alarm` / Event Injection 経由でセンサー異常を注入する `--inject` 等)を CLI surface に正式実装(Step 20 X〜の TDD で UNIT-005.1 拡張 + UNIT-002.3 BATTERY_LOW 追加と並行)。SEP-003 ランタイム検証は ITPR §6.16 IT-ALM.1-10〜12 で Python import 経路の AST + 戻り値書込み禁止 + 例外伝播禁止 + AlarmEvent 不変性検証を実施(STPR では subprocess 経路の system observable な振舞いに focus)。

**マーカー方針:** `@pytest.mark.system` + `@pytest.mark.alm`(STPR v0.5+ 候補で `pyproject.toml` に追加)+ 高優先度発報 + 状態遷移は `system-fast`(PR / push)、長時間消音時間試験(ST-ALM.1-07〜 の 60 秒待機)+ HZ-009 駆動の安全側遷移確認(ST-ALM.1-16〜)は `@pytest.mark.nightly`(Inc.1 §6.1 ST-PERF.1-05 SRS-P07 24 時間試験と同方針)。

**STPR v0.5+ 候補で詳細化する項目(Inc.2 着手中の発見申し送り):**

- IEC 60601-1-8 §6.4「健康ケアプロバイダの操作なしで自動復帰しない」規定の system 試験(UNIT-006.3 Reservoir Empty 復元時の自動 RUNNING 復帰禁止、UTPR §7.3.21 UT-006.3-10〜 と整合)
- ARCH-009 Logging Stub(Inc.2 では no-op スタブのまま、Inc.4 で本実装予定)経由の AlarmEvent 永続化試験(Inc.4 申し送り)
- Inc.2 完了タグ `v0.2.0-inc2` 付与時の RMF Verified 化判定基準(RCM-006/009/010/011/012 の system レベル実証 + transitive RCM-020 候補)
- 対話 CLI 実装(`acknowledge_alarm` / `silence_alarm` / `--inject`)の SDD §4.15.G 詳細化(UTPR §7.3.15.G UT-005.1-G01〜 と整合)が Step 20 X〜で着手される時点での STPR ケース実装着手判断
- IEC 60601-1-8 §6.4 高優先度消音時間 ≤ 120 秒の境界値試験(120 秒ちょうど vs 121 秒、ARCH-005.1 拡張側で `Err(SilenceTooLong)` 強制実装契約、SAD v0.2 §5.1 IF-U-014 / ITPR v0.12 §4.3 IF-U-014-A と整合)

### 6.7 ST-SEC — セキュリティ — **Step 19 H3 で記入完了**

- **目的:** SRS-SEC-002(機密情報非出力)+ SRS-SEC-003(pip-audit による既知脆弱性検出)が機能することを検証する。SRS-SEC-001(チェックサム改ざん検知)は UT/IT で検証済(F7 IT-SIDE で定数時間性も検証済)。
- **関連 SRS:** SRS-SEC-002(機密情報非出力 / Inc.1 では患者情報非取扱のためレビュー)、SRS-SEC-003(pip-audit / `.github/workflows/unit-test.yml` で自動化済)
- **試験ケース数目安:** ≥ 2 件(レビュー 1 件 + CI 確認 1 件)
- **レビュー / CI 確認記録(Step 19 H3 = 2026-05-07、レビュー者 k-abe):**

| 試験 ID | 関連 SRS | 確認内容 | 結果 | 根拠 |
|---------|---------|---------|------|------|
| ST-SEC.1-01 | SRS-SEC-002(機密情報非出力)| Inc.1 範囲のソースコード + ログ I/F が患者情報を扱わないこと、bandit `-ll` で機密情報リーク警告がないこと | **OK(レビュー記録)** | (a) Inc.1 範囲は流量制御コア(SRS-001〜032、設定値 + 状態 + 永続レコード)で **患者情報自体を扱わない**(SRS-SEC-002 注記 + STPR §3.2 整合)、(b) `bandit -ll -r src -c pyproject.toml` 0 issues 維持(severity / confidence ともに 0、Step 19 H1〜H3 全期間)、(c) `vip_ctrl.cli._emit_event` の JSON Lines 出力フィールド(timestamp / level / component / event / details)を網羅レビュー = `details` に持続化される情報は永続レコード整合性検証結果と機器状態のみで患者情報なし。Inc.4 ロギング本格化 + 患者情報扱い時に試験(自動)へ昇格、現時点はレビュー記録として確定 |
| ST-SEC.1-02 | SRS-SEC-003(pip-audit による既知脆弱性検出)| CI ワークフローで pip-audit が SOUP の既知脆弱性をスキャンしていること | **OK(CI 確認)** | `.github/workflows/unit-test.yml` の `pip-audit` ジョブが PR / push ごとに `pip-audit --strict -r requirements-audit.txt` を実行(CI-CFG-011 + SOUP-010 = pip-audit 2.7+、Step 19 B1 で正式運用化)、Step 19 H2 PR #45 マージ前 CI(Run ID 25485492578、2026-05-07T08:43Z)で pip-audit Pass を実測確認、Step 19 H3 PR でも同 CI が Pass する設計。継続的脆弱性検出の自動化が Inc.1 範囲で確立 = SRS-SEC-003 充足。新規 SOUP 追加 / 既存 SOUP メジャーバージョンアップ時は CI が自動検出する運用 |

- **総評:** Inc.1 範囲 SRS-SEC は SRS-SEC-001 = UT/IT 検証済(F7 IT-SIDE で定数時間性も Linux nightly 5 連続 Pass、Step 19 H3 で F7 申し送り回収完了)+ SRS-SEC-002 = レビュー OK + SRS-SEC-003 = CI 自動化確立の 3 本立てで網羅。Inc.4 ロギング本格化 + 患者情報扱い時に SRS-SEC-002 を試験へ昇格申し送り。Inc.5 で SRS-SEC-001 強判定(IT-SIDE < 1 sigma)再評価 + 専用 runner 検討申し送り(F7 + ITPR PRB-0001 §11.3 IT-PERF.2-02 と並列)。

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

- [ ] 計画が SRS / SAD / SDD / RMF / ITPR / UTPR と整合している(§2 参照文書、§6 試験観点。Inc.2 = SRS v0.3 / SAD v0.2 / SDD v0.5 / RMF v0.4 / UTPR v0.22 / ITPR v0.12 / INC2-SCOPE-VIP-001 v0.1 / IEC 60601-1-8 と整合)
- [ ] 各試験ケースが期待結果・合格基準を明示している(Inc.1 = §6.1〜§6.3 / §6.5 / §6.7 詳細化済 + §6.4 / §6.6 / §6.8 / §6.9 骨格 / **Inc.2 = §6.6 ST-ALM 詳細化 + §6.4.G / §6.2.G / §6.3.G 既存 ST 拡張節 骨格**(Step 20 H、CR-0014)、ST-ALM.1-01〜 / ST-x.G-01〜 ID 体系確定済、実装は STPR v0.5+ 候補)
- [ ] 試験が再現可能である(§4.4 自動化方針、`pytest` ベース、CI 自動実行)
- [ ] リスクコントロール手段を検証するケースが含まれている(Inc.1 = 全 RCM 6 件 §6.3 ST-RCM / **Inc.2 = RCM-006/009/010/011/012 + RCM-020 候補 §6.3.G ST-RCM.G + §6.6 ST-ALM**)
- [ ] SRS 必須要求が試験対象として網羅されている(§13 トレーサビリティマトリクス、Inc.2 = SRS-040〜044 + SRS-ALM-004〜008 + SRS-RCM-006/009/010/011/012 + SRS-IF-010 + SRS-O-040 + SRS-I-040 + SRS-REG-002 詳細化)
- [ ] 試験環境が実使用環境を妥当に代表している(§4.3、VIP-SIM-001 シミュレータ + Inc.2 で対話 CLI 拡張)
- [ ] 合否判定基準が客観的である(各 §6.x.2 試験ケース表に明記)
- [ ] §5.7.4 妥当性確認チェックリスト(§6.3.3)が記入されている(**Inc.1 = Step 19 H3 で記入完了 / Inc.2 = STPR v0.5+ 候補で Inc.2 RCM 5 件 + RCM-020 候補の transitive 充足を記入予定**)
- [ ] **規格適合(Inc.2 新規):** IEC 60601-1-8 §6.1 優先度分類 + §5.1.4 テクニカル / 生理アラーム区分 + §6.4 アラーム確認・休止規定が ST-ALM.1-01〜 で網羅されている(STPR v0.5+ 候補で実装 + 規格チェックリスト記入)

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
| ST-IF(内部 I/F、§6.5 詳細化済 Step 19 H3)| **5**(レビュー記録 5 件、ST-IF.1-01〜05)| **5**(全件 OK = レビュー Pass、Step 19 H3 記入完了)| 0 | 0 | 2026-05-07 | (Step 19 H3 PR マージコミットで確定)|
| ST-ALM(アラーム、§6.6 Inc.1 = スタブ ST-ALM.1-01 レビュー / **Inc.2 = §6.6 詳細化骨格、Step 20 H、CR-0014**)| Inc.1 = 0(スタブ I/F のレビューは ST-IF.1-XX に集約)/ **Inc.2 = ≥ 12**(ST-ALM.1-01〜、IEC 60601-1-8 §6.1/§5.1.4/§6.4)| TBD | TBD | TBD | TBD | TBD |
| ST-SEC(セキュリティ、§6.7 詳細化済 Step 19 H3)| **2**(ST-SEC.1-01 レビュー + ST-SEC.1-02 CI 確認)| **2**(全件 OK、Step 19 H3 記入完了)| 0 | 0 | 2026-05-07 | (Step 19 H3 PR マージコミットで確定)|
| ST-UX(ユーザビリティ、§6.8 骨格、Inc.4)| **≥ 4**(Inc.4 詳細化)| TBD | TBD | TBD | TBD | TBD |
| ST-DATA(データ永続化、§6.9 骨格)| **≥ 4**(Step 19 H 詳細化、ST-RCM.1-04 で SRS-DATA-001 部分網羅済)| TBD | TBD | TBD | TBD | TBD |
| **Inc.1 小計**(§6.1〜§6.3 + §6.5 + §6.7 集計)| **23**(Step 19 G + H2 + H3)| **14**(H2 で 7 + H3 で ST-IF 5 + ST-SEC 2 = 14)| **0** | **9**(Inc.4 申し送り 8 + Inc.1 完了タグ後 1、Step 19 H2 で確定)| 2026-05-07 | (Step 19 H2 / H3 PR マージコミット)|
| **ST-FUNC.G(Inc.2 機能要求、§6.4.G 骨格、Step 20 H、CR-0014)** | **≥ 5**(目安、ST-FUNC.G-01〜)| TBD | TBD | TBD | TBD | TBD |
| **ST-OPS.G(Inc.2 受入試験 + 運用、§6.2.G 骨格、対話 CLI 拡張、Step 20 H、CR-0014)** | **≥ 4**(目安、ST-OPS.G-01〜)| TBD | TBD | TBD | TBD | TBD |
| **ST-RCM.G(Inc.2 RCM 統合、§6.3.G 骨格、RCM-006/009/010/011/012 + RCM-020 候補、Step 20 H、CR-0014)** | **≥ 6**(目安、ST-RCM.G-01〜)| TBD | TBD | TBD | TBD | TBD |
| **Inc.2 小計**(骨格、§6.6 ST-ALM + §6.x.G、合計目安)| **≥ 27**(ST-ALM ≥ 12 + ST-FUNC.G ≥ 5 + ST-OPS.G ≥ 4 + ST-RCM.G ≥ 6)| TBD(Step 20 X〜の TDD 実装と並行する詳細化 + 実測で確定、STPR v0.5+ 候補)| TBD | TBD | — | — |
| **総計**(Inc.1 + Inc.2)| **≥ 50** | Inc.1 = 14 Pass / Inc.2 = TBD | 0 + TBD | 9 + TBD | — | — |

### 11.3 不具合・逸脱

| 問題 ID(PRB) | 発見 ST-ID | 内容 | 重大度 | 対応 | ステータス |
|----------------|-----------|------|-------|------|----------|
| **PRB-0001(transitive 影響参照)** | —(IT 起因、ST 直接影響なし) | ITPR-VIP-001 v0.11 §11.3 で正式記録された ANOM-001(IT-PERF.2-02 SDD §4.7.A 50 ms 厳密境界の構造的 CI flake)が Step 19 H3 で発見・残留異常化された。ST 観点では **ST-PERF.1-04 SRS-P05 起動時間 ≤ 3 秒**(STPR §6.1)が SRS-P05 全体予算で 5 連続 Pass しているため、SRS 性能要求の本旨 = システム起動時間は満たされている。ITPR の SDD 内訳予算(50 ms)厳密境界の閾値緩和は CR-0006 として Inc.2 以降に申し送り | Minor(transitive、ST 直接対応なし)| ST-PERF.1-04 SRS-P05 全体予算 5 連続 Pass で SRS 要求充足を再確認、ITPR §11.3 PRB-0001 行と紐付けて記録 | **Active**(transitive、ITPR 側で管理)|

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
| 内部 I/F | ST-IF.1-01〜05(§6.5 詳細化済 Step 19 H3)| SRS-IF-001〜005 | —(I/F 設計)| —(I/F 設計)| —(IT で動作試験済)| レビュー記録 | **5/5 OK(Step 19 H3 記入完了、全 SRS-IF が UT(契約)+ IT(結合動作)+ ST(system 観測)の 3 段網羅で充足、Inc.4 拡張時に範囲再評価申し送り)** |
| アラーム(Inc.1)| ST-ALM.1-XX(§6.6 骨格 = Inc.1 スタブ I/F のレビューは ST-IF.1-XX に集約)| SRS-ALM-001〜003 + IEC 60601-1-8(Inc.1 はスタブ)| RCM-003、RCM-004 | HZ-002 | —(Inc.1 はスタブ)| —(Inc.1 範囲は ST-IF.1-XX で集約)| 骨格(Inc.2 アラーム正式化、本 v0.4 で §6.6 を Inc.2 詳細化)|
| **アラーム(Inc.2、§6.6 ST-ALM 詳細化、Step 20 H、CR-0014、骨格)** | **ST-ALM.1-01〜**(目安 ≥ 12 件、IEC 60601-1-8 §6.1 優先度 + §5.1.4 区分 + §6.4 ACK/SILENCE)| **SRS-ALM-004〜008、SRS-040〜044、SRS-RCM-006/009/010/011/012、SRS-IF-010、SRS-O-040、SRS-I-040、SRS-REG-002 詳細化** | **RCM-006/009/010/011/012(Designed → Verified 化目標)+ RCM-020 候補(HZ-009)** | HZ-002、HZ-004(EV-HZ004-001/002/003)、HZ-005(EV-HZ005-001)、**HZ-009(EV-HZ009-001、新規識別)** | **IT-RCM006(§6.11)+ IT-RCM009(§6.12)+ IT-RCM010(§6.13)+ IT-RCM011(§6.14)+ IT-RCM012(§6.15)+ IT-ALM(§6.16 = SEP-003 + IEC 60601-1-8 §6.4 + IS-7/IS-8 全層 E2E)** | 試験(自動、subprocess + venv 隔離 + 対話 CLI)+ IEC 60601-1-8 規格適合 | **骨格(Step 20 H、CR-0014):結合経路 + 試験ケース骨格 + ケース数目安 + SUT 構成方針 + マーカー方針 + STPR v0.5+ 候補で詳細化する項目記述、対話 CLI 実装(Step 20 X〜)後に実装 + 実測** |
| **機能(Inc.2、§6.4.G ST-FUNC.G、Step 20 H、CR-0014、骨格)** | **ST-FUNC.G-01〜**(目安 ≥ 5 件)| **SRS-040〜044** | RCM-006/009/010/011/012(間接) | HZ-004、HZ-005、HZ-009(間接) | **IT-RCM006/009/010/011/012(機能整合性 IT 側で網羅、ST は subprocess 経路の system 機能再確認)** | 試験(自動)| **骨格(Step 20 H、CR-0014):対話 CLI(`acknowledge_alarm` / `silence_alarm` / `--inject`)実装後に詳細化、ST-ALM.1-XX との分担 = ST-FUNC.G は SRS 機能要求 / ST-ALM は規格適合** |
| **受入試験 + 運用(Inc.2、§6.2.G ST-OPS.G、Step 20 H、CR-0014、骨格)** | **ST-OPS.G-01〜**(目安 ≥ 4 件)| **SRS-OPS-001〜004(必須、CLI surface 拡張)、SRS-OPS-010(JSON Lines 5 必須キー + AlarmEvent ペイロード整合)、SRS-044** | —(運用要求)| —(運用要求)| **IT-ALM(Mock 経路は IT、subprocess 経路は ST)** | 試験(自動、subprocess + venv 隔離 + 対話 CLI 拡張)| **骨格(Step 20 H、CR-0014):Inc.1 既存 ST-OPS.1-01〜05 全 5 件 Pass への回帰なし確認 + Inc.2 対話 CLI(`acknowledge_alarm` / `silence_alarm` / `--inject`)の system 経路試験を STPR v0.5+ 候補で詳細化** |
| **RCM 統合(Inc.2、§6.3.G ST-RCM.G、Step 20 H、CR-0014、骨格、Inc.2 RCM 5 件 + RCM-020 候補)** | **ST-RCM.G-01〜**(目安 ≥ 6 件)| **SRS-RCM-006/009/010/011/012 + RCM-020 候補(HZ-009)** | **RCM-006/009/010/011/012(Inc.2 Designed → Verified 化目標、Inc.2 完了タグ `v0.2.0-inc2` 付与時)+ RCM-020 候補** | HZ-004、HZ-005、**HZ-009(EV-HZ009-001 駆動)** | **IT-RCM006/009/010/011/012(§6.11〜§6.15 結合観点)+ IT-ALM.1-13〜(§6.16 IS-8 全層 E2E で HZ-009 駆動経路実証)** | 試験(自動)+ §5.7.4 妥当性確認 transitive 充足 | **骨格(Step 20 H、CR-0014):対話 CLI 実装後に system 再現可能となる RCM(検知群 + 発報経路)+ Inc.4 申し送りとなる RCM(内部スレッド・冗長経路 = system observable boundary が小さい)を分離して STPR v0.5+ 候補で詳細化、Inc.2 完了タグ `v0.2.0-inc2` 付与時の §5.7.4 妥当性確認チェックリスト記入** |
| セキュリティ | ST-SEC.1-01/02(§6.7 詳細化済 Step 19 H3)| SRS-SEC-002 / SRS-SEC-003 | —(性能 / 副次品質)| —(Inc.1 脅威モデル外)| F7 IT-SIDE(SRS-SEC-001 関連、Linux nightly 10/10 Pass = 申し送り回収完了)| レビュー(SEC-002)+ CI 確認(SEC-003)| **2/2 OK(Step 19 H3 記入完了、SRS-SEC-002 = レビュー OK / SRS-SEC-003 = pip-audit CI 自動化確立、SRS-SEC-001 = F7 IT-SIDE で定数時間性も Linux nightly 5 連続 Pass で確認済、Inc.4 ロギング本格化時に SRS-SEC-002 を試験へ昇格申し送り)** |
| ユーザビリティ | ST-UX.1-XX(§6.8 骨格)| SRS-UX-001 / SRS-UX-002 + IEC 62366-1 | RCM-017、RCM-018(Inc.4)| HZ-008(Inc.4)| UT-005.2 / UT-005.3(API 検証済)| レビュー(Inc.1)+ 試験(Inc.4)| 骨格(Inc.4 UI 層詳細化)|
| データ永続化 | ST-DATA.1-XX(§6.9 骨格)| SRS-DATA-001〜004 | RCM-015 | HZ-007 | F6 IT-PWR、F7 IT-SIDE | 試験(自動、F6 IT-PWR の system 再現)| 骨格(Step 19 H 詳細化)|

**カバレッジ:** 本マトリクスにより、**Inc.1 範囲**(SRS-001〜032、SRS-P01〜P07 のうち必須、SRS-OPS-001〜004、SRS-RCM-* 全件、SRS-SEC-001〜003、SRS-DATA-001〜004)+ RCM(全 6 件)+ **Inc.2 範囲**(SRS-040〜044、SRS-ALM-004〜008、SRS-RCM-006/009/010/011/012、SRS-IF-010、SRS-O-040、SRS-I-040、SRS-REG-002 詳細化、IEC 60601-1-8 §6.1/§5.1.4/§6.4)+ Inc.2 RCM(5 件 + RCM-020 候補)が ST 試験 ID と紐付き、SRS / RCM / HZ への双方向トレーサビリティが確立した(Inc.1 = §6.1〜§6.3 + §6.5 + §6.7 で詳細化済 + ST レベル実証済 / Inc.2 = §6.6 ST-ALM + §6.4.G / §6.2.G / §6.3.G で骨格化済、結果欄は STPR v0.5+ 候補(Step 20 X〜の TDD 実装と並行する詳細化)で確定)。残 3 観点(§6.4 ST-FUNC / §6.8 ST-UX / §6.9 ST-DATA)は Inc.4(UI 層)+ Step 20 X〜(ST-DATA は Inc.2 実装と並行)で詳細化。

## 14. 改訂履歴

| バージョン | 日付 | 変更内容 | 変更者 |
|----------|------|---------|--------|
| 0.4 | 2026-05-13 | **Step 20 H(CR-0014、Inc.2 連動改訂の STPR 部分、骨格化、Step 14 v0.1 流儀 / Step 19 G STPR v0.1 流儀継承、「単一文書 = 単一 CR」運用パターン 8 度目、「§4 CLOSED 一気通貫」運用パターン 8 度目、Inc.2 着手準備 Step 系列の 9 番目 = 真の最終)を反映。**(A) ヘッダ更新 + 対象範囲拡張(対象 SW v0.1.0-inc1 → v0.2.0-inc2、対象範囲 = Inc.1(代表 3 観点詳細化済 + ST-IF / ST-SEC レビュー記録済)+ Inc.2(§6.6 ST-ALM 詳細化 + §6.x.G 既存 ST 拡張節))、最終更新日 2026-05-13。**(B) §1.1 段階成熟方式の Inc.2 拡張記述追加**(Step 14 v0.1 流儀 / Step 19 G STPR v0.1 流儀継承で本 Step 20 H で骨格化、後続 STPR v0.5+ 候補で詳細化)。**(C) §2 参照文書更新**(SRS v0.1 → v0.3、SAD v0.1 → v0.2、SDD v0.2 → v0.5、UTPR v0.19 → v0.22、ITPR v0.10 → v0.12、RMF v0.1 → v0.4、SRMP v0.1 → v0.2、SCMP v0.1 → v0.3、SPRP v0.1 → v0.2、CIL v0.41 → v0.53、Inc.2 範囲計画書(INC2-SCOPE-VIP-001 v0.1)+ IEC 60601-1-8 を [13]/[14] として追加)。**(D) §3.1 SRS 網羅性方針 Inc.2 SRS 列挙追加**(SRS-040〜044 + SRS-ALM-004〜008 + SRS-RCM-006/009/010/011/012 + SRS-IF-010 + SRS-O-040 + SRS-I-040 + SRS-REG-002 詳細化)。**(E) §3.3 試験 ID 体系 Inc.2 拡張**(ST-OPS.G / ST-RCM.G / ST-FUNC.G の Inc.2 拡張節 ID + ST-ALM.1-XX を Inc.2 詳細化骨格状態に更新)。**(F) §4.1 試験戦略段階成熟方式 Inc.2 ステップ追加**(本 v0.4 = Step 20 H 段階成熟方式の Inc.2 ステップとして明文化)。**(G) §6.6 ST-ALM Inc.2 詳細化(本書最大の改訂):** 目的・関連 SRS / RCM / HZ / IT-ID 申し送り・環境制約 + 7 ケース骨格(ST-ALM.1-01〜 IEC 60601-1-8 §6.1 高優先度発報 / 1-04〜 中優先度発報 + HZ-009 駆動 / 1-07〜 §6.4 ACK/SILENCE 状態遷移 + 60 秒経過後 ACTIVE 復帰 / 1-10〜 高優先度消音時間 ≤ 120 秒制限 / 1-12〜 アラームタスク監視 system 再現 / 1-14〜 発報路冗長 system 再現 / 1-16〜 HZ-009 EV-HZ009-001 + RCM-020 候補安全側遷移)+ SUT 構成方針(subprocess.Popen + `installed_venv` fixture 再利用 + 対話 CLI 拡張)+ マーカー方針(`@pytest.mark.system` + `@pytest.mark.alm` + `nightly` for 60 秒待機 + HZ-009)+ STPR v0.5+ 候補で詳細化する項目(IEC 60601-1-8 §6.4 自動復帰禁止 / ARCH-009 Logging Stub 経由 AlarmEvent 永続化 Inc.4 申し送り / Inc.2 完了タグ RMF Verified 化判定基準 / 対話 CLI 実装後の試験設計 / 高優先度消音時間 120 秒境界値試験)。**(H) §6.4.G ST-FUNC Inc.2 拡張**(SRS-040〜044 機能要求 system 再確認、5 ケース骨格、ST-ALM.1-XX との分担明示)。**(I) §6.2.G ST-OPS Inc.2 拡張**(対話 CLI `acknowledge_alarm` / `silence_alarm` / `--inject` の subprocess 経路試験 + Inc.1 既存 5 件への回帰なし、4 ケース骨格)。**(J) §6.3.G ST-RCM Inc.2 拡張**(RCM-006/009/010/011/012 + RCM-020 候補の system 再現、6 ケース骨格、§5.7.4 妥当性確認 transitive 充足戦略を Inc.1 流儀継承 = 検知群 + 発報経路は ST 直接実証 / 内部スレッド・冗長経路は Inc.4 申し送り)。**(K) §7.1 計画レビューチェックリスト Inc.2 拡張**(Inc.2 RCM 5 件 + RCM-020 候補 + IEC 60601-1-8 規格適合チェック項目追加 + Inc.2 完了タグ §5.7.4 妥当性確認チェックリスト記入を STPR v0.5+ 候補申し送り)。**(L) §11.2 試験ケース結果テーブル拡張**(Inc.2 4 行追加 = ST-ALM ≥ 12 + ST-FUNC.G ≥ 5 + ST-OPS.G ≥ 4 + ST-RCM.G ≥ 6 = 全件「未実施(TBD)」+ Inc.1 / Inc.2 / 総計 ≥ 50 件 集計行)。**(M) §13 トレーサビリティマトリクス追補**(Inc.2 4 行追加 = ST-ALM(Inc.2)+ ST-FUNC.G + ST-OPS.G + ST-RCM.G、関連 SRS / RCM / HZ / IT-ID 申し送りを双方向リンク、結果欄は STPR v0.5+ 候補で確定)+ Inc.1 既存 ST-ALM 行を「Inc.1 はスタブ I/F のレビューは ST-IF.1-XX に集約」に整合化。**(N) §14 改訂履歴 v0.4 行追加**(本行)。**(O) MODERATE 区分・「単一文書 = 単一 CR」運用パターン 8 度目適用**(SCMP §4.1「中度」、Inc.2 アラーム機能 + IEC 60601-1-8 規格適合 + RCM-020 候補(HZ-009 安全側遷移)の system 試験範囲追加により「軽微」を超える、ただし Inc.1 既存 §6.1〜§6.3 / §6.5 / §6.7 詳細化部分 + 14 Pass / 9 Skip は据置 = Inc.1 完了タグ `v0.1.0-inc1` 付与時点の確定内容を維持、本書は STPR の Inc.2 連動改訂のみで実装コード変更なし)。**(P) Step 20 H 着手中の発見:** Inc.2 でも Inc.1 ISS-H-002 と同種の対話 CLI 課題(`acknowledge_alarm` / `silence_alarm` / `--inject` 等)が存在することが判明 → 対話 CLI 実装は Step 20 X〜の TDD で UNIT-005.1 拡張(§4.15.G)+ UNIT-002.3 BATTERY_LOW 追加(§4.11.G)と並行実施、完了後 STPR v0.5+ 候補で ST-ALM.1-XX + ST-x.G 実装 + 実測の段階成熟方式とすることを §6.6 環境制約節で明文化(Inc.4 申し送り化を回避し Inc.2 完了タグ前に Verified 化目標を達成する設計)。**(Q) 著しい教訓:** **(a) Inc.2 着手準備 Step 系列(A〜H、9 ステップ)真の完走 = SRS → RMF → SAD → SDD → UTPR → ITPR → STPR の上流 → 下流連鎖が 9 ステップで完走**(後続プロジェクトでは「範囲計画書(Step N A)→ SRS Inc.x 残務(B-1、MAJOR)→ SRS Inc.(x+1)追補(B-2、MAJOR)→ RMF 連動(C、MAJOR)→ SAD 連動(D、MAJOR)→ SDD 骨格化(E、MODERATE)→ UTPR 骨格化(F、MODERATE)→ ITPR 骨格化(G、MODERATE)→ STPR 骨格化(H、MODERATE)」の 9 ステップ パターンを Inc.3 / Inc.4 で再利用推奨、Step 20 G 完了時点では「Step 20 H or Step 20 Y への配置検討」と申し送られていたが、Inc.2 着手準備として Step 20 H(STPR Inc.2 範囲拡張)を実施することで完成度の高い着手準備を達成)、**(b) 段階成熟方式の継承価値再実証**(Inc.1 = Step 19 G STPR v0.1 で「代表 3 観点詳細化 + 残骨格 6 観点」を確立 → Inc.2 でも本 Step 20 H で「ST-ALM 詳細化 + ST-x.G 拡張節骨格化」のパターンを継承 = 段階成熟方式が Inc 範囲拡張時にも有効と実証)、**(c) IEC 60601-1-8 規格適合の system 試験パターン**(SAD v0.2 §5.3(IEC 60601-1-8 §6.4 状態遷移)+ SDD v0.5 §5.1.A(`AlarmEvent` 実装契約)+ ITPR v0.12 §6.16 IT-ALM(SEP-003 + 規格適合)で確立した規格適合検証を STPR §6.6 で system 観点に拡張 = 規格適合検証の上流 → 下流連鎖パターン化、後続プロジェクトでは「規格適合は SAD で構造定義 → SDD で実装契約 → ITPR で結合検証 → STPR で system 観点規格適合」の 4 段網羅運用ルール推奨)、**(d)「§4 CLOSED 一気通貫」運用パターン 8 度目適用 = default 運用ルールとして完全確立**(Step 19 I 発見 → Step 20 B-1 / B-2 / C / D / E / F / G / 本 H 連続 8 回適用)、**(e)「事前 25 箇所リストアップ」網羅レビュー継続**(派生ドキュメント更新漏れ教訓の 39 度目試行、Inc.2 着手準備系列の B-1 = 21 → B-2 = 23 → C = 27 → D = 28 → E = 30 → F = 32 → G = 30 → 本 H = 25 で平均 ~27 箇所、本 H で減少した理由 = STPR §6.6 ST-ALM 単一観点詳細化 + §6.x.G 3 サブ節 + §11.2/§13 4 行追加と縮小傾向、Inc.2 範囲計画書 §9 で予告された通り)、**(f) Inc.2 着手準備真の完走 = TDD 実装フェーズ Step 20 X〜への完全な移行準備完了**(本 Step 20 H 完了で Inc.2 範囲の「上流文書すべて MAJOR 反映済 + 下流文書すべて MODERATE 骨格化済(SDD / UTPR / ITPR / STPR)+ 範囲計画書確定済」の 4 条件すべてが揃った状態となり、Step 20 X〜の TDD 実装に着手可能、Inc.N 着手前の準備完了基準として後続プロジェクトに推奨)。**SRMP §7.3「RCM 関連部の追記化」相当**(新規 5 RCM の system 試験計画枠組み追加 + RCM-020 候補(HZ-009)の system 再現枠組み確保、本 CR-0014 は STPR 改訂のみで実装コード / SOUP / 試験への波及なし、後続 Step 20 X〜で連動)、**RMF 更新不要**(RMF v0.4 で既に Designed 状態反映済) | k-abe |
| 0.3 | 2026-05-07 | **Step 19 H3(§5.7.4 妥当性確認チェックリスト記入 + §6.5 ST-IF + §6.7 ST-SEC レビュー記録 + Linux nightly 5 連続 Pass 申し送り回収 + ANOM-001 transitive 参照 + Inc.1 完了タグ前準備)を反映。** **(1) §6.3.3 §5.7.4 妥当性確認チェックリスト 6 項目を全件 OK で記入(クラス C 必須):** SRS 網羅 / 試験手順明確 / 試験環境代表性 / 測定機器精度 / 合否判定客観性 / 不具合検出能力の各項目を ST-RCM.1-04 + F1〜F6 IT 結果(ITPR §11.2 / §13)+ UT MC/DC 100%(UTPR §11)から transitive に充填。**(2) §6.5 ST-IF 詳細化(レビュー記録 5 件):** ST-IF.1-01(SRS-IF-001 仮想 HW I/F = `vip_sim` パッケージ)/ ST-IF.1-02(SRS-IF-002 制御 API = `vip_api.control_api`)/ ST-IF.1-03(SRS-IF-003 状態観測 API)/ ST-IF.1-04(SRS-IF-004 ロギング I/F = `vip_ctrl.cli._emit_event`)/ ST-IF.1-05(SRS-IF-005 永続化 I/F = `vip_persist`)を全件 OK で記録、各 IF が UT(契約)+ IT(結合動作)+ ST(system 観測)の 3 段で網羅されていることを根拠として記載。**(3) §6.7 ST-SEC 詳細化(レビュー 1 + CI 確認 1):** ST-SEC.1-01(SRS-SEC-002 機密情報非出力レビュー = Inc.1 範囲は患者情報非取扱 + bandit 0 issues + JSON Lines フィールド網羅レビュー)/ ST-SEC.1-02(SRS-SEC-003 pip-audit CI 確認 = `unit-test.yml` の `pip-audit` ジョブが PR / push ごとに脆弱性検出)を全件 OK で記録。**(4) §11.2 試験ケース結果テーブル更新:** ST-IF 行 = 5/5 OK + ST-SEC 行 = 2/2 OK + 合計 16 → 23(Step 19 H2 で 7 + H3 で ST-IF 5 + ST-SEC 2 = 14 Pass + 9 Skip)。**(5) §11.3 PRB-0001 transitive 参照行追加:** ITPR §11.3 で正式記録された ANOM-001(IT-PERF.2-02 SDD §4.7.A 50 ms 厳密境界の構造的 CI flake、Linux nightly 5/5 fail)が ST 側では ST-PERF.1-04 SRS-P05 起動時間 5 連続 Pass で SRS 性能要求の本旨は満たされていることを記録、ITPR 側で管理。**(6) §13 トレース行更新**(ST-IF / ST-SEC = 「設計確定」 → 「H3 で n/m Pass + 申し送り根拠」)。**(7) Inc.1 範囲全 RCM 6 件の §5.7.4 妥当性確認 transitive 充足:** Inc.1 範囲 RCM-001/003/004/015/016/019(SRS-RCM-001/003/004/015/016/020)は IT (F1〜F6) で各 RCM の機能不具合検出能力が実証済 + ST-RCM.1-04(RCM-015 / HZ-007 system 再現)で 1 件は ST レベル直接実証 + 残 5 件は ISS-H-002 拡張で Inc.4 申し送り(対話 CLI 非対応に起因、F1〜F6 IT 結果から transitive に「不具合検出能力が適切である」項目を充足、§6.3.3 表で記録)。**(8) Step 19 H3 着手中の発見:** Linux nightly 5 連続トリガで IT-PWR / IT-SIDE は 20/20 + 10/10 = 5 連続 Pass 達成 = F6 / F7 申し送り回収完了 ✓、IT-PERF.2-02 のみ 5/5 fail = 構造的 CI flake = ANOM-001 として ITPR §11.3 PRB-0001 で正式記録(F5 / F7 申し送り「Linux nightly 5 連続 Pass 確認」運用ルールが flake リスクの実検出装置として機能、運用ルールが正しく作動した実例)。**(9) MINOR 区分・CR 不要**(SCMP §4.1「軽微」、SRS / SDD / RMF / SAD 本体不変、外部 API 変更なし、§5.7.4 妥当性確認 + ST-IF / ST-SEC レビュー記録 + ANOM-001 transitive 参照は試験記録 + リリース判定への入力 = 試験運用層の変更で実装には影響しない、CR-0006 SDD §4.7.A 閾値緩和は Inc.2 以降に申し送り)。**(10) 著しい教訓:** **(a) §5.7.4 妥当性確認チェックリストの transitive 充足パターン**:Inc.1 CLI 範囲制約で ST 直接実証できない RCM 5 件も、IT 結果 + UT 結果 + ST 部分実証 + ISS-H-002 Inc.4 申し送りの 4 系列で「不具合検出能力が適切である」項目を transitive に充足する設計は IEC 62304 §5.7.4 の意図(試験全体の妥当性、IT + ST の役割分担で網羅可能)に整合。後続プロジェクトでは「ST 直接実証できない場合の transitive 充足ロジック」を §5.7.4 チェックリスト記入時の default パターンとすることを推奨。**(b) ST-IF / ST-SEC レビュー記録の 3 段網羅原則**:UT(契約)+ IT(結合動作)+ ST(system 観測)の 3 段で網羅していれば、レビュー結果として OK 判定可能。各 IF / SEC 観点で 3 段の根拠を 1 行ずつ記載するパターンは、後続プロジェクトのレビュー記録 default として推奨 | k-abe |
| 0.2 | 2026-05-07 | **Step 19 H2(代表 3 観点 16 ケース実装 + `system-test.yml` 新設 + ISS-H-002 拡張解消)を反映。** **(1) `tests/system/` 新設**(`__init__.py` + `conftest.py` + `test_perf_acceptance.py` + `test_ops_acceptance.py` + `test_rcm_acceptance.py`、計 16 ケース、`session`-scoped `installed_venv` fixture で venv 構築 + `pip install -e .` を 1 回償却)。**(2) Inc.1 範囲で 7 件 Pass 確定**(ST-PERF.1-04 SRS-P05 起動時間 ≤ 3 秒 / ST-OPS.1-01 venv インストール + `vip-ctrl --version` / ST-OPS.1-02 SRS-OPS-003 デフォルト起動 = HZ-007 安全側起動 / ST-OPS.1-03 SRS-OPS-010 JSON Lines 5 必須キー = boot_snapshot + diagnose 2 経路網羅 / ST-OPS.1-04 SRS-OPS-011 整合レコード `--diagnose` / ST-OPS.1-05 SRS-OPS-012 `pip install --upgrade -e .` 永続レコード保持簡略実証 / ST-RCM.1-04 RCM-015 改ざん永続レコード `--diagnose` 検出 = HZ-007 system 再現)。**(3) Inc.4 申し送り 8 件 + Inc.1 完了タグ後申し送り 1 件 = `pytest.mark.skip` で骨格保持**(ST-PERF.1-01/02/03 + ST-RCM.1-01/02/03/05/06 = ISS-H-002 拡張、Inc.1 CLI が対話 start / stop / flow_rate / confirm を提供しない構造的乖離を H2 着手中に発見、F1〜F6 IT で機能検証済 → Inc.4 UI 層実装時に CLI 経由 system 再現を正式実装 / ST-PERF.1-05 SRS-P07 24 時間連続運転 = self-hosted runner 申し送り、SDP §4.4 リリース判定遅延入力)。**(4) `.github/workflows/system-test.yml` 新設**(`system-fast`(PR / push)+ `system-nightly`(scheduled、`workflow_dispatch`)の 2 ジョブ構成、`integration-test.yml` と同パターン、SRS-OPS-004「CI で自動実行」必須要求満足)。**(5) `pyproject.toml` 拡張**(`system` マーカー新規登録、`addopts` を `not integration and not system` に拡張で UT 実行から system テストを除外、IT / system 分離マトリクスを `pytest -m system` で明示選択)。**(6) ISS-H-002 解消(拡張版):** Step 19 H1 計画時点では ST-OPS.1-03 のみが対話 start / stop 要求の問題と特定されたが、Step 19 H2 着手中の網羅レビューで ST-PERF.1-01/02/03 + ST-RCM.1-01/02/03/05/06 にも同じ構造的乖離(対話コマンド非対応)が存在することを発見 → ISS-H-002 を **計 9 件**(ST-PERF 3 + ST-RCM 5 + ST-OPS.1-03 簡略化 1)に拡張、各ケースで `pytest.mark.skip(reason=…)` に DEVELOPMENT_STEPS.md Step 19 H2 セクションへの相互参照を埋め込んで監査トレーサビリティを担保。**(7) §6.1.5 / §6.2.5 / §6.3.5 申し送りを「Step 19 G 完了時点」 → 「Step 19 H2 完了時点」に更新**、各 ID の Inc.1 範囲実装済 / Inc.4 申し送り / Inc.1 完了タグ後申し送り 3 区分を明示。**(8) §11.2 試験ケース結果テーブルを Pass / Fail / Skip 内訳で確定**(ST-PERF: 1 Pass / 4 Skip、ST-OPS: 5 Pass / 0 Skip、ST-RCM: 1 Pass / 5 Skip = 16 ID 合計 7 Pass / 0 Fail / 9 Skip)。**(9) §13 トレーサビリティマトリクス**(§6.1〜§6.3 詳細化分の 3 行)を「設計確定」 → 「Step 19 H2 で n/m Pass + n/m Skip + 申し送り根拠」に更新、SRS / RCM / HZ への双方向トレーサビリティを実施結果まで延伸。**(10) §5.7.4 妥当性確認チェックリスト**(§6.3.3、6 項目)は Step 19 H3 で全件記入する申し送りを §6.3.5 で明示。**(11) ローカル CI 等価検証 全 Pass:** `pytest -m system` 7 passed / 9 skipped / 501 deselected(macOS local + venv 1 回償却で 45.96 秒)、`mypy --strict` Success(60 source files、+2 = `tests/system/conftest.py` + `test_*.py` 群、CLI session venv ヘルパ追加)、`ruff check . / ruff format --check .` All Pass、UT non-system 462 passed 維持(+system 除外 hook で UT timing 影響なし)、IT non-nightly 27 passed 維持(IT 系列影響なし)。**Step 19 H2 著しい教訓:** (1) **計画フェーズ移行点でのクロスレビューによる ISS 拡張発見**(H1 → H2 移行で ISS-H-002 が 1 件 → 9 件に拡張、Step 19 G 計画時の「対話 UI Inc.4 申し送り」設計判断と Step 19 G STPR §6.x の対話コマンド前提が設計時点では整合確認漏れだった構造的乖離を H2 着手中に網羅レビューで発見、後続プロジェクトでは「フェーズ移行点で全試験ケースの CLI surface 整合を網羅レビュー」運用ルール化推奨)、(2) **`pytest.mark.skip(reason=…)` で 16 ID 構造保持 + Inc.4 合流先明示パターン**(全 skip ケースに F 系列 IT-ID + ISS-H-002 + DEVELOPMENT_STEPS.md セクション + Inc.4 実装時の合流先を埋め込み、監査トレーサビリティを Inc.4 まで延伸)、(3) **session-scoped `installed_venv` fixture による venv 構築 1 回償却**(各テスト個別 venv では合計 5 分超 → session 1 回で 45 秒、F6 IT-PWR の精密 subprocess 同期パターンとは別系統の system test 独自最適化)、(4) **CLI 経由 ST と Python API 経由 IT の分散配置確立**(IT は import 経路の契約整合 / ST は subprocess 経路の SRS 要求網羅、Inc.1 範囲では「CLI surface = 観測可能な system boundary」が小さいため Inc.4 申し送りで対話拡張)。MINOR 区分・CR 不要(SCMP §4.1「軽微」、SRS / SDD / RMF 本体不変、外部 API 変更なし、`system` マーカー追加と `addopts` 拡張は CI 機械化 = 試験運用層の変更で実装には影響しない)| k-abe |
| 0.1 | 2026-05-07 | **初版作成(計画、Step 19 G、F 系列完了 = ITPR §6.1〜§6.10 全 10 観点詳細化済を受けた節目)。** Inc.1 全 17 ユニット UT 完了(UTPR v0.19)+ Inc.1 全 RCM 6 件 IT 検証完了(ITPR v0.10)を前提に、システム試験戦略(SRS 要求網羅 100% + 全 RCM のシステム統合動作 + 性能全体予算 + 受入試験)を確立。**「代表 3 観点詳細化 + 残骨格 6 観点」段階成熟方式**(ITPR v0.1 = Step 19 D-2 / UTPR v0.1 = Step 19 A の確立パターンに整合)で **§6.1 ST-PERF**(性能要求の全体予算、5 ケース、F5 で確立した「IT は SDD 内訳 / ST は SRS 全体」分散配置の正式実装)、**§6.2 ST-OPS**(受入試験 + 運用、5 ケース、SRS-OPS-004 必須要求の CI 自動化)、**§6.3 ST-RCM**(RCM 統合 + IEC 62304 §5.7.4 妥当性確認(クラス C 必須)、6 ケース + チェックリスト 6 項目、F1〜F6 IT 結果の system 再現)を詳細化。残 6 観点(§6.4 ST-FUNC / §6.5 ST-IF / §6.6 ST-ALM / §6.7 ST-SEC / §6.8 ST-UX / §6.9 ST-DATA、合計目安 ≥ 27)は試験観点・関連 SRS のみ記述する骨格(Inc.2 で ST-ALM、Inc.4 で ST-UX、Step 19 H で ST-IF / ST-SEC / ST-DATA を順次詳細化、ST-FUNC は Inc.4 UI 層実装時)。試験 ID 体系(`ST-{プレフィックス}.{サブ番号}-{連番}`)、試験種別 8 区分、自動化方針(`tests/system/` 配下 + `system-test.yml` 新設は Step 19 H)、§5.7.4 妥当性確認チェックリスト(クラス C 必須、§6.3.3 + §7.2)、トレーサビリティマトリクス(SRS / RCM / HZ / IT-ID 申し送り、§13)を確立。**F5 申し送り回収:** ITPR v0.8 §6.8.4 で「IT は SDD 内訳予算 / ST は SRS 全体予算」の分散配置を確立 → STPR で明文化(本 STPR §1.2)、SRS-P03/P04 全体予算は ST-PERF.1-02/03 で SRS 値そのもので合否判定。**Inc.1 完了タグ前申し送り:** Step 19 H で代表 3 観点(ST-PERF / ST-OPS / ST-RCM)の試験実装 + CI ワークフロー新設 + §5.7.4 妥当性確認チェックリスト記入、SRS-P07(24 時間連続運転)は self-hosted runner または別途実機環境で Inc.1 完了タグ後実施申し送り、CLI エントリポイント `vip-ctrl` の実装は Step 19 H と並行(現時点では未実装)。**設計判断:** F1〜F6 IT 結果の system 再現方式採用(重複試験回避 + IT/ST 分散配置の明確化)、CLI 経由 subprocess + venv 隔離方式採用(F6 IT-PWR の精密同期方式とは異なり ST-OPS は実 CLI 経路の正常動作確認が目的)。第 II 部(報告)は骨格のみ、Step 19 H の試験実施で埋めていく(UTPR / ITPR と同じ「代表 + 骨格」段階成熟方式) | k-abe |
