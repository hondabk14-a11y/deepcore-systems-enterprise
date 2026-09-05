"""Reference checkpoint anchoring for detecting valid-prefix truncation."""
from __future__ import annotations

from dataclasses import dataclass

from ledger import EventSourcedLedger, GENESIS


class CheckpointMismatch(ValueError):
    """Raised when persisted history does not match an expected checkpoint."""


@dataclass(frozen=True)
class LedgerCheckpoint:
    """Externally retained commitment to a specific ledger head."""

    head_hash: str = GENESIS
    event_count: int = 0
    anchor_id: str = ""


def checkpoint(ledger: EventSourcedLedger, anchor_id: str = "") -> LedgerCheckpoint:
    """Capture the current persisted head and record count."""
    records = ledger.replay()
    return LedgerCheckpoint(
        head_hash=ledger.last_hash(),
        event_count=len(records),
        anchor_id=anchor_id,
    )


def verify_checkpoint(ledger: EventSourcedLedger, expected: LedgerCheckpoint) -> None:
    """Reject histories that differ from the externally retained anchor."""
    records = ledger.replay()
    actual = LedgerCheckpoint(
        head_hash=ledger.last_hash(),
        event_count=len(records),
        anchor_id=expected.anchor_id,
    )
    if actual != expected:
        raise CheckpointMismatch(
            f"ledger checkpoint mismatch: expected {expected!r}, got {actual!r}"
        )
