# BKILLINGS v4 hardening laboratory

Protocol version **2**, package iteration **4**. This is a new, isolated event-ledger reference implementation. It does not change an existing DeepCore v1 chain, replace the repository's CORE runtime, migrate balances, or claim production readiness.

## Run the evidence

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python cluster_demo.py
python benchmark.py
```

Run these commands from this directory. `cluster_demo.py` creates four independent validator processes, encrypted throwaway keys, separate databases, and authenticated HTTP endpoints bound to loopback. It uses random local ports and cleans up the processes and temporary secrets. No private keys or tokens are included in the package. The benchmark is intentionally bounded and uses synthetic observation events.

## Implemented

- Signed transaction domain includes protocol version and the digest of a fixed genesis specification: network, epoch, validators, fault budget, and authorized writers.
- Ed25519 verification, strict sequential nonces, integer-only bounded canonical JSON, size/depth limits, and writer allowlisting.
- Replay evaluates recorded timestamps against recorded block time. Only live voting checks the wall clock; archival verification does not.
- Fixed committee signed certificates require N-f distinct registered validators with N >= 3f+1.
- Persistent per-validator, per-height vote locks are committed before a signature is released. A validator refuses to sign two different blocks at the same height.
- SQLite WAL/FULL persistence verifies history in a single pass. Finalized head metadata catches inconsistent suffix deletion. Optional externally trusted checkpoints detect coordinated rollback past the checkpoint.
- PKCS8 encrypted local Ed25519 keys, owner-only file permissions, no-overwrite creation, symlink rejection, and passphrase delivery over an input pipe to the local harness.
- Authenticated local vote/commit/readiness/status routes, SQLite backup API, restart and restore checks.

## What the consensus component does not do

This is a conservative fixed-committee certificate protocol, **not HotStuff or a complete live BFT network**. It locks one value forever at a height. Equivocation or split votes can stall it indefinitely. It has no rounds/view changes, leader election, automatic catch-up, peer discovery, dynamic membership, or multi-host authenticated transport. Certificate threshold and lock tests support the stated safety mechanism; they are not a formal proof or independent audit.

Never restore a validator's signing database from an old backup and resume signing: a rolled-back vote lock can permit equivocation. Backups of observer ledgers are recoverable; validator disaster recovery needs an external monotonic signer, protected lock journal, or reviewed reconfiguration procedure. Encrypted PEM protects stored key bytes but does not protect keys after decryption in process memory. HSM/KMS/threshold signing remains pending.

## State and migration

State consists of sender nonces, event-type counters, and a hash chain committing the ordered signed events. Blocks store full signed events and their certified state root. This is an event ledger, not a payment, smart-contract, or asset issuance implementation.

Do not reinterpret v1 signatures or roots as v2. Existing v1 files remain unchanged. A production migration must independently verify the old ledger, approve an externally recorded checkpoint, specify data/state mapping, provision a fixed committee and authorized writers, sign a new genesis specification, and validate rollback/cutover in staging. This package does not perform that migration.

## Operation and limitations

Initialize a fresh database explicitly with `Ledger(path, spec, create=True)`. Normal opens reject a missing database. Keep databases on local storage with correct locking/fsync behavior. Use `Ledger.backup(destination)` for consistent backups. Store externally trusted checkpoints outside the same failure domain. Retaining all signatures and replaying the full history on every operation is intentionally conservative and becomes expensive; incremental validation/checkpoint optimization requires further design and tests.

`node.py` is a loopback-only test harness built with Python's basic HTTP server, not a production web server. It is single-threaded, uses a shared local bearer token, and lacks TLS, workload isolation and robust DoS resistance. The Dockerfile is a **validation image**, not a deployment of the financial or consensus system. Production endpoints must use reviewed transport, per-node identities, authorization and rate limits.

See `PENDING_MAP.md` for exact completion status, blockers, and exit criteria. See `evidence/` for outputs from this run.

## Reference documentation

- https://cryptography.io/en/latest/hazmat/primitives/asymmetric/serialization/ — encrypted PKCS8 serialization.
- https://sqlite.org/pragma.html#pragma_synchronous — WAL/FULL durability settings.
- https://sqlite.org/lang_transaction.html — SQLite transactions and write serialization.
