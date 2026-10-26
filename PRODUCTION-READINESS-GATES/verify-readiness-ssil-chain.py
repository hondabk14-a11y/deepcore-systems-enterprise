"""Verify the complete readiness evidence -> SSIL -> ledger audit chain.

This is a deterministic audit verification harness. It does not certify
production, authorize deployment, or grant key/ledger authority.
"""

from __future__ import annotations

import json
import importlib.util
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "CORE" / "event-sourced-ledger"))
sys.path.insert(0, str(ROOT / "SECURITY" / "SSIL"))

from ledger import EventSourcedLedger, LedgerIntegrityError  # noqa: E402
spec = importlib.util.spec_from_file_location(
    "readiness_evidence_event", Path(__file__).with_name("readiness-evidence-event.py")
)
readiness_module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = readiness_module
spec.loader.exec_module(readiness_module)
build_readiness_evidence_event = readiness_module.build_readiness_evidence_event
from ssil_decision_event import build_decision_event, validate_decision_event  # noqa: E402
from ssil_readiness_adapter import readiness_to_ssil_evidence  # noqa: E402
from ssil_readiness_decision_event import (  # noqa: E402
    build_readiness_decision_event,
    validate_readiness_decision_event,
)


POLICY_VERSION = "ssil-policy/1.0.0"


def load_manifest(path: Path) -> dict[str, Any]:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict):
        raise ValueError("readiness manifest must be an object")
    return manifest


def verify_chain(manifest: dict[str, Any]) -> str:
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

    evidence_mapping = evidence.to_mapping()
    decision_mapping = decision.to_mapping()
    link_mapping = link.to_mapping()

    with tempfile.TemporaryDirectory() as temp_dir:
        ledger = EventSourcedLedger(Path(temp_dir) / "readiness-ssil-audit.jsonl")
        ledger.append(evidence_mapping)
        ledger.append(decision_mapping)
        ledger.append(link_mapping)
        if not ledger.verify():
            raise LedgerIntegrityError("readiness SSIL audit chain failed verification")
        replayed = ledger.replay()
        if len(replayed) != 3:
            raise LedgerIntegrityError("unexpected audit-chain length")
        if replayed[0]["event_type"] != "READINESS_EVIDENCE":
            raise LedgerIntegrityError("missing readiness evidence event")
        if replayed[1]["event_type"] != "SSIL_DECISION":
            raise LedgerIntegrityError("missing SSIL decision event")
        if replayed[2]["event_type"] != "SSIL_READINESS_DECISION":
            raise LedgerIntegrityError("missing SSIL readiness link event")
        if replayed[1]["evidence_hash"] != decision.evidence_hash:
            raise LedgerIntegrityError("decision evidence hash changed after replay")
        if replayed[2]["evidence_event_hash"] != evidence.event_hash():
            raise LedgerIntegrityError("evidence hash link mismatch after replay")
        if replayed[2]["decision_event_hash"] != decision.event_hash():
            raise LedgerIntegrityError("decision hash link mismatch after replay")
        if replayed[2]["decision"] != decision.decision:
            raise LedgerIntegrityError("decision value mismatch after replay")

    return link.event_hash()


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: verify-readiness-ssil-chain.py <readiness-evidence-manifest.json>")
        return 2
    try:
        manifest = load_manifest(Path(sys.argv[1]))
        digest = verify_chain(manifest)
    except (OSError, ValueError, TypeError, KeyError, LedgerIntegrityError) as exc:
        print(f"READINESS SSIL CHAIN FAIL: {exc}")
        return 1
    print(f"READINESS SSIL CHAIN PASS sha256={digest}")
    print("Audit evidence is verified; production certification remains NOT_CERTIFIED.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
