import unittest

from ssil_engine import Decision, Reason, SSILEvidence, evaluate, evaluate_mapping


class SSILEngineTests(unittest.TestCase):
    def test_clean_evidence_allows(self):
        result = evaluate(SSILEvidence())
        self.assertEqual(result.decision, Decision.ALLOW)
        self.assertEqual(result.reasons, (Reason.POLICY_SATISFIED,))

    def test_incomplete_evidence_defers(self):
        result = evaluate(SSILEvidence(evidence_complete=False))
        self.assertEqual(result.decision, Decision.DEFER)
        self.assertEqual(result.reasons, (Reason.EVIDENCE_INCOMPLETE,))

    def test_high_risk_signal_requires_review(self):
        result = evaluate(SSILEvidence(high_risk_signals=("liquidity_spike",)))
        self.assertEqual(result.decision, Decision.REVIEW)
        self.assertEqual(result.reasons, (Reason.HIGH_RISK_SIGNAL,))

    def test_integrity_failure_fails_closed(self):
        result = evaluate(SSILEvidence(ledger_integrity_valid=False))
        self.assertEqual(result.decision, Decision.FAIL_CLOSED)
        self.assertIn(Reason.LEDGER_INTEGRITY_FAILURE, result.reasons)

    def test_multiple_mandatory_failures_remain_fail_closed(self):
        result = evaluate(
            SSILEvidence(
                cryptography_valid=False,
                authorization_valid=False,
                secret_boundary_valid=False,
            )
        )
        self.assertEqual(result.decision, Decision.FAIL_CLOSED)
        self.assertEqual(
            result.reasons,
            (
                Reason.CRYPTOGRAPHIC_FAILURE,
                Reason.AUTHORIZATION_FAILURE,
                Reason.SECRET_BOUNDARY_FAILURE,
            ),
        )

    def test_unknown_mapping_field_fails_closed(self):
        result = evaluate_mapping({"not_a_policy_field": True})
        self.assertEqual(result.decision, Decision.FAIL_CLOSED)


if __name__ == "__main__":
    unittest.main()
