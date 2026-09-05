import json
import tempfile
import unittest
from pathlib import Path

from ledger import EventSourcedLedger, LedgerIntegrityError


class TestReplayCompleteness(unittest.TestCase):
    def _ledger(self):
        tmp = tempfile.TemporaryDirectory()
        ledger = EventSourcedLedger(Path(tmp.name) / "events.jsonl")
        ledger.append({"event": "CREDIT", "amount": 100})
        ledger.append({"event": "DEBIT", "amount": 25})
        ledger.append({"event": "CREDIT", "amount": 7})
        return tmp, ledger

    def _write_records(self, ledger, records):
        ledger.path.write_text(
            "".join(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n" for record in records),
            encoding="utf-8",
        )

    def test_deleting_intermediate_record_breaks_chain(self):
        tmp, ledger = self._ledger()
        try:
            records = [json.loads(line) for line in ledger.path.read_text().splitlines()]
            del records[1]
            self._write_records(ledger, records)
            with self.assertRaises(LedgerIntegrityError):
                ledger.replay()
        finally:
            tmp.cleanup()

    def test_reordering_records_breaks_chain(self):
        tmp, ledger = self._ledger()
        try:
            records = [json.loads(line) for line in ledger.path.read_text().splitlines()]
            records[1], records[2] = records[2], records[1]
            self._write_records(ledger, records)
            with self.assertRaises(LedgerIntegrityError):
                ledger.replay()
        finally:
            tmp.cleanup()

    def test_duplicate_record_breaks_chain(self):
        tmp, ledger = self._ledger()
        try:
            records = [json.loads(line) for line in ledger.path.read_text().splitlines()]
            records.insert(1, dict(records[0]))
            self._write_records(ledger, records)
            with self.assertRaises(LedgerIntegrityError):
                ledger.replay()
        finally:
            tmp.cleanup()

    def test_modified_final_record_breaks_hash_commitment(self):
        tmp, ledger = self._ledger()
        try:
            records = [json.loads(line) for line in ledger.path.read_text().splitlines()]
            records[-1]["amount"] = 8
            self._write_records(ledger, records)
            with self.assertRaises(LedgerIntegrityError):
                ledger.replay()
        finally:
            tmp.cleanup()


if __name__ == "__main__":
    unittest.main()
