# Post-Quantum Cryptography Readiness

DeepCore treats post-quantum cryptography (PQC) as a security-readiness track integrated with identity, transport, signing, and verification controls.

## Goals

- Inventory cryptographic dependencies and trust boundaries.
- Support migration planning away from quantum-vulnerable primitives where required.
- Preserve algorithm agility without weakening existing verification guarantees.
- Evaluate hybrid classical/PQC schemes before production adoption.
- Track cryptographic transitions as auditable configuration/state changes.

## Validation

PQC choices must be based on current standards, vetted implementations, interoperability testing, performance measurements, and threat-model review. No unverified algorithm or library should be treated as production-ready merely because it is labeled PQC.