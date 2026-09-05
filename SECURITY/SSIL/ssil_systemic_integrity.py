"""DeepCore SSIL systemic integrity decision boundary.

Deterministic reference implementation. This module evaluates supplied
security/integrity evidence and emits a machine-readable decision. It does
not access secrets, mutate ledger state, or perform external actions.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Mapping


class IntegrityDecision(str, Enum):
    ALLOW = "ALLOW"
    REVIEW = "REVIEW"
    DEFER = "DEFER"
    FAIL_CLOSED = "FAIL_CLOSED"


class IntegrityReason(str, Enum):
    CRYPTOGRAPHY = "CRYPTOGRAPHY"
    LEDGER = "LEDGER"
    CONSENSUS = "CONSENSUS"
    AUTHORIZATION = "AUTHORIZATION"
    RECOVERY = "RECOVERY"
    TRANSPORT = "TRANSPORT"
    HIGH_RISK = "HIGH_RISK"
    INCOMPLETE = "INCOMPLETE"
    SATISFIED = "SATISFIED"


@dataclass(frozen=True)
class IntegrityEvidence:
    cryptography_valid: bool = True
    ledger_valid: bool = True
    consensus_valid: bool = True
    authorization_valid: bool = True
    recovery_valid: bool = True
    transport_valid: bool = True
    evidence_complete: bool = True
    high_risk_signals: tuple[str, ...] = ()


_FIELDS = (
    "cryptography_valid",
    "ledger_valid",
    "consensus_valid",
    "authorization_valid",
    "recovery_valid",
    "transport_valid",
    "evidence_complete",
)

_FAILURES = (
    ("cryptography_valid", IntegrityReason.CRYPTOGRAPHY),
    ("ledger_valid", IntegrityReason.LEDGER),
    ("consensus_valid", IntegrityReason.CONSENSUS),
    ("authorization_valid", IntegrityReason.AUTHORIZATION),
    ("recovery_valid", IntegrityReason.RECOVERY),
    ("transport_valid", IntegrityReason.TRANSPORT),
)


def evaluate(evidence: IntegrityEvidence) -> tuple[IntegrityDecision, tuple[IntegrityReason, ...]]:
    """Evaluate SSIL evidence with deterministic fail-closed precedence."""
    if not isinstance(evidence, IntegrityEvidence):
        raise TypeError("evidence must be an IntegrityEvidence instance")

    for field_name in _FIELDS:
        if not isinstance(getattr(evidence, field_name), bool):
            raise TypeError(f"{field_name} must be boolean")
    if any(not isinstance(item, str) for item in evidence.high_risk_signals):
        raise TypeError("high_risk_signals must contain strings")

    failures = tuple(reason for field_name, reason in _FAILURES if not getattr(evidence, field_name))
    if failures:
        return IntegrityDecision.FAIL_CLOSED, failures
    if not evidence.evidence_complete:
        return IntegrityDecision.DEFER, (IntegrityReason.INCOMPLETE,)
    if evidence.high_risk_signals:
        return IntegrityDecision.REVIEW, (IntegrityReason.HIGH_RISK,)
    return IntegrityDecision.ALLOW, (IntegrityReason.SATISFIED,)


def evaluate_mapping(values: Mapping[str, object]) -> tuple[IntegrityDecision, tuple[IntegrityReason, ...]]:
    """Safely evaluate mapping input while rejecting unknown/type-confused data."""
    if not isinstance(values, Mapping):
        raise TypeError("values must be a mapping")
    allowed = set(IntegrityEvidence.__dataclass_fields__)
    if set(values) - allowed:
        return IntegrityDecision.FAIL_CLOSED, (IntegrityReason.AUTHORIZATION,)
    normalized = dict(values)
    if "high_risk_signals" in normalized:
        signals = normalized["high_risk_signals"]
        if not isinstance(signals, (tuple, list)) or any(not isinstance(x, str) for x in signals):
            return IntegrityDecision.FAIL_CLOSED, (IntegrityReason.AUTHORIZATION,)
        normalized["high_risk_signals"] = tuple(signals)
    try:
        return evaluate(IntegrityEvidence(**normalized))
    except (TypeError, ValueError):
        return IntegrityDecision.FAIL_CLOSED, (IntegrityReason.AUTHORIZATION,)
