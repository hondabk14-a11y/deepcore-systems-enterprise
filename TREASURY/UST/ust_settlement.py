"""Deterministic DeepCore UST-0001 treasury settlement reference model."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class SettlementState(str, Enum):
    CREATED = "TX_CREATED"
    VALIDATED = "TX_VALIDATION_PASSED"
    BROADCAST_ATTEMPTED = "TX_BROADCAST_ATTEMPTED"
    MEMPOOL_ACCEPTED = "TX_MEMPOOL_ACCEPTED"
    CONFIRMED = "TX_CONFIRMED"
    REJECTED = "TX_REJECTED"


@dataclass(frozen=True)
class SettlementEvent:
    tx_id: str
    state: SettlementState
    sequence: int


class USTSettlementNode:
    """Reference-only state machine for UST-0001 settlement events."""

    NODE_ID = "0001"
    LOGICAL_NAME = "UST-0001"
    CONSENSUS_WEIGHT = 35
    TRUST_BASELINE = 1.0

    _ORDER = (
        SettlementState.CREATED,
        SettlementState.VALIDATED,
        SettlementState.BROADCAST_ATTEMPTED,
        SettlementState.MEMPOOL_ACCEPTED,
        SettlementState.CONFIRMED,
    )

    def __init__(self) -> None:
        self._events: dict[str, list[SettlementEvent]] = {}

    def apply(self, tx_id: str, state: SettlementState) -> SettlementEvent:
        if not isinstance(tx_id, str) or not tx_id:
            raise ValueError("tx_id must be a non-empty string")
        if not isinstance(state, SettlementState):
            raise TypeError("state must be SettlementState")

        history = self._events.setdefault(tx_id, [])
        if state is SettlementState.REJECTED:
            if history and history[-1].state is SettlementState.CONFIRMED:
                raise ValueError("confirmed settlement cannot be rejected")
        elif not history:
            if state is not SettlementState.CREATED:
                raise ValueError("settlement must start with TX_CREATED")
        else:
            current = history[-1].state
            if current is SettlementState.REJECTED:
                raise ValueError("rejected settlement cannot advance")
            if current is SettlementState.CONFIRMED:
                raise ValueError("confirmed settlement cannot advance")
            expected_index = self._ORDER.index(current) + 1
            if self._ORDER[expected_index] is not state:
                raise ValueError(f"invalid transition: {current.value} -> {state.value}")

        event = SettlementEvent(tx_id, state, len(history) + 1)
        history.append(event)
        return event

    def history(self, tx_id: str) -> tuple[SettlementEvent, ...]:
        return tuple(self._events.get(tx_id, ()))

    def state(self, tx_id: str) -> SettlementState | None:
        history = self._events.get(tx_id)
        return history[-1].state if history else None
