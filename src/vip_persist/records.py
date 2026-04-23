"""Persistence data models (UNIT-003/004 shared types).

Defines the immutable records that flow across the persistence boundary:

* `Settings` — operator-configured dosage parameters (SRS-I-001 range).
* `RuntimeState` — control-loop state snapshot (SRS-O-001 range).
* `RawPersistedRecord` — deserialised record prior to integrity validation.
  Produced by UNIT-003.1 Serializer's `from_json` (SDD §4.12).
* `TrustedRecord` — integrity-validated record produced exclusively by
  `vip_integrity.validator.validate` on success (SDD §4.5.C). Accepting a
  `TrustedRecord` argument is a type-level guarantee that every §4.5.B
  check passed.

Step 19 B6 brings these types forward from UNIT-003.1 because UNIT-004.1
depends on them for its `validate(record)` signature, and defining them
once here avoids the duplication that a later Serializer implementation
would have to resolve.

Related SRS: SRS-DATA-001 (record shape), SRS-DATA-004 (schema versioning).
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal  # noqa: TC003  (pydantic v2 resolves field types at runtime)
from typing import Final, Self

from pydantic import BaseModel, ConfigDict

from vip_ctrl.state_machine import State  # noqa: TC001  (pydantic v2 runtime type)

__all__ = [
    "CURRENT_SCHEMA_VERSION",
    "SUPPORTED_SCHEMA_VERSIONS",
    "RawPersistedRecord",
    "RuntimeState",
    "Settings",
    "TrustedRecord",
]


CURRENT_SCHEMA_VERSION: Final[int] = 1
SUPPORTED_SCHEMA_VERSIONS: Final[frozenset[int]] = frozenset({CURRENT_SCHEMA_VERSION})


class Settings(BaseModel):
    """Operator-configured dosage parameters (SRS-I-001).

    Range enforcement is the Integrity Validator's responsibility (SDD §4.5.B)
    rather than pydantic's — we want out-of-range values to be reported as
    `FailsafeRecommended` reasons rather than as `ValidationError` at
    deserialisation time, so the fail-safe boot path (SRS-027) can enumerate
    every detected anomaly.
    """

    model_config = ConfigDict(frozen=True, strict=True)

    flow_rate: Decimal
    dose_volume: Decimal
    duration_min: int


class RuntimeState(BaseModel):
    """Control-loop runtime state snapshot persisted to storage."""

    model_config = ConfigDict(frozen=True)

    state: State
    current_flow: Decimal
    accumulated_volume: Decimal


class RawPersistedRecord(BaseModel):
    """Deserialised persisted record prior to integrity validation."""

    model_config = ConfigDict(frozen=True)

    schema_version: int
    settings: Settings
    runtime_state: RuntimeState
    payload_bytes: bytes
    checksum: str
    saved_at: str


@dataclass(frozen=True, slots=True)
class TrustedRecord:
    """Integrity-validated persisted record (SDD §4.5.C)."""

    schema_version: int
    settings: Settings
    runtime_state: RuntimeState
    checksum: str
    saved_at: str

    @classmethod
    def from_raw(cls, raw: RawPersistedRecord) -> Self:
        """Build a TrustedRecord from a RawPersistedRecord that passed validation."""
        return cls(
            schema_version=raw.schema_version,
            settings=raw.settings,
            runtime_state=raw.runtime_state,
            checksum=raw.checksum,
            saved_at=raw.saved_at,
        )
