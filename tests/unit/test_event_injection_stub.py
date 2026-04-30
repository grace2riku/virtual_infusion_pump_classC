"""UT-002.3 — Event Injection Stub (UNIT-002.3 per SDD-VIP-001 §4.11).

Implements UTPR-VIP-001 §7.3.13 detailed test cases UT-002.3-01 .. UT-002.3-11.
Inc.1 stub-only realisation of SRS-032 (and the SRS-I-040 placeholder for
Inc.2). The stub records injected `VirtualHwEvent` values into a 1000-entry
ring buffer and **does not propagate them to the pump** in Inc.1 (no-op).

Step 19 B14 design judgments (recorded in DEVELOPMENT_STEPS.md):

* `VirtualHwEventKind` is renamed from SDD's bare `EventKind` to avoid the
  name collision with `vip_ctrl.state_machine.EventKind` (control-plane
  events such as CMD_START / WDT_TIMEOUT). The two namespaces stay
  segregated so an aliased import is never required.
* `VirtualHwEvent` is `frozen=True, slots=True` (B11 / B12 / B13 pattern):
  `dataclasses.FrozenInstanceError` on attribute assignment becomes a
  contract test (UT-002.3-08).
* No-op behaviour (UT-002.3-06) is verified by running the stub alongside
  a `PumpSimulator` + `PumpObserver` and asserting observed state is
  unchanged across a sequence of `inject()` calls. SDD §4.11.F.2 wording.
* `recent_events()` returns a `list[VirtualHwEvent]` *copy* of the deque
  slice, so callers may not aliase the internal buffer (UT-002.3-10).

Related SRS: SRS-032, SRS-I-040 (Inc.2 placeholder).
Related HZ:  HZ-004 (future linkage in Inc.2).
"""

from __future__ import annotations

import dataclasses
import threading
import time
from collections import Counter
from decimal import Decimal

import pytest

from vip_sim.event_injection import (
    EventInjectionStub,
    VirtualHwEvent,
    VirtualHwEventKind,
)
from vip_sim.pump_observer import PumpObserver
from vip_sim.pump_simulator import PumpSimulator

# ---------- helpers ----------


@pytest.fixture
def stub() -> EventInjectionStub:
    return EventInjectionStub()


def _make_event(
    kind: VirtualHwEventKind = VirtualHwEventKind.OCCLUSION,
    severity: int = 1,
    metadata: dict[str, object] | None = None,
) -> VirtualHwEvent:
    return VirtualHwEvent(
        kind=kind,
        severity=severity,
        occurred_at=time.monotonic(),
        metadata=metadata if metadata is not None else {},
    )


# ---------- UT-002.3-01: 基本動作 ----------


def test_ut_002_3_01_inject_then_recent_events_returns_same_event(
    stub: EventInjectionStub,
) -> None:
    """`inject` で投入したイベントが `recent_events(1)` で取り出せる。"""
    event = _make_event(kind=VirtualHwEventKind.OCCLUSION, severity=3)
    stub.inject(event)

    recent = stub.recent_events(limit=1)

    assert recent == [event]


# ---------- UT-002.3-02: FIFO 順序の保持 ----------


def test_ut_002_3_02_recent_events_preserves_fifo_order(
    stub: EventInjectionStub,
) -> None:
    """複数 `inject` が時系列順(先入先出)で観測される。"""
    events = [
        _make_event(kind=VirtualHwEventKind.OCCLUSION, severity=1),
        _make_event(kind=VirtualHwEventKind.AIR_BUBBLE, severity=2),
        _make_event(kind=VirtualHwEventKind.RESERVOIR_EMPTY, severity=3),
    ]
    for ev in events:
        stub.inject(ev)

    recent = stub.recent_events(limit=10)

    assert recent == events


# ---------- UT-002.3-03: limit による末尾切り出し ----------


def test_ut_002_3_03_recent_events_returns_last_n_when_limit_smaller(
    stub: EventInjectionStub,
) -> None:
    """`limit < buffer 件数` のとき末尾 limit 件のみが返る。"""
    events = [_make_event(severity=i) for i in range(5)]
    for ev in events:
        stub.inject(ev)

    recent = stub.recent_events(limit=2)

    assert recent == events[-2:]


# ---------- UT-002.3-04: limit がバッファサイズより大きいとき全件返す ----------


def test_ut_002_3_04_recent_events_default_limit_returns_all_when_buffer_smaller(
    stub: EventInjectionStub,
) -> None:
    """`limit` が現在件数より大きいとき、全件返り、件数は変わらない。"""
    events = [_make_event(severity=i) for i in range(3)]
    for ev in events:
        stub.inject(ev)

    recent = stub.recent_events()  # default limit=100

    assert recent == events


# ---------- UT-002.3-05: リングバッファ満杯時の自動破棄(SDD §4.11.F.3) ----------


def test_ut_002_3_05_ring_buffer_drops_oldest_when_full(
    stub: EventInjectionStub,
) -> None:
    """1001 件 inject → 最古は破棄、新しい 1000 件のみ残る。"""
    events = [_make_event(severity=i) for i in range(1001)]
    for ev in events:
        stub.inject(ev)

    recent = stub.recent_events(limit=1000)

    assert len(recent) == 1000
    # 最古(severity=0)は破棄され、severity=1 以降が残る。
    assert recent[0].severity == 1
    assert recent[-1].severity == 1000


# ---------- UT-002.3-06: no-op 検証(SDD §4.11.F.2) ----------


def test_ut_002_3_06_inject_does_not_affect_pump_observation(
    stub: EventInjectionStub,
) -> None:
    """Inc.1 では `inject` が Pump.observe の値に影響しない(no-op スタブ)。"""
    pump = PumpSimulator()
    observer = PumpObserver(pump=pump)
    pump.set_flow_rate(Decimal(120))
    before = observer.observe()

    stub.inject(_make_event(kind=VirtualHwEventKind.OCCLUSION, severity=10))
    stub.inject(_make_event(kind=VirtualHwEventKind.AIR_BUBBLE, severity=20))
    stub.inject(_make_event(kind=VirtualHwEventKind.RESERVOIR_EMPTY, severity=30))

    after = observer.observe()
    assert after.current_flow == before.current_flow
    assert after.target_flow == before.target_flow
    assert after.accumulated_volume == before.accumulated_volume
    assert after.elapsed_min == before.elapsed_min
    assert after.failsafe_active == before.failsafe_active


# ---------- UT-002.3-07: 並行 inject 試験 ----------


def test_ut_002_3_07_concurrent_inject_records_all_events(
    stub: EventInjectionStub,
) -> None:
    """10 スレッド x 10 件の並行 inject で 100 件が損失なく記録される。"""
    threads_n = 10
    per_thread = 10
    kinds = [
        VirtualHwEventKind.OCCLUSION,
        VirtualHwEventKind.AIR_BUBBLE,
        VirtualHwEventKind.RESERVOIR_EMPTY,
    ]

    def _worker(thread_idx: int) -> None:
        for i in range(per_thread):
            stub.inject(_make_event(kind=kinds[(thread_idx + i) % 3], severity=i))

    threads = [threading.Thread(target=_worker, args=(t,)) for t in range(threads_n)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=5.0)
        assert not t.is_alive()

    recent = stub.recent_events(limit=threads_n * per_thread)
    assert len(recent) == threads_n * per_thread
    # 各 kind が `threads_n * per_thread / 3` 周辺で出現することを軽く確認。
    counter = Counter(ev.kind for ev in recent)
    assert sum(counter.values()) == threads_n * per_thread


# ---------- UT-002.3-08: VirtualHwEvent frozen 契約 ----------


def test_ut_002_3_08_virtual_hw_event_is_frozen() -> None:
    """`VirtualHwEvent` は frozen dataclass であり代入不可(B12 パターン)。"""
    event = _make_event()
    with pytest.raises(dataclasses.FrozenInstanceError):
        event.severity = 99  # type: ignore[misc]


# ---------- UT-002.3-09: VirtualHwEventKind 列挙の網羅 ----------


def test_ut_002_3_09_event_kind_enum_lists_three_inc1_kinds() -> None:
    """SDD §4.11.B が定める 3 種の kind がすべて列挙されている。"""
    members = {member.name for member in VirtualHwEventKind}
    assert members == {"OCCLUSION", "AIR_BUBBLE", "RESERVOIR_EMPTY"}


# ---------- UT-002.3-10: recent_events 返却 list の独立性 ----------


def test_ut_002_3_10_returned_list_does_not_alias_internal_buffer(
    stub: EventInjectionStub,
) -> None:
    """`recent_events` の返り値を mutate しても内部バッファに反映されない。"""
    stub.inject(_make_event(severity=1))
    snapshot = stub.recent_events(limit=10)
    snapshot.append(_make_event(severity=999))

    assert len(stub.recent_events(limit=10)) == 1


# ---------- UT-002.3-11: severity / metadata の透過 ----------


def test_ut_002_3_11_severity_and_metadata_are_passed_through_unchanged(
    stub: EventInjectionStub,
) -> None:
    """任意の severity / metadata が変形されずに観測される。"""
    metadata: dict[str, object] = {"location": "tube_3", "code": 42}
    event = _make_event(
        kind=VirtualHwEventKind.OCCLUSION,
        severity=7,
        metadata=metadata,
    )
    stub.inject(event)

    [observed] = stub.recent_events(limit=1)
    assert observed.severity == 7
    assert observed.metadata == metadata
    assert observed.kind is VirtualHwEventKind.OCCLUSION


# ---------- UT-002.3-12: metadata 省略時のデフォルト ----------


def test_ut_002_3_12_metadata_defaults_to_empty_mapping_when_omitted() -> None:
    """`metadata` 未指定で生成した `VirtualHwEvent` は空 Mapping を持つ。"""
    event = VirtualHwEvent(
        kind=VirtualHwEventKind.AIR_BUBBLE,
        severity=1,
        occurred_at=time.monotonic(),
    )
    assert dict(event.metadata) == {}
