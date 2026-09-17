import pytest
from fastapi.testclient import TestClient
from SERVICES.reference_api import create_app, verify_reference_runtime
from CORE.deepcore_consensus import SignedQuorumCertificate


def test_serves_verified_reference_evidence_without_write_routes():
    with TestClient(create_app()) as client:
        assert client.get("/healthz").status_code == 200
        assert client.get("/readyz").json()["ready"] is True
        evidence = client.get("/api/status").json()
        assert all(evidence["checks"].values())
        assert evidence["production_certified"] is False
        assert evidence["mode"] == "reference-simulation"
        assert evidence["validator_processes"] == 1
        assert evidence["external_transactions_enabled"] is False
        assert "private_key" not in str(evidence)
        assert client.post("/api/status", json={"amount": 1}).status_code == 405
        assert client.post("/transactions", json={"amount": 1}).status_code == 404


def test_signature_verification_failure_prevents_startup(monkeypatch):
    monkeypatch.setattr(SignedQuorumCertificate, "verify_certificate", lambda *args: False)
    with pytest.raises(RuntimeError, match="startup verification failed"):
        with TestClient(create_app()):
            pass


def test_readiness_is_not_available_before_verification():
    client = TestClient(create_app())
    assert client.get("/readyz").status_code == 503
    assert client.get("/api/status").status_code == 503


def test_ephemeral_runs_do_not_claim_persistent_identity():
    first, second = verify_reference_runtime(), verify_reference_runtime()
    assert first["state_root"] == second["state_root"]
    assert first["block_hash"] != second["block_hash"]
    assert first["storage"] == "ephemeral"
