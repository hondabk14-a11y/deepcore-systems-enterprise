# Kafka

Kafka is the durable event-stream backbone for DeepCore components that require ordered, replayable event delivery.

## Responsibilities

- Publish domain and infrastructure events.
- Partition streams according to documented ordering requirements.
- Retain events long enough to support replay and recovery objectives.
- Support consumer groups for independent projections and services.
- Preserve event schemas and compatibility rules.

## DeepCore requirements

Events are inputs to deterministic reducers and must be authenticated and validated at service boundaries. Consumers must be idempotent where duplicate delivery is possible. Kafka availability must not silently authorize invalid state transitions.