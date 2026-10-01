import copy
import tempfile
import unittest
from unittest.mock import patch
from CORE.binance_observer import normalize, ObservationJournal, fetch_quote


class BinanceTests(unittest.TestCase):
    def setUp(self):
        self.payload = {"symbol": "BTCUSDT", "bidPrice": "85000.01",
                        "askPrice": "85000.02", "bidQty": "1.00", "askQty": "2.00"}
        self.event = normalize(self.payload, "BTCUSDT", 123456)
        self.directory = tempfile.TemporaryDirectory()
        self.path = self.directory.name + "/journal.sqlite"
        self.journal = ObservationJournal(self.path)

    def tearDown(self):
        self.journal.close()
        self.directory.cleanup()

    def test_restart_and_dedup(self):
        self.assertTrue(self.journal.append(self.event))
        before = self.journal.replay()
        self.journal.close()
        self.journal = ObservationJournal(self.path)
        self.assertFalse(self.journal.append(copy.deepcopy(self.event)))
        self.assertEqual(before, self.journal.replay())

    def test_tampering(self):
        self.journal.append(self.event)
        altered = copy.deepcopy(self.event)
        altered["quote"]["bidPrice"] = "1"
        import json
        self.journal.db.execute("UPDATE binance_observations SET body=?", (json.dumps(altered),))
        with self.assertRaises(ValueError):
            self.journal.replay()

    def test_invalid_quotes(self):
        for key, value in [("bidPrice", "NaN"), ("askPrice", "0"),
                           ("bidQty", "-1"), ("bidPrice", 1.2),
                           ("symbol", "ETHUSDT"), ("bidPrice", "99999")]:
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                normalize({**self.payload, key: value}, "BTCUSDT", 1)

    def test_invalid_symbol_never_requests(self):
        with patch("CORE.binance_observer.urlopen") as request:
            with self.assertRaises(ValueError):
                fetch_quote("BTCUSDT&secret=x")
            request.assert_not_called()

    def test_http_failure_does_not_append(self):
        with patch("CORE.binance_observer.urlopen", side_effect=OSError("unavailable")):
            with self.assertRaises(OSError):
                fetch_quote("BTCUSDT")
        self.assertEqual({}, self.journal.replay()["state"])

    def test_ordered_replay(self):
        self.journal.append(self.event)
        next_event = normalize({**self.payload, "bidQty": "3.0"}, "BTCUSDT", 123457)
        self.journal.append(next_event)
        self.assertEqual(next_event, self.journal.replay()["state"]["BTCUSDT"])
        self.journal.db.execute("DELETE FROM binance_observations WHERE seq=1")
        with self.assertRaises(ValueError):
            self.journal.replay()

    def test_schema_rejected_without_write(self):
        with self.assertRaises(ValueError):
            self.journal.append({**self.event, "trust": "authoritative"})
        self.assertEqual({}, self.journal.replay()["state"])


if __name__ == "__main__":
    unittest.main()
