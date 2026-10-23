"""Falsification checks. BMIE tries to break claims before verifying them."""
from decimal import Decimal
from .mathematical_state import ResourceState


def run_resource_checks(state: ResourceState) -> dict[str, bool]:
    checks = {
        "conservation": state.verify_conservation(),
        "non_negative_available": state.available >= 0,
        "non_negative_consumed": state.consumed >= 0,
        "non_negative_reserve": state.reserve >= 0,
        "non_negative_intervals": state.intervals_remaining >= 0,
    }
    return checks


def transition_rejects_invalid(state: ResourceState) -> dict[str, bool]:
    results = {}
    try:
        state.transition(Decimal("-1"))
        results["reject_negative"] = False
    except ValueError:
        results["reject_negative"] = True
    try:
        state.transition(state.available + Decimal("0.01"))
        results["reject_over_capacity"] = False
    except ValueError:
        results["reject_over_capacity"] = True
    return results


def all_pass(checks: dict[str, bool]) -> bool:
    return bool(checks) and all(checks.values())
