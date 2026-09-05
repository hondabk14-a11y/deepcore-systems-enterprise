import tempfile
import unittest
from pathlib import Path

from ledger import EventSourcedLedger, LedgerIntegrityError


class EventSourcedLedgerTests(unittest.TestCase):
    def test_append_and_verify(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger = EventSourcedLedger(Path(tmp) / "events.jsonl")
            first = ledger.append({"event": "A", "value": 1})
            second = ledger.append({"event": "B", "value": 2})
            self.assertEqual(first["previous_hash"], "GENESIS")
            self.assertEqual(second["previous_hash"], first["hash"])
            self.assertTrue(ledger.verify())

    def test_tampering_is_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "events.jsonl"
            ledger = EventSourcedLedger(path)
            ledger.append({"event": "A", "value": 1})
            path.write_text(path.read_text(encoding="utf-8").replace("\"value\":1", "\"value\":9"), encoding="utf-8")
            self.assertFalse(ledger.verify())

    def test_invalid_ledger_cannot_replay(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "events.jsonl"
            ledger = EventSourcedLedger(path)
            ledger.append({"event": "A"})
            path.write_text(path.read_text(encoding="utf-8").replace("GENESIS", "BROKEN"), encoding="utf-8")
            with self.assertRaises(LedgerIntegrityError):
                ledger.replay()

    def test_caller_cannot_override_chain_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger = EventSourcedLedger(Path(tmp) / "events.jsonl")
            with self.assertRaises(LedgerIntegrityError):
                ledger.append({"event": "A", "hash": "fake"})


if __name__ == "__main__":
    unittest.main()
