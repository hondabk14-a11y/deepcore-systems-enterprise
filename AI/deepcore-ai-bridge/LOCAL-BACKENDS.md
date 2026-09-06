# DeepCore Local AI Backends

DeepCore supports OpenAI-compatible local inference as an advisory AI capability. The inference backend is not a ledger authority and must not receive private keys, wallet seeds, signing material, or authorization to mutate authoritative state.

## Supported local endpoints

| Backend | Example endpoint | Model |
|---|---|---|
| vLLM | `http://127.0.0.1:8000/v1` | `deepseek-ai/DeepSeek-V4-Flash` |
| SGLang | `http://127.0.0.1:30000/v1` | `deepseek-ai/DeepSeek-V4-Flash` |

Both are treated as OpenAI-compatible HTTP backends by the bridge.

## vLLM

```bash
vllm serve "deepseek-ai/DeepSeek-V4-Flash" --host 127.0.0.1 --port 8000
```

Then configure:

```dotenv
DEEPCORE_AI_BASE_URL=http://127.0.0.1:8000/v1
DEEPCORE_AI_MODEL=deepseek-ai/DeepSeek-V4-Flash
```

## SGLang

```bash
python3 -m sglang.launch_server \
  --model-path "deepseek-ai/DeepSeek-V4-Flash" \
  --host 127.0.0.1 \
  --port 30000
```

Then configure:

```dotenv
DEEPCORE_AI_BASE_URL=http://127.0.0.1:30000/v1
DEEPCORE_AI_MODEL=deepseek-ai/DeepSeek-V4-Flash
```

## Preflight

From `AI/deepcore-ai-bridge`:

```bash
npm run local:test
npm run local:health
```

`local:test` is offline and does not require a model server. `local:health` requires the configured backend to be running and validates model advertisement plus a minimal completion response.

## Security boundary

Bind local services to `127.0.0.1` unless a controlled network exposure is explicitly required. If a service must listen on `0.0.0.0`, place authentication, network policy, TLS, and access controls in front of it.

A successful local preflight is evidence that an endpoint responded correctly at test time. It is not evidence of production availability, security certification, key custody, backup/restore, rollback, observability, or independent review.
