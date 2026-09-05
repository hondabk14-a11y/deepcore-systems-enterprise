import tempfile
import unittest
from pathlib import Path

from checkpoint import CheckpointMismatch, checkpoint
from ledger import EventSourcedLedger
from reducer import reduce_ledger


class TestCheckpointBoundary(unittest.TestCase):
    def test_reducer_rejects_truncated_history_when_anchored(self):
        tmp = tempfile.TemporaryDirectory()
        ledger = EventSourcedLedger(Path(tmp.name) / "events.jsonl")
        try:
            ledger.append({"event": "CREDIT", "amount": 100})
            ledger.append({"event": "DEBIT", "amount": 25})
            anchor = checkpoint(ledger)

            lines = ledger.path.read_text(encoding="utf-8").splitlines()
            ledger.path.write_text(lines[0] + "\n", encoding="utf-8")

            with self.assertRaises(CheckpointMismatch):
                reduce_ledger(ledger, checkpoint_anchor=anchor)
        finally:
            tmp.cleanup()

    def test_reducer_accepts_matching_checkpoint(self):
        tmp = tempfile.TemporaryDirectory()
        ledger = EventSourcedLedger(Path(tmp.name) / "events.jsonl")
        try:
            ledger.append({"event": "CREDIT", "amount": 100})
            ledger.append({"event": "DEBIT", "amount": 25})
            anchor = checkpoint(ledger)

            state = reduce_ledger(ledger, checkpoint_anchor=anchor)
            self.assertEqual(state.balance, 75)
            self.assertEqual(state.event_count, 2)
        finally:
            tmp.cleanup()

    def test_stale_checkpoint_cannot_be_reused_after_append(self):
        tmp = tempfile.TemporaryDirectory()
        ledger = EventSourcedLedger(Path(tmp.name) / "events.jsonl")
        try:
            ledger.append({"event": "CREDIT", "amount": 100})
            anchor = checkpoint(ledger)
            ledger.append({"event": "CREDIT", "amount": 1})

            with self.assertRaises(CheckpointMismatch):
                reduce_ledger(ledger, checkpoint_anchor=anchor)
        finally:
            tmp.cleanup()

    def test_without_checkpoint_reducer_remains_backward_compatible(self):
        tmp = tempfile.TemporaryDirectory()
        ledger = EventSourcedLedger(Path(tmp.name) / "events.jsonl")
        try:
            ledger.append({"event": "CREDIT", "amount": 40})
            state = reduce_ledger(ledger)
            self.assertEqual(state.balance, 40)
            self.assertEqual(state.event_count, 1)
        finally:
            tmp.cleanup()


if __name__ == "__main__":
    unittest.main()
