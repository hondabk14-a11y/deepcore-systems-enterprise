"""Deterministic tests for SSIL decision-event construction."""

from __future__ import annotations

import sys
from pathlib import Path
import unittest

SSIL_DIR = Path(__file__).resolve().parent
LEDGER_DIR = SSIL_DIR.parent.parent / "CORE" / "event-sourced-ledger"
sys.path.insert(0, str(SSIL_DIR))
sys.path.insert(0, str(LEDGER_DIR))

from ledger import EventSourcedLedger
from ssil_decision_event import build_decision_event, validate_decision_event
from ssil_engine import Decision, SSILEvidence


class SSILDecisionEventTests(unittest.TestCase):
    def clean_evidence(self) -> SSILEvidence:
        return SSILEvidence(
            cryptography_valid=True,
            ledger_integrity_valid=True,
            consensus_valid=True,
            authorization_valid=True,
            security_controls_valid=True,
            recovery_controls_valid=True,
            secret_boundary_valid=True,
            evidence_complete=True,
        )

    def test_event_is_deterministic(self) -> None:
        evidence = self.clean_evidence()
        first = build_decision_event(evidence, policy_version="ssil-policy/1.0.0", event_sequence=7)
        second = build_decision_event(evidence, policy_version="ssil-policy/1.0.0", event_sequence=7)
        self.assertEqual(first.canonical_json(), second.canonical_json())
        self.assertEqual(first.event_hash(), second.event_hash())
        self.assertEqual(first.decision, Decision.ALLOW.value)

    def test_failure_decision_is_preserved(self) -> None:
        evidence = SSILEvidence(ledger_integrity_valid=False)
        event = build_decision_event(evidence, policy_version="ssil-policy/1.0.0", event_sequence=8)
        self.assertEqual(event.decision, Decision.FAIL_CLOSED.value)
        self.assertIn("LEDGER_INTEGRITY_FAILURE", event.reason_codes)

    def test_event_validates(self) -> None:
        event = build_decision_event(self.clean_evidence(), policy_version="ssil-policy/1.0.0", event_sequence=9)
        validate_decision_event(event)

    def test_ledger_replay_to_ssil_decision_is_deterministic(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as directory:
            ledger = EventSourcedLedger(Path(directory) / "events.jsonl")
            record = ledger.append({
                "event_type": "STATE_TRANSITION",
                "operation": "test-operation",
                "status": "VERIFIED",
            })
            self.assertTrue(ledger.verify())
            replayed = ledger.replay()
            self.assertEqual(len(replayed), 1)
            self.assertEqual(replayed[0]["hash"], record["hash"])

            evidence = self.clean_evidence()
            first = build_decision_event(
                evidence,
                policy_version="ssil-policy/1.0.0",
                event_sequence=len(replayed),
            )
            second = build_decision_event(
                evidence,
                policy_version="ssil-policy/1.0.0",
                event_sequence=len(replayed),
            )
            self.assertEqual(first.event_hash(), second.event_hash())
            self.assertEqual(first.event_sequence, 1)
            validate_decision_event(first)

    def test_invalid_sequence_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            build_decision_event(self.clean_evidence(), policy_version="ssil-policy/1.0.0", event_sequence=-1)

    def test_empty_policy_version_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            build_decision_event(self.clean_evidence(), policy_version=" ", event_sequence=1)


if __name__ == "__main__":
    unittest.main()
