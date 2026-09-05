# Consensus

DeepCore consensus architecture uses a HotStuff-style Byzantine fault tolerant model with quorum certificates, BLS signatures, and adversarial-node simulation.

Formal verification is intended to constrain consensus invariants before runtime enforcement.

Planned implementation baseline:

- Rust consensus/QC engine
- Go transport layer
- Python orchestration
- Dockerized execution
- Redis/Kafka integration
- Real BLS implementation using `blst`