#!/usr/bin/env python3
"""Crash-safe persistence primitives for the DeepCore reference consensus layer.

Snapshots are versioned, canonicalized, checksummed, and atomically replaced.
This is a local reference implementation, not a substitute for a production
WAL or replicated durable storage system.
"""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import asdict
from pathlib import Path
from typing import Any

from CORE.deepcore_consensus import ConsensusVote, QuorumCertificate
from CORE.deepcore_hotstuff import HotStuffState, Phase
from CORE.deepcore_runtime import canonical, sha256_bytes


SCHEMA_VERSION = 1


def _qc_to_dict(qc: QuorumCertificate | None) -> dict[str, Any] | None:
    if qc is None:
        return None
    return {
        "height": qc.height,
        "round": qc.round,
        "proposal_hash": qc.proposal_hash,
        "votes": [asdict(v) for v in qc.votes],
    }


def _qc_from_dict(value: dict[str, Any] | None) -> QuorumCertificate | None:
    if value is None:
        return None
    try:
        votes = tuple(ConsensusVote(**vote) for vote in value["votes"])
        return QuorumCertificate(int(value["height"]), int(value["round"]), str(value["proposal_hash"]), votes)
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("invalid quorum certificate snapshot") from exc


class ConsensusSnapshotStore:
    """Persist and recover HotStuff safety state with integrity checks."""

    def __init__(self, path: str | os.PathLike[str]):
        self.path = Path(path)

    @staticmethod
    def _body(state: HotStuffState, transport_sequences: dict[str, int] | None = None) -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "state": {
                "view": state.view,
                "phase": state.phase.value,
                "proposal_hash": state.proposal_hash,
                "prepare_qc": _qc_to_dict(state.prepare_qc),
                "pre_commit_qc": _qc_to_dict(state.pre_commit_qc),
                "locked_hash": state.locked_hash,
                "highest_qc": _qc_to_dict(state.highest_qc),
            },
            "transport_sequences": dict(sorted((transport_sequences or {}).items())),
        }

    @staticmethod
    def _encode(body: dict[str, Any]) -> bytes:
        return canonical(body)

    def save(self, state: HotStuffState, transport_sequences: dict[str, int] | None = None) -> str:
        if state.view < 0:
            raise ValueError("view cannot be negative")
        if any(not isinstance(v, int) or v < 1 for v in (transport_sequences or {}).values()):
            raise ValueError("transport sequence values must be positive integers")
        body = self._body(state, transport_sequences)
        payload = {"body": body, "checksum": sha256_bytes(self._encode(body))}
        encoded = canonical(payload)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_name = tempfile.mkstemp(prefix=f".{self.path.name}.", dir=self.path.parent)
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(encoded)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(tmp_name, self.path)
            directory_fd = os.open(self.path.parent, os.O_RDONLY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
        finally:
            if os.path.exists(tmp_name):
                os.unlink(tmp_name)
        return sha256_bytes(encoded)

    def load(self, minimum_view: int | None = None) -> tuple[HotStuffState, dict[str, int], str]:
        try:
            raw = self.path.read_bytes()
            document = json.loads(raw.decode("utf-8"))
            body = document["body"]
            checksum = document["checksum"]
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, KeyError, TypeError) as exc:
            raise ValueError("invalid or unreadable consensus snapshot") from exc
        if not isinstance(body, dict) or not isinstance(checksum, str):
            raise ValueError("malformed consensus snapshot")
        if sha256_bytes(self._encode(body)) != checksum:
            raise ValueError("consensus snapshot checksum mismatch")
        if body.get("schema_version") != SCHEMA_VERSION:
            raise ValueError("unsupported consensus snapshot schema")
        try:
            raw_state = body["state"]
            view = int(raw_state["view"])
            phase = Phase(raw_state["phase"])
            state = HotStuffState(
                view=view,
                phase=phase,
                proposal_hash=raw_state.get("proposal_hash"),
                prepare_qc=_qc_from_dict(raw_state.get("prepare_qc")),
                pre_commit_qc=_qc_from_dict(raw_state.get("pre_commit_qc")),
                locked_hash=raw_state.get("locked_hash"),
                highest_qc=_qc_from_dict(raw_state.get("highest_qc")),
            )
            sequences = {str(k): int(v) for k, v in body.get("transport_sequences", {}).items()}
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("invalid consensus state snapshot") from exc
        if view < 0 or any(v < 1 for v in sequences.values()):
            raise ValueError("invalid rollback or sequence state")
        if minimum_view is not None and view < minimum_view:
            raise ValueError(f"snapshot rollback detected: minimum view is {minimum_view}, got {view}")
        return state, sequences, sha256_bytes(raw)


class PersistentHotStuffStateMachine:
    """HotStuff state wrapper that persists after safety-critical transitions."""

    def __init__(self, machine: Any, store: ConsensusSnapshotStore):
        self.machine = machine
        self.store = store

    def save(self, transport_sequences: dict[str, int] | None = None) -> str:
        return self.store.save(self.machine.state, transport_sequences)

    def restore(self, minimum_view: int | None = None) -> dict[str, int]:
        state, sequences, _ = self.store.load(minimum_view=minimum_view)
        self.machine.state = state
        return sequences
