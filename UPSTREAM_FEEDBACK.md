# iec62304_template への修正要望

**ドキュメント ID:** UF-VIP-001
**作成日:** 2026-04-21
**対象リポジトリ:** [grace2riku/iec62304_template](https://github.com/grace2riku/iec62304_template)
**位置づけ:** 本プロジェクト(仮想輸液ポンプ / クラス C)でテンプレートを運用する中で発見した改善提案を記録し、upstream テンプレートへ随時フィードバックするための台帳。

---

## 本書の目的

本プロジェクトは [grace2riku/iec62304_template](https://github.com/grace2riku/iec62304_template) を clone し `.git` を破棄して独立リポジトリ化したもの(DEVELOPMENT_STEPS.md Step 0 参照)。テンプレートを実プロジェクトで運用する過程で発見した「テンプレート側で改善すべき点」を本書に蓄積し、upstream に Issue や Pull Request として還元する。

本書は監査成果物ではなく **プロジェクト運用補助文書** であるが、構成アイテム(CI-DOC-UPSTREAM)として CIL に登録し、Git 管理下に置く。

## 記録ルール

### エントリ ID 形式

`UF-NNN`(Upstream Feedback、3 桁連番)。NNN は本書内でのローカル連番であり、GitHub Issue 番号とは独立。upstream に Issue 起票した際は「upstream Issue」欄に Issue 番号を記録する。

### 記録項目

| 項目 | 内容 |
|------|------|
| ID | `UF-NNN` |
| 発見日 | `YYYY-MM-DD` |
| 発見経緯 | 本プロジェクトのどの Step / 作業で発見したか |
| 現状(upstream 側) | テンプレートでの現状の問題点 |
| 提案 | 具体的な修正提案 |
| 優先度 | High(安全/整合性問題)/ Medium(運用効率)/ Low(改善提案) |
| 状態 | 未提案 / 提案済み(Issue #NNN) / 受領済み(PR #NNN マージ) / 却下 |
| upstream Issue | GitHub Issue URL(提案後に記入) |
| 関連 DEVELOPMENT_STEPS | 本リポジトリ内の関連 Step |

### 更新タイミング

- 新しい修正要望を発見した際に即時追記
- upstream に提案した際に「状態」欄を更新
- upstream で受領/却下された際に「状態」欄を更新

---

## 修正要望一覧

### UF-001 — 問題報告 ID の衝突回避(`PR-NNNN` → `PRB-NNNN`)

| 項目 | 内容 |
|------|------|
| 発見日 | 2026-04-18 |
| 発見経緯 | Step 6(SPRP 作成)および Step 8(ID 表記統一)。支援プロセス計画を連続で書いた際に、問題報告(Problem Report)の ID `PR-NNNN` が GitHub の Pull Request(PR)と混同されることに気付いた |
| 現状(upstream 側) | テンプレートの SPRP / SCMP / SMP 等で、問題報告 ID を `PR-NNNN` と表記。GitHub Flow を採用する現代のプロジェクトでは、コミット履歴・Issue・PR 番号と区別が付きにくい |
| 提案 | 問題報告 ID を `PRB-NNNN`(**P**ro**B**lem report)に変更。略語表・ID プレフィックス表・関連ドキュメント本文を一括更新。本プロジェクトの CLAUDE.md「ID 体系の本プロジェクト固有規則」参照 |
| 優先度 | Medium(監査整合性に影響)|
| 状態 | 受領済み(PR #15 マージ、2026-04-21) |
| upstream Issue | <https://github.com/grace2riku/iec62304_template/issues/6>(PR: <https://github.com/grace2riku/iec62304_template/pull/15>) |
| 関連 DEVELOPMENT_STEPS | Step 6、Step 8 |

### UF-002 — Issue テンプレートの `labels:` frontmatter だけではラベルが作成されない

| 項目 | 内容 |
|------|------|
| 発見日 | 2026-04-19 |
| 発見経緯 | Step 14a(CR-0001 起票時)。Issue テンプレート frontmatter の `labels: change-request` 指定だけではラベル本体がリポジトリに登録されず、`gh issue create --label change-request` がエラー終了した |
| 現状(upstream 側) | Issue テンプレート(`.github/ISSUE_TEMPLATE/problem_report.md`、`change_request.md`)の frontmatter に `labels:` を指定しているが、ラベル本体を作成する手順やスクリプトが README 等に記載されていない |
| 提案 | 以下のいずれかを追加:(a) README に「Issue テンプレート使用前のラベル作成手順」を明記(`gh label create change-request --color 0366d6` 等)、(b) リポジトリ初期化スクリプト(`scripts/setup_labels.sh`)を同梱し、`change-request`、`problem-report`、`enhancement` 等の必須ラベルを一括作成可能にする |
| 優先度 | Medium(新規プロジェクト立ち上げ時の躓きポイント)|
| 状態 | 受領済み(PR #16 マージ、2026-04-21) |
| upstream Issue | <https://github.com/grace2riku/iec62304_template/issues/7>(PR: <https://github.com/grace2riku/iec62304_template/pull/16>) |
| 関連 DEVELOPMENT_STEPS | Step 14a |

### UF-003 — `gh` コマンドのデフォルト repo 解決が upstream を向く問題

| 項目 | 内容 |
|------|------|
| 発見日 | 2026-04-18(Step 9 で発覚)、2026-04-21(Step 14b で再発見)|
| 発見経緯 | Step 9(GitHub インフラ整備時)で CI ステータス確認が upstream(`grace2riku/iec62304_template`)を参照していて失敗。Step 14b の 24h インターバル検証時に `gh issue view 1` が再び upstream を参照し、本プロジェクトの Issue #1 を取得できなかった |
| 現状(upstream 側) | テンプレートを clone + `.git` 破棄 + `git init` + 新リポジトリとして派生運用するフローで、`upstream` remote を残すと `gh` コマンドのデフォルト repo 解決が upstream を向くケースがある。本テンプレートの派生運用ガイドにはこの注意が記載されていない |
| 提案 | README の「テンプレートから派生リポジトリを作る手順」セクションに以下を追記:(a) `upstream` remote を残す場合は `gh repo set-default <自リポジトリ>` を実行するか、(b) 全ての `gh` コマンドで `--repo <自リポジトリ>` を明示する、(c) CI 確認時は `gh run list --repo <自リポジトリ>` を徹底する |
| 優先度 | High(監査時に CI 状態の誤認に繋がる)|
| 状態 | 受領済み(PR #17 マージ、2026-04-21) |
| upstream Issue | <https://github.com/grace2riku/iec62304_template/issues/8>(PR: <https://github.com/grace2riku/iec62304_template/pull/17>) |
| 関連 DEVELOPMENT_STEPS | Step 9 教訓、Step 14b 教訓 |

### UF-004 — CI 失敗の長期放置リスクへの注意喚起

| 項目 | 内容 |
|------|------|
| 発見日 | 2026-04-21 |
| 発見経緯 | Step 14b。Step 11 以降 5 ステップ連続で CI が失敗していたが、気付かずに進行していた(Step 9 の教訓に「CI は本リポジトリで一度も成功していなかった」と記録済みだったにもかかわらず、Step 11〜13 で再発見できなかった) |
| 現状(upstream 側) | `docs-check.yml` は設定済みだが、CI 失敗を開発者に伝達する仕組みや運用ガイダンスが README に記載されていない |
| 提案 | 以下のいずれかを追加:(a) README または `docs-check.yml` のコメントに「CI 失敗は次ステップ進行前に必ず修正すること」のガイダンス追記、(b) CI 失敗時の Slack / メール / GitHub 通知設定サンプルの提供、(c) Branch Protection Rule で required status checks に `docs-check` ジョブを設定する手順の明記(本プロジェクトでは既に適用済、ただし Step 9 で設定時に judgment に悩んだ) |
| 優先度 | High(安全クリティカルプロジェクトでの監査リスク)|
| 状態 | 受領済み(PR #18 マージ、2026-04-21) |
| upstream Issue | <https://github.com/grace2riku/iec62304_template/issues/9>(PR: <https://github.com/grace2riku/iec62304_template/pull/18>) |
| 関連 DEVELOPMENT_STEPS | Step 11〜13、Step 14b 教訓 |

### UF-005 — SRS テンプレート §4.9 の表列数不整合(MD056)可能性

| 項目 | 内容 |
|------|------|
| 発見日 | 2026-04-21 |
| 発見経緯 | Step 14b。本プロジェクトの SRS-VIP-001 v0.1 で §4.9 表の SRS-OPS-011 行が列数不整合(Expected 3, Actual 4)を持っていた。本プロジェクト独自に書き加えた可能性もあるが、テンプレート側に同種の不整合が残っていないか確認が望ましい |
| 現状(upstream 側) | テンプレートの SRS 雛形 `5.2_software_requirements_analysis/software_requirements_specification.md` に「推奨」フラグの表記揺れが混入している可能性あり。本プロジェクトでは修正済だが、upstream 側は未確認 |
| 提案 | (a) upstream の SRS テンプレートに対して `markdownlint-cli2` を実行し MD056 エラーの有無を確認、(b) 存在する場合は修正、(c) テンプレート側の CI で docs-check を常時 Pass 状態に保つ |
| 優先度 | Medium(派生プロジェクトに不整合が伝播するリスク)|
| 状態 | 受領済み(PR #19 マージ、2026-04-21) |
| upstream Issue | <https://github.com/grace2riku/iec62304_template/issues/10>(PR: <https://github.com/grace2riku/iec62304_template/pull/19>) |
| 関連 DEVELOPMENT_STEPS | Step 14b |

### UF-006 — マージ後アクション(台帳クローズ記録等)の運用ルート明文化

| 項目 | 内容 |
|------|------|
| 発見日 | 2026-04-21 |
| 発見経緯 | Step 14c。CR クローズ記録として CRR v0.3 を更新する際、これを PR 化すると「CR クローズ用 CR」が必要になり循環する。やむを得ず admin bypass で main に直接 push したところ `Bypassed rule violations: 4 of 4 required status checks are expected` の警告が発生 |
| 現状(upstream 側) | SCMP §4.1.2 の軽微区分は「誤字、コメント、整形、CI 設定の非機能変更」を列挙しているが、「CR マージ後の台帳クローズ記録」のような運用メタ作業の扱いが明文化されていない |
| 提案 | SCMP テンプレートの §4.1.2 に以下を追記:「マージ後アクションの軽微台帳更新(CRR クローズ日記入、CIL バージョン昇格の反映、DEVELOPMENT_STEPS.md への Step 追記等)は、事前にローカル lint(`npx markdownlint-cli2@<CI 相当バージョン>` 等)を実施した上で直接 push を許可する。ただし bypass ログが残ることを認識し、各 Inc. 完了時の CCB 監査で bypass 回数をレビューする」|
| 優先度 | High(監査時の指摘リスク軽減、全派生プロジェクトに影響)|
| 状態 | 受領済み(PR #20 マージ、2026-04-21) |
| upstream Issue | <https://github.com/grace2riku/iec62304_template/issues/11>(PR: <https://github.com/grace2riku/iec62304_template/pull/20>) |
| 関連 DEVELOPMENT_STEPS | Step 14c 教訓 |

### UF-007 — CIL の自己参照および派生ドキュメント更新漏れの予防

| 項目 | 内容 |
|------|------|
| 発見日 | 2026-04-21 |
| 発見経緯 | Step 14d。CIL v0.2 コミット時に以下 3 件の更新漏れが発生していた:(a) CI-DOC-SAD が「未着手」のまま(Step 12c で SAD v0.1 完成済)、(b) CI-DOC-CCB が「未着手」のまま(Step 10c で CCB v0.1 完成済)、(c) **CI-DOC-CIL 自己参照が v0.1 のまま**(CIL 自身は v0.2 に昇格しているのに自己参照行は v0.1) |
| 現状(upstream 側) | CIL テンプレートには「更新時の全走査チェックリスト」が記載されていない。`CI-DOC-CIL` 行が CIL 自身を指す自己参照であることも明示されていない |
| 提案 | CIL テンプレート末尾に「更新時チェックリスト」を追加:(1) 今回の CR で直接変更する CI のバージョン・状態を更新した、(2) **自己参照(CI-DOC-CIL)のバージョンと状態を更新した**、(3) 過去ステップで完成したが CIL に未反映の CI が無いか全走査した、(4) ベースライン履歴への追加が必要かを判定した、(5) 改訂履歴に v0.N エントリを追加した |
| 優先度 | Medium(派生プロジェクトで同種の漏れが頻発するリスク)|
| 状態 | 受領済み(PR #21 マージ、2026-04-21) |
| upstream Issue | <https://github.com/grace2riku/iec62304_template/issues/12>(PR: <https://github.com/grace2riku/iec62304_template/pull/21>) |
| 関連 DEVELOPMENT_STEPS | Step 14d 教訓 |

### UF-008 — CCB インターバル時間のプロジェクト規模別推奨値の明示

| 項目 | 内容 |
|------|------|
| 発見日 | 2026-04-21 |
| 発見経緯 | Step 15a(CR-0002)。本プロジェクト(学習目的・仮想)では 24 時間インターバルが学習効率と乖離し、1 分インターバルに改訂した。upstream テンプレートは実機前提で 24 時間のみを記述しており、学習/小規模プロジェクトで運用する際の参考値が無い |
| 現状(upstream 側) | CCB-VIP-001 テンプレート §5.4 は 24 時間インターバルのみを記述。学習・小規模・中規模・実機のプロジェクト規模による推奨値のグラデーションが無い |
| 提案 | CCB テンプレート §5.4 に「プロジェクト規模別推奨インターバル値」の表を追加:(a) 学習・デモプロジェクト = 1 分以上、(b) 小規模単独開発(実機未搭載)= 数時間、(c) 中規模チーム開発 = 12〜24 時間、(d) 医療機器実機搭載プロジェクト = 24 時間以上を推奨。派生プロジェクト側は自プロジェクトに合う値を選んで明記する運用 |
| 優先度 | Low(テンプレートの使い勝手改善、既存値を変更する必要はなし)|
| 状態 | 受領済み(PR #22 マージ、2026-04-21) |
| upstream Issue | <https://github.com/grace2riku/iec62304_template/issues/13>(PR: <https://github.com/grace2riku/iec62304_template/pull/22>) |
| 関連 DEVELOPMENT_STEPS | Step 15a |

### UF-009 — 日付書式 CI チェックの欧州順(`DD/MM/YYYY`)検出強化

| 項目 | 内容 |
|------|------|
| 発見日 | 2026-04-21 |
| 発見経緯 | Step 14/15 作業中、`docs-check.yml` の日付書式チェック正規表現を確認した際に発見 |
| 現状(upstream 側) | `.github/workflows/docs-check.yml` の日付書式ポリシー検査は `\b[0-9]{4}/[0-9]{1,2}/[0-9]{1,2}\b` でスラッシュ区切りの `YYYY/MM/DD` 形式のみを検出。CLAUDE.md で **使用禁止** と明記している `DD/MM/YYYY`(欧州順)や `MM/DD/YYYY`(米国順)、`4/17` 等は検出されない |
| 提案 | 正規表現を以下に拡張:(a) `\b[0-9]{1,4}/[0-9]{1,2}/[0-9]{1,4}\b` で全形式のスラッシュ区切りを検出、(b) `\b[A-Z][a-z]+ [0-9]+,? ?[0-9]{4}\b` で自然言語表記(`April 17, 2026` 等)を検出、(c) 許容例外として `{{YYYY-MM-DD}}` プレースホルダと数式中のスラッシュ(`1/10`)を除外ルールに追加 |
| 優先度 | Low(本プロジェクトでは実害発生していない)|
| 状態 | 受領済み(PR #23 マージ、2026-04-21) |
| upstream Issue | <https://github.com/grace2riku/iec62304_template/issues/14>(PR: <https://github.com/grace2riku/iec62304_template/pull/23>) |
| 関連 DEVELOPMENT_STEPS | Step 15a(運用中に発見)|

---

## upstream への提案手順(参考)

1. 本書のエントリ状態が「未提案」のものを優先度 High から順に選定
2. upstream リポジトリに Issue 起票:
   - リポジトリ: <https://github.com/grace2riku/iec62304_template/issues/new>
   - タイトル: `[UF-NNN] <修正要望の要約>`
   - 本文: 本書の該当エントリ内容 + 本プロジェクト(`grace2riku/virtual_infusion_pump_classC`)の DEVELOPMENT_STEPS.md 該当 Step へのリンク
3. 起票後、本書の「状態」欄を「提案済み(Issue #NNN)」に更新、「upstream Issue」欄に URL を記入
4. 可能であれば Pull Request も送付(upstream 受領の促進)
5. upstream 受領時は「状態」欄を「受領済み(PR #NNN マージ)」に更新

---

## 改訂履歴

| バージョン | 日付 | 変更内容 | 変更者 |
|----------|------|---------|--------|
| 0.3 | 2026-04-21 | upstream リポジトリ(`grace2riku/iec62304_template`)で UF-001〜UF-009 に対応する Issue #6〜#14 が全て PR #15〜#23 経由でマージ済み(stateReason=COMPLETED)となったことを確認。全 9 エントリの状態を「提案済み(Issue #N、2026-04-21)」→「受領済み(PR #M マージ、2026-04-21)」に更新し、「upstream Issue」列に対応 PR URL を併記 | k-abe |
| 0.2 | 2026-04-21 | 9 件の初期エントリ(UF-001〜UF-009)を upstream リポジトリ(`grace2riku/iec62304_template`)へ Issue #6〜#14 として一括起票。全エントリの状態を「未提案」→「提案済み(Issue #N、2026-04-21)」に更新、「upstream Issue」列に URL を記入 | k-abe |
| 0.1 | 2026-04-21 | 初版作成。本プロジェクト運用中(Step 0 〜 Step 15a)に発見した修正要望 9 件(UF-001 〜 UF-009)を初期エントリとして登録 | k-abe |
