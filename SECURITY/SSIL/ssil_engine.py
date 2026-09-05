"""Deterministic reference evaluator for DeepCore SSIL.

This module is intentionally policy-only: it evaluates supplied evidence and
never accesses secrets, changes ledger history, or performs external actions.
It is a reference implementation, not a production authorization service.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable, Mapping


class Decision(str, Enum):
    ALLOW = "ALLOW"
    REVIEW = "REVIEW"
    DEFER = "DEFER"
    FAIL_CLOSED = "FAIL_CLOSED"


class Reason(str, Enum):
    CRYPTOGRAPHIC_FAILURE = "CRYPTOGRAPHIC_FAILURE"
    LEDGER_INTEGRITY_FAILURE = "LEDGER_INTEGRITY_FAILURE"
    CONSENSUS_FAILURE = "CONSENSUS_FAILURE"
    AUTHORIZATION_FAILURE = "AUTHORIZATION_FAILURE"
    SECURITY_CONTROL_FAILURE = "SECURITY_CONTROL_FAILURE"
    RECOVERY_CONTROL_FAILURE = "RECOVERY_CONTROL_FAILURE"
    SECRET_BOUNDARY_FAILURE = "SECRET_BOUNDARY_FAILURE"
    HIGH_RISK_SIGNAL = "HIGH_RISK_SIGNAL"
    EVIDENCE_INCOMPLETE = "EVIDENCE_INCOMPLETE"
    POLICY_SATISFIED = "POLICY_SATISFIED"


@dataclass(frozen=True)
class SSILEvidence:
    """Immutable evidence supplied to the evaluator."""

    cryptography_valid: bool = True
    ledger_integrity_valid: bool = True
    consensus_valid: bool = True
    authorization_valid: bool = True
    security_controls_valid: bool = True
    recovery_controls_valid: bool = True
    secret_boundary_valid: bool = True
    evidence_complete: bool = True
    high_risk_signals: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class SSILDecision:
    decision: Decision
    reasons: tuple[Reason, ...]


def evaluate(evidence: SSILEvidence) -> SSILDecision:
    """Evaluate evidence deterministically using fail-closed precedence."""

    reasons: list[Reason] = []

    mandatory_failures = (
        (not evidence.cryptography_valid, Reason.CRYPTOGRAPHIC_FAILURE),
        (not evidence.ledger_integrity_valid, Reason.LEDGER_INTEGRITY_FAILURE),
        (not evidence.consensus_valid, Reason.CONSENSUS_FAILURE),
        (not evidence.authorization_valid, Reason.AUTHORIZATION_FAILURE),
        (not evidence.security_controls_valid, Reason.SECURITY_CONTROL_FAILURE),
        (not evidence.recovery_controls_valid, Reason.RECOVERY_CONTROL_FAILURE),
        (not evidence.secret_boundary_valid, Reason.SECRET_BOUNDARY_FAILURE),
    )

    for failed, reason in mandatory_failures:
        if failed:
            reasons.append(reason)

    if reasons:
        return SSILDecision(Decision.FAIL_CLOSED, tuple(reasons))

    if not evidence.evidence_complete:
        return SSILDecision(Decision.DEFER, (Reason.EVIDENCE_INCOMPLETE,))

    if evidence.high_risk_signals:
        return SSILDecision(Decision.REVIEW, (Reason.HIGH_RISK_SIGNAL,))

    return SSILDecision(Decision.ALLOW, (Reason.POLICY_SATISFIED,))


def evaluate_mapping(evidence: Mapping[str, object]) -> SSILDecision:
    """Evaluate a mapping while rejecting unknown fields for deterministic use."""

    allowed = set(SSILEvidence.__dataclass_fields__)
    unknown = set(evidence) - allowed
    if unknown:
        return SSILDecision(Decision.FAIL_CLOSED, (Reason.SECURITY_CONTROL_FAILURE,))

    normalized = dict(evidence)
    if "high_risk_signals" in normalized:
        normalized["high_risk_signals"] = tuple(normalized["high_risk_signals"])
    return evaluate(SSILEvidence(**normalized))
