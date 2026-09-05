#!/usr/bin/env python3
"""Deterministic authenticated message transport for DeepCore consensus.

This is a reference transport model, not a network socket implementation.
Messages are canonicalized, addressed to known validators, sequenced per sender,
and authenticated with the existing Ed25519 key registry.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from CORE.deepcore_runtime import canonical, sha256_bytes


@dataclass(frozen=True)
class ConsensusMessage:
    sender: str
    recipient: str
    view: int
    sequence: int
    kind: str
    payload: dict[str, Any]
    signature: str

    def unsigned(self) -> dict[str, Any]:
        return {
            "sender": self.sender,
            "recipient": self.recipient,
            "view": self.view,
            "sequence": self.sequence,
            "kind": self.kind,
            "payload": self.payload,
        }

    @property
    def message_id(self) -> str:
        return sha256_bytes(canonical({**self.unsigned(), "signature": self.signature}))


class AuthenticatedTransport:
    """In-memory reference transport with deterministic delivery semantics."""

    def __init__(self, validators: list[str], registry: Any, identities: dict[str, Any]):
        if not validators or len(set(validators)) != len(validators):
            raise ValueError("validators must be non-empty and unique")
        self.validators = tuple(sorted(validators))
        self.registry = registry
        self.identities = identities
        if set(identities) != set(self.validators):
            raise ValueError("identities must contain every validator")
        self._next_sequence = {validator: 1 for validator in self.validators}
        self._seen_sequences: dict[str, set[int]] = {validator: set() for validator in self.validators}
        self._queue: list[ConsensusMessage] = []

    def send(self, sender: str, recipient: str, view: int, kind: str, payload: dict[str, Any]) -> ConsensusMessage:
        if sender not in self.validators or recipient not in self.validators:
            raise ValueError("unknown transport participant")
        if view < 0 or not kind:
            raise ValueError("invalid message metadata")
        sequence = self._next_sequence[sender]
        unsigned = {"sender": sender, "recipient": recipient, "view": view, "sequence": sequence, "kind": kind, "payload": payload}
        signature = self.identities[sender].sign(canonical(unsigned))
        message = ConsensusMessage(sender, recipient, view, sequence, kind, dict(payload), signature)
        self._queue.append(message)
        self._next_sequence[sender] += 1
        return message

    def verify(self, message: ConsensusMessage, expected_view: int | None = None) -> bool:
        if message.sender not in self.validators or message.recipient not in self.validators:
            return False
        if expected_view is not None and message.view != expected_view:
            return False
        if message.sequence <= 0 or message.sequence in self._seen_sequences[message.sender]:
            return False
        if not self.registry.verify(message.sender, canonical(message.unsigned()), message.signature):
            return False
        return True

    def receive(self, recipient: str, expected_view: int | None = None) -> ConsensusMessage:
        if recipient not in self.validators:
            raise ValueError("unknown transport recipient")
        for index, message in enumerate(self._queue):
            if message.recipient != recipient:
                continue
            if not self.verify(message, expected_view):
                raise ValueError("invalid or stale consensus message")
            self._queue.pop(index)
            self._seen_sequences[message.sender].add(message.sequence)
            return message
        raise LookupError("no deliverable message")

    def pending(self) -> tuple[ConsensusMessage, ...]:
        return tuple(self._queue)
