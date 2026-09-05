"""Deterministic reference evaluator for DeepCore SSIL.

This module is intentionally policy-only: it evaluates supplied evidence and
never accesses secrets, changes ledger history, or performs external actions.
It is a reference implementation, not a production authorization service.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping


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


_BOOLEAN_FIELDS = (
    "cryptography_valid",
    "ledger_integrity_valid",
    "consensus_valid",
    "authorization_valid",
    "security_controls_valid",
    "recovery_controls_valid",
    "secret_boundary_valid",
    "evidence_complete",
)


def _validate_evidence_types(evidence: SSILEvidence) -> None:
    """Reject type confusion instead of relying on Python truthiness."""
    for field_name in _BOOLEAN_FIELDS:
        value = getattr(evidence, field_name)
        if not isinstance(value, bool):
            raise TypeError(f"{field_name} must be a boolean")

    signals = evidence.high_risk_signals
    if not isinstance(signals, (tuple, list)):
        raise TypeError("high_risk_signals must be a tuple or list of strings")
    if any(not isinstance(signal, str) for signal in signals):
        raise TypeError("high_risk_signals entries must be strings")


def evaluate(evidence: SSILEvidence) -> SSILDecision:
    """Evaluate evidence deterministically using fail-closed precedence."""
    if not isinstance(evidence, SSILEvidence):
        raise TypeError("evidence must be an SSILEvidence instance")
    _validate_evidence_types(evidence)

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
    """Evaluate a mapping while rejecting unknown fields and type confusion."""
    if not isinstance(evidence, Mapping):
        raise TypeError("evidence must be a mapping")

    allowed = set(SSILEvidence.__dataclass_fields__)
    unknown = set(evidence) - allowed
    if unknown:
        return SSILDecision(Decision.FAIL_CLOSED, (Reason.SECURITY_CONTROL_FAILURE,))

    normalized = dict(evidence)
    for field_name in _BOOLEAN_FIELDS:
        if field_name in normalized and not isinstance(normalized[field_name], bool):
            return SSILDecision(Decision.FAIL_CLOSED, (Reason.SECURITY_CONTROL_FAILURE,))

    if "high_risk_signals" in normalized:
        signals = normalized["high_risk_signals"]
        if not isinstance(signals, (tuple, list)) or any(not isinstance(item, str) for item in signals):
            return SSILDecision(Decision.FAIL_CLOSED, (Reason.SECURITY_CONTROL_FAILURE,))
        normalized["high_risk_signals"] = tuple(signals)

    try:
        return evaluate(SSILEvidence(**normalized))
    except (TypeError, ValueError):
        return SSILDecision(Decision.FAIL_CLOSED, (Reason.SECURITY_CONTROL_FAILURE,))
