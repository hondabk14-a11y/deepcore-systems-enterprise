"""Fail-closed admission boundary between authorization and consensus.

Admission verifies that an already-authorized request is structurally safe to
enter consensus. It does not mutate ledger state, sign commands, or commit
transactions.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from coingecko_observation import canonical_hash
from market_authorization import MarketAuthorizationRequest
from authorization_validator import AuthorizationValidationResult


@dataclass(frozen=True)
class LedgerAdmissionResult:
    admitted: bool
    reason: str
    request_hash: str


def admit_authorized_request(
    request: MarketAuthorizationRequest,
    validation: AuthorizationValidationResult,
    *,
    expected_action: str,
    expected_risk_hash: str,
) -> LedgerAdmissionResult:
    """Admit only a cryptographically validated, policy-authorized request."""
    if not validation.valid:
        return LedgerAdmissionResult(False, "authorization validation failed", request.request_hash)
    if validation.request_hash != request.request_hash:
        return LedgerAdmissionResult(False, "authorization validation hash mismatch", request.request_hash)
    if request.policy_decision != "ALLOW":
        return LedgerAdmissionResult(False, "policy decision is not ALLOW", request.request_hash)
    if request.action != expected_action:
        return LedgerAdmissionResult(False, "action mismatch", request.request_hash)
    if request.risk_assessment_hash != expected_risk_hash:
        return LedgerAdmissionResult(False, "risk evidence hash mismatch", request.request_hash)
    if canonical_hash(request.canonical_dict()) != request.request_hash:
        return LedgerAdmissionResult(False, "request integrity check failed", request.request_hash)
    return LedgerAdmissionResult(True, "request admitted to consensus", request.request_hash)
