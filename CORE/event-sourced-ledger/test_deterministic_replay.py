import tempfile
import unittest
from pathlib import Path

from ledger import EventSourcedLedger, event_hash
from reducer import LedgerState, reduce_ledger


class TestDeterministicReplay(unittest.TestCase):
    def _build_ledger(self, events):
        path = Path(tempfile.mktemp())
        ledger = EventSourcedLedger(path)
        for event in events:
            ledger.append(event)
        return ledger

    def test_repeated_replay_produces_identical_history_and_state(self):
        ledger = self._build_ledger(
            [
                {"event": "CREDIT", "amount": 100},
                {"event": "DEBIT", "amount": 25},
                {"event": "CREDIT", "amount": 7},
            ]
        )

        first_history = ledger.replay()
        first_state = reduce_ledger(ledger)
        first_hashes = [record["hash"] for record in first_history]

        second_history = ledger.replay()
        second_state = reduce_ledger(ledger)
        second_hashes = [record["hash"] for record in second_history]

        self.assertEqual(first_history, second_history)
        self.assertEqual(first_hashes, second_hashes)
        self.assertEqual(first_state, second_state)
        self.assertEqual(first_state, LedgerState(balance=82, event_count=3))

    def test_canonical_event_hash_is_stable(self):
        event_a = {"event": "CREDIT", "amount": 42}
        event_b = {"amount": 42, "event": "CREDIT"}
        self.assertEqual(event_hash(event_a), event_hash(event_b))

    def test_replay_is_read_only(self):
        ledger = self._build_ledger(
            [
                {"event": "CREDIT", "amount": 10},
                {"event": "DEBIT", "amount": 4},
            ]
        )
        before = ledger.path.read_bytes()
        reduce_ledger(ledger)
        after = ledger.path.read_bytes()
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
