from SECURITY.SSIL.ssil_systemic_integrity import IntegrityEvidence
from TREASURY.UST.ust_controller import USTController
from TREASURY.UST.ust_settlement import SettlementState, USTSettlementNode
from TREASURY.UST.ust_ssil_gate import evaluate_ust_settlement


def test_controller_accepts_clean_transaction():
    node = USTSettlementNode()
    controller = USTController(node, evaluate_ust_settlement)

    result = controller.process("tx-001", IntegrityEvidence())

    assert result.action.value == "ACCEPT"
    assert node.state("tx-001") is SettlementState.CREATED


def test_controller_holds_high_risk_transaction():
    node = USTSettlementNode()
    controller = USTController(node, evaluate_ust_settlement)

    result = controller.process(
        "tx-002", IntegrityEvidence(high_risk_signals=("anomaly",))
    )

    assert result.action.value == "HOLD"
    assert node.state("tx-002") is None


def test_controller_rejects_integrity_failure():
    node = USTSettlementNode()
    controller = USTController(node, evaluate_ust_settlement)

    result = controller.process("tx-003", IntegrityEvidence(ledger_valid=False))

    assert result.action.value == "REJECT"
    assert node.state("tx-003") is None
