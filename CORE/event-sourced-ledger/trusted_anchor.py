"""Explicit trust boundary for retrieving ledger checkpoints.

The interface deliberately separates checkpoint retrieval from checkpoint
verification. A provider is a trust boundary, not a cryptographic trust root.
Production providers must use durable, authenticated storage or a signed
checkpoint verification layer.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from checkpoint import LedgerCheckpoint


class TrustedCheckpointAnchor(Protocol):
    """Provider interface for retrieving a retained checkpoint by ledger ID."""

    def get_checkpoint(self, ledger_id: str) -> LedgerCheckpoint | None:
        """Return the retained checkpoint for a ledger, or None if absent."""
        ...


class AnchorNotFound(ValueError):
    """Raised when an anchored replay has no retained checkpoint."""


@dataclass
class InMemoryCheckpointAnchor:
    """Reference provider for tests and local deterministic experiments."""

    _checkpoints: dict[str, LedgerCheckpoint] = field(default_factory=dict)

    def retain(self, ledger_id: str, checkpoint: LedgerCheckpoint) -> None:
        if not ledger_id:
            raise ValueError("ledger_id is required")
        self._checkpoints[ledger_id] = checkpoint

    def get_checkpoint(self, ledger_id: str) -> LedgerCheckpoint | None:
        if not ledger_id:
            return None
        return self._checkpoints.get(ledger_id)


def resolve_checkpoint_anchor(
    provider: TrustedCheckpointAnchor,
    *,
    ledger_id: str,
) -> LedgerCheckpoint:
    """Resolve a checkpoint through the explicit trust boundary."""
    if not ledger_id:
        raise ValueError("ledger_id is required for anchored replay")
    checkpoint = provider.get_checkpoint(ledger_id)
    if checkpoint is None:
        raise AnchorNotFound(f"no retained checkpoint for ledger {ledger_id!r}")
    return checkpoint
