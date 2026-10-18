"""Repository secret-path and obvious literal-secret checks; not a full scanner."""
from pathlib import Path
import re
import subprocess
import sys

FORBIDDEN = re.compile(r"(^|/)(\.env($|\.)|.*\.(pem|key|p12|pfx|jks)$|secrets/|credentials/|wallets/)", re.I)
PRIVATE_MATERIAL = re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |ENCRYPTED )?PRIVATE KEY-----")
LITERAL_SECRET = re.compile(
    r"(?im)^\s*(?:(?:const|let|var|export)\s+)?(?:[a-z0-9_]*(?:api_key|secret|private_key|password|token))"
    r"\s*=\s*['\"][A-Za-z0-9_./+\-=]{16,}['\"]"
)
ENV_SECRET = re.compile(
    r"(?im)^\s*(?:export\s+)?[A-Z0-9_]*(?:API_KEY|SECRET|PRIVATE_KEY|PASSWORD|TOKEN)"
    r"\s*=\s*[^\s#]+"
)


def findings(path, text):
    issues = []
    template = Path(path).name == ".env.example"
    if FORBIDDEN.search(path) and not template:
        issues.append("forbidden credential/key path")
    if PRIVATE_MATERIAL.search(text):
        issues.append("private-key material")
    if LITERAL_SECRET.search(text):
        issues.append("possible literal secret")
    if template:
        for line in text.splitlines():
            stripped = line.strip()
            match = ENV_SECRET.search(stripped) if stripped and not stripped.startswith("#") else None
            if match and stripped.split("=", 1)[1].strip().strip("\"'"):
                issues.append("credential value in environment template")
                break
    elif Path(path).suffix not in {".py", ".js", ".mjs", ".ts", ".md"} and ENV_SECRET.search(text):
        issues.append("possible environment credential value")
    return issues


def check_repository(root):
    result = subprocess.run(["git", "-C", str(root), "ls-files", "-z"],
                            capture_output=True, check=True)
    paths = [p for p in result.stdout.decode().split("\0") if p]
    if not paths:
        raise ValueError("No tracked files available for verification")
    issues = []
    for path in paths:
        file = root / path
        if not file.is_file() or file.is_symlink():
            issues.append(f"{path}: tracked file unavailable or symbolic link")
            continue
        text = file.read_text(encoding="utf-8", errors="replace")
        issues.extend(f"{path}: {issue}" for issue in findings(path, text))
    return issues


def main():
    try:
        issues = check_repository(Path(__file__).resolve().parents[1])
    except (OSError, ValueError, subprocess.CalledProcessError):
        print("SECRET CHECK FAIL: tracked file inventory unavailable")
        return 1
    for issue in issues:
        print(issue)  # Never print matched values.
    print("TRACKED_SECRET_CHECK=" + ("FAIL" if issues else "PASS"))
    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
