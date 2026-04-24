"""Serializer (UNIT-003.1) per SDD-VIP-001 v0.2 §4.12.

JSON serialisation and deserialisation for `PersistedRecord` /
`RawPersistedRecord`. The module holds three serialisation rules that
together provide a stable, deterministic, round-trip-safe format:

1. Decimals are tagged as `{"__decimal__": "<string>"}` so string and
   Decimal values are never conflated on restore (SDD §4.12 design note).
2. `State` enum values are tagged as `{"__state__": "<name>"}` -- never
   by `auto()` numeric -- so future enum insertions do not break existing
   persisted records (Step 19 B7 cross-review point 3).
3. Raw `bytes` (the `payload_bytes` field) are tagged as
   `{"__bytes__": "<base64>"}` so `json.dumps` can round-trip them
   losslessly (Step 19 B7 implementation extension of §4.12.C, MINOR).

`json.dumps` runs with `sort_keys=True`, `separators=(",", ":")` and
`ensure_ascii=False` so the SHA-256 digest of the payload bytes is
stable for any identical record (SDD §4.12.F determinism).

RCM-015 prerequisite: restored records carry typed fields and a valid
inner-checksum that Integrity Validator (UNIT-004.1) then re-checks.

Related SRS: SRS-DATA-001 (JSON + checksum), SRS-DATA-004 (schema version).
Related RCM: RCM-015 prerequisite.
Related HZ:  HZ-007 (persisted-data corruption).
"""

from __future__ import annotations

import base64
import hashlib
import json
from typing import Any, Final

from vip_ctrl.state_machine import State
from vip_persist.records import (
    CURRENT_SCHEMA_VERSION,
    PersistedRecord,
    RawPersistedRecord,
    RuntimeState,
    Settings,
)

__all__ = [
    "build_persisted_record",
    "compute_payload_checksum",
    "current_schema_version",
    "from_json",
    "to_json",
]


_DECIMAL_TAG: Final[str] = "__decimal__"
_STATE_TAG: Final[str] = "__state__"
_BYTES_TAG: Final[str] = "__bytes__"


def current_schema_version() -> int:
    """Return the current schema version per SDD §4.12.A."""
    return CURRENT_SCHEMA_VERSION


def _default(obj: object) -> dict[str, str]:
    """json.dumps hook -- tag-wrap Decimal / State / bytes values."""
    # Local import kept out to avoid circulars; Decimal is always hashable.
    from decimal import Decimal  # noqa: PLC0415

    if isinstance(obj, Decimal):
        return {_DECIMAL_TAG: str(obj)}
    if isinstance(obj, State):
        return {_STATE_TAG: obj.name}
    if isinstance(obj, bytes):
        return {_BYTES_TAG: base64.b64encode(obj).decode("ascii")}
    msg = f"Unsupported type: {type(obj).__name__}"
    raise TypeError(msg)


def _hook(obj: dict[str, Any]) -> Any:
    """json.loads object_hook -- invert the tag wrap performed by `_default`."""
    from decimal import Decimal  # noqa: PLC0415

    if _DECIMAL_TAG in obj:
        return Decimal(obj[_DECIMAL_TAG])
    if _STATE_TAG in obj:
        return State[obj[_STATE_TAG]]
    if _BYTES_TAG in obj:
        return base64.b64decode(obj[_BYTES_TAG])
    return obj


def _serialise(payload: dict[str, Any]) -> bytes:
    """Shared `json.dumps` configuration enforcing determinism (SDD §4.12.C)."""
    return json.dumps(
        payload,
        default=_default,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")


def compute_payload_checksum(
    schema_version: int,
    settings: Settings,
    runtime_state: RuntimeState,
    saved_at: str,
) -> tuple[bytes, str]:
    """Compute (payload_bytes, checksum) from the inner record body.

    `payload_bytes` is the JSON serialisation of every field except
    `payload_bytes` and `checksum` themselves (SDD §4.12.B definition:
    "payload_bytes: bytes (自身を除く JSON)"). The checksum is the
    SHA-256 hex digest of that serialisation.
    """
    inner: dict[str, Any] = {
        "schema_version": schema_version,
        "settings": settings.model_dump(mode="python"),
        "runtime_state": runtime_state.model_dump(mode="python"),
        "saved_at": saved_at,
    }
    payload_bytes = _serialise(inner)
    checksum = hashlib.sha256(payload_bytes).hexdigest()
    return payload_bytes, checksum


def build_persisted_record(
    settings: Settings,
    runtime_state: RuntimeState,
    saved_at: str,
    schema_version: int = CURRENT_SCHEMA_VERSION,
) -> PersistedRecord:
    """Assemble a PersistedRecord with computed payload_bytes and checksum."""
    payload_bytes, checksum = compute_payload_checksum(
        schema_version,
        settings,
        runtime_state,
        saved_at,
    )
    return PersistedRecord(
        schema_version=schema_version,
        settings=settings,
        runtime_state=runtime_state,
        payload_bytes=payload_bytes,
        checksum=checksum,
        saved_at=saved_at,
    )


def to_json(record: PersistedRecord) -> bytes:
    """Serialise a PersistedRecord to deterministic UTF-8 JSON bytes.

    Pure function. No exceptions under normal use: pydantic already
    enforced field types, and the `_default` hook covers every custom
    type the model can contain.
    """
    return _serialise(record.model_dump(mode="python"))


def from_json(data: bytes) -> RawPersistedRecord:
    """Decode UTF-8 JSON bytes into a RawPersistedRecord.

    Raises:
        UnicodeDecodeError: input bytes are not valid UTF-8.
        json.JSONDecodeError: input is not parseable JSON.
        pydantic.ValidationError: JSON shape does not match the model.

    """
    raw = json.loads(data.decode("utf-8"), object_hook=_hook)
    return RawPersistedRecord.model_validate(raw)
