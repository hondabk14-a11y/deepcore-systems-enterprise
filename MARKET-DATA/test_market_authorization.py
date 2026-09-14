"""Tests for market policy to authorization-request binding."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / filename)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


policy = _load("market_policy", "market_policy.py")
authorization = _load("market_authorization", "market_authorization.py")


def _decision(name: str = "ALLOW"):
    return policy.MarketPolicyDecision(
        decision_type="policy.market-risk",
        decision=name,
        asset_id="bitcoin",
        currency="usd",
        risk_score=0 if name == "ALLOW" else 90,
        risk_assessment_hash="a" * 64,
        policy_version="market-risk-v1",
        reason="test",
        decision_hash="b" * 64,
    )


def test_policy_evidence_is_bound_to_authorization_request() -> None:
    request = authorization.build_authorization_request(
        _decision(),
        request_id="req-001",
        principal="risk-service",
        action="market.observe",
        nonce="nonce-001",
        expires_at="2026-09-14T01:00:00+00:00",
    )
    assert request.request_type == "authorization.request"
    assert request.policy_decision == "ALLOW"
    assert request.policy_version == "market-risk-v1"
    assert request.risk_assessment_hash == "a" * 64
    assert request.subject == "bitcoin"
    assert request.request_hash


def test_non_allow_policy_cannot_become_authorization_request() -> None:
    for decision in ("REVIEW", "ESCALATE", "BLOCK"):
        with pytest.raises(ValueError, match="only ALLOW"):
            authorization.build_authorization_request(
                _decision(decision),
                request_id="req-002",
                principal="risk-service",
                action="market.observe",
                nonce="nonce-002",
                expires_at="2026-09-14T01:00:00+00:00",
            )


def test_required_request_fields_fail_closed() -> None:
    for field, value in (
        ("request_id", ""),
        ("principal", ""),
        ("action", ""),
        ("nonce", ""),
        ("expires_at", ""),
    ):
        kwargs = {
            "request_id": "req-003",
            "principal": "risk-service",
            "action": "market.observe",
            "nonce": "nonce-003",
            "expires_at": "2026-09-14T01:00:00+00:00",
        }
        kwargs[field] = value
        with pytest.raises(ValueError, match=field):
            authorization.build_authorization_request(_decision(), **kwargs)


def test_request_hash_is_deterministic() -> None:
    kwargs = {
        "request_id": "req-004",
        "principal": "risk-service",
        "action": "market.observe",
        "nonce": "nonce-004",
        "expires_at": "2026-09-14T01:00:00+00:00",
    }
    first = authorization.build_authorization_request(_decision(), **kwargs)
    second = authorization.build_authorization_request(_decision(), **kwargs)
    assert first.request_hash == second.request_hash
