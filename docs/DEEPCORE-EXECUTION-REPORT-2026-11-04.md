# DeepCore execution and verification — 2026-11-04

**Deployment readiness: NOT READY / NOT CERTIFIED.** No merge, deployment, production transaction, or external signing was performed.

Repository: `hondabk14-a11y/deepcore-systems-enterprise`; baseline `e48c05b2092f2b4110ab9e9f908608b872d0294e`; branch `feat/deepcore-execution-verification`.

Execution used the attached Codex environment `ccarenv_b64_Y2NhcmVudl9lZDlkNWZlZGEwN2M4MTkxODAzYjQ0NDNjZTBhZDA4Yg`, not the requested UUID `01a0f6fb-1aa7-73f6-9dc1-41a8ad0b203e`, which was not an available tool target. Python 3.12.14 and Node 24.22.1 were available. GitHub CI specifies Python 3.11/3.12 and Node 20; those additional versions were not exercised.

## Bootstrap and commands

The workspace initially had no checkout. Initial clone failed because the configured proxy was unavailable; clone succeeded after the environment restarted. No credentials were needed for the public checkout. The GitHub connector reports the repository as public, despite the README describing it as private; an owner should review this discrepancy.

From repository root:

```sh
python -m venv .venv
.venv/bin/python -m pip install -r requirements.txt -r CORE/event-sourced-ledger/requirements-test.txt
.venv/bin/python -m pip install 'jsonschema>=4.23,<5.0'
.venv/bin/python -m pip check
.venv/bin/python -m CORE.deepcore_runtime
.venv/bin/python -m pytest -q --tb=no
.venv/bin/python -m unittest discover -s CORE/event-sourced-ledger -p 'test_*.py' -v
.venv/bin/python -m unittest discover -s SECURITY/SSIL -p 'test_ssil*.py' -v
.venv/bin/python -m unittest PRODUCTION-READINESS-GATES/test-readiness-evidence-event.py PRODUCTION-READINESS-GATES/test-record-readiness-evidence.py PRODUCTION-READINESS-GATES/test-write-readiness-ssil-audit-record.py
node --test AI/deepcore-ai-bridge/test-local-inference-health-check.mjs
node --check AI/deepcore-ai-bridge/vscode-extension/extension.js
```

Dependency installation succeeded; `pip check` reported `No broken requirements found.` Exact installed versions are retained in [packages.txt](verification-2026-11-04/packages.txt). Only the advisory agent's JSON Schema dependency was needed for its no-network tests; its full optional MCP/OpenAI/Gradio stack was not installed or exercised.

There is no verified enterprise service bootstrap, container stack, or Kubernetes deployment command in this checkout. Infrastructure, Bitcoin, BLS, formal verification, and kernel orchestration directories mainly describe intended architecture. The actual deployment workflow is `.github/workflows/static.yml`: it uploads the entire checkout to GitHub Pages, then runs `actions/deploy-pages@v5`. It was inspected, never invoked. Publishing the entire source checkout merits explicit owner review given the README's privacy requirements.

## Actual results

Counts below overlap and must not be summed.

| Executed check | Actual result |
| --- | --- |
| Initial root pytest | Collection interrupted: 3 errors |
| Final root pytest after import fixes and JSON Schema installation | **266 passed, 18 failed**, 0.57s |
| Ledger workflow unittest command | **97 run; 1 failure, 7 errors** (89 passed) |
| Runtime, consensus, transport, persistence, fault, UST tests plus consensus-commitment tests | **88 passed, 3 failed** |
| SSIL unittest discovery | **51 passed** |
| Focused SSIL, crypto, key registry, UST controls/gates/settlement pytest | **80 passed** |
| Deterministic replay, adversarial replay, replay completeness, domain-state attacks | **16 passed** |
| Readiness tests explicitly named above | **11 run; 1 failed, 10 passed** |
| Advisory agent tests (included in final pytest after installing jsonschema) | **6 passed** |
| Node local inference health-check tests | **4 passed** |
| Extension JavaScript syntax | Exit 0 |
| `py_compile CORE/*.py PRODUCTION-READINESS-GATES/*.py` | Exit 0 |
| Local infrastructure, synthetic backup/restore, synthetic rollback, observability contract preflights | Each exit 0 |
| Key custody repository preflight | **Exit 1**; path/pattern findings retained without values |
| Gate summary | Exit 0; explicitly **NOT CERTIFIED**, external evidence pending |
| `git diff --check` | Exit 0 |

Unittest discovery with `-p 'test-*.py'` found **zero tests**; it is not counted as validation. Explicit file arguments were used afterward.

The module runtime demo exited 0, reporting `validators=4 f=1 quorum=3`, `block_height=1`, `qc_verified=True`, and `ssil_score=0.1075 category=accept`. It emitted public commitments only. Several printed verification labels in the demo are literal strings; the separate automated tests provide the meaningful validation evidence. Direct execution with `python CORE/deepcore_runtime.py` failed with `ModuleNotFoundError: No module named 'CORE'`.

## Failures and limits

Final root pytest's exact failing test names are in [full-final.txt](verification-2026-11-04/full-final.txt).

- Seven signed-checkpoint tests supply callable resolvers while `verify_signed_checkpoint` requires `.resolve()`. Signature verification is therefore not fully green; registry/vector tests do pass. No compatibility fallback was introduced at this trust boundary.
- Malformed persisted JSON test expects an exception, but verification returns false at an earlier invalid record. Both reject the ledger, but error-contract expectations disagree.
- Consensus wrong-proposal test changes `block_hash`, which the current pre-certificate digest excludes. The proposal/committed-block distinction needs a focused review before changing the commitment scheme.
- HotStuff determinism test compares independently generated cryptographic identities/signatures; differing inputs produce differing commitments. Reproducibility with identical signed inputs is a different claim.
- Weighted-quorum test expects weight 5 of 7 to fail, while the implementation accepts its configured two-thirds weight rule. Required voter-count versus weight semantics need explicit resolution.
- Seven market-data failures: two admission expectations return false and five verification fixtures raise `ValueError: market price event requires a CoinGecko observation`. The CoinGecko adapter source boundary and test fixtures need reconciliation.
- One separately executed readiness-ledger test compares the returned unchained event with a replayed record containing ledger-managed fields. This is a failing test expectation; the report does not call the chain fully verified.
- Key-custody preflight flags `.env.example` and possible embedded patterns in nine tracked paths. Pattern matches alone do not establish leaked credentials. Values were not included in the evidence. No broad allowlist or secret-check bypass was added.

Nonce/replay protection, event/state roots, tamper detection, cryptographic vectors, persistent recovery, SSIL adversarial policy regressions, and audit-chain controls have executable coverage in the runs above. Passing subsets do not certify all these boundaries: the checkpoint, consensus, and readiness failures remain release blockers.

No executable execution-DAG verifier or QSI stability calculation was found. `ARCHITECTURE/qsi-quantum.md` describes quantum augmentation, not a stability index. DAG/QSI checks are **blocked by absent implementations**, not passed. Live Bitcoin/Lightning/Liquid, production Kafka/NATS/Kubernetes, HSM/KMS custody, independent BLS validation, formal proof/model checking, live market/API integrations, VSIX packaging, and production recovery/observability were **not executed**. No external endpoints or production credentials were substituted to manufacture results.

## GitHub Actions diagnostics

Six existing failed runs were inspected through jobs and check annotations: CI `40265569099`, Production Gate `40265569133`, Readiness `40265569124`, Ledger `40265569106`, Security `40265569127`, Runtime `40265569057`. These runs target PR commit `a77c8a231f79453469a107253965d215504b2006`, not the checked-out main baseline.

The sampled jobs have zero executed steps. GitHub's failure annotation says: **“The job was not started because your account is locked due to a billing issue.”** Thus these remote failures do not prove tests ran or failed. Structured diagnostic evidence is in [github-diagnostics.json](verification-2026-11-04/github-diagnostics.json). Job-log retrieval was attempted but denied; no runner logs are claimed available. Reproduce metadata collection with:

```sh
gh run list --repo hondabk14-a11y/deepcore-systems-enterprise --limit 12 --json databaseId,name,conclusion,headSha,url
gh api repos/hondabk14-a11y/deepcore-systems-enterprise/actions/runs/40265569099/jobs
gh api repos/hondabk14-a11y/deepcore-systems-enterprise/check-runs/121387131478/annotations
```

Billing remediation requires the account owner; repository changes cannot fix it. No workflows were dispatched or deployments authorized.

## Fixes prepared for review

- Use module invocation in the two runtime workflows, matching the executable package imports.
- Remove the CI argument naming nonexistent `MARKET-DATA/test_coingecko_observation.py`; keep the existing SDK adapter suite. Missing observation-specific coverage remains a gap.
- Rename readiness evidence module to match its existing import sites, restoring SSIL audit test collection and readiness CLI imports.
- Register the dynamically loaded market-admission module before executing its dataclass definitions.
- Make readiness test loading independent of the working directory and correctly load hyphenated CLI filenames. This exposes the previously hidden readiness assertion failure.

These changes repair execution and test discovery without weakening cryptography, consensus, authorization, or ledger checks. Remaining behavior and contract failures are intentionally visible for review. Production readiness requires resolving those failures, restoring hosted CI, and supplying independently reviewed infrastructure, custody, recovery, and operational evidence.
