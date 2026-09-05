# Ed25519 Checkpoint Verification

The signed ledger checkpoint envelope is verified with the concrete Ed25519 adapter in `ed25519_checkpoint.py`.

## Verification boundary

- `SignedCheckpoint` defines canonical bytes to authenticate.
- `Ed25519CheckpointVerifier` verifies signatures with the `cryptography` package.
- Key lookup remains external. The verifier does not decide which key is the organizational trust root.
- Private keys are not generated or persisted by the verification adapter.

## Test coverage

The test suite includes an RFC 8032 Ed25519 verification vector and a generated signing round trip, plus checkpoint tampering, wrong-key, and malformed-signature rejection.

## Production requirements

A deployment still needs authenticated key distribution, key rotation and revocation, durable trusted-anchor storage, and monotonic freshness/rollback policy. A valid Ed25519 signature authenticates the signed checkpoint under the supplied public key, but does not establish those additional controls.

The test dependency is pinned in `requirements-test.txt` so local and CI validation use an explicit cryptographic library version.
