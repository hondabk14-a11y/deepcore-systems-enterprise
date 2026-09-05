# DeepCore Agent Operating Contract

## Scope
This repository is a private DeepCore Systems Enterprise codebase. Agents may inspect, plan, implement, test, and document changes within the repository, subject to repository permissions and human review.

## Non-negotiable safety rules
- Never commit secrets, credentials, private keys, wallet seeds, API tokens, certificates containing private material, or `.env` files containing secrets.
- Do not bypass authentication, authorization, signature verification, certificate validation, replay protection, consensus safety, or ledger invariants to make a change pass.
- Treat event history as authoritative and preserve deterministic replay and idempotency.
- Keep AI advisory and orchestration functions separate from ledger authority and cryptographic key custody.
- Do not claim a feature is deployed, secure, verified, or production-ready without executable evidence.

## Change workflow
1. Inspect the relevant implementation, tests, and configuration before editing.
2. Make the smallest coherent change that satisfies the task.
3. Add or update tests for behavioral changes.
4. Run the repository's existing validation tooling when available.
5. Report exactly what was validated and any validation that could not be performed.
6. Prefer a pull request for security-sensitive, cryptographic, consensus, financial, or production-impacting changes.

## Architecture priorities
Preserve deterministic state, explicit trust boundaries, fail-closed behavior, auditability, reproducible recovery, and clear separation between external integration systems and DeepCore's authoritative state.

## Review priorities
For cryptography, consensus, payments, treasury, PKI, identity, Bitcoin/Lightning, or security changes, reviewers should focus on threat model coverage, authorization boundaries, replay/double-spend resistance, key custody, failure modes, deterministic behavior, and test evidence.
