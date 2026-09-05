from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from checkpoint import LedgerCheckpoint
from checkpoint_freshness import CheckpointConflictError, CheckpointRollbackError
from durable_freshness import DurableFreshnessError, DurableFreshnessStore


class DurableFreshnessTests(unittest.TestCase):
    def checkpoint(self, sequence: int, head: str) -> LedgerCheckpoint:
        return LedgerCheckpoint(head_hash=head, event_count=sequence)

    def test_persists_and_reloads_latest_checkpoint(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "freshness.json"
            store = DurableFreshnessStore(path, ledger_id="ledger-a")
            store.accept(self.checkpoint(1, "h1"))
            store.accept(self.checkpoint(2, "h2"))
            restored = DurableFreshnessStore(path, ledger_id="ledger-a")
            self.assertEqual(restored.load(), self.checkpoint(2, "h2"))

    def test_restart_rejects_rollback(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "freshness.json"
            store = DurableFreshnessStore(path, ledger_id="ledger-a")
            store.accept(self.checkpoint(3, "h3"))
            restored = DurableFreshnessStore(path, ledger_id="ledger-a")
            restored.load()
            with self.assertRaises(CheckpointRollbackError):
                restored.accept(self.checkpoint(2, "h2"))

    def test_same_sequence_conflict_does_not_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "freshness.json"
            store = DurableFreshnessStore(path, ledger_id="ledger-a")
            store.accept(self.checkpoint(4, "h4"))
            with self.assertRaises(CheckpointConflictError):
                store.accept(self.checkpoint(4, "fork"))
            self.assertEqual(store.load(), self.checkpoint(4, "h4"))

    def test_malformed_state_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "freshness.json"
            path.write_text("not-json", encoding="utf-8")
            with self.assertRaises(DurableFreshnessError):
                DurableFreshnessStore(path, ledger_id="ledger-a").load()

    def test_wrong_ledger_state_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "freshness.json"
            path.write_text(json.dumps({
                "ledger_id": "ledger-b",
                "checkpoint": {"head_hash": "h1", "event_count": 1},
            }), encoding="utf-8")
            with self.assertRaises(ValueError):
                DurableFreshnessStore(path, ledger_id="ledger-a").load()


if __name__ == "__main__":
    unittest.main()
