# Adversarial Consensus Simulation

This track defines testing for Byzantine, faulty, delayed, partitioned, and restarted nodes before consensus components are considered production-ready.

## Scenarios

- Byzantine proposals and conflicting votes.
- Equivocation and duplicate messages.
- Network delay, loss, duplication, and reordering.
- Leader failure and view changes.
- Node restart and state recovery.
- Partial network partitions.
- Malformed or invalid cryptographic proofs.
- Resource pressure and message floods.

## Safety properties

Simulation should verify that invalid transitions are rejected, quorum rules are respected, committed state does not diverge under the modeled fault assumptions, and recovery remains deterministic.

Simulation results should be reproducible and stored as test artifacts. A passing simulation is evidence for the tested model, not proof of unrestricted production safety.