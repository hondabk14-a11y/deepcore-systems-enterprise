"""Reference signed-checkpoint envelope and verification boundary.

The envelope is deliberately independent of a concrete Ed25519 library.
Production verification must provide an authenticated public-key resolver and
an implementation of CheckpointSignatureVerifier. This module does not create
or persist private keys.
"""
from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from typing import Protocol

from checkpoint import LedgerCheckpoint


class SignatureVerificationError(ValueError):
    """Raised when a signed checkpoint cannot be trusted."""


class CheckpointSignatureVerifier(Protocol):
    """Cryptographic verification interface supplied by the deployment."""

    def verify(self, message: bytes, signature: bytes, public_key: bytes) -> bool:
        """Return True only when the signature is valid for the message."""
        ...


class CheckpointPublicKeyResolver(Protocol):
    """Resolve the authenticated public key for a checkpoint key ID."""

    def resolve(self, key_id: str) -> bytes | None:
        ...


@dataclass(frozen=True)
class SignedCheckpoint:
    """Canonical checkpoint envelope carrying an external signature."""

    ledger_id: str
    sequence: int
    head_hash: str
    event_count: int
    key_id: str
    signature: bytes

    @classmethod
    def from_checkpoint(
        cls,
        checkpoint: LedgerCheckpoint,
        *,
        key_id: str,
        signature: bytes,
    ) -> "SignedCheckpoint":
        if not checkpoint.ledger_id:
            raise ValueError("checkpoint ledger_id is required")
        if not key_id:
            raise ValueError("key_id is required")
        return cls(
            ledger_id=checkpoint.ledger_id,
            sequence=checkpoint.sequence,
            head_hash=checkpoint.head_hash,
            event_count=checkpoint.event_count,
            key_id=key_id,
            signature=bytes(signature),
        )

    def unsigned_bytes(self) -> bytes:
        """Return the canonical bytes covered by the signature."""
        payload = {
            "event_count": self.event_count,
            "head_hash": self.head_hash,
            "key_id": self.key_id,
            "ledger_id": self.ledger_id,
            "sequence": self.sequence,
        }
        return json.dumps(
            payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True
        ).encode("utf-8")

    def to_checkpoint(self) -> LedgerCheckpoint:
        return LedgerCheckpoint(
            ledger_id=self.ledger_id,
            sequence=self.sequence,
            head_hash=self.head_hash,
            event_count=self.event_count,
        )

    def encoded_signature(self) -> str:
        return base64.b64encode(self.signature).decode("ascii")


def verify_signed_checkpoint(
    signed: SignedCheckpoint,
    *,
    key_resolver: CheckpointPublicKeyResolver,
    verifier: CheckpointSignatureVerifier,
) -> LedgerCheckpoint:
    """Verify the signature and return only the authenticated checkpoint."""
    if not signed.ledger_id or not signed.key_id:
        raise SignatureVerificationError("signed checkpoint identity is incomplete")
    public_key = key_resolver.resolve(signed.key_id)
    if public_key is None:
        raise SignatureVerificationError(
            f"no authenticated public key for key_id {signed.key_id!r}"
        )
    try:
        valid = verifier.verify(signed.unsigned_bytes(), signed.signature, public_key)
    except Exception as exc:
        raise SignatureVerificationError("checkpoint signature verification failed") from exc
    if not valid:
        raise SignatureVerificationError("checkpoint signature is invalid")
    return signed.to_checkpoint()
