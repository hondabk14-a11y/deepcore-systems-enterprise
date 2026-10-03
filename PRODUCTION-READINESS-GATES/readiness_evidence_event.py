"""Build deterministic DeepCore readiness-evidence events.

The event binds an evidence manifest to its exact commit and workflow run.
It is an audit representation only and does not certify production or mutate
an authoritative ledger by itself.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any

EVENT_TYPE = "READINESS_EVIDENCE"


@dataclass(frozen=True)
class ReadinessEvidenceEvent:
    event_type: str
    schema_version: str
    repository: str
    commit_sha: str
    workflow_run_id: int
    workflow_run_attempt: int
    manifest_hash: str
    certification: str
    external_evidence_required: bool

    def to_mapping(self) -> dict[str, Any]:
        return {
            "event_type": self.event_type,
            "schema_version": self.schema_version,
            "repository": self.repository,
            "commit_sha": self.commit_sha,
            "workflow_run_id": self.workflow_run_id,
            "workflow_run_attempt": self.workflow_run_attempt,
            "manifest_hash": self.manifest_hash,
            "certification": self.certification,
            "external_evidence_required": self.external_evidence_required,
        }

    def canonical_json(self) -> str:
        return json.dumps(self.to_mapping(), sort_keys=True, separators=(",", ":"))

    def event_hash(self) -> str:
        return hashlib.sha256(self.canonical_json().encode("utf-8")).hexdigest()


def build_readiness_evidence_event(manifest: dict[str, Any]) -> ReadinessEvidenceEvent:
    """Bind a validated readiness manifest to a deterministic audit event."""
    required = {
        "schema_version", "evidence_type", "repository", "commit_sha",
        "workflow_run_id", "workflow_run_attempt", "certification",
        "external_evidence_required",
    }
    missing = required - manifest.keys()
    if missing:
        raise ValueError(f"manifest missing fields: {sorted(missing)}")
    if manifest["evidence_type"] != "readiness-preflight":
        raise ValueError("unexpected evidence_type")
    if manifest["certification"] != "NOT_CERTIFIED":
        raise ValueError("readiness evidence cannot certify production")
    if manifest["external_evidence_required"] is not True:
        raise ValueError("external_evidence_required must remain true")
    if not isinstance(manifest["commit_sha"], str) or len(manifest["commit_sha"]) != 40:
        raise ValueError("commit_sha must be a 40-character identifier")
    if not isinstance(manifest["workflow_run_id"], int) or isinstance(manifest["workflow_run_id"], bool) or manifest["workflow_run_id"] <= 0:
        raise ValueError("workflow_run_id must be a positive integer")
    if not isinstance(manifest["workflow_run_attempt"], int) or isinstance(manifest["workflow_run_attempt"], bool) or manifest["workflow_run_attempt"] <= 0:
        raise ValueError("workflow_run_attempt must be a positive integer")

    canonical_manifest = json.dumps(manifest, sort_keys=True, separators=(",", ":"))
    manifest_hash = hashlib.sha256(canonical_manifest.encode("utf-8")).hexdigest()

    return ReadinessEvidenceEvent(
        event_type=EVENT_TYPE,
        schema_version=str(manifest["schema_version"]),
        repository=str(manifest["repository"]),
        commit_sha=manifest["commit_sha"],
        workflow_run_id=manifest["workflow_run_id"],
        workflow_run_attempt=manifest["workflow_run_attempt"],
        manifest_hash=manifest_hash,
        certification="NOT_CERTIFIED",
        external_evidence_required=True,
    )
