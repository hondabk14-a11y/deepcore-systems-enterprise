"""Regression tests for deterministic readiness evidence binding."""

from __future__ import annotations

import importlib.util
import unittest


SPEC = importlib.util.spec_from_file_location(
    "readiness_evidence_event",
    "readiness-evidence-event.py",
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


BASE_MANIFEST = {
    "schema_version": "1.0",
    "evidence_type": "readiness-preflight",
    "repository": "hondabk14-a11y/deepcore-systems-enterprise",
    "commit_sha": "a" * 40,
    "ref": "main",
    "event": "push",
    "workflow_run_id": 123456,
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


class ReadinessEvidenceEventTests(unittest.TestCase):
    def test_deterministic_binding(self) -> None:
        first = MODULE.build_readiness_evidence_event(dict(BASE_MANIFEST))
        second = MODULE.build_readiness_evidence_event(dict(BASE_MANIFEST))
        self.assertEqual(first.manifest_hash, second.manifest_hash)
        self.assertEqual(first.event_hash(), second.event_hash())
        self.assertEqual(first.to_mapping(), second.to_mapping())

    def test_commit_change_changes_manifest_hash(self) -> None:
        changed = dict(BASE_MANIFEST)
        changed["commit_sha"] = "b" * 40
        first = MODULE.build_readiness_evidence_event(dict(BASE_MANIFEST))
        second = MODULE.build_readiness_evidence_event(changed)
        self.assertNotEqual(first.manifest_hash, second.manifest_hash)
        self.assertNotEqual(first.event_hash(), second.event_hash())

    def test_workflow_run_change_changes_binding(self) -> None:
        changed = dict(BASE_MANIFEST)
        changed["workflow_run_id"] = 123457
        first = MODULE.build_readiness_evidence_event(dict(BASE_MANIFEST))
        second = MODULE.build_readiness_evidence_event(changed)
        self.assertNotEqual(first.manifest_hash, second.manifest_hash)

    def test_certification_boundary_rejects_certified_manifest(self) -> None:
        invalid = dict(BASE_MANIFEST)
        invalid["certification"] = "CERTIFIED"
        with self.assertRaises(ValueError):
            MODULE.build_readiness_evidence_event(invalid)

    def test_external_evidence_requirement_cannot_be_removed(self) -> None:
        invalid = dict(BASE_MANIFEST)
        invalid["external_evidence_required"] = False
        with self.assertRaises(ValueError):
            MODULE.build_readiness_evidence_event(invalid)

    def test_missing_field_rejected(self) -> None:
        invalid = dict(BASE_MANIFEST)
        del invalid["commit_sha"]
        with self.assertRaises(ValueError):
            MODULE.build_readiness_evidence_event(invalid)


if __name__ == "__main__":
    unittest.main()
