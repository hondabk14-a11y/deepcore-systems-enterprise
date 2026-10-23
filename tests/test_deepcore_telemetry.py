"""Tests for DeepCore's optional telemetry boundary."""

import builtins

from CORE import deepcore_telemetry as telemetry


def reset_state():
    telemetry._STATE.enabled = False
    telemetry._STATE.initialized = False
    telemetry._STATE.provider = None
    telemetry._STATE.tracer = None
    telemetry._STATE.openai_instrumented = False
    telemetry._STATE.error = None


def test_telemetry_is_disabled_by_default(monkeypatch):
    reset_state()
    monkeypatch.delenv("DEEPCORE_TELEMETRY_ENABLED", raising=False)

    assert telemetry.telemetry_enabled() is False
    assert telemetry.initialize_telemetry() is False
    assert telemetry.telemetry_status()["enabled"] is False


def test_noop_span_preserves_runtime_flow(monkeypatch):
    reset_state()
    monkeypatch.delenv("DEEPCORE_TELEMETRY_ENABLED", raising=False)

    with telemetry.start_span("deepcore.test") as span:
        span.set_attribute("deepcore.test", True)
        result = 2 + 2

    assert result == 4


def test_missing_otel_dependencies_fail_open(monkeypatch):
    reset_state()
    monkeypatch.setenv("DEEPCORE_TELEMETRY_ENABLED", "1")

    original_import = builtins.__import__

    def guarded_import(name, *args, **kwargs):
        if name == "opentelemetry" or name.startswith("opentelemetry."):
            raise ImportError("simulated missing OpenTelemetry dependency")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", guarded_import)

    assert telemetry.initialize_telemetry() is False
    status = telemetry.telemetry_status()
    assert status["configured"] is True
    assert status["enabled"] is False
    assert "simulated missing OpenTelemetry dependency" in status["error"]
