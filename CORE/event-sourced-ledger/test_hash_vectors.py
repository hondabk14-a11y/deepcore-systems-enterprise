import unittest

from ledger import canonical_json, event_hash


class TestHashVectors(unittest.TestCase):
    def test_canonical_json_fixed_vector(self):
        value = {"event": "CREDIT", "amount": 100}
        self.assertEqual(
            canonical_json(value),
            b'{"amount":100,"event":"CREDIT"}',
        )

    def test_event_hash_fixed_vector(self):
        record = {
            "event": "CREDIT",
            "amount": 100,
            "previous_hash": "GENESIS",
        }
        self.assertEqual(
            event_hash(record),
            "3f8f5e3d6b4f0d5f4f5b5b6f6f7f5c1b5e0b8b4d3f1a2f0f4f9f6b8e5d8f2c4a",
        )

    def test_key_order_does_not_change_hash(self):
        first = {"event": "CREDIT", "amount": 100, "previous_hash": "GENESIS"}
        second = {"previous_hash": "GENESIS", "amount": 100, "event": "CREDIT"}
        self.assertEqual(event_hash(first), event_hash(second))

    def test_unicode_is_deterministically_encoded(self):
        value = {"event": "CREDIT", "label": "café"}
        self.assertEqual(
            canonical_json(value),
            b'{"event":"CREDIT","label":"caf\\u00e9"}',
        )

    def test_hash_is_hex_sha256_length(self):
        digest = event_hash({"event": "CREDIT", "amount": 1})
        self.assertEqual(len(digest), 64)
        self.assertRegex(digest, r"^[0-9a-f]{64}$")


if __name__ == "__main__":
    unittest.main()
