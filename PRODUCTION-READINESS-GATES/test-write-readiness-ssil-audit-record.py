"""Tests for deterministic SSIL readiness audit-record generation."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "PRODUCTION-READINESS-GATES"))

from write_readiness_ssil_audit_record import build_record  # noqa: E402


class ReadinessSSILAuditRecordTests(unittest.TestCase):
    def manifest(self):
        return {
            "schema_version": "1.0",
            "evidence_type": "readiness-preflight",
            "repository": "hondabk14-a11y/deepcore-systems-enterprise",
            "commit_sha": "0123456789abcdef0123456789abcdef01234567",
            "ref": "main",
            "event": "push",
            "workflow_run_id": 12345,
            "workflow_run_attempt": 1,
            "controls": {
                "infrastructure": "preflight-executed",
                "key_custody": "boundary-preflight-executed",
                "backup_restore": "synthetic-test-executed",
                "rollback": "synthetic-test-executed",
                "observability": "contract-preflight-executed",
            },
            "certification": "NOT_CERTIFIED",
            "external_evidence_required": True,
        }

    def test_record_is_deterministic(self):
        first = build_record(self.manifest())
        second = build_record(self.manifest())
        self.assertEqual(first, second)
        self.assertTrue(first["audit_chain_verified"])
        self.assertEqual(first["production_certification"], "NOT_CERTIFIED")

    def test_manifest_change_changes_evidence(self):
        first = build_record(self.manifest())
        changed = self.manifest()
        changed["workflow_run_id"] = 12346
        second = build_record(changed)
        self.assertNotEqual(first["manifest_hash"], second["manifest_hash"])
        self.assertNotEqual(first["evidence_event_hash"], second["evidence_event_hash"])

    def test_certification_spoof_rejected(self):
        manifest = self.manifest()
        manifest["certification"] = "CERTIFIED"
        with self.assertRaises(ValueError):
            build_record(manifest)

    def test_external_evidence_requirement_cannot_be_removed(self):
        manifest = self.manifest()
        manifest["external_evidence_required"] = False
        with self.assertRaises(ValueError):
            build_record(manifest)


if __name__ == "__main__":
    unittest.main()
