"""Deterministic, auditable SSIL decision-event construction.

This module converts an SSIL evaluation into an immutable event suitable for
an audit/risk stream. It does not mutate the authoritative ledger, sign keys,
or authorize production actions.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Mapping

from ssil_engine import SSILEvidence, SSILDecision, evaluate


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
        return json.dumps(
            self.to_mapping(), sort_keys=True, separators=(",", ":")
        )

    def event_hash(self) -> str:
        return hashlib.sha256(self.canonical_json().encode("utf-8")).hexdigest()


def _canonical_evidence(evidence: SSILEvidence) -> str:
    return json.dumps(
        {
            "crypto_verified": evidence.crypto_verified,
            "ledger_integrity_verified": evidence.ledger_integrity_verified,
            "consensus_verified": evidence.consensus_verified,
            "authorization_verified": evidence.authorization_verified,
            "security_controls_verified": evidence.security_controls_verified,
            "recovery_controls_verified": evidence.recovery_controls_verified,
            "secret_boundary_verified": evidence.secret_boundary_verified,
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
    evidence_hash = hashlib.sha256(
        _canonical_evidence(evidence).encode("utf-8")
    ).hexdigest()

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
    """Reject structurally invalid decision events."""
    if event.event_type != EVENT_TYPE:
        raise ValueError("invalid event_type")
    if not event.policy_version.strip():
        raise ValueError("policy_version must be non-empty")
    if len(event.evidence_hash) != 64:
        raise ValueError("evidence_hash must be a SHA-256 hex digest")
    try:
        int(event.evidence_hash, 16)
    except ValueError as exc:
        raise ValueError("evidence_hash must be hexadecimal") from exc
    if isinstance(event.event_sequence, bool) or event.event_sequence < 0:
        raise ValueError("event_sequence must be non-negative")
    if event.decision not in {item.value for item in __import__("ssil_engine").Decision}:
        raise ValueError("invalid decision")
    if not event.reason_codes:
        raise ValueError("reason_codes must be non-empty")
    if not event.evaluator_version.strip():
        raise ValueError("evaluator_version must be non-empty")
