# Automated Repository Gate

The DeepCore repository has GitHub Actions workflows configured for pushes to `main`, pull requests targeting `main`, and manual dispatch. Configuration is **not** proof that a workflow ran.

## Execution Status (2026-10-18 UTC)

**BLOCKED: no verified GitHub-hosted run has passed.** The latest checked PR #44 commit (`995877cd2373a9170b559a5439dbbda13821e787`) generated runs [39099372215](https://github.com/hondabk14-a11y/deepcore-systems-enterprise/actions/runs/39099372215) and [39099374757](https://github.com/hondabk14-a11y/deepcore-systems-enterprise/actions/runs/39099374757); both reported `BuildFailed` / `startup_failure` with zero jobs. No ledger test, compilation, tracked-secret scan, or other CI step executed in those runs.

A separate minimal runner smoke workflow also failed before creating jobs, as recorded in [CI issue #2](https://github.com/hondabk14-a11y/deepcore-systems-enterprise/issues/2). The root cause is **not established**. An account billing/policy restriction, workflow registration problem, or service-side startup failure must be investigated outside workflow steps. Do not remove tests or weaken security controls to make a badge appear green.

**Release decision: HOLD.** PR #44 stays draft until named workflows start real jobs, pass, and produce inspectable evidence. See [Production Gate Runbook](PRODUCTION-GATE-RUNBOOK.md) for exact recovery and acceptance checks.

## Scope of the Repository Gate

When actually executed, the repository production gate is configured to validate:

- Event-sourced ledger tests
- Python compilation
- Tracked-secret detection
- Required repository controls

A successful run is evidence only for the checks actually executed on the recorded commit. It is **not** certification of the complete DeepCore distributed production deployment.

## Production Certification Boundary

Production release requires separately verified, environment-specific evidence including:

- Security controls and threat-model validation
- Cryptographic key custody and hardware-backed boundaries
- Identity and authorization controls
- Observability and alerting
- Failure recovery, disaster recovery, and rollback
- Operational runbooks
- Independent security or engineering review
- Reproducible build and deployment evidence

## Repository Visibility and Secret-Handling Boundary

**The GitHub repository was private when reviewed on 2026-10-18.** Visibility can change; being private does not make credentials safe to commit. No repository visibility setting implies authorization to expose production infrastructure, keys, or private runtime data.

Never commit:

- API keys or access tokens
- Private keys, wallet seeds, or signing secrets
- Passwords or credentials
- Production certificates containing sensitive material
- `.env` secrets
- Unredacted personal or operational secrets
- Local databases or private runtime state

The repository gate is an evidence mechanism. It must not be interpreted as a statement that every DeepCore subsystem is implemented, independently verified, or production-ready.
