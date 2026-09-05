# Liquid Integration

DeepCore's Liquid track is intended for integration with the Liquid network and its asset/settlement capabilities.

## Baseline

- Treat Liquid state as an external network state source.
- Keep Liquid events distinct from Bitcoin L1 events.
- Preserve deterministic event recording and replayability.
- Integrate settlement observations with treasury reconciliation where appropriate.
- Keep wallet seeds, signing keys, credentials, and other secrets out of the repository.

Production integration requires explicit asset-identity handling, transaction validation, confirmation policy, recovery behavior, and network-specific security review.