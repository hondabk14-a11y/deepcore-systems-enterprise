import tempfile
import unittest
from pathlib import Path

from invariants import InvariantViolation, verify_invariants
from ledger import EventSourcedLedger


class TestLedgerInvariants(unittest.TestCase):
    def test_valid_chain_and_domain_events(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger = EventSourcedLedger(Path(tmp) / "events.jsonl")
            ledger.append({"event": "CREDIT", "amount": 100})
            ledger.append({"event": "DEBIT", "amount": 25})
            verify_invariants(ledger.replay())

    def test_broken_previous_hash_is_rejected(self):
        records = [
            {"event": "CREDIT", "amount": 1, "previous_hash": "WRONG", "hash": "x"}
        ]
        with self.assertRaises(InvariantViolation):
            verify_invariants(records)

    def test_unsupported_event_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger = EventSourcedLedger(Path(tmp) / "events.jsonl")
            ledger.append({"event": "CREDIT", "amount": 1})
            records = ledger.replay()
            records.append({"event": "UNKNOWN", "amount": 1})
            with self.assertRaises(InvariantViolation):
                verify_invariants(records)

    def test_negative_amount_is_rejected(self):
        with self.assertRaises(InvariantViolation):
            verify_invariants([{"event": "DEBIT", "amount": -1}])

    def test_boolean_amount_is_rejected(self):
        with self.assertRaises(InvariantViolation):
            verify_invariants([{"event": "CREDIT", "amount": True}])


if __name__ == "__main__":
    unittest.main()
