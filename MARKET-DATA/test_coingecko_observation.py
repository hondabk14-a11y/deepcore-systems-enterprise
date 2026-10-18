"""Offline regression tests for the external market observation boundary."""
import hashlib
import json
import unittest
from decimal import Decimal
from unittest.mock import patch

from coingecko_observation import build_observation, canonical_hash, require_api_key


class TestCoinGeckoObservation(unittest.TestCase):
    def build(self, **changes):
        fields = dict(coingecko_id="bitcoin", symbol="btc", name="Bitcoin",
                      price="123.456789012345678901", currency="usd",
                      retrieved_at="2026-09-15T00:00:00+00:00")
        fields.update(changes)
        return build_observation(**fields)

    def test_decimal_precision_survives_serialization(self):
        price = "123.456789012345678901"
        observation = self.build(price=Decimal(price))
        self.assertEqual(observation.price, price)
        self.assertEqual(json.loads(json.dumps(observation.canonical_dict()))["price"], price)

    def test_invalid_prices_fail_closed(self):
        for price in (True, False, -1, "-0.01", "NaN", "Infinity", "-Infinity", "invalid"):
            with self.subTest(price=price), self.assertRaises(ValueError):
                self.build(price=price)

    def test_zero_price_is_valid(self):
        self.assertEqual(self.build(price=0).price, "0")

    def test_missing_identity_is_rejected(self):
        for field in ("coingecko_id", "symbol", "name", "currency"):
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.build(**{field: ""})

    def test_provenance_matches_external_serialization_contract(self):
        observation = self.build()
        expected_payload = {"coingecko_id": "bitcoin", "currency": "usd",
                            "name": "Bitcoin", "price": "123.456789012345678901",
                            "provider": "coingecko",
                            "retrieved_at": "2026-09-15T00:00:00+00:00", "symbol": "btc"}
        digest = hashlib.sha256(json.dumps(expected_payload, sort_keys=True,
                               separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()
        self.assertEqual(observation.canonical_dict(), expected_payload)
        self.assertEqual(observation.provenance_hash, digest)

    def test_provenance_binds_every_observation_field(self):
        original = self.build()
        replacements = dict(coingecko_id="ethereum", symbol="eth", name="Ethereum",
                            price="124", currency="eur",
                            retrieved_at="2026-09-15T00:00:01+00:00")
        for field, value in replacements.items():
            with self.subTest(field=field):
                self.assertNotEqual(original.provenance_hash,
                                    self.build(**{field: value}).provenance_hash)

    def test_hash_is_independent_of_dictionary_order(self):
        self.assertEqual(canonical_hash({"a": 1, "b": 2}),
                         canonical_hash({"b": 2, "a": 1}))

    def test_absent_credentials_fail_closed(self):
        with patch.dict("os.environ", {}, clear=True), self.assertRaises(RuntimeError):
            require_api_key()

    def test_credential_is_read_from_environment(self):
        with patch.dict("os.environ", {"CG_API_KEY": "test-only-placeholder"}, clear=True):
            self.assertEqual(require_api_key(), "test-only-placeholder")


if __name__ == "__main__":
    unittest.main()
