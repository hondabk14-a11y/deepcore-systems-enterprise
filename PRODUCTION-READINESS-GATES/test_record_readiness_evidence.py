"""End-to-end test for recording readiness evidence in the event ledger."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "CORE" / "event-sourced-ledger"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from ledger import EventSourcedLedger, LedgerIntegrityError  # noqa: E402
from record_readiness_evidence import record  # noqa: E402


class ReadinessEvidenceLedgerTests(unittest.TestCase):
    def test_invalid_existing_history_is_not_modified(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = root / "manifest.json"
            manifest.write_text(json.dumps({
                "schema_version": "1.0", "evidence_type": "readiness-preflight",
                "certification": "NOT_CERTIFIED", "external_evidence_required": True,
                "repository": "test", "commit_sha": "a" * 40,
                "workflow_run_id": 1, "workflow_run_attempt": 1,
                "ref": "main", "controls": {},
            }))
            ledger = root / "events.jsonl"
            original = b'{"event":"tampered","hash":"wrong"}\n'
            ledger.write_bytes(original)
            with self.assertRaises(LedgerIntegrityError):
                record(manifest, ledger)
            self.assertEqual(ledger.read_bytes(), original)

    def test_manifest_becomes_verifiable_ledger_event(self) -> None:
        manifest = {
            "schema_version": "1.0",
            "evidence_type": "readiness-preflight",
            "repository": "hondabk14-a11y/deepcore-systems-enterprise",
            "commit_sha": "a" * 40,
            "ref": "main",
            "event": "push",
            "workflow_run_id": 123456,
            "workflow_run_attempt": 1,
            "controls": {
                "infrastructure": "preflight-executed",
                "key_custody": "boundary-preflight-executed",
                "backup_restore": "synthetic-test-executed",
                "rollback": "synthetic-test-executed",
                "observability": "contract-preflight-executed",
            },
            "certification": "NOT_CERTIFIED",
            "external_evidence_required": True,
        }

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest_path = root / "manifest.json"
            ledger_path = root / "ledger.jsonl"
            manifest_path.write_text(
                json.dumps(manifest, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )

            event = record(manifest_path, ledger_path)
            ledger = EventSourcedLedger(ledger_path)
            ledger.verify()
            replayed = ledger.replay()

            self.assertEqual(len(replayed), 1)
            self.assertEqual(replayed[0], event)
            self.assertEqual(replayed[0]["event_type"], "READINESS_EVIDENCE")
            self.assertEqual(replayed[0]["commit_sha"], "a" * 40)
            self.assertEqual(replayed[0]["certification"], "NOT_CERTIFIED")
            self.assertTrue(replayed[0]["external_evidence_required"])


if __name__ == "__main__":
    unittest.main()
