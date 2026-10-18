# Advisory task lifecycle

First implementation slice of the proposed DeepCore task console. Development only.

## Usage

Import createTaskWorkflow from ./task-workflow.mjs and inject the existing createReviewAdapter result as adapter. submit({ id, fileName, source, instructions }) records source and instruction SHA-256 digests. review(id, { source, instructions }) calls the adapter only when content matches submission. Inspect the returned proposal, then call decide(id, { approved, proposalHash, sourceHash, actor }). Use get(id) to retrieve an isolated snapshot.

States: submitted -> reviewing -> awaiting_approval -> approved or rejected. Provider failures transition to failed, with sanitized error output. Terminal tasks cannot be retried; submit a new ID.

## Trust boundaries

This is a library module, not a web service. The host must authenticate the reviewer and derive actor from trusted session identity. The actor string alone proves no identity. Approval records intent only: no file writes, patch application, subprocesses, or deployment occur. The host must screen paths and source before calling review; this module does not scan secrets. Model-generated proposals can contain source and must be treated as sensitive, untrusted content, including when rendered in a future UI.

Storage is process-local and lost on restart. History is ordered diagnostic state, not signed, durable, or an authoritative DeepCore ledger. Digests bind reviewed content but do not authenticate the reviewer or prevent a privileged host from rewriting memory. No production authorization or ledger guarantees are claimed.

## Verification

Run from AI/deepcore-ai-bridge:

    node --test test-task-workflow.mjs

Six offline tests passed with a fake adapter on Node 24.19.0. No live AI provider or hosted CI pass is claimed. This standalone test command must be added to the integrated CI gate before release.

## Remaining milestones

1. Authenticated host and persistent storage with deterministic recovery and authoritative event integration.
2. Tasks, Review & Approval, and History dashboard with safe text rendering.
3. Isolated patch application, source revalidation at execution, and allowlisted test execution.
4. End-to-end validation, independent review, and successful hosted CI after the account billing lock is cleared.
