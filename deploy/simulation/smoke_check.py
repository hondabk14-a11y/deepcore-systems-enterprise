"""Verify the Compose simulation without printing its generated API token."""
import json
import subprocess
import time
from urllib.error import URLError
from urllib.request import Request, urlopen


def main():
    base = "http://127.0.0.1:8000"
    for attempt in range(30):
        try:
            with urlopen(base + "/health", timeout=2) as response:
                health = json.load(response)
            break
        except (URLError, TimeoutError):
            if attempt == 29:
                raise
            time.sleep(2)
    if health.get("status") != "ok" or health.get("mode") != "simulation":
        raise RuntimeError("unexpected health response")
    token = subprocess.check_output([
        "docker", "compose", "-f", "deploy/simulation/compose.yaml", "exec", "-T", "simulation",
        "python", "-c", "from pathlib import Path; print(Path('/data/api-token').read_text().strip())",
    ], text=True).strip()
    def run():
        request = Request(base + "/api/simulations", data=b'{"steps":3,"seed":"ci"}',
                          headers={"Content-Type": "application/json", "Authorization": "Bearer " + token,
                                   "Idempotency-Key": "ci-smoke"})
        with urlopen(request, timeout=10) as response:
            return json.load(response)
    result, duplicate = run(), run()
    if result != duplicate or result.get("block_height") != 3:
        raise RuntimeError("simulation or idempotency verification failed")
    if not all(result.get(key) is True for key in ["signature_verified", "quorum_verified", "replay_verified"]):
        raise RuntimeError("ledger verification failed")
    subprocess.run(["docker", "compose", "-f", "deploy/simulation/compose.yaml", "restart", "simulation"], check=True,
                   stdout=subprocess.DEVNULL)
    for attempt in range(30):
        try:
            with urlopen(base + "/api/simulations/ci-smoke", timeout=2) as response:
                restored = json.load(response)
            break
        except (URLError, TimeoutError):
            if attempt == 29:
                raise
            time.sleep(2)
    if restored != result:
        raise RuntimeError("restart recovery failed")
    with urlopen(base + "/api/market/binance", timeout=5) as response:
        market = json.load(response)
    if market.get("mode") != "read-only external observations":
        raise RuntimeError("market observation boundary failed")
    print("Simulation HTTP health, authenticated run, idempotency, restart recovery and market endpoint verified.")


if __name__ == "__main__":
    main()
