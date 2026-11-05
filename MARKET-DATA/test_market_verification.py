"""Tests for deterministic cross-provider market verification."""

from __future__ import annotations


import pytest


import coingecko_observation as observation_module
import market_price_event as event_module
import market_verification as verification_module


build_observation = observation_module.build_observation
build_market_price_event = event_module.build_market_price_event
verify_market_prices = verification_module.verify_market_prices


def _event(provider: str, price: str):
    observation = build_observation(
        coingecko_id="bitcoin",
        symbol="btc",
        name="Bitcoin",
        price=price,
        currency="usd",
        retrieved_at="2026-09-14T00:00:00+00:00",
    )
    if provider == "coingecko":
        return build_market_price_event(observation)
    # Synthetic independent-provider event, not a live provider integration.
    source = {**observation.canonical_dict(), "provider": provider}
    payload = dict(event_type="market.price", provider=provider,
                   asset_id="bitcoin", symbol="btc", price=price, currency="usd",
                   observed_at=observation.retrieved_at,
                   provenance_hash=observation_module.canonical_hash(source))
    return event_module.MarketPriceEvent(
        **payload, event_hash=observation_module.canonical_hash(payload))


def test_coingecko_adapter_rejects_other_provider():
    from dataclasses import replace
    observation = build_observation(coingecko_id="bitcoin", symbol="btc",
                                    name="Bitcoin", price="100", currency="usd")
    with pytest.raises(ValueError, match="requires a CoinGecko observation"):
        build_market_price_event(replace(observation, provider="arkham"))


def test_matching_independent_observations_are_verified() -> None:
    result = verify_market_prices(_event("coingecko", "100000"), _event("arkham", "100500"))
    assert result.status == "VERIFIED"
    assert result.result_type == "verification.result"
    assert result.result_hash


def test_material_price_divergence_is_preserved_as_discrepancy() -> None:
    result = verify_market_prices(_event("coingecko", "100000"), _event("arkham", "120000"))
    assert result.status == "DISCREPANCY"
    assert result.relative_difference == "0.1666666666666666666666666667"


def test_same_provider_is_rejected() -> None:
    with pytest.raises(ValueError, match="independent providers"):
        verify_market_prices(_event("coingecko", "100000"), _event("coingecko", "100001"))


def test_mismatched_asset_is_rejected() -> None:
    first = _event("coingecko", "100000")
    second = _event("arkham", "100000")
    second = second.__class__(**{**second.__dict__, "asset_id": "ethereum"})
    with pytest.raises(ValueError, match="same asset and currency"):
        verify_market_prices(first, second)


def test_mismatched_currency_is_rejected() -> None:
    first = _event("coingecko", "100000")
    second = _event("arkham", "100000")
    second = second.__class__(**{**second.__dict__, "currency": "eur"})
    with pytest.raises(ValueError, match="same asset and currency"):
        verify_market_prices(first, second)


def test_invalid_price_is_rejected() -> None:
    first = _event("coingecko", "100000")
    second = first.__class__(**{**first.__dict__, "provider": "arkham", "price": "NaN"})
    with pytest.raises(ValueError, match="finite non-negative decimal"):
        verify_market_prices(first, second)


def test_result_hash_is_deterministic_and_source_hashes_are_preserved() -> None:
    first = _event("coingecko", "100000")
    second = _event("arkham", "100500")
    a = verify_market_prices(first, second)
    b = verify_market_prices(first, second)
    assert a.result_hash == b.result_hash
    assert a.source_event_hashes == (first.event_hash, second.event_hash)

