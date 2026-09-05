from pathlib import Path

import pytest

from CORE.deepcore_consensus import ConsensusVote, QuorumCertificate
from CORE.deepcore_hotstuff import HotStuffState, Phase
from CORE.deepcore_persistence import ConsensusSnapshotStore, PersistentHotStuffStateMachine


def qc() -> QuorumCertificate:
    votes = tuple(
        ConsensusVote(f"v{i}", 7, 2, "proposal-7", f"sig-{i}") for i in range(3)
    )
    return QuorumCertificate(7, 2, "proposal-7", votes)


def state() -> HotStuffState:
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


def test_round_trip_restores_safety_state_and_sequences(tmp_path: Path):
    store = ConsensusSnapshotStore(tmp_path / "consensus.json")
    digest = store.save(state(), {"v0": 9, "v1": 4})

    restored, sequences, recovered_digest = store.load()

    assert restored == state()
    assert sequences == {"v0": 9, "v1": 4}
    assert digest == recovered_digest


def test_serialization_is_deterministic(tmp_path: Path):
    first = tmp_path / "one.json"
    second = tmp_path / "two.json"
    store1 = ConsensusSnapshotStore(first)
    store2 = ConsensusSnapshotStore(second)

    store1.save(state(), {"v1": 4, "v0": 9})
    store2.save(state(), {"v0": 9, "v1": 4})

    assert first.read_bytes() == second.read_bytes()


def test_checksum_detects_tampering(tmp_path: Path):
    path = tmp_path / "consensus.json"
    store = ConsensusSnapshotStore(path)
    store.save(state())
    raw = path.read_text()
    path.write_text(raw.replace("proposal-7", "proposal-X", 1))

    with pytest.raises(ValueError, match="checksum mismatch"):
        store.load()


def test_truncated_snapshot_is_rejected(tmp_path: Path):
    path = tmp_path / "consensus.json"
    store = ConsensusSnapshotStore(path)
    store.save(state())
    path.write_bytes(path.read_bytes()[:20])

    with pytest.raises(ValueError, match="invalid or unreadable"):
        store.load()


def test_rollback_is_rejected(tmp_path: Path):
    store = ConsensusSnapshotStore(tmp_path / "consensus.json")
    store.save(state())

    with pytest.raises(ValueError, match="rollback detected"):
        store.load(minimum_view=8)


def test_wrapper_restores_hotstuff_state(tmp_path: Path):
    machine = type("Machine", (), {})()
    machine.state = state()
    wrapper = PersistentHotStuffStateMachine(machine, ConsensusSnapshotStore(tmp_path / "state.json"))
    wrapper.save({"v0": 3})

    machine.state = HotStuffState(99, Phase.PROPOSE)
    sequences = wrapper.restore(minimum_view=7)

    assert machine.state == state()
    assert sequences == {"v0": 3}


def test_invalid_transport_sequence_rejected(tmp_path: Path):
    store = ConsensusSnapshotStore(tmp_path / "state.json")
    with pytest.raises(ValueError, match="positive integers"):
        store.save(state(), {"v0": 0})
