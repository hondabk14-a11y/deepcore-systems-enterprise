from SECURITY.SSIL.ssil_systemic_integrity import IntegrityEvidence
from TREASURY.UST.ust_ssil_gate import GateAction, evaluate_ust_settlement


def test_clean_settlement_is_accepted():
    result = evaluate_ust_settlement(IntegrityEvidence())
    assert result.action is GateAction.ACCEPT
    assert result.decision.value == "ALLOW"


def test_high_risk_settlement_is_held():
    result = evaluate_ust_settlement(IntegrityEvidence(high_risk_signals=("anomaly",)))
    assert result.action is GateAction.HOLD
    assert result.decision.value == "REVIEW"


def test_incomplete_settlement_is_held():
    result = evaluate_ust_settlement(IntegrityEvidence(evidence_complete=False))
    assert result.action is GateAction.HOLD
    assert result.decision.value == "DEFER"


def test_integrity_failure_rejects():
    result = evaluate_ust_settlement(IntegrityEvidence(ledger_valid=False))
    assert result.action is GateAction.REJECT
    assert result.decision.value == "FAIL_CLOSED"
