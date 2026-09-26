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
from protocol import public, sign_transaction, propose, digest
from storage import Ledger


def run(blocks=100, batch=10, incremental=True, material=None):
    keys, writer = material or ([Ed25519PrivateKey.generate() for _ in range(4)], Ed25519PrivateKey.generate())
    spec = {'version':2, 'network':'benchmark-v2', 'epoch':0, 'validators':[public(k) for k in keys], 'faults':1, 'writers':[public(writer)]}
    durations = []
    with tempfile.TemporaryDirectory() as temp:
        path = Path(temp)/'ledger.sqlite'
        with Ledger(path, spec, create=True, incremental=incremental) as ledger:
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
            cached = ledger.snapshot()
            tick = time.perf_counter(); snapshot = ledger.snapshot(full_audit=True); replay = time.perf_counter()-tick
            assert cached == snapshot
            assert snapshot['height'] == blocks and snapshot['state']['nonces'][public(writer)] == blocks*batch
    ordered = sorted(durations)
    return {'mode':'incremental' if incremental else 'full-replay-per-operation',
            'final_state_root':digest('state',snapshot['state']), 'final_block_hash':snapshot['hash'],
            'audit_equal':True, 'blocks':blocks, 'transactions':blocks*batch, 'batch_size':batch,
            'elapsed_seconds':round(elapsed,4), 'transactions_per_second':round(blocks*batch/elapsed,2),
            'block_p50_ms':round(statistics.median(durations)*1000,2),
            'block_p95_ms':round(ordered[int(.95*(len(ordered)-1))]*1000,2),
            'full_replay_ms':round(replay*1000,2), 'python':platform.python_version(),
            'sqlite':sqlite3.sqlite_version, 'cryptography':cryptography.__version__,
            'scope':'single machine; three signer keys in one process; no network/HSM; final replay independently audited',
            'production_capacity_claim':False}


def compare(blocks=100, batch=10):
    material = ([Ed25519PrivateKey.generate() for _ in range(4)], Ed25519PrivateKey.generate())
    baseline = run(blocks, batch, incremental=False, material=material)
    optimized = run(blocks, batch, incremental=True, material=material)
    assert baseline['final_state_root'] == optimized['final_state_root']
    assert baseline['final_block_hash'] == optimized['final_block_hash']
    return {'baseline':baseline, 'incremental':optimized,
            'identical_final_state_and_block':True,
            'throughput_ratio':round(optimized['transactions_per_second']/baseline['transactions_per_second'],2)}


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--compare', action='store_true')
    parser.add_argument('--blocks', type=int, default=100)
    parser.add_argument('--batch', type=int, default=10)
    args = parser.parse_args()
    if args.blocks < 1 or not 1 <= args.batch <= 100: parser.error('Require blocks >= 1 and batch 1..100')
    print(json.dumps((compare if args.compare else run)(args.blocks, args.batch), indent=2))
