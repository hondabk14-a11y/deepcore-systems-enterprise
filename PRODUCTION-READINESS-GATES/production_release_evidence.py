"""Verify independently attested release evidence; never deploy or certify.

The caller must supply a trusted reviewer public key through a separate trust
channel. An included key or an arbitrary user-generated key is not a trust root.
Artifact checks prove binding and integrity; reviewers establish their substance.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import time

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

DOMAIN = b"deepcore-production-release-evidence-v1\x00"
REPOSITORY = "hondabk14-a11y/deepcore-systems-enterprise"
CONTROLS = frozenset({
    "ci", "security", "infrastructure", "key_custody", "backup_restore",
    "rollback", "observability", "distributed_recovery",
    "enterprise_integrations", "independent_review",
})
FIELDS = frozenset({"schema_version", "repository", "commit_sha", "environment",
                    "deployment_id", "release_scope", "mode", "reviewer_id",
                    "issued_at", "expires_at", "controls"})
MAX_DOCUMENT_BYTES = 1024 * 1024
MAX_ARTIFACT_BYTES = 64 * 1024 * 1024


def canonical_bytes(manifest):
    return json.dumps(manifest, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False).encode("utf-8")


def unique_object(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("Duplicate JSON key")
        value[key] = item
    return value


def load_manifest(path):
    with Path(path).open("rb") as source:
        data = source.read(MAX_DOCUMENT_BYTES + 1)
    if len(data) > MAX_DOCUMENT_BYTES:
        raise ValueError("Manifest exceeds size limit")
    return json.loads(data, object_pairs_hook=unique_object)


def validate(manifest, signature, trusted_public_key, evidence_directory, *,
             commit_sha, environment, deployment_id, now=None):
    if not isinstance(manifest, dict) or set(manifest) != FIELDS:
        raise ValueError("Invalid release manifest fields")
    if not isinstance(trusted_public_key, Ed25519PublicKey):
        raise ValueError("Trusted reviewer key must be Ed25519")
    try:
        trusted_public_key.verify(signature, DOMAIN + canonical_bytes(manifest))
    except InvalidSignature as exc:
        raise ValueError("Reviewer signature invalid") from exc
    if (manifest["schema_version"] != "1.0"
            or manifest["repository"] != REPOSITORY
            or manifest["mode"] != "production"
            or manifest["release_scope"] != "full-enterprise"):
        raise ValueError("Production enterprise scope required")
    if (not isinstance(commit_sha, str) or not re.fullmatch(r"[0-9a-f]{40}", commit_sha)
            or manifest["commit_sha"] != commit_sha):
        raise ValueError("Commit binding mismatch")
    for field, expected in (("environment", environment), ("deployment_id", deployment_id)):
        if not isinstance(expected, str) or not expected or manifest[field] != expected:
            raise ValueError(f"{field} binding mismatch")
    if not isinstance(manifest["reviewer_id"], str) or not manifest["reviewer_id"].strip():
        raise ValueError("Reviewer identity required")
    issued, expires = manifest["issued_at"], manifest["expires_at"]
    now = int(time.time()) if now is None else now
    if (type(issued) is not int or type(expires) is not int
            or not 0 <= issued <= now < expires
            or expires - issued > 7 * 24 * 3600):
        raise ValueError("Evidence expired or invalid validity interval")
    controls = manifest["controls"]
    if not isinstance(controls, dict) or set(controls) != CONTROLS:
        raise ValueError("All enterprise release controls required")
    root = Path(evidence_directory).resolve(strict=True)
    artifacts = set()
    for name, record in controls.items():
        if (not isinstance(record, dict) or set(record) != {"status", "artifact", "sha256"}
                or record["status"] != "PASS"):
            raise ValueError(f"Control {name} lacks reviewed PASS evidence")
        relative = record["artifact"]
        digest = record["sha256"]
        if (not isinstance(relative, str) or not relative or "\\" in relative
                or Path(relative).is_absolute() or ".." in Path(relative).parts
                or not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest)):
            raise ValueError("Invalid artifact path or digest")
        path = root
        for component in Path(relative).parts:
            path = path / component
            if path.is_symlink():
                raise ValueError("Symbolic-link evidence is forbidden")
        path = path.resolve(strict=True)
        if not path.is_relative_to(root) or not path.is_file() or path in artifacts:
            raise ValueError("Evidence must be distinct files inside its directory")
        artifacts.add(path)
        size = 0
        actual = hashlib.sha256()
        with path.open("rb") as source:
            while chunk := source.read(65536):
                size += len(chunk)
                if size > MAX_ARTIFACT_BYTES:
                    raise ValueError("Artifact exceeds size limit")
                actual.update(chunk)
        if size == 0 or actual.hexdigest() != digest:
            raise ValueError(f"Artifact integrity failure for {name}")
    return {"release_evidence": "VERIFIED", "commit_sha": commit_sha,
            "environment": environment, "deployment_id": deployment_id,
            "reviewer_id": manifest["reviewer_id"], "controls_verified": sorted(CONTROLS),
            "production_certified": False,
            "scope": "reviewer attestation and artifact integrity; not live operational verification"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--signature", required=True)
    parser.add_argument("--trusted-reviewer-key", required=True)
    parser.add_argument("--evidence-dir", required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--environment", required=True)
    parser.add_argument("--deployment-id", required=True)
    args = parser.parse_args()
    try:
        key = serialization.load_pem_public_key(Path(args.trusted_reviewer_key).read_bytes())
        result = validate(load_manifest(args.manifest), Path(args.signature).read_bytes(),
                          key, args.evidence_dir, commit_sha=args.commit,
                          environment=args.environment, deployment_id=args.deployment_id)
    except (OSError, ValueError, TypeError) as exc:
        print(json.dumps({"release_evidence": "BLOCKED", "reason": str(exc),
                          "production_certified": False}))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
