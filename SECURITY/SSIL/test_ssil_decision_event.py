"""Deterministic tests for SSIL decision-event construction."""

from __future__ import annotations

import unittest

from ssil_decision_event import build_decision_event, validate_decision_event
from ssil_engine import Decision, SSILEvidence


class SSILDecisionEventTests(unittest.TestCase):
    def clean_evidence(self) -> SSILEvidence:
        return SSILEvidence(
            crypto_verified=True,
            ledger_integrity_verified=True,
            consensus_verified=True,
            authorization_verified=True,
            security_controls_verified=True,
            recovery_controls_verified=True,
            secret_boundary_verified=True,
            evidence_complete=True,
        )

    def test_event_is_deterministic(self) -> None:
        evidence = self.clean_evidence()
        first = build_decision_event(
            evidence, policy_version="ssil-policy/1.0.0", event_sequence=7
        )
        second = build_decision_event(
            evidence, policy_version="ssil-policy/1.0.0", event_sequence=7
        )
        self.assertEqual(first.canonical_json(), second.canonical_json())
        self.assertEqual(first.event_hash(), second.event_hash())
        self.assertEqual(first.decision, Decision.ALLOW.value)

    def test_failure_decision_is_preserved(self) -> None:
        evidence = SSILEvidence(
            crypto_verified=True,
            ledger_integrity_verified=False,
            consensus_verified=True,
            authorization_verified=True,
            security_controls_verified=True,
            recovery_controls_verified=True,
            secret_boundary_verified=True,
            evidence_complete=True,
        )
        event = build_decision_event(
            evidence, policy_version="ssil-policy/1.0.0", event_sequence=8
        )
        self.assertEqual(event.decision, Decision.FAIL_CLOSED.value)
        self.assertIn("LEDGER_INTEGRITY_FAILURE", event.reason_codes)

    def test_event_validates(self) -> None:
        event = build_decision_event(
            self.clean_evidence(), policy_version="ssil-policy/1.0.0", event_sequence=9
        )
        validate_decision_event(event)

    def test_invalid_sequence_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            build_decision_event(
                self.clean_evidence(), policy_version="ssil-policy/1.0.0", event_sequence=-1
            )

    def test_empty_policy_version_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            build_decision_event(
                self.clean_evidence(), policy_version=" ", event_sequence=1
            )


if __name__ == "__main__":
    unittest.main()
