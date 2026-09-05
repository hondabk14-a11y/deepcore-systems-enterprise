"""Authenticated durable freshness envelope.

This boundary combines a signed checkpoint with the freshness state that was
previously accepted. It does not choose a trust root or persist private keys.
"""
from __future__ import annotations

from dataclasses import dataclass

from checkpoint import LedgerCheckpoint
from checkpoint_freshness import CheckpointFreshnessPolicy
from signed_checkpoint import (
    CheckpointPublicKeyResolver,
    CheckpointSignatureVerifier,
    SignedCheckpoint,
    verify_signed_checkpoint,
)


class AuthenticatedFreshnessError(ValueError):
    """Raised when authenticated freshness verification fails."""


@dataclass
class AuthenticatedFreshnessBoundary:
    """Verify checkpoint authenticity before advancing trusted freshness."""

    ledger_id: str
    key_resolver: CheckpointPublicKeyResolver
    verifier: CheckpointSignatureVerifier
    policy: CheckpointFreshnessPolicy | None = None

    def __post_init__(self) -> None:
        if not self.ledger_id:
            raise AuthenticatedFreshnessError("ledger_id is required")
        if self.policy is None:
            self.policy = CheckpointFreshnessPolicy(self.ledger_id)

    def accept(self, signed: SignedCheckpoint) -> LedgerCheckpoint:
        """Authenticate a signed checkpoint, then apply monotonic freshness."""
        try:
            checkpoint = verify_signed_checkpoint(
                signed,
                key_resolver=self.key_resolver,
                verifier=self.verifier,
            )
        except Exception as exc:
            raise AuthenticatedFreshnessError("checkpoint authentication failed") from exc
        if checkpoint.ledger_id != self.ledger_id:
            raise AuthenticatedFreshnessError("checkpoint ledger identity mismatch")
        try:
            return self.policy.accept(checkpoint)
        except Exception as exc:
            raise AuthenticatedFreshnessError("checkpoint freshness rejected") from exc
