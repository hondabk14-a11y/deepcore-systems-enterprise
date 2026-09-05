"""Durable boundary for checkpoint freshness state.

This module deliberately stores only the last accepted checkpoint in a small
JSON document. The file is not itself an authenticated trust root. Production
use requires authenticated storage, atomic replacement, permissions, backup
integrity, and recovery/rollback controls.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from checkpoint import LedgerCheckpoint
from checkpoint_freshness import CheckpointFreshnessPolicy


class DurableFreshnessError(ValueError):
    """Raised when durable freshness state is missing or malformed."""


def _checkpoint_to_dict(checkpoint: LedgerCheckpoint) -> dict[str, object]:
    return {
        "ledger_id": checkpoint.ledger_id,
        "sequence": checkpoint.sequence,
        "head_hash": checkpoint.head_hash,
        "event_count": checkpoint.event_count,
    }


def _checkpoint_from_dict(value: object) -> LedgerCheckpoint:
    if not isinstance(value, dict):
        raise DurableFreshnessError("durable checkpoint must be an object")
    try:
        return LedgerCheckpoint(
            ledger_id=value["ledger_id"],
            sequence=value["sequence"],
            head_hash=value["head_hash"],
            event_count=value["event_count"],
        )
    except (KeyError, TypeError):
        raise DurableFreshnessError("durable checkpoint fields are incomplete") from None


class DurableFreshnessStore:
    """Persist the freshness boundary with atomic file replacement."""

    def __init__(self, path: str | Path, *, ledger_id: str) -> None:
        self.path = Path(path)
        self.policy = CheckpointFreshnessPolicy(ledger_id)

    def load(self) -> LedgerCheckpoint | None:
        if not self.path.exists():
            return None
        try:
            with self.path.open("r", encoding="utf-8") as handle:
                value = json.load(handle)
        except (OSError, json.JSONDecodeError) as exc:
            raise DurableFreshnessError("unable to read durable freshness state") from exc
        checkpoint = _checkpoint_from_dict(value)
        self.policy.accept(checkpoint)
        return checkpoint

    def accept(self, candidate: LedgerCheckpoint) -> LedgerCheckpoint:
        accepted = self.policy.accept(candidate)
        self._persist(accepted)
        return accepted

    def _persist(self, checkpoint: LedgerCheckpoint) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_name(f".{self.path.name}.tmp")
        payload = json.dumps(_checkpoint_to_dict(checkpoint), sort_keys=True, separators=(",", ":")) + "\n"
        try:
            with temporary.open("w", encoding="utf-8") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, self.path)
        except OSError as exc:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass
            raise DurableFreshnessError("unable to persist freshness state") from exc
