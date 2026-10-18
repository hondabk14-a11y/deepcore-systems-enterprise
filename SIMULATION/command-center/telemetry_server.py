"""Local-only, read-only DeepCore dashboard proxy. No synthetic fallback."""
from __future__ import annotations

import argparse
import json
import os
from datetime import datetime
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib import error, parse, request

MAX_BODY = 512 * 1024
ROOT = Path(__file__).resolve().parent
REQUIRED = ('totalNodes', 'valueLockedUsd', 'healthPercent', 'energyPw', 'riskIndex',
            'blockHeight', 'flow24hUsd', 'threats')


class TelemetryError(ValueError):
    pass


def number(value, name, lo, hi):
    if isinstance(value, bool) or not isinstance(value, (float, int)) or not lo <= value <= hi:
        raise TelemetryError(f'Invalid numeric telemetry field: {name}')
    return value


def short(value, name, limit=150):
    if not isinstance(value, str) or len(value) > limit:
        raise TelemetryError(f'Invalid text telemetry field: {name}')
    return value


def timestamp(value):
    value = short(value, 'timestamp', 40)
    try:
        date = datetime.fromisoformat(value.replace('Z', '+00:00'))
        if date.tzinfo is None:
            raise ValueError('timezone required')
    except (ValueError, TypeError) as exc:
        raise TelemetryError('Timestamp must have a timezone') from exc
    return value


def validate_snapshot(payload):
    """Validate a strict, bounded snapshot; never synthesize missing measurements."""
    if not isinstance(payload, dict) or not isinstance(payload.get('metrics'), dict):
        raise TelemetryError('Expected metrics object')
    metrics = payload['metrics']
    for key in REQUIRED:
        if key not in metrics:
            raise TelemetryError(f'Missing metric: {key}')
    bounds = {'totalNodes': (0, 50_000_000), 'valueLockedUsd': (0, 1e20),
              'healthPercent': (0, 100), 'energyPw': (0, 1e12),
              'riskIndex': (0, 1), 'blockHeight': (0, 1e16),
              'flow24hUsd': (0, 1e20), 'threats': (0, 1e9)}
    clean_metrics = {k: number(metrics[k], k, *bounds[k]) for k in REQUIRED}
    nodes = payload.get('nodes')
    flows = payload.get('flows')
    events = payload.get('events')
    if not isinstance(nodes, list) or len(nodes) > 150:
        raise TelemetryError('Expected at most 150 nodes')
    if not isinstance(flows, list) or len(flows) > 500:
        raise TelemetryError('Expected at most 500 flows')
    if not isinstance(events, list) or len(events) > 100:
        raise TelemetryError('Expected at most 100 events')
    good_nodes = []
    for item in nodes:
        if not isinstance(item, dict):
            raise TelemetryError('Invalid node')
        ident = short(item.get('id'), 'node.id', 48)
        if not ident or not all(c.isalnum() or c in '-_' for c in ident):
            raise TelemetryError('Unsafe node ID')
        good_nodes.append({
            'id': ident, 'role': short(item.get('role'), 'node.role', 64),
            'x': number(item.get('x'), 'node.x', 0, 900),
            'y': number(item.get('y'), 'node.y', 0, 510),
            'health': number(item.get('health'), 'node.health', 0, 100),
            'risk': number(item.get('risk'), 'node.risk', 0, 1),
            'energy': number(item.get('energy'), 'node.energy', 0, 1),
        })
    identifiers = {n['id'] for n in good_nodes}
    if len(identifiers) != len(good_nodes):
        raise TelemetryError('Duplicate node IDs')
    good_flows = []
    for item in flows:
        if not isinstance(item, dict):
            raise TelemetryError('Invalid flow')
        source = short(item.get('source'), 'flow.source', 48)
        target = short(item.get('target'), 'flow.target', 48)
        if source not in identifiers or target not in identifiers:
            raise TelemetryError('Flow refers to an unknown node')
        good_flows.append({'source': source, 'target': target,
                           'intensity': number(item.get('intensity'), 'flow.intensity', 0, 1)})
    good_events = []
    for item in events:
        if not isinstance(item, dict):
            raise TelemetryError('Invalid event')
        kind = short(item.get('kind'), 'event.kind', 24).upper()
        if kind not in {'SETTLEMENT', 'CONSENSUS', 'RISK', 'LIQUIDITY', 'SECURITY', 'INFO'}:
            raise TelemetryError('Invalid event kind')
        good_events.append({'id': short(item.get('id'), 'event.id', 64),
                            'time': timestamp(item.get('time')),
                            'kind': kind,
                            'nodeId': short(item.get('nodeId', ''), 'event.nodeId', 48),
                            'message': short(item.get('message'), 'event.message', 500)})
    consensus = payload.get('consensus')
    if not isinstance(consensus, dict):
        raise TelemetryError('Expected consensus')
    clean_consensus = {'round': number(consensus.get('round'), 'round', 0, 1e16),
                       'status': short(consensus.get('status'), 'consensus.status', 40),
                       'progress': number(consensus.get('progress'), 'progress', 0, 100)}
    def shares(key):
        arr = payload.get(key)
        if not isinstance(arr, list) or len(arr) > 7:
            raise TelemetryError(f'Invalid {key}')
        if not all(isinstance(e, dict) for e in arr):
            raise TelemetryError(f'Invalid {key} entry')
        return [{'name': short(e.get('name'), key + '.name', 40),
                 'share': number(e.get('share'), key + '.share', 0, 100)}
                for e in arr]
    return {'timestamp': timestamp(payload.get('timestamp')),
            'metrics': clean_metrics, 'nodes': good_nodes, 'flows': good_flows,
            'events': good_events, 'consensus': clean_consensus,
            'liquidity': shares('liquidity'), 'distribution': shares('distribution')}


class NoRedirects(request.HTTPRedirectHandler):
    def redirect_request(self, *_):
        raise TelemetryError('Upstream redirects are disabled')


def load_upstream():
    url = os.environ.get('DEEPCORE_TELEMETRY_URL', '').strip()
    if not url:
        raise TelemetryError('Telemetry upstream not configured')
    parsed = parse.urlsplit(url)
    if parsed.scheme not in ('http', 'https') or not parsed.hostname or parsed.username or parsed.password or parsed.fragment:
        raise TelemetryError('Invalid telemetry upstream configuration')
    headers = {'Accept': 'application/json', 'User-Agent': 'DeepCoreReadOnlyDashboard/1.0'}
    token = os.environ.get('DEEPCORE_UPSTREAM_TOKEN', '')
    if token and parsed.scheme != 'https' and parsed.hostname not in ('localhost', '127.0.0.1', '::1'):
        raise TelemetryError('Bearer authentication requires HTTPS except on loopback')
    if token:
        if '\r' in token or '\n' in token:
            raise TelemetryError('Invalid upstream token')
        headers['Authorization'] = f'Bearer {token}'
    req = request.Request(url, headers=headers, method='GET')
    opener = request.build_opener(NoRedirects())
    try:
        with opener.open(req, timeout=5) as resp:
            if resp.status != 200 or resp.headers.get_content_type() != 'application/json':
                raise TelemetryError('Upstream must return JSON 200')
            body = resp.read(MAX_BODY + 1)
    except (error.URLError, OSError, TimeoutError) as exc:
        raise TelemetryError('Unable to retrieve upstream telemetry') from exc
    if len(body) > MAX_BODY:
        raise TelemetryError('Upstream response too large')
    try:
        return validate_snapshot(json.loads(body))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise TelemetryError('Invalid JSON from upstream') from exc


class Handler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Referrer-Policy', 'no-referrer')
        self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self' data:; object-src 'none'; base-uri 'none'; frame-ancestors 'none'")
        super().end_headers()

    def do_GET(self):
        if parse.urlsplit(self.path).path != '/api/telemetry':
            return super().do_GET()
        try:
            data = load_upstream()
        except TelemetryError:
            # Do not leak upstream hostnames, credentials, private payloads or stacktraces.
            self.send_error(503, 'Telemetry unavailable')
            return
        body = json.dumps(data, separators=(',', ':'), allow_nan=False).encode('utf8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main():
    parser = argparse.ArgumentParser(description='Loopback-only DeepCore telemetry dashboard')
    parser.add_argument('--port', type=int, default=4174)
    args = parser.parse_args()
    server = ThreadingHTTPServer(('127.0.0.1', args.port), partial(Handler, directory=str(ROOT)))
    print(f'DeepCore live operations: http://127.0.0.1:{server.server_port}/live.html', flush=True)
    print('Read-only upstream: ' + ('configured' if os.environ.get('DEEPCORE_TELEMETRY_URL') else 'not configured (demo only)'), flush=True)
    server.serve_forever()


if __name__ == '__main__':
    main()