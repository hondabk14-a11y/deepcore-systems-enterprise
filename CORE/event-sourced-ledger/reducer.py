"""Deterministic reference reducer for DeepCore ledger events."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
from typing import Any, Iterable

from checkpoint import LedgerCheckpoint, verify_checkpoint
from invariants import verify_domain_events
from ledger import EventSourcedLedger, canonical_json
from trusted_anchor import TrustedCheckpointAnchor, resolve_checkpoint_anchor


class ReducerError(ValueError):
    """Raised when an event cannot produce a valid state transition."""


@dataclass(frozen=True)
class LedgerState:
    balance: int = 0
    event_count: int = 0


def state_hash(state: LedgerState) -> str:
    """SHA-256 commitment to reference reducer v1 state, including its domain."""
    if type(state.balance) is not int or type(state.event_count) is not int:
        raise ReducerError("state fields must be integers")
    if state.event_count < 0:
        raise ReducerError("event_count cannot be negative")
    return hashlib.sha256(canonical_json({
        "domain": "deepcore-reference-ledger-state",
        "reducer_version": 1,
        "balance": state.balance,
        "event_count": state.event_count,
    })).hexdigest()


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


def reduce_ledger(
    ledger: EventSourcedLedger,
    initial: LedgerState | None = None,
    checkpoint_anchor: LedgerCheckpoint | None = None,
) -> LedgerState:
    """Validate persisted history before deterministic reduction.

    When an externally retained checkpoint is supplied directly, replay
    completeness is enforced before any domain event can affect derived state.
    """
    if checkpoint_anchor is not None:
        verify_checkpoint(ledger, checkpoint_anchor)
    return reduce_events(ledger.replay(validator=verify_domain_events), initial=initial)


def reduce_ledger_from_anchor(
    ledger: EventSourcedLedger,
    anchor: TrustedCheckpointAnchor,
    *,
    ledger_id: str,
    initial: LedgerState | None = None,
) -> LedgerState:
    """Resolve a retained checkpoint through the explicit trust boundary."""
    checkpoint_anchor = resolve_checkpoint_anchor(anchor, ledger_id=ledger_id)
    return reduce_ledger(ledger, initial=initial, checkpoint_anchor=checkpoint_anchor)
