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


def test_authorization_commitment_changes_proposal_hash():
    consensus = SignedQuorumCertificate(["validator_A", "validator_B", "validator_C", "validator_D"])
    original = consensus.proposal_hash(_proposal(VALID_AUTH))
    tampered = consensus.proposal_hash(_proposal(TAMPERED_AUTH))
    assert original != tampered


def test_missing_authorization_commitment_cannot_match_bound_proposal():
    consensus = SignedQuorumCertificate(["validator_A", "validator_B", "validator_C", "validator_D"])
    bound = consensus.proposal_hash(_proposal(VALID_AUTH))
    missing = consensus.proposal_hash(_proposal(""))
    assert bound != missing


def test_changed_commitment_invalidates_existing_proposal_hash():
    consensus = SignedQuorumCertificate(["validator_A", "validator_B", "validator_C", "validator_D"])
    proposal = _proposal(VALID_AUTH)
    signed_proposal_hash = consensus.proposal_hash(proposal)
    proposal.authorization_commitment = TAMPERED_AUTH
    assert consensus.proposal_hash(proposal) != signed_proposal_hash


def test_commitment_is_part_of_vote_payload():
    consensus = SignedQuorumCertificate(["validator_A", "validator_B", "validator_C", "validator_D"])
    first = consensus.proposal_hash(_proposal(VALID_AUTH))
    second = consensus.proposal_hash(_proposal(TAMPERED_AUTH))
    assert consensus.vote_payload(7, 0, first) != consensus.vote_payload(7, 0, second)
