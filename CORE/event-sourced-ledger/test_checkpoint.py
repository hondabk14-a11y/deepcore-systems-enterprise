import tempfile
import unittest
from pathlib import Path

from checkpoint import CheckpointMismatch, checkpoint, verify_checkpoint
from ledger import EventSourcedLedger


class TestCheckpoint(unittest.TestCase):
    def test_checkpoint_detects_truncated_valid_prefix(self):
        tmp = tempfile.TemporaryDirectory()
        ledger = EventSourcedLedger(Path(tmp.name) / "events.jsonl")
        try:
            ledger.append({"event": "CREDIT", "amount": 100})
            ledger.append({"event": "DEBIT", "amount": 25})
            expected = checkpoint(ledger, ledger_id="ledger-A")

            lines = ledger.path.read_text(encoding="utf-8").splitlines()
            ledger.path.write_text(lines[0] + "\n", encoding="utf-8")

            with self.assertRaises(CheckpointMismatch):
                verify_checkpoint(ledger, expected)
        finally:
            tmp.cleanup()

    def test_checkpoint_accepts_unchanged_history(self):
        tmp = tempfile.TemporaryDirectory()
        ledger = EventSourcedLedger(Path(tmp.name) / "events.jsonl")
        try:
            ledger.append({"event": "CREDIT", "amount": 100})
            expected = checkpoint(ledger, ledger_id="ledger-A")
            verify_checkpoint(ledger, expected)
            self.assertEqual(expected.ledger_id, "ledger-A")
            self.assertEqual(expected.sequence, 1)
        finally:
            tmp.cleanup()

    def test_checkpoint_detects_appended_record(self):
        tmp = tempfile.TemporaryDirectory()
        ledger = EventSourcedLedger(Path(tmp.name) / "events.jsonl")
        try:
            ledger.append({"event": "CREDIT", "amount": 100})
            expected = checkpoint(ledger, ledger_id="ledger-A")
            ledger.append({"event": "CREDIT", "amount": 1})
            with self.assertRaises(CheckpointMismatch):
                verify_checkpoint(ledger, expected)
        finally:
            tmp.cleanup()

    def test_checkpoint_binds_expected_ledger_identity(self):
        tmp = tempfile.TemporaryDirectory()
        ledger = EventSourcedLedger(Path(tmp.name) / "events.jsonl")
        try:
            ledger.append({"event": "CREDIT", "amount": 100})
            expected = checkpoint(ledger, ledger_id="ledger-A")
            wrong_identity = expected.__class__(
                ledger_id="ledger-B",
                sequence=expected.sequence,
                head_hash=expected.head_hash,
                event_count=expected.event_count,
            )
            with self.assertRaises(CheckpointMismatch):
                verify_checkpoint(ledger, wrong_identity)
        finally:
            tmp.cleanup()


if __name__ == "__main__":
    unittest.main()
