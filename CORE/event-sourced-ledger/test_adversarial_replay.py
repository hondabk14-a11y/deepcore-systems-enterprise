import json
import tempfile
import unittest
from pathlib import Path

from ledger import EventSourcedLedger, LedgerIntegrityError
from reducer import reduce_ledger


class TestAdversarialReplay(unittest.TestCase):
    def _ledger_with_events(self, events):
        tmp = tempfile.TemporaryDirectory()
        ledger = EventSourcedLedger(Path(tmp.name) / "events.jsonl")
        for event in events:
            ledger.append(event)
        return tmp, ledger

    def test_tampered_middle_record_cannot_replay(self):
        tmp, ledger = self._ledger_with_events(
            [
                {"event": "CREDIT", "amount": 100},
                {"event": "DEBIT", "amount": 25},
                {"event": "CREDIT", "amount": 7},
            ]
        )
        try:
            records = [json.loads(line) for line in ledger.path.read_text().splitlines()]
            records[1]["amount"] = 99
            ledger.path.write_text("".join(json.dumps(r, sort_keys=True, separators=(",", ":")) + "\n" for r in records))

            with self.assertRaises(LedgerIntegrityError):
                ledger.replay()
            with self.assertRaises(LedgerIntegrityError):
                reduce_ledger(ledger)
        finally:
            tmp.cleanup()

    def test_truncated_history_cannot_replay_as_original_state(self):
        tmp, ledger = self._ledger_with_events(
            [
                {"event": "CREDIT", "amount": 100},
                {"event": "DEBIT", "amount": 25},
                {"event": "CREDIT", "amount": 7},
            ]
        )
        try:
            records = ledger.path.read_text().splitlines()
            ledger.path.write_text(records[0] + "\n")
            state = reduce_ledger(ledger)
            self.assertEqual(state.event_count, 1)
            self.assertEqual(state.balance, 100)
            self.assertNotEqual(state.balance, 82)
        finally:
            tmp.cleanup()

    def test_appended_garbage_after_valid_history_is_rejected(self):
        tmp, ledger = self._ledger_with_events([{"event": "CREDIT", "amount": 10}])
        try:
            ledger.path.write_text(ledger.path.read_text() + "garbage\n")
            with self.assertRaises(LedgerIntegrityError):
                ledger.replay()
        finally:
            tmp.cleanup()


if __name__ == "__main__":
    unittest.main()
