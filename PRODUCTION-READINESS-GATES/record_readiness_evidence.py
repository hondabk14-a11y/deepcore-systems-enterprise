"""Append a verified readiness-evidence event to an event-sourced ledger."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "CORE" / "event-sourced-ledger"))

from ledger import EventSourcedLedger, LedgerIntegrityError  # noqa: E402


def canonical_json(value: dict) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def load_verified_manifest(path: Path) -> tuple[dict, str]:
    raw = path.read_bytes()
    manifest = json.loads(raw)
    if not isinstance(manifest, dict):
        raise ValueError("manifest root must be an object")
    if manifest.get("schema_version") != "1.0":
        raise ValueError("unsupported schema_version")
    if manifest.get("evidence_type") != "readiness-preflight":
        raise ValueError("unexpected evidence_type")
    if manifest.get("certification") != "NOT_CERTIFIED":
        raise ValueError("certification boundary violation")
    if manifest.get("external_evidence_required") is not True:
        raise ValueError("external_evidence_required must remain true")
    digest = hashlib.sha256(raw).hexdigest()
    return manifest, digest


def record(manifest_path: Path, ledger_path: Path) -> dict:
    manifest, evidence_hash = load_verified_manifest(manifest_path)
    event = {
        "event_type": "READINESS_EVIDENCE",
        "schema_version": "1.0",
        "repository": manifest["repository"],
        "commit_sha": manifest["commit_sha"],
        "workflow_run_id": manifest["workflow_run_id"],
        "workflow_run_attempt": manifest["workflow_run_attempt"],
        "ref": manifest["ref"],
        "evidence_hash": evidence_hash,
        "controls": manifest["controls"],
        "certification": "NOT_CERTIFIED",
        "external_evidence_required": True,
    }
    ledger = EventSourcedLedger(ledger_path)
    if not ledger.verify():
        raise LedgerIntegrityError("cannot append readiness evidence to an invalid ledger")
    event = ledger.append(event)
    if not ledger.verify():
        raise LedgerIntegrityError("readiness ledger verification failed")
    ledger.replay()
    return event


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("ledger", type=Path)
    args = parser.parse_args()
    event = record(args.manifest, args.ledger)
    print("READINESS EVIDENCE RECORDED")
    print(canonical_json(event))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
