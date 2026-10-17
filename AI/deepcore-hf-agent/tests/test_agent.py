"""No-network tests for DeepCore advisory CMC tool boundaries."""
import asyncio
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest

spec = importlib.util.spec_from_file_location("agent", Path(__file__).parents[1] / "agent.py")
agent = importlib.util.module_from_spec(spec)
spec.loader.exec_module(agent)

class Stub:
    def __init__(self, require_more=False, execution_error=False):
        self.calls = []
        self.require_more = require_more
        self.execution_error = execution_error

    async def list_tools(self):
        return SimpleNamespace(tools=[
            SimpleNamespace(name="find_skill", input_schema={"type":"object"}),
            SimpleNamespace(name="execute_skill", input_schema={
                "type":"object", "properties":{
                    "unique_name":{"type":"string"}, "parameters":{"type":"object"}},
                "required":["unique_name","parameters"], "additionalProperties":False})])

    async def call_tool(self, name, args):
        self.calls.append((name, args))
        if name == "find_skill":
            schema = {"type":"object", "properties":{"preview":{"type":"boolean"}},
                      "required":["preview"], "additionalProperties":False}
            if self.require_more:
                schema["properties"]["lookback_days"] = {"type":"integer"}
                schema["required"].append("lookback_days")
            return SimpleNamespace(is_error=False, structured_content={"skills":[{
                "unique_name":agent.SKILL,"skill_description":"fixture", "input_schema":schema}]})
        if self.execution_error:
            return SimpleNamespace(is_error=True, content=[SimpleNamespace(text="untrusted error")])
        return SimpleNamespace(is_error=False, structured_content={"correlation":0.0})

class PreviewTests(unittest.TestCase):
    def test_exact_discover_then_execute(self):
        client = Stub()
        result = asyncio.run(agent.execute_preview(client))
        self.assertEqual([n for n, _ in client.calls], ["find_skill", "execute_skill"])
        self.assertEqual(client.calls[0][1], {"query": agent.SKILL})
        self.assertEqual(client.calls[1][1], {
            "unique_name":agent.SKILL,"parameters":{"preview":True}})
        self.assertEqual(result["mode"], "preview-only")

    def test_missing_required_parameter_blocks_execution(self):
        client = Stub(require_more=True)
        with self.assertRaisesRegex(agent.AgentError, "lookback_days"):
            asyncio.run(agent.execute_preview(client))
        self.assertEqual(len(client.calls), 1)

    def test_non_preview_is_rejected_before_network(self):
        client = Stub()
        with self.assertRaisesRegex(agent.AgentError,"preview=true"):
            asyncio.run(agent.execute_preview(client, parameters={"preview":False}))
        self.assertFalse(client.calls)

    def test_wrong_skill_is_rejected(self):
        with self.assertRaisesRegex(agent.AgentError, "allowlisted"):
            asyncio.run(agent.execute_preview(Stub(), skill="wallet_transfer"))

    def test_server_error_not_retried(self):
        client = Stub(execution_error=True)
        with self.assertRaisesRegex(agent.AgentError, "tool error"):
            asyncio.run(agent.execute_preview(client))
        self.assertEqual(len(client.calls), 2)

    def test_missing_dynamic_schema_rejected(self):
        with self.assertRaisesRegex(agent.AgentError, "input_schema"):
            agent.find_exact({"skills":[{"unique_name":agent.SKILL}]}, agent.SKILL)

if __name__ == "__main__":
    unittest.main()
