# DeepCore Systems Enterprise Copilot Instructions

## Mission
DeepCore is a private event-sourced distributed-systems platform centered on deterministic state, cryptographic trust, verifiable execution, and controlled integration with financial and AI infrastructure.

## Engineering rules
- Treat event history as authoritative. State must be reconstructible from ordered events.
- Preserve deterministic replay, idempotency, invariant enforcement, auditability, and safe recovery.
- Fail closed on malformed, unverifiable, unauthorized, or invariant-violating inputs.
- Keep cryptographic policy and authorization deterministic and explicit. AI may propose or coordinate changes but must not silently become ledger authority.
- Never claim that architecture or documentation is deployed or production-ready without executable evidence.
- Separate key custody from application logic. Never introduce private keys, wallet seeds, API keys, tokens, passwords, certificates containing sensitive material, or .env secrets into source control.
- Prefer small, reviewable changes with tests and reproducible validation.
- For security-sensitive or cryptographic changes, favor a pull request and explicit human review over direct production-branch modification.

## Repository areas
- ARCHITECTURE: system architecture, consensus, crypto/PQC, NBL/DC02, QSI
- CORE: event sourcing, replay, invariants, runtime, orchestration
- CONSENSUS: BFT, quorum certificates, BLS, adversarial simulation
- SECURITY: PKI, SPIFFE/Istio mTLS, SSIL, PQC, MCP verification
- BITCOIN: Bitcoin Core, Lightning, Liquid, DC02 anchoring
- TREASURY: accounting, reconciliation, accelerator controls
- DEEPCORE-PAY: NFC, Secure Enclave/HSM boundaries, L1/L2/L3 payment architecture
- FORMAL-VERIFICATION: TLA+, Lean, runtime/model verification
- AI: OpenAI integration, agents, Launch Desk
- SIMULATION: B.K./U.S.A. CRYPTO distributed-financial baseline
- INFRASTRUCTURE: Kafka, NATS, Kubernetes, Istio, SPIFFE, Helm, ArgoCD, observability
- ROADMAP: release gates and sequencing

## Validation expectations
Before proposing a change, inspect the relevant implementation and tests. Prefer existing project tooling and avoid inventing commands. Report exactly what was validated and distinguish documented, implemented, tested, and production-ready states.

## Security and dependency hygiene
Do not weaken authentication, authorization, signature verification, certificate validation, replay protection, consensus safety, or invariant checks merely to make tests pass. Review dependency changes for security impact and avoid unnecessary new dependencies.

## Change discipline
Keep unrelated refactors out of task-specific changes. Preserve public interfaces unless the task explicitly requires a breaking change. Add or update tests for behavioral changes. Document assumptions where protocol behavior is not obvious.
