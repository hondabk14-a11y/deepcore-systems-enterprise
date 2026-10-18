"""Tests for deterministic market risk projection."""

from __future__ import annotations



import market_risk as risk_module
import market_verification as verification_module
import coingecko_observation as observation_module
import market_price_event as event_module


def _verification(status: str, difference: str):
    return verification_module.MarketVerificationResult(
        result_type="verification.result",
        status=status,
        asset_id="bitcoin",
        currency="usd",
        providers=("coingecko", "arkham"),
        relative_difference=difference,
        tolerance="0.01",
        source_event_hashes=("a" * 64, "b" * 64),
        result_hash="c" * 64,
    )


def test_verified_observation_has_zero_market_risk() -> None:
    assessment = risk_module.assess_market_risk(_verification("VERIFIED", "0.001"))
    assert assessment.risk_score == 0
    assert assessment.status == "VERIFIED"
    assert assessment.assessment_type == "risk.market"
    assert assessment.verification_hash == "c" * 64


def test_discrepancy_maps_deterministically_to_risk_score() -> None:
    assessment = risk_module.assess_market_risk(_verification("DISCREPANCY", "0.20"))
    assert assessment.risk_score == 20
    assert assessment.reason == "independent market observations exceed tolerance"


def test_risk_score_is_capped_at_100() -> None:
    assessment = risk_module.assess_market_risk(_verification("DISCREPANCY", "2.00"))
    assert assessment.risk_score == 100


def test_unsupported_verification_status_is_rejected() -> None:
    try:
        risk_module.assess_market_risk(_verification("UNKNOWN", "0.01"))
    except ValueError as exc:
        assert "unsupported verification status" in str(exc)
    else:
        raise AssertionError("unsupported status must be rejected")


def test_assessment_hash_is_deterministic() -> None:
    first = risk_module.assess_market_risk(_verification("DISCREPANCY", "0.20"))
    second = risk_module.assess_market_risk(_verification("DISCREPANCY", "0.20"))
    assert first.assessment_hash == second.assessment_hash

