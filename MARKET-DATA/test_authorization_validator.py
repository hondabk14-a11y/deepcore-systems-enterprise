"""Deterministic cryptographic authorization validation coverage."""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

import authorization_validator as validator
import market_authorization as authorization
import market_policy as policy


class Decision:
    decision = "ALLOW"
    decision_hash = "b" * 64
    policy_version = "market-risk-v1"
    risk_assessment_hash = "a" * 64
    asset_id = "bitcoin"


def _request():
    return authorization.build_authorization_request(
        Decision(),
        request_id="req-crypto-001",
        principal="risk-service",
        action="market.observe",
        nonce="nonce-crypto-001",
        expires_at="2026-09-14T12:00:00+00:00",
    )


def _now():
    return datetime(2026, 9, 14, 11, 0, tzinfo=timezone.utc)


def test_valid_ed25519_signature_is_accepted():
    request = _request()
    private_key = Ed25519PrivateKey.generate()
    signature = private_key.sign(request.request_hash.encode("ascii"))
    result = validator.validate_authorization_request(
        request,
        signature=signature,
        public_key=private_key.public_key(),
        expected_principal="risk-service",
        nonce_store=validator.InMemoryNonceStore(),
        now=_now(),
    )
    assert result.valid is True
    assert result.reason == "authorization request verified"


def test_invalid_signature_is_rejected():
    request = _request()
    private_key = Ed25519PrivateKey.generate()
    other_key = Ed25519PrivateKey.generate()
    signature = private_key.sign(request.request_hash.encode("ascii"))
    result = validator.validate_authorization_request(
        request,
        signature=signature,
        public_key=other_key.public_key(),
        expected_principal="risk-service",
        nonce_store=validator.InMemoryNonceStore(),
        now=_now(),
    )
    assert result.valid is False
    assert result.reason == "invalid signature"


def test_principal_mismatch_is_rejected_before_signature_check():
    request = _request()
    key = Ed25519PrivateKey.generate()
    signature = key.sign(request.request_hash.encode("ascii"))
    result = validator.validate_authorization_request(
        request,
        signature=signature,
        public_key=key.public_key(),
        expected_principal="different-principal",
        nonce_store=validator.InMemoryNonceStore(),
        now=_now(),
    )
    assert result.valid is False
    assert result.reason == "principal mismatch"


def test_expired_request_is_rejected():
    request = authorization.build_authorization_request(
        Decision(),
        request_id="req-crypto-expired",
        principal="risk-service",
        action="market.observe",
        nonce="nonce-expired",
        expires_at="2026-09-14T10:00:00+00:00",
    )
    key = Ed25519PrivateKey.generate()
    signature = key.sign(request.request_hash.encode("ascii"))
    result = validator.validate_authorization_request(
        request,
        signature=signature,
        public_key=key.public_key(),
        expected_principal="risk-service",
        nonce_store=validator.InMemoryNonceStore(),
        now=_now(),
    )
    assert result.valid is False
    assert result.reason == "authorization request expired"


def test_nonce_replay_is_rejected():
    request = _request()
    key = Ed25519PrivateKey.generate()
    signature = key.sign(request.request_hash.encode("ascii"))
    store = validator.InMemoryNonceStore()
    first = validator.validate_authorization_request(
        request,
        signature=signature,
        public_key=key.public_key(),
        expected_principal="risk-service",
        nonce_store=store,
        now=_now(),
    )
    second = validator.validate_authorization_request(
        request,
        signature=signature,
        public_key=key.public_key(),
        expected_principal="risk-service",
        nonce_store=store,
        now=_now(),
    )
    assert first.valid is True
    assert second.valid is False
    assert second.reason == "authorization request replayed"


def test_tampered_request_hash_is_rejected():
    request = _request()
    key = Ed25519PrivateKey.generate()
    signature = key.sign(request.request_hash.encode("ascii"))
    tampered = authorization.MarketAuthorizationRequest(
        **{**request.__dict__, "action": "tampered"}
    )
    result = validator.validate_authorization_request(
        tampered,
        signature=signature,
        public_key=key.public_key(),
        expected_principal="risk-service",
        nonce_store=validator.InMemoryNonceStore(),
        now=_now(),
    )
    assert result.valid is False
    assert result.reason == "request hash mismatch"
