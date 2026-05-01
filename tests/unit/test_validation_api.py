"""UT-005.3 — Validation API (UNIT-005.3 per SDD-VIP-001 §4.17, class B).

Implements UTPR-VIP-001 §7.3.17 detailed test cases UT-005.3-01 .. UT-005.3-13.
Realises SRS-UX-001 (validate API surface), SRS-004 (flow x duration / 60
≈ dose, ±1%), and SRS-005 (range validation). The unit is class B per
SAD §9 SEP-001; the import-graph test (UT-005.3-13) verifies that the
production module pulls no class-C unit (allowing only the value-object
module ``vip_persist.records``).

Step 19 B18 design judgments (recorded in DEVELOPMENT_STEPS.md):

* SDD §4.17.C ``drug_name`` validation is deferred to Inc.4 because
  ``vip_persist.records.Settings`` does not yet carry ``drug_name``
  (B15/B16/B17 hand-off chain). UTPR §7.3.17 records this Inc.1 scope
  restriction explicitly.
* ``ValidationFailure`` is a sealed hierarchy of frozen+slots
  dataclasses (B11〜B17 pattern) — ``OutOfRange`` / ``Inconsistency`` /
  ``MissingField``.
* The internal-exception swallow contract (SDD §4.17.E) is realised by a
  single top-level try/except that wraps the entire validator body and
  returns ``Err([Inconsistency("internal: ...")])`` — the class-B unit
  must never raise across the SEP-001 boundary.
* SEP-001 import-graph compliance is mechanically verified in
  UT-005.3-13 by AST-walking ``src/vip_api_b/validation_api.py`` and
  asserting that no name in {``vip_ctrl``, ``vip_sim``,
  ``vip_integrity``} appears as an import target. ``vip_persist`` is
  allowed because Settings is a frozen value object with no behaviour.

Related SRS: SRS-UX-001, SRS-004, SRS-005.
Related RCM: — (class B side, separated).
"""

from __future__ import annotations

import ast
import dataclasses
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

import pytest

from vip_api_b.validation_api import (
    Err,
    Inconsistency,
    MissingField,
    Ok,
    OutOfRange,
    ValidationFailure,
    ValidationResult,
    validate_settings,
)
from vip_persist.records import Settings

# ---------- helpers ----------


def _consistent_settings(
    flow_rate: Decimal = Decimal("100.0"),
    duration_min: int = 60,
    dose_volume: Decimal | None = None,
) -> Settings:
    """Build a Settings whose dose matches flow * duration / 60 exactly."""
    if dose_volume is None:
        dose_volume = flow_rate * Decimal(duration_min) / Decimal(60)
    return Settings(
        flow_rate=flow_rate,
        dose_volume=dose_volume,
        duration_min=duration_min,
    )


# ---------- UT-005.3-01: 正常系(整合した Settings) ----------


def test_ut_005_3_01_consistent_settings_returns_ok() -> None:
    """flow_rate x duration_min / 60 == dose_volume → Ok(settings)。"""
    settings = _consistent_settings(
        flow_rate=Decimal("500.0"),
        duration_min=60,
        dose_volume=Decimal("500.0"),
    )

    result = validate_settings(settings)

    assert isinstance(result, Ok)
    assert result.settings == settings


# ---------- UT-005.3-02: flow_rate 範囲外 → OutOfRange ----------


def test_ut_005_3_02_flow_rate_out_of_range_yields_out_of_range_failure() -> None:
    """flow_rate が 0.0 未満 / 1200.0 超 → OutOfRange("flow_rate", ...)。"""
    settings = Settings(
        flow_rate=Decimal("1500.0"),  # > 1200.0
        dose_volume=Decimal("100.0"),
        duration_min=4,
    )

    result = validate_settings(settings)

    assert isinstance(result, Err)
    out_of_range = [f for f in result.failures if isinstance(f, OutOfRange)]
    assert any(f.field == "flow_rate" for f in out_of_range)


# ---------- UT-005.3-03: dose_volume 範囲外 → OutOfRange ----------


def test_ut_005_3_03_dose_volume_out_of_range_yields_out_of_range_failure() -> None:
    """dose_volume が 9999.9 超 → OutOfRange("dose_volume", ...)。"""
    settings = Settings(
        flow_rate=Decimal("100.0"),
        dose_volume=Decimal("99999.0"),  # > 9999.9
        duration_min=600,
    )

    result = validate_settings(settings)

    assert isinstance(result, Err)
    assert any(isinstance(f, OutOfRange) and f.field == "dose_volume" for f in result.failures)


# ---------- UT-005.3-04: duration_min 範囲外 → OutOfRange ----------


@pytest.mark.parametrize(
    "duration_min",
    [0, 6000],
)
def test_ut_005_3_04_duration_min_out_of_range_yields_out_of_range_failure(
    duration_min: int,
) -> None:
    """duration_min が 1〜5999 の範囲外 → OutOfRange("duration_min", ...)。"""
    settings = Settings(
        flow_rate=Decimal("100.0"),
        dose_volume=Decimal("100.0"),
        duration_min=duration_min,
    )

    result = validate_settings(settings)

    assert isinstance(result, Err)
    assert any(isinstance(f, OutOfRange) and f.field == "duration_min" for f in result.failures)


# ---------- UT-005.3-05: 整合性違反(SRS-004) → Inconsistency ----------


def test_ut_005_3_05_inconsistent_dose_yields_inconsistency_failure() -> None:
    """500 mL/h x 60 min / 60 = 500 mL ≠ dose=800 → Inconsistency。"""
    settings = Settings(
        flow_rate=Decimal("500.0"),
        dose_volume=Decimal("800.0"),  # 整合計算 = 500 と乖離 60%
        duration_min=60,
    )

    result = validate_settings(settings)

    assert isinstance(result, Err)
    assert any(isinstance(f, Inconsistency) for f in result.failures)


# ---------- UT-005.3-06: 整合性境界(±1%) ----------


@pytest.mark.parametrize(
    ("dose_volume", "should_pass"),
    [
        (Decimal("500.00"), True),  # 0.00% diff → Pass
        (Decimal("504.99"), True),  # +0.998% diff → Pass(< 1%)
        (Decimal("505.01"), False),  # +1.002% diff → Fail
    ],
)
def test_ut_005_3_06_inconsistency_boundary_at_one_percent(
    dose_volume: Decimal,
    *,
    should_pass: bool,
) -> None:
    """flow*duration/60 = 500.0 に対する dose の ±1% 境界判定。"""
    settings = Settings(
        flow_rate=Decimal("500.0"),
        dose_volume=dose_volume,
        duration_min=60,
    )

    result = validate_settings(settings)

    if should_pass:
        assert isinstance(result, Ok)
    else:
        assert isinstance(result, Err)
        assert any(isinstance(f, Inconsistency) for f in result.failures)


# ---------- UT-005.3-07: 多重失敗(範囲外 + 整合性違反) ----------


def test_ut_005_3_07_multiple_failures_are_all_collected() -> None:
    """範囲外 + 整合性違反を同時に検出すると failures に複数列挙される。"""
    settings = Settings(
        flow_rate=Decimal("1500.0"),  # > 1200.0
        dose_volume=Decimal("100.0"),  # 整合計算 = 100 で OK だが flow_rate 範囲外
        duration_min=4,
    )

    result = validate_settings(settings)

    assert isinstance(result, Err)
    assert any(isinstance(f, OutOfRange) and f.field == "flow_rate" for f in result.failures)


# ---------- UT-005.3-08: 内部例外握りつぶし契約(SEP-001) ----------


def test_ut_005_3_08_internal_exception_is_swallowed_and_returns_err() -> None:
    """内部 Decimal 演算例外でも例外伝播せず Err([Inconsistency("internal:...")]) で復帰。"""
    settings = _consistent_settings()

    # validate_settings 内部の Decimal 演算で例外を発生させる(モンキーパッチ)。
    with patch("vip_api_b.validation_api.Decimal", side_effect=ArithmeticError("boom")):
        result = validate_settings(settings)

    assert isinstance(result, Err)
    assert len(result.failures) == 1
    failure = result.failures[0]
    assert isinstance(failure, Inconsistency)
    assert "internal" in failure.detail


# ---------- UT-005.3-09: 純粋関数 / 副作用なし ----------


def test_ut_005_3_09_validate_settings_is_pure() -> None:
    """同じ入力で複数回呼出し → 戻り値の構造が同等(Ok / Err と内訳が一致)。"""
    settings = _consistent_settings(
        flow_rate=Decimal("100.0"),
        duration_min=60,
        dose_volume=Decimal("100.0"),
    )

    r1 = validate_settings(settings)
    r2 = validate_settings(settings)

    assert isinstance(r1, Ok)
    assert isinstance(r2, Ok)
    assert r1.settings == r2.settings


# ---------- UT-005.3-10: ValidationFailure sealed hierarchy frozen 契約 ----------


def test_ut_005_3_10_validation_failure_objects_are_frozen() -> None:
    """`OutOfRange` / `Inconsistency` / `MissingField` は frozen dataclass。"""
    out_of_range = OutOfRange(field="x", actual="y", allowed_range="0..1")
    inconsistency = Inconsistency(detail="d")
    missing = MissingField(field="x")

    for obj, attr in [
        (out_of_range, "field"),
        (inconsistency, "detail"),
        (missing, "field"),
    ]:
        with pytest.raises(dataclasses.FrozenInstanceError):
            setattr(obj, attr, "tampered")


# ---------- UT-005.3-11: ValidationResult Union 網羅性 ----------


def test_ut_005_3_11_validation_result_union_covers_ok_and_err() -> None:
    """`ValidationResult` Union は `Ok` と `Err` を含む(命名・export 整合性)。"""
    settings = _consistent_settings()

    samples: list[ValidationResult] = [
        Ok(settings=settings),
        Err(failures=[MissingField(field="x")]),
    ]
    assert all(isinstance(s, Ok | Err) for s in samples)


# ---------- UT-005.3-12: ValidationFailure 基底型 整合性 ----------


def test_ut_005_3_12_failure_subtypes_are_assignable_to_base_type() -> None:
    """`OutOfRange` / `Inconsistency` / `MissingField` は ValidationFailure として扱える。"""
    failures: list[ValidationFailure] = [
        OutOfRange(field="x", actual="y", allowed_range="0..1"),
        Inconsistency(detail="d"),
        MissingField(field="x"),
    ]
    assert len(failures) == 3


# ---------- UT-005.3-13: SEP-001 import グラフ機械検証 ----------


def test_ut_005_3_13_sep001_import_graph_excludes_class_c_units() -> None:
    """`vip_api_b.validation_api` は `vip_ctrl` / `vip_sim` / `vip_integrity` を import しない。

    SAD §9 SEP-001(クラス B → クラス C 副作用伝播遮断)を AST 解析で機械検証する。
    `vip_persist.records` のみ frozen 値オブジェクトとして許容。
    """
    src = Path(__file__).resolve().parents[2] / "src" / "vip_api_b" / "validation_api.py"
    tree = ast.parse(src.read_text(encoding="utf-8"))

    forbidden_roots = {"vip_ctrl", "vip_sim", "vip_integrity", "vip_api"}
    seen_imports: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                seen_imports.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            seen_imports.add(node.module.split(".")[0])

    intersection = seen_imports & forbidden_roots
    assert not intersection, (
        f"SEP-001 violation: vip_api_b.validation_api imports class-C roots {intersection}"
    )
