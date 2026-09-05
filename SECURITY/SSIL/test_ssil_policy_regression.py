"""Regression matrix for the DeepCore SSIL policy boundary."""

from __future__ import annotations

import unittest

from ssil_engine import Decision, Reason, SSILEvidence, evaluate


class SSILPolicyRegressionTests(unittest.TestCase):
    def base(self, **overrides: object) -> SSILEvidence:
        values = {
            "cryptography_valid": True,
            "ledger_integrity_valid": True,
            "consensus_valid": True,
            "authorization_valid": True,
            "security_controls_valid": True,
            "recovery_controls_valid": True,
            "secret_boundary_valid": True,
            "evidence_complete": True,
            "high_risk_signals": (),
        }
        values.update(overrides)
        return SSILEvidence(**values)

    def assert_fail_closed(self, evidence: SSILEvidence, reason: Reason) -> None:
        result = evaluate(evidence)
        self.assertEqual(result.decision, Decision.FAIL_CLOSED)
        self.assertIn(reason, result.reasons)

    def test_clean_evidence_allows(self) -> None:
        result = evaluate(self.base())
        self.assertEqual(result.decision, Decision.ALLOW)
        self.assertEqual(result.reasons, (Reason.POLICY_SATISFIED,))

    def test_incomplete_evidence_defers(self) -> None:
        result = evaluate(self.base(evidence_complete=False))
        self.assertEqual(result.decision, Decision.DEFER)
        self.assertIn(Reason.EVIDENCE_INCOMPLETE, result.reasons)

    def test_high_risk_signal_requires_review(self) -> None:
        result = evaluate(self.base(high_risk_signals=("unusual-volume",)))
        self.assertEqual(result.decision, Decision.REVIEW)
        self.assertIn(Reason.HIGH_RISK_SIGNAL, result.reasons)

    def test_mandatory_fail_closed_matrix(self) -> None:
        cases = (
            ("crypto", "cryptography_valid", Reason.CRYPTOGRAPHIC_FAILURE),
            ("ledger", "ledger_integrity_valid", Reason.LEDGER_INTEGRITY_FAILURE),
            ("consensus", "consensus_valid", Reason.CONSENSUS_FAILURE),
            ("authorization", "authorization_valid", Reason.AUTHORIZATION_FAILURE),
            ("security", "security_controls_valid", Reason.SECURITY_CONTROL_FAILURE),
            ("recovery", "recovery_controls_valid", Reason.RECOVERY_CONTROL_FAILURE),
            ("secret-boundary", "secret_boundary_valid", Reason.SECRET_BOUNDARY_FAILURE),
        )
        for label, field, reason in cases:
            with self.subTest(control=label):
                self.assert_fail_closed(self.base(**{field: False}), reason)

    def test_fail_closed_precedes_high_risk_review(self) -> None:
        evidence = self.base(
            ledger_integrity_valid=False,
            high_risk_signals=("critical-anomaly",),
        )
        result = evaluate(evidence)
        self.assertEqual(result.decision, Decision.FAIL_CLOSED)
        self.assertIn(Reason.LEDGER_INTEGRITY_FAILURE, result.reasons)
        self.assertNotEqual(result.decision, Decision.REVIEW)

    def test_nonempty_high_risk_signals_require_review(self) -> None:
        result = evaluate(self.base(high_risk_signals=("", "  ")))
        self.assertEqual(result.decision, Decision.REVIEW)
        self.assertIn(Reason.HIGH_RISK_SIGNAL, result.reasons)


if __name__ == "__main__":
    unittest.main()
