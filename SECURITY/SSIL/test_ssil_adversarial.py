"""Adversarial tests for SSIL input and decision-event integrity boundaries."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SSIL_DIR = os.path.join(ROOT, "SECURITY", "SSIL")
if SSIL_DIR not in sys.path:
    sys.path.insert(0, SSIL_DIR)

from ssil_decision_event import (  # noqa: E402
    SSILDecisionEvent,
    build_decision_event,
    validate_decision_event,
)
from ssil_engine import Decision, Reason, SSILEvidence, evaluate, evaluate_mapping  # noqa: E402


class SSILAdversarialTests(unittest.TestCase):
    def test_unknown_mapping_field_fails_closed(self) -> None:
        result = evaluate_mapping({"unexpected": True})
        self.assertEqual(result.decision, Decision.FAIL_CLOSED)
        self.assertIn(Reason.SECURITY_CONTROL_FAILURE, result.reasons)

    def test_string_boolean_type_confusion_fails_closed(self) -> None:
        result = evaluate_mapping({"ledger_integrity_valid": "false"})
        self.assertEqual(result.decision, Decision.FAIL_CLOSED)
        self.assertIn(Reason.SECURITY_CONTROL_FAILURE, result.reasons)

    def test_numeric_boolean_type_confusion_fails_closed(self) -> None:
        result = evaluate_mapping({"consensus_valid": 1})
        self.assertEqual(result.decision, Decision.FAIL_CLOSED)
        self.assertIn(Reason.SECURITY_CONTROL_FAILURE, result.reasons)

    def test_malformed_risk_signal_container_fails_closed(self) -> None:
        result = evaluate_mapping({"high_risk_signals": "risk"})
        self.assertEqual(result.decision, Decision.FAIL_CLOSED)
        self.assertIn(Reason.SECURITY_CONTROL_FAILURE, result.reasons)

    def test_malformed_risk_signal_entry_fails_closed(self) -> None:
        result = evaluate_mapping({"high_risk_signals": ["risk", 7]})
        self.assertEqual(result.decision, Decision.FAIL_CLOSED)
        self.assertIn(Reason.SECURITY_CONTROL_FAILURE, result.reasons)

    def test_direct_evaluation_rejects_wrong_evidence_type(self) -> None:
        with self.assertRaises(TypeError):
            evaluate({"ledger_integrity_valid": False})  # type: ignore[arg-type]

    def test_contradictory_controls_fail_closed_before_review(self) -> None:
        evidence = SSILEvidence(ledger_integrity_valid=False, high_risk_signals=("risk",))
        result = evaluate(evidence)
        self.assertEqual(result.decision, Decision.FAIL_CLOSED)
        self.assertIn(Reason.LEDGER_INTEGRITY_FAILURE, result.reasons)
        self.assertNotEqual(result.decision, Decision.REVIEW)

    def test_negative_sequence_rejected(self) -> None:
        with self.assertRaises(ValueError):
            build_decision_event(SSILEvidence(), policy_version="ssil/1", event_sequence=-1)

    def test_boolean_sequence_rejected(self) -> None:
        with self.assertRaises(TypeError):
            build_decision_event(SSILEvidence(), policy_version="ssil/1", event_sequence=True)  # type: ignore[arg-type]

    def test_corrupted_event_fields_are_rejected(self) -> None:
        event = build_decision_event(SSILEvidence(), policy_version="ssil/1", event_sequence=0)
        validate_decision_event(event)

        corrupted = replace(event, event_type="CORRUPTED")
        with self.assertRaises(ValueError):
            validate_decision_event(corrupted)
        self.assertNotEqual(event.event_hash(), corrupted.event_hash())

        corrupted = replace(event, evidence_hash="0" * 63 + "g")
        with self.assertRaises(ValueError):
            validate_decision_event(corrupted)
        self.assertNotEqual(event.event_hash(), corrupted.event_hash())

        corrupted = replace(event, decision="ALLOW")
        self.assertEqual(corrupted.decision, "ALLOW")
        self.assertNotEqual(event.event_hash(), corrupted.event_hash())

    def test_reason_code_tampering_changes_event_hash(self) -> None:
        event = build_decision_event(SSILEvidence(), policy_version="ssil/1", event_sequence=1)
        tampered = replace(event, reason_codes=("LEDGER_INTEGRITY_FAILURE",))
        self.assertNotEqual(event.event_hash(), tampered.event_hash())
        validate_decision_event(tampered)

    def test_frozen_decision_event_cannot_be_mutated(self) -> None:
        event = build_decision_event(SSILEvidence(), policy_version="ssil/1", event_sequence=2)
        with self.assertRaises(FrozenInstanceError):
            event.decision = "FAIL_CLOSED"  # type: ignore[misc]

    def test_event_round_trip_mapping_is_stable(self) -> None:
        event = build_decision_event(
            SSILEvidence(high_risk_signals=("network-anomaly",)),
            policy_version="ssil/1",
            event_sequence=3,
            evaluator_version="ssil-engine/test",
        )
        clone = SSILDecisionEvent(
            event_type=event.event_type,
            policy_version=event.policy_version,
            evidence_hash=event.evidence_hash,
            event_sequence=event.event_sequence,
            decision=event.decision,
            reason_codes=tuple(event.to_mapping()["reason_codes"]),
            evaluator_version=event.evaluator_version,
        )
        validate_decision_event(clone)
        self.assertEqual(event.to_mapping(), clone.to_mapping())
        self.assertEqual(event.event_hash(), clone.event_hash())


if __name__ == "__main__":
    unittest.main()
