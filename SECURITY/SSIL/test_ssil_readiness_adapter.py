"""Regression tests for the readiness-to-SSIL adapter."""

from __future__ import annotations

import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from ssil_engine import Decision, Reason  # noqa: E402
from ssil_readiness_adapter import evaluate_readiness_manifest  # noqa: E402


BASE_MANIFEST = {
    "schema_version": "1.0",
    "evidence_type": "readiness-preflight",
    "repository": "hondabk14-a11y/deepcore-systems-enterprise",
    "commit_sha": "a" * 40,
    "ref": "main",
    "event": "push",
    "workflow_run_id": 123,
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


class SSILReadinessAdapterTests(unittest.TestCase):
    def test_complete_uncertified_manifest_allows_advisory_evaluation(self) -> None:
        result = evaluate_readiness_manifest(BASE_MANIFEST)
        self.assertEqual(result.decision, Decision.ALLOW)
        self.assertEqual(result.reasons, (Reason.POLICY_SATISFIED,))

    def test_missing_control_defers(self) -> None:
        manifest = dict(BASE_MANIFEST)
        manifest["controls"] = dict(BASE_MANIFEST["controls"])
        del manifest["controls"]["rollback"]
        result = evaluate_readiness_manifest(manifest)
        self.assertEqual(result.decision, Decision.DEFER)
        self.assertEqual(result.reasons, (Reason.EVIDENCE_INCOMPLETE,))

    def test_certification_boundary_violation_fails_closed(self) -> None:
        manifest = dict(BASE_MANIFEST)
        manifest["certification"] = "CERTIFIED"
        result = evaluate_readiness_manifest(manifest)
        self.assertEqual(result.decision, Decision.FAIL_CLOSED)
        self.assertIn(Reason.SECURITY_CONTROL_FAILURE, result.reasons)

    def test_external_evidence_requirement_cannot_be_removed(self) -> None:
        manifest = dict(BASE_MANIFEST)
        manifest["external_evidence_required"] = False
        result = evaluate_readiness_manifest(manifest)
        self.assertEqual(result.decision, Decision.FAIL_CLOSED)
        self.assertIn(Reason.SECURITY_CONTROL_FAILURE, result.reasons)

    def test_malformed_controls_fail_closed(self) -> None:
        manifest = dict(BASE_MANIFEST)
        manifest["controls"] = "preflight-executed"
        result = evaluate_readiness_manifest(manifest)
        self.assertEqual(result.decision, Decision.FAIL_CLOSED)
        self.assertIn(Reason.SECURITY_CONTROL_FAILURE, result.reasons)


if __name__ == "__main__":
    unittest.main()
