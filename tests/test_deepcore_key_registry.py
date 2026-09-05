import pytest

from CORE.deepcore_crypto import Ed25519Identity
from CORE.deepcore_key_registry import ValidatorKeyRegistry


def test_register_and_verify():
    identity = Ed25519Identity.generate()
    registry = ValidatorKeyRegistry()
    record = registry.register("validator_A", identity.public_key_bytes)

    payload = b"deepcore-key-registry-test"
    signature = identity.sign(payload)

    assert record.key_id == identity.key_id
    assert registry.verify("validator_A", payload, signature)


def test_wrong_validator_cannot_verify():
    first = Ed25519Identity.generate()
    second = Ed25519Identity.generate()
    registry = ValidatorKeyRegistry()
    registry.register("validator_A", first.public_key_bytes)
    registry.register("validator_B", second.public_key_bytes)

    signature = first.sign(b"payload")
    assert not registry.verify("validator_B", b"payload", signature)


def test_revoked_key_is_rejected():
    identity = Ed25519Identity.generate()
    registry = ValidatorKeyRegistry()
    registry.register("validator_A", identity.public_key_bytes)
    signature = identity.sign(b"payload")

    registry.revoke("validator_A")

    assert not registry.verify("validator_A", b"payload", signature)
    assert registry.get("validator_A").active is False


def test_rotation_replaces_revoked_key():
    old = Ed25519Identity.generate()
    new = Ed25519Identity.generate()
    registry = ValidatorKeyRegistry()
    registry.register("validator_A", old.public_key_bytes)
    registry.revoke("validator_A")
    rotated = registry.rotate("validator_A", new.public_key_bytes)

    old_signature = old.sign(b"payload")
    new_signature = new.sign(b"payload")

    assert rotated.key_id == new.key_id
    assert not registry.verify("validator_A", b"payload", old_signature)
    assert registry.verify("validator_A", b"payload", new_signature)


def test_duplicate_active_registration_is_rejected():
    identity = Ed25519Identity.generate()
    registry = ValidatorKeyRegistry()
    registry.register("validator_A", identity.public_key_bytes)

    with pytest.raises(ValueError, match="active validator key already exists"):
        registry.register("validator_A", identity.public_key_bytes)
