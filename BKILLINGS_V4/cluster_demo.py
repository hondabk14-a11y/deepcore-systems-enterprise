"""Four independent loopback validator processes, throwaway keys and storage."""
import json
import os
import secrets
import selectors
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from key_store import create_key
from protocol import canonical, digest, public, propose, sign_transaction, verify_certificate
from storage import Ledger


def run():
    processes = []
    with tempfile.TemporaryDirectory(prefix='bk-cluster-') as folder:
        root = Path(folder)
        password = secrets.token_urlsafe(32).encode()
        validators = [create_key(root/f'key-{i}.pem', password) for i in range(4)]
        writer = Ed25519PrivateKey.generate()
        spec = {'version': 2, 'network': 'bkillings-local-demo-v2', 'epoch': 0,
                'validators': validators, 'faults': 1, 'writers': [public(writer)]}
        (root/'spec.json').write_bytes(canonical(spec))
        token = secrets.token_urlsafe(32)
        fd = os.open(root/'token', os.O_CREAT|os.O_EXCL|os.O_WRONLY, 0o600)
        with os.fdopen(fd, 'w') as stream: stream.write(token)
        configs = []
        ports = []
        def start(i):
            proc = subprocess.Popen([sys.executable, str(Path(__file__).with_name('node.py')), '--config', str(configs[i])],
                                    stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            processes.append(proc)
            proc.stdin.write(password+b'\n'); proc.stdin.close()
            selector = selectors.DefaultSelector(); selector.register(proc.stdout, selectors.EVENT_READ)
            try:
                if not selector.select(10): raise RuntimeError('Validator startup timeout')
                ready = json.loads(proc.stdout.readline())
            finally: selector.close()
            return proc, ready['port']
        def request(port, path, body=None, authorized=True):
            data = None if body is None else canonical(body)
            headers = {'Content-Type': 'application/json'}
            if authorized: headers['Authorization'] = 'Bearer '+token
            req = urllib.request.Request(f'http://127.0.0.1:{port}{path}', data=data, headers=headers)
            try:
                with urllib.request.urlopen(req, timeout=10) as response: return response.status, json.load(response)
            except urllib.error.HTTPError as exc: return exc.code, json.load(exc)
        try:
            nodes = []
            for i in range(4):
                with Ledger(root/f'node-{i}.sqlite', spec, create=True): pass
                cfg = {'spec': str(root/'spec.json'), 'database': str(root/f'node-{i}.sqlite'),
                       'key': str(root/f'key-{i}.pem'), 'token': str(root/'token'), 'port': 0}
                path = root/f'config-{i}.json'; path.write_bytes(canonical(cfg)); configs.append(path)
                proc, port = start(i); nodes.append(proc); ports.append(port)
            unauthorized, _ = request(ports[0], '/status', authorized=False)
            assert unauthorized == 401
            # One offline process: the remaining 3-of-4 can certify.
            nodes[3].terminate(); nodes[3].wait(timeout=5)
            with Ledger(root/'node-0.sqlite', spec) as ledger: snap = ledger.snapshot()
            now = int(time.time())
            tx = sign_transaction(writer, spec, 1, now, 'OBSERVATION', {'demo': True})
            block = propose(spec, snap['state'], 1, snap['hash'], 0, [tx], now)
            votes = []
            for port in ports[:3]:
                status, vote = request(port, '/vote', block); assert status == 200; votes.append(vote)
            assert verify_certificate(spec, block, votes)
            # Reopen the signer process before checking its persisted vote lock.
            nodes[0].terminate(); nodes[0].wait(timeout=5)
            nodes[0], ports[0] = start(0)
            conflicting = propose(spec, snap['state'], 1, snap['hash'], 0,
                                   [sign_transaction(writer, spec, 1, now, 'OBSERVATION', {'different': True})], now)
            status, _ = request(ports[0], '/vote', conflicting); assert status == 400
            for port in ports[:3]:
                status, result = request(port, '/commit', {'block':block, 'votes':votes})
                assert status == 200 and result['committed']
            states = [request(port, '/status')[1] for port in ports[:3]]
            assert len({s['hash'] for s in states}) == 1
            # Restart a process and verify persistent head and key identity.
            nodes[0].terminate(); nodes[0].wait(timeout=5)
            nodes[0], ports[0] = start(0)
            status, restored = request(ports[0], '/status')
            assert status == 200 and restored['hash'] == digest('block', block)
            assert restored['validator'] == validators[0]
            insufficient = False
            try: verify_certificate(spec, block, votes[:2])
            except ValueError: insufficient = True
            assert insufficient
            return {'validator_processes_started': 4, 'available_to_finalize': 3,
                    'offline_validators_tolerated_in_demo': 1, 'quorum': '3-of-4',
                    'matching_finalized_heads': 3, 'height': 1,
                    'unauthorized_request_rejected': True, 'conflicting_vote_rejected': True,
                    'two_votes_rejected': True, 'restart_head_and_identity_preserved': True,
                    'transport': 'authenticated HTTP on loopback', 'independent_hosts': False,
                    'production_certified': False}
        finally:
            for proc in processes:
                if proc.poll() is None: proc.terminate()
            for proc in processes:
                try: proc.wait(timeout=5)
                except subprocess.TimeoutExpired: proc.kill(); proc.wait()


if __name__ == '__main__': print(json.dumps(run(), indent=2))
