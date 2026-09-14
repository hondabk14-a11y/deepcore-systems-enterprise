"""Deterministic verification boundary for external market observations.

This module compares independently sourced market.price events. A verification
result is evidence about external observations, not an authorization to mutate
DeepCore state.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any

from market_price_event import MarketPriceEvent
from coingecko_observation import canonical_hash


@dataclass(frozen=True)
class MarketVerificationResult:
    result_type: str
    status: str
    asset_id: str
    currency: str
    providers: tuple[str, str]
    relative_difference: str
    tolerance: str
    source_event_hashes: tuple[str, str]
    result_hash: str

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "asset_id": self.asset_id,
            "currency": self.currency,
            "providers": list(self.providers),
            "relative_difference": self.relative_difference,
            "result_type": self.result_type,
            "source_event_hashes": list(self.source_event_hashes),
            "status": self.status,
            "tolerance": self.tolerance,
        }


def _decimal(value: str, field: str) -> Decimal:
    try:
        result = Decimal(value)
    except (InvalidOperation, ValueError):
        raise ValueError(f"{field} must be a finite decimal") from None
    if not result.is_finite() or result < 0:
        raise ValueError(f"{field} must be a finite non-negative decimal")
    return result


def verify_market_prices(
    first: MarketPriceEvent,
    second: MarketPriceEvent,
    *,
    tolerance: str = "0.01",
) -> MarketVerificationResult:
    """Compare two independent market.price events deterministically.

    ``tolerance`` is a fractional relative-difference threshold. The two
    events must describe the same asset/currency and come from different
    providers. No verification result authorizes a financial action.
    """
    if first.event_type != "market.price" or second.event_type != "market.price":
        raise ValueError("verification requires market.price events")
    if first.provider == second.provider:
        raise ValueError("verification requires independent providers")
    if first.asset_id != second.asset_id or first.currency != second.currency:
        raise ValueError("events must reference the same asset and currency")
    if not first.event_hash or not second.event_hash:
        raise ValueError("source event hashes are required")

    threshold = _decimal(tolerance, "tolerance")
    first_price = _decimal(first.price, "first.price")
    second_price = _decimal(second.price, "second.price")

    if max(first_price, second_price) == 0:
        relative_difference = Decimal("0")
    else:
        relative_difference = abs(first_price - second_price) / max(first_price, second_price)

    status = "VERIFIED" if relative_difference <= threshold else "DISCREPANCY"
    providers = (first.provider, second.provider)
    source_event_hashes = (first.event_hash, second.event_hash)
    payload = {
        "asset_id": first.asset_id,
        "currency": first.currency,
        "providers": list(providers),
        "relative_difference": format(relative_difference, "f"),
        "result_type": "verification.result",
        "source_event_hashes": list(source_event_hashes),
        "status": status,
        "tolerance": format(threshold, "f"),
    }
    return MarketVerificationResult(
        result_type=payload["result_type"],
        status=payload["status"],
        asset_id=payload["asset_id"],
        currency=payload["currency"],
        providers=providers,
        relative_difference=payload["relative_difference"],
        tolerance=payload["tolerance"],
        source_event_hashes=source_event_hashes,
        result_hash=canonical_hash(payload),
    )
