from CORE.deepcore_crypto import Ed25519Identity, key_id, verify


def test_ed25519_sign_and_verify():
    identity = Ed25519Identity.generate()
    payload = b"deepcore:test:transaction:v1"
    signature = identity.sign(payload)

    assert identity.verify(payload, signature)
    assert verify(identity.public_key_bytes, payload, signature)
    assert len(identity.public_key_bytes) == 32
    assert len(identity.key_id) == 64


def test_modified_payload_rejected():
    identity = Ed25519Identity.generate()
    signature = identity.sign(b"original")

    assert not identity.verify(b"modified", signature)


def test_wrong_key_rejected():
    signer = Ed25519Identity.generate()
    other = Ed25519Identity.generate()
    signature = signer.sign(b"payload")

    assert not other.verify(b"payload", signature)


def test_signature_tampering_rejected():
    identity = Ed25519Identity.generate()
    signature = identity.sign(b"payload")
    replacement = ("A" if signature[0] != "A" else "B") + signature[1:]

    assert not identity.verify(b"payload", replacement)


def test_key_id_is_sha256_public_key_fingerprint():
    identity = Ed25519Identity.generate()
    assert identity.key_id == key_id(identity.public_key_bytes)


def test_private_key_round_trip():
    identity = Ed25519Identity.generate()
    restored = Ed25519Identity.from_private_bytes(identity.private_key_bytes)

    assert restored.public_key_bytes == identity.public_key_bytes
    assert restored.key_id == identity.key_id
    assert restored.verify(b"round-trip", restored.sign(b"round-trip"))


def test_malformed_signature_rejected():
    identity = Ed25519Identity.generate()
    assert not identity.verify(b"payload", "not-a-signature")
