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
            "d60feaeb9e2e22153b8f543b2a2eb6d7c496b46aa0f38af98d75c005ac01522b",
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
