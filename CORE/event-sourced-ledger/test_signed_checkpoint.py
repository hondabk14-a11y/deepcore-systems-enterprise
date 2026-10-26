import unittest
from types import SimpleNamespace

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from checkpoint import LedgerCheckpoint
from signed_checkpoint import SignatureVerificationError, SignedCheckpoint, verify_signed_checkpoint


class TestSignedCheckpoint(unittest.TestCase):
    def setUp(self):
        self.private_key = Ed25519PrivateKey.generate()
        self.public_key = self.private_key.public_key().public_bytes_raw()
        checkpoint = LedgerCheckpoint("ledger-A", 3, "abc123", 3)
        unsigned = SignedCheckpoint.from_checkpoint(checkpoint, key_id="key-1", signature=b"")
        self.signed = SignedCheckpoint.from_checkpoint(
            checkpoint, key_id="key-1", signature=self.private_key.sign(unsigned.unsigned_bytes())
        )

    def test_valid_signature(self):
        result = verify_signed_checkpoint(
            self.signed,
            key_resolver=SimpleNamespace(resolve=lambda key_id: self.public_key),
            verifier=__import__("ed25519_checkpoint").Ed25519CheckpointVerifier(),
        )
        self.assertEqual(result, self.signed.to_checkpoint())

    def test_tampering_is_rejected(self):
        tampered = SignedCheckpoint("ledger-A", 4, "abc123", 3, "key-1", self.signed.signature)
        with self.assertRaises(SignatureVerificationError):
            verify_signed_checkpoint(tampered, key_resolver=SimpleNamespace(resolve=lambda _: self.public_key),
                                     verifier=__import__("ed25519_checkpoint").Ed25519CheckpointVerifier())

    def test_wrong_key_is_rejected(self):
        wrong = Ed25519PrivateKey.generate().public_key().public_bytes_raw()
        with self.assertRaises(SignatureVerificationError):
            verify_signed_checkpoint(self.signed, key_resolver=SimpleNamespace(resolve=lambda _: wrong),
                                     verifier=__import__("ed25519_checkpoint").Ed25519CheckpointVerifier())


if __name__ == "__main__":
    unittest.main()
