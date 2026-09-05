# Production Gate Runbook

1. Push or merge a change into `main`, or start `DeepCore Production Gate V3` manually with `workflow_dispatch`.
2. Require a successful Production Gate run before release.
3. Confirm ledger tests and compilation pass.
4. Confirm tracked-secret detection passes.
5. Confirm required repository controls are present.
6. Separately validate production infrastructure, cryptographic key custody, consensus configuration, observability, backups, recovery, and rollback before deploying.

A green GitHub Actions gate is necessary evidence, not a blanket certification of the entire production system.
