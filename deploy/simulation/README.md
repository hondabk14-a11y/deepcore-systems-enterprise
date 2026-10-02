# DeepCore local simulation server

The persistent HTTP process runs isolated deterministic simulations of the existing DeepCore ledger. Each run uses four validators, a quorum of three, Ed25519 test signatures and verified replay. Results and idempotency keys are saved in SQLite. Runs survive process restarts. This is a single-process simulation service; the validators are simulated, and the deliberately public test keys must never be used for real assets or signing.

## Local launch

From the repository root, with the runtime cryptography dependency installed:

```bash
python -m SIMULATION.local_server --state-dir state/simulation
```

Open http://127.0.0.1:8000/. Use the locally generated token in `state/simulation/api-token` in the dashboard's API token field. The token file has mode 0600; keep it private and outside Git. The server binds to loopback by default. Simulation POST requests require the token; cross-origin requests and unexpected Host headers are rejected.

Endpoints:

- `GET /health`: local service health.
- `POST /api/simulations`: JSON `{"steps":5,"seed":"example"}`. Steps are bounded to 1–100. Requires `Authorization: Bearer <local token>`. Optional `Idempotency-Key` prevents duplicate runs; changing parameters under the same key is rejected.
- `GET /api/simulations`: latest 20 saved runs.
- `GET /api/simulations/<id>`: one saved run.
- `GET /api/market/binance`: saved, untrusted Binance BTCUSDT observations, with age and staleness indicators.
- `POST /api/market/binance/refresh`: authenticated empty JSON request to fetch public BTCUSDT bid/ask data from Binance's market-data endpoint. Requires outbound HTTPS. Failed refreshes retain cached observations.

## Binance plugin and BKillings

The connected Binance plugin can supply the initial bid/ask snapshot. Supply a JSON file containing `quote` and `observed_at_ms` using `--market-snapshot <path>`. The snapshot is normalized and appended to the existing Binance observation journal. Subsequent refreshes use the public spot market-data endpoint. This server cannot call chat plugins autonomously.

BKillings is the workspace label and the separately confirmed Hugging Face account. It is not a Binance account authentication or validator identity. Market observations never enter the simulated ledger, and no trade/order execution is implemented.

## Container simulation deployment

```bash
docker compose -f deploy/simulation/compose.yaml up -d --build
docker compose -f deploy/simulation/compose.yaml ps
docker compose -f deploy/simulation/compose.yaml logs --tail=30
```

The container uses an unprivileged user, a persistent named volume, a health check, a read-only root filesystem, and a host port restricted to 127.0.0.1. The Docker build context excludes all unrelated files and state. The image pins cryptography to 46.0.1. The base Python image is not digest-pinned. Container build and runtime must be verified in the target environment before claiming deployment.

## Verification

```bash
python -m unittest SIMULATION.test_local_server -v
```

The suite covers deterministic replay, restart persistence, idempotency conflicts, result tampering, Binance observation persistence, authentication, Host/Origin rejection and request limits. Result hashes detect accidental modification; they do not authenticate the database against an attacker who can rewrite it. This package does not deploy the documented Enterprise payment, custody, distributed transport or production infrastructure layers.
