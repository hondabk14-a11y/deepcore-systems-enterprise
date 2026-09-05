# Security

Security architecture includes private PKI, cryptographic identity, SPIFFE/Istio mTLS, SSIL risk and invariant enforcement, and post-quantum cryptography readiness.

## PKI

Private CA architecture uses an event-sourced ledger, trust anchor, certificate issuance, and verification boundaries.

## Identity

Ed25519 and ECDSA are used according to component requirements. Hardware-bound identity is a core trust boundary.

## PQC

PQC migration is treated as an architectural readiness requirement, with hybrid/transition strategies to be validated against deployment constraints.

Never store private keys, credentials, seeds, API tokens, or production secrets in this repository.