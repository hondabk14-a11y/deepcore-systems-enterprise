# DeepCore SSIL Risk Policy

## Purpose

The DeepCore Security, Safety, Integrity and Liquidity (SSIL) layer provides a deterministic risk-policy boundary for DeepCore Systems Enterprise.

SSIL evaluates observed events and system conditions. It may recommend, require review, or fail closed, but it does not become the authoritative ledger, consensus engine, or cryptographic key custodian.

## Decision states

SSIL produces one of four policy outcomes:

- `ALLOW`: required controls and evidence are satisfied.
- `REVIEW`: execution requires an authorized human or designated control-plane review.
- `DEFER`: required evidence is incomplete or an external dependency is unavailable.
- `FAIL_CLOSED`: a security, integrity, authorization, consensus, or invariant violation prevents the operation.

## Risk dimensions

SSIL evaluates at minimum:

1. **Identity risk**: workload, certificate, credential, or authorization anomalies.
2. **Cryptographic risk**: signature, hash, key-state, certificate, or verification failures.
3. **Ledger risk**: broken hash chains, invalid events, nondeterministic replay, or invariant violations.
4. **Consensus risk**: quorum anomalies, conflicting votes, equivocation indicators, or unsafe state transitions.
5. **Infrastructure risk**: service health, dependency failures, resource exhaustion, and network anomalies.
6. **Financial risk**: settlement inconsistencies, abnormal transaction state, liquidity stress, or reconciliation failures.
7. **AI/control-plane risk**: unauthorized tool use, policy bypass attempts, unsafe generated changes, or missing verification evidence.
8. **Recovery risk**: backup, restore, rollback, or disaster-recovery controls that cannot be demonstrated.

## Deterministic evaluation

Risk evaluation must be reproducible from an ordered event/evidence set. A policy decision must identify:

- policy version;
- evidence identifiers or hashes;
- observed risk signals;
- decision state;
- reason codes;
- required remediation or review;
- timestamp or event sequence reference.

## Fail-closed rules

SSIL must produce `FAIL_CLOSED` when any mandatory condition is violated, including:

- cryptographic verification failure;
- unauthorized state transition;
- ledger integrity failure;
- invalid consensus evidence;
- required security control failure;
- unverifiable production release evidence;
- detected secret/key-boundary violation;
- recovery or rollback control failure where the operation depends on that control.

## Authority boundaries

SSIL does **not**:

- rewrite authoritative event history;
- manufacture consensus evidence;
- approve its own policy changes;
- expose or export private keys, wallet seeds, credentials, or secrets;
- grant itself authorization;
- treat AI output as authoritative evidence;
- declare the system production-certified without the required independent evidence.

## Change control

Changes to SSIL policy require versioned review and regression testing. A policy change must not silently reinterpret historical authoritative events.

## Production status

This document defines a control policy. It is not evidence that production infrastructure, HSM/KMS custody, disaster recovery, rollback, or live observability has been successfully validated.
