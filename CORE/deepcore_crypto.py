#!/usr/bin/env python3
"""Production-oriented Ed25519 identity primitives for DeepCore.

Private keys are intentionally kept in memory only. This module does not
provide HSM storage, rotation, revocation, or remote key management.
Those are separate custody controls that must be designed and audited.
"""

from __future__ import annotations

import base64
import hashlib
from dataclasses import dataclass

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey


def _b64u(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64u_decode(value: str) -> bytes:
    if not isinstance(value, str) or not value:
        raise ValueError("signature must be a non-empty string")
    padding = "=" * (-len(value) % 4)
    try:
        return base64.urlsafe_b64decode((value + padding).encode("ascii"))
    except (ValueError, UnicodeEncodeError) as exc:
        raise ValueError("invalid base64url encoding") from exc


def key_id(public_key: bytes) -> str:
    """Stable SHA-256 fingerprint used as the DeepCore key identifier."""
    if len(public_key) != 32:
        raise ValueError("Ed25519 public key must be exactly 32 bytes")
    return hashlib.sha256(public_key).hexdigest()


@dataclass(frozen=True)
class Ed25519Identity:
    """An Ed25519 signing identity with an explicit public-key fingerprint."""

    private_key: Ed25519PrivateKey

    @classmethod
    def generate(cls) -> "Ed25519Identity":
        return cls(Ed25519PrivateKey.generate())

    @classmethod
    def from_private_bytes(cls, private_key: bytes) -> "Ed25519Identity":
        if len(private_key) != 32:
            raise ValueError("Ed25519 private key must be exactly 32 bytes")
        return cls(Ed25519PrivateKey.from_private_bytes(private_key))

    @property
    def private_key_bytes(self) -> bytes:
        return self.private_key.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption(),
        )

    @property
    def public_key_bytes(self) -> bytes:
        return self.private_key.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )

    @property
    def public_key_b64(self) -> str:
        return _b64u(self.public_key_bytes)

    @property
    def key_id(self) -> str:
        return key_id(self.public_key_bytes)

    def sign(self, payload: bytes) -> str:
        """Sign exact bytes and return a compact base64url signature."""
        return _b64u(self.private_key.sign(payload))

    def verify(self, payload: bytes, signature: str) -> bool:
        return verify(self.public_key_bytes, payload, signature)


def verify(public_key: bytes, payload: bytes, signature: str) -> bool:
    """Verify an Ed25519 signature without accepting malformed key sizes."""
    if len(public_key) != 32:
        raise ValueError("Ed25519 public key must be exactly 32 bytes")
    raw_signature = _b64u_decode(signature)
    if len(raw_signature) != 64:
        return False
    try:
        Ed25519PublicKey.from_public_bytes(public_key).verify(raw_signature, payload)
    except (InvalidSignature, ValueError):
        return False
    return True
