# Istio and SPIFFE

Istio provides the service-mesh enforcement layer, while SPIFFE provides workload identity for authenticated service communication.

## Security model

- Workloads receive explicit identities.
- mTLS protects service-to-service transport.
- Authorization is based on authenticated workload identity and policy, not network location alone.
- Certificate rotation should be automated and observable.
- Policies should fail closed for missing or invalid identity.

Identity issuance, authorization, and application invariants remain separate concerns. A valid mTLS connection does not by itself authorize a financial or state-changing operation.