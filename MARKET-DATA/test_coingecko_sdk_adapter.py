from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


MODULE_PATH = Path(__file__).with_name("coingecko_sdk_adapter.py")
SPEC = importlib.util.spec_from_file_location("coingecko_sdk_adapter", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class FakePriceEndpoint:
    def __init__(self, payload):
        self.payload = payload

    def get(self, **kwargs):
        assert kwargs == {"vs_currencies": "usd", "ids": "bitcoin"}
        return self.payload


class FakeSimple:
    def __init__(self, payload):
        self.price = FakePriceEndpoint(payload)


class FakeClient:
    def __init__(self, payload):
        self.simple = FakeSimple(payload)


def test_fetch_bitcoin_usd_normalizes_sdk_dict_response():
    observation = MODULE.fetch_bitcoin_usd(
        client=FakeClient({"bitcoin": {"usd": "105432.123456"}})
    )

    assert observation.provider == "coingecko"
    assert observation.coingecko_id == "bitcoin"
    assert observation.price == "105432.123456"
    assert len(observation.provenance_hash) == 64


def test_build_client_requires_demo_credential(monkeypatch):
    monkeypatch.delenv(MODULE.DEMO_API_KEY_ENV, raising=False)

    with pytest.raises(RuntimeError, match="COINGECKO_DEMO_API_KEY is required"):
        MODULE.build_client()


def test_build_client_uses_demo_environment(monkeypatch):
    monkeypatch.setenv(MODULE.DEMO_API_KEY_ENV, "test-only-not-a-real-key")

    class FakeCoingecko:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    monkeypatch.setattr(MODULE, "Coingecko", FakeCoingecko)
    client = MODULE.build_client()

    assert client.kwargs == {
        "demo_api_key": "test-only-not-a-real-key",
        "environment": "demo",
        "max_retries": 2,
    }
