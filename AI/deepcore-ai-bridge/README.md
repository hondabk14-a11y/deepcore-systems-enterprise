# DeepCore AI Bridge

A local VS Code/terminal bridge for sending selected DeepCore source files to an AI backend for read-only engineering review.

## Local setup

```bash
cd AI/deepcore-ai-bridge
npm install
cp .env.example .env
```

Never commit `.env` or API keys.

## OpenAI review

Set `OPENAI_API_KEY` in the local `.env`, then:

```bash
npm run review -- ../../CORE/event-sourced-ledger/ledger.py
```

## Bounded advisory review

The review command uses the **JavaScript OpenAI SDK** and the Responses API. Keep provider credentials in the bridge's local environment, never in the VS Code extension, repository, browser, or request text. It accepts the official OpenAI endpoint, OpenRouter, or an HTTP(S) loopback model server. Arbitrary remote inference endpoints are rejected to avoid leaking the OpenAI API key to another host. For a loopback server requiring an auth token, set `DEEPCORE_LOCAL_AI_API_KEY`.

Reviews are non-persistent (`store: false`), have a 30-second timeout, disable automatic retries, and reject source files larger than 128 KiB. Files must reside inside this repository after symlink resolution. Paths conventionally used for secrets, credentials, wallet material, and key files are blocked. **Path screening is not a secret scanner:** inspect any source for embedded tokens or personal data before requesting a cloud review. The rate guard is six requests per 60 seconds **per adapter instance/process**; it does not impose a distributed or cross-CLI rate limit. A future publicly reachable HTTP service must separately authenticate callers and apply a centralized limiter.

Offline verification (no credential or network required):

```bash
npm run local:test
```

A successful offline test does not validate provider connectivity, authorization, access to the configured model, or deployment readiness.

## OpenRouter review

Set the credential only in the local environment:

```dotenv
OPENROUTER_API_KEY=
DEEPCORE_AI_BASE_URL=https://openrouter.ai/api/v1
DEEPCORE_AI_MODEL=openai/gpt-4o
```

Optional attribution headers can be configured with `OPENROUTER_HTTP_REFERER` and `OPENROUTER_X_TITLE`. The bridge selects `OPENROUTER_API_KEY` only when the configured endpoint is OpenRouter. It never prints or persists the credential.

```bash
npm run review -- ../../CORE/event-sourced-ledger/ledger.py
```

## Local vLLM or SGLang preflight

The bridge can target an OpenAI-compatible local inference server:

```dotenv
DEEPCORE_AI_BASE_URL=http://127.0.0.1:8000/v1
DEEPCORE_AI_MODEL=deepseek-ai/DeepSeek-V4-Flash
```

For SGLang, use `http://127.0.0.1:30000/v1` instead. Start the local server separately, then run:

```bash
npm run local:health
npm run local:test
```

The preflight checks the `/v1/models` contract, verifies the expected model is advertised, sends a minimal deterministic chat-completion probe, and validates the response shape. It prints only pass/fail metadata and never dumps the model response or credentials.

The offline contract tests do not require a running model server.

## Security boundary

The bridge and all AI backends remain advisory. They must not bypass repository controls, alter ledger authority, handle private keys, or weaken authentication, authorization, signature verification, replay protection, consensus safety, or invariants.

Local and external AI readiness checks are engineering preflights, not production certification. A passing AI check does not establish production availability, security, key custody, backup/restore, rollback, observability, or independent review.
