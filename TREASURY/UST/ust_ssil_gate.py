"""SSIL gate for the DeepCore UST-0001 settlement reference model."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from SECURITY.SSIL.ssil_systemic_integrity import (
    IntegrityDecision,
    IntegrityEvidence,
    evaluate,
)


class GateAction(str, Enum):
    ACCEPT = "ACCEPT"
    HOLD = "HOLD"
    REJECT = "REJECT"


@dataclass(frozen=True)
class USTGateResult:
    action: GateAction
    decision: IntegrityDecision
    reasons: tuple[str, ...]


def evaluate_ust_settlement(evidence: IntegrityEvidence) -> USTGateResult:
    """Map SSIL's deterministic decision into a settlement control action.

    SSIL does not authorize funds or mutate the treasury ledger. This gate
    only determines whether the reference settlement workflow may proceed.
    """
    decision, reasons = evaluate(evidence)
    if decision is IntegrityDecision.ALLOW:
        action = GateAction.ACCEPT
    elif decision in (IntegrityDecision.REVIEW, IntegrityDecision.DEFER):
        action = GateAction.HOLD
    else:
        action = GateAction.REJECT
    return USTGateResult(action, decision, tuple(reason.value for reason in reasons))
