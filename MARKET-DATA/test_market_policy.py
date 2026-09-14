"""Tests for the deterministic market-risk policy gate."""

from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / filename)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


risk_module = _load("market_risk", "market_risk.py")
policy_module = _load("market_policy", "market_policy.py")


def _assessment(score: int):
    return risk_module.MarketRiskAssessment(
        assessment_type="risk.market",
        status="DISCREPANCY" if score else "VERIFIED",
        asset_id="bitcoin",
        currency="usd",
        verification_hash="a" * 64,
        relative_difference=str(score / 100),
        risk_score=score,
        reason="fixture",
        assessment_hash="b" * 64,
    )


def test_policy_thresholds_are_deterministic() -> None:
    assert policy_module.evaluate_market_policy(_assessment(0)).decision == "ALLOW"
    assert policy_module.evaluate_market_policy(_assessment(19)).decision == "ALLOW"
    assert policy_module.evaluate_market_policy(_assessment(20)).decision == "REVIEW"
    assert policy_module.evaluate_market_policy(_assessment(49)).decision == "REVIEW"
    assert policy_module.evaluate_market_policy(_assessment(50)).decision == "ESCALATE"
    assert policy_module.evaluate_market_policy(_assessment(79)).decision == "ESCALATE"
    assert policy_module.evaluate_market_policy(_assessment(80)).decision == "BLOCK"
    assert policy_module.evaluate_market_policy(_assessment(100)).decision == "BLOCK"


def test_policy_version_is_bound_into_decision_hash() -> None:
    first = policy_module.evaluate_market_policy(_assessment(50), policy_version="market-risk-v1")
    second = policy_module.evaluate_market_policy(_assessment(50), policy_version="market-risk-v2")
    assert first.decision_hash != second.decision_hash
    assert first.policy_version == "market-risk-v1"
    assert second.policy_version == "market-risk-v2"


def test_invalid_risk_score_is_rejected() -> None:
    invalid = _assessment(101)
    try:
        policy_module.evaluate_market_policy(invalid)
    except ValueError as exc:
        assert "between 0 and 100" in str(exc)
    else:
        raise AssertionError("invalid risk score must be rejected")


def test_policy_requires_risk_market_assessment() -> None:
    invalid = _assessment(10)
    invalid = invalid.__class__(**{**invalid.__dict__, "assessment_type": "other"})
    try:
        policy_module.evaluate_market_policy(invalid)
    except ValueError as exc:
        assert "risk.market" in str(exc)
    else:
        raise AssertionError("wrong assessment type must be rejected")


def test_policy_decision_hash_is_deterministic() -> None:
    first = policy_module.evaluate_market_policy(_assessment(80))
    second = policy_module.evaluate_market_policy(_assessment(80))
    assert first.decision_hash == second.decision_hash
    assert first.decision == "BLOCK"
