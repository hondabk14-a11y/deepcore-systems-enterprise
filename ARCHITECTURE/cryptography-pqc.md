# Cryptography and PQC

## Current primitives

- SHA-256 for integrity hashing
- Ed25519 for identity/signing workflows
- ECDSA for private CA certificates and trust anchors
- BLS signatures for consensus aggregation

## Private PKI

DeepCore uses a private CA model with a trust anchor and event-sourced issuance/audit concepts. Certificate and key material must remain outside source control.

## Post-quantum readiness

The architecture reserves a dedicated PQC layer for migration planning, hybrid cryptographic schemes, algorithm agility, and validation of lattice-based primitives. No production cryptographic claim should be treated as complete until independently tested and reviewed.
