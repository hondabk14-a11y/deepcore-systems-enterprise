# Event-Sourced Ledger

The ledger is the authoritative application-state model for DeepCore components that require deterministic history.

## Design principles

- Append-only domain events are the source of truth.
- Reducers derive current state from ordered events.
- Snapshots accelerate recovery but do not replace event history.
- Event identifiers and transition rules must support idempotent processing.
- State transitions are validated before commitment.
- Replays must reproduce the same state from the same event stream.

## Integration

The ledger connects to the invariant engine, replay engine, treasury controls, Bitcoin state adapters, and consensus layer. External systems provide observations or requests; they do not silently rewrite authoritative DeepCore history.

## Implementation status

Architecture documented. Executable implementations must be linked here only after the corresponding project artifacts are verified.
