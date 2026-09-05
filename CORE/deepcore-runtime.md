# DeepCore Runtime Baseline

The Python runtime baseline includes an `EventSourcedLedger` and `BitcoinConnector` exposed through an aiohttp REST interface.

`EventSourcedLedger` is designed around SQLite with aiosqlite and WAL mode. Configuration includes ledger database path, snapshot interval, Bitcoin RPC settings, Web3 RPC URL, and an NFT contract address.

Runtime state must be reconstructible from events, with snapshots treated as acceleration artifacts rather than the sole source of truth.