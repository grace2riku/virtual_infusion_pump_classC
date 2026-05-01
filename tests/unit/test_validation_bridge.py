"""UT-005.1-bridge — Class-B Validation API Adapter (CR-0004 (b)).

Verifies `src/vip_api/_validation_bridge.py` —
`ClassBValidationApiAdapter` wraps `vip_api_b.validate_settings`'s
`Ok` / `Err` hierarchy into the `list[ValidationError]` shape required
by `vip_api.control_api.ValidationApi` Protocol.

Test cases:

* UT-005.1-bridge-01:整合 Settings → 空 list(`Ok` パススルー).
* UT-005.1-bridge-02:範囲外単独 → `OutOfRange` を 1 件の ValidationError に変換.
* UT-005.1-bridge-03:多重失敗(範囲外 + 整合性違反)→ 2 件以上の ValidationError 集約.
* UT-005.1-bridge-04:整合性違反単独 → `Inconsistency` を `settings_consistency` field に変換.
* UT-005.1-bridge-05:`make_validation_api()` factory が ValidationApi Protocol を満たす.
* UT-005.1-bridge-06:Adapter は `ControlApi.start` 経路で実体注入できる(契約整合化の本質).
"""

from __future__ import annotations

from decimal import Decimal

from vip_api._validation_bridge import (
    ClassBValidationApiAdapter,
    make_validation_api,
)
from vip_persist.records import Settings


def _consistent_settings() -> Settings:
    """flow=60.0, dose=60.0, duration=60 → flow * duration / 60 == dose(SRS-004)."""
    return Settings(
        flow_rate=Decimal("60.0"),
        dose_volume=Decimal("60.0"),
        duration_min=60,
    )


# ---------- UT-005.1-bridge-01: 整合 Settings → 空 list ----------


def test_ut_bridge_01_consistent_settings_returns_empty_list() -> None:
    adapter = ClassBValidationApiAdapter()

    errors = adapter.validate_settings(_consistent_settings())

    assert errors == []


# ---------- UT-005.1-bridge-02: 範囲外単独 → ValidationError 1 件 ----------


def test_ut_bridge_02_out_of_range_yields_single_error() -> None:
    """flow_rate > 1200 で OutOfRange → ValidationError(field=flow_rate)."""
    adapter = ClassBValidationApiAdapter()
    settings = Settings(
        flow_rate=Decimal("1500.0"),
        dose_volume=Decimal("1500.0"),
        duration_min=60,
    )

    errors = adapter.validate_settings(settings)

    assert len(errors) == 1
    err = errors[0]
    assert err.field == "flow_rate"
    assert "out_of_range" in err.message
    assert "1500" in err.message
    assert "0.0..1200.0" in err.message


# ---------- UT-005.1-bridge-03: 多重失敗 → 集約変換 ----------


def test_ut_bridge_03_multiple_failures_aggregated() -> None:
    """flow_rate>max かつ dose_volume>max → 2 件の ValidationError 集約.

    Settings は flow=2000, dose=20000, duration=60 で 2 つの範囲外を同時発生。
    整合性チェックは flow*duration/60 == 2000 vs dose=20000 で 1% を大きく超えるため
    Inconsistency も追加され、合計 3 件。
    """
    adapter = ClassBValidationApiAdapter()
    settings = Settings(
        flow_rate=Decimal("2000.0"),
        dose_volume=Decimal("20000.0"),
        duration_min=60,
    )

    errors = adapter.validate_settings(settings)

    assert len(errors) >= 2
    fields = {e.field for e in errors}
    assert "flow_rate" in fields
    assert "dose_volume" in fields


# ---------- UT-005.1-bridge-04: 整合性違反 → settings_consistency field ----------


def test_ut_bridge_04_inconsistency_maps_to_consistency_field() -> None:
    """flow=60, duration=60, dose=70 → SRS-004 整合性違反(diff > 1%).

    `Inconsistency(detail=...)` は field=`settings_consistency`、message=`inconsistency: <detail>`
    に変換される。
    """
    adapter = ClassBValidationApiAdapter()
    settings = Settings(
        flow_rate=Decimal("60.0"),
        dose_volume=Decimal("70.0"),
        duration_min=60,
    )

    errors = adapter.validate_settings(settings)

    assert len(errors) == 1
    err = errors[0]
    assert err.field == "settings_consistency"
    assert err.message.startswith("inconsistency:")


# ---------- UT-005.1-bridge-05: factory + Protocol 適合 ----------


def test_ut_bridge_05_factory_returns_validation_api_compatible() -> None:
    """`make_validation_api()` が `ValidationApi` Protocol を構造的に満たす.

    戻り値の型注釈が `ValidationApi` であること(静的型)+ Protocol が要求する
    `validate_settings(settings) -> list[ValidationError]` がランタイムで動作することを
    両面で確認。
    """
    api = make_validation_api()

    errors = api.validate_settings(_consistent_settings())
    assert errors == []


# ---------- UT-005.1-bridge-06: ControlApi.start 経路で実体注入できる ----------


def test_ut_bridge_06_adapter_injectable_into_control_api() -> None:
    """`ControlApi(validation_api=ClassBValidationApiAdapter())` が型整合し、
    `start(consistent_settings)` が ValidationFailed にならない(空 list 経路).

    本ケースは CR-0004 の本質を最小再現する:Adapter 経由で `vip_api_b` の
    `Ok` を ControlApi の「空 list = pass」契約に橋渡しする。
    """
    from unittest.mock import Mock  # noqa: PLC0415

    from vip_api.control_api import (  # noqa: PLC0415
        ApiResult,
        ControlApi,
        Ok,
    )
    from vip_ctrl.command_handler import (  # noqa: PLC0415
        Accepted,
        CommandHandler,
    )
    from vip_integrity.resume_gate import ResumeConfirmationGate  # noqa: PLC0415

    handler: Mock = Mock(spec=CommandHandler)
    handler.enqueue.return_value = Accepted(token="bridge-token")
    gate: Mock = Mock(spec=ResumeConfirmationGate)

    api = ControlApi(
        command_handler=handler,
        resume_gate=gate,
        validation_api=ClassBValidationApiAdapter(),
    )

    result: ApiResult = api.start(_consistent_settings())

    assert isinstance(result, Ok)
    handler.enqueue.assert_called_once()
