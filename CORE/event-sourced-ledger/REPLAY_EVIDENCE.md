# Replay release evidence (issue #24, partial implementation)

Run from this directory:

```sh
python replay_evidence.py --commit "$(git rev-parse HEAD)" --build-id local-1 --output replay-evidence.json
```

Use a clean checkout for commit attribution. The supplied commit and build ID
are provenance labels, not signatures; per-file SHA-256 digests identify the
Python sources actually tested. Do not label modified sources as a clean commit.
CI supplies its checkout SHA and run ID/attempt automatically.

The command runs the entire local ledger unittest suite, then reconstructs a
fixed three-event ledger in three separate Python processes using different
hash seeds. It requires matching history heads and canonical state commitments,
and compares the state hash against a fixed regression vector. Failed tests,
skipped tests, subprocess failures, or hash mismatches cause a nonzero exit.
JSON evidence and a full test log are written together. CI uploads both even
when checks fail; no artifact can be produced if the workflow never starts.

State commitment v1 uses SHA-256 over ASCII JSON with sorted keys and compact
separators. The payload contains domain, reducer_version, balance, and event_count.
Integers are required; booleans are rejected. The domain is
`deepcore-reference-ledger-state` and reducer_version is 1. This names the
state commitment format; it does not introduce event schema migration support.

## Verified scope and remaining work

- Existing tests cover hash-chain tampering, reordering, structural duplication,
  retained-checkpoint truncation detection, and checkpoint signature failures.
- Immutable reducer state and the new regression test cover failure without
  mutating the supplied initial state.
- Seven signature tests now use the existing authenticated-registry interface.
  The malformed-JSON test now places invalid JSON after a valid record, so
  verification reaches the parser rather than returning false on an earlier
  missing hash.
- Event schemas and migrations are still unversioned.
- Semantic event IDs, conflicting duplicate detection, and admission idempotency
  remain open. Structural duplicate detection is not semantic idempotency.
- Valid-prefix truncation requires an independently retained checkpoint.
- Multiple reads in replay/checkpoint verification need a coherent snapshot
  boundary for concurrent writers.
- Cross-seed fixture checks do not prove absence of every nondeterministic input.
- Evidence covers this reference ledger, not the other runtime/persistence
  implementations or distributed production operation.

Keep issue #24 open until these broader requirements are implemented and the
relevant CI evidence is available.
