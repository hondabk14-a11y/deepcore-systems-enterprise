# Argo CD

Argo CD is the GitOps deployment layer for declarative DeepCore infrastructure and service configuration.

## Responsibilities

- Reconcile approved Git state into deployment environments.
- Provide deployment history and observable synchronization state.
- Support controlled promotion and rollback.
- Keep infrastructure changes reviewable and auditable.

## Security requirements

Production credentials and private keys must remain outside Git. Repository access, deployment permissions, image provenance, environment separation, and rollback authority must be explicitly controlled.

Git state is desired configuration, not a substitute for runtime authorization or ledger truth.