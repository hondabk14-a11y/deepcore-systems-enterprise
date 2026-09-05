# NATS

NATS provides the low-latency messaging path in the DeepCore dual-mesh architecture.

## Responsibilities

- Service-to-service messaging where low latency is important.
- Request/reply and pub/sub communication.
- Lightweight coordination between runtime components.
- Operational messaging that does not replace the durable event history.

Kafka remains the durable event-stream reference path. NATS must not become an undocumented source of authoritative state.