from CORE.deepcore_consensus import SignedQuorumCertificate
from CORE.deepcore_crypto import Ed25519Identity
from CORE.deepcore_key_registry import ValidatorKeyRegistry
from CORE.deepcore_runtime import DeepCoreLedger, Transaction


VALIDATORS = ["validator_A", "validator_B", "validator_C", "validator_D"]


def setup_consensus():
    identities = {v: Ed25519Identity.generate() for v in VALIDATORS}
    registry = ValidatorKeyRegistry()
    for validator, identity in identities.items():
        registry.register(validator, identity.public_key_bytes)
    ledger = DeepCoreLedger(VALIDATORS)
    tx = Transaction("validator_A", "validator_B", 100_000, 1_000, 1, "validator_A").sign_ed25519(identities["validator_A"])
    ledger.append_ed25519(tx, registry)
    proposal = ledger.prepare_block(VALIDATORS[:3])
    consensus = SignedQuorumCertificate(VALIDATORS)
    return identities, registry, ledger, proposal, consensus


def make_certificate(identities, registry, proposal, consensus):
    votes = [consensus.sign_vote(v, proposal, 0, identities[v]) for v in VALIDATORS[:3]]
    return consensus.build_certificate(proposal, 0, votes, registry)


def test_valid_signed_quorum_certificate():
    identities, registry, _, proposal, consensus = setup_consensus()
    certificate = make_certificate(identities, registry, proposal, consensus)
    assert len(certificate.votes) == 3
    assert certificate.voters == tuple(sorted(VALIDATORS[:3]))
    assert certificate.digest == make_certificate(identities, registry, proposal, consensus).digest
    assert consensus.verify_certificate(proposal, certificate, registry)


def test_certificate_can_be_committed_into_block():
    identities, registry, ledger, proposal, consensus = setup_consensus()
    certificate = make_certificate(identities, registry, proposal, consensus)
    block = ledger.commit(VALIDATORS[:3], certificate)
    assert block.quorum_certificate == certificate
    assert block.block_hash != proposal.block_hash
    assert ledger.verify_block(block, proposal.previous_hash)
    assert consensus.verify_certificate(proposal, block.quorum_certificate, registry)
    assert ledger.replay() == ledger.state


def test_insufficient_quorum_rejected():
    identities, registry, _, proposal, consensus = setup_consensus()
    votes = [consensus.sign_vote("validator_A", proposal, 0, identities["validator_A"])]
    try:
        consensus.build_certificate(proposal, 0, votes, registry)
    except ValueError as exc:
        assert "quorum" in str(exc)
    else:
        raise AssertionError("certificate unexpectedly accepted without quorum")


def test_forged_vote_rejected():
    identities, registry, _, proposal, consensus = setup_consensus()
    forged = consensus.sign_vote("validator_A", proposal, 0, identities["validator_A"])
    forged = type(forged)(forged.validator, forged.height, forged.round, "00" * 32, forged.signature)
    votes = [forged] + [consensus.sign_vote(v, proposal, 0, identities[v]) for v in VALIDATORS[1:3]]
    try:
        consensus.build_certificate(proposal, 0, votes, registry)
    except ValueError as exc:
        assert "invalid consensus vote" in str(exc)
    else:
        raise AssertionError("forged vote unexpectedly accepted")


def test_duplicate_vote_rejected():
    identities, registry, _, proposal, consensus = setup_consensus()
    vote = consensus.sign_vote("validator_A", proposal, 0, identities["validator_A"])
    votes = [vote, vote, consensus.sign_vote("validator_B", proposal, 0, identities["validator_B"]), consensus.sign_vote("validator_C", proposal, 0, identities["validator_C"])]
    try:
        consensus.build_certificate(proposal, 0, votes, registry)
    except ValueError as exc:
        assert "duplicate" in str(exc)
    else:
        raise AssertionError("duplicate vote unexpectedly accepted")


def test_revoked_key_invalidates_certificate():
    identities, registry, _, proposal, consensus = setup_consensus()
    votes = [consensus.sign_vote(v, proposal, 0, identities[v]) for v in VALIDATORS[:3]]
    registry.revoke("validator_B")
    try:
        consensus.build_certificate(proposal, 0, votes, registry)
    except ValueError as exc:
        assert "invalid consensus vote" in str(exc)
    else:
        raise AssertionError("vote from revoked key unexpectedly accepted")


def test_weighted_quorum_enforced():
    identities, registry, _, proposal, _ = setup_consensus()
    weights = {"validator_A": 1, "validator_B": 1, "validator_C": 1, "validator_D": 7}
    consensus = SignedQuorumCertificate(VALIDATORS, weights=weights)
    votes = [consensus.sign_vote(v, proposal, 0, identities[v]) for v in VALIDATORS[:3]]
    try:
        consensus.build_certificate(proposal, 0, votes, registry)
    except ValueError as exc:
        assert "weighted quorum" in str(exc)
    else:
        raise AssertionError("underweighted certificate unexpectedly accepted")
    votes.append(consensus.sign_vote("validator_D", proposal, 0, identities["validator_D"]))
    certificate = consensus.build_certificate(proposal, 0, votes, registry)
    assert consensus.verify_certificate(proposal, certificate, registry)


def test_wrong_proposal_certificate_rejected():
    identities, registry, _, proposal, consensus = setup_consensus()
    certificate = make_certificate(identities, registry, proposal, consensus)
    altered = type(proposal)(proposal.height, proposal.previous_hash, proposal.state_root, proposal.event_root, proposal.validator_votes, proposal.events, "11" * 32, None)
    assert consensus.verify_certificate(altered, certificate, registry) is False
