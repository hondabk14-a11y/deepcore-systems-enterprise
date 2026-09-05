#!/usr/bin/env python3
"""DeepCore observability preflight.

Validates that the repository declares the minimum operational telemetry
contract without connecting to production systems. A passing result confirms
the contract is machine-checkable, not that production dashboards or alerts
are healthy.
"""

from __future__ import annotations

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
REQUIRED_SIGNALS = (
    "availability",
    "latency",
    "error",
    "event",
    "consensus",
    "security",
    "backup",
    "rollback",
)


def main() -> int:
    workflow_dir = ROOT / ".github" / "workflows"
    source_files = list(workflow_dir.glob("*.yml")) + list(workflow_dir.glob("*.yaml"))
    source_files += list((ROOT / "PRODUCTION-READINESS-GATES").glob("*.py"))

    corpus = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore").lower()
        for path in source_files
        if path.is_file()
    )

    missing = [signal for signal in REQUIRED_SIGNALS if not re.search(rf"\b{re.escape(signal)}\b", corpus)]
    if missing:
        print("OBSERVABILITY_PREFLIGHT=FAIL")
        print("MISSING_SIGNALS=" + ",".join(missing))
        return 1

    print("OBSERVABILITY_PREFLIGHT=PASS")
    print("SCOPE=repository telemetry contract preflight")
    print("SIGNALS=" + ",".join(REQUIRED_SIGNALS))
    print("RESULT=required operational signal categories are represented in repository controls")
    print("PRODUCTION_TELEMETRY=not queried")
    print("NOTE=production dashboards, metric exporters, logs, traces, alert routing, SLO thresholds, on-call response, and alert drills require environment-specific evidence")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
