"""Verify a DeepCore readiness evidence manifest and its captured summary."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

REQUIRED_FIELDS = {
    "schema_version",
    "evidence_type",
    "repository",
    "commit_sha",
    "ref",
    "event",
    "workflow_run_id",
    "workflow_run_attempt",
    "controls",
    "certification",
    "external_evidence_required",
}

REQUIRED_CONTROLS = {
    "infrastructure",
    "key_custody",
    "backup_restore",
    "rollback",
    "observability",
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def verify_manifest(path: Path) -> tuple[bool, list[str]]:
    errors: list[str] = []
    try:
        raw = path.read_bytes()
        manifest = json.loads(raw)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return False, [f"manifest unreadable or invalid JSON: {exc}"]

    if not isinstance(manifest, dict):
        return False, ["manifest root must be an object"]

    missing = REQUIRED_FIELDS - manifest.keys()
    if missing:
        errors.append(f"missing fields: {sorted(missing)}")

    if manifest.get("schema_version") != "1.0":
        errors.append("unsupported schema_version")
    if manifest.get("evidence_type") != "readiness-preflight":
        errors.append("unexpected evidence_type")
    if not isinstance(manifest.get("commit_sha"), str) or len(manifest["commit_sha"]) != 40:
        errors.append("commit_sha must be a 40-character SHA-1 commit identifier")
    if not isinstance(manifest.get("workflow_run_id"), int) or manifest["workflow_run_id"] <= 0:
        errors.append("workflow_run_id must be a positive integer")
    if not isinstance(manifest.get("workflow_run_attempt"), int) or manifest["workflow_run_attempt"] <= 0:
        errors.append("workflow_run_attempt must be a positive integer")
    if manifest.get("certification") != "NOT_CERTIFIED":
        errors.append("certification boundary must remain NOT_CERTIFIED")
    if manifest.get("external_evidence_required") is not True:
        errors.append("external_evidence_required must remain true")

    controls = manifest.get("controls")
    if not isinstance(controls, dict):
        errors.append("controls must be an object")
    else:
        missing_controls = REQUIRED_CONTROLS - controls.keys()
        if missing_controls:
            errors.append(f"missing controls: {sorted(missing_controls)}")
        for name in REQUIRED_CONTROLS & controls.keys():
            if not isinstance(controls[name], str) or not controls[name]:
                errors.append(f"control {name!r} must contain a non-empty status")

    return not errors, errors


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("readiness-evidence-manifest.json")
    ok, errors = verify_manifest(path)
    if ok:
        digest = sha256_bytes(path.read_bytes())
        print(f"EVIDENCE MANIFEST PASS sha256={digest}")
        return 0

    print("EVIDENCE MANIFEST FAIL")
    for error in errors:
        print(f"- {error}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
