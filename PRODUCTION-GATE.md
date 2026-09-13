# DeepCore Production Gate

The production gate is an automated minimum release barrier. A passing gate does not by itself certify the entire distributed system for production; it proves only the checks implemented by the workflow have passed.

## Required checks

- Event-sourced ledger unit tests
- Python source compilation
- Repository hygiene files present
- No tracked `.env`, private-key, certificate-keystore, secrets, credentials, or wallet paths

## AI dependency boundary

OpenAI, other model providers, and AI APIs are not required for **DeepCore Core Production Certification** unless a release explicitly declares an AI provider as a mandatory runtime dependency.

The authoritative DeepCore core must remain safe and operational when the AI subsystem or external model provider is unavailable. AI output is untrusted input and must not bypass cryptographic verification, ledger invariants, authentication, authorization, consensus safety, policy enforcement, or key custody.

If an AI subsystem is included in a production release, its provider integration receives a separate production gate covering authentication, secret handling, timeouts, retries, rate limits, provider failure, degraded-mode behavior, output validation, observability, and recovery. An AI-provider outage must not be treated as proof that the authoritative DeepCore core is unavailable unless the release explicitly declares that dependency.

## Release rule

A production deployment must not be represented as verified unless the applicable production-gate workflow run is successful and the deployment environment has independently completed its operational, security, key-custody, observability, backup/recovery, and rollback validation.

## DeepCore safety boundary

AI agents may propose and test changes. They do not receive authority to bypass cryptographic verification, ledger invariants, authentication, authorization, consensus safety, or key custody.
