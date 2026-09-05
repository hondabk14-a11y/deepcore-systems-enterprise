import pytest

from TREASURY.UST.ust_settlement import SettlementState, USTSettlementNode


def test_full_settlement_lifecycle_is_deterministic():
    node = USTSettlementNode()
    states = [
        SettlementState.CREATED,
        SettlementState.VALIDATED,
        SettlementState.BROADCAST_ATTEMPTED,
        SettlementState.MEMPOOL_ACCEPTED,
        SettlementState.CONFIRMED,
    ]
    for state in states:
        node.apply("tx-001", state)

    assert node.state("tx-001") is SettlementState.CONFIRMED
    assert [event.sequence for event in node.history("tx-001")] == [1, 2, 3, 4, 5]


def test_settlement_cannot_skip_validation():
    node = USTSettlementNode()
    node.apply("tx-002", SettlementState.CREATED)
    with pytest.raises(ValueError):
        node.apply("tx-002", SettlementState.BROADCAST_ATTEMPTED)


def test_confirmed_settlement_cannot_advance_or_reject():
    node = USTSettlementNode()
    for state in (
        SettlementState.CREATED,
        SettlementState.VALIDATED,
        SettlementState.BROADCAST_ATTEMPTED,
        SettlementState.MEMPOOL_ACCEPTED,
        SettlementState.CONFIRMED,
    ):
        node.apply("tx-003", state)
    with pytest.raises(ValueError):
        node.apply("tx-003", SettlementState.REJECTED)


def test_identity_profile():
    assert USTSettlementNode.NODE_ID == "0001"
    assert USTSettlementNode.LOGICAL_NAME == "UST-0001"
    assert USTSettlementNode.CONSENSUS_WEIGHT == 35
    assert USTSettlementNode.TRUST_BASELINE == 1.0
