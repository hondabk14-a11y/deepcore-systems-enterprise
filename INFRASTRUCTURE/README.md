# Infrastructure

Planned/used platform components:

- Kafka backbone
- NATS dual mesh
- Kubernetes
- Istio mTLS
- SPIFFE identities
- Helm deployment packaging
- ArgoCD GitOps
- Prometheus and Grafana observability
- Docker Compose development environments
- HAProxy and Nginx edge/service infrastructure
- GitHub Actions CI/CD

Infrastructure changes must preserve cryptographic identity, auditability, deterministic recovery, and least-privilege boundaries.