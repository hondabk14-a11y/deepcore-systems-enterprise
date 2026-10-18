"""Authenticated signed-checkpoint envelope and verification boundary."""
from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from typing import Callable, Protocol

from checkpoint import LedgerCheckpoint


class SignatureVerificationError(ValueError):
    """Raised when a signed checkpoint cannot be trusted."""


class CheckpointSignatureVerifier(Protocol):
    def verify(self, message: bytes, signature: bytes, public_key: bytes) -> bool:
        ...


class CheckpointPublicKeyResolver(Protocol):
    def resolve(self, key_id: str) -> bytes | None:
        ...


@dataclass(frozen=True)
class SignedCheckpoint:
    ledger_id: str
    sequence: int
    head_hash: str
    event_count: int
    key_id: str
    signature: bytes

    @classmethod
    def from_checkpoint(cls, checkpoint: LedgerCheckpoint, *, key_id: str, signature: bytes) -> "SignedCheckpoint":
        if not checkpoint.ledger_id:
            raise ValueError("checkpoint ledger_id is required")
        if not key_id:
            raise ValueError("key_id is required")
        return cls(checkpoint.ledger_id, checkpoint.sequence, checkpoint.head_hash, checkpoint.event_count, key_id, bytes(signature))

    def unsigned_bytes(self) -> bytes:
        payload = {
            "event_count": self.event_count,
            "head_hash": self.head_hash,
            "key_id": self.key_id,
            "ledger_id": self.ledger_id,
            "sequence": self.sequence,
        }
        return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")

    def to_checkpoint(self) -> LedgerCheckpoint:
        return LedgerCheckpoint(self.ledger_id, self.sequence, self.head_hash, self.event_count)

    def encoded_signature(self) -> str:
        return base64.b64encode(self.signature).decode("ascii")


def verify_signed_checkpoint(signed: SignedCheckpoint, *, key_resolver: CheckpointPublicKeyResolver | Callable[[str], bytes | None], verifier: CheckpointSignatureVerifier) -> LedgerCheckpoint:
    if not signed.ledger_id or not signed.key_id:
        raise SignatureVerificationError("signed checkpoint identity is incomplete")
    try:
        resolve = getattr(key_resolver, "resolve", None)
        public_key = resolve(signed.key_id) if callable(resolve) else key_resolver(signed.key_id)
    except Exception as exc:
        raise SignatureVerificationError("authenticated key resolution failed") from exc
    if public_key is None:
        raise SignatureVerificationError(f"no authenticated public key for key_id {signed.key_id!r}")
    try:
        valid = verifier.verify(signed.unsigned_bytes(), signed.signature, public_key)
    except Exception as exc:
        raise SignatureVerificationError("checkpoint signature verification failed") from exc
    if not valid:
        raise SignatureVerificationError("checkpoint signature is invalid")
    return signed.to_checkpoint()
