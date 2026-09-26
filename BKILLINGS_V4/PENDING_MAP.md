# BKILLINGS remaining-work execution map

Evidence date: 2026-09-26. This map distinguishes executable local results from production completion. Scope: the saved DeepCore event-ledger prototype and its new isolated v2 protocol laboratory; not every component in the enterprise repository.

| Work item | Executed result | Status | Remaining exit criterion |
|---|---|---|---|
| Transaction network binding | Signatures bind protocol and genesis-spec digest; network/writer/signature rejection tests pass | Implemented locally | Independent protocol review and approved v1-to-v2 migration |
| Clock-independent replay | Historical verification uses block timestamps; test forbids wall-clock access during replay | Implemented locally | Cross-implementation test vectors and operational time policy |
| Durable storage/recovery | WAL/FULL, transactional ledger/head writes, single-pass recovery, explicit initialization, backup API, trusted checkpoint checks | Implemented and tested locally | Storage-device power-loss testing, encrypted backups, RPO/RTO drills, protected signer lock recovery |
| Distributed consensus | Four independent local processes; 3-of-4 signatures; durable no-double-vote locks; one offline node tolerated in demonstrated run | Partial reference implementation | Audited BFT protocol with view changes, leader recovery, partition healing, catch-up, multi-host TLS and failure testing |
| Key custody | Encrypted PKCS8, permissions/ownership/symlink checks, key survives process restart | Local at-rest protection implemented | External signer/HSM/KMS, rotation/revocation, backup ceremonies, compromise drills, protected monotonic vote locks |
| Admission/authorization | Genesis writer allowlist; authenticated loopback API; bounded input | Tested local harness | Per-node production identities, TLS, rate limits, DoS protection, production application server |
| Performance testing | 100 blocks / 1,000 transactions, 16.64 tx/s, 603.79ms median block, 1135.08ms P95, 234.63ms complete replay | Local baseline executed | Define target SLOs; checkpoint/incremental optimization; sustained multi-host load and fault injection |
| Deployment | Local four-process service launched and exercised; validation Dockerfile prepared | Local execution done; hosted deployment blocked | Docker builder unavailable; HF OAuth has read-repos/jobs but no repo-write; provision an authorized private target and persistence before deployment |
| Repository integration | New isolated BKILLINGS_V4 directory proposed through draft PR | Review artifact | Review and merge approval; integrate with CORE through an explicit adapter/migration |
| Existing deployment PR | PR #30 open, based on fix/weighted-quorum-test (#29), head 71425724b7a3a9f5f95d212f54fc15d9c33e4241 | Existing dependency unresolved | Review #29 then retarget/review #30; reproduce CI startup diagnostic and obtain passing jobs |
| Independent security assurance | Threat boundaries and failure limits documented; local automated checks run | Pending independent review | Reviewer validates consensus assumptions, canonical encoding, key lifecycle and recovery design |

## Verification counts

69 tests passed together in this turn: 24 original saved DeepCore blockchain tests, 21 prior math/runtime/storage tests, and 24 new hardening tests. This is not the entire GitHub repository test suite. The separate four-process test completed successfully. `evidence/cluster.json` and `evidence/benchmark.json` contain observed results. New-directory-only verification runs 24 tests.

## Verified access constraints

GitHub repository is private and accessible with push permission. No merge or visibility change is performed. HF authentication resolves to BKillings; current credential scopes are jobs, openid, profile, read-mcp and read-repos. No write-repos scope is present, so a Space upload is not attempted. Docker is absent locally, so the image has not been built. No persistent production server or external validator hosts are supplied. Neither funding nor new paid infrastructure is provisioned.

## Highest-priority follow-up

1. Review v2 domains, canonical encoding, admission time rules, state schema, and migration boundary.
2. Select an established BFT engine or complete a reviewed view-change design. Never unlock conflicting votes to make the test network progress.
3. Select protected signer custody and a lock-preserving disaster recovery model before independent production validators.
4. Obtain authorized deployment credentials and persistent staging hosts, build the container, run multi-host recovery/load drills, and verify the deployed revision.
5. Optimize only against agreed capacity/latency SLOs while preserving replay equivalence.

These items remain pending because a local test cannot establish production consensus liveness, external key protection, or independent assurance, and the required hosting permissions/infrastructure are unavailable.
