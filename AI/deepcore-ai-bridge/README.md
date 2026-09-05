# DeepCore AI Bridge

A local VS Code/terminal bridge for sending selected DeepCore source files to the OpenAI API for read-only engineering review.

## Local setup

```bash
cd AI/deepcore-ai-bridge
npm install
cp .env.example .env
```

Set `OPENAI_API_KEY` in the local `.env` file. Never commit `.env` or API keys.

## Review a file

```bash
npm run review -- ../../CORE/event-sourced-ledger/ledger.py
```

The bridge reads the file and asks the model for security, correctness, determinism, failure-handling, and test-review findings. It does not modify repository files.

## VS Code

Use GitHub Copilot for interactive editor assistance. Use this bridge when an independent, read-only OpenAI review is useful before committing or opening a pull request.

## Security boundary

The bridge must remain advisory. It must not bypass repository controls, alter ledger authority, handle private keys, or weaken authentication, authorization, signature verification, replay protection, consensus safety, or invariants.
