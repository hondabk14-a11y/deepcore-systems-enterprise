"""Freshness and rollback policy for retained ledger checkpoints.

A valid signature proves authenticity of a checkpoint, but does not prove
that it is the newest checkpoint. This module makes freshness an explicit
stateful verification boundary.
"""
from __future__ import annotations

from dataclasses import dataclass

from checkpoint import LedgerCheckpoint


class CheckpointFreshnessError(ValueError):
    """Base error for checkpoint freshness violations."""


class CheckpointIdentityError(CheckpointFreshnessError):
    """Raised when a checkpoint belongs to a different ledger."""


class CheckpointRollbackError(CheckpointFreshnessError):
    """Raised when a checkpoint is older than the accepted checkpoint."""


class CheckpointConflictError(CheckpointFreshnessError):
    """Raised when one sequence maps to conflicting checkpoint heads."""


class CheckpointFormatError(CheckpointFreshnessError):
    """Raised when checkpoint sequence metadata is internally inconsistent."""


@dataclass
class CheckpointFreshnessPolicy:
    """Track the newest accepted checkpoint for one explicitly identified ledger.

    Acceptance is monotonic. An exact repeat of the current checkpoint is
    idempotent; an older checkpoint or a conflicting checkpoint at the same
    sequence is rejected. Rejected candidates never mutate trusted state.
    """

    ledger_id: str
    accepted: LedgerCheckpoint | None = None

    def __post_init__(self) -> None:
        if not self.ledger_id:
            raise CheckpointIdentityError("ledger_id is required")
        if self.accepted is not None:
            self._validate(self.accepted)
            if self.accepted.ledger_id and self.accepted.ledger_id != self.ledger_id:
                raise CheckpointIdentityError("accepted checkpoint ledger_id does not match policy")

    def _validate(self, candidate: LedgerCheckpoint) -> None:
        if not isinstance(candidate, LedgerCheckpoint):
            raise CheckpointFormatError("candidate must be a LedgerCheckpoint")
        if candidate.ledger_id and candidate.ledger_id != self.ledger_id:
            raise CheckpointIdentityError("checkpoint ledger_id does not match policy")
        if not isinstance(candidate.sequence, int) or isinstance(candidate.sequence, bool) or candidate.sequence < 0:
            raise CheckpointFormatError("sequence must be a non-negative integer")
        if not isinstance(candidate.event_count, int) or isinstance(candidate.event_count, bool) or candidate.event_count < 0:
            raise CheckpointFormatError("event_count must be a non-negative integer")
        if candidate.sequence != candidate.event_count:
            raise CheckpointFormatError("sequence must equal event_count")
        if not isinstance(candidate.head_hash, str) or not candidate.head_hash:
            raise CheckpointFormatError("head_hash is required")

    def accept(self, candidate: LedgerCheckpoint) -> LedgerCheckpoint:
        """Accept a fresh checkpoint or idempotently accept the current one."""
        self._validate(candidate)
        current = self.accepted
        if current is None:
            self.accepted = candidate
            return candidate
        if candidate.sequence < current.sequence:
            raise CheckpointRollbackError(
                f"checkpoint sequence rollback: current={current.sequence}, candidate={candidate.sequence}"
            )
        if candidate.sequence == current.sequence:
            if candidate == current:
                return current
            raise CheckpointConflictError(
                f"conflicting checkpoint at sequence {candidate.sequence}"
            )
        self.accepted = candidate
        return candidate
