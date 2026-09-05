"""Write a deterministic, machine-readable SSIL readiness audit record.

This produces evidence of repository-side verification only. It does not
certify production, authorize deployment, or grant key/ledger authority.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "CORE" / "event-sourced-ledger"))
sys.path.insert(0, str(ROOT / "SECURITY" / "SSIL"))

from ledger import EventSourcedLedger, LedgerIntegrityError  # noqa: E402
from readiness_evidence_event import build_readiness_evidence_event  # noqa: E402
from ssil_decision_event import build_decision_event, validate_decision_event  # noqa: E402
from ssil_readiness_adapter import readiness_to_ssil_evidence  # noqa: E402
from ssil_readiness_decision_event import (  # noqa: E402
    build_readiness_decision_event,
    validate_readiness_decision_event,
)

POLICY_VERSION = "ssil-policy/1.0.0"
SCHEMA_VERSION = "1.0"


def canonical_json(value: dict[str, Any]) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def load_manifest(path: Path) -> dict[str, Any]:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict):
        raise ValueError("readiness manifest must be an object")
    return manifest


def build_record(manifest: dict[str, Any]) -> dict[str, Any]:
    evidence = build_readiness_evidence_event(manifest)
    ssil_evidence = readiness_to_ssil_evidence(manifest)
    decision = build_decision_event(
        ssil_evidence,
        policy_version=POLICY_VERSION,
        event_sequence=1,
    )
    validate_decision_event(decision)
    link = build_readiness_decision_event(evidence.event_hash(), decision)
    validate_readiness_decision_event(link)

    ledger = EventSourcedLedger(Path("/tmp/deepcore-readiness-ssil-audit.jsonl"))
    ledger_path = ledger.path
    try:
        if ledger_path.exists():
            ledger_path.unlink()
        ledger.append(evidence.to_mapping())
        ledger.append(decision.to_mapping())
        ledger.append(link.to_mapping())
        if not ledger.verify():
            raise LedgerIntegrityError("audit ledger verification failed")
        replayed = ledger.replay()
        if len(replayed) != 3:
            raise LedgerIntegrityError("unexpected audit ledger length")
    finally:
        if ledger_path.exists():
            ledger_path.unlink()

    manifest_hash = hashlib.sha256(canonical_json(manifest).encode("utf-8")).hexdigest()
    record = {
        "schema_version": SCHEMA_VERSION,
        "evidence_type": "readiness-ssil-audit",
        "manifest_hash": manifest_hash,
        "evidence_event_hash": evidence.event_hash(),
        "decision_event_hash": decision.event_hash(),
        "readiness_decision_event_hash": link.event_hash(),
        "decision": decision.decision,
        "reason_codes": list(decision.reason_codes),
        "policy_version": decision.policy_version,
        "evaluator_version": decision.evaluator_version,
        "certification": manifest.get("certification"),
        "external_evidence_required": manifest.get("external_evidence_required"),
        "audit_chain_verified": True,
        "production_certification": "NOT_CERTIFIED",
    }
    if record["certification"] != "NOT_CERTIFIED" or record["external_evidence_required"] is not True:
        raise ValueError("production certification boundary violated")
    return record


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: write-readiness-ssil-audit-record.py <manifest> <output>")
        return 2
    try:
        record = build_record(load_manifest(Path(sys.argv[1])))
        Path(sys.argv[2]).write_text(canonical_json(record) + "\n", encoding="utf-8")
    except (OSError, ValueError, TypeError, KeyError, LedgerIntegrityError) as exc:
        print(f"READINESS SSIL AUDIT FAIL: {exc}")
        return 1
    digest = hashlib.sha256(canonical_json(record).encode("utf-8")).hexdigest()
    print(f"READINESS SSIL AUDIT PASS sha256={digest}")
    print("Audit evidence is repository-side verification; production certification remains NOT_CERTIFIED.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
