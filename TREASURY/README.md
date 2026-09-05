# Treasury Ledger

Treasury architecture includes an event-driven ledger, SSIL controls, reconciliation, and accelerator interfaces.

Transaction lifecycle:

`TX_EVENT_STREAM → TX_CREATED → TX_VALIDATION_PASSED → TX_BROADCAST_ATTEMPTED → TX_MEMPOOL_ACCEPTED → TX_CONFIRMED`

The reconciliation layer compares internal event state with external settlement observations. Accelerator integration includes mempool.space telemetry and policy-controlled transaction acceleration.