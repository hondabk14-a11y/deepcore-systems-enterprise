import unittest

from reducer import LedgerState, ReducerError, apply_event, reduce_events


class ReducerTests(unittest.TestCase):
    def test_credit_and_debit_are_deterministic(self):
        events = [
            {"event": "CREDIT", "amount": 100},
            {"event": "DEBIT", "amount": 30},
            {"event": "CREDIT", "amount": 5},
        ]
        expected = LedgerState(balance=75, event_count=3)
        self.assertEqual(reduce_events(events), expected)
        self.assertEqual(reduce_events(events), expected)

    def test_initial_state_is_supported(self):
        self.assertEqual(
            apply_event(LedgerState(balance=50, event_count=2), {"event": "DEBIT", "amount": 10}),
            LedgerState(balance=40, event_count=3),
        )

    def test_unknown_event_is_rejected(self):
        with self.assertRaises(ReducerError):
            apply_event(LedgerState(), {"event": "TRANSFER", "amount": 1})

    def test_negative_amount_is_rejected(self):
        with self.assertRaises(ReducerError):
            apply_event(LedgerState(), {"event": "CREDIT", "amount": -1})

    def test_boolean_amount_is_rejected(self):
        with self.assertRaises(ReducerError):
            apply_event(LedgerState(), {"event": "CREDIT", "amount": True})


if __name__ == "__main__":
    unittest.main()
