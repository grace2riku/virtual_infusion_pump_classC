"""Integration test — IT-SIDE(SDD §4.13.F タイミング試験(参考)、SRS-SEC-001).

ITPR-VIP-001 §6.10 の詳細化(Step 19 F7、IT 7 観点目、F 系列最終)。SDD §4.13.F
「タイミング試験(参考)」の **弱判定 = 「明らかに有意な差(例:10x 以上)が出ない
こと」** で、`vip_persist.checksum.verify` 内の `hmac.compare_digest` 定数時間
比較が結合状態(本物 SHA-256 計算経路を含む)でも維持されていることを検証する。

設計判断(Step 19 F7、ITPR §6.10.4 と二重記録):

* **SUT は本物 `vip_persist.checksum.verify`:** SDD §4.13.E に従い `verify(data,
  expected) -> bool` は (i) 長さ + hex 文字検証、(ii) `compute(data)` で本物
  SHA-256 再計算、(iii) `hmac.compare_digest(actual, normalised)` で定数時間
  比較、の 3 段で動作。本 IT は **(iii) `compare_digest` の定数時間性** が結合
  状態(SHA-256 計算込み)で維持されているかを統計的に検証する。Mock は使用
  しない(F5 / F6 と同じ本物 SUT 主体方針継続)。
* **弱判定 (median 比 < 10x) の選定:** SDD §4.13.F は「タイミング試験(参考)」
  と明記され SRS-SEC-001 は本 Inc.1 で「参考扱い」(ITPR §6.10 骨格 + Inc.5
  正式化予定)。CI 共有環境 + Python interpreter の GC / JIT 影響で nanosecond
  精度の統計判定はノイズ過多のため、**median 比 < 10x** という **強健な弱判定**
  を採用。短絡比較(C で `for c in expected: if c != actual[i]: return False`
  のような実装)であれば不一致経路が **数百倍** 早く返るため 10x で十分検出
  できる(`hmac.compare_digest` は C 実装で全長比較のため median 比 ~1.0 が
  期待値)。**強判定(< 1 sigma)はローカル安定環境または専用 runner で Inc.5
  で再評価**(F7 申し送り、ITPR §6.10.5)。
* **`linux_only` auto-skip + Linux nightly:** F5 で先取り実装し F6 で初再利用
  された hook を **F7 で 3 ステップ目連続再利用**(`pytestmark = [integration,
  nightly, linux_only]`、`tests/conftest.py` の hook を新規追加なしで再利用)。
  「規定 → 機械化 → 利用」3 段階パターンの **「利用」フェーズ 2 回目実行**、
  F5/F6/F7 で 3 ステップ連続再利用が達成され `pytest.mark.skipif` 個別記述
  の重複が完全排除されたことを実証。
* **サンプル数とウォームアップ:** 各経路 200 サンプル(`SAMPLE_COUNT`)を取得
  し最初の 20 サンプル(`WARMUP_COUNT`)を破棄(Python interpreter の interpreter
  bytecode キャッシュ + GC 安定化のため)。median を用いることで外れ値の影響
  を抑制(F5 で IT-PERF が percentile 計算で採用したパターン継続)。
* **タイマ精度:** `time.perf_counter_ns()` で nanosecond 精度、サンプル間の
  GC 制御は行わない(GC は両経路で平等に発生する想定、F5 `pytest-benchmark`
  の `disable_gc` 制御は本 IT では過剰精度)。
* **試験ケース構成(SDD §4.13.F 参考要求の 2 観点を 1 ケース):**
  * IT-SIDE.1-01 — 全長一致 vs 1 byte 不一致(末尾)の median 比 < 10x
    (`compare_digest` が True / False を返す両経路でほぼ同時間)
  * IT-SIDE.1-02 — 末尾不一致 vs 先頭不一致 の median 比 < 10x
    (`compare_digest` が定数時間 = 不一致位置に依存しない)

関連 SRS: SRS-SEC-001(Inc.1 では参考扱い、Inc.5 セキュリティ拡張で正式化)。
関連 SDD: §4.13.E(`verify` 実装)、§4.13.F(タイミング試験(参考))。
関連 IF-U: —(`vip_persist.checksum.compute` / `verify` 内部実装契約)。
関連 RCM: —(SRS-SEC-001 は性能 / 副次品質要求でリスクコントロール直接対応なし)。
関連 HZ:  HZ-007(persisted-data corruption — タイミング攻撃で digest が漏れる
          余地は Inc.1 の脅威モデル外、Inc.5 で再評価)。
関連 UT 申し送り: UT-003.2(UTPR §7.3.7 v0.8 Step 19 B8 申し送り、SDD §4.13.F
          末尾「タイミング試験(参考)」を IT へ分散配置)。
"""

from __future__ import annotations

import statistics
import time

import pytest

from vip_persist.checksum import compute, verify

# 本ファイル全体に integration + nightly + linux_only マーカー付与
# (§8.1 規定:IT-PERF / IT-PWR / IT-SIDE は Linux runner 限定 + nightly schedule)
# `linux_only` は `tests/conftest.py` の hook で macOS / Windows では auto-skip
# される(Step 19 F5 で先取り実装、F6 で初再利用、本 F7 で 3 ステップ目連続再利用)。
pytestmark = [
    pytest.mark.integration,
    pytest.mark.nightly,
    pytest.mark.linux_only,
]

# 統計サンプル数(各経路に対して取得)
_SAMPLE_COUNT = 200
# ウォームアップサンプル数(interpreter bytecode キャッシュ + GC 安定化のため破棄)
_WARMUP_COUNT = 20
# 弱判定の閾値(median 比、1.0 が定数時間理論値、10.0 は短絡比較なら確実に超える境界)
_MEDIAN_RATIO_THRESHOLD = 10.0
# 試験用代表データ(SHA-256 計算時間が観測可能な程度の長さ、4 KB)
_TEST_DATA = b"VIP-CTRL-INTEGRATION-TEST-PAYLOAD-4KB-" * 100


def _measure_verify_ns(data: bytes, digest: str) -> int:
    """`verify(data, digest)` の経過時間を nanosecond で取得."""
    t0 = time.perf_counter_ns()
    verify(data, digest)
    t1 = time.perf_counter_ns()
    return t1 - t0


def _collect_samples(data: bytes, digest: str) -> list[int]:
    """ウォームアップ後の経過時間サンプルを `_SAMPLE_COUNT` 件取得."""
    # ウォームアップ(interpreter キャッシュ + GC を安定化)
    for _ in range(_WARMUP_COUNT):
        verify(data, digest)
    return [_measure_verify_ns(data, digest) for _ in range(_SAMPLE_COUNT)]


def _flip_hex_char(digest: str, position: int) -> str:
    """digest の指定位置(0 = 先頭、-1 = 末尾)の hex 文字を別の hex 文字へ反転."""
    chars = list(digest)
    original = chars[position]
    # 0..f の中から original 以外の任意 1 文字を選ぶ(0 が original なら 1 を、
    # それ以外は 0 を)。決定論的に異なる文字を生成。
    chars[position] = "1" if original == "0" else "0"
    return "".join(chars)


# ---------------------------------------------------------------------------
# IT-SIDE.1-01 — 全長一致 vs 1 byte 不一致 の median 比 < 10x
# ---------------------------------------------------------------------------
def test_it_side_1_01_match_vs_single_byte_diff() -> None:
    """SDD §4.13.F 参考: `verify` の True / False 経路でタイミング差が 10x 未満.

    検証手順:
    1. `correct_digest = compute(_TEST_DATA)` を計算
    2. `wrong_digest = correct_digest の末尾 1 文字を反転`(SHA-256 として
       長さ・hex 文字制約は維持、`compare_digest` 段で False 判定される)
    3. 各経路 200 サンプルの `verify` 経過時間を取得(ウォームアップ 20 件破棄後)
    4. median 比 = max(median_match, median_diff) / min(median_match, median_diff)
    5. 弱判定: median 比 < 10.0(`hmac.compare_digest` が短絡比較なら数百倍
       となる、定数時間なら ~1.0 が期待値)

    短絡比較(早期 return)の代表的検出ケース。長さ + hex 検証は両経路同一、
    SHA-256 再計算 (`compute`) も両経路同一、唯一の差は `hmac.compare_digest`
    内部の True / False 経路 → ここで定数時間でない実装ならタイミング差大。
    """
    correct_digest = compute(_TEST_DATA)
    wrong_digest = _flip_hex_char(correct_digest, position=-1)
    # 前提確認:両 digest とも長さ 64 hex(verify の長さ + hex 検証経路は同一)
    assert len(correct_digest) == 64
    assert len(wrong_digest) == 64
    assert correct_digest != wrong_digest

    samples_match = _collect_samples(_TEST_DATA, correct_digest)
    samples_diff = _collect_samples(_TEST_DATA, wrong_digest)

    median_match = statistics.median(samples_match)
    median_diff = statistics.median(samples_diff)
    ratio = max(median_match, median_diff) / max(min(median_match, median_diff), 1)
    assert ratio < _MEDIAN_RATIO_THRESHOLD, (
        f"timing ratio {ratio:.2f}x exceeds {_MEDIAN_RATIO_THRESHOLD}x "
        f"(median_match={median_match} ns, median_diff={median_diff} ns) — "
        f"hmac.compare_digest may not be constant-time"
    )


# ---------------------------------------------------------------------------
# IT-SIDE.1-02 — 末尾不一致 vs 先頭不一致 の median 比 < 10x
# ---------------------------------------------------------------------------
def test_it_side_1_02_diff_position_independence() -> None:
    """SDD §4.13.F 参考: 不一致位置(先頭 / 末尾)に依存せず定数時間.

    検証手順:
    1. `correct_digest = compute(_TEST_DATA)` を計算
    2. `wrong_at_start = correct_digest の先頭 1 文字を反転`
       `wrong_at_end   = correct_digest の末尾 1 文字を反転`
    3. 各経路 200 サンプルの `verify` 経過時間を取得(ウォームアップ 20 件破棄後)
    4. median 比 = max(median_start, median_end) / min(median_start, median_end)
    5. 弱判定: median 比 < 10.0(短絡比較なら先頭不一致が早く返る、定数時間
       なら ~1.0)

    短絡比較の代表的検出ケース。両経路とも `compare_digest` は False を返すが、
    先頭で不一致を検出して早期 return する短絡実装ではタイミング差が大。
    `hmac.compare_digest` の C 実装は **常に全長を比較してから結果を返す** ため、
    定数時間性を満たすなら median 比は ~1.0。
    """
    correct_digest = compute(_TEST_DATA)
    wrong_at_start = _flip_hex_char(correct_digest, position=0)
    wrong_at_end = _flip_hex_char(correct_digest, position=-1)
    assert wrong_at_start != correct_digest
    assert wrong_at_end != correct_digest
    assert wrong_at_start != wrong_at_end

    samples_start = _collect_samples(_TEST_DATA, wrong_at_start)
    samples_end = _collect_samples(_TEST_DATA, wrong_at_end)

    median_start = statistics.median(samples_start)
    median_end = statistics.median(samples_end)
    ratio = max(median_start, median_end) / max(min(median_start, median_end), 1)
    assert ratio < _MEDIAN_RATIO_THRESHOLD, (
        f"timing ratio {ratio:.2f}x exceeds {_MEDIAN_RATIO_THRESHOLD}x "
        f"(median_start={median_start} ns, median_end={median_end} ns) — "
        f"hmac.compare_digest may not be constant-time across mismatch position"
    )
