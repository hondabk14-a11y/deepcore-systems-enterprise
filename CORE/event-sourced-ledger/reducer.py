"""Deterministic reference reducer for DeepCore ledger events."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from invariants import verify_domain_events
from ledger import EventSourcedLedger


class ReducerError(ValueError):
    """Raised when an event cannot produce a valid state transition."""


@dataclass(frozen=True)
class LedgerState:
    balance: int = 0
    event_count: int = 0


def apply_event(state: LedgerState, event: dict[str, Any]) -> LedgerState:
    kind = event.get("event")
    amount = event.get("amount")

    if kind not in {"CREDIT", "DEBIT"}:
        raise ReducerError(f"unsupported event type: {kind!r}")
    if not isinstance(amount, int) or isinstance(amount, bool) or amount < 0:
        raise ReducerError("amount must be a non-negative integer")

    balance = state.balance + amount if kind == "CREDIT" else state.balance - amount
    return LedgerState(balance=balance, event_count=state.event_count + 1)


def reduce_events(events: Iterable[dict[str, Any]], initial: LedgerState | None = None) -> LedgerState:
    state = initial or LedgerState()
    for event in events:
        state = apply_event(state, event)
    return state


def reduce_ledger(ledger: EventSourcedLedger, initial: LedgerState | None = None) -> LedgerState:
    """Validate persisted history before deterministic reduction."""
    return reduce_events(ledger.replay(validator=verify_domain_events), initial=initial)
