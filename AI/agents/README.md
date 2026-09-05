# DeepCore Agents

This directory defines the agent architecture used to connect AI capabilities with DeepCore services without granting models unrestricted authority.

## Controls

- Explicit tool permissions.
- Authentication and authorization at service boundaries.
- Input/output validation.
- Event-sourced audit trails for material actions.
- Deterministic policy and invariant checks before state changes.
- Timeouts, retries, rate limits, and circuit-breaking for external services.
- Human or policy approval gates for sensitive operations.

Agents should be treated as adaptive decision-support components. They do not become ledger, cryptographic, treasury, or consensus authorities merely because an agent can call a tool.