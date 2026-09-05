import unittest

from checkpoint import LedgerCheckpoint
from signed_checkpoint import (
    SignatureVerificationError,
    SignedCheckpoint,
    verify_signed_checkpoint,
)


class FakeResolver:
    def __init__(self, keys):
        self.keys = keys

    def resolve(self, key_id):
        return self.keys.get(key_id)


class FakeVerifier:
    def __init__(self, valid=True):
        self.valid = valid
        self.calls = []

    def verify(self, message, signature, public_key):
        self.calls.append((message, signature, public_key))
        return self.valid


class TestSignedCheckpoint(unittest.TestCase):
    def _signed(self):
        checkpoint = LedgerCheckpoint(
            ledger_id="ledger-A",
            sequence=3,
            head_hash="abc123",
            event_count=3,
        )
        return SignedCheckpoint.from_checkpoint(
            checkpoint,
            key_id="key-1",
            signature=b"signature",
        )

    def test_valid_signature_returns_authenticated_checkpoint(self):
        signed = self._signed()
        resolver = FakeResolver({"key-1": b"public-key"})
        verifier = FakeVerifier()

        result = verify_signed_checkpoint(
            signed, key_resolver=resolver, verifier=verifier
        )

        self.assertEqual(result, signed.to_checkpoint())
        self.assertEqual(verifier.calls[0][1], b"signature")
        self.assertEqual(verifier.calls[0][2], b"public-key")

    def test_invalid_signature_is_rejected(self):
        signed = self._signed()
        with self.assertRaises(SignatureVerificationError):
            verify_signed_checkpoint(
                signed,
                key_resolver=FakeResolver({"key-1": b"public-key"}),
                verifier=FakeVerifier(valid=False),
            )

    def test_unknown_key_is_rejected(self):
        with self.assertRaises(SignatureVerificationError):
            verify_signed_checkpoint(
                self._signed(),
                key_resolver=FakeResolver({}),
                verifier=FakeVerifier(),
            )

    def test_signature_covers_canonical_identity_and_checkpoint_fields(self):
        signed = self._signed()
        verifier = FakeVerifier()
        verify_signed_checkpoint(
            signed,
            key_resolver=FakeResolver({"key-1": b"public-key"}),
            verifier=verifier,
        )
        message = verifier.calls[0][0]
        self.assertEqual(
            message,
            b'{"event_count":3,"head_hash":"abc123","key_id":"key-1","ledger_id":"ledger-A","sequence":3}',
        )

    def test_missing_identity_is_rejected(self):
        signed = SignedCheckpoint(
            ledger_id="",
            sequence=1,
            head_hash="abc",
            event_count=1,
            key_id="key-1",
            signature=b"signature",
        )
        with self.assertRaises(SignatureVerificationError):
            verify_signed_checkpoint(
                signed,
                key_resolver=FakeResolver({"key-1": b"public-key"}),
                verifier=FakeVerifier(),
            )


if __name__ == "__main__":
    unittest.main()
