#!/usr/bin/env python3
"""DeepCore release rollback preflight.

Models a release pointer moving from a known-good version to a candidate and
then rolling back to the known-good version. The check is intentionally local
and synthetic. It does not deploy, mutate infrastructure, or claim that a
production rollback has been executed.
"""

from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path


def release_digest(version: str, payload: dict) -> str:
    body = json.dumps(
        {"version": version, "payload": payload},
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(body).hexdigest()


def main() -> int:
    known_good = {"version": "release-good", "payload": {"schema": 1, "mode": "stable"}}
    candidate = {"version": "release-candidate", "payload": {"schema": 1, "mode": "candidate"}}

    good_digest = release_digest(known_good["version"], known_good["payload"])
    candidate_digest = release_digest(candidate["version"], candidate["payload"])
    if good_digest == candidate_digest:
        print("ROLLBACK_PREFLIGHT=FAIL")
        print("FAILURE=synthetic release identities are not distinct")
        return 1

    with tempfile.TemporaryDirectory(prefix="deepcore-rollback-") as tmp:
        pointer = Path(tmp) / "active-release.json"

        pointer.write_text(json.dumps({"active": known_good["version"], "digest": good_digest}), encoding="utf-8")
        original = json.loads(pointer.read_text(encoding="utf-8"))

        pointer.write_text(json.dumps({"active": candidate["version"], "digest": candidate_digest}), encoding="utf-8")
        deployed = json.loads(pointer.read_text(encoding="utf-8"))
        if deployed["active"] != candidate["version"] or deployed["digest"] != candidate_digest:
            print("ROLLBACK_PREFLIGHT=FAIL")
            print("FAILURE=candidate activation was not deterministic")
            return 1

        pointer.write_text(json.dumps(original), encoding="utf-8")
        restored = json.loads(pointer.read_text(encoding="utf-8"))
        if restored != original:
            print("ROLLBACK_PREFLIGHT=FAIL")
            print("FAILURE=rollback did not restore the known-good release pointer")
            return 1

    print("ROLLBACK_PREFLIGHT=PASS")
    print("SCOPE=synthetic release-pointer rollback test")
    print("RESULT=known-good release was activated, candidate state modeled, and known-good state restored exactly")
    print("PRODUCTION_DEPLOYMENT=not performed")
    print("NOTE=production rollback requires environment-specific deployment evidence, health gates, database/schema compatibility checks, traffic controls, operator authorization, and a tested rollback runbook")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
