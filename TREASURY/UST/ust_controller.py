"""DeepCore UST-0001 reference settlement controller.

This is a simulation/reference component. It is not an implementation of
or an authorized system of the U.S. Department of the Treasury.
"""

from __future__ import annotations

from typing import Callable

from TREASURY.UST.ust_settlement import SettlementState
from TREASURY.UST.ust_ssil_gate import GateAction, USTGateResult


class USTController:
    """Apply the SSIL gate before entering the UST settlement lifecycle."""

    NODE_ID = "0001"
    LOGICAL_NAME = "UST-0001"

    def __init__(self, settlement_node, ssil_gate: Callable) -> None:
        self.settlement = settlement_node
        self.ssil_gate = ssil_gate

    def process(self, tx_id: str, evidence) -> USTGateResult:
        gate = self.ssil_gate(evidence)

        if gate.action in (GateAction.REJECT, GateAction.HOLD):
            return gate

        self.settlement.apply(tx_id, SettlementState.CREATED)
        return gate
