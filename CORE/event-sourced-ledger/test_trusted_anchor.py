import tempfile
import unittest
from pathlib import Path

from checkpoint import CheckpointMismatch, checkpoint, verify_checkpoint
from ledger import EventSourcedLedger
from reducer import LedgerState, reduce_ledger_from_anchor
from trusted_anchor import AnchorNotFound, InMemoryCheckpointAnchor, resolve_checkpoint_anchor


class TestTrustedCheckpointAnchor(unittest.TestCase):
    def _ledger(self):
        tmp = tempfile.TemporaryDirectory()
        ledger = EventSourcedLedger(Path(tmp.name) / "events.jsonl")
        ledger.append({"event": "CREDIT", "amount": 100})
        return tmp, ledger

    def test_provider_resolves_matching_ledger(self):
        tmp, ledger = self._ledger()
        try:
            anchor = InMemoryCheckpointAnchor()
            expected = checkpoint(ledger)
            anchor.retain("ledger-A", expected)

            resolved = resolve_checkpoint_anchor(anchor, ledger_id="ledger-A")
            self.assertEqual(resolved, expected)
            verify_checkpoint(ledger, resolved)
        finally:
            tmp.cleanup()

    def test_missing_or_wrong_ledger_anchor_is_rejected(self):
        tmp, ledger = self._ledger()
        try:
            anchor = InMemoryCheckpointAnchor()
            anchor.retain("ledger-A", checkpoint(ledger))

            with self.assertRaises(AnchorNotFound):
                resolve_checkpoint_anchor(anchor, ledger_id="ledger-B")
        finally:
            tmp.cleanup()

    def test_empty_ledger_identity_is_rejected(self):
        anchor = InMemoryCheckpointAnchor()
        with self.assertRaises(ValueError):
            resolve_checkpoint_anchor(anchor, ledger_id="")

    def test_resolved_anchor_still_requires_checkpoint_verification(self):
        tmp, ledger = self._ledger()
        try:
            anchor = InMemoryCheckpointAnchor()
            expected = checkpoint(ledger)
            anchor.retain("ledger-A", expected)

            ledger.append({"event": "CREDIT", "amount": 1})
            resolved = resolve_checkpoint_anchor(anchor, ledger_id="ledger-A")
            with self.assertRaises(CheckpointMismatch):
                verify_checkpoint(ledger, resolved)
        finally:
            tmp.cleanup()

    def test_reducer_can_resolve_anchor_without_accepting_caller_checkpoint(self):
        tmp, ledger = self._ledger()
        try:
            anchor = InMemoryCheckpointAnchor()
            anchor.retain("ledger-A", checkpoint(ledger))

            state = reduce_ledger_from_anchor(ledger, anchor, ledger_id="ledger-A")
            self.assertEqual(state, LedgerState(balance=100, event_count=1))
        finally:
            tmp.cleanup()

    def test_anchored_reducer_rejects_missing_anchor(self):
        tmp, ledger = self._ledger()
        try:
            with self.assertRaises(AnchorNotFound):
                reduce_ledger_from_anchor(
                    ledger,
                    InMemoryCheckpointAnchor(),
                    ledger_id="ledger-A",
                )
        finally:
            tmp.cleanup()


if __name__ == "__main__":
    unittest.main()
