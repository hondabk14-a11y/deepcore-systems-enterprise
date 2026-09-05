"""Map readiness evidence into an SSIL decision without granting authority."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from ssil_engine import SSILEvidence, SSILDecision, evaluate  # noqa: E402


REQUIRED_CONTROL_KEYS = (
    "infrastructure",
    "key_custody",
    "backup_restore",
    "rollback",
    "observability",
)


def evaluate_readiness_manifest(manifest: dict) -> SSILDecision:
    """Evaluate readiness evidence as SSIL evidence.

    This adapter is advisory: it produces a decision only and never authorizes
    deployment, key use, ledger mutation, or production certification.
    """
    if not isinstance(manifest, dict):
        raise TypeError("manifest must be a mapping")

    controls = manifest.get("controls")
    if not isinstance(controls, dict):
        return evaluate(SSILEvidence(security_controls_valid=False))

    complete = all(
        isinstance(controls.get(key), str) and bool(controls.get(key).strip())
        for key in REQUIRED_CONTROL_KEYS
    )

    certification_boundary_valid = (
        manifest.get("certification") == "NOT_CERTIFIED"
        and manifest.get("external_evidence_required") is True
    )

    return evaluate(
        SSILEvidence(
            security_controls_valid=certification_boundary_valid,
            evidence_complete=complete,
        )
    )
