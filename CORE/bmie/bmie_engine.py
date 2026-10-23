"""BMIE v0.1 orchestration. AI proposals never become authoritative by themselves."""
from dataclasses import dataclass
from decimal import Decimal
from .mathematical_state import ResourceState
from .natural_pace import natural_pace
from .falsification_engine import all_pass, run_resource_checks, transition_rejects_invalid
from .evidence_commitment import evidence_root


@dataclass(frozen=True)
class VerificationResult:
    status: str
    state_root: str
    evidence_root: str
    expected_pace: Decimal
    checks: dict[str, bool]


def verify_transition(state: ResourceState, consumption: Decimal) -> VerificationResult:
    expected = natural_pace(state)
    next_state = state.transition(consumption)
    checks = run_resource_checks(next_state)
    checks.update(transition_rejects_invalid(next_state))
    status = "VERIFIED" if all_pass(checks) else "TESTED"
    evidence = evidence_root(
        inputs={"state_root": state.state_root(), "consumption": str(consumption)},
        computation={"algorithm": "BMIE-NATURAL-PACE-v0.1", "expected_pace": str(expected)},
        outputs={"state_root": next_state.state_root()},
        tests=checks,
    )
    return VerificationResult(status, next_state.state_root(), evidence, expected, checks)
