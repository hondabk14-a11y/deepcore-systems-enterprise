# Replay Engine

The replay engine reconstructs DeepCore state from authoritative event history and provides a reproducibility boundary for testing, audit, and recovery.

## Responsibilities

- Consume an explicit event stream.
- Reapply the same reducer logic used by runtime execution.
- Detect ordering, schema, integrity, or invariant violations.
- Compare reconstructed state with expected checkpoints.
- Support deterministic incident reproduction and regression testing.

## Safety boundary

Replay is observational unless an explicitly authorized recovery workflow promotes reconstructed state. A replay result must not mutate production state merely because it differs from an external observation.

## Implementation status

Architecture documented. Executable implementations must be linked here only after the corresponding project artifacts are verified.
