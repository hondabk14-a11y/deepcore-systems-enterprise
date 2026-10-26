#!/usr/bin/env python3
"""DeepCore cryptographic key-custody preflight.

This checker validates repository custody boundaries without loading, generating,
or printing real private keys. Production key custody must be performed by the
approved HSM/KMS or isolated signing environment and evidenced separately.
"""

from __future__ import annotations

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
FORBIDDEN_NAME = re.compile(r"(^|/)(\.env($|\.)|.*\.(pem|key|p12|pfx|jks)$|secrets/|credentials/|wallets/)", re.I)
# Literal values only: runtime expressions and Python type annotations are not secrets.
SECRET_NAME = r"\b[a-z_]*(?:api[_-]?key|secret|private[_-]?key|password|token)"
SECRET_VALUE = re.compile(
    SECRET_NAME + r"[ \t]*[:=][ \t]*([\"'])[A-Za-z0-9_./+\-=]{16,}\1", re.I
)
RAW_VALUE = r"[A-Za-z0-9_./+\-=]{16,}(?=[ \t]*(?:$|[#;]))"
ENV_VALUE = re.compile(r"^[ \t]*(?:export[ \t]+)?" + SECRET_NAME + r"[ \t]*=[ \t]*" + RAW_VALUE, re.I | re.M)
YAML_VALUE = re.compile(SECRET_NAME + r"[ \t]*:[ \t]*" + RAW_VALUE, re.I | re.M)


def contains_secret(sample: str, suffix: str = "") -> bool:
    return bool(SECRET_VALUE.search(sample) or ENV_VALUE.search(sample)
                or (suffix in {".yaml", ".yml"} and YAML_VALUE.search(sample)))


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

    tracked = []
    git_dir = ROOT / ".git"
    if git_dir.exists():
        import subprocess
        result = subprocess.run(
            ["git", "-C", str(ROOT), "ls-files"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            tracked = result.stdout.splitlines()
            for path in tracked:
                if FORBIDDEN_NAME.search(path):
                    failures.append(f"forbidden credential/key path tracked: {path}")
                file_path = ROOT / path
                if file_path.is_file():
                    try:
                        sample = file_path.read_text(encoding="utf-8", errors="ignore")
                    except OSError:
                        continue
                    if contains_secret(sample, file_path.suffix):
                        failures.append(f"possible embedded secret in tracked file: {path}")

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
