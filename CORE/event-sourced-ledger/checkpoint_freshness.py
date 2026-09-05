"""Freshness and rollback policy for retained ledger checkpoints.

A valid signature proves authenticity of a checkpoint, but does not prove
that it is the newest checkpoint. This module makes freshness an explicit
stateful verification boundary while preserving the current checkpoint
schema, whose event_count is the monotonic sequence number.
"""
from __future__ import annotations

from dataclasses import dataclass

from checkpoint import LedgerCheckpoint


class CheckpointFreshnessError(ValueError):
    """Base error for checkpoint freshness violations."""


class CheckpointIdentityError(CheckpointFreshnessError):
    """Raised when a checkpoint is evaluated under the wrong ledger identity."""


class CheckpointRollbackError(CheckpointFreshnessError):
    """Raised when a checkpoint is older than the accepted checkpoint."""


class CheckpointConflictError(CheckpointFreshnessError):
    """Raised when one sequence maps to conflicting checkpoint heads."""


class CheckpointFormatError(CheckpointFreshnessError):
    """Raised when checkpoint metadata is internally inconsistent."""


@dataclass
class CheckpointFreshnessPolicy:
    """Track the newest accepted checkpoint for one explicitly identified ledger.

    The current LedgerCheckpoint has no ledger_id or separate sequence field,
    so event_count is the monotonic sequence for this policy and the ledger
    identity is bound by the policy instance. An exact repeat is idempotent;
    older checkpoints and same-sequence conflicts are rejected. Rejected
    candidates never mutate trusted state.
    """

    ledger_id: str
    accepted: LedgerCheckpoint | None = None

    def __post_init__(self) -> None:
        if not self.ledger_id:
            raise CheckpointIdentityError("ledger_id is required")
        if self.accepted is not None:
            self._validate(self.accepted)

    @staticmethod
    def _validate(candidate: LedgerCheckpoint) -> None:
        if not isinstance(candidate, LedgerCheckpoint):
            raise CheckpointFormatError("candidate must be a LedgerCheckpoint")
        if not isinstance(candidate.event_count, int) or isinstance(candidate.event_count, bool):
            raise CheckpointFormatError("event_count must be an integer")
        if candidate.event_count < 0:
            raise CheckpointFormatError("event_count must be non-negative")
        if not isinstance(candidate.head_hash, str) or not candidate.head_hash:
            raise CheckpointFormatError("head_hash is required")

    def accept(self, candidate: LedgerCheckpoint) -> LedgerCheckpoint:
        """Accept a fresh checkpoint or idempotently accept the current one."""
        self._validate(candidate)
        current = self.accepted
        if current is None:
            self.accepted = candidate
            return candidate

        if candidate.event_count < current.event_count:
            raise CheckpointRollbackError(
                f"checkpoint sequence rollback: current={current.event_count}, "
                f"candidate={candidate.event_count}"
            )

        if candidate.event_count == current.event_count:
            if candidate == current:
                return current
            raise CheckpointConflictError(
                f"conflicting checkpoint at sequence {candidate.event_count}"
            )

        self.accepted = candidate
        return candidate
