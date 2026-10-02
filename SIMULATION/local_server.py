"""Local, authenticated simulation API. All validator keys are public test fixtures."""
from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import re
import secrets
import sqlite3
import time
import uuid
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from CORE.binance_observer import ObservationJournal, fetch_quote, normalize
from CORE.deepcore_consensus import SignedQuorumCertificate
from CORE.deepcore_crypto import Ed25519Identity
from CORE.deepcore_key_registry import ValidatorKeyRegistry
from CORE.deepcore_runtime import DeepCoreLedger, Transaction, sha256_obj


def simulate(parameters: dict) -> dict:
    if not isinstance(parameters, dict) or set(parameters) - {"steps", "seed"}:
        raise ValueError("expected steps and optional seed")
    steps, seed = parameters.get("steps", 5), parameters.get("seed", "deepcore-local")
    if type(steps) is not int or not 1 <= steps <= 100:
        raise ValueError("steps must be an integer from 1 to 100")
    if not isinstance(seed, str) or not 1 <= len(seed) <= 128:
        raise ValueError("seed must contain 1 to 128 characters")
    validators = [f"validator_{letter}" for letter in "ABCD"]
    # Deterministic, deliberately public TEST keys. Never use for real signing.
    identities = {v: Ed25519Identity.from_private_bytes(hashlib.sha256(
        ("PUBLIC_SIMULATION_FIXTURE:" + seed + ":" + v).encode()).digest()) for v in validators}
    registry = ValidatorKeyRegistry()
    for v in validators:
        registry.register(v, identities[v].public_key_bytes)
    ledger, consensus = DeepCoreLedger(validators), SignedQuorumCertificate(validators)
    for step in range(steps):
        sender, receiver = validators[step % 4], validators[(step + 1) % 4]
        tx = Transaction(sender, receiver, 1000, 1, ledger.state[sender]["nonce"] + 1, sender).sign_ed25519(identities[sender])
        if not tx.verify_ed25519(identities[sender].public_key_bytes):
            raise ValueError("simulation signature verification failed")
        ledger.append_ed25519(tx, registry)
        authorization = sha256_obj({"scope": "simulation-only", "seed": seed, "step": step})
        proposal = ledger.prepare_block(validators[:3], authorization)
        votes = [consensus.sign_vote(v, proposal, step, identities[v]) for v in validators[:3]]
        certificate = consensus.build_certificate(proposal, step, votes, registry)
        if not consensus.verify_certificate(proposal, certificate, registry):
            raise ValueError("simulation certificate verification failed")
        ledger.commit(validators[:3], certificate, authorization)
    if ledger.replay() != ledger.state:
        raise ValueError("simulation replay mismatch")
    return {"mode": "simulation", "steps": steps, "seed": seed, "validators": 4,
            "quorum": 3, "block_height": len(ledger.blocks), "state": ledger.state,
            "state_root": ledger.state_root(), "block_hash": ledger.blocks[-1].block_hash,
            "signature_verified": True, "quorum_verified": True, "replay_verified": True,
            "key_scope": "public deterministic test fixtures", "production_certified": False}


class SimulationStore:
    def __init__(self, directory: Path):
        directory.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(directory / "simulations.sqlite3")
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA synchronous=FULL")
        self.db.execute("CREATE TABLE IF NOT EXISTS runs (id TEXT PRIMARY KEY, input_hash TEXT NOT NULL, result TEXT NOT NULL, result_hash TEXT NOT NULL)")
        self.db.commit()
        self.market = ObservationJournal(str(directory / "market.sqlite3"))
        self.market.replay()  # Fail startup on a corrupted existing journal.

    def close(self):
        self.market.close()
        self.db.close()

    def run(self, parameters: dict, request_id: str | None = None) -> tuple[dict, bool]:
        if request_id is not None and not re.fullmatch(r"[A-Za-z0-9_.-]{1,128}", request_id):
            raise ValueError("invalid Idempotency-Key")
        if not isinstance(parameters, dict):
            raise ValueError("request must be an object")
        normalized = {"steps": parameters.get("steps", 5), "seed": parameters.get("seed", "deepcore-local")}
        if set(parameters) - set(normalized):
            raise ValueError("unexpected simulation parameter")
        input_hash = sha256_obj(normalized)
        request_id = request_id or str(uuid.uuid4())
        existing = self.get(request_id)
        if existing is not None:
            row = self.db.execute("SELECT input_hash FROM runs WHERE id=?", (request_id,)).fetchone()
            if row[0] != input_hash:
                raise ValueError("Idempotency-Key already used with different parameters")
            return existing, False
        result = {"id": request_id, "created_at_ms": time.time_ns() // 1_000_000, **simulate(parameters)}
        with self.db:
            self.db.execute("INSERT INTO runs VALUES (?,?,?,?)", (request_id, input_hash, json.dumps(result, sort_keys=True), sha256_obj(result)))
        return result, True

    def get(self, request_id: str) -> dict | None:
        row = self.db.execute("SELECT result,result_hash FROM runs WHERE id=?", (request_id,)).fetchone()
        if row is None:
            return None
        value = json.loads(row[0])
        if sha256_obj(value) != row[1]:
            raise ValueError("stored simulation result integrity mismatch")
        return value

    def recent(self):
        ids = self.db.execute("SELECT id FROM runs ORDER BY rowid DESC LIMIT 20").fetchall()
        return [self.get(row[0]) for row in ids]

    def market_status(self):
        events = self.market.replay()["state"]
        now = time.time_ns() // 1_000_000
        return {"source": "binance", "mode": "read-only external observations",
                "observations": [{**event, "age_ms": max(0, now - event["observed_at_ms"]),
                                  "stale": now - event["observed_at_ms"] > 60_000}
                                 for event in events.values()]}


PAGE = b'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>DeepCore Simulation</title>
<style>body{font:16px system-ui;max-width:850px;margin:40px auto;padding:20px;background:#101923;color:#ecf2f8}button,input{font:inherit;padding:10px;margin:6px}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#1a2735;padding:20px}label{display:block}</style>
<h1>DeepCore Simulation</h1><p>Workspace: BKillings. Local simulation with four test validators and verified ledger replay.</p>
<label>Local API token <input id="token" type="password" autocomplete="off"></label><label>Steps <input id="steps" type="number" min="1" max="100" value="5"></label>
<button id="run">Run simulation</button><button id="market">Show Binance observations</button><pre id="result">Ready</pre>
<script>const out=document.getElementById('result');async function request(url,options={}){out.textContent='Working...';try{const response=await fetch(url,options);const body=await response.json();out.textContent=JSON.stringify(body,null,2)}catch(e){out.textContent=e.message}}
document.getElementById('run').onclick=()=>request('/api/simulations',{method:'POST',headers:{'Content-Type':'application/json','Authorization':'Bearer '+document.getElementById('token').value},body:JSON.stringify({steps:Number(document.getElementById('steps').value)})});
document.getElementById('market').onclick=()=>request('/api/market/binance');</script></html>'''


class Handler(BaseHTTPRequestHandler):
    def respond(self, status, value, content_type="application/json"):
        body = value if isinstance(value, bytes) else json.dumps(value).encode()
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.end_headers()
        self.wfile.write(body)

    def allowed_host(self):
        host = self.headers.get("Host", "")
        return host in {f"127.0.0.1:{self.server.server_port}", f"localhost:{self.server.server_port}"}

    def do_GET(self):
        if not self.allowed_host():
            return self.respond(403, {"error": "local Host header required"})
        route = urlsplit(self.path).path
        try:
            if route == "/":
                return self.respond(200, PAGE, "text/html; charset=utf-8")
            if route == "/health":
                return self.respond(200, {"status": "ok", "mode": "simulation", "workspace": "BKillings"})
            if route == "/api/simulations":
                return self.respond(200, {"runs": self.server.store.recent()})
            if route.startswith("/api/simulations/"):
                result = self.server.store.get(route.rsplit("/", 1)[-1])
                return self.respond(200 if result else 404, result or {"error": "run not found"})
            if route == "/api/market/binance":
                return self.respond(200, self.server.store.market_status())
            return self.respond(404, {"error": "route not found"})
        except (ValueError, sqlite3.Error):
            self.respond(503, {"error": "stored state could not be verified"})

    def do_POST(self):
        if not self.allowed_host():
            return self.respond(403, {"error": "local Host header required"})
        origin = self.headers.get("Origin")
        if origin and origin != "http://" + self.headers["Host"]:
            return self.respond(403, {"error": "cross-origin requests are not allowed"})
        if not hmac.compare_digest(self.headers.get("Authorization", "").encode(), ("Bearer " + self.server.token).encode()):
            return self.respond(401, {"error": "local API token required"})
        if self.headers.get("Content-Type", "").split(";", 1)[0].strip() != "application/json":
            return self.respond(415, {"error": "application/json required"})
        try:
            length = int(self.headers.get("Content-Length", "-1"))
            if not 0 <= length <= 8192:
                return self.respond(413, {"error": "request body must be at most 8192 bytes"})
            parameters = json.loads(self.rfile.read(length))
            route = urlsplit(self.path).path
            if route == "/api/simulations":
                result, created = self.server.store.run(parameters, self.headers.get("Idempotency-Key"))
                return self.respond(201 if created else 200, result)
            if route == "/api/market/binance/refresh":
                if parameters != {}:
                    raise ValueError("refresh expects an empty JSON object")
                self.server.store.market.append(fetch_quote("BTCUSDT"))
                return self.respond(200, self.server.store.market_status())
            return self.respond(404, {"error": "route not found"})
        except (ValueError, UnicodeDecodeError) as exc:
            self.respond(400, {"error": str(exc)})
        except Exception:
            self.respond(503, {"error": "operation failed; cached market data may still be available"})

    def log_message(self, format, *args):
        # Do not record request paths, tokens, payloads or query parameters.
        print("simulation HTTP request completed", flush=True)


class Server(HTTPServer):
    def get_request(self):
        connection, address = super().get_request()
        connection.settimeout(10)
        return connection, address


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", choices=["127.0.0.1", "0.0.0.0"], default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--state-dir", type=Path, default=Path("state/simulation"))
    parser.add_argument("--market-snapshot", type=Path)
    args = parser.parse_args()
    store = SimulationStore(args.state_dir)
    token_path = args.state_dir / "api-token"
    if not token_path.exists():
        descriptor = os.open(token_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "w") as handle:
            handle.write(secrets.token_urlsafe(32))
    token = token_path.read_text().strip()
    if len(token) < 32:
        raise ValueError("invalid local API token")
    if args.market_snapshot:
        snapshot = json.loads(args.market_snapshot.read_text())
        store.market.append(normalize(snapshot["quote"], "BTCUSDT", snapshot["observed_at_ms"]))
    server = Server((args.host, args.port), Handler)
    server.store, server.token = store, token
    print(f"DeepCore simulation server listening on {args.host}:{args.port}; token file: {token_path}", flush=True)
    try:
        server.serve_forever()
    finally:
        server.server_close()
        store.close()


if __name__ == "__main__":
    main()
