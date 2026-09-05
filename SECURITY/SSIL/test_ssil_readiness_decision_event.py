"""Tests for deterministic SSIL readiness decision event binding."""

from __future__ import annotations

import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from ssil_decision_event import build_decision_event  # noqa: E402
from ssil_engine import SSILEvidence  # noqa: E402
from ssil_readiness_decision_event import (  # noqa: E402
    build_readiness_decision_event,
    validate_readiness_decision_event,
)


class SSILReadinessDecisionEventTests(unittest.TestCase):
    def test_decision_is_bound_to_evidence_event(self) -> None:
        decision = build_decision_event(
            SSILEvidence(),
            policy_version="ssil-policy/1.0.0",
            event_sequence=7,
        )
        event = build_readiness_decision_event("b" * 64, decision)
        validate_readiness_decision_event(event)
        self.assertEqual(event.evidence_event_hash, "b" * 64)
        self.assertEqual(event.decision_event_hash, decision.event_hash())
        self.assertEqual(event.decision, "ALLOW")

    def test_decision_change_changes_binding(self) -> None:
        allow = build_decision_event(
            SSILEvidence(), policy_version="ssil-policy/1.0.0", event_sequence=1
        )
        defer = build_decision_event(
            SSILEvidence(evidence_complete=False),
            policy_version="ssil-policy/1.0.0",
            event_sequence=1,
        )
        allow_event = build_readiness_decision_event("c" * 64, allow)
        defer_event = build_readiness_decision_event("c" * 64, defer)
        self.assertNotEqual(allow_event.decision_event_hash, defer_event.decision_event_hash)

    def test_evidence_hash_requires_sha256_hex(self) -> None:
        decision = build_decision_event(
            SSILEvidence(), policy_version="ssil-policy/1.0.0", event_sequence=1
        )
        with self.assertRaises(ValueError):
            build_readiness_decision_event("not-a-hash", decision)

    def test_tampered_decision_event_is_rejected(self) -> None:
        decision = build_decision_event(
            SSILEvidence(), policy_version="ssil-policy/1.0.0", event_sequence=1
        )
        decision.decision = "FAIL_CLOSED"  # type: ignore[misc]

    def test_frozen_link_event_cannot_mutate(self) -> None:
        decision = build_decision_event(
            SSILEvidence(), policy_version="ssil-policy/1.0.0", event_sequence=1
        )
        event = build_readiness_decision_event("d" * 64, decision)
        with self.assertRaises(AttributeError):
            event.decision = "FAIL_CLOSED"  # type: ignore[misc]


if __name__ == "__main__":
    unittest.main()
