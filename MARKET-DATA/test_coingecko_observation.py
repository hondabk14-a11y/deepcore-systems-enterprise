"""Offline regression tests for the external market observation boundary."""
import unittest
from unittest.mock import patch
from coingecko_observation import build_observation, canonical_hash, require_api_key


class ObservationTests(unittest.TestCase):
    def observation(self, **changes):
        values = dict(coingecko_id="bitcoin", symbol="btc", name="Bitcoin",
                      price="123.4567890123456789", currency="usd",
                      retrieved_at="2026-10-03T00:00:00+00:00")
        values.update(changes)
        return build_observation(**values)

    def test_precision_and_provenance(self):
        item = self.observation()
        self.assertEqual(item.price, "123.4567890123456789")
        self.assertEqual(item.provenance_hash, canonical_hash(item.canonical_dict()))
        self.assertEqual(item, self.observation())

    def test_invalid_prices_rejected(self):
        for price in (True, "NaN", "Infinity", "-1", "invalid"):
            with self.subTest(price=price), self.assertRaises(ValueError):
                self.observation(price=price)

    def test_identity_required(self):
        with self.assertRaises(ValueError):
            self.observation(symbol="")

    def test_credential_required_without_network_calls(self):
        with patch.dict("os.environ", {}, clear=True):
            with self.assertRaises(RuntimeError):
                require_api_key()
