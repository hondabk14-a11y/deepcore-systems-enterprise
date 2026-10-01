# BKILLINGS Binance MCP bridge

Install the tested MCP SDK version: `python -m pip install mcp==1.30.0`.
Set BKILLINGS_BINANCE_JOURNAL to an absolute, private, persistent journal path.
Run from the repository root: `python -m CORE.binance_mcp`.

This is an implemented local stdio MCP server. It exposes:
- binance_quote: read public spot bid/ask data without journal storage.
- record_binance_observation: acquire and persist one external observation.
- verify_binance_replay: verify and reconstruct the observation journal.

The recording tool is declared as a write operation. No signing keys, balances,
orders, custody, or consensus controls are exposed. Journal paths are server
configuration, never model-controlled tool arguments. HTTP failures propagate.

Verified locally using MCP SDK tool discovery and invocation with fixture data,
plus the existing observer tests. Remote transport and live Binance access are
not verified.

Connection status: NOT CONNECTED TO CHATGPT.
The Hugging Face target BKillings/deepcore-systems-enterprise returned not found
or authentication required; connected HF OAuth lacks repository write scope.
GitHub PR #30 contains an unmerged HTTP reference service, not this MCP bridge.

ChatGPT requires a reachable remote MCP endpoint for a hosted connection.
Before exposing this personal journal remotely, add a reviewed OAuth gateway,
configure durable storage, verify the private Space, and prove initialize,
tools/list, and tools/call through the deployed transport. Stdio is intentionally
the only enabled transport in this change; do not expose it by disabling auth.
No automatic registration or deployment is claimed.

Official connection guide:
https://developers.openai.com/plugins/deploy/connect-chatgpt
