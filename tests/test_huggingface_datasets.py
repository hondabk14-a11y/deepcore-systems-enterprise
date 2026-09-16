import copy
import sqlite3

import pytest

from AI.datasets import ingest as module
from CORE.deepcore_runtime import DeepCoreLedger, sha256_bytes


@pytest.fixture
def source(monkeypatch):
    raw = b'text,label\n"Revenue up, costs down",1\nLoss widens,0\n'
    spec = copy.deepcopy(module.source_spec("financial-news-validation"))
    spec["sha256"] = sha256_bytes(raw)
    monkeypatch.setattr(module, "source_spec", lambda name: spec)
    return spec, raw


def test_ingest_reopen_idempotency_and_ledger_isolation(tmp_path, source):
    _, raw = source
    ledger = DeepCoreLedger(["a", "b", "c", "d"])
    before = ledger.state_root()
    db = tmp_path / "observations.sqlite"
    first = module.ingest("fixture", db, raw=raw)
    second = module.ingest("fixture", db, raw=raw)
    assert (first["inserted"], second["inserted"], second["duplicates"]) == (2, 0, 2)
    rows = list(module.read_observations(db))
    assert {r["body"]["label"] for r in rows} == {"bullish", "bearish"}
    assert all(r["body"]["trust"] == "external_untrusted" for r in rows)
    assert ledger.state_root() == before and not ledger.events and not ledger.blocks


def test_checksum_rejected_before_store_creation(tmp_path, source):
    db = tmp_path / "observations.sqlite"
    with pytest.raises(ValueError, match="SHA-256"):
        module.ingest("fixture", db, raw=source[1] + b'changed')
    assert not db.exists()


@pytest.mark.parametrize("raw", [
    b'text,label\nok,1\nbad,99\n',
    b'text,label\nok,1\n,0\n',
    b'text,label\nok,1\nbad,0,extra\n',
    b'text,label\n',
    b'text,wrong\nok,1\n',
])
def test_invalid_source_is_atomic(tmp_path, source, raw):
    spec, _ = source
    spec["sha256"] = sha256_bytes(raw)
    db = tmp_path / "observations.sqlite"
    with pytest.raises(ValueError):
        module.ingest("fixture", db, raw=raw)
    assert not db.exists()


def test_split_provenance_changes_identity(source):
    spec, raw = source
    original = module.observations(spec, raw)
    other = dict(spec, split="train")
    assert original == module.observations(spec, raw)
    assert original[0]["observation_id"] != module.observations(other, raw)[0]["observation_id"]


def test_tampered_store_rejected_and_import_rolled_back(tmp_path, source):
    spec, raw = source
    db = tmp_path / "observations.sqlite"
    module.ingest("fixture", db, raw=raw)
    rows = module.observations(spec, raw)
    with sqlite3.connect(db) as con:
        con.execute("DELETE FROM dataset_observations WHERE observation_id = ?", (rows[0]["observation_id"],))
        con.execute("UPDATE dataset_observations SET body = '{}' WHERE observation_id = ?", (rows[1]["observation_id"],))
    with pytest.raises(ValueError, match="integrity"):
        module.ingest("fixture", db, raw=raw)
    with sqlite3.connect(db) as con:
        assert con.execute("SELECT count(*) FROM dataset_observations").fetchone()[0] == 1
    with pytest.raises(ValueError, match="integrity"):
        list(module.read_observations(db))


def test_unknown_dataset_fails_closed():
    with pytest.raises(ValueError, match="reviewed registry"):
        module.source_spec("unreviewed/source")


def test_download_limit(monkeypatch):
    class Response:
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def read(self, n): return b'x' * n
    monkeypatch.setattr(module.urllib.request, "urlopen", lambda *a, **kw: Response())
    monkeypatch.setattr(module, "MAX_BYTES", 8)
    with pytest.raises(ValueError, match="download limit"):
        module.fetch(module.source_spec("financial-news-validation"))
