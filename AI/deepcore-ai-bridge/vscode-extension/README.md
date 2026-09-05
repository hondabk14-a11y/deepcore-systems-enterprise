# DeepCore AI Bridge for VS Code

Read-only VS Code integration for the DeepCore AI Bridge.

## Development

1. Open this repository in VS Code.
2. Open `AI/deepcore-ai-bridge/vscode-extension`.
3. Press `F5` to launch an Extension Development Host.
4. Open a source file in the DeepCore repository.
5. Use the editor context menu or Command Palette and run **DeepCore: Review Current File with OpenAI**.

The extension launches the repository bridge in a terminal. It does not write files or commit changes.

## Security

- Keep `OPENAI_API_KEY` in the local `.env` used by the bridge.
- Never commit API keys, private keys, wallet seeds, certificates, or other credentials.
- Treat AI output as advisory review material.
- Ledger authority, cryptographic verification, consensus safety, authorization, and production release decisions remain outside the AI bridge.
