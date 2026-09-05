import tempfile
import unittest
from pathlib import Path

from ledger import EventSourcedLedger
from reducer import LedgerState, reduce_ledger


class TestEndToEndReplay(unittest.TestCase):
    def test_persisted_event_stream_reduces_to_expected_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger = EventSourcedLedger(Path(tmp) / "events.jsonl")
            ledger.append({"event": "CREDIT", "amount": 100})
            ledger.append({"event": "DEBIT", "amount": 35})
            ledger.append({"event": "CREDIT", "amount": 10})

            self.assertTrue(ledger.verify())
            state = reduce_ledger(ledger)

            self.assertEqual(state, LedgerState(balance=75, event_count=3))

    def test_corrupted_persisted_stream_cannot_be_reduced(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "events.jsonl"
            ledger = EventSourcedLedger(path)
            ledger.append({"event": "CREDIT", "amount": 50})
            path.write_text(path.read_text() + "{not-json}\n")

            with self.assertRaises(Exception):
                reduce_ledger(ledger)


if __name__ == "__main__":
    unittest.main()
