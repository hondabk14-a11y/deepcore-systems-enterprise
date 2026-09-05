# HotStuff-Style BFT

DeepCore's consensus track uses a HotStuff-style Byzantine Fault Tolerant model for replicated state transitions.

## Baseline

- Proposal and voting phases produce quorum certificates (QCs).
- State transitions are accepted only after required quorum rules are satisfied.
- Nodes maintain deterministic state and replayable consensus history.
- View/leader changes must preserve safety across faults and restarts.
- Consensus decisions integrate with the event-sourced ledger and invariant engine.

## Planned implementation path

1. Rust consensus/QC engine.
2. Go transport layer.
3. Python orchestration and simulation.
4. Containerized multi-node testing.
5. Redis/Kafka messaging integration.
6. Adversarial and chaos testing before production consideration.

This document is an architecture baseline, not a claim of production-ready BFT security.