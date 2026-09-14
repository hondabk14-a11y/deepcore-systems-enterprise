"""Cryptographic validation boundary for DeepCore authorization requests.

The validator verifies an externally supplied signature and authorization
request. It never creates signatures, handles private keys, mutates ledger
state, or advances consensus.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from coingecko_observation import canonical_hash
from market_authorization import MarketAuthorizationRequest


class NonceStore(Protocol):
    def claim(self, principal: str, nonce: str) -> bool:
        """Atomically claim a nonce, returning False when already consumed."""


@dataclass
class InMemoryNonceStore:
    """Test/reference nonce store; production must use durable atomic storage."""

    _seen: set[tuple[str, str]]

    def __init__(self) -> None:
        self._seen = set()

    def claim(self, principal: str, nonce: str) -> bool:
        key = (principal, nonce)
        if key in self._seen:
            return False
        self._seen.add(key)
        return True


@dataclass(frozen=True)
class AuthorizationValidationResult:
    valid: bool
    reason: str
    request_hash: str


def _parse_expiry(expires_at: str) -> datetime:
    try:
        value = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
    except ValueError:
        raise ValueError("expires_at must be an ISO-8601 timestamp") from None
    if value.tzinfo is None:
        raise ValueError("expires_at must include a timezone")
    return value.astimezone(timezone.utc)


def validate_authorization_request(
    request: MarketAuthorizationRequest,
    *,
    signature: bytes,
    public_key: Ed25519PublicKey,
    expected_principal: str,
    nonce_store: NonceStore,
    now: datetime | None = None,
) -> AuthorizationValidationResult:
    """Verify identity, request integrity, signature, expiry, and replay state."""
    if request.principal != expected_principal:
        return AuthorizationValidationResult(False, "principal mismatch", request.request_hash)
    if request.policy_decision not in {"ALLOW", "REVIEW", "ESCALATE"}:
        return AuthorizationValidationResult(False, "policy decision is not authorizable", request.request_hash)

    expected_hash = canonical_hash(request.canonical_dict())
    if expected_hash != request.request_hash:
        return AuthorizationValidationResult(False, "request hash mismatch", request.request_hash)

    try:
        public_key.verify(signature, request.request_hash.encode("ascii"))
    except (InvalidSignature, ValueError, TypeError):
        return AuthorizationValidationResult(False, "invalid signature", request.request_hash)

    try:
        expiry = _parse_expiry(request.expires_at)
    except ValueError as exc:
        return AuthorizationValidationResult(False, str(exc), request.request_hash)

    current = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    if expiry <= current:
        return AuthorizationValidationResult(False, "authorization request expired", request.request_hash)

    if not nonce_store.claim(request.principal, request.nonce):
        return AuthorizationValidationResult(False, "authorization request replayed", request.request_hash)

    return AuthorizationValidationResult(True, "authorization request verified", request.request_hash)
