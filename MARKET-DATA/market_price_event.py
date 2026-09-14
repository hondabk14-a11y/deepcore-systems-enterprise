"""Canonical market.price event contract for external observations.

This module converts a validated external observation into a deterministic
DeepCore event payload. Provider-specific validation belongs in the upstream
adapter. This layer does not authorize commands, sign transactions,
participate in consensus, or mutate authoritative ledger state.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from coingecko_observation import CoinGeckoObservation, canonical_hash


@dataclass(frozen=True)
class MarketPriceEvent:
    """Immutable canonical representation of one external price observation."""

    event_type: str
    provider: str
    asset_id: str
    symbol: str
    price: str
    currency: str
    observed_at: str
    provenance_hash: str
    event_hash: str

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "asset_id": self.asset_id,
            "currency": self.currency,
            "event_type": self.event_type,
            "observed_at": self.observed_at,
            "price": self.price,
            "provider": self.provider,
            "provenance_hash": self.provenance_hash,
            "symbol": self.symbol,
        }


def build_market_price_event(observation: CoinGeckoObservation) -> MarketPriceEvent:
    """Convert a validated external observation into a deterministic event."""
    if not observation.provider or not isinstance(observation.provider, str):
        raise ValueError("observation provider is required")
    if not observation.provenance_hash:
        raise ValueError("observation provenance_hash is required")

    payload = {
        "asset_id": observation.coingecko_id,
        "currency": observation.currency,
        "event_type": "market.price",
        "observed_at": observation.retrieved_at,
        "price": observation.price,
        "provider": observation.provider,
        "provenance_hash": observation.provenance_hash,
        "symbol": observation.symbol,
    }
    return MarketPriceEvent(
        **payload,
        event_hash=canonical_hash(payload),
    )
