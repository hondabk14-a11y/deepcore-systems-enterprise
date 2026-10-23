import io
import json
import tempfile
import unittest
from email.message import Message
from pathlib import Path
from types import SimpleNamespace

from CORE.binance_observer import normalize
from SIMULATION.local_server import Handler, SimulationStore, simulate


class SimulationTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.store = SimulationStore(Path(self.directory.name))

    def tearDown(self):
        self.store.close()
        self.directory.cleanup()

    def test_reproducible_verified_blocks(self):
        first = simulate({"steps": 3, "seed": "fixture"})
        self.assertEqual(first, simulate({"steps": 3, "seed": "fixture"}))
        self.assertEqual(first["block_height"], 3)
        self.assertTrue(first["replay_verified"] and first["quorum_verified"])
        self.assertEqual(sum(account["balance"] for account in first["state"].values()), 4_000_000 - 3)
        self.assertNotEqual(first["block_hash"], simulate({"steps": 3, "seed": "other"})["block_hash"])

    def test_restart_and_idempotency(self):
        original, created = self.store.run({"steps": 2}, "restart-test")
        self.assertTrue(created)
        self.store.close()
        self.store = SimulationStore(Path(self.directory.name))
        duplicate, created = self.store.run({"steps": 2}, "restart-test")
        self.assertFalse(created)
        self.assertEqual(original, duplicate)
        self.assertEqual(len(self.store.recent()), 1)
        with self.assertRaises(ValueError):
            self.store.run({"steps": 3}, "restart-test")

    def test_invalid_inputs_do_not_persist(self):
        for value in [{"steps": True}, {"steps": 0}, {"steps": 101}, {"seed": ""}, {"extra": 1}, []]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.store.run(value)
        self.assertEqual(self.store.recent(), [])

    def test_stored_tampering_is_rejected(self):
        self.store.run({}, "tamper")
        self.store.db.execute("UPDATE runs SET result='{}' WHERE id='tamper'")
        self.store.db.commit()
        with self.assertRaises(ValueError):
            self.store.get("tamper")

    def test_market_is_observational_and_durable(self):
        quote = {"symbol": "BTCUSDT", "bidPrice": "100.00", "bidQty": "1", "askPrice": "101.00", "askQty": "2"}
        event = normalize(quote, "BTCUSDT", 1)
        self.assertTrue(self.store.market.append(event))
        self.assertFalse(self.store.market.append(event))
        self.assertEqual(self.store.recent(), [])
        self.store.close()
        self.store = SimulationStore(Path(self.directory.name))
        observation = self.store.market_status()["observations"][0]
        self.assertEqual(observation["trust"], "external_untrusted")
        self.assertTrue(observation["stale"])

    def request(self, body, **headers):
        handler = Handler.__new__(Handler)
        handler.server = SimpleNamespace(server_port=8000, token="test-token", store=self.store)
        handler.path = "/api/simulations"
        handler.headers = Message()
        default = {"Host": "localhost:8000", "Content-Type": "application/json", "Content-Length": str(len(body)), "Authorization": "Bearer test-token"}
        for key, value in (default | headers).items():
            handler.headers[key] = value
        handler.rfile = io.BytesIO(body)
        result = []
        handler.respond = lambda status, value, *args: result.append((status, value))
        handler.do_POST()
        return result[0]

    def test_authenticated_route(self):
        status, result = self.request(b'{"steps":2}')
        self.assertEqual(status, 201)
        self.assertEqual(result["block_height"], 2)

    def test_unauthorized_and_cross_origin_rejected(self):
        self.assertEqual(self.request(b'{}', Authorization="Bearer wrong")[0], 401)
        self.assertEqual(self.request(b'{}', Authorization="Bearer \u00e9")[0], 401)
        self.assertEqual(self.request(b'{}', Origin="http://untrusted.example")[0], 403)
        self.assertEqual(self.request(b'{}', Host="untrusted.example")[0], 403)
        self.assertEqual(self.store.recent(), [])

    def test_malformed_and_large_bodies_rejected(self):
        self.assertEqual(self.request(b'not-json')[0], 400)
        self.assertEqual(self.request(b'{}', **{"Content-Length": "9000"})[0], 413)
        self.assertEqual(self.request(b'{}', **{"Content-Type": "text/plain"})[0], 415)
        self.assertEqual(self.store.recent(), [])


if __name__ == "__main__":
    unittest.main()
