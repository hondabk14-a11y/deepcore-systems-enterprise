import tempfile
import unittest
from pathlib import Path

from invariants import InvariantViolation, verify_event_chain, verify_invariants
from ledger import EventSourcedLedger, LedgerIntegrityError, GENESIS, event_hash


class TestPropertyInvariants(unittest.TestCase):
    def test_valid_multi_record_chain(self):
        ledger = EventSourcedLedger(Path(tempfile.mktemp()))
        ledger.append({"event": "CREDIT", "amount": 10})
        ledger.append({"event": "DEBIT", "amount": 3})
        self.assertTrue(ledger.verify())
        verify_invariants(ledger.replay())

    def test_middle_record_tampering_breaks_commitment(self):
        records = [
            {"event": "CREDIT", "amount": 10, "previous_hash": GENESIS},
        ]
        records[0]["hash"] = event_hash({k: v for k, v in records[0].items() if k != "hash"})
        records.append({"event": "DEBIT", "amount": 3, "previous_hash": records[0]["hash"]})
        records[1]["hash"] = event_hash({k: v for k, v in records[1].items() if k != "hash"})
        records[0]["amount"] = 11
        with self.assertRaises(InvariantViolation):
            verify_event_chain(records)

    def test_broken_previous_hash_is_rejected(self):
        record = {"event": "CREDIT", "amount": 10, "previous_hash": "WRONG"}
        record["hash"] = event_hash({k: v for k, v in record.items() if k != "hash"})
        with self.assertRaises(InvariantViolation):
            verify_event_chain([record])

    def test_missing_hash_is_rejected(self):
        with self.assertRaises(InvariantViolation):
            verify_event_chain([{"event": "CREDIT", "amount": 10, "previous_hash": GENESIS}])

    def test_malformed_persisted_json_blocks_verification(self):
        path = Path(tempfile.mktemp())
        EventSourcedLedger(path).append({"event": "CREDIT", "amount": 10})
        with path.open("a", encoding="utf-8") as stream:
            stream.write("not-json\n")
        with self.assertRaises(LedgerIntegrityError):
            EventSourcedLedger(path).verify()

    def test_domain_invariant_rejects_unknown_event(self):
        record = {"event": "UNKNOWN", "amount": 1, "previous_hash": GENESIS}
        record["hash"] = event_hash({k: v for k, v in record.items() if k != "hash"})
        with self.assertRaises(InvariantViolation):
            verify_invariants([record])

    def test_domain_invariant_rejects_boolean_amount(self):
        record = {"event": "CREDIT", "amount": True, "previous_hash": GENESIS}
        record["hash"] = event_hash({k: v for k, v in record.items() if k != "hash"})
        with self.assertRaises(InvariantViolation):
            verify_invariants([record])


if __name__ == "__main__":
    unittest.main()
