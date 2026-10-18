# DeepCore Live Operations Dashboard

A responsive dashboard inspired by the provided DeepCore network screenshot. Built as a standalone, dependency-free extension to the existing `SIMULATION/command-center` work in PR #41.

## Run locally

From `SIMULATION/command-center`:

```bash
python telemetry_server.py
# open http://127.0.0.1:4174/live.html
```

The default view uses **illustrative sample data**, with a prominent DEMO label. Nothing in the example metrics, network map, risk chart, consensus display, or events is a measurement of an actual DeepCore network. It cannot submit transactions, change validators, move value, modify ledger state, or control infrastructure.

## Connect read-only real telemetry

Configure an existing HTTP(S) endpoint returning a JSON snapshot. The endpoint must be operated separately and must use the exact schema described below. The dashboard **does not** discover, ingest, or invent production metrics by itself.

```bash
export DEEPCORE_TELEMETRY_URL='http://127.0.0.1:9000/telemetry/snapshot'
# Optional, set privately (never commit or paste the token):
# export DEEPCORE_UPSTREAM_TOKEN='...'
python telemetry_server.py
```

Open the dashboard and switch **DATA SOURCE → Live API**. The server does a bounded GET, validates the payload, and returns it from `/api/telemetry`. If it is missing, malformed, unavailable, or more than two minutes stale, the UI shows an error or stale state; it never swaps in fake green operational metrics. Polling can be set to 5, 15, 30, or 60 seconds; refresh, pause, node selection, search, severity filtering, time-range filtering, and JSON event export work locally. The graph is a **sampled visualization** of up to 150 upstream nodes, not a claim to render every node in a very large network.

The expected JSON includes UTC timestamp with timezone, `metrics`, `consensus`, `nodes`, `flows`, `events`, `liquidity`, and `distribution`:

```json
{
  "timestamp":"2026-10-18T08:00:00+00:00",
  "metrics":{"totalNodes":1,"valueLockedUsd":123,"healthPercent":96,"energyPw":0.5,"riskIndex":0.18,"blockHeight":1234,"flow24hUsd":120,"threats":0},
  "consensus":{"round":100,"status":"COMMITTED","progress":100},
  "nodes":[{"id":"N-001","role":"CORE","x":450,"y":255,"health":96,"risk":0.18,"energy":0.9}],
  "flows":[],
  "events":[{"id":"evt-1","time":"2026-10-18T08:00:00+00:00","kind":"CONSENSUS","nodeId":"N-001","message":"Commit observed"}],
  "liquidity":[{"name":"Pools","share":100}],
  "distribution":[{"name":"DeFi","share":100}]
}
```

**Security:** The backend binds only `127.0.0.1`; do not expose it as a public service without authenticated, TLS-terminated access control and network segmentation. Upstream URL and optional bearer token are server-side environment configuration; they are never sent to the browser. No redirects are followed, payload size is capped at 512 KiB, and snapshot field types/ranges are validated. The proxy contains no write endpoints. The client renders all external labels and event messages via text nodes, not `innerHTML`.

**Important:** There is no production telemetry source configured in this package. Energy units and finance metrics are UI examples until a real, authorized source supplies those exact measurements.

## Validate

```bash
python -m unittest discover -s . -p 'test_live.py' -v
node --check live.js
```

Browser rendering and live production instrumentation must be tested independently. This module has no dependencies on real custodied funds, wallets, signing keys, or authoritative consensus state.