from __future__ import annotations

import pytest

from CORE.deepcore_consensus import SignedQuorumCertificate
from CORE.deepcore_crypto import Ed25519Identity
from CORE.deepcore_hotstuff import HotStuffStateMachine, Phase, Timeout
from CORE.deepcore_key_registry import ValidatorKeyRegistry
from CORE.deepcore_runtime import Block, Event, Transaction, ZERO_HASH, merkle_root, sha256_obj


VALIDATORS = ["validator_A", "validator_B", "validator_C", "validator_D"]


def setup():
    identities = {v: Ed25519Identity.generate() for v in VALIDATORS}
    registry = ValidatorKeyRegistry()
    for v, identity in identities.items():
        registry.register(v, identity.public_key_bytes)
    machine = HotStuffStateMachine(VALIDATORS, registry)
    tx = Transaction("validator_A", "validator_B", 100, 1, 1, "validator_A").sign_ed25519(identities["validator_A"])
    event = Event(tx)
    state = {v: {"balance": 1_000_000, "nonce": 0} for v in VALIDATORS}
    state["validator_A"]["balance"] -= 101
    state["validator_A"]["nonce"] = 1
    state["validator_B"]["balance"] += 100
    block = Block(1, ZERO_HASH, sha256_obj(state), merkle_root([event.event_id]), tuple(VALIDATORS[:3]), (event,), "proposal-placeholder")
    consensus = SignedQuorumCertificate(VALIDATORS)
    votes = [consensus.sign_vote(v, block, 0, identities[v]) for v in VALIDATORS[:3]]
    return machine, registry, identities, block, votes, consensus


def test_deterministic_leader_election():
    machine, *_ = setup()
    assert machine.leader == "validator_A"
    assert machine.timeout(Timeout("validator_A", 0)) == 0
    assert machine.timeout(Timeout("validator_B", 0)) == 0
    assert machine.timeout(Timeout("validator_C", 0)) == 1
    assert machine.leader == "validator_B"


def test_valid_phase_progression():
    machine, _, _, block, votes, _ = setup()
    proposal = machine.propose("validator_A", block, 0)
    assert proposal == machine.state.proposal_hash
    prepare_qc = machine.prepare(block, 0, votes)
    assert machine.state.phase == Phase.PRE_COMMIT
    assert machine.state.prepare_qc == prepare_qc
    precommit_qc = machine.pre_commit(block, 0, votes)
    assert machine.state.phase == Phase.COMMIT
    assert machine.state.pre_commit_qc == precommit_qc
    assert machine.commit(block, 0) == precommit_qc


def test_wrong_leader_rejected():
    machine, _, _, block, _, _ = setup()
    with pytest.raises(ValueError, match="invalid leader"):
        machine.propose("validator_B", block, 0)


def test_wrong_view_rejected():
    machine, _, _, block, _, _ = setup()
    with pytest.raises(ValueError, match="stale or future view"):
        machine.propose("validator_A", block, 1)


def test_proposal_hash_mismatch_rejected():
    machine, _, _, block, votes, _ = setup()
    machine.propose("validator_A", block, 0)
    other = Block(block.height, block.previous_hash, block.state_root, block.event_root, ("validator_A", "validator_B", "validator_D"), block.events, block.block_hash)
    with pytest.raises(ValueError, match="proposal hash mismatch"):
        machine.prepare(other, 0, votes)


def test_prepare_qc_required_for_precommit():
    machine, _, _, block, votes, _ = setup()
    machine.propose("validator_A", block, 0)
    machine.state = machine.state.__class__(0, Phase.PRE_COMMIT, machine.state.proposal_hash)
    with pytest.raises(ValueError, match="prepare QC required"):
        machine.pre_commit(block, 0, votes)


def test_precommit_qc_required_for_commit():
    machine, _, _, block, _, _ = setup()
    machine.propose("validator_A", block, 0)
    machine.state = machine.state.__class__(0, Phase.COMMIT, machine.state.proposal_hash)
    with pytest.raises(ValueError, match="pre-commit QC required"):
        machine.commit(block, 0)


def test_locked_proposal_prevents_conflict():
    machine, _, _, block, votes, _ = setup()
    machine.propose("validator_A", block, 0)
    machine.prepare(block, 0, votes)
    conflicting = Block(block.height, block.previous_hash, block.state_root, block.event_root, ("validator_A", "validator_B", "validator_D"), block.events, block.block_hash)
    machine.state = machine.state.__class__(1, Phase.PROPOSE, locked_hash=machine.state.locked_hash, highest_qc=machine.state.highest_qc)
    with pytest.raises(ValueError, match="locked proposal"):
        machine.propose("validator_B", conflicting, 1)


def test_timeout_advances_view_only_at_quorum():
    machine, *_ = setup()
    assert machine.timeout(Timeout("validator_A", 0)) == 0
    assert machine.timeout(Timeout("validator_B", 0)) == 0
    assert machine.timeout(Timeout("validator_C", 0)) == 1
    assert machine.state.phase == Phase.PROPOSE


def test_stale_timeout_rejected():
    machine, *_ = setup()
    machine.timeout(Timeout("validator_A", 0))
    machine.timeout(Timeout("validator_B", 0))
    machine.timeout(Timeout("validator_C", 0))
    with pytest.raises(ValueError, match="stale timeout"):
        machine.timeout(Timeout("validator_D", 0))


def test_forged_vote_rejected_via_qc():
    machine, _, _, block, votes, _ = setup()
    machine.propose("validator_A", block, 0)
    forged = votes[0].__class__(votes[0].validator, votes[0].height, votes[0].round, votes[0].proposal_hash, "forged")
    with pytest.raises(ValueError, match="invalid consensus vote"):
        machine.prepare(block, 0, [forged, votes[1], votes[2]])


def test_revoked_validator_rejected():
    machine, registry, _, block, votes, _ = setup()
    registry.revoke("validator_C")
    machine.propose("validator_A", block, 0)
    with pytest.raises(ValueError, match="invalid consensus vote"):
        machine.prepare(block, 0, votes)


def test_transition_is_deterministic():
    m1, _, _, block1, votes1, _ = setup()
    m2, _, _, block2, votes2, _ = setup()
    assert m1.propose("validator_A", block1, 0) == m2.propose("validator_A", block2, 0)
    assert m1.state.phase == m2.state.phase == Phase.PREPARE
    qc1 = m1.prepare(block1, 0, votes1)
    qc2 = m2.prepare(block2, 0, votes2)
    assert qc1.proposal_hash == qc2.proposal_hash
    assert m1.state.phase == m2.state.phase == Phase.PRE_COMMIT
