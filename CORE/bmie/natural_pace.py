"""Natural Pace Controller for bounded resource allocation."""
from decimal import Decimal
from .mathematical_state import ResourceState


def natural_pace(state: ResourceState) -> Decimal:
    if state.intervals_remaining <= 0:
        return Decimal("0")
    return state.available / Decimal(state.intervals_remaining)


def variance(actual: Decimal, expected: Decimal) -> Decimal:
    return actual - expected


def bounded_adjustment(value: Decimal, maximum: Decimal) -> Decimal:
    if maximum < 0:
        raise ValueError("maximum adjustment must be non-negative")
    return max(-maximum, min(maximum, value))
