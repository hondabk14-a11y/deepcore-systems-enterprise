"""Minimal executable DeepCore event-sourced ledger baseline.

The event history is authoritative. Each record commits to the previous
record with a SHA-256 hash, allowing deterministic integrity verification.
This module is a reference implementation, not a production ledger.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Callable, Iterable

GENESIS = "GENESIS"


def canonical_json(value: dict[str, Any]) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def event_hash(event: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_json(event)).hexdigest()


class LedgerIntegrityError(ValueError):
    """Raised when an event cannot be safely appended or verified."""


class EventSourcedLedger:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _records(self):
        if not self.path.exists():
            return
        with self.path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, 1):
                if not line.strip():
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise LedgerIntegrityError(f"invalid JSON at line {line_number}") from exc
                if not isinstance(record, dict):
                    raise LedgerIntegrityError(f"record at line {line_number} is not an object")
                yield line_number, record

    def last_hash(self) -> str:
        previous = GENESIS
        for _, record in self._records() or ():
            previous = record.get("hash", "")
        return previous

    def append(self, event: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(event, dict):
            raise TypeError("event must be a dictionary")
        if "hash" in event or "previous_hash" in event:
            raise LedgerIntegrityError("caller cannot supply ledger-managed hash fields")
        if not event:
            raise LedgerIntegrityError("empty events are not permitted")
        previous_hash = self.last_hash()
        record = dict(event)
        record["previous_hash"] = previous_hash
        record["hash"] = event_hash(record)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")
        return record

    def verify(self) -> bool:
        previous_hash = GENESIS
        for line_number, record in self._records() or ():
            stored_hash = record.get("hash")
            if not isinstance(stored_hash, str):
                return False
            if record.get("previous_hash") != previous_hash:
                return False
            unsigned = dict(record)
            unsigned.pop("hash", None)
            if event_hash(unsigned) != stored_hash:
                return False
            previous_hash = stored_hash
        return True

    def replay(self, validator: Callable[[Iterable[dict[str, Any]]], None] | None = None) -> list[dict[str, Any]]:
        """Verify structure, materialize history, then optionally validate domain invariants."""
        if not self.verify():
            raise LedgerIntegrityError("cannot replay an invalid ledger")
        records = [record for _, record in (self._records() or ())]
        if validator is not None:
            validator(records)
        return records
