"""Virtual-HW event injection stub (UNIT-002.3) per SDD-VIP-001 v0.2 §4.11.

Inc.1 stub-only realisation of SRS-032 (and the SRS-I-040 placeholder for
Inc.2). The stub exposes the two-method API agreed by SDD §4.11.A —
`inject` and `recent_events` — and records every injected
`VirtualHwEvent` into a 1000-entry ring buffer guarded by a
`threading.Lock`. Inc.1 deliberately does **not** propagate events to the
pump (`PumpSimulator`); SDD §4.11.C lists the Inc.2 hooks (occlusion
pressure, air-bubble flag, reservoir cut-off) that will replace the
no-op body in a later inclremental step.

Step 19 B14 design judgments (recorded in DEVELOPMENT_STEPS.md):

* `VirtualHwEventKind` is the renamed-from-`EventKind` enum: keeping
  control-plane events (`vip_ctrl.state_machine.EventKind`) and
  virtual-HW events in separate type namespaces avoids a name collision
  that would force callers to use aliased imports.
* `VirtualHwEvent` is `frozen=True, slots=True` (B11 / B12 / B13
  pattern). The frozen contract is exercised by UT-002.3-08.
* `_buffer = collections.deque(maxlen=BUFFER_MAXLEN)` provides
  fixed-cost ring-buffer semantics: oldest entries are dropped without
  user-visible signalling, matching SDD §4.11.E ("performance優先").
* `_lock = threading.Lock()` (non-reentrant) is sufficient because no
  internal helper re-enters the locked region. UT-002.3-07 covers the
  concurrency contract.
* `recent_events` returns `list(self._buffer)[-limit:]` so the caller
  receives a *copy* and cannot alias the internal deque (UT-002.3-10).

Related SRS: SRS-032, SRS-I-040 (Inc.2 placeholder).
Related RCM: — (Inc.2 will couple this to RCM-005 / 006 / 007 once the
real propagation paths land).
Related HZ:  HZ-004 (future linkage via Inc.2 hooks).
"""

from __future__ import annotations

import threading
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from collections.abc import Mapping

__all__ = [
    "BUFFER_MAXLEN",
    "DEFAULT_RECENT_LIMIT",
    "EventInjectionStub",
    "VirtualHwEvent",
    "VirtualHwEventKind",
]


BUFFER_MAXLEN: Final[int] = 1000
"""Ring-buffer capacity per SDD §4.11.B (oldest entries auto-evicted)."""

DEFAULT_RECENT_LIMIT: Final[int] = 100
"""Default `recent_events` limit per SDD §4.11.A."""


class VirtualHwEventKind(Enum):
    """Inc.1 catalogue of virtual-HW event kinds (SDD §4.11.B)."""

    OCCLUSION = "occlusion"
    AIR_BUBBLE = "air_bubble"
    RESERVOIR_EMPTY = "reservoir_empty"


def _empty_metadata() -> Mapping[str, object]:
    """Return an empty metadata mapping (typed factory for mypy --strict)."""
    return {}


@dataclass(frozen=True, slots=True)
class VirtualHwEvent:
    """Immutable virtual-HW event record (SDD §4.11.B).

    Fields mirror SDD §4.11.B exactly. The `metadata` mapping is opaque
    to this stub (callers may use it for Inc.2 propagation parameters).
    """

    kind: VirtualHwEventKind
    severity: int
    occurred_at: float
    metadata: Mapping[str, object] = field(default_factory=_empty_metadata)


class EventInjectionStub:
    """Inc.1 no-op event injection stub (UNIT-002.3).

    Records injected events into a thread-safe ring buffer; pump state is
    untouched in Inc.1. `recent_events` returns a copy so callers cannot
    alias the internal buffer.
    """

    def __init__(self) -> None:
        """Initialise an empty 1000-entry ring buffer with a fresh lock."""
        self._buffer: deque[VirtualHwEvent] = deque(maxlen=BUFFER_MAXLEN)
        self._lock = threading.Lock()

    def inject(self, event: VirtualHwEvent) -> None:
        """Record `event` in the ring buffer (SDD §4.11.C, no propagation)."""
        with self._lock:
            self._buffer.append(event)
        # Inc.2 will hook pump propagation here, e.g.:
        #   if event.kind is VirtualHwEventKind.OCCLUSION:
        #       self._pump.set_occlusion_pressure(event.severity)

    def recent_events(self, limit: int = DEFAULT_RECENT_LIMIT) -> list[VirtualHwEvent]:
        """Return up to `limit` most-recent events (newest last, copy)."""
        with self._lock:
            return list(self._buffer)[-limit:]
