#!/usr/bin/env bash
set -euo pipefail
simulation_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$simulation_root"
exec python -m SIMULATION.local_server \
  --state-dir "${DEEPCORE_SIMULATION_STATE_DIR:-state/simulation}" \
  --market-snapshot deploy/simulation/binance-snapshot.json
