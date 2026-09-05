"""End-to-end tests for the readiness evidence -> SSIL audit chain."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "CORE" / "event-sourced-ledger"))
sys.path.insert(0, str(ROOT / "PRODUCTION-READINESS-GATES"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from ledger import EventSourcedLedger, LedgerIntegrityError  # noqa: E402
from readiness_evidence_event import build_readiness_evidence_event  # noqa: E402
from ssil_decision_event import build_decision_event  # noqa: E402
from ssil_engine import SSILEvidence  # noqa: E402
from ssil_readiness_decision_event import build_readiness_decision_event  # noqa: E402


class SSILReadinessAuditChainTests(unittest.TestCase):
    def _manifest(self) -> dict[str, object]:
        return {
            "schema_version": "1.0",
            "evidence_type": "DEEP_CORE_READINESS_EVIDENCE",
            "repository": "hondabk14-a11y/deepcore-systems-enterprise",
            "commit_sha": "a" * 40,
            "ref": "refs/heads/main",
            "event": "workflow_dispatch",
            "workflow_run_id": 123456,
            "workflow_run_attempt": 1,
            "controls": {
                "infrastructure": "PENDING_EXTERNAL_EVIDENCE",
                "key_custody": "PENDING_EXTERNAL_EVIDENCE",
                "backup_restore": "PENDING_EXTERNAL_EVIDENCE",
                "rollback": "PENDING_EXTERNAL_EVIDENCE",
                "observability": "PENDING_EXTERNAL_EVIDENCE",
            },
            "certification": "NOT_CERTIFIED",
            "external_evidence_required": True,
        }

    def _chain(self) -> tuple[dict[str, object], dict[str, object], dict[str, object], dict[str, object]]:
        manifest = self._manifest()
        evidence = build_readiness_evidence_event(manifest)
        decision = build_decision_event(
            SSILEvidence(), policy_version="ssil-policy/1.0.0", event_sequence=1
        )
        link = build_readiness_decision_event(evidence.event_hash(), decision)
        return manifest, evidence.to_mapping(), decision.to_mapping(), link.to_mapping()

    def test_complete_chain_appends_verifies_and_replays(self) -> None:
        _, evidence, decision, link = self._chain()
        with tempfile.TemporaryDirectory() as temp_dir:
            ledger = EventSourcedLedger(Path(temp_dir) / "audit.jsonl")
            records = [ledger.append(evidence), ledger.append(decision), ledger.append(link)]
            self.assertTrue(ledger.verify())
            replayed = ledger.replay()

        self.assertEqual(len(replayed), 3)
        self.assertEqual(replayed[1]["event_type"], "SSIL_DECISION")
        self.assertEqual(replayed[2]["event_type"], "SSIL_READINESS_DECISION")
        self.assertEqual(replayed[2]["evidence_event_hash"], evidence["event_hash"])
        self.assertEqual(replayed[2]["decision_event_hash"], decision["event_hash"])
        self.assertEqual(records[-1], replayed[-1])

    def test_cross_event_hash_links_are_deterministic(self) -> None:
        _, evidence_a, decision_a, link_a = self._chain()
        _, evidence_b, decision_b, link_b = self._chain()
        self.assertEqual(evidence_a, evidence_b)
        self.assertEqual(decision_a, decision_b)
        self.assertEqual(link_a, link_b)

    def test_tampering_any_chain_record_invalidates_ledger(self) -> None:
        _, evidence, decision, link = self._chain()
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "audit.jsonl"
            ledger = EventSourcedLedger(path)
            ledger.append(evidence)
            ledger.append(decision)
            ledger.append(link)
            lines = path.read_text(encoding="utf-8").splitlines()
            tampered = json.loads(lines[1])
            tampered["decision"] = "FAIL_CLOSED"
            lines[1] = json.dumps(tampered, sort_keys=True, separators=(",", ":"))
            path.write_text("\n".join(lines) + "\n", encoding="utf-8")

            self.assertFalse(ledger.verify())
            with self.assertRaises(LedgerIntegrityError):
                ledger.replay()

    def test_chain_order_is_authoritative(self) -> None:
        _, evidence, decision, link = self._chain()
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "audit.jsonl"
            ledger = EventSourcedLedger(path)
            ledger.append(evidence)
            ledger.append(decision)
            ledger.append(link)
            lines = path.read_text(encoding="utf-8").splitlines()
            lines[0], lines[1] = lines[1], lines[0]
            path.write_text("\n".join(lines) + "\n", encoding="utf-8")
            self.assertFalse(ledger.verify())


if __name__ == "__main__":
    unittest.main()
