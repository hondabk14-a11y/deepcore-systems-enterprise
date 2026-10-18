#!/usr/bin/env python3
"""DeepCore cryptographic key-custody preflight.

This checker validates repository custody boundaries without loading, generating,
or printing real private keys. Production key custody must be performed by the
approved HSM/KMS or isolated signing environment and evidenced separately.
"""

from __future__ import annotations

import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
from tracked_secret_check import check_repository


def main() -> int:
    failures: list[str] = []
    gitignore = ROOT / ".gitignore"

    if not gitignore.is_file():
        failures.append(".gitignore missing")
    else:
        text = gitignore.read_text(encoding="utf-8")
        for required in (".env", "*.pem", "*.key", "secrets/", "credentials/", "wallets/"):
            if required not in text:
                failures.append(f".gitignore does not explicitly cover {required}")

    try:
        failures.extend(check_repository(ROOT))
    except (OSError, ValueError, subprocess.CalledProcessError):
        failures.append("tracked file inventory unavailable; custody check was not performed")

    print("KEY_CUSTODY_PREFLIGHT=" + ("PASS" if not failures else "FAIL"))
    print("SCOPE=repository custody-boundary preflight")
    print("PRIVATE_KEYS=not loaded, generated, printed, or stored by this checker")
    if failures:
        for failure in failures:
            print("FAILURE=" + failure)
        return 1

    print("RESULT=no forbidden tracked key/credential paths or obvious embedded secret patterns detected")
    print("NOTE=HSM/KMS custody, access policy, signing ceremony, rotation, recovery, and production authorization require environment-specific evidence")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
