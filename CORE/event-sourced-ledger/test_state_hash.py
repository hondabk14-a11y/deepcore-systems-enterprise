import unittest

from reducer import LedgerState, ReducerError, reduce_events, state_hash


class TestStateHash(unittest.TestCase):
    def test_known_state_commitment(self):
        self.assertEqual(
            state_hash(LedgerState(balance=82, event_count=3)),
            "026dc6918fbd9180f8f66c3c620f6d31bfd75fcd6f5e38a85c3d3a302cac1bf4",
        )

    def test_each_state_field_is_committed(self):
        base = state_hash(LedgerState(82, 3))
        self.assertNotEqual(base, state_hash(LedgerState(83, 3)))
        self.assertNotEqual(base, state_hash(LedgerState(82, 4)))

    def test_invalid_state_is_rejected(self):
        for state in (LedgerState(True, 1), LedgerState(1, False),
                      LedgerState(1.0, 1), LedgerState(1, -1)):
            with self.subTest(state=state), self.assertRaises(ReducerError):
                state_hash(state)

    def test_later_failure_preserves_initial_state_commitment(self):
        initial = LedgerState(10, 1)
        before = state_hash(initial)
        with self.assertRaises(ReducerError):
            reduce_events([{"event": "CREDIT", "amount": 7},
                           {"event": "CREDIT", "amount": True}], initial)
        self.assertEqual(state_hash(initial), before)


if __name__ == "__main__":
    unittest.main()
