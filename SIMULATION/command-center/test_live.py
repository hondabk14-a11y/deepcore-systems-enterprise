"""Offline tests for schema contract, server isolation, and read-only proxy behavior."""
import json
import os
import threading
import unittest
from datetime import datetime, timezone
from functools import partial
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import patch
from urllib import error, request

from telemetry_server import Handler, TelemetryError, load_upstream, validate_snapshot


def snapshot():
    t = datetime.now(timezone.utc).isoformat()
    return {'timestamp': t,
            'metrics': {'totalNodes': 1, 'valueLockedUsd': 123, 'healthPercent': 96,
                        'energyPw': 0.5, 'riskIndex': .18, 'blockHeight': 1234,
                        'flow24hUsd': 120, 'threats': 0},
            'nodes': [{'id': 'N-001', 'role': 'CORE', 'x': 500, 'y': 200,
                       'health': 96, 'risk': .18, 'energy': .9}],
            'flows': [], 'events': [{'id': 'evt-1', 'time': t, 'kind': 'CONSENSUS',
                                    'nodeId': 'N-001', 'message': 'Sample event'}],
            'consensus': {'round': 100, 'status': 'COMMITTED', 'progress': 100},
            'liquidity': [{'name': 'Pools', 'share': 100}],
            'distribution': [{'name': 'DeFi', 'share': 100}]}


class FixtureServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.server.request_path = self.path
        if self.path == '/redirect':
            self.send_response(302)
            self.send_header('Location', '/snapshot')
            self.end_headers()
            return
        body = json.dumps(snapshot()).encode('utf8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)
    def log_message(self, *_):
        pass


class SilentHandler(Handler):
    def log_message(self, *_):
        pass


class TestTelemetry(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = ThreadingHTTPServer(('127.0.0.1', 0), FixtureServer)
        cls.site = ThreadingHTTPServer(('127.0.0.1', 0), partial(SilentHandler,
            directory=os.path.dirname(__file__)))
        cls.threads = [threading.Thread(target=s.serve_forever, daemon=True)
                       for s in (cls.fixture, cls.site)]
        for th in cls.threads:
            th.start()
        cls.upstream = f'http://127.0.0.1:{cls.fixture.server_port}'
        cls.base = f'http://127.0.0.1:{cls.site.server_port}'

    @classmethod
    def tearDownClass(cls):
        for s in (cls.fixture, cls.site):
            s.shutdown()
            s.server_close()

    def test_accepts_valid_snapshot(self):
        self.assertEqual(validate_snapshot(snapshot())['nodes'][0]['id'], 'N-001')

    def test_rejects_missing_authoritative_metric(self):
        value = snapshot()
        del value['metrics']['riskIndex']
        with self.assertRaises(TelemetryError):
            validate_snapshot(value)

    def test_rejects_nonfinite_and_bool_fields(self):
        for invalid in (True, float('nan'), float('inf'), -1, 103):
            value = snapshot()
            value['metrics']['healthPercent'] = invalid
            with self.subTest(invalid=invalid), self.assertRaises(TelemetryError):
                validate_snapshot(value)

    def test_rejects_unknown_flow_node_and_duplicate_ids(self):
        value = snapshot()
        value['flows'] = [{'source': 'N-001', 'target': 'N-999', 'intensity': .5}]
        with self.assertRaises(TelemetryError):
            validate_snapshot(value)
        value = snapshot()
        value['nodes'].append(value['nodes'][0])
        with self.assertRaises(TelemetryError):
            validate_snapshot(value)

    def test_rejects_untrusted_node_ids(self):
        value = snapshot()
        value['nodes'][0]['id'] = '<script>alert(1)</script>'
        with self.assertRaises(TelemetryError):
            validate_snapshot(value)

    def test_rejects_oversized_lists(self):
        value = snapshot()
        value['nodes'] *= 151
        with self.assertRaises(TelemetryError):
            validate_snapshot(value)

    def test_no_upstream_returns_explicit_503(self):
        with patch.dict(os.environ, {'DEEPCORE_TELEMETRY_URL': ''}):
            with self.assertRaises(error.HTTPError) as caught:
                request.urlopen(self.base + '/api/telemetry')
        self.assertEqual(caught.exception.code, 503)

    def test_authenticated_upstream_get_and_headers(self):
        with patch.dict(os.environ, {'DEEPCORE_TELEMETRY_URL': self.upstream + '/snapshot',
                                     'DEEPCORE_UPSTREAM_TOKEN': 'a-secret-token'}):
            with request.urlopen(self.base + '/api/telemetry') as response:
                self.assertEqual(response.status, 200)
                self.assertEqual(response.headers.get('Cache-Control'), 'no-store')
                self.assertIn("connect-src 'self'", response.headers['Content-Security-Policy'])
                payload = json.load(response)
                self.assertEqual(payload['consensus']['round'], 100)
                self.assertNotIn('a-secret-token', json.dumps(payload))

    def test_redirect_rejected(self):
        with patch.dict(os.environ, {'DEEPCORE_TELEMETRY_URL': self.upstream + '/redirect'}):
            with self.assertRaises(TelemetryError):
                load_upstream()

    def test_public_host_not_configurable(self):
        with request.urlopen(self.base + '/live.html') as response:
            self.assertEqual(response.status, 200)
            self.assertIn(b'DEEPCORE', response.read())


if __name__ == '__main__':
    unittest.main()