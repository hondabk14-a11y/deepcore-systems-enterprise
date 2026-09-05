#!/usr/bin/env python3
"""DeepCore backup/restore preflight.

Creates a temporary synthetic event log, copies it as a backup, verifies the
backup hash, restores it, and checks deterministic replay. No production data
or credentials are accessed. Passing this test is evidence for the backup
mechanism pattern only, not proof that production backups are configured.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import shutil
import tempfile


def canonical(value: dict) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def digest(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def replay(path: pathlib.Path) -> list[dict]:
    events: list[dict] = []
    previous = "GENESIS"
    for line in path.read_text(encoding="utf-8").splitlines():
        event = json.loads(line)
        if event["previous_hash"] != previous:
            raise ValueError("broken event chain")
        expected = hashlib.sha256(
            canonical({k: v for k, v in event.items() if k != "hash"})
        ).hexdigest()
        if event["hash"] != expected:
            raise ValueError("event hash mismatch")
        previous = event["hash"]
        events.append(event)
    return events


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="deepcore-backup-") as tmp:
        root = pathlib.Path(tmp)
        source = root / "source.jsonl"
        backup = root / "backup.jsonl"
        restored = root / "restored.jsonl"

        previous = "GENESIS"
        records = []
        for sequence, payload in enumerate(("BOOT", "STATE_COMMITTED", "CHECKPOINT"), 1):
            event = {"sequence": sequence, "type": payload, "previous_hash": previous}
            event["hash"] = hashlib.sha256(canonical(event)).hexdigest()
            previous = event["hash"]
            records.append(event)
        source.write_text("".join(json.dumps(e, sort_keys=True) + "\n" for e in records), encoding="utf-8")

        shutil.copy2(source, backup)
        source_hash = digest(source)
        backup_hash = digest(backup)
        if source_hash != backup_hash:
            print("BACKUP_RESTORE_PREFLIGHT=FAIL")
            print("FAILURE=backup hash differs from source")
            return 1

        shutil.copy2(backup, restored)
        original_events = replay(source)
        restored_events = replay(restored)
        if original_events != restored_events:
            print("BACKUP_RESTORE_PREFLIGHT=FAIL")
            print("FAILURE=restored event history differs from source")
            return 1

        if digest(restored) != source_hash:
            print("BACKUP_RESTORE_PREFLIGHT=FAIL")
            print("FAILURE=restored backup hash differs from source")
            return 1

    print("BACKUP_RESTORE_PREFLIGHT=PASS")
    print("SCOPE=synthetic local backup, integrity, and deterministic replay test")
    print("RESULT=backup hash matched and restored history replayed identically")
    print("PRODUCTION_DATA=not accessed")
    print("NOTE=production backup schedule, encryption, retention, offsite copies, restore drills, RPO/RTO, and disaster recovery require environment-specific evidence")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
