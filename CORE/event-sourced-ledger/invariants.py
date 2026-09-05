"""Explicit integrity invariants for the reference event-sourced ledger."""
from __future__ import annotations

from typing import Any, Iterable

from ledger import GENESIS, EventSourcedLedger, event_hash


class InvariantViolation(ValueError):
    """Raised when persisted event history violates a ledger invariant."""


def verify_event_chain(records: Iterable[dict[str, Any]]) -> None:
    """Verify hash linkage and content commitments for an ordered record stream."""
    previous_hash = GENESIS
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            raise InvariantViolation(f"record {index} is not an object")
        stored_hash = record.get("hash")
        if not isinstance(stored_hash, str):
            raise InvariantViolation(f"record {index} has no valid hash")
        if record.get("previous_hash") != previous_hash:
            raise InvariantViolation(f"record {index} breaks previous_hash linkage")
        unsigned = dict(record)
        unsigned.pop("hash", None)
        if event_hash(unsigned) != stored_hash:
            raise InvariantViolation(f"record {index} hash commitment is invalid")
        previous_hash = stored_hash


def verify_domain_events(records: Iterable[dict[str, Any]]) -> None:
    """Verify reducer-domain events without repeating structural verification."""
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            raise InvariantViolation(f"record {index} is not an object")
        kind = record.get("event")
        if kind not in {"CREDIT", "DEBIT"}:
            raise InvariantViolation(f"record {index} has unsupported event type: {kind!r}")
        amount = record.get("amount")
        if not isinstance(amount, int) or isinstance(amount, bool) or amount < 0:
            raise InvariantViolation(f"record {index} has invalid amount")


def verify_invariants(records: Iterable[dict[str, Any]]) -> None:
    """Apply structural and domain invariants to an ordered event stream."""
    materialized = list(records)
    verify_event_chain(materialized)
    verify_domain_events(materialized)


def replay_validated(ledger: EventSourcedLedger) -> list[dict[str, Any]]:
    """Read persisted history only after the complete invariant boundary passes."""
    records = ledger.replay()
    verify_invariants(records)
    return records
