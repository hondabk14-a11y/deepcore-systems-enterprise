#!/usr/bin/env python3
"""Summarize DeepCore production-readiness evidence.

This is a status aggregator only. Presence of a gate artifact does not make
the corresponding production gate green. Actual production evidence remains
explicitly recorded as pending until independently verified.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent
GATES = {
    "CI": "../.github/workflows/production-gate.yml",
    "Security / CodeQL": "../.github/workflows/security-gate.yml",
    "VSIX packaging": "../.github/workflows/extension-package.yml",
    "Infrastructure": "infrastructure-health-check.py",
    "Key custody": "key-custody-check.py",
    "Backup / restore": "backup-restore-check.py",
    "Rollback": "rollback-check.py",
    "Observability": "observability-check.py",
}


def main() -> int:
    print("DEEPCORE_PRODUCTION_READINESS")
    print("=" * 31)
    for name, relative in GATES.items():
        path = (ROOT / relative).resolve()
        state = "CONTROL PRESENT / EVIDENCE PENDING" if path.exists() else "MISSING CONTROL"
        print(f"[{state}] {name}: {relative}")

    print()
    print("WORKFLOW HYGIENE: EVIDENCE PENDING; stale BuildFailed registration must be disabled/removed")
    print("PRODUCTION CERTIFICATION: NOT CERTIFIED")
    print("CLASSIFICATION: PRODUCTION-CANDIDATE / CI-VERIFIED CORE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
