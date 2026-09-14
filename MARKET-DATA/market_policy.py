"""Deterministic policy projection from market-risk evidence."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from coingecko_observation import canonical_hash
from market_risk import MarketRiskAssessment


@dataclass(frozen=True)
class MarketPolicyDecision:
    decision_type: str
    decision: str
    asset_id: str
    currency: str
    risk_score: int
    risk_assessment_hash: str
    policy_version: str
    reason: str
    decision_hash: str

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "asset_id": self.asset_id,
            "currency": self.currency,
            "decision": self.decision,
            "decision_type": self.decision_type,
            "policy_version": self.policy_version,
            "reason": self.reason,
            "risk_assessment_hash": self.risk_assessment_hash,
            "risk_score": self.risk_score,
        }


def evaluate_market_policy(
    assessment: MarketRiskAssessment,
    *,
    policy_version: str = "market-risk-v1",
) -> MarketPolicyDecision:
    """Apply a deterministic fail-closed policy to a market-risk assessment.

    Thresholds are deliberately explicit and versioned:
    0-19 -> ALLOW, 20-49 -> REVIEW, 50-79 -> ESCALATE, 80-100 -> BLOCK.
    This decision is policy evidence only. It is not financial authorization.
    """
    if assessment.assessment_type != "risk.market":
        raise ValueError("policy requires a risk.market assessment")
    if not assessment.assessment_hash:
        raise ValueError("risk assessment hash is required")
    if not policy_version:
        raise ValueError("policy_version is required")
    if not 0 <= assessment.risk_score <= 100:
        raise ValueError("risk_score must be between 0 and 100")

    score = assessment.risk_score
    if score < 20:
        decision, reason = "ALLOW", "market risk is below review threshold"
    elif score < 50:
        decision, reason = "REVIEW", "market risk requires review"
    elif score < 80:
        decision, reason = "ESCALATE", "market risk requires escalation"
    else:
        decision, reason = "BLOCK", "market risk exceeds blocking threshold"

    payload = {
        "asset_id": assessment.asset_id,
        "currency": assessment.currency,
        "decision": decision,
        "decision_type": "policy.market-risk",
        "policy_version": policy_version,
        "reason": reason,
        "risk_assessment_hash": assessment.assessment_hash,
        "risk_score": score,
    }
    return MarketPolicyDecision(
        **payload,
        decision_hash=canonical_hash(payload),
    )
