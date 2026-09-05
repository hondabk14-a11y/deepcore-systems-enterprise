from __future__ import annotations

import pytest

from CORE.deepcore_crypto import Ed25519Identity
from CORE.deepcore_key_registry import ValidatorKeyRegistry
from CORE.deepcore_transport import AuthenticatedTransport, ConsensusMessage


VALIDATORS = ["validator_A", "validator_B", "validator_C", "validator_D"]


def setup():
    identities = {v: Ed25519Identity.generate() for v in VALIDATORS}
    registry = ValidatorKeyRegistry()
    for v, identity in identities.items():
        registry.register(v, identity.public_key_bytes)
    return AuthenticatedTransport(VALIDATORS, registry, identities), registry, identities


def test_authenticated_delivery_and_sequence():
    transport, _, _ = setup()
    first = transport.send("validator_A", "validator_B", 0, "PROPOSE", {"proposal": "abc"})
    second = transport.send("validator_A", "validator_C", 0, "PREPARE", {"proposal": "abc"})
    assert first.sequence == 1
    assert second.sequence == 2
    assert transport.verify(first, 0)
    assert transport.receive("validator_B", 0) == first
    assert transport.receive("validator_C", 0) == second
    assert transport.pending() == ()


def test_tampering_is_rejected():
    transport, _, _ = setup()
    message = transport.send("validator_A", "validator_B", 0, "PROPOSE", {"proposal": "abc"})
    tampered = ConsensusMessage(message.sender, message.recipient, message.view, message.sequence, message.kind, {"proposal": "evil"}, message.signature)
    assert not transport.verify(tampered, 0)


def test_stale_view_is_rejected():
    transport, _, _ = setup()
    transport.send("validator_A", "validator_B", 0, "PROPOSE", {})
    with pytest.raises(ValueError, match="invalid or stale"):
        transport.receive("validator_B", 1)


def test_replay_sequence_is_rejected():
    transport, _, _ = setup()
    message = transport.send("validator_A", "validator_B", 0, "PROPOSE", {})
    transport.receive("validator_B", 0)
    assert not transport.verify(message, 0)


def test_revoked_sender_is_rejected():
    transport, registry, _ = setup()
    message = transport.send("validator_A", "validator_B", 0, "PROPOSE", {})
    registry.revoke("validator_A")
    assert not transport.verify(message, 0)


def test_unknown_participant_rejected():
    transport, _, _ = setup()
    with pytest.raises(ValueError, match="unknown transport participant"):
        transport.send("validator_X", "validator_B", 0, "PROPOSE", {})
