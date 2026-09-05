# Treasury Ledger

DeepCore's treasury ledger is an event-driven accounting and control layer designed for deterministic state reconstruction and auditability.

## Baseline

- Treasury state is derived from an append-only event history.
- Reducers reconstruct balances and state from validated events.
- SSIL controls can gate sensitive transitions.
- Reconciliation compares internal state with external settlement/network observations.
- Every material transition should carry sufficient metadata for audit and replay.

## Transaction lifecycle

`TX_EVENT_STREAM → TX_CREATED → TX_VALIDATION_PASSED → TX_BROADCAST_ATTEMPTED → TX_MEMPOOL_ACCEPTED → TX_CONFIRMED`

Confirmation is not interchangeable with creation, broadcast, or mempool acceptance. Reorgs and failed transactions must remain representable in the event history.