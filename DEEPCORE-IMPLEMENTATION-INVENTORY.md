# DeepCore Implementation Inventory and Code-to-Spec Traceability

**Execution phase:** P0.1 — Implementation inventory and code-to-spec traceability  
**Branch:** `production-readiness-execution`  
**Assessment state:** NOT_READY  
**Evidence rule:** A design document proves intent only. An implementation entry is counted only when executable source is present. A test claim requires executable test evidence. Production readiness requires execution evidence, security validation, recovery evidence, and approval.

## Evidence boundary

This inventory is a repository inspection artifact, not a claim that the listed components are production-ready. The repository itself states that documentation is not evidence of deployment and that AI remains bounded from ledger authority. The current inspection found a real executable deterministic-ledger/reference-crypto surface, while several architectural areas remain documentation/planning only.

## Traceability matrix

| Spec / capability | Repository evidence | Executable evidence found | Test evidence found | P0.1 disposition |
|---|---|---|---|---|
| Deterministic event-sourced ledger | `CORE/event-sourced-ledger/` | `ledger.py`, `reducer.py`, checkpoint/trust-boundary modules | `test_validation_boundary.py`, signed-checkpoint tests, trusted-anchor tests | IMPLEMENTED_REFERENCE / NOT_PRODUCTION_READY |
| Ledger integrity hash chain | `CORE/event-sourced-ledger/ledger.py` | `EventSourcedLedger.verify()` and replay path | Validation tests present | IMPLEMENTED_REFERENCE |
| Deterministic reducer | `CORE/event-sourced-ledger/reducer.py` | `apply_event()`, `reduce_events()`, `reduce_ledger()` | Validation-boundary coverage present | IMPLEMENTED_REFERENCE |
| Domain invariant validation | `CORE/event-sourced-ledger/` | `verify_domain_events` integration | Validation tests present | IMPLEMENTED_REFERENCE |
| Trusted checkpoint boundary | `CORE/event-sourced-ledger/` | `verify_checkpoint`, `TrustedCheckpointAnchor`, resolver | `test_trusted_anchor.py` | IMPLEMENTED_REFERENCE |
| Ed25519 checkpoint verification | `CORE/event-sourced-ledger/ed25519_checkpoint.py` | Concrete Ed25519 verifier | RFC/vector and tamper/wrong-key/malformed-signature tests documented in repo | IMPLEMENTED_REFERENCE |
| Authenticated key lookup boundary | `CORE/event-sourced-ledger/key_registry.py` | Reference key-registry boundary | Related checkpoint tests | IMPLEMENTED_REFERENCE / CUSTODY_MISSING |
| General cryptographic signing helper | `CORE/deepcore_crypto.py` | Ed25519 sign/verify helper | Some checkpoint vectors | PARTIAL |
| PQC crypto agility | `ARCHITECTURE/cryptography-pqc.md`, `SECURITY/pqc/README.md` | No verified production PQC implementation found in P0.1 search | No production PQC execution evidence found | UNVERIFIED |
| Private PKI / ECDSA CA | `ARCHITECTURE/cryptography-pqc.md`, security architecture docs | No complete CA lifecycle implementation established in P0.1 evidence | No complete lifecycle evidence | PARTIAL / UNVERIFIED |
| Enterprise key lifecycle / KMS-HSM | Security and architecture requirements | No authoritative GENERATE→REGISTER→ACTIVATE→ROTATE→SUSPEND→REVOKE→DESTROY implementation found | None establishing production custody | MISSING |
| IAM / RBAC / ABAC / delegation | Architecture/security requirements | No complete executable IAM/AuthZ service found in P0.1 search | None | MISSING |
| Signed policy decision boundary | Architecture and project operating contract | No complete executable policy decision service found in P0.1 search | None | MISSING / PARTIAL DESIGN |
| HotStuff-style BFT | `CONSENSUS/README.md`, roadmap | No Rust consensus engine found in P0.1 code search; README labels Rust/QC/BLS as planned | No executable consensus evidence | UNVERIFIED |
| QC / BLS / `blst` | `CONSENSUS/bls/README.md`, `CONSENSUS/README.md` | Documentation/reference target only in inspected evidence | No executable `blst` evidence | UNVERIFIED |
| Adversarial consensus testing | Roadmap / consensus architecture | No executable adversarial consensus harness established | None | UNVERIFIED |
| Bitcoin / DC02 anchoring | `BITCOIN/dc02-anchoring/README.md`, `ARCHITECTURE/nbl-dc02.md` | No verified production anchoring implementation established in P0.1 search | No end-to-end anchoring evidence | PARTIAL / UNVERIFIED |
| Treasury | `TREASURY/` architecture/material | No authoritative production accounting implementation established in P0.1 evidence | None | UNVERIFIED |
| DeepCore Pay | `DEEPCORE-PAY/README.md` | Architecture/documentation only in inspected evidence | None | UNVERIFIED |
| AI bridge | `AI/deepcore-ai-bridge/` | Node.js bridge source and local inference health-check tooling present | Local health-check test present | IMPLEMENTED_COMPONENT / SECURITY_GATE_REQUIRED |
| AI authority boundary | README, engineering roles, AI docs | Architectural boundary is explicit; authoritative state gate still requires executable proof | No end-to-end unauthorized-action test found in P0.1 search | PARTIAL |
| MCP verifier | `SECURITY/mcp-verifier.md` | Documentation describes intended Ed25519 verifier/service boundary | No verified production service evidence found | PARTIAL DESIGN |
| Observability | CI/runtime/architecture docs | Workflow/runtime artifacts exist; production telemetry/SLO evidence not established | No execution evidence | PARTIAL |
| Secure CI/CD | `.github/workflows/*` | Multiple CI/security/readiness workflows exist | Workflow execution evidence not inspected in P0.1 | PARTIAL |
| Supply-chain security | Repository security policy, CI roadmap | No complete SBOM/provenance/signing/admission chain established | None | MISSING |
| Disaster recovery | Repository security/recovery requirements | No verified restore drill artifact found | None | UNVERIFIED |
| Multi-region resilience | Architecture/roadmap | No verified multi-region executable deployment found | None | UNVERIFIED |
| Formal verification | Architecture/roadmap | TLA+/Lean intent documented; implementation-to-proof linkage not established | No machine-verified proof artifact found | PARTIAL |
| Threat model | Security requirements | No completed current threat-model artifact established | None | MISSING |
| Operations/runbooks | Security/release requirements | No complete production runbook set established | None | MISSING |

## Code-to-spec traceability rules

1. **Design → implementation:** every claimed production capability must map to one or more concrete source paths.
2. **Implementation → test:** every security-sensitive implementation must map to executable unit/integration/adversarial tests as applicable.
3. **Test → execution evidence:** a committed test file is not proof that CI or a production-like environment executed it successfully.
4. **Implementation → authority boundary:** any path that can affect authoritative ledger state must explicitly cross deterministic authorization, validation, and cryptographic controls.
5. **External systems → observation/integration boundary:** Bitcoin, market feeds, Lightning, Liquid, and AI must not silently rewrite authoritative DeepCore history.
6. **Documentation → status:** documentation-only claims remain `DESIGNED` or `UNVERIFIED` and cannot be promoted by prose.

## P0.1 findings

### Confirmed executable surface

The repository contains an executable reference ledger with SHA-256 hash chaining, structural verification, deterministic replay, invariant validation, checkpoint verification, trusted-anchor resolution, and Ed25519 checkpoint verification. These components are useful evidence of implementation progress, but their own documentation identifies the ledger as a reference implementation rather than a production ledger.

### Confirmed planned-only / unverified surface

The inspected consensus documentation explicitly describes Rust consensus/QC, Go transport, Python orchestration, Docker, Redis/Kafka, and real `blst` BLS as the planned implementation baseline. No corresponding executable consensus implementation was established by the P0.1 code search. This remains a release-blocking gap.

### Security boundary finding

The repository has deliberately separated checkpoint signature verification from organizational trust-root/key custody decisions. That is a sound boundary, but it also means the missing enterprise key lifecycle and IAM/AuthZ systems cannot be inferred from the verifier code.

## P0.1 completion criteria

P0.1 is considered **COMPLETE FOR DISCOVERY** because the major architecture claims were mapped to concrete source/documentation evidence and unsupported implementation claims were downgraded. It is **NOT COMPLETE FOR PRODUCTION READINESS** because the traceability matrix exposes unresolved P0 implementation and verification blockers.

## Next blocker

**P0.2 — Close the authoritative authorization boundary: implement and test IAM/AuthZ + signed policy decisions + fail-closed execution gate before any component may mutate authoritative DeepCore state.**
