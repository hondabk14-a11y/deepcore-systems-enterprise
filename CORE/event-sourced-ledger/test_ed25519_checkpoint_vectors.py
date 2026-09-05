import unittest

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from ed25519_checkpoint import Ed25519CheckpointVerifier


class TestEd25519CheckpointVectors(unittest.TestCase):
    def test_known_rfc8032_vector(self):
        public_key = bytes.fromhex(
            "d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a"
        )
        message = b""
        signature = bytes.fromhex(
            "e5564300c360ac729086e2cc806e828a84877f1eb8e5d974d873e06522490155"
            "5fb8821590a33bacc61e39701cf9b46bd25bf5f0595bbe24655141438e7a100b"
        )
        self.assertTrue(
            Ed25519CheckpointVerifier().verify(message, signature, public_key)
        )

    def test_private_key_signing_round_trip(self):
        private_key = Ed25519PrivateKey.from_private_bytes(bytes(range(32)))
        public_key = private_key.public_key().public_bytes_raw()
        message = b"deepcore-ed25519-checkpoint"
        signature = private_key.sign(message)
        self.assertTrue(
            Ed25519CheckpointVerifier().verify(message, signature, public_key)
        )


if __name__ == "__main__":
    unittest.main()
