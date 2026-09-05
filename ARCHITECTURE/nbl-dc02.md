# NBL v2 and DC02 Anchoring

NBL v2 defines bidirectional state hash commitments between DeepCore and Bitcoin:

- `H_DC_t`: DeepCore state commitment at time/state index `t`
- `H_BTC_t`: Bitcoin-side commitment corresponding to the anchored state
- Cross-signatures bind the commitments and provide an auditable relationship.

DC02 extends the anchoring model by committing L3 Merkle roots into Bitcoin OP_RETURN transactions. The anchoring layer is an integrity and audit mechanism, not a replacement for DeepCore's authoritative event history.