# DC02 Anchoring

DC02 is the DeepCore integrity-anchoring design for committing higher-layer state summaries to Bitcoin.

## Baseline

- DeepCore maintains an internal event-sourced state history.
- NBL v2 records bidirectional state commitments such as `H_DC_t` and `H_BTC_t` with cross-signatures.
- DC02 can anchor an L3 Merkle root into Bitcoin using an OP_RETURN commitment.
- Anchoring provides external integrity evidence; it does not replace the authoritative DeepCore event history.
- Anchors must be independently verifiable from the committed state and associated metadata.

## Safety and operations

The anchoring pipeline must be deterministic, idempotent, auditable, and resilient to Bitcoin reorgs or failed broadcasts. Payload-size, fee, privacy, and transaction-policy constraints must be evaluated before production deployment.

The project has referenced a DC01/DC02 state-anchorage standardization track; any formal standards claim requires separate specification and review.