# GitHub to Hugging Face launch

## Implemented scope

This deployment serves the existing DeepCore Python reference ledger with real
Ed25519 signing/verification, signed quorum certificate verification, block
commitment verification, and deterministic replay checks. A failed self-test
prevents service startup. It has no external transaction admission routes.

This is an initial running reference service, not enterprise production
certification. Four identities are simulated in one process. State and signing
identities are regenerated at startup; no durable business ledger is hosted.
HF models and datasets are not given ledger authority by this change.

## Prerequisites and exact launch steps

1. Merge the existing runtime/CI fixes in PR #29, then review and merge the
   deployment PR. This deployment branch is based on PR #29.
2. Resolve GitHub's separate Actions startup blocker. The inspected run
   `35240903488` has `startup_failure` and zero jobs. The connector does not expose
   its diagnostic. Open the run summary in GitHub and follow the actual error;
   do not assume a billing, policy, or YAML cause without the message.
3. In Hugging Face, create a **private Docker Space** owned by `BKillings`, named
   `deepcore-systems-enterprise`. Use CPU Basic for the reference service. Do not
   upload the complete private GitHub repository or change either repo's visibility.
4. Create a Hugging Face token scoped to writing that Space. Store it directly
   in GitHub; never paste it into chat or commit it.
5. In the GitHub repository, open Settings → Environments → New environment:
   `huggingface`. Add environment secret `HF_TOKEN` and environment variable
   `HF_SPACE_ID=BKillings/deepcore-systems-enterprise`.
6. Open Actions → DeepCore Hugging Face Reference Service → Run workflow → main.
   The workflow tests, builds, probes the container, uploads the allowlisted
   sources, and checks the deployed revision. PR events only verify; they never
   deploy and never receive the deployment token.
7. Open the Space while signed in. `/readyz` must return HTTP 200 and
   `/api/status` must show the deployed source SHA and four passing checks.
   A successful upload alone is not a successful deployment.

The currently connected HF OAuth credential has read-repos and jobs scopes but
no repository-write scope. It cannot deploy this Space. Codex Tasks also returned
AuthenticationRequired; that remote environment is not connected for execution.

## Local verification and container reproduction

From the repository root:

```bash
python -m pip install -r deploy/huggingface/requirements.txt 'pytest>=8,<9' 'httpx>=0.27,<1'
python -m pytest -q tests CORE/test_deepcore_consensus_commitment.py
python -m deploy.huggingface.package_space --output /tmp/deepcore-space --source-commit "$(git rev-parse HEAD)"
docker build -t deepcore-reference /tmp/deepcore-space
docker run --rm -p 127.0.0.1:7860:7860 deepcore-reference
```

The package output must not already exist. Runtime dependencies include pinned
FastAPI/Uvicorn versions; the full transitive dependency tree and base image are
not digest-locked. A production reproducibility gate must address that.

## Deployment safety and rollback

The publisher requires an existing private Docker Space, checks its namespace,
and uses the observed HF parent commit to reject concurrent repository changes.
The package excludes treasury source, repository history, credentials, databases,
and local runtime state. Existing unrelated Space files are not deleted.

To roll back, revert the deployment change on GitHub main using normal review,
then dispatch the workflow again. Verify the new source SHA through `/api/status`.
This rolls back this stateless reference service only; no business-state restore
or database rollback is implemented or claimed.

## Evidence and remaining enterprise gates

Local Python 3.12 validation on 2026-09-17: 106 tests passed. The packaged source
also started under Uvicorn and returned verified readiness and status over HTTP.
Docker was not available in the editing environment, so container build validation
is delegated to the workflow and is not yet verified. No HF deployment succeeded
or was attempted without write credentials. No GitHub-hosted passing run is claimed.

Before any production financial workload: implement and verify durable event
storage/recovery, independent validator processes and key custody, authorization
and admission boundaries, external observation adapters, monitoring/alerting,
backup/restore and rollback drills, and independent security review. The existing
production-readiness gates remain authoritative. Do not relabel this simulation
as a live financial system.

References:
- https://huggingface.co/docs/hub/spaces-sdks-docker
- https://huggingface.co/docs/hub/spaces-github-actions
- https://huggingface.co/docs/huggingface_hub/package_reference/hf_api
