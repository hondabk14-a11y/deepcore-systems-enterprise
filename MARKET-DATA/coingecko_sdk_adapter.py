"""CoinGecko Demo SDK adapter for external market observations.

The adapter only retrieves and validates external observations. It does not
sign, authorize, mutate ledger state, or participate in consensus.
"""

from __future__ import annotations

import os
from typing import Any

from coingecko_sdk import Coingecko

from coingecko_observation import CoinGeckoObservation, build_observation


DEMO_API_KEY_ENV = "COINGECKO_DEMO_API_KEY"


def build_client() -> Coingecko:
    """Build one reusable official CoinGecko Demo client from the environment."""
    api_key = os.environ.get(DEMO_API_KEY_ENV)
    if not api_key:
        raise RuntimeError(f"{DEMO_API_KEY_ENV} is required")
    return Coingecko(
        demo_api_key=api_key,
        environment="demo",
        max_retries=2,
    )


def fetch_bitcoin_usd(*, client: Any | None = None) -> CoinGeckoObservation:
    """Fetch Bitcoin/USD through the official SDK and normalize the result."""
    sdk_client = client or build_client()
    response = sdk_client.simple.price.get(vs_currencies="usd", ids="bitcoin")
    bitcoin = response["bitcoin"] if isinstance(response, dict) else response.bitcoin
    price = bitcoin["usd"] if isinstance(bitcoin, dict) else bitcoin.usd
    return build_observation(
        coingecko_id="bitcoin",
        symbol="btc",
        name="Bitcoin",
        price=price,
        currency="usd",
    )
