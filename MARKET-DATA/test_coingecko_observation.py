"""Meaningful deterministic tests for the CoinGecko observation boundary."""

from __future__ import annotations

from decimal import Decimal
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch


MODULE_PATH = Path(__file__).with_name("coingecko_observation.py")
SPEC = importlib.util.spec_from_file_location("coingecko_observation", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class CoinGeckoObservationTests(unittest.TestCase):
    def test_identical_inputs_produce_identical_hashes(self) -> None:
        kwargs = {
            "coingecko_id": "bitcoin",
            "symbol": "BTC",
            "name": "Bitcoin",
            "price": Decimal("105432.12345678"),
            "currency": "usd",
            "retrieved_at": "2026-09-14T15:00:00+00:00",
        }
        first = MODULE.build_observation(**kwargs)
        second = MODULE.build_observation(**kwargs)

        self.assertEqual(first.canonical_dict(), second.canonical_dict())
        self.assertEqual(first.provenance_hash, second.provenance_hash)

    def test_decimal_price_is_canonicalized_without_float_rounding(self) -> None:
        observation = MODULE.build_observation(
            coingecko_id="bitcoin",
            symbol="BTC",
            name="Bitcoin",
            price=Decimal("105432.12345678"),
            currency="usd",
            retrieved_at="2026-09-14T15:00:00+00:00",
        )
        self.assertEqual(observation.price, "105432.12345678")

    def test_asset_identity_is_required(self) -> None:
        with self.assertRaises(ValueError):
            MODULE.build_observation(
                coingecko_id="",
                symbol="BTC",
                name="Bitcoin",
                price=100,
                currency="usd",
                retrieved_at="2026-09-14T15:00:00+00:00",
            )

    def test_negative_price_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            MODULE.build_observation(
                coingecko_id="bitcoin",
                symbol="BTC",
                name="Bitcoin",
                price=Decimal("-1"),
                currency="usd",
                retrieved_at="2026-09-14T15:00:00+00:00",
            )

    def test_boolean_price_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            MODULE.build_observation(
                coingecko_id="bitcoin",
                symbol="BTC",
                name="Bitcoin",
                price=True,
                currency="usd",
                retrieved_at="2026-09-14T15:00:00+00:00",
            )

    def test_non_finite_price_is_rejected(self) -> None:
        for value in ("NaN", "Infinity", "-Infinity"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    MODULE.build_observation(
                        coingecko_id="bitcoin",
                        symbol="BTC",
                        name="Bitcoin",
                        price=value,
                        currency="usd",
                        retrieved_at="2026-09-14T15:00:00+00:00",
                    )

    def test_canonical_hash_is_key_order_independent(self) -> None:
        first = {"b": 2, "a": 1}
        second = {"a": 1, "b": 2}
        self.assertEqual(MODULE.canonical_hash(first), MODULE.canonical_hash(second))

    def test_missing_api_key_fails_closed(self) -> None:
        with patch.dict("os.environ", {}, clear=True):
            with self.assertRaises(RuntimeError):
                MODULE.require_api_key()

    def test_api_key_is_read_from_environment(self) -> None:
        with patch.dict("os.environ", {"CG_API_KEY": "test-only-not-a-real-key"}):
            self.assertEqual(MODULE.require_api_key(), "test-only-not-a-real-key")


if __name__ == "__main__":
    unittest.main()
