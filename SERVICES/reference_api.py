"""Read-only service for the existing DeepCore reference runtime.

Ephemeral identities and synthetic balances are deliberately confined to a
startup self-test. This service never admits external transactions.
"""
from contextlib import asynccontextmanager
import json
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse

from CORE.deepcore_consensus import SignedQuorumCertificate
from CORE.deepcore_crypto import Ed25519Identity
from CORE.deepcore_key_registry import ValidatorKeyRegistry
from CORE.deepcore_runtime import DeepCoreLedger, Transaction, ZERO_HASH, canonical, sha256_obj


def verify_reference_runtime():
    validators = [f"validator_{letter}" for letter in "ABCD"]
    identities = {name: Ed25519Identity.generate() for name in validators}
    registry = ValidatorKeyRegistry()
    for name, identity in identities.items():
        registry.register(name, identity.public_key_bytes)
    ledger = DeepCoreLedger(validators)
    tx = Transaction(validators[0], validators[1], 100, 1, 1, validators[0])
    tx = tx.sign_ed25519(identities[validators[0]])
    ledger.append_ed25519(tx, registry)
    commitment = sha256_obj({"purpose": "reference-startup-self-test", "real_funds": False})
    proposal = ledger.prepare_block(validators[:3], commitment)
    consensus = SignedQuorumCertificate(validators)
    votes = [consensus.sign_vote(name, proposal, 0, identities[name]) for name in validators[:3]]
    certificate = consensus.build_certificate(proposal, 0, votes, registry)
    block = ledger.commit(validators[:3], certificate, commitment)
    checks = {
        "transaction_signature": registry.verify(tx.signer, canonical(tx.unsigned()), tx.signature),
        "quorum_certificate": consensus.verify_certificate(proposal, certificate, registry),
        "block_commitment": ledger.verify_block(block, ZERO_HASH),
        "deterministic_replay": ledger.replay() == ledger.state,
    }
    if not all(checks.values()):
        raise RuntimeError("DeepCore startup verification failed")
    revision_file = Path(__file__).resolve().parents[1] / "deployment.json"
    revision = json.loads(revision_file.read_text())["source_commit"] if revision_file.exists() else "local"
    return {
        "service": "DeepCore Systems Enterprise",
        "mode": "reference-simulation",
        "production_certified": False,
        "source_commit": revision,
        "storage": "ephemeral",
        "external_transactions_enabled": False,
        "validator_processes": 1,
        "simulated_validator_identities": len(validators),
        "block_height": block.height,
        "state_root": block.state_root,
        "block_hash": block.block_hash,
        "quorum_certificate_digest": certificate.digest,
        "checks": checks,
    }


def create_app(verifier=verify_reference_runtime):
    @asynccontextmanager
    async def lifespan(app):
        app.state.evidence = verifier()
        yield

    app = FastAPI(title="DeepCore Reference Service", lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)

    @app.get("/healthz")
    def health():
        return {"status": "alive"}

    @app.get("/readyz")
    def ready():
        evidence = getattr(app.state, "evidence", None)
        ok = bool(evidence) and all(evidence["checks"].values())
        return JSONResponse({"ready": ok, "scope": "reference-runtime"}, status_code=200 if ok else 503)

    @app.get("/api/status")
    def status():
        evidence = getattr(app.state, "evidence", None)
        if evidence is None:
            return JSONResponse({"ready": False}, status_code=503)
        return JSONResponse(evidence, headers={"Cache-Control": "no-store"})

    @app.get("/", response_class=HTMLResponse)
    def index():
        return """<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>DeepCore Systems Enterprise</title>
<body style="font:18px system-ui;max-width:760px;margin:8vh auto;padding:24px;background:#101824;color:#e4edf5">
<p>DEEPCORE SYSTEMS ENTERPRISE</p><h1>Reference runtime</h1>
<p>Signed transactions, quorum certificates, block commitments and deterministic replay are checked at startup.</p>
<p>This is a single-process simulation using synthetic balances and ephemeral identities. It is not a production financial service.</p>
<p><a style="color:#6ee7b7" href="/api/status">View verification evidence</a> &nbsp;
<a style="color:#6ee7b7" href="/readyz">Readiness</a></p></body></html>"""

    return app


app = create_app()
