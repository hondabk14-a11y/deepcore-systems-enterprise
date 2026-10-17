---
title: DeepCore CMC Advisory Agent
emoji: 🛡️
colorFrom: blue
colorTo: gray
sdk: gradio
app_file: app.py
pinned: false
---

# DeepCore CMC Advisory Agent

This folder is the deployable root of a **private** Hugging Face Gradio Space.
The agent is **advisory only**. It cannot trade, sign, change a ledger, access
private keys, or send unapproved tool instructions.

## What it does

1. Opens an HTTPS Streamable HTTP MCP connection to CMC Skill Hub.
2. Calls find_skill(query="btc_cross_asset_correlation") exactly once.
3. Reads the *actual* skill_description, unique_name and input_schema.
4. Validates {"preview": true} against the returned skill schema.
5. Validates the intended execute_skill invocation against MCP tool schema.
6. Calls execute_skill with {"unique_name": ..., "parameters":{"preview":true}}
   exactly once. On any error it stops, without fabricating inputs or retrying.
7. Optionally sends the resulting market data to an OpenAI model for a read-only
   summary; source content is treated as untrusted data, not instructions.

No CMC or OpenAI credentials belong in repository files or chat transcripts.

## Hugging Face deployment

1. Use https://huggingface.co/new-space while signed into BKillings and create
   a **private** Gradio Space. Keep the existing DeepCore GitHub repo private.
2. Upload only files from this folder to the **root of the Space** (README.md,
   app.py, agent.py, requirements.txt). Do not upload the wider repository.
3. In Space **Settings -> Variables and secrets -> Secrets** add:
   - DEEPCORE_OPERATOR_PASSWORD: new strong unique password, required to start.
   - CMC_MCP_API_KEY: **rotated** CoinMarketCap key. Never reuse the key exposed
     in an earlier chat message.
   - OPENAI_API_KEY: scoped OpenAI project key, optional until model summaries.
4. Set OPENAI_MODEL to a model enabled on your project under Space **Variables**
   if you want model summaries. Optionally set DEEPCORE_OPERATOR_USER.
5. Start the Space, authenticate using operator account, inspect connection
   readiness and trigger CMC preview. Confirm no required CMC arguments were
   missing; do not interpret a blocked result as successful execution.

If your Hugging Face plan or billing does not allow a Gradio Space, deployment
is BLOCKED. Do not switch to a public static Space; secrets and paid model APIs
must remain server-side. Hugging Face Jobs are a bounded alternative *only*
when billing and encrypted job-secret provisioning are in place.

## Offline validation

Install requirements and run Python's unittest tests/test_agent.py. The tests
simulate MCP behavior and do NOT verify live CMC access or production readiness.

- python -m unittest discover -s tests -v
- python agent.py --health (shows secret presence but never values)
- python agent.py (live CMC preview, only after secrets)
- python agent.py --summarize (optional model analysis)

## Operations and trust

Do not merge or deploy without CI results, secret setup and a human review.
The MCP server is fixed to https://mcp.coinmarketcap.com/skill-hub/stream.
Secrets are sent only to their respective service. Unexpected errors fail closed
and key-bearing SDK errors are not printed to public UI or stdout.
The model may recommend, but it does not obtain ledger, wallet or payment tools.
