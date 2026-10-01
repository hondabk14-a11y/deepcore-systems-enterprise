"""Optional OpenTelemetry support for DeepCore runtime observability.

Telemetry is observational only. It must never participate in consensus,
authorization, ledger state transitions, signature verification, or replay.
The module is deliberately lazy-loaded so DeepCore can run without OTel
packages installed or a collector available.
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Iterator


_TRUE_VALUES = {"1", "true", "yes", "on"}


@dataclass
class _TelemetryState:
    enabled: bool = False
    initialized: bool = False
    provider: Any | None = None
    tracer: Any | None = None
    openai_instrumented: bool = False
    error: str | None = None


_STATE = _TelemetryState()


class _NoopSpan:
    def set_attribute(self, _key: str, _value: Any) -> None:
        return None

    def record_exception(self, _exception: BaseException) -> None:
        return None

    def set_status(self, *_args: Any, **_kwargs: Any) -> None:
        return None


def telemetry_enabled() -> bool:
    return os.getenv("DEEPCORE_TELEMETRY_ENABLED", "").strip().lower() in _TRUE_VALUES


def _openai_instrumentation_enabled() -> bool:
    return os.getenv("DEEPCORE_OTEL_INSTRUMENT_OPENAI", "").strip().lower() in _TRUE_VALUES


def initialize_telemetry(
    service_name: str = "deepcore-enterprise-agent",
    service_version: str = "1.0.0",
) -> bool:
    """Initialize OTLP tracing when explicitly enabled.

    Returns True only when a tracer was initialized successfully. Failures are
    captured in telemetry_status() and do not prevent DeepCore startup.
    """
    if _STATE.initialized:
        return _STATE.enabled

    _STATE.initialized = True

    if not telemetry_enabled():
        return False

    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        resource = Resource.create(
            {
                "service.name": service_name,
                "service.namespace": "deepcore",
                "service.version": service_version,
                "deployment.environment.name": os.getenv("ENVIRONMENT", "production"),
            }
        )

        endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
        exporter = OTLPSpanExporter(
            endpoint=endpoint,
            insecure=endpoint.startswith("http://"),
        )
        processor = BatchSpanProcessor(exporter)

        current_provider = trace.get_tracer_provider()
        if hasattr(current_provider, "add_span_processor"):
            provider = current_provider
            provider.add_span_processor(processor)
            owns_provider = False
        else:
            provider = TracerProvider(resource=resource)
            provider.add_span_processor(processor)
            trace.set_tracer_provider(provider)
            owns_provider = True

        tracer = trace.get_tracer("deepcore.ai.tracer", service_version)

        _STATE.provider = provider if owns_provider else None
        _STATE.tracer = tracer
        _STATE.enabled = True

        if _openai_instrumentation_enabled():
            try:
                from opentelemetry.instrumentation.openai_v2 import OpenAIInstrumentor

                OpenAIInstrumentor().instrument(tracer_provider=provider)
                _STATE.openai_instrumented = True
            except Exception as exc:  # instrumentation must remain non-authoritative
                _STATE.error = f"OpenAI instrumentation unavailable: {exc}"

        return True

    except Exception as exc:  # telemetry must fail open
        _STATE.enabled = False
        _STATE.error = str(exc)
        return False


@contextmanager
def start_span(name: str, attributes: dict[str, Any] | None = None) -> Iterator[Any]:
    """Create an observability span or a no-op span when telemetry is disabled."""
    if not _STATE.enabled or _STATE.tracer is None:
        yield _NoopSpan()
        return

    from opentelemetry.trace import Status, StatusCode

    with _STATE.tracer.start_as_current_span(name) as span:
        span.set_attribute("deepcore.telemetry.authority", "observational-only")
        for key, value in (attributes or {}).items():
            span.set_attribute(key, value)

        try:
            yield span
            span.set_status(Status(StatusCode.OK))
        except Exception as exc:
            span.record_exception(exc)
            span.set_status(Status(StatusCode.ERROR, str(exc)))
            raise


def telemetry_status() -> dict[str, Any]:
    return {
        "configured": telemetry_enabled(),
        "enabled": _STATE.enabled,
        "initialized": _STATE.initialized,
        "openai_instrumented": _STATE.openai_instrumented,
        "error": _STATE.error,
    }


def shutdown_telemetry() -> None:
    """Flush and close the provider if this module initialized one."""
    provider = _STATE.provider
    if provider is None:
        return

    shutdown = getattr(provider, "shutdown", None)
    if callable(shutdown):
        try:
            shutdown()
        except Exception:
            pass
