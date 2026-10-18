# Advisory task lifecycle

Development foundation for the proposed DeepCore task console; not production certified.

## Usage

Import createTaskWorkflow from ./task-workflow.mjs and inject the existing createReviewAdapter result as adapter. submit({ id, fileName, source, instructions }) records source and instruction SHA-256 digests. review(id, { source, instructions }) requires the original content. Inspect the proposal, then call decide(id, { approved, proposalHash, sourceHash, actor }). get(id) returns an isolated snapshot.

States: submitted -> reviewing -> awaiting_approval -> approved or rejected. Provider errors produce failed tasks. Terminal tasks cannot be retried; submit a new ID.

## Optional local persistence

Import openTaskFileStore from ./task-file-store.mjs. Pass an absolute path outside the repository to a trusted private directory, then inject the returned store:

    const store = openTaskFileStore('/absolute/private/task-data');
    try {
      const workflow = createTaskWorkflow({ adapter, store });
      // Submit, await review completion, inspect and decide.
      // Stop accepting requests and drain every pending review before shutdown.
    } finally {
      store.close();
    }

Without store, state is memory-only. The store is synchronous, single-writer, and POSIX-only. Use a local filesystem supporting atomic same-directory rename and file/directory fsync; network filesystems and Windows are unsupported. Every transition rewrites a versioned snapshot with an 8 MiB total cap. This is for small local workloads, not high-throughput multi-user service storage.

The final directory must be owned by the current OS user with no group/other permissions; all parent directories must also be trusted. Newly created directories use mode 0700 and snapshot files mode 0600. Read-time symlinks are rejected. Proposals may reproduce sensitive source: snapshot contents are NOT encrypted. Source and instruction bodies are not separately stored.

Writes use an exclusive temporary file, file fsync, atomic rename, then directory fsync. A transition is acknowledged only after save succeeds. Any persistence error disables that workflow instance until restart. If an error occurs after rename, the transition may already be on disk: reopen and inspect rather than assuming it failed or repeating external effects. This is not an exactly-once execution guarantee.

Snapshots are checked for checksum, version, schema, state/history consistency, duplicate IDs and approval/proposal digests. Invalid data blocks startup; there is no silent reset. Checksums detect corruption, not malicious rewriting or rollback by a privileged actor. No signed or authoritative ledger guarantee is claimed.

## Restart and interrupted-process recovery

On graceful shutdown, drain pending reviews and call store.close() to release .writer-lock. One store may be attached to only one workflow.

After a crash, .writer-lock deliberately remains. Confirm the previous writer is stopped before manually removing that lock directory. Never break a live writer's lock. Preserve the snapshot and any leftover temporary files for diagnosis; do not promote temporary files into tasks.json. Reopen the store. Persisted reviewing tasks become failed with REVIEW_INTERRUPTED exactly once; no provider request is automatically retried. Submitted, awaiting-approval and terminal states are retained. Corrupt snapshots require operator recovery from a trusted backup.

Process-interruption recovery is tested. Hardware power-loss, filesystem fault matrices, backup restore, and production deployment are not verified.

## Trust boundaries

This library is not a web service or authentication system. The host must authenticate reviewers and derive actor from trusted session identity. An actor string alone proves no identity. Approval records intent only; it does not apply patches, spawn commands, or deploy software. Screen paths and source before calling review; this module is not a secret scanner. Render proposals as untrusted text.

This local task history is separate from the authoritative DeepCore event ledger. Do not use it as consensus, financial, or cryptographic authority.

## Verification

Run from AI/deepcore-ai-bridge:

    node --test test-review-adapter.mjs test-task-workflow.mjs test-task-adapter-integration.mjs test-task-persistence.mjs

25 scoped tests passed on Node 24.19.0: five adapter, six lifecycle, four integration, and ten persistence/recovery tests. Includes child-process interruption, lock exclusion, corrupted snapshots, invalid state, actual filesystem rename failure, and injected save failures before request dispatch, review completion, and approval.

The shared npm run local:test command includes all these suites and is invoked by the extension packaging workflow. The complete broader suite was not rerun for this change. No real provider request or hosted CI pass is claimed.

## Remaining milestones

1. Authenticated host and independent review of persistence and recovery boundaries.
2. Tasks, Review & Approval, and History dashboard with safe text rendering.
3. Authoritative event integration, backup/restore evidence, and operational storage design.
4. Isolated patch application, source revalidation, and allowlisted test execution.
5. End-to-end validation and successful hosted CI.
