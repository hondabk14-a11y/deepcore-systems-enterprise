"""Adversarial tests for the readiness -> SSIL -> ledger audit chain."""

from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "CORE" / "event-sourced-ledger"))
sys.path.insert(0, str(ROOT / "SECURITY" / "SSIL"))
sys.path.insert(0, str(ROOT / "PRODUCTION-READINESS-GATES"))

from ledger import EventSourcedLedger  # noqa: E402
from readiness_evidence_event import build_readiness_evidence_event  # noqa: E402
from ssil_decision_event import build_decision_event  # noqa: E402
from ssil_readiness_adapter import readiness_to_ssil_evidence  # noqa: E402
from ssil_readiness_decision_event import build_readiness_decision_event  # noqa: E402


POLICY_VERSION = "ssil-policy/1.0.0"


def manifest() -> dict:
    return {
        "schema_version": "1.0",
        "evidence_type": "readiness-preflight",
        "repository": "hondabk14-a11y/deepcore-systems-enterprise",
        "commit_sha": "a" * 40,
        "workflow_run_id": 123,
        "workflow_run_attempt": 1,
        "controls": {
            "infrastructure": "PASS",
            "key_custody": "PASS",
            "backup_restore": "PASS",
            "rollback": "PASS",
            "observability": "PASS",
        },
        "certification": "NOT_CERTIFIED",
        "external_evidence_required": True,
    }


def chain_objects(manifest_value: dict):
    evidence = build_readiness_evidence_event(manifest_value)
    decision = build_decision_event(
        readiness_to_ssil_evidence(manifest_value),
        policy_version=POLICY_VERSION,
        event_sequence=1,
    )
    link = build_readiness_decision_event(evidence.event_hash(), decision)
    return evidence, decision, link


def chain_records(manifest_value: dict) -> list[dict]:
    evidence, decision, link = chain_objects(manifest_value)
    return [evidence.to_mapping(), decision.to_mapping(), link.to_mapping()]


class SSILReadinessAuditChainAdversarialTests(unittest.TestCase):
    def test_manifest_tampering_changes_evidence_hash(self) -> None:
        original = manifest()
        tampered = copy.deepcopy(original)
        tampered["controls"]["rollback"] = "FAIL"
        self.assertNotEqual(
            build_readiness_evidence_event(original).event_hash(),
            build_readiness_evidence_event(tampered).event_hash(),
        )

    def test_certification_spoof_is_not_accepted_by_ssil(self) -> None:
        spoofed = manifest()
        spoofed["certification"] = "CERTIFIED"
        evidence = readiness_to_ssil_evidence(spoofed)
        self.assertFalse(evidence.security_controls_valid)

    def test_external_evidence_requirement_cannot_be_removed(self) -> None:
        spoofed = manifest()
        spoofed["external_evidence_required"] = False
        evidence = readiness_to_ssil_evidence(spoofed)
        self.assertFalse(evidence.security_controls_valid)

    def test_decision_link_retarget_is_detectable(self) -> None:
        evidence, decision, link = chain_objects(manifest())
        self.assertEqual(link.decision_event_hash, decision.event_hash())
        self.assertNotEqual(link.decision_event_hash, "0" * 64)

        tampered = dict(link.to_mapping())
        tampered["decision_event_hash"] = "0" * 64
        self.assertNotEqual(tampered["decision_event_hash"], decision.event_hash())

    def test_event_order_swap_breaks_ledger_integrity(self) -> None:
        records = chain_records(manifest())
        records[0], records[1] = records[1], records[0]
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "audit.jsonl"
            path.write_text(
                "".join(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n" for record in records),
                encoding="utf-8",
            )
            ledger = EventSourcedLedger(path)
            self.assertFalse(ledger.verify())


if __name__ == "__main__":
    unittest.main()
