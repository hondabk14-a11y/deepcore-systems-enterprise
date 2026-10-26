import unittest
from types import SimpleNamespace

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from checkpoint import LedgerCheckpoint
from ed25519_checkpoint import Ed25519CheckpointVerifier
from signed_checkpoint import SignatureVerificationError, SignedCheckpoint, verify_signed_checkpoint


class TestEd25519CheckpointVerifier(unittest.TestCase):
    def setUp(self):
        self.private_key = Ed25519PrivateKey.generate()
        self.public_key = self.private_key.public_key().public_bytes_raw()
        checkpoint = LedgerCheckpoint(
            ledger_id="ledger-A",
            sequence=7,
            head_hash="abc123",
            event_count=7,
        )
        unsigned = SignedCheckpoint.from_checkpoint(
            checkpoint,
            key_id="key-1",
            signature=b"placeholder",
        )
        signature = self.private_key.sign(unsigned.unsigned_bytes())
        self.signed = SignedCheckpoint.from_checkpoint(
            checkpoint,
            key_id="key-1",
            signature=signature,
        )

    def test_real_ed25519_signature_verifies(self):
        result = verify_signed_checkpoint(
            self.signed,
            key_resolver=SimpleNamespace(resolve=lambda key_id: self.public_key),
            verifier=Ed25519CheckpointVerifier(),
        )
        self.assertEqual(result, self.signed.to_checkpoint())

    def test_tampered_checkpoint_is_rejected(self):
        tampered = SignedCheckpoint(
            ledger_id=self.signed.ledger_id,
            sequence=self.signed.sequence + 1,
            head_hash=self.signed.head_hash,
            event_count=self.signed.event_count,
            key_id=self.signed.key_id,
            signature=self.signed.signature,
        )
        with self.assertRaises(SignatureVerificationError):
            verify_signed_checkpoint(
                tampered,
                key_resolver=SimpleNamespace(resolve=lambda key_id: self.public_key),
                verifier=Ed25519CheckpointVerifier(),
            )

    def test_wrong_public_key_is_rejected(self):
        wrong_public_key = Ed25519PrivateKey.generate().public_key().public_bytes_raw()
        with self.assertRaises(SignatureVerificationError):
            verify_signed_checkpoint(
                self.signed,
                key_resolver=SimpleNamespace(resolve=lambda key_id: wrong_public_key),
                verifier=Ed25519CheckpointVerifier(),
            )

    def test_malformed_signature_is_rejected(self):
        malformed = SignedCheckpoint(
            ledger_id=self.signed.ledger_id,
            sequence=self.signed.sequence,
            head_hash=self.signed.head_hash,
            event_count=self.signed.event_count,
            key_id=self.signed.key_id,
            signature=b"bad",
        )
        with self.assertRaises(SignatureVerificationError):
            verify_signed_checkpoint(
                malformed,
                key_resolver=SimpleNamespace(resolve=lambda key_id: self.public_key),
                verifier=Ed25519CheckpointVerifier(),
            )


if __name__ == "__main__":
    unittest.main()
