"""Tamper and mismatch tests for consensus authorization commitments."""

from __future__ import annotations

from types import SimpleNamespace

from CORE.deepcore_consensus import SignedQuorumCertificate


VALID_AUTH = "a" * 64
TAMPERED_AUTH = "b" * 64


def _proposal(authorization_commitment: str = VALID_AUTH):
    return SimpleNamespace(
        height=7,
        previous_hash="1" * 64,
        state_root="2" * 64,
        event_root="3" * 64,
        validator_votes=("validator_A", "validator_B", "validator_C"),
        authorization_commitment=authorization_commitment,
    )


def _consensus() -> SignedQuorumCertificate:
    return SignedQuorumCertificate(
        ["validator_A", "validator_B", "validator_C", "validator_D"]
    )


def test_authorization_commitment_changes_proposal_hash():
    consensus = _consensus()
    original = consensus.proposal_hash(_proposal(VALID_AUTH))
    tampered = consensus.proposal_hash(_proposal(TAMPERED_AUTH))
    assert original != tampered


def test_missing_authorization_commitment_cannot_match_bound_proposal():
    consensus = _consensus()
    bound = consensus.proposal_hash(_proposal(VALID_AUTH))
    missing = consensus.proposal_hash(_proposal(""))
    assert bound != missing


def test_changed_commitment_invalidates_existing_proposal_hash():
    consensus = _consensus()
    original_hash = consensus.proposal_hash(_proposal(VALID_AUTH))
    tampered_hash = consensus.proposal_hash(_proposal(TAMPERED_AUTH))
    assert tampered_hash != original_hash


def test_commitment_is_part_of_vote_payload():
    consensus = _consensus()
    first = consensus.proposal_hash(_proposal(VALID_AUTH))
    second = consensus.proposal_hash(_proposal(TAMPERED_AUTH))
    assert consensus.vote_payload(7, 0, first) != consensus.vote_payload(7, 0, second)


def test_other_proposal_fields_cannot_hide_commitment_tampering():
    consensus = _consensus()
    baseline = _proposal(VALID_AUTH)
    tampered = _proposal(TAMPERED_AUTH)
    assert baseline.height == tampered.height
    assert baseline.previous_hash == tampered.previous_hash
    assert baseline.state_root == tampered.state_root
    assert baseline.event_root == tampered.event_root
    assert baseline.validator_votes == tampered.validator_votes
    assert consensus.proposal_hash(baseline) != consensus.proposal_hash(tampered)
