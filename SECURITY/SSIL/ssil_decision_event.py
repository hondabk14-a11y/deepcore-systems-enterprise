"""Deterministic, auditable SSIL decision-event construction.

This module converts an SSIL evaluation into an immutable event suitable for
an audit/risk stream. It does not mutate the authoritative ledger, sign keys,
or authorize production actions.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any

from ssil_engine import Decision, Reason, SSILEvidence, SSILDecision, evaluate


EVENT_TYPE = "SSIL_DECISION"


@dataclass(frozen=True)
class SSILDecisionEvent:
    event_type: str
    policy_version: str
    evidence_hash: str
    event_sequence: int
    decision: str
    reason_codes: tuple[str, ...]
    evaluator_version: str

    def to_mapping(self) -> dict[str, Any]:
        return {
            "event_type": self.event_type,
            "policy_version": self.policy_version,
            "evidence_hash": self.evidence_hash,
            "event_sequence": self.event_sequence,
            "decision": self.decision,
            "reason_codes": list(self.reason_codes),
            "evaluator_version": self.evaluator_version,
        }

    def canonical_json(self) -> str:
        return json.dumps(self.to_mapping(), sort_keys=True, separators=(",", ":"))

    def event_hash(self) -> str:
        return hashlib.sha256(self.canonical_json().encode("utf-8")).hexdigest()


def _canonical_evidence(evidence: SSILEvidence) -> str:
    return json.dumps(
        {
            "cryptography_valid": evidence.cryptography_valid,
            "ledger_integrity_valid": evidence.ledger_integrity_valid,
            "consensus_valid": evidence.consensus_valid,
            "authorization_valid": evidence.authorization_valid,
            "security_controls_valid": evidence.security_controls_valid,
            "recovery_controls_valid": evidence.recovery_controls_valid,
            "secret_boundary_valid": evidence.secret_boundary_valid,
            "evidence_complete": evidence.evidence_complete,
            "high_risk_signals": list(evidence.high_risk_signals),
        },
        sort_keys=True,
        separators=(",", ":"),
    )


def build_decision_event(
    evidence: SSILEvidence,
    *,
    policy_version: str,
    event_sequence: int,
    evaluator_version: str = "ssil-engine/0.1.0",
) -> SSILDecisionEvent:
    """Evaluate evidence and construct a deterministic SSIL decision event."""
    if not policy_version.strip():
        raise ValueError("policy_version must be non-empty")
    if not evaluator_version.strip():
        raise ValueError("evaluator_version must be non-empty")
    if isinstance(event_sequence, bool) or not isinstance(event_sequence, int):
        raise TypeError("event_sequence must be an integer")
    if event_sequence < 0:
        raise ValueError("event_sequence must be non-negative")

    decision: SSILDecision = evaluate(evidence)
    evidence_hash = hashlib.sha256(_canonical_evidence(evidence).encode("utf-8")).hexdigest()

    return SSILDecisionEvent(
        event_type=EVENT_TYPE,
        policy_version=policy_version,
        evidence_hash=evidence_hash,
        event_sequence=event_sequence,
        decision=decision.decision.value,
        reason_codes=tuple(reason.value for reason in decision.reasons),
        evaluator_version=evaluator_version,
    )


def validate_decision_event(event: SSILDecisionEvent) -> None:
    """Reject structurally invalid or semantically contradictory decision events."""
    if not isinstance(event, SSILDecisionEvent):
        raise TypeError("event must be an SSILDecisionEvent instance")
    if event.event_type != EVENT_TYPE:
        raise ValueError("invalid event_type")
    if not isinstance(event.policy_version, str) or not event.policy_version.strip():
        raise ValueError("policy_version must be non-empty")
    if not isinstance(event.evidence_hash, str) or len(event.evidence_hash) != 64:
        raise ValueError("evidence_hash must be a SHA-256 hex digest")
    try:
        int(event.evidence_hash, 16)
    except ValueError as exc:
        raise ValueError("evidence_hash must be hexadecimal") from exc
    if isinstance(event.event_sequence, bool) or not isinstance(event.event_sequence, int) or event.event_sequence < 0:
        raise ValueError("event_sequence must be a non-negative integer")
    if event.decision not in {item.value for item in Decision}:
        raise ValueError("invalid decision")
    if not isinstance(event.reason_codes, tuple) or not event.reason_codes:
        raise ValueError("reason_codes must be a non-empty tuple")
    valid_reasons = {item.value for item in Reason}
    if any(not isinstance(code, str) or code not in valid_reasons for code in event.reason_codes):
        raise ValueError("reason_codes contains an invalid reason")
    if not isinstance(event.evaluator_version, str) or not event.evaluator_version.strip():
        raise ValueError("evaluator_version must be non-empty")

    reasons = set(event.reason_codes)
    if event.decision == Decision.ALLOW.value and reasons != {Reason.POLICY_SATISFIED.value}:
        raise ValueError("ALLOW requires POLICY_SATISFIED")
    if event.decision == Decision.REVIEW.value and reasons != {Reason.HIGH_RISK_SIGNAL.value}:
        raise ValueError("REVIEW requires HIGH_RISK_SIGNAL")
    if event.decision == Decision.DEFER.value and reasons != {Reason.EVIDENCE_INCOMPLETE.value}:
        raise ValueError("DEFER requires EVIDENCE_INCOMPLETE")
    if event.decision == Decision.FAIL_CLOSED.value:
        failure_reasons = {
            Reason.CRYPTOGRAPHIC_FAILURE.value,
            Reason.LEDGER_INTEGRITY_FAILURE.value,
            Reason.CONSENSUS_FAILURE.value,
            Reason.AUTHORIZATION_FAILURE.value,
            Reason.SECURITY_CONTROL_FAILURE.value,
            Reason.RECOVERY_CONTROL_FAILURE.value,
            Reason.SECRET_BOUNDARY_FAILURE.value,
        }
        if not reasons.issubset(failure_reasons):
            raise ValueError("FAIL_CLOSED contains non-failure reason codes")
