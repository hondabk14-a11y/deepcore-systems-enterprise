"""Adversarial checks using temporary test evidence and ephemeral keys only."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from production_release_evidence import CONTROLS, DOMAIN, canonical_bytes, load_manifest, validate


class ReleaseEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.key = Ed25519PrivateKey.generate()
        self.manifest = {"schema_version": "1.0",
                         "repository": "hondabk14-a11y/deepcore-systems-enterprise",
                         "commit_sha": "a" * 40, "environment": "test-fixture-only",
                         "deployment_id": "fixture", "release_scope": "full-enterprise",
                         "mode": "production", "reviewer_id": "test-reviewer",
                         "issued_at": 100, "expires_at": 200, "controls": {}}
        for name in CONTROLS:
            data = f"Temporary TEST fixture for {name}".encode()
            path = name + ".txt"
            (self.root / path).write_bytes(data)
            self.manifest["controls"][name] = {
                "status": "PASS", "artifact": path, "sha256": hashlib.sha256(data).hexdigest()}

    def check(self, manifest=None, **changes):
        manifest = self.manifest if manifest is None else manifest
        values = dict(commit_sha="a" * 40, environment="test-fixture-only", deployment_id="fixture", now=150)
        values.update(changes)
        return validate(manifest, self.key.sign(DOMAIN + canonical_bytes(manifest)),
                        self.key.public_key(), self.root, **values)

    def test_valid_attestation_never_claims_certification(self):
        result = self.check()
        self.assertEqual(result["release_evidence"], "VERIFIED")
        self.assertFalse(result["production_certified"])

    def test_missing_control_and_failed_control_rejected(self):
        for mode in ("missing", "failed"):
            manifest = deepcopy(self.manifest)
            if mode == "missing":
                del manifest["controls"]["key_custody"]
            else:
                manifest["controls"]["ci"]["status"] = "PENDING"
            with self.assertRaises(ValueError):
                self.check(manifest)

    def test_scope_and_deployment_bindings_rejected(self):
        for changes in ({"commit_sha": "b" * 40}, {"environment": "other"}, {"deployment_id": "other"}):
            with self.assertRaises(ValueError):
                self.check(**changes)
        manifest = deepcopy(self.manifest)
        manifest["mode"] = "simulation"
        with self.assertRaises(ValueError):
            self.check(manifest)

    def test_expired_future_and_boolean_timestamps_rejected(self):
        for issued, expires in ((100, 149), (151, 200), (True, 200), (100, 1000000)):
            manifest = deepcopy(self.manifest)
            manifest.update(issued_at=issued, expires_at=expires)
            with self.assertRaises(ValueError):
                self.check(manifest)

    def test_artifact_tampering_rejected(self):
        (self.root / "ci.txt").write_bytes(b"changed")
        with self.assertRaises(ValueError):
            self.check()

    def test_wrong_trust_key_and_altered_signature_rejected(self):
        signature = self.key.sign(DOMAIN + canonical_bytes(self.manifest))
        for key, sig in ((Ed25519PrivateKey.generate().public_key(), signature),
                         (self.key.public_key(), b"\0" * 64)):
            with self.assertRaises(ValueError):
                validate(self.manifest, sig, key, self.root,
                         commit_sha="a" * 40, environment="test-fixture-only", deployment_id="fixture", now=150)

    def test_paths_and_symlinks_rejected(self):
        for path in ("../outside", "/outside", "nested\\outside"):
            manifest = deepcopy(self.manifest)
            manifest["controls"]["ci"]["artifact"] = path
            with self.assertRaises(ValueError):
                self.check(manifest)
        (self.root / "ci.txt").unlink()
        (self.root / "ci.txt").symlink_to(self.root / "security.txt")
        with self.assertRaises(ValueError):
            self.check()

    def test_duplicate_json_keys_rejected(self):
        path = self.root / "manifest.json"
        path.write_text('{"schema_version":"1.0","schema_version":"2.0"}')
        with self.assertRaises(ValueError):
            load_manifest(path)
