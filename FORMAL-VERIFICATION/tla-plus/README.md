# TLA+ Verification

TLA+ provides the specification layer for DeepCore distributed-state, consensus, and safety properties.

## Target properties

- State transitions preserve defined invariants.
- A committed state cannot be replaced by an invalid alternative.
- Quorum certificates require the defined participant and voting conditions.
- View changes do not violate safety assumptions.
- Event replay produces deterministic state under the same valid event history.
- Cross-layer commitments remain correctly bound to the state they claim to represent.

## Verification workflow

1. Define the state variables and actions.
2. State safety and liveness assumptions explicitly.
3. Model normal and adversarial transitions.
4. Check invariants and temporal properties.
5. Map verified properties to runtime validation rules.
6. Regression-test implementation behavior against the specification.

A passing model check is evidence for the modeled system, not proof that an implementation is bug-free. Model scope and assumptions must remain documented.