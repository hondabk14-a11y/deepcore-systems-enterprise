"""Run the ledger release checks and emit compact, non-secret evidence."""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
import tempfile
import unittest

from ledger import EventSourcedLedger
from reducer import reduce_ledger, state_hash

EXPECTED_STATE_HASH = "026dc6918fbd9180f8f66c3c620f6d31bfd75fcd6f5e38a85c3d3a302cac1bf4"


def fixture_commitment() -> dict:
    with tempfile.TemporaryDirectory() as tmp:
        ledger = EventSourcedLedger(Path(tmp) / "events.jsonl")
        for kind, amount in (("CREDIT", 100), ("DEBIT", 25), ("CREDIT", 7)):
            ledger.append({"event": kind, "amount": amount})
        return {"state_hash": state_hash(reduce_ledger(ledger)),
                "head_hash": ledger.last_hash(), "event_count": 3}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture-only", action="store_true")
    parser.add_argument("--commit")
    parser.add_argument("--build-id")
    parser.add_argument("--output", type=Path, default=Path("replay-evidence.json"))
    args = parser.parse_args()
    if args.fixture_only:
        print(json.dumps(fixture_commitment(), sort_keys=True))
        return 0
    if not args.commit or not re.fullmatch(r"[0-9a-f]{40}", args.commit):
        parser.error("--commit must be the exact 40-character source commit")
    if not args.build_id:
        parser.error("--build-id is required")
    root = Path(__file__).resolve().parent
    log = io.StringIO()
    suite = unittest.defaultTestLoader.discover(str(root), pattern="test_*.py")
    result = unittest.TextTestRunner(stream=log, verbosity=2).run(suite)
    observations = []
    errors = []
    for seed in ("0", "1", "8675309"):
        try:
            process = subprocess.run(
                [sys.executable, str(Path(__file__).resolve()), "--fixture-only"],
                env={**os.environ, "PYTHONHASHSEED": seed},
                capture_output=True, text=True, check=True, timeout=30,
            )
            observations.append(json.loads(process.stdout))
        except (subprocess.SubprocessError, ValueError) as exc:
            errors.append(type(exc).__name__)
    deterministic = (len(observations) == 3 and
                     all(item == observations[0] for item in observations) and
                     observations[0]["state_hash"] == EXPECTED_STATE_HASH)
    passed = result.wasSuccessful() and result.testsRun > 0 and not result.skipped and deterministic
    sources = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
               for p in sorted(root.glob("*.py"))}
    evidence = {
        "evidence_version": 1, "scope": "reference-ledger-local-replay",
        "commit": args.commit, "build_id": args.build_id,
        "python_version": platform.python_version(),
        "status": "passed" if passed else "failed",
        "tests": {"run": result.testsRun, "failures": len(result.failures),
                  "errors": len(result.errors), "skipped": len(result.skipped)},
        "hash_seeds": ["0", "1", "8675309"],
        "deterministic_fixture": deterministic, "observations": observations,
        "subprocess_errors": errors, "source_sha256": sources,
        "limitations": [
            "No distributed production certification.",
            "Fixture evidence does not attest to a deployed ledger.",
            "Event schema version enforcement and semantic idempotency remain open.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.with_suffix(".log").write_text(log.getvalue(), encoding="utf-8")
    args.output.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(log.getvalue(), end="")
    print(json.dumps({"status": evidence["status"], "tests": evidence["tests"],
                      "state_hash": observations[0]["state_hash"] if observations else None}))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
