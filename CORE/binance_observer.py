"""Read-only Binance spot observations. Never submits transactions to consensus."""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import time
from decimal import Decimal
from pathlib import Path
from urllib.request import Request, urlopen

from CORE.deepcore_runtime import canonical, sha256_obj, ZERO_HASH

BASE_URL = "https://data-api.binance.vision"
NETWORK_ID = "deepcore-enterprise-2026"


def normalize(payload: dict, symbol: str, observed_at_ms: int) -> dict:
    if not re.fullmatch(r"[A-Z0-9]{5,20}", symbol):
        raise ValueError("invalid symbol")
    if type(observed_at_ms) is not int or observed_at_ms < 0:
        raise ValueError("invalid observation time")
    if not isinstance(payload, dict) or payload.get("symbol") != symbol:
        raise ValueError("symbol mismatch")
    values = {}
    for key in ("bidPrice", "bidQty", "askPrice", "askQty"):
        raw = payload.get(key)
        if not isinstance(raw, str) or len(raw) > 80 or not re.fullmatch(r"[0-9]+(?:\.[0-9]+)?", raw):
            raise ValueError("invalid decimal: " + key)
        number = Decimal(raw)
        if number <= 0 and key.endswith("Price"):
            raise ValueError("price must be positive")
        values[key] = raw  # Preserve exchange precision without binary floats.
    if Decimal(values["bidPrice"]) > Decimal(values["askPrice"]):
        raise ValueError("crossed quote")
    return {
        "schema_version": 1, "network_id": NETWORK_ID,
        "source": "binance", "venue": "spot", "symbol": symbol,
        "event_type": "MARKET_OBSERVATION", "trust": "external_untrusted",
        "observed_at_ms": observed_at_ms,
        "timestamp_kind": "local_receive_time",
        "source_hash": sha256_obj(payload), "quote": values,
    }


def fetch_quote(symbol: str, timeout: float = 5.0) -> dict:
    if not re.fullmatch(r"[A-Z0-9]{5,20}", symbol):
        raise ValueError("invalid symbol")
    request = Request(BASE_URL + "/api/v3/ticker/bookTicker?symbol=" + symbol,
                      headers={"User-Agent": "BKILLINGS-Observer/1"})
    # HTTP errors (including throttling or location restrictions) propagate.
    # No automatic retries, credentials, redirects to trading, or alternate venues.
    with urlopen(request, timeout=timeout) as response:
        raw = response.read(65537)
    if len(raw) > 65536:
        raise ValueError("oversized response")
    return normalize(json.loads(raw), symbol, time.time_ns() // 1_000_000)


def validate_event(event: dict) -> None:
    quote = event["quote"]
    expected = normalize({"symbol": event["symbol"], **quote},
                         event["symbol"], event["observed_at_ms"])
    for key in expected:
        if key != "source_hash" and event.get(key) != expected[key]:
            raise ValueError("invalid event field: " + key)
    if set(event) != set(expected) or not isinstance(event["source_hash"], str) or not re.fullmatch(r"[0-9a-f]{64}", event["source_hash"]):
        raise ValueError("invalid event schema or source hash")


class ObservationJournal:
    """Single SQLite journal with atomic deduplication and hash-chain replay.

    Hashes prove internal consistency, not Binance authenticity or protection
    against wholesale journal replacement. Anchor the head independently for that.
    """

    def __init__(self, path: str, *, read_only: bool = False):
        if read_only:
            # URI encoding prevents '?' or '#' in filenames becoming options.
            # mode=ro fails if missing and never initializes schema or WAL mode.
            self.db = sqlite3.connect(
                Path(path).absolute().as_uri() + "?mode=ro",
                uri=True, isolation_level=None)
            return
        self.db = sqlite3.connect(path, isolation_level=None)
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA synchronous=FULL")
        self.db.execute("""CREATE TABLE IF NOT EXISTS binance_observations (
            seq INTEGER PRIMARY KEY, event_id TEXT UNIQUE NOT NULL,
            body TEXT NOT NULL, previous_hash TEXT NOT NULL,
            record_hash TEXT NOT NULL)""")

    def close(self):
        self.db.close()

    def append(self, event: dict) -> bool:
        validate_event(event)
        body = canonical(event).decode()
        event_id = sha256_obj(event)
        self.db.execute("BEGIN IMMEDIATE")
        try:
            if self.db.execute("SELECT 1 FROM binance_observations WHERE event_id=?", (event_id,)).fetchone():
                self.db.execute("COMMIT")
                return False
            last = self.db.execute("SELECT seq, record_hash FROM binance_observations ORDER BY seq DESC LIMIT 1").fetchone()
            seq, previous = (last[0] + 1, last[1]) if last else (1, ZERO_HASH)
            digest = sha256_obj({"seq": seq, "event_id": event_id, "previous_hash": previous})
            self.db.execute("INSERT INTO binance_observations VALUES (?,?,?,?,?)",
                            (seq, event_id, body, previous, digest))
            self.db.execute("COMMIT")
            return True
        except BaseException:
            self.db.execute("ROLLBACK")
            raise

    def replay(self) -> dict:
        previous = ZERO_HASH
        state = {}
        for expected_seq, row in enumerate(self.db.execute(
                "SELECT seq,event_id,body,previous_hash,record_hash FROM binance_observations ORDER BY seq"), 1):
            seq, event_id, body, parent, digest = row
            event = json.loads(body)
            validate_event(event)
            if seq != expected_seq or parent != previous or sha256_obj(event) != event_id:
                raise ValueError("journal commitment mismatch")
            if sha256_obj({"seq": seq, "event_id": event_id, "previous_hash": parent}) != digest:
                raise ValueError("journal hash mismatch")
            state[event["symbol"]] = event
            previous = digest
        return {"head_hash": previous, "state_root": sha256_obj(state), "state": state}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--symbol", default="BTCUSDT")
    parser.add_argument("--journal", required=True)
    parser.add_argument("--replay", action="store_true")
    args = parser.parse_args()
    journal = ObservationJournal(args.journal)
    try:
        journal.replay()  # Fail closed on existing corruption before acquiring data.
        if not args.replay:
            journal.append(fetch_quote(args.symbol))
        print(json.dumps(journal.replay(), sort_keys=True))
    finally:
        journal.close()


if __name__ == "__main__":
    main()
