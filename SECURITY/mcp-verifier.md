# MCP Verifier

Security service concept for verifying MCP-related messages and artifacts.

Baseline design references Ed25519 verification, an SSE endpoint, systemd service management, Nginx/TLS termination, and AWS deployment considerations.

Verification must fail closed on invalid signatures, malformed messages, missing trust context, or policy violations. Secrets and private signing material remain outside source control.