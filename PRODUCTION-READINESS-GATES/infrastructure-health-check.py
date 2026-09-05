#!/usr/bin/env python3
"""DeepCore infrastructure health preflight.

This is an environment-neutral preflight. It validates the local execution
host and required repository controls without pretending that remote
Kafka/NATS/Kubernetes/Bitcoin infrastructure is reachable.

Exit 0 means the checks that this script is capable of proving passed.
It does not certify production infrastructure.
"""

from __future__ import annotations

import os
import pathlib
import platform
import shutil
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
REQUIRED_FILES = (
    ".gitignore",
    "SECURITY.md",
    "PRODUCTION-GATE.md",
    ".github/workflows/production-gate.yml",
    ".github/workflows/security-gate.yml",
    "CORE/event-sourced-ledger/ledger.py",
    "CORE/event-sourced-ledger/test_ledger.py",
)


def check(label: str, passed: bool, detail: str) -> bool:
    state = "PASS" if passed else "FAIL"
    print(f"[{state}] {label}: {detail}")
    return passed


def main() -> int:
    results: list[bool] = []
    results.append(check("repository root", REPO_ROOT.is_dir(), str(REPO_ROOT)))
    results.append(check("python runtime", sys.version_info >= (3, 12), platform.python_version()))
    results.append(check("git available", shutil.which("git") is not None, str(shutil.which("git"))))

    for relative in REQUIRED_FILES:
        path = REPO_ROOT / relative
        results.append(check(f"required control {relative}", path.is_file(), "present" if path.is_file() else "missing"))

    secret_env_names = ("OPENAI_API_KEY", "AWS_SECRET_ACCESS_KEY", "GITHUB_TOKEN")
    present_secrets = [name for name in secret_env_names if os.environ.get(name)]
    # Presence is reported but never printed as a value. This is intentionally
    # a warning-level observation because CI environments may legitimately set
    # credentials. The repository must never contain their values.
    results.append(check("secret values not exposed by checker", True, f"observed {len(present_secrets)} configured secret variable(s); values not printed"))

    print(f"INFRASTRUCTURE_PREFLIGHT={'PASS' if all(results) else 'FAIL'}")
    print("SCOPE=local repository and execution-host preflight only")
    print("NOTE=remote production infrastructure, key custody, backup, rollback, and observability require environment-specific evidence")
    return 0 if all(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
