"""Authorization-request binding for deterministic market policy evidence.

This module creates an authorization request from policy evidence. It does not
sign, submit, or commit a command. Private-key operations remain outside this
market-data boundary.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from coingecko_observation import canonical_hash
from market_policy import MarketPolicyDecision


@dataclass(frozen=True)
class MarketAuthorizationRequest:
    request_type: str
    request_id: str
    principal: str
    action: str
    subject: str
    policy_decision: str
    policy_version: str
    risk_assessment_hash: str
    nonce: str
    expires_at: str
    request_hash: str

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "action": self.action,
            "expires_at": self.expires_at,
            "nonce": self.nonce,
            "policy_decision": self.policy_decision,
            "policy_version": self.policy_version,
            "principal": self.principal,
            "request_id": self.request_id,
            "request_type": self.request_type,
            "risk_assessment_hash": self.risk_assessment_hash,
            "subject": self.subject,
        }


def build_authorization_request(
    decision: MarketPolicyDecision,
    *,
    request_id: str,
    principal: str,
    action: str,
    nonce: str,
    expires_at: str,
) -> MarketAuthorizationRequest:
    """Bind policy evidence to an authorization request without signing it."""
    for value, field in (
        (request_id, "request_id"),
        (principal, "principal"),
        (action, "action"),
        (nonce, "nonce"),
        (expires_at, "expires_at"),
    ):
        if not value:
            raise ValueError(f"{field} is required")
    if not decision.decision_hash:
        raise ValueError("policy decision hash is required")
    if decision.decision == "BLOCK":
        raise ValueError("blocked policy decision cannot become an authorization request")

    payload = {
        "action": action,
        "expires_at": expires_at,
        "nonce": nonce,
        "policy_decision": decision.decision,
        "policy_version": decision.policy_version,
        "principal": principal,
        "request_id": request_id,
        "request_type": "authorization.request",
        "risk_assessment_hash": decision.risk_assessment_hash,
        "subject": decision.asset_id,
    }
    return MarketAuthorizationRequest(
        **payload,
        request_hash=canonical_hash(payload),
    )
