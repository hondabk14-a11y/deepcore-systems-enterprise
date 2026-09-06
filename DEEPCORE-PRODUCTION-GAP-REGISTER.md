# DeepCore Systems Enterprise Production Gap Register

**Execution phase:** Phase 0 — Repository and Architecture Discovery
**Branch:** `production-readiness-execution`
**Status:** NOT_READY
**Evidence standard:** Documentation alone does not establish implementation, verification, deployment, or production readiness.

## Initial evidence boundary

This register is based on the repository-level architecture and operating contract currently visible during Phase 0. The repository README explicitly describes the repository as a structured architectural baseline with some executable artifacts and other specifications awaiting verified implementation. Therefore, capabilities described architecturally but not backed by executable evidence are marked `UNVERIFIED` rather than complete.

## Current gaps

| Area | Status | Initial finding | Required evidence / next action |
|---|---|---|---|
| Architecture baseline | IMPLEMENTED | Repository has structured architecture areas and explicit production principles. | Maintain architecture-to-code traceability. |
| Event-sourced deterministic core | PARTIAL | Architecture identifies event history, deterministic replay, reducers, and invariants, but repository status says not all components are verified implementations. | Inventory executable core, tests, replay proofs, and recovery tests. |
| BFT consensus | UNVERIFIED | HotStuff-style BFT, QC, BLS, and adversarial testing are specified. | Prove executable implementation, quorum tests, Byzantine tests, and benchmark evidence. |
| Cryptographic identity | PARTIAL | Ed25519/ECDSA/private PKI and hardware-bound identity are described. | Establish implementation inventory, key lifecycle, rotation, revocation, and test evidence. |
| Key management | MISSING | Full enterprise key lifecycle is not established by the visible repository baseline. | Implement GENERATE/REGISTER/ACTIVATE/ROTATE/SUSPEND/REVOKE/DESTROY/AUDIT with custody boundaries. |
| PQC crypto agility | PARTIAL | PQC migration readiness is described, but complete algorithm abstraction and migration evidence are not established. | Implement versioned crypto abstraction and approved hybrid/PQC profiles where required. |
| Private PKI | PARTIAL | PKI is part of the architecture. | Verify CA hierarchy, issuance, rotation, revocation, trust anchors, compromise isolation, and tests. |
| IAM/AuthZ | MISSING | Explicit authorization is a design principle, but a complete enterprise IAM capability is not established. | Implement identity, workload identity, RBAC/ABAC, delegation, privileged access, break-glass, SoD, and audit. |
| Policy engine | PARTIAL | Policy/authorization is architecturally defined. | Verify signed decisions, policy version/hash, constraints, expiry, fail-closed behavior, and tests. |
| Audit/evidence | PARTIAL | Auditability and Bitcoin/Merkle evidence are architectural goals. | Build request→auth→action→event→state→Merkle→anchor traceability and verification tooling. |
| Bitcoin/DC02 anchoring | PARTIAL | Bitcoin Core, NBL/DC02 and anchoring are specified. | Verify executable anchoring, confirmation policy, reorg handling, RPC failure handling, replay protection, recovery. |
| Treasury controls | UNVERIFIED | Treasury reconciliation and accelerator controls are specified. | Verify authoritative accounting, reconciliation, authorization, double-spend controls, and failure handling. |
| DeepCore Pay | UNVERIFIED | NFC/L3 invoice/DC02 proof architecture is documented. | Verify executable implementation, secure key custody, replay protection, payment-state invariants, and tests. |
| Observability | PARTIAL | Infrastructure architecture includes monitoring/observability. | Establish SLI/SLO, structured telemetry, correlation IDs, alerting, security events, and evidence. |
| Security operations | MISSING | SIEM/SOAR-compatible security-event pipeline is not established by current visible baseline. | Implement security event taxonomy, detection rules, escalation, and integration contracts. |
| Incident response | MISSING | Runbook framework is required but not evidenced as complete. | Create executable incident runbooks and auditable incident lifecycle. |
| Disaster recovery | UNVERIFIED | Recovery is a stated production requirement, but successful restore evidence is not established. | Define RPO/RTO, immutable backups, restoration, key/PKI/ledger recovery, and execute drills. |
| Multi-region resilience | UNVERIFIED | Multi-region architecture has been discussed, but production evidence is not established. | Validate partition, region loss, reconciliation, quorum behavior, and recovery. |
| Chaos engineering | UNVERIFIED | Adversarial/chaos testing is a roadmap requirement. | Build repeatable fault injection and invariant assertions. |
| Supply-chain security | MISSING | Current baseline does not establish complete SBOM/provenance/signing/admission enforcement. | Implement dependency controls, SBOM, provenance, artifact/image signing and verification. |
| Secure CI/CD | PARTIAL | CI/CD is part of the architecture/roadmap. | Verify security gates, signed artifacts, provenance, deployment controls, and rollback. |
| Runtime security | UNVERIFIED | Kubernetes/Istio/SPIFFE are architectural components. | Verify admission, workload identity, network policy, secret isolation, least privilege, runtime integrity. |
| Performance/capacity | UNVERIFIED | No production benchmark evidence established in Phase 0. | Build reproducible normal/adversarial load tests and capacity model. |
| Data governance | MISSING | Enterprise retention/classification/lifecycle controls are not established by visible baseline. | Define applicable data classification, retention, archival, deletion, residency, isolation. |
| API governance | UNVERIFIED | APIs exist conceptually, but enterprise lifecycle controls are not established. | Verify versioning, schema, auth, rate limits, idempotency, replay protection, compatibility. |
| Configuration management | MISSING | No complete signed/versioned production configuration control is evidenced. | Implement environment separation, validation, access control, audit, and safe promotion. |
| Formal verification | PARTIAL | TLA+/Lean/runtime invariants are explicitly planned. | Connect specifications to implementation and CI; publish machine-verifiable evidence. |
| Testing system | PARTIAL | Testing is a stated discipline, but complete unit/integration/system/fuzz/chaos/recovery coverage is not evidenced. | Establish test matrix and CI execution evidence. |
| Threat model | MISSING | Threat-model requirement exists but a current completed model is not established. | Create and maintain `DEEPCORE-THREAT-MODEL.md`. |
| AI security | PARTIAL | AI is explicitly bounded as advisory/orchestration. | Verify tool authorization, sandboxing, output validation, model provenance, and deterministic action gates. |
| Governance/compliance | UNVERIFIED | Applicable controls are identified conceptually; certification/compliance evidence is not established. | Build control/evidence matrix without making unsupported compliance claims. |
| External security assessment | MISSING | No independent assessment evidence established. | Prepare audit scope and remediate findings before any production claim. |
| Operational runbooks | MISSING | Repository requires runbooks but completeness is not established. | Create production, incident, deployment, rollback, recovery, and key-management runbooks. |

## Blocking P0 gaps

1. Complete implementation inventory and code-to-spec traceability.
2. Enterprise IAM/AuthZ.
3. Cryptographic key lifecycle and custody controls.
4. Ledger integrity/replay verification evidence.
5. BFT consensus executable/adversarial verification evidence.
6. PKI lifecycle verification.
7. Audit/evidence chain.
8. Secrets and software supply-chain controls.
9. Backup and disaster-recovery verification.
10. Threat model and security-control evidence.

## Production rule

No item may move to `COMPLETE` or `PRODUCTION_READY` without executable evidence. Any untested architectural statement remains `UNVERIFIED`.
