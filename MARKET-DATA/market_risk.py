"""Deterministic risk projection from independently verified market data."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any

from market_verification import MarketVerificationResult
from coingecko_observation import canonical_hash


@dataclass(frozen=True)
class MarketRiskAssessment:
    assessment_type: str
    status: str
    asset_id: str
    currency: str
    verification_hash: str
    relative_difference: str
    risk_score: int
    reason: str
    assessment_hash: str

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "asset_id": self.asset_id,
            "assessment_type": self.assessment_type,
            "currency": self.currency,
            "reason": self.reason,
            "relative_difference": self.relative_difference,
            "risk_score": self.risk_score,
            "status": self.status,
            "verification_hash": self.verification_hash,
        }


def _decimal(value: str) -> Decimal:
    try:
        result = Decimal(value)
    except (InvalidOperation, ValueError):
        raise ValueError("relative_difference must be a finite decimal") from None
    if not result.is_finite() or result < 0:
        raise ValueError("relative_difference must be a finite non-negative decimal")
    return result


def assess_market_risk(result: MarketVerificationResult) -> MarketRiskAssessment:
    """Project verification evidence into a deterministic, non-authoritative risk score.

    Risk scoring is deliberately simple at this boundary: verified observations
    score zero, while discrepancies are scored from the relative divergence,
    capped at 100. This assessment cannot authorize or mutate ledger state.
    """
    if result.result_type != "verification.result":
        raise ValueError("risk assessment requires a verification.result")
    if not result.result_hash:
        raise ValueError("verification result hash is required")

    difference = _decimal(result.relative_difference)
    if result.status == "VERIFIED":
        score = 0
        reason = "independent market observations are within tolerance"
    elif result.status == "DISCREPANCY":
        score = min(100, int((difference * Decimal("100")).to_integral_value()))
        reason = "independent market observations exceed tolerance"
    else:
        raise ValueError("unsupported verification status")

    payload = {
        "asset_id": result.asset_id,
        "assessment_type": "risk.market",
        "currency": result.currency,
        "reason": reason,
        "relative_difference": format(difference, "f"),
        "risk_score": score,
        "status": result.status,
        "verification_hash": result.result_hash,
    }
    return MarketRiskAssessment(
        **payload,
        assessment_hash=canonical_hash(payload),
    )
