# Event-Sourced Ledger

The ledger is the authoritative application-state model for DeepCore components that require deterministic history.

## Design principles

- Append-only domain events are the source of truth.
- Reducers derive current state from ordered events.
- Snapshots accelerate recovery but do not replace event history.
- Event identifiers and transition rules must support idempotent processing.
- State transitions are validated before commitment.
- Replays must reproduce the same state from the same event stream.

## Executable baseline

- `ledger.py` provides the focused local append-only ledger implementation.
- `reducer.py` provides the deterministic reference state reducer.
- `test_ledger.py` provides integrity and tamper-detection tests.
- `test_replay.py` provides deterministic replay and corruption tests.
- `test_reducer.py` provides state-transition validation tests.
- GitHub Actions is configured to execute all `test_*.py` files under this component.
- The component remains **Implemented**, with CI execution required before marking it **Tested**.
- It is **not production-ready**.

## Reducer contract

The reference reducer accepts only `CREDIT` and `DEBIT` events with non-negative integer amounts. Unsupported event types, negative amounts, and boolean amounts are rejected rather than silently coerced. The reducer returns an immutable `LedgerState` containing the derived balance and processed event count.

This is intentionally a narrow reference state machine. Domain-specific treasury, Bitcoin, consensus, authorization, and distributed-state transitions must be added as separate validated contracts rather than being inferred implicitly.

## Security boundary

The local implementation provides hash-chain integrity, replay validation, and deterministic state reduction for its own event history. It does not by itself provide Byzantine consensus, distributed replication, authorization, hardware key custody, network security, or production recovery guarantees.

Those controls belong to the larger DeepCore architecture and must be implemented and tested separately before production claims are made.

## Integration

The ledger connects to the invariant engine, replay engine, treasury controls, Bitcoin state adapters, and consensus layer. External systems provide observations or requests; they do not silently rewrite authoritative DeepCore history.
