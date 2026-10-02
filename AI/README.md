# AI Integration

DeepCore AI integration includes OpenAI API/Responses API usage, an Agents SDK Launch Desk concept, evaluation interfaces, and controlled AI-assisted orchestration.

The project has referenced an OpenAPI v3.0.3 interface with:

- `/v1/chat/completions`
- `/v1/embeddings`
- `/v1/eval/run`

AI components must remain bounded by DeepCore authorization, invariant, audit, and secret-management controls.

## Hugging Face datasets

The [dataset integration](datasets/README.md) imports pinned financial-news
training and validation data into a separate SQLite observation store for
advisory AI evaluation. It does not grant ledger or transaction authority.
