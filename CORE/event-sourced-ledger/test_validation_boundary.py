import tempfile
import unittest
from pathlib import Path

from invariants import InvariantViolation
from ledger import EventSourcedLedger
from reducer import LedgerState, reduce_ledger


class ValidationBoundaryTests(unittest.TestCase):
    def test_replay_validator_runs_after_structural_verification(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger = EventSourcedLedger(Path(tmp) / "events.jsonl")
            ledger.append({"event": "CREDIT", "amount": 25})
            seen = []

            def validator(records):
                seen.extend(records)

            records = ledger.replay(validator=validator)
            self.assertEqual(records, seen)
            self.assertEqual(records[0]["event"], "CREDIT")

    def test_reducer_rejects_structurally_valid_unknown_event(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger = EventSourcedLedger(Path(tmp) / "events.jsonl")
            ledger.append({"event": "UNKNOWN", "amount": 25})
            with self.assertRaises(InvariantViolation):
                reduce_ledger(ledger)

    def test_reducer_accepts_validated_domain_history(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger = EventSourcedLedger(Path(tmp) / "events.jsonl")
            ledger.append({"event": "CREDIT", "amount": 100})
            ledger.append({"event": "DEBIT", "amount": 40})
            self.assertEqual(reduce_ledger(ledger), LedgerState(balance=60, event_count=2))


if __name__ == "__main__":
    unittest.main()
