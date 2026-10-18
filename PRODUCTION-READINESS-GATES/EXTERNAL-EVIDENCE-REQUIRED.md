# DeepCore Systems Enterprise: External Evidence Requirements

**Status:** OPEN / BLOCKING FOR PRODUCTION CERTIFICATION

Repository-side controls are implemented, but production certification requires evidence from systems outside the source tree.

## Required evidence

1. GitHub Actions: successful execution of canonical CI, security, packaging, and readiness-preflight workflows.
2. Workflow hygiene: stale registered workflow `BuildFailed` (workflow ID `350815380`) disabled or removed by an account with Actions administration permission.
3. Infrastructure: production environment health checks executed against the intended deployment.
4. Key custody: production HSM/KMS custody and key-boundary evidence.
5. Backup/restore: authorized production restore drill with integrity verification.
6. Rollback: authorized deployment rollback drill with successful recovery verification.
7. Observability: production telemetry, alerting, and incident-response evidence.
8. Independent review: evidence independently checked before certification.

## Current boundary

No repository commit can manufacture any of the above evidence. Synthetic tests and configuration checks remain useful controls, but they do not certify an external production environment.

## Current classification

**REFERENCE CORE / CI AND EXTERNAL EVIDENCE PENDING**

**PRODUCTION CERTIFICATION: NOT CERTIFIED**
