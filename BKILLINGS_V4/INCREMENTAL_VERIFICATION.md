# Incremental state verification

The transition rule is unchanged: S[h+1] = F(S[h], E[h+1]). Starting from verified state S[h], accepting the next block still requires valid domain-bound transaction signatures, sequential nonces, permitted writers, valid recorded timestamps, correct parent/height/state root, and a distinct-validator certificate meeting the quorum threshold.

The optimization removes repeated verification of an unchanged prefix. It does not remove transaction or quorum signature checks from new blocks, alter signed bytes, change the genesis specification, or migrate storage.

## Invariant and reference path

The volatile cache records a verified height, block hash, timestamp and state. Opening a ledger always replays history before constructing a cache. Successful commits advance the cache only after SQLite commit succeeds. Every returned snapshot is copied so caller mutation cannot alter cached state.

`Ledger(..., incremental=False)` uses the original full-history validation path. `snapshot(full_audit=True)` always runs a full history audit even in incremental mode. Differential tests feed identical signed blocks to both modes and compare state, head, nonces, counters and event commitments after every block. This is independently executed replay using the same transition implementation, not a separate implementation or formal proof.

## Invalidation and transaction boundary

Cache tokens combine the same connection's SQLite `data_version`, connection `total_changes`, `schema_version`, genesis-spec identity and checkpoint encoding. Changes made through other SQLite connections force full replay; same-connection SQL outside the ledger operations also invalidates the cache. Failed operations clear the cache. Tokens are captured inside the transaction, before it is released, so a subsequent external commit cannot be mislabeled as already verified.

Ledger writes reject unexpected SQL side-effect counts (for example, history-mutating triggers). Voting still commits the no-double-vote lock before releasing a signature. Read transactions may legitimately return their original snapshot while another writer commits; the next operation must detect that external change and audit.

## Threat boundary

This cache assumes the application process and SQLite locking/change tracking remain trustworthy. It does not detect arbitrary process-memory modification or promise detection of filesystem edits that bypass SQLite. It is not a substitute for disk integrity, externally trusted checkpoints, immutable backups or independent audit. Restoring old validator vote locks remains unsafe. Do not reset locks to restore progress.

Separate processes sharing one SQLite database will invalidate one another's caches and may still require frequent full replay. The four-node harness gives each validator its own database; this performance change does not add cross-host transport or consensus view changes.

## Computational cost

Normal operations stop rechecking signatures for all previous blocks. They still verify the new batch/certificate and copy/hash current state. Consequently, latency depends on transaction batch size and state-map size; it is not universally constant time. Startup and explicit audit still process all history. Unique event types can grow the counter map and must be included in future scaling tests.

## Reproduce

```bash
python -m unittest discover -s tests -v
python cluster_demo.py
python benchmark.py --compare
```

The comparison uses the same identities and deterministic signed transactions for both modes, with 100 blocks and 10 transactions per block. It checks exact final state-root and block-hash equality and explicitly measures a final full audit. Timings exclude network/HSM latency and are not production capacity guarantees.

Reference: https://www.sqlite.org/pragma.html#pragma_data_version — data-version comparisons are meaningful on the same connection and signal commits by other connections.

## Measured result, 2026-09-26

One sequential comparison on the same environment, using identical keys, signed transactions and block timestamps:

| Metric | Full replay per operation | Incremental |
|---|---:|---:|
| Transactions / blocks | 1,000 / 100 | 1,000 / 100 |
| Elapsed | 107.0187 s | 1.9941 s |
| Throughput | 9.34 tx/s | 501.48 tx/s |
| Median block time | 1,080.55 ms | 19.02 ms |
| P95 block time | 1,966.88 ms | 24.50 ms |
| Explicit complete-history audit | 416.04 ms | 414.82 ms |

Final state roots and final block hashes matched exactly. The observed throughput ratio is 53.69x. These are single-run measurements, without confidence intervals, randomized run order, cross-host networking or HSM work. The baseline differs from the earlier 16.64 tx/s result because it was rerun in this session; compare the two contemporaneous modes rather than mixing runs.

Validation: 38 tests passed (24 existing hardening + 14 incremental tests), and the four-process harness passed. The earlier broader 69-test suite was not rerun. Hosted CI and production consensus liveness remain unverified.
