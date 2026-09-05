import tempfile
import unittest
from pathlib import Path

from ledger import EventSourcedLedger, LedgerIntegrityError


def reduce_events(events):
    state = {"balance": 0, "events": []}
    for event in events:
        if event["event"] == "CREDIT":
            state["balance"] += event["amount"]
        elif event["event"] == "DEBIT":
            state["balance"] -= event["amount"]
        else:
            raise ValueError(f"unknown event: {event['event']}")
        state["events"].append(event["event"])
    return state


class DeterministicReplayTests(unittest.TestCase):
    def test_replay_reconstructs_same_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger = EventSourcedLedger(Path(tmp) / "events.jsonl")
            ledger.append({"event": "CREDIT", "amount": 100})
            ledger.append({"event": "DEBIT", "amount": 25})
            ledger.append({"event": "CREDIT", "amount": 10})

            first = reduce_events(ledger.replay())
            second = reduce_events(ledger.replay())

            self.assertEqual(first, second)
            self.assertEqual(first["balance"], 85)
            self.assertEqual(first["events"], ["CREDIT", "DEBIT", "CREDIT"])

    def test_replay_preserves_event_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger = EventSourcedLedger(Path(tmp) / "events.jsonl")
            ledger.append({"event": "CREDIT", "amount": 40})
            ledger.append({"event": "DEBIT", "amount": 15})

            replayed = ledger.replay()

            self.assertEqual([e["event"] for e in replayed], ["CREDIT", "DEBIT"])
            self.assertEqual([e["amount"] for e in replayed], [40, 15])

    def test_corrupt_json_blocks_replay(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "events.jsonl"
            ledger = EventSourcedLedger(path)
            ledger.append({"event": "CREDIT", "amount": 1})
            path.write_text(path.read_text(encoding="utf-8") + "not-json\n", encoding="utf-8")

            with self.assertRaises(LedgerIntegrityError):
                ledger.replay()

    def test_unknown_domain_event_is_not_silently_reduced(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger = EventSourcedLedger(Path(tmp) / "events.jsonl")
            ledger.append({"event": "UNKNOWN", "amount": 1})

            with self.assertRaises(ValueError):
                reduce_events(ledger.replay())


if __name__ == "__main__":
    unittest.main()
