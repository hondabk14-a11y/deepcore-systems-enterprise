#!/usr/bin/env python3
"""Signed quorum certificates for the DeepCore reference consensus layer.

This module authenticates a consensus decision with individual Ed25519
validator votes. It is a quorum-certificate primitive, not a complete
HotStuff implementation: networking, proposal phases, pacemaking, durable
key custody, and timeout/view-change logic remain separate controls.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from CORE.deepcore_runtime import Block, canonical, sha256_bytes


@dataclass(frozen=True)
class ConsensusVote:
    """One validator's signed vote for an exact block decision."""

    validator: str
    height: int
    round: int
    block_hash: str
    signature: str

    def unsigned(self) -> dict[str, Any]:
        return {
            "validator": self.validator,
            "height": self.height,
            "round": self.round,
            "block_hash": self.block_hash,
        }


@dataclass(frozen=True)
class QuorumCertificate:
    """Deterministic collection of authenticated votes forming a quorum."""

    height: int
    round: int
    block_hash: str
    votes: tuple[ConsensusVote, ...]

    @property
    def voters(self) -> tuple[str, ...]:
        return tuple(v.validator for v in self.votes)

    @property
    def digest(self) -> str:
        return sha256_bytes(
            canonical(
                {
                    "height": self.height,
                    "round": self.round,
                    "block_hash": self.block_hash,
                    "votes": [
                        {
                            "validator": v.validator,
                            "height": v.height,
                            "round": v.round,
                            "block_hash": v.block_hash,
                            "signature": v.signature,
                        }
                        for v in self.votes
                    ],
                }
            )
        )


class SignedQuorumCertificate:
    """Build and independently verify Ed25519-backed quorum certificates."""

    def __init__(self, validators: list[str], weights: dict[str, int] | None = None, max_byzantine: int | None = None):
        if not validators or len(set(validators)) != len(validators):
            raise ValueError("validators must be non-empty and unique")
        self.validators = tuple(sorted(validators))
        self.weights = weights or {v: 1 for v in self.validators}
        if set(self.weights) != set(self.validators) or any(w <= 0 for w in self.weights.values()):
            raise ValueError("weights must contain every validator and be positive")
        self.f = (len(self.validators) - 1) // 3 if max_byzantine is None else max_byzantine
        if len(self.validators) < 3 * self.f + 1:
            raise ValueError("BFT safety requires N >= 3f + 1")

    @property
    def quorum(self) -> int:
        return 2 * self.f + 1

    @property
    def total_weight(self) -> int:
        return sum(self.weights.values())

    def vote_payload(self, height: int, round: int, block_hash: str) -> bytes:
        return canonical({"height": height, "round": round, "block_hash": block_hash})

    def sign_vote(self, validator: str, block: Block, round: int, identity: Any) -> ConsensusVote:
        if validator not in self.validators:
            raise ValueError("unknown validator")
        payload = self.vote_payload(block.height, round, block.block_hash)
        return ConsensusVote(validator, block.height, round, block.block_hash, identity.sign(payload))

    def _validate_vote(self, vote: ConsensusVote, height: int, round: int, block_hash: str, registry: Any) -> bool:
        if vote.validator not in self.validators:
            return False
        if vote.height != height or vote.round != round or vote.block_hash != block_hash:
            return False
        return registry.verify(vote.validator, self.vote_payload(height, round, block_hash), vote.signature)

    def build_certificate(
        self,
        block: Block,
        round: int,
        votes: list[ConsensusVote],
        registry: Any,
    ) -> QuorumCertificate:
        if not votes:
            raise ValueError("no votes supplied")
        seen: set[str] = set()
        valid: list[ConsensusVote] = []
        for vote in votes:
            if vote.validator in seen:
                raise ValueError("duplicate validator vote")
            seen.add(vote.validator)
            if not self._validate_vote(vote, block.height, round, block.block_hash, registry):
                raise ValueError(f"invalid consensus vote: {vote.validator}")
            valid.append(vote)

        if len(valid) < self.quorum:
            raise ValueError(f"BFT quorum not met: need {self.quorum} unique voters")
        weight = sum(self.weights[v.validator] for v in valid)
        if weight * 3 < self.total_weight * 2:
            raise ValueError("weighted quorum not met")

        ordered = tuple(sorted(valid, key=lambda v: v.validator))
        return QuorumCertificate(block.height, round, block.block_hash, ordered)

    def verify_certificate(self, block: Block, certificate: QuorumCertificate, registry: Any) -> bool:
        if certificate.height != block.height or certificate.block_hash != block.block_hash:
            return False
        if len(certificate.votes) < self.quorum:
            return False
        seen: set[str] = set()
        weight = 0
        for vote in certificate.votes:
            if vote.validator in seen:
                return False
            seen.add(vote.validator)
            if not self._validate_vote(vote, certificate.height, certificate.round, certificate.block_hash, registry):
                return False
            weight += self.weights[vote.validator]
        return weight * 3 >= self.total_weight * 2
