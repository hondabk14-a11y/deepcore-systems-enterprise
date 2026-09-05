from pathlib import Path

import pytest

from CORE.deepcore_consensus import ConsensusVote, QuorumCertificate
from CORE.deepcore_fault_injection import FaultInjectionHarness, FaultPoint, InjectedCrash
from CORE.deepcore_hotstuff import HotStuffState, Phase
from CORE.deepcore_persistence import ConsensusSnapshotStore


def qc() -> QuorumCertificate:
    votes = tuple(ConsensusVote(f"v{i}", 7, 2, "proposal-7", f"sig-{i}") for i in range(3))
    return QuorumCertificate(7, 2, "proposal-7", votes)


def committed_state() -> HotStuffState:
    certificate = qc()
    return HotStuffState(
        view=7,
        phase=Phase.COMMIT,
        proposal_hash="proposal-7",
        prepare_qc=certificate,
        pre_commit_qc=certificate,
        locked_hash="proposal-7",
        highest_qc=certificate,
    )


def test_crash_is_deterministic(tmp_path: Path):
    store = ConsensusSnapshotStore(tmp_path / "state.json")
    state = committed_state()

    with pytest.raises(InjectedCrash, match="AFTER_PREPARE"):
        FaultInjectionHarness.checkpoint(
            FaultPoint.AFTER_PREPARE,
            state,
            {"v0": 12},
            crash_at=FaultPoint.AFTER_PREPARE,
            store=store,
        )


def test_recovery_restores_exact_safety_state_and_sequences(tmp_path: Path):
    store = ConsensusSnapshotStore(tmp_path / "state.json")
    harness = FaultInjectionHarness(store)
    state = committed_state()
    evidence = harness.run_recovery_scenario(
        FaultPoint.AFTER_PRE_COMMIT,
        state,
        {"v0": 12, "v1": 8},
        minimum_view=7,
    )

    recovered, sequences, digest = store.load(minimum_view=7)
    assert recovered == state
    assert sequences == {"v0": 12, "v1": 8}
    assert evidence.snapshot_digest == digest
    assert evidence.recovered_view == 7
    assert evidence.recovered_phase == Phase.COMMIT.value


def test_corrupted_snapshot_fails_closed_after_crash(tmp_path: Path):
    path = tmp_path / "state.json"
    store = ConsensusSnapshotStore(path)
    harness = FaultInjectionHarness(store)
    harness.run_recovery_scenario(FaultPoint.BEFORE_COMMIT, committed_state(), {"v0": 3})

    raw = path.read_text()
    path.write_text(raw.replace("proposal-7", "proposal-corrupted", 1))

    with pytest.raises(ValueError, match="checksum mismatch"):
        harness.recover(minimum_view=7)


def test_rollback_snapshot_is_rejected(tmp_path: Path):
    store = ConsensusSnapshotStore(tmp_path / "state.json")
    harness = FaultInjectionHarness(store)
    harness.run_recovery_scenario(FaultPoint.AFTER_TIMEOUT, committed_state(), {"v0": 3})

    with pytest.raises(ValueError, match="rollback detected"):
        harness.recover(minimum_view=8)
