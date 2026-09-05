#!/usr/bin/env python3
"""Deterministic crash/fault-injection harness for DeepCore recovery testing.

The harness models process crashes around safety-critical phase boundaries and
verifies that recovery comes only from a durable snapshot. It performs no
network, wallet, treasury, or external side effects.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable

from CORE.deepcore_hotstuff import HotStuffState
from CORE.deepcore_persistence import ConsensusSnapshotStore


class FaultPoint(str, Enum):
    BEFORE_PROPOSE = "BEFORE_PROPOSE"
    AFTER_PROPOSE = "AFTER_PROPOSE"
    AFTER_PREPARE = "AFTER_PREPARE"
    AFTER_PRE_COMMIT = "AFTER_PRE_COMMIT"
    BEFORE_COMMIT = "BEFORE_COMMIT"
    AFTER_COMMIT = "AFTER_COMMIT"
    BEFORE_TIMEOUT = "BEFORE_TIMEOUT"
    AFTER_TIMEOUT = "AFTER_TIMEOUT"


class InjectedCrash(RuntimeError):
    """Deterministic simulated process crash."""

    def __init__(self, point: FaultPoint):
        super().__init__(f"injected crash at {point.value}")
        self.point = point


@dataclass(frozen=True)
class RecoveryEvidence:
    fault_point: FaultPoint
    snapshot_digest: str
    recovered_view: int
    recovered_phase: str
    transport_sequences: dict[str, int]


class FaultInjectionHarness:
    """Inject a single deterministic crash and recover from a snapshot."""

    def __init__(self, store: ConsensusSnapshotStore):
        self.store = store

    @staticmethod
    def checkpoint(
        point: FaultPoint,
        state: HotStuffState,
        transport_sequences: dict[str, int] | None = None,
        crash_at: FaultPoint | None = None,
        store: ConsensusSnapshotStore | None = None,
    ) -> str | None:
        """Persist a checkpoint, then crash if the requested point is reached."""
        digest = None
        if store is not None:
            digest = store.save(state, transport_sequences)
        if point == crash_at:
            raise InjectedCrash(point)
        return digest

    def recover(self, minimum_view: int | None = None) -> tuple[HotStuffState, dict[str, int], str]:
        """Recover safety state and transport sequence state from durable storage."""
        return self.store.load(minimum_view=minimum_view)

    def run_recovery_scenario(
        self,
        fault_point: FaultPoint,
        state: HotStuffState,
        transport_sequences: dict[str, int] | None = None,
        minimum_view: int | None = None,
        mutate_before_recovery: Callable[[Any], None] | None = None,
    ) -> RecoveryEvidence:
        """Save a durable checkpoint, simulate a crash, optionally corrupt RAM, recover."""
        digest = self.store.save(state, transport_sequences)
        try:
            self.checkpoint(fault_point, state, transport_sequences, fault_point, self.store)
        except InjectedCrash as crash:
            if crash.point != fault_point:
                raise
        if mutate_before_recovery is not None:
            mutate_before_recovery(self)
        recovered, sequences, recovered_digest = self.recover(minimum_view=minimum_view)
        return RecoveryEvidence(
            fault_point=fault_point,
            snapshot_digest=recovered_digest,
            recovered_view=recovered.view,
            recovered_phase=recovered.phase.value,
            transport_sequences=sequences,
        )

    def assert_recovery(self, expected: HotStuffState, expected_sequences: dict[str, int] | None = None) -> RecoveryEvidence:
        """Recover and assert exact safety-state equality."""
        recovered, sequences, digest = self.recover(minimum_view=expected.view)
        if recovered != expected:
            raise AssertionError("recovered HotStuff safety state differs from checkpoint")
        if sequences != (expected_sequences or {}):
            raise AssertionError("recovered transport sequences differ from checkpoint")
        return RecoveryEvidence(
            fault_point=FaultPoint.AFTER_COMMIT,
            snapshot_digest=digest,
            recovered_view=recovered.view,
            recovered_phase=recovered.phase.value,
            transport_sequences=sequences,
        )
