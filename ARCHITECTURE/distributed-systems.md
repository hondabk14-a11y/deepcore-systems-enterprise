# Distributed Systems

## Messaging

- Kafka provides the durable backbone/event stream.
- NATS provides the low-latency dual-mesh communication layer.
- Reducers materialize deterministic state from events.
- Invariant services evaluate state-transition constraints.
- The kernel orchestrator coordinates system-level execution.
- The replay engine reconstructs state from the event history.

## Platform

Planned infrastructure includes Kubernetes, Helm, ArgoCD GitOps, Istio service networking, SPIFFE identity, Prometheus, and Grafana.

## Determinism

State transitions should be represented as explicit events, validated before commitment, and replayable from a known event history.
