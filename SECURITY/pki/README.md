# Private PKI

DeepCore Systems Enterprise uses a private, event-sourced PKI model for system identity and trust establishment.

## Architecture

- Private CA and explicit trust anchor.
- ECDSA certificates where certificate semantics require them.
- Ed25519 identities/signatures for components that use Ed25519.
- Hardware-bound cryptographic identity for the private-local system.
- Certificate issuance, rotation, and revocation represented as auditable state transitions.
- Cryptographic material must remain outside source control.

## Security requirements

1. Never commit private keys, CA keys, wallet seeds, passwords, API keys, or production credentials.
2. Separate trust-anchor material from application workloads.
3. Make certificate lifecycle events replayable and auditable.
4. Fail closed when identity or trust validation fails.
5. Test rotation, revocation, recovery, and compromised-identity scenarios before production use.

This document describes the architecture baseline, not a production CA implementation.