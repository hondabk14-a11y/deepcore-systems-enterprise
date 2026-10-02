"""Loopback-only authenticated validator harness. Not an internet-facing server."""
import argparse
import hmac
import json
import os
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from key_store import load_key
from protocol import MAX_BYTES, canonical, public
from storage import Ledger


def serve(config, passphrase):
    spec = json.loads(Path(config['spec']).read_text())
    key = load_key(config['key'], passphrase)
    if public(key) not in spec['validators']: raise ValueError('Signer outside committee')
    token = Path(config['token']).read_text().strip()
    if len(token) < 32: raise ValueError('Bearer token too short')
    ledger = Ledger(config['database'], spec)

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args): pass
        def setup(self):
            super().setup()
            self.connection.settimeout(5)
        def respond(self, code, body):
            data = canonical(body)
            self.send_response(code)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Cache-Control', 'no-store')
            self.send_header('Content-Length', str(len(data)))
            self.end_headers(); self.wfile.write(data)
        def authorized(self):
            if not hmac.compare_digest(self.headers.get('Authorization', '').encode(), ('Bearer '+token).encode()):
                self.respond(401, {'error': 'unauthorized'}); return False
            return True
        def do_GET(self):
            if not self.authorized(): return
            if self.path not in ('/readyz', '/status'):
                self.respond(404, {'error': 'not found'}); return
            try:
                snapshot = ledger.snapshot()
                self.respond(200, {'ready': True, 'height': snapshot['height'], 'hash': snapshot['hash'],
                                  'validator': public(key), 'production_certified': False})
            except Exception:
                self.respond(503, {'ready': False})
        def do_POST(self):
            if not self.authorized(): return
            if self.path not in ('/vote', '/commit'):
                self.respond(404, {'error': 'not found'}); return
            try:
                if self.headers.get('Transfer-Encoding'):
                    self.respond(400, {'error': 'chunked input unsupported'}); return
                length = int(self.headers.get('Content-Length', '0'))
                if not 0 < length <= MAX_BYTES:
                    self.respond(413, {'error': 'body size'}); return
                raw = self.rfile.read(length)
                if len(raw) != length: raise ValueError('Incomplete body')
                def unique(pairs):
                    out = {}
                    for k,v in pairs:
                        if k in out: raise ValueError('Duplicate JSON key')
                        out[k] = v
                    return out
                data = json.loads(raw, object_pairs_hook=unique)
                if self.path == '/vote':
                    result = ledger.vote(key, data, int(time.time()))
                else:
                    if type(data) is not dict or set(data) != {'block','votes'}: raise ValueError('Commit fields')
                    ledger.commit(data['block'], data['votes'])
                    result = {'committed': True}
                self.respond(200, result)
            except (ValueError, KeyError, TypeError, RecursionError):
                self.respond(400, {'error': 'invalid request or ledger operation'})
            except Exception:
                self.respond(503, {'error': 'operation unavailable'})

    server = HTTPServer(('127.0.0.1', config['port']), Handler)
    print(json.dumps({'port': server.server_port, 'pid': os.getpid()}), flush=True)
    try: server.serve_forever()
    finally: server.server_close(); ledger.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', required=True)
    args = parser.parse_args()
    # In production replace this harness with a separately reviewed signer boundary.
    import sys
    password = sys.stdin.buffer.readline(4096).rstrip(b'\n')
    serve(json.loads(Path(args.config).read_text()), password)
