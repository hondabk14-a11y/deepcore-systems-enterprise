#!/usr/bin/env python3
"""Deterministic validator key registry for DeepCore.

The registry binds a validator identity to an Ed25519 public key and an
explicit lifecycle state. It intentionally stores public material only.
Private-key custody remains outside the ledger runtime.
"""

from __future__ import annotations

from dataclasses import dataclass

from CORE.deepcore_crypto import key_id


@dataclass(frozen=True)
class ValidatorKey:
    validator: str
    key_id: str
    public_key: bytes
    active: bool = True


class ValidatorKeyRegistry:
    """In-memory reference registry with explicit rotation and revocation."""

    def __init__(self) -> None:
        self._keys: dict[str, ValidatorKey] = {}

    def register(self, validator: str, public_key: bytes) -> ValidatorKey:
        if not validator:
            raise ValueError("validator must be non-empty")
        computed = key_id(public_key)
        existing = self._keys.get(validator)
        if existing is not None and existing.active:
            raise ValueError("active validator key already exists")
        record = ValidatorKey(validator, computed, bytes(public_key), True)
        self._keys[validator] = record
        return record

    def rotate(self, validator: str, public_key: bytes) -> ValidatorKey:
        existing = self._keys.get(validator)
        if existing is None:
            raise ValueError("validator key does not exist")
        return self.register(validator, public_key)

    def revoke(self, validator: str) -> ValidatorKey:
        existing = self._keys.get(validator)
        if existing is None:
            raise ValueError("validator key does not exist")
        revoked = ValidatorKey(existing.validator, existing.key_id, existing.public_key, False)
        self._keys[validator] = revoked
        return revoked

    def get(self, validator: str) -> ValidatorKey | None:
        return self._keys.get(validator)

    def verify(self, validator: str, payload: bytes, signature: str) -> bool:
        from CORE.deepcore_crypto import verify

        record = self._keys.get(validator)
        if record is None or not record.active:
            return False
        return verify(record.public_key, payload, signature)
