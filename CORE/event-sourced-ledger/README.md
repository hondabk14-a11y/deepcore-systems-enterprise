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
- `test_ledger.py` provides integrity and tamper-detection tests.
- Test execution is still pending in a reproducible runtime, so the component is **Implemented**, not yet **Tested**.
- It is **not production-ready**.

## Security boundary

The local implementation provides hash-chain integrity and validation of its own event history. It does not by itself provide Byzantine consensus, distributed replication, authorization, hardware key custody, network security, or production recovery guarantees.

Those controls belong to the larger DeepCore architecture and must be implemented and tested separately before production claims are made.

## Integration

The ledger connects to the invariant engine, replay engine, treasury controls, Bitcoin state adapters, and consensus layer. External systems provide observations or requests; they do not silently rewrite authoritative DeepCore history.
