from decimal import Decimal

from CORE.bmie import ResourceState, natural_pace, verify_transition


def budget_state():
    # Exact monthly reference: 2150 = 1976.29 allocated + 173.71 reserve.
    return ResourceState(
        initial=Decimal("2150.00"),
        available=Decimal("1976.29"),
        consumed=Decimal("0.00"),
        reserve=Decimal("173.71"),
        intervals_remaining=30,
    )


def test_exact_budget_conservation():
    assert budget_state().verify_conservation()


def test_natural_pace_is_deterministic():
    state = budget_state()
    assert natural_pace(state) == Decimal("1976.29") / Decimal(30)


def test_transition_preserves_conservation():
    state = budget_state().transition(Decimal("50.00"))
    assert state.verify_conservation()
    assert state.available == Decimal("1926.29")
    assert state.consumed == Decimal("50.00")


def test_bmie_0001_1000_identical_replays():
    roots = set()
    evidence = set()
    for _ in range(1000):
        result = verify_transition(budget_state(), Decimal("50.00"))
        assert result.status == "VERIFIED"
        roots.add(result.state_root)
        evidence.add(result.evidence_root)
    assert len(roots) == 1
    assert len(evidence) == 1
