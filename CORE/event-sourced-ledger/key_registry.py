"""Authenticated public-key registry boundary for signed checkpoints."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


class KeyRegistryError(ValueError):
    """Raised when a key registry entry is invalid or unavailable."""


@dataclass(frozen=True)
class KeyRecord:
    key_id: str
    public_key: bytes
    status: str = "active"

    def __post_init__(self) -> None:
        if not self.key_id:
            raise KeyRegistryError("key_id is required")
        if self.status not in {"active", "revoked"}:
            raise KeyRegistryError("unsupported key status")
        if not isinstance(self.public_key, bytes) or len(self.public_key) != 32:
            raise KeyRegistryError("Ed25519 public key must be 32 bytes")


class InMemoryKeyRegistry:
    """Reference resolver backed by an explicitly supplied authenticated mapping.

    This class is intentionally not a persistence or trust-root implementation.
    """

    def __init__(self, records: Mapping[str, KeyRecord]) -> None:
        self._records = dict(records)

    def resolve(self, key_id: str) -> bytes | None:
        record = self._records.get(key_id)
        if record is None or record.status != "active":
            return None
        return record.public_key

    def revoke(self, key_id: str) -> None:
        record = self._records.get(key_id)
        if record is None:
            raise KeyRegistryError(f"unknown key_id {key_id!r}")
        self._records[key_id] = KeyRecord(
            key_id=record.key_id,
            public_key=record.public_key,
            status="revoked",
        )
