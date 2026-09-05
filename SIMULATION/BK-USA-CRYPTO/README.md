# B.K./U.S.A. CRYPTO Baseline

AFSS v4 hybrid distributed-financial simulation baseline.

## Reference nodes

| Node | ID | Port | Role | Trust | Consensus weight |
|---|---:|---:|---|---:|---:|
| UST | 0001 | 8000 | Root Ledger Authority | 1.00 | 35% |
| BKA | 1001 | 8001 | Distributed node | 0.85 | 20% |
| BKB | 1002 | 8002 | Distributed node | 0.85 | 20% |
| GOV | 2001 | 8003 | Government node | 0.95 | 25% |

## v2 direction

Multi-language consensus lab using Rust for the HotStuff/QC engine, Go for transport, and Python for orchestration, with Dockerized deployment and Redis messaging. Planned expansion includes Kafka, Kubernetes, ChaosMesh, and production-grade BLS.