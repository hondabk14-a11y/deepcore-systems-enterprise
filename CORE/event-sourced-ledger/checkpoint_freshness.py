"""Freshness and rollback policy for retained ledger checkpoints."""
from __future__ import annotations

from dataclasses import dataclass

from checkpoint import LedgerCheckpoint


class CheckpointFreshnessError(ValueError):
    """Base error for checkpoint freshness violations."""


class CheckpointIdentityError(CheckpointFreshnessError):
    """Raised when a freshness policy has no explicit ledger identity."""


class CheckpointRollbackError(CheckpointFreshnessError):
    """Raised when a checkpoint is older than the accepted checkpoint."""


class CheckpointConflictError(CheckpointFreshnessError):
    """Raised when one sequence maps to conflicting checkpoint heads."""


class CheckpointFormatError(CheckpointFreshnessError):
    """Raised when checkpoint metadata is internally inconsistent."""


@dataclass
class CheckpointFreshnessPolicy:
    """Track the newest accepted checkpoint for one explicitly named ledger.

    The current checkpoint schema has no ledger identity field, so identity is
    held by this policy boundary rather than fabricated into the checkpoint.
    Exact repeats are idempotent; stale and same-sequence conflicting heads
    are rejected, and rejected candidates never mutate trusted state.
    """

    ledger_id: str
    accepted: LedgerCheckpoint | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.ledger_id, str) or not self.ledger_id:
            raise CheckpointIdentityError("ledger_id is required")
        if self.accepted is not None:
            self._validate(self.accepted)

    @staticmethod
    def _validate(candidate: LedgerCheckpoint) -> None:
        if not isinstance(candidate, LedgerCheckpoint):
            raise CheckpointFormatError("candidate must be a LedgerCheckpoint")
        if not isinstance(candidate.event_count, int) or isinstance(candidate.event_count, bool):
            raise CheckpointFormatError("event_count must be a non-negative integer")
        if candidate.event_count < 0:
            raise CheckpointFormatError("event_count must be a non-negative integer")
        if not isinstance(candidate.head_hash, str) or not candidate.head_hash:
            raise CheckpointFormatError("head_hash is required")

    def accept(self, candidate: LedgerCheckpoint) -> LedgerCheckpoint:
        """Accept a newer checkpoint or idempotently accept the current one."""
        self._validate(candidate)
        current = self.accepted
        if current is None:
            self.accepted = candidate
            return candidate
        if candidate.event_count < current.event_count:
            raise CheckpointRollbackError(
                f"checkpoint sequence rollback: current={current.event_count}, candidate={candidate.event_count}"
            )
        if candidate.event_count == current.event_count:
            if candidate == current:
                return current
            raise CheckpointConflictError(
                f"conflicting checkpoint at sequence {candidate.event_count}"
            )
        self.accepted = candidate
        return candidate
