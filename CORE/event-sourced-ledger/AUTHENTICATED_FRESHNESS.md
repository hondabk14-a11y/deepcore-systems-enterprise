# Authenticated freshness boundary

`authenticated_freshness.py` composes three existing security boundaries without collapsing their responsibilities:

1. `SignedCheckpoint` carries canonical checkpoint signing material.
2. `CheckpointPublicKeyResolver` and the key registry establish which public key is currently accepted.
3. `CheckpointSignatureVerifier` verifies the cryptographic signature.
4. `CheckpointFreshnessPolicy` enforces monotonic checkpoint progress.

A checkpoint must authenticate successfully and belong to the configured ledger before it can advance trusted freshness state. Signature failure, unknown/revoked key, ledger mismatch, rollback, and same-sequence conflicts fail closed.

## Trust boundary

This composition does not create a trust root. The key resolver remains responsible for authenticated key distribution, and durable freshness storage remains responsible for protecting retained state from rollback. No private signing key is stored by this module.

The checkpoint schema now carries `ledger_id` and `sequence` explicitly, while retaining `event_count` for compatibility and requiring the freshness policy to keep sequence and event count consistent.

Production deployment still requires authenticated durable key storage, key rotation/revocation policy, authenticated durable freshness storage, recovery controls, and multi-writer coordination where applicable.
