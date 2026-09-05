import unittest

from checkpoint import LedgerCheckpoint
from checkpoint_freshness import (
    CheckpointConflictError,
    CheckpointFormatError,
    CheckpointIdentityError,
    CheckpointRollbackError,
    CheckpointFreshnessPolicy,
)


class CheckpointFreshnessTests(unittest.TestCase):
    def setUp(self):
        self.policy = CheckpointFreshnessPolicy("ledger-A")

    def checkpoint(self, count, head):
        return LedgerCheckpoint(head_hash=head, event_count=count)

    def test_first_checkpoint_is_accepted(self):
        candidate = self.checkpoint(1, "a" * 64)
        self.assertIs(self.policy.accept(candidate), candidate)
        self.assertEqual(self.policy.accepted, candidate)

    def test_newer_checkpoint_is_accepted(self):
        first = self.checkpoint(1, "a" * 64)
        newer = self.checkpoint(2, "b" * 64)
        self.policy.accept(first)
        self.assertIs(self.policy.accept(newer), newer)
        self.assertEqual(self.policy.accepted, newer)

    def test_older_checkpoint_is_rejected_without_state_change(self):
        current = self.checkpoint(3, "c" * 64)
        older = self.checkpoint(2, "b" * 64)
        self.policy.accept(current)
        with self.assertRaises(CheckpointRollbackError):
            self.policy.accept(older)
        self.assertEqual(self.policy.accepted, current)

    def test_same_checkpoint_is_idempotent(self):
        current = self.checkpoint(3, "c" * 64)
        self.policy.accept(current)
        self.assertIs(self.policy.accept(current), current)

    def test_same_sequence_different_head_is_conflict(self):
        current = self.checkpoint(3, "c" * 64)
        conflict = self.checkpoint(3, "d" * 64)
        self.policy.accept(current)
        with self.assertRaises(CheckpointConflictError):
            self.policy.accept(conflict)
        self.assertEqual(self.policy.accepted, current)

    def test_empty_ledger_checkpoint_is_valid_initial_state(self):
        genesis = self.checkpoint(0, "GENESIS")
        self.assertIs(self.policy.accept(genesis), genesis)

    def test_missing_ledger_identity_is_rejected(self):
        with self.assertRaises(CheckpointIdentityError):
            CheckpointFreshnessPolicy("")

    def test_invalid_count_is_rejected(self):
        with self.assertRaises(CheckpointFormatError):
            self.policy.accept(LedgerCheckpoint(head_hash="a" * 64, event_count=True))

    def test_missing_head_hash_is_rejected(self):
        with self.assertRaises(CheckpointFormatError):
            self.policy.accept(LedgerCheckpoint(head_hash="", event_count=1))


if __name__ == "__main__":
    unittest.main()
