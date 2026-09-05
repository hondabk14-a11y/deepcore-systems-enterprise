# Durable checkpoint freshness

`durable_freshness.py` persists the last accepted `LedgerCheckpoint` and restores it across process restarts. Persistence uses a temporary file, `fsync`, and atomic `os.replace` so a successful write does not depend on an in-place partial overwrite.

## Security boundary

Durable storage is a state-retention mechanism, not a trust root. The JSON file is intentionally unauthenticated. An attacker who can rewrite the file can attempt rollback by replacing it with an older valid checkpoint.

Production deployment therefore requires an authenticated storage boundary, restricted filesystem permissions, integrity-protected backups, recovery controls, and a trusted mechanism for detecting rollback of the freshness store itself. A signed checkpoint remains necessary to authenticate the checkpoint payload and key policy remains responsible for authenticating the signing key.

The intended chain is:

`Ledger -> Checkpoint -> Signed Checkpoint -> Ed25519 -> Key Registry -> Freshness -> Durable Freshness State`

The reference implementation makes no production claim about filesystem durability, distributed locking, crash-consistency across filesystems, backup trust, or multi-writer coordination.
