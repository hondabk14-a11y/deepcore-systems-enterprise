# BKILLINGS Binance observation integration

Implemented scope: one-shot public spot bid/ask acquisition, strict decimal-string
validation, DeepCore canonical SHA-256 hashing, atomic SQLite observation journal,
exact-event deduplication, and deterministic hash-chain replay.

Run from the repository root using Python 3.10 or newer, no new dependencies:

```sh
python -m unittest discover -s tests -p 'test_binance_observer.py' -v
python -m CORE.binance_observer --symbol BTCUSDT --journal /tmp/binance-observations.sqlite
python -m CORE.binance_observer --replay --journal /tmp/binance-observations.sqlite
```

Use a private persistent journal path for operation; do not commit database files.
Endpoint: https://data-api.binance.vision/api/v3/ticker/bookTicker
Official reference: https://github.com/binance/binance-spot-api-docs/blob/master/faqs/market_data_only.md

The exchange endpoint supplies no exchange timestamp or sequence for this snapshot.
observed_at_ms is explicitly local receipt time. source_hash commits to the parsed
source JSON, not raw HTTP bytes. Normalized prices preserve source strings.
Identical events are deduplicated; a fresh observation of an unchanged quote is
a distinct event because its receipt time differs.

Observations are external and untrusted. The journal uses CORE.deepcore_runtime
hashing but does not submit payment transactions, affect balances, participate in
consensus, or automatically anchor anything to Bitcoin. Consumers can use replay
state and its root as evidence inputs, subject to their own authorization policy.
This is the implemented observation boundary, not a deployed background collector.

HTTP errors propagate, including 429, 418, and region restrictions. Schedule polls
within Binance limits; honor Retry-After externally rather than immediately retrying.
No API keys are needed. No futures, websocket order-book reconstruction, automatic
QSI alerts, freshness gate, or production scheduling is claimed in this change.

Replay detects modified rows and broken linkage. A hash chain alone cannot detect
complete replacement or valid suffix truncation without an independently stored
head commitment. Hashes do not authenticate Binance as a cryptographic signer.

Validation: offline fixture tests cover restart, exact-event deduplication, malformed
quotes, forged trust metadata, HTTP failure, ordered replay, and tampering.
Live reachability and full repository CI require separate evidence.
