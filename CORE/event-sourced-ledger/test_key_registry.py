import unittest

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from key_registry import InMemoryKeyRegistry, KeyRecord, KeyRegistryError


class TestInMemoryKeyRegistry(unittest.TestCase):
    def setUp(self):
        self.public_key = Ed25519PrivateKey.generate().public_key().public_bytes_raw()
        self.registry = InMemoryKeyRegistry(
            {"key-1": KeyRecord("key-1", self.public_key)}
        )

    def test_active_key_resolves(self):
        self.assertEqual(self.registry.resolve("key-1"), self.public_key)

    def test_unknown_key_does_not_resolve(self):
        self.assertIsNone(self.registry.resolve("missing"))

    def test_revoked_key_does_not_resolve(self):
        self.registry.revoke("key-1")
        self.assertIsNone(self.registry.resolve("key-1"))

    def test_unknown_revoke_is_rejected(self):
        with self.assertRaises(KeyRegistryError):
            self.registry.revoke("missing")

    def test_invalid_public_key_length_is_rejected(self):
        with self.assertRaises(KeyRegistryError):
            KeyRecord("bad", b"short")

    def test_invalid_status_is_rejected(self):
        with self.assertRaises(KeyRegistryError):
            KeyRecord("bad", self.public_key, status="unknown")


if __name__ == "__main__":
    unittest.main()
