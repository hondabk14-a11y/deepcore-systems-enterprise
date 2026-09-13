# Automated Repository Gate

The automated repository gate is installed in GitHub Actions. It runs on pushes to `main`, pull requests targeting `main`, and manual dispatch.

The gate validates the repository checks currently defined by the workflow, including:

- Event-sourced ledger tests
- Python compilation
- Tracked-secret detection
- Required repository controls

A successful run is evidence that these automated repository checks passed. It is **not** certification of the complete DeepCore distributed production deployment.

## Production Certification Boundary

Production release requires additional executable evidence for the production environment and operational boundary, including as applicable:

- Security controls and threat-model validation
- Cryptographic key custody and hardware-backed boundaries
- Identity and authorization controls
- Observability and alerting
- Failure recovery and disaster recovery
- Rollback procedures
- Operational runbooks
- Independent security or engineering review
- Reproducible build and deployment evidence

## Public Repository Boundary

This repository is public by design. Public source does not imply public runtime access, credentials, private keys, production infrastructure access, or authorization to operate external systems.

Never commit:

- API keys or access tokens
- Private keys, wallet seeds, or signing secrets
- Passwords or credentials
- Production certificates containing sensitive material
- `.env` secrets
- Unredacted personal or operational secrets
- Local databases or private runtime state

The repository gate is a control and evidence mechanism. It must not be interpreted as a blanket statement that every DeepCore subsystem is implemented, independently verified, or production-ready.
