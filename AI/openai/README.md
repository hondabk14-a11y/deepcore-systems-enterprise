# OpenAI Integration

DeepCore's AI layer can integrate OpenAI APIs for bounded intelligence, analysis, orchestration support, and evaluation.

## Baseline

- Responses API is the primary modern application interface referenced by the project.
- API credentials must be supplied through secure runtime configuration, never source control.
- AI outputs are untrusted inputs until validated by application policy and invariants.
- Authorization, audit logging, rate limits, and failure handling belong outside the model itself.
- Model identifiers must be treated as deploy-time configuration and verified against current platform availability.

## DeepCore boundary

AI may propose actions, classifications, plans, or analyses. Deterministic policy, authorization, cryptographic controls, and invariant enforcement remain the authority for state-changing operations.