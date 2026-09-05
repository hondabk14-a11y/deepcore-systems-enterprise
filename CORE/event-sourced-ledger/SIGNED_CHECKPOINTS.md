# Signed Checkpoint Boundary

This reference layer defines how a retained ledger checkpoint can become an authenticated replay input.

## Trust flow

1. A checkpoint identifies `ledger_id`, `sequence`, `head_hash`, and `event_count`.
2. A signer produces a signature over a canonical representation of those fields plus `key_id`.
3. A deployment-specific key resolver maps `key_id` to an authenticated public key.
4. A deployment-specific verifier checks the signature.
5. Only the resulting authenticated `LedgerCheckpoint` is passed to replay verification.

## Deliberate scope

`SignedCheckpoint` does not generate or store private keys. `CheckpointSignatureVerifier` is an interface so the reference layer does not silently choose a cryptographic library or key-management model.

A production implementation should use an approved signature scheme such as Ed25519, authenticated key distribution, durable anchor storage, key rotation/revocation policy, and protected operational boundaries.

A valid signature proves authenticity of the signed checkpoint under the configured key. It does not by itself prove that the key is the correct organizational trust root, that the checkpoint is the newest one, or that the underlying ledger has been durably stored. Those are separate policy and infrastructure controls.
