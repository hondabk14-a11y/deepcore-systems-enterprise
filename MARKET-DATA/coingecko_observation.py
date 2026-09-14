"""CoinGecko external-observation boundary for DeepCore.

This module deliberately stops at a validated external observation. It does
not authorize commands, sign transactions, or mutate authoritative ledger
state.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from typing import Any


@dataclass(frozen=True)
class CoinGeckoObservation:
    provider: str
    coingecko_id: str
    symbol: str
    name: str
    price: int
    currency: str
    retrieved_at: str
    provenance_hash: str

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "coingecko_id": self.coingecko_id,
            "currency": self.currency,
            "name": self.name,
            "price": self.price,
            "provider": self.provider,
            "retrieved_at": self.retrieved_at,
            "symbol": self.symbol,
        }


def canonical_hash(payload: dict[str, Any]) -> str:
    """Return the SHA-256 digest of deterministic JSON serialization."""
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def build_observation(
    *,
    coingecko_id: str,
    symbol: str,
    name: str,
    price: int,
    currency: str,
    retrieved_at: str | None = None,
) -> CoinGeckoObservation:
    """Build a validated observation from an already retrieved SDK result.

    Prices are represented as integer minor units by the caller so the
    canonical event is deterministic and does not depend on floating-point
    serialization.
    """
    if not coingecko_id or not symbol or not name or not currency:
        raise ValueError("asset identity fields must be non-empty")
    if isinstance(price, bool) or not isinstance(price, int) or price < 0:
        raise ValueError("price must be a non-negative integer")

    timestamp = retrieved_at or datetime.now(timezone.utc).isoformat()
    payload = {
        "coingecko_id": coingecko_id,
        "currency": currency,
        "name": name,
        "price": price,
        "provider": "coingecko",
        "retrieved_at": timestamp,
        "symbol": symbol,
    }
    return CoinGeckoObservation(
        **payload,
        provenance_hash=canonical_hash(payload),
    )


def require_api_key() -> str:
    """Require a CoinGecko credential from the process environment."""
    key = os.environ.get("CG_API_KEY")
    if not key:
        raise RuntimeError("CG_API_KEY is required")
    return key
