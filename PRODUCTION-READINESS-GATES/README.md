# DeepCore Systems Enterprise Production Readiness Gates

This directory defines the evidence gates required before DeepCore Systems Enterprise can be classified as production-certified.

## Gate policy

A gate is **GREEN** only when its required evidence has actually been produced and independently checked. Creating a script or checklist does not make the gate pass.

| Gate | Required evidence | Current state |
|---|---|---|
| CI | Successful GitHub Actions Production Gate | RED / evidence pending |
| Security | Successful Security Gate and CodeQL result | RED / evidence pending |
| Packaging | Successful VSIX build and artifact | RED / evidence pending |
| Workflow hygiene | Stale `BuildFailed` registration disabled/removed | RED / admin action pending |
| Infrastructure | Health and dependency validation | RED / execution pending |
| Key custody | Key isolation and signing controls verified | RED / execution pending |
| Backup/restore | Successful restore and integrity/replay verification | RED / execution pending |
| Rollback | Successful rollback with integrity verification | RED / execution pending |
| Observability | Metrics, logs, alerts, and audit evidence | RED / execution pending |

## Release rule

`PRODUCTION-CERTIFIED` requires all mandatory gates to be GREEN. A passing unit-test suite is necessary evidence for the implemented core, but is not sufficient evidence for the complete distributed enterprise system.

## Evidence standard

Each gate should record:

1. exact commit/release identifier;
2. execution timestamp;
3. environment and configuration scope;
4. commands or workflow used;
5. expected result;
6. observed result;
7. logs/artifacts or equivalent evidence;
8. reviewer/verification record;
9. rollback or remediation outcome when applicable.

## Safety boundary

Never commit secrets, private keys, wallet seeds, credentials, production tokens, or unredacted sensitive data. Evidence must be sanitized before entering the repository.

## Current classification

**PRODUCTION-CANDIDATE / CI-VERIFIED CORE**

This framework intentionally keeps unexecuted controls RED. Humans have apparently decided that changing a checkbox is easier than proving a distributed system works, so this repository does the opposite.