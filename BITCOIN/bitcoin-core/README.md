# Bitcoin Core Integration

DeepCore treats Bitcoin as a trust-minimized external settlement and integrity layer.

## Baseline

- Bitcoin Core RPC is the primary node integration boundary.
- Bitcoin chain state is represented through an event-sourced, replayable model.
- Mempool and fee telemetry can inform economic and treasury analysis.
- Confirmations are distinct from broadcast or mempool acceptance.
- External Bitcoin state must never silently overwrite DeepCore's authoritative event history.

## Transaction lifecycle

`TX_CREATED → TX_VALIDATION_PASSED → TX_BROADCAST_ATTEMPTED → TX_MEMPOOL_ACCEPTED → TX_CONFIRMED`

Production operation requires explicit RPC authentication, network selection, timeout handling, reorg handling, idempotency, and secure secret management.