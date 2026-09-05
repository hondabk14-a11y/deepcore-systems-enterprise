from __future__ import annotations

import unittest

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from authenticated_freshness import AuthenticatedFreshnessBoundary, AuthenticatedFreshnessError
from checkpoint import LedgerCheckpoint
from key_registry import InMemoryKeyRegistry, KeyRecord
from signed_checkpoint import SignedCheckpoint
from ed25519_checkpoint import Ed25519CheckpointVerifier


class TestAuthenticatedFreshness(unittest.TestCase):
    def setUp(self):
        self.private = Ed25519PrivateKey.generate()
        self.public = self.private.public_key().public_bytes_raw()
        self.registry = InMemoryKeyRegistry({"key-1": KeyRecord("key-1", self.public)})
        self.boundary = AuthenticatedFreshnessBoundary(
            ledger_id="ledger-A",
            key_resolver=self.registry,
            verifier=Ed25519CheckpointVerifier(),
        )

    def signed(self, sequence: int, head: str) -> SignedCheckpoint:
        checkpoint = LedgerCheckpoint("ledger-A", sequence, head, sequence)
        unsigned = SignedCheckpoint.from_checkpoint(checkpoint, key_id="key-1", signature=b"")
        return SignedCheckpoint.from_checkpoint(
            checkpoint, key_id="key-1", signature=self.private.sign(unsigned.unsigned_bytes())
        )

    def test_valid_newer_checkpoint_advances_freshness(self):
        self.assertEqual(self.boundary.accept(self.signed(1, "a" * 64)).sequence, 1)
        self.assertEqual(self.boundary.accept(self.signed(2, "b" * 64)).sequence, 2)

    def test_tampered_signature_cannot_advance_state(self):
        valid = self.signed(2, "b" * 64)
        tampered = SignedCheckpoint("ledger-A", 3, "c" * 64, 3, "key-1", valid.signature)
        with self.assertRaises(AuthenticatedFreshnessError):
            self.boundary.accept(tampered)
        self.assertIsNone(self.boundary.policy.accepted)

    def test_wrong_ledger_cannot_advance_state(self):
        checkpoint = LedgerCheckpoint("ledger-B", 1, "a" * 64, 1)
        unsigned = SignedCheckpoint.from_checkpoint(checkpoint, key_id="key-1", signature=b"")
        signed = SignedCheckpoint.from_checkpoint(
            checkpoint, key_id="key-1", signature=self.private.sign(unsigned.unsigned_bytes())
        )
        with self.assertRaises(AuthenticatedFreshnessError):
            self.boundary.accept(signed)
        self.assertIsNone(self.boundary.policy.accepted)

    def test_revoked_key_cannot_advance_state(self):
        self.registry.revoke("key-1")
        with self.assertRaises(AuthenticatedFreshnessError):
            self.boundary.accept(self.signed(1, "a" * 64))
        self.assertIsNone(self.boundary.policy.accepted)


if __name__ == "__main__":
    unittest.main()
