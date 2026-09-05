"""Bind an SSIL decision to a specific readiness evidence event."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any

from ssil_decision_event import SSILDecisionEvent, validate_decision_event


EVENT_TYPE = "SSIL_READINESS_DECISION"


@dataclass(frozen=True)
class SSILReadinessDecisionEvent:
    event_type: str
    evidence_event_hash: str
    decision_event_hash: str
    decision: str
    policy_version: str
    evaluator_version: str

    def to_mapping(self) -> dict[str, Any]:
        return {
            "event_type": self.event_type,
            "evidence_event_hash": self.evidence_event_hash,
            "decision_event_hash": self.decision_event_hash,
            "decision": self.decision,
            "policy_version": self.policy_version,
            "evaluator_version": self.evaluator_version,
        }

    def canonical_json(self) -> str:
        return json.dumps(self.to_mapping(), sort_keys=True, separators=(",", ":"))

    def event_hash(self) -> str:
        return hashlib.sha256(self.canonical_json().encode("utf-8")).hexdigest()


def build_readiness_decision_event(
    evidence_event_hash: str,
    decision_event: SSILDecisionEvent,
) -> SSILReadinessDecisionEvent:
    """Create a deterministic link from readiness evidence to its SSIL decision."""
    validate_decision_event(decision_event)
    if not isinstance(evidence_event_hash, str) or len(evidence_event_hash) != 64:
        raise ValueError("evidence_event_hash must be a SHA-256 hex digest")
    try:
        int(evidence_event_hash, 16)
    except ValueError as exc:
        raise ValueError("evidence_event_hash must be hexadecimal") from exc

    decision_hash = decision_event.event_hash()
    return SSILReadinessDecisionEvent(
        event_type=EVENT_TYPE,
        evidence_event_hash=evidence_event_hash,
        decision_event_hash=decision_hash,
        decision=decision_event.decision,
        policy_version=decision_event.policy_version,
        evaluator_version=decision_event.evaluator_version,
    )


def validate_readiness_decision_event(event: SSILReadinessDecisionEvent) -> None:
    if not isinstance(event, SSILReadinessDecisionEvent):
        raise TypeError("event must be an SSILReadinessDecisionEvent instance")
    if event.event_type != EVENT_TYPE:
        raise ValueError("invalid event_type")
    for name, value in (
        ("evidence_event_hash", event.evidence_event_hash),
        ("decision_event_hash", event.decision_event_hash),
    ):
        if not isinstance(value, str) or len(value) != 64:
            raise ValueError(f"{name} must be a SHA-256 hex digest")
        try:
            int(value, 16)
        except ValueError as exc:
            raise ValueError(f"{name} must be hexadecimal") from exc
    if not isinstance(event.decision, str) or not event.decision:
        raise ValueError("decision must be non-empty")
    if not isinstance(event.policy_version, str) or not event.policy_version.strip():
        raise ValueError("policy_version must be non-empty")
    if not isinstance(event.evaluator_version, str) or not event.evaluator_version.strip():
        raise ValueError("evaluator_version must be non-empty")
