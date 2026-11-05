"""Offline checks for the external market observation boundary."""
from decimal import Decimal

import pytest

from coingecko_observation import build_observation, canonical_hash, require_api_key


def observation(**changes):
    fields = dict(coingecko_id="bitcoin", symbol="btc", name="Bitcoin",
                  price="12345.123456789", currency="usd",
                  retrieved_at="2026-09-14T00:00:00+00:00")
    fields.update(changes)
    return build_observation(**fields)


def test_precision_and_reproducible_provenance():
    first = observation(price=Decimal("12345.123456789"))
    assert first.price == "12345.123456789"
    assert first == observation()
    assert first.provenance_hash == canonical_hash(first.canonical_dict())


@pytest.mark.parametrize("price", [True, False, -1, "NaN", "Infinity", "-Infinity", "bad"])
def test_invalid_prices_rejected(price):
    with pytest.raises(ValueError, match="non-negative decimal"):
        observation(price=price)


@pytest.mark.parametrize("field", ["coingecko_id", "symbol", "name", "currency"])
def test_missing_identity_rejected(field):
    with pytest.raises(ValueError, match="non-empty"):
        observation(**{field: ""})


@pytest.mark.parametrize("changes", [
    {"price": "12346"}, {"currency": "eur"},
    {"retrieved_at": "2026-09-15T00:00:00+00:00"},
])
def test_changed_source_fields_change_provenance(changes):
    assert observation().provenance_hash != observation(**changes).provenance_hash


def test_missing_api_key_fails_closed(monkeypatch):
    monkeypatch.delenv("CG_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="CG_API_KEY is required"):
        require_api_key()
