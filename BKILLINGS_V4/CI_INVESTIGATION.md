# CI startup investigation — 2026-09-26

## Observed evidence

GitHub run 36233829984, source commit 7e2cc5c804bad76a48cfacbd4990f59c6944a826, concludes `startup_failure`. The raw run metadata reports `path: BuildFailed`, an empty workflow name and check suite 98123442645. Its job list is empty. No runtime test command executed in that run.

The label `BuildFailed` alone does not establish a root cause, prove that an obsolete workflow exists, or justify disabling checks. The available GitHub connector can read the run and repository files, but rejects the check-suite/check-runs and workflow-detail endpoints. Detailed server annotations therefore remain unavailable here. No billing, permission, runner, or YAML cause is asserted.

Run: https://github.com/hondabk14-a11y/deepcore-systems-enterprise/actions/runs/36233829984

## Concrete changes

1. Add `.github/workflows/bkillings-v4.yml`. Existing workflows did not exercise the new BKILLINGS_V4 directory. The new workflow runs the 24 hardening tests, starts the independent-process harness, validates newly generated results, binds them to the workflow source SHA/run ID/attempt, and uploads only that run's evidence. It uses read-only repository access and does not deploy or require secrets.
2. Remove the unsupported instruction in `diagnostic-test.yml` telling operators to disable a supposedly stale BuildFailed workflow. Replace it with annotation inspection and an explicit instruction not to disable verification checks to conceal failure.

These are coverage and diagnostic-correctness fixes, not a claimed fix for the platform startup failure.

## Local validation

- Nine workflow YAML documents parsed with duplicate-key rejection.
- All 48 shell blocks passed `bash -n`.
- Basic structural checks verified job/step presence and exactly one run/uses per step.
- 24 BKILLINGS_V4 hardening tests passed again.
- Four-process harness passed again, including one offline validator, persistent vote lock across restart, certificate rejection and recovered finalized identity/head.
- The new workflow's evidence-validation script passed locally using RUN_ID=local.

This is not actionlint, GitHub server validation, or successful hosted execution. Existing runtime entrypoint changes are already proposed separately in PR #29; this change does not duplicate or merge them. No required workflow was disabled, no branch protection changed, and no merge or deployment performed.

## Remaining blocker

Open the failed run's summary/check annotation while signed into GitHub and capture the exact error text. A screenshot is sufficient. Use that diagnostic to choose the next repair; retrying zero-job runs or guessing at account settings provides no evidence. Hosted CI must create jobs and pass on the reviewed source before it can be counted as verification.
