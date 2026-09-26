"""Bounded local baseline; excludes network and HSM latency."""
import json
import platform
import sqlite3
import statistics
import tempfile
import time
from pathlib import Path
import cryptography
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from protocol import public, sign_transaction, propose
from storage import Ledger


def run(blocks=100, batch=10):
    keys = [Ed25519PrivateKey.generate() for _ in range(4)]
    writer = Ed25519PrivateKey.generate()
    spec = {'version':2, 'network':'benchmark-v2', 'epoch':0, 'validators':[public(k) for k in keys], 'faults':1, 'writers':[public(writer)]}
    durations = []
    with tempfile.TemporaryDirectory() as temp:
        path = Path(temp)/'ledger.sqlite'
        with Ledger(path, spec, create=True) as ledger:
            start = time.perf_counter()
            nonce = 0
            for i in range(blocks):
                tick = time.perf_counter(); snapshot = ledger.snapshot(); txs = []
                for _ in range(batch):
                    nonce += 1
                    txs.append(sign_transaction(writer, spec, nonce, 1000+i, 'BENCHMARK', {'v':nonce}))
                block = propose(spec, snapshot['state'], i+1, snapshot['hash'], snapshot['timestamp'], txs, 1000+i)
                votes = [ledger.vote(k, block, 1000+i) for k in keys[:3]]
                ledger.commit(block, votes)
                durations.append(time.perf_counter()-tick)
            elapsed = time.perf_counter()-start
            tick = time.perf_counter(); snapshot = ledger.snapshot(); replay = time.perf_counter()-tick
            assert snapshot['height'] == blocks and snapshot['state']['nonces'][public(writer)] == blocks*batch
    ordered = sorted(durations)
    return {'blocks':blocks, 'transactions':blocks*batch, 'batch_size':batch,
            'elapsed_seconds':round(elapsed,4), 'transactions_per_second':round(blocks*batch/elapsed,2),
            'block_p50_ms':round(statistics.median(durations)*1000,2),
            'block_p95_ms':round(ordered[int(.95*(len(ordered)-1))]*1000,2),
            'full_replay_ms':round(replay*1000,2), 'python':platform.python_version(),
            'sqlite':sqlite3.sqlite_version, 'cryptography':cryptography.__version__,
            'scope':'single machine; three signer keys in one process; full replay per operation; no network/HSM',
            'production_capacity_claim':False}


if __name__ == '__main__': print(json.dumps(run(), indent=2))
