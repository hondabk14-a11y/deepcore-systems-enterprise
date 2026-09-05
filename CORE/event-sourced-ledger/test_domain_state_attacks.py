import tempfile
import unittest
from pathlib import Path

from ledger import EventSourcedLedger, LedgerIntegrityError
from reducer import reduce_ledger


class TestDomainStateAttacks(unittest.TestCase):
    def _ledger_with_events(self, events):
        tmp = tempfile.TemporaryDirectory()
        ledger = EventSourcedLedger(Path(tmp.name) / "events.jsonl")
        for event in events:
            ledger.append(event)
        return tmp, ledger

    def test_unknown_event_type_cannot_reduce(self):
        tmp, ledger = self._ledger_with_events([{"event": "CREDIT", "amount": 10}])
        try:
            ledger.append({"event": "UNKNOWN", "amount": 5})
            with self.assertRaises(ValueError):
                reduce_ledger(ledger)
        finally:
            tmp.cleanup()

    def test_negative_amount_cannot_reduce(self):
        tmp, ledger = self._ledger_with_events([{"event": "CREDIT", "amount": 10}])
        try:
            ledger.append({"event": "DEBIT", "amount": -5})
            with self.assertRaises(ValueError):
                reduce_ledger(ledger)
        finally:
            tmp.cleanup()

    def test_boolean_amount_cannot_reduce_as_integer(self):
        tmp, ledger = self._ledger_with_events([{"event": "CREDIT", "amount": 10}])
        try:
            ledger.append({"event": "DEBIT", "amount": True})
            with self.assertRaises(ValueError):
                reduce_ledger(ledger)
        finally:
            tmp.cleanup()

    def test_fractional_amount_cannot_reduce(self):
        tmp, ledger = self._ledger_with_events([{"event": "CREDIT", "amount": 10}])
        try:
            ledger.append({"event": "DEBIT", "amount": 1.5})
            with self.assertRaises(ValueError):
                reduce_ledger(ledger)
        finally:
            tmp.cleanup()

    def test_domain_attack_with_valid_hashes_is_rejected_before_state_change(self):
        tmp, ledger = self._ledger_with_events([{"event": "CREDIT", "amount": 100}])
        try:
            ledger.append({"event": "DEBIT", "amount": 25})
            ledger.append({"event": "CREDIT", "amount": 7})
            original = reduce_ledger(ledger)
            self.assertEqual(original.balance, 82)

            # Rebuild a validly chained history containing an unsupported event.
            ledger.append({"event": "TRANSFER", "amount": 1})
            with self.assertRaises(ValueError):
                reduce_ledger(ledger)
        finally:
            tmp.cleanup()

    def test_replay_does_not_apply_domain_state_before_validation(self):
        tmp, ledger = self._ledger_with_events([{"event": "CREDIT", "amount": 100}])
        try:
            ledger.append({"event": "DEBIT", "amount": -50})
            with self.assertRaises(ValueError):
                reduce_ledger(ledger)
            # Structural replay remains valid because the malicious record was
            # committed correctly, but domain validation must stop reduction.
            self.assertTrue(ledger.verify())
        finally:
            tmp.cleanup()


if __name__ == "__main__":
    unittest.main()
