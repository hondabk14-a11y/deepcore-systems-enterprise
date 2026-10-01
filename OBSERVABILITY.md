# DeepCore OpenTelemetry observability

This document describes the optional OpenTelemetry boundary introduced by
`CORE/deepcore_telemetry.py`.

## Authority boundary

Telemetry is observational only. Trace export, collectors, dashboards, OpenAI
instrumentation, or telemetry failures MUST NOT participate in or influence:

- transaction validity;
- authorization decisions;
- quorum formation or certificate validity;
- block commitments;
- validator signatures or key custody;
- deterministic replay;
- ledger state transitions.

DeepCore must continue authoritative execution when telemetry is disabled,
misconfigured, unavailable, or unable to reach its collector.

## Installation

Core DeepCore dependencies remain in `requirements.txt`. Optional observability
packages are isolated in:

```text
requirements-observability.txt
```

Install them only in environments that require telemetry:

```bash
python -m pip install -r requirements.txt
python -m pip install -r requirements-observability.txt
```

## Configuration

Telemetry is disabled by default.

Enable OTLP tracing:

```bash
export DEEPCORE_TELEMETRY_ENABLED=1
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
export ENVIRONMENT=development
```

OpenAI SDK auto-instrumentation is separately gated:

```bash
export DEEPCORE_OTEL_INSTRUMENT_OPENAI=1
```

Do not enable prompt/completion content capture by default. Sensitive prompts,
credentials, private ledger material, signing material, transaction payloads,
or personally identifying data must not be added to span attributes.

## Runtime behavior

When tracing is disabled, `start_span()` returns a no-op span and the runtime
continues normally.

When tracing is enabled but OpenTelemetry initialization fails,
`initialize_telemetry()` records the failure in `telemetry_status()` and
returns `False`. Runtime execution continues.

When OpenAI instrumentation is requested but unavailable, base telemetry can
remain enabled while the instrumentation error is reported in telemetry status.

## Verification

Minimum verification before this feature can leave draft status:

```bash
python -m pytest -q tests/test_deepcore_telemetry.py
python -m CORE.deepcore_runtime
```

Then install `requirements-observability.txt` in an isolated environment and
repeat with:

```bash
DEEPCORE_TELEMETRY_ENABLED=1 \
OTEL_EXPORTER_OTLP_ENDPOINT=http://127.0.0.1:4317 \
python -m CORE.deepcore_runtime
```

An unavailable collector may prevent export, but it must not alter DeepCore
ledger results or make authoritative execution fail.

## Merge dependency

This branch is based on `main`, whose current runtime workflow still invokes
`python CORE/deepcore_runtime.py`. PR #29 contains the verified module-invocation
fix to `python -m CORE.deepcore_runtime`. Do not duplicate that change in this
observability branch. Validate and integrate the PR #29 runtime/CI line first,
then rebase or retarget this observability work and rerun the tests.
