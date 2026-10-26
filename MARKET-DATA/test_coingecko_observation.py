"""Offline observation-boundary regressions required by DeepCore CI."""
from decimal import Decimal

import pytest

from coingecko_observation import build_observation, canonical_hash, require_api_key


def build(**overrides):
    fields = dict(coingecko_id='bitcoin', symbol='btc', name='Bitcoin',
                  price=Decimal('123.4567890123456789'), currency='usd',
                  retrieved_at='2026-01-01T00:00:00+00:00')
    return build_observation(**(fields | overrides))


def test_observation_preserves_precision_and_binds_provenance():
    observation = build()
    assert observation.price == '123.4567890123456789'
    assert observation.provider == 'coingecko'
    assert observation == build()
    assert observation.provenance_hash == canonical_hash(observation.canonical_dict())
    assert observation.provenance_hash != build(price='124').provenance_hash


@pytest.mark.parametrize('price', [-1, True, 'NaN', 'Infinity', 'invalid'])
def test_invalid_price_rejected(price):
    with pytest.raises(ValueError):
        build(price=price)


@pytest.mark.parametrize('field', ['coingecko_id', 'symbol', 'name', 'currency'])
def test_empty_identity_rejected(field):
    with pytest.raises(ValueError):
        build(**{field: ''})


def test_missing_credential_rejected(monkeypatch):
    monkeypatch.delenv('CG_API_KEY', raising=False)
    with pytest.raises(RuntimeError, match='CG_API_KEY is required'):
        require_api_key()
