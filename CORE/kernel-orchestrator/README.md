# Kernel Orchestrator

The kernel orchestrator coordinates validated DeepCore components without becoming an alternative source of truth.

## Responsibilities

- Coordinate event ingestion, reduction, validation, consensus, and recovery workflows.
- Enforce explicit component ordering and failure handling.
- Route work using authenticated workload identity.
- Preserve auditability across orchestration decisions.
- Keep secrets and cryptographic key custody outside ordinary orchestration logic.

## Control model

The orchestrator may coordinate actions, but authoritative state remains governed by the event-sourced ledger and its validation/consensus boundaries. AI-generated requests remain untrusted until authorization and invariant checks succeed.

## Implementation status

Architecture documented. Executable implementations must be linked here only after the corresponding project artifacts are verified.
