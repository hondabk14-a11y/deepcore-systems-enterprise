# DeepCore Source Restoration Plan

This branch is the controlled archive/source-recovery lane for DeepCore Systems Enterprise.

The binary library archive is preserved under `ARCHIVE/zips/`. Source restoration must exclude compiled Python caches, credentials, private keys, wallet seeds, `.env` files containing secrets, and generated runtime state.

Canonical restoration order:
1. Core runtime and cryptography
2. Event ledger and verification
3. Agent/policy boundaries
4. Tests and CI
5. Infrastructure/deployment
6. Launch Desk and auxiliary applications

Every restored component must retain its provenance and must not be labeled production-ready until CI and runtime evidence exists.
