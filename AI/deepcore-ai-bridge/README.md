# DeepCore AI Bridge

A local VS Code/terminal bridge for sending selected DeepCore source files to an AI backend for read-only engineering review.

## Local setup

```bash
cd AI/deepcore-ai-bridge
npm install
cp .env.example .env
```

For OpenAI review, set `OPENAI_API_KEY` in the local `.env` file. Never commit `.env` or API keys.

## OpenAI review

```bash
npm run review -- ../../CORE/event-sourced-ledger/ledger.py
```

The bridge reads the file and asks the model for security, correctness, determinism, failure-handling, and test-review findings. It does not modify repository files.

## Local vLLM preflight

The bridge can also target an OpenAI-compatible local vLLM server. Configure `.env` like this:

```dotenv
DEEPCORE_AI_BASE_URL=http://127.0.0.1:8000/v1
DEEPCORE_AI_MODEL=deepseek-ai/DeepSeek-V4-Flash
```

Start the local server separately, then run:

```bash
npm run local:health
```

The preflight checks the `/v1/models` contract, verifies the expected model is advertised, sends a minimal deterministic chat-completion probe, and validates the response shape. It prints only pass/fail metadata and never dumps the model response or credentials.

The corresponding offline contract tests are:

```bash
npm run local:test
```

These tests use Node's built-in test runner and do not require a running model server.

## VS Code

Use GitHub Copilot for interactive editor assistance. Use this bridge when an independent, read-only AI review is useful before committing or opening a pull request.

## Security boundary

The bridge and local inference backend must remain advisory. They must not bypass repository controls, alter ledger authority, handle private keys, or weaken authentication, authorization, signature verification, replay protection, consensus safety, or invariants.

Local inference readiness is an engineering preflight, not production certification. A passing local check does not establish production availability, security, key custody, backup/restore, rollback, observability, or independent review.
