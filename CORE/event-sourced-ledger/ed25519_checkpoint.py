"""Concrete Ed25519 verifier for signed ledger checkpoints.

This adapter uses the widely reviewed ``cryptography`` package. Key
resolution remains outside this module so authenticated key custody and
rotation policy are not silently embedded in application code.
"""
from __future__ import annotations

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey


class Ed25519CheckpointVerifier:
    """Verify checkpoint signatures with an Ed25519 public key."""

    def verify(self, message: bytes, signature: bytes, public_key: bytes) -> bool:
        try:
            Ed25519PublicKey.from_public_bytes(public_key).verify(signature, message)
        except (InvalidSignature, ValueError, TypeError):
            return False
        return True
