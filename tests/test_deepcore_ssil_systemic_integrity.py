from SECURITY.SSIL.ssil_systemic_integrity import (
    IntegrityDecision,
    IntegrityEvidence,
    IntegrityReason,
    evaluate,
    evaluate_mapping,
)


def test_clean_evidence_allows():
    decision, reasons = evaluate(IntegrityEvidence())
    assert decision is IntegrityDecision.ALLOW
    assert reasons == (IntegrityReason.SATISFIED,)


def test_security_failure_is_fail_closed():
    evidence = IntegrityEvidence(cryptography_valid=False, consensus_valid=False)
    decision, reasons = evaluate(evidence)
    assert decision is IntegrityDecision.FAIL_CLOSED
    assert reasons == (IntegrityReason.CRYPTOGRAPHY, IntegrityReason.CONSENSUS)


def test_incomplete_evidence_defers():
    decision, reasons = evaluate(IntegrityEvidence(evidence_complete=False))
    assert decision is IntegrityDecision.DEFER
    assert reasons == (IntegrityReason.INCOMPLETE,)


def test_high_risk_evidence_requires_review():
    decision, reasons = evaluate(IntegrityEvidence(high_risk_signals=("fee_spike",)))
    assert decision is IntegrityDecision.REVIEW
    assert reasons == (IntegrityReason.HIGH_RISK,)


def test_unknown_mapping_fails_closed():
    decision, reasons = evaluate_mapping({"unexpected": True})
    assert decision is IntegrityDecision.FAIL_CLOSED
    assert reasons == (IntegrityReason.AUTHORIZATION,)


def test_boolean_type_confusion_fails_closed():
    decision, reasons = evaluate_mapping({"ledger_valid": 1})
    assert decision is IntegrityDecision.FAIL_CLOSED
    assert reasons == (IntegrityReason.AUTHORIZATION,)
