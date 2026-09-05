# SPIFFE and Istio mTLS

DeepCore's distributed security model uses workload identity and mutually authenticated transport.

## Baseline

- SPIFFE identities provide workload-level cryptographic identity.
- Istio mTLS protects service-to-service communication.
- Authorization is independent of network location.
- Identity validation is fail-closed.
- Certificate rotation should be automated and auditable.

## Integration

The model is intended to sit alongside the private PKI, event-sourced audit trail, invariant engine, and SSIL controls. Kubernetes deployment should preserve identity across scheduling, restart, and recovery.

Production configuration must be validated in a controlled environment before deployment.