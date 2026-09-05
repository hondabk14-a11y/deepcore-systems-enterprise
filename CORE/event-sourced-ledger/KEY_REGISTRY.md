# Authenticated Key Registry

The signed-checkpoint verifier needs a separate answer to one question: which public key is authorized for a given `key_id`?

`key_registry.py` provides a deliberately small reference boundary for that decision.

## Contract

- `key_id` must be explicit and non-empty.
- Ed25519 public keys must be exactly 32 bytes.
- Only `active` keys resolve to verification material.
- Revoked keys resolve to `None` and therefore cannot authenticate new checkpoint verification attempts.
- Unknown keys fail closed.

## Trust boundary

`InMemoryKeyRegistry` is test/reference infrastructure. Its input mapping is assumed to have come from an authenticated source. It does **not** establish a production trust root, durable storage, key rotation protocol, revocation distribution, or rollback protection.

Production integration must authenticate the registry source and define key lifecycle policy independently of the checkpoint verifier.
