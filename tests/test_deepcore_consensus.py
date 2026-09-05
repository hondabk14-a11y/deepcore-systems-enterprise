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
    tx = Transaction("validator_A", "validator_B", 100_000, 1_000, 1, "validator_A")
    tx = tx.sign_ed25519(identities["validator_A"])
    ledger.append_ed25519(tx, registry)
    block = ledger.commit(VALIDATORS[:3])
    consensus = SignedQuorumCertificate(VALIDATORS)
    return identities, registry, ledger, block, consensus


def test_valid_signed_quorum_certificate():
    identities, registry, _, block, consensus = setup_consensus()
    votes = [consensus.sign_vote(v, block, 0, identities[v]) for v in VALIDATORS[:3]]
    certificate = consensus.build_certificate(block, 0, votes, registry)

    assert len(certificate.votes) == 3
    assert certificate.voters == tuple(sorted(VALIDATORS[:3]))
    assert certificate.digest == consensus.build_certificate(block, 0, votes, registry).digest
    assert consensus.verify_certificate(block, certificate, registry)


def test_insufficient_quorum_rejected():
    identities, registry, _, block, consensus = setup_consensus()
    votes = [consensus.sign_vote("validator_A", block, 0, identities["validator_A"])]

    try:
        consensus.build_certificate(block, 0, votes, registry)
    except ValueError as exc:
        assert "quorum" in str(exc)
    else:
        raise AssertionError("certificate unexpectedly accepted without quorum")


def test_forged_vote_rejected():
    identities, registry, _, block, consensus = setup_consensus()
    forged = consensus.sign_vote("validator_A", block, 0, identities["validator_A"])
    forged = type(forged)(forged.validator, forged.height, forged.round, "00" * 32, forged.signature)
    votes = [forged] + [consensus.sign_vote(v, block, 0, identities[v]) for v in VALIDATORS[1:3]]

    try:
        consensus.build_certificate(block, 0, votes, registry)
    except ValueError as exc:
        assert "invalid consensus vote" in str(exc)
    else:
        raise AssertionError("forged vote unexpectedly accepted")


def test_duplicate_vote_rejected():
    identities, registry, _, block, consensus = setup_consensus()
    vote = consensus.sign_vote("validator_A", block, 0, identities["validator_A"])
    votes = [vote, vote, consensus.sign_vote("validator_B", block, 0, identities["validator_B"]), consensus.sign_vote("validator_C", block, 0, identities["validator_C"])]

    try:
        consensus.build_certificate(block, 0, votes, registry)
    except ValueError as exc:
        assert "duplicate" in str(exc)
    else:
        raise AssertionError("duplicate vote unexpectedly accepted")


def test_revoked_key_invalidates_certificate():
    identities, registry, _, block, consensus = setup_consensus()
    votes = [consensus.sign_vote(v, block, 0, identities[v]) for v in VALIDATORS[:3]]
    registry.revoke("validator_B")

    try:
        consensus.build_certificate(block, 0, votes, registry)
    except ValueError as exc:
        assert "invalid consensus vote" in str(exc)
    else:
        raise AssertionError("vote from revoked key unexpectedly accepted")


def test_weighted_quorum_enforced():
    identities, registry, _, block, _ = setup_consensus()
    weights = {"validator_A": 1, "validator_B": 1, "validator_C": 1, "validator_D": 7}
    consensus = SignedQuorumCertificate(VALIDATORS, weights=weights)
    votes = [consensus.sign_vote(v, block, 0, identities[v]) for v in VALIDATORS[:3]]

    try:
        consensus.build_certificate(block, 0, votes, registry)
    except ValueError as exc:
        assert "weighted quorum" in str(exc)
    else:
        raise AssertionError("underweighted certificate unexpectedly accepted")

    votes.append(consensus.sign_vote("validator_D", block, 0, identities["validator_D"]))
    certificate = consensus.build_certificate(block, 0, votes, registry)
    assert consensus.verify_certificate(block, certificate, registry)
