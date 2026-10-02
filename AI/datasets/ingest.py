"""Pinned public Hugging Face CSVs -> external observation SQLite store.

No dataset code is executed and no transaction or ledger API is called.
The registry is reviewed configuration, not downloaded dataset content.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import re
import sqlite3
import urllib.request
from pathlib import Path

from CORE.deepcore_runtime import canonical, sha256_bytes, sha256_obj

REGISTRY = Path(__file__).with_name("registry.json")
MAX_BYTES = 16 * 1024 * 1024
MAX_ROWS = 100_000


def source_spec(name: str) -> dict:
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    if name not in registry:
        raise ValueError("dataset is not in the reviewed registry")
    spec = registry[name]
    if not re.fullmatch(r"[\w.-]+/[\w.-]+", spec["repository"]):
        raise ValueError("invalid repository")
    if not re.fullmatch(r"[0-9a-f]{40}", spec["revision"]):
        raise ValueError("dataset revision must be a commit SHA")
    if not re.fullmatch(r"[0-9a-f]{64}", spec["sha256"]):
        raise ValueError("invalid source hash")
    if not re.fullmatch(r"[\w-]+\.csv", spec["file"]):
        raise ValueError("invalid dataset filename")
    return spec


def fetch(spec: dict) -> bytes:
    url = (f'https://huggingface.co/datasets/{spec["repository"]}/resolve/'
           f'{spec["revision"]}/{spec["file"]}')
    request = urllib.request.Request(url, headers={"User-Agent": "DeepCore-datasets/1"})
    # Public curated sources only. Never attach a credential to redirect targets.
    with urllib.request.urlopen(request, timeout=30) as response:
        data = response.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise ValueError("dataset exceeds download limit")
    return data


def observations(spec: dict, raw: bytes) -> list[dict]:
    if len(raw) > MAX_BYTES or sha256_bytes(raw) != spec["sha256"]:
        raise ValueError("dataset size or SHA-256 mismatch")
    reader = csv.DictReader(io.StringIO(raw.decode("utf-8"), newline=""), strict=True)
    if reader.fieldnames != ["text", "label"]:
        raise ValueError("unexpected CSV schema")
    result = []
    for index, row in enumerate(reader):
        if index >= MAX_ROWS:
            raise ValueError("dataset exceeds row limit")
        if (set(row) != {"text", "label"} or not row["text"]
                or not row["text"].strip() or len(row["text"]) > 100_000
                or row["label"] not in spec["labels"]):
            raise ValueError(f"invalid dataset row {index}")
        body = {
            "schema_version": 1,
            "event_type": "DATASET_ROW_OBSERVED",
            "trust": "external_untrusted",
            "provider": "huggingface",
            "repository": spec["repository"],
            "revision": spec["revision"],
            "file": spec["file"],
            "split": spec["split"],
            "source_sha256": spec["sha256"],
            "license": spec["license"],
            "purpose": spec["purpose"],
            "row_index": index,
            "text": row["text"],
            "label": spec["labels"][row["label"]],
        }
        result.append({"observation_id": sha256_obj(body), "body": body})
    if not result:
        raise ValueError("empty dataset")
    return result


def ingest(name: str, database: str | Path, *, raw: bytes | None = None) -> dict:
    spec = source_spec(name)
    items = observations(spec, fetch(spec) if raw is None else raw)
    # Validate the entire source before opening the store. One import is atomic.
    connection = sqlite3.connect(database)
    try:
        with connection:
            connection.execute("""CREATE TABLE IF NOT EXISTS dataset_observations (
                observation_id TEXT PRIMARY KEY, body TEXT NOT NULL)""")
            inserted = 0
            for item in items:
                encoded = canonical(item["body"]).decode("utf-8")
                existing = connection.execute(
                    "SELECT body FROM dataset_observations WHERE observation_id = ?",
                    (item["observation_id"],),
                ).fetchone()
                if existing is not None:
                    if existing[0] != encoded:
                        raise ValueError("stored observation integrity mismatch")
                    continue
                connection.execute("INSERT INTO dataset_observations VALUES (?, ?)",
                                   (item["observation_id"], encoded))
                inserted += 1
        return {"dataset": name, "rows": len(items), "inserted": inserted,
                "duplicates": len(items) - inserted, "source_sha256": spec["sha256"],
                "trust": "external_untrusted"}
    finally:
        connection.close()


def read_observations(database: str | Path):
    """Yield checked records for advisory evaluation; never authorize actions."""
    uri = Path(database).resolve().as_uri() + "?mode=ro"
    connection = sqlite3.connect(uri, uri=True)
    try:
        for observation_id, encoded in connection.execute(
            "SELECT observation_id, body FROM dataset_observations ORDER BY observation_id"
        ):
            body = json.loads(encoded)
            if sha256_obj(body) != observation_id:
                raise ValueError("stored observation integrity mismatch")
            yield {"observation_id": observation_id, "body": body}
    finally:
        connection.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset", choices=sorted(json.loads(REGISTRY.read_text())))
    parser.add_argument("--database", required=True, help="Dedicated observation SQLite path")
    args = parser.parse_args()
    try:
        print(json.dumps(ingest(args.dataset, args.database), sort_keys=True))
    except (ValueError, OSError, sqlite3.Error, csv.Error) as exc:
        parser.exit(1, f"Dataset ingestion failed: {exc}\n")


if __name__ == "__main__":
    main()
