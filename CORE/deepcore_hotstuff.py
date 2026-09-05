#!/usr/bin/env python3
"""Reference HotStuff-style phase state machine for DeepCore.

This is a deterministic safety-oriented reference model, not a production
network implementation. It models proposal, prepare, pre-commit and commit
phases, views, locks, timeouts and quorum-certificate validation.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from CORE.deepcore_consensus import QuorumCertificate, SignedQuorumCertificate
from CORE.deepcore_runtime import Block, canonical, sha256_bytes


class Phase(str, Enum):
    PROPOSE = "PROPOSE"
    PREPARE = "PREPARE"
    PRE_COMMIT = "PRE_COMMIT"
    COMMIT = "COMMIT"


@dataclass(frozen=True)
class Timeout:
    validator: str
    view: int
    reason: str = "timeout"

    def digest(self) -> str:
        return sha256_bytes(canonical({"validator": self.validator, "view": self.view, "reason": self.reason}))


@dataclass(frozen=True)
class HotStuffState:
    view: int
    phase: Phase
    proposal_hash: str | None = None
    prepare_qc: QuorumCertificate | None = None
    pre_commit_qc: QuorumCertificate | None = None
    locked_hash: str | None = None
    highest_qc: QuorumCertificate | None = None


class HotStuffStateMachine:
    """Deterministic single-replica HotStuff-style safety state machine."""

    def __init__(self, validators: list[str], registry: Any, weights: dict[str, int] | None = None, max_byzantine: int | None = None):
        self.consensus = SignedQuorumCertificate(validators, weights, max_byzantine)
        self.registry = registry
        self.validators = self.consensus.validators
        self.state = HotStuffState(0, Phase.PROPOSE)
        self._timeouts: dict[int, set[str]] = {}

    @property
    def leader(self) -> str:
        return self.validators[self.state.view % len(self.validators)]

    @property
    def quorum(self) -> int:
        return self.consensus.quorum

    def _require_view(self, view: int) -> None:
        if view != self.state.view:
            raise ValueError(f"stale or future view: expected {self.state.view}, got {view}")

    def _require_phase(self, phase: Phase) -> None:
        if self.state.phase != phase:
            raise ValueError(f"invalid phase transition: expected {phase.value}, got {self.state.phase.value}")

    def _check_leader(self, proposer: str) -> None:
        if proposer != self.leader:
            raise ValueError(f"invalid leader: expected {self.leader}")

    def propose(self, proposer: str, block: Block, view: int) -> str:
        self._require_view(view)
        self._require_phase(Phase.PROPOSE)
        self._check_leader(proposer)
        proposal_hash = self.consensus.proposal_hash(block)
        if self.state.locked_hash is not None and proposal_hash != self.state.locked_hash:
            raise ValueError("conflicting proposal violates locked proposal")
        self.state = HotStuffState(view, Phase.PREPARE, proposal_hash, None, None, self.state.locked_hash, self.state.highest_qc)
        return proposal_hash

    def prepare(self, block: Block, view: int, votes: list[Any]) -> QuorumCertificate:
        self._require_view(view)
        self._require_phase(Phase.PREPARE)
        proposal_hash = self.consensus.proposal_hash(block)
        if proposal_hash != self.state.proposal_hash:
            raise ValueError("proposal hash mismatch")
        qc = self.consensus.build_certificate(block, view, votes, self.registry)
        self.state = HotStuffState(view, Phase.PRE_COMMIT, proposal_hash, qc, None, proposal_hash, qc)
        return qc

    def pre_commit(self, block: Block, view: int, votes: list[Any]) -> QuorumCertificate:
        self._require_view(view)
        self._require_phase(Phase.PRE_COMMIT)
        proposal_hash = self.consensus.proposal_hash(block)
        if proposal_hash != self.state.proposal_hash:
            raise ValueError("proposal hash mismatch")
        if self.state.prepare_qc is None:
            raise ValueError("prepare QC required before PRE_COMMIT")
        qc = self.consensus.build_certificate(block, view, votes, self.registry)
        self.state = HotStuffState(view, Phase.COMMIT, proposal_hash, self.state.prepare_qc, qc, self.state.locked_hash, qc)
        return qc

    def commit(self, block: Block, view: int) -> QuorumCertificate:
        self._require_view(view)
        self._require_phase(Phase.COMMIT)
        proposal_hash = self.consensus.proposal_hash(block)
        if proposal_hash != self.state.proposal_hash:
            raise ValueError("proposal hash mismatch")
        if self.state.pre_commit_qc is None:
            raise ValueError("pre-commit QC required before COMMIT")
        return self.state.pre_commit_qc

    def timeout(self, timeout: Timeout) -> int:
        if timeout.validator not in self.validators:
            raise ValueError("unknown timeout validator")
        if timeout.view != self.state.view:
            raise ValueError(f"stale timeout: expected view {self.state.view}")
        voters = self._timeouts.setdefault(timeout.view, set())
        voters.add(timeout.validator)
        if len(voters) < self.quorum:
            return self.state.view
        self.state = HotStuffState(self.state.view + 1, Phase.PROPOSE, locked_hash=self.state.locked_hash, highest_qc=self.state.highest_qc)
        return self.state.view

    def verify_locked_proposal(self, block: Block, view: int) -> bool:
        self._require_view(view)
        proposal_hash = self.consensus.proposal_hash(block)
        return self.state.locked_hash is None or proposal_hash == self.state.locked_hash
