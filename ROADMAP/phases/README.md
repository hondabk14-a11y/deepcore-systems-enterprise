# Roadmap Phase Gates

This directory tracks implementation gates without implying that an architectural component is already production-ready.

## Phase 1: Foundation

- Event-sourced deterministic core
- Cryptographic identity and private PKI
- Invariants and replay semantics

## Phase 2: Distributed execution

- HotStuff-style BFT consensus
- Quorum certificates and BLS signatures
- Kafka/NATS transport
- Kubernetes/Istio/SPIFFE deployment
- Adversarial and chaos testing

## Phase 3: Financial integration

- Bitcoin Core integration
- Lightning and Liquid interfaces
- NBL v2 commitments
- DC02 anchoring
- Treasury reconciliation and accelerator controls

## Phase 4: Verification

- TLA+ specifications
- Lean proof development
- Runtime invariant enforcement
- Model-to-implementation correspondence testing

## Phase 5: AI and QSI augmentation

- OpenAI Responses/Agents integration
- Launch Desk
- Controlled QSI quantum augmentation
- Evaluation, authorization, audit, and rollback gates

## Release gate

A phase is not considered production-ready from documentation alone. Each release requires executable tests, security review, reproducibility evidence, operational rollback, and explicit handling of secrets and key custody.
