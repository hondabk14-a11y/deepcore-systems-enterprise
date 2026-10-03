import asyncio
import tempfile
import unittest
from pathlib import Path
from CORE.binance_mcp import create_bridge
from CORE.binance_observer import normalize


class BridgeTests(unittest.TestCase):
    def test_tool_contract_and_round_trip(self):
        event = normalize({"symbol": "BTCUSDT", "bidPrice": "1", "askPrice": "2",
                           "bidQty": "3", "askQty": "4"}, "BTCUSDT", 123)
        with tempfile.TemporaryDirectory() as directory:
            server = create_bridge(str(Path(directory) / "journal.sqlite"),
                                   fetcher=lambda symbol: event)
            async def exercise():
                tools = {tool.name: tool for tool in await server.list_tools()}
                self.assertEqual(set(tools), {"binance_quote", "record_binance_observation",
                                             "verify_binance_replay"})
                self.assertTrue(tools["binance_quote"].annotations.readOnlyHint)
                self.assertFalse(tools["record_binance_observation"].annotations.readOnlyHint)
                self.assertTrue(tools["verify_binance_replay"].annotations.readOnlyHint)
                quote = await server.call_tool("binance_quote", {"symbol": "BTCUSDT"})
                self.assertIn("BTCUSDT", str(quote))
                record = await server.call_tool("record_binance_observation", {"symbol": "BTCUSDT"})
                self.assertIn("head_hash", str(record))
                replay = await server.call_tool("verify_binance_replay", {})
                self.assertIn("state_root", str(replay))
            asyncio.run(exercise())

    def test_rejects_relative_storage_path(self):
        with self.assertRaises(ValueError):
            create_bridge("relative.sqlite")


if __name__ == "__main__":
    unittest.main()
