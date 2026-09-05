# Ed25519 Checkpoint Verification

The ledger checkpoint envelope can be verified with the concrete Ed25519 adapter in `ed25519_checkpoint.py`.

## Boundary

- `SignedCheckpoint` defines the canonical bytes to authenticate.
- `Ed25519CheckpointVerifier` performs signature verification using the `cryptography` package.
- Key lookup remains an external responsibility. The verifier does not establish that a key is an organizational trust root.
- Private keys are not generated, persisted, or accepted by the verification adapter.

## Production requirements

A deployment must still provide authenticated key distribution, key rotation and revocation, durable trusted-anchor storage, and monotonic freshness/rollback policy. A valid Ed25519 signature authenticates the signed checkpoint under the supplied public key, but it does not establish those additional controls.

The test dependency is pinned in `requirements-test.txt` so CI and local validation use an explicit cryptographic library version rather than an unconstrained dependency.
