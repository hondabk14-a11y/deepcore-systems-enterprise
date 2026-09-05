"""Reference checkpoint anchoring for detecting valid-prefix truncation."""
from __future__ import annotations

from dataclasses import dataclass

from ledger import EventSourcedLedger, GENESIS


class CheckpointMismatch(ValueError):
    """Raised when persisted history does not match an expected checkpoint."""


@dataclass(frozen=True)
class LedgerCheckpoint:
    """Externally retained commitment to a specific ledger head."""

    ledger_id: str = ""
    sequence: int = 0
    head_hash: str = GENESIS
    event_count: int = 0


def checkpoint(
    ledger: EventSourcedLedger,
    *,
    ledger_id: str = "",
) -> LedgerCheckpoint:
    """Capture a structural commitment to the current persisted ledger head."""
    records = ledger.replay()
    return LedgerCheckpoint(
        ledger_id=ledger_id,
        sequence=len(records),
        head_hash=ledger.last_hash(),
        event_count=len(records),
    )


def verify_checkpoint(ledger: EventSourcedLedger, expected: LedgerCheckpoint) -> None:
    """Reject histories that differ from the externally retained anchor."""
    records = ledger.replay()
    actual = LedgerCheckpoint(
        ledger_id=expected.ledger_id,
        sequence=len(records),
        head_hash=ledger.last_hash(),
        event_count=len(records),
    )
    if actual != expected:
        raise CheckpointMismatch(
            f"ledger checkpoint mismatch: expected {expected!r}, got {actual!r}"
        )
