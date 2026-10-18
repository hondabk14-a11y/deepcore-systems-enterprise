# Production Gate Runbook

## A. Pre-job GitHub Actions recovery

A workflow run whose conclusion is `startup_failure`, whose path is `BuildFailed`, and which has zero jobs **did not run the repository's tests**. This cannot be fixed by changing a Python test or adding a runner step: no runner step has started.

Confirmed examples as of 2026-10-18:

- Main commit `a3298ddb4b54f7ec636761e84e5d7726fcab6c34`: [run 39098704987](https://github.com/hondabk14-a11y/deepcore-systems-enterprise/actions/runs/39098704987), synthetic workflow ID `350815380`, zero jobs.
- PR #44 commit `995877cd2373a9170b559a5439dbbda13821e787`: [run 39099372215](https://github.com/hondabk14-a11y/deepcore-systems-enterprise/actions/runs/39099372215) and [run 39099374757](https://github.com/hondabk14-a11y/deepcore-systems-enterprise/actions/runs/39099374757), same startup-failure signature.
- A minimal, one-step runner smoke workflow also failed before any job ran. See [issue #2](https://github.com/hondabk14-a11y/deepcore-systems-enterprise/issues/2).

### Administrator checklist

1. Review **account Billing & licensing / Budgets and alerts** for Actions usage, payment holds, and budget limits. This private repository uses GitHub-hosted runners, so billing or usage policy can prevent jobs from starting. Do not increase a budget without considering cost exposure.
2. In repository **Settings > Actions > General**, verify Actions is enabled and the applicable actions/reusable-workflow policy allows the configured workflows. Check upstream policies if applicable.
3. Inspect run annotations and the workflow registry using the GitHub UI. If the `gh` CLI is authenticated with access to the private repository, obtain read-only evidence:

   ```bash
   gh api repos/hondabk14-a11y/deepcore-systems-enterprise/actions/runs/39099374757 \
     --jq '{id, name, path, workflow_id, status, conclusion, head_sha}'
   gh api repos/hondabk14-a11y/deepcore-systems-enterprise/actions/runs/39099374757/jobs \
     --jq '{total_count, jobs: [.jobs[] | {name, conclusion}]}'
   gh api repos/hondabk14-a11y/deepcore-systems-enterprise/actions/workflows \
     --jq '.workflows[] | {id, name, path, state}'
   gh api repos/hondabk14-a11y/deepcore-systems-enterprise/actions/permissions
   ```

4. If settings and billing are healthy and zero-job failures persist, [contact GitHub Support](https://support.github.com/contact), requesting investigation of workflow registration/dispatch, account restrictions, and the synthetic `BuildFailed` record. Include repository, affected run IDs, workflow ID `350815380`, observed `startup_failure`, and the minimal smoke reproduction. **Do not delete or disable the synthetic workflow solely on the assumption that its existence caused the failure.**
5. Once the issue is corrected, trigger `DeepCore Diagnostic Test` manually or through a relevant event. Verify its **named job** starts, reaches actual steps, emits runner logs, and completes successfully.

## B. Verify the canonical CI gates

After the diagnostic genuinely passes:

1. Run or trigger **DeepCore CI** and **DeepCore Runtime Verification**; inspect the runtime and cryptography tests.
2. Run **DeepCore Ledger Tests**, **DeepCore Security Gate**, and **DeepCore Production Gate**; inspect test logs, secret checks, and production-gate evidence.
3. Run **DeepCore Readiness Preflight** and, for AI bridge/extension changes, **DeepCore VS Code Extension Package**; inspect artifacts and their commit identity.
4. Require all checks needed for the target commit to have completed with a successful conclusion. Fix any actual job-level failures shown by logs. Do not mistake absence of checks, empty status arrays, or a completed `startup_failure` run for success.
5. Keep PR #44 as draft until hosted checks pass and independent review completes. Do not merge or release solely on local tests or a passing smoke diagnostic.

## C. Deployment certification remains separate

A green repository gate is necessary but insufficient evidence for production. Separately verify actual production infrastructure, cryptographic key custody, consensus configuration, observability, backup/restore, recovery, rollback, and independent review. Until that evidence exists, use the decision `NOT_CERTIFIED`.

Track the ongoing infrastructure blocker in [GitHub issue #2](https://github.com/hondabk14-a11y/deepcore-systems-enterprise/issues/2) and its implementation branch in [PR #44](https://github.com/hondabk14-a11y/deepcore-systems-enterprise/pull/44).
