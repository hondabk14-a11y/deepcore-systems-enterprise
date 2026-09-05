# Bitcoin Integration

DeepCore Bitcoin integration is designed around an event-sourced Bitcoin DAG and replayable economic state machine.

Components include:

- Bitcoin Core RPC integration
- Mempool and fee/liquidity telemetry
- Lightning Network integration
- Liquid integration
- MultiExchangeOracle using exchange feeds such as Coinbase and Kraken
- Fused price calculation
- NBL v2 bidirectional state commitments
- DC02 L3 Merkle-root anchoring through Bitcoin OP_RETURN

Bitcoin remains an external settlement and anchoring system. DeepCore state must remain independently auditable.