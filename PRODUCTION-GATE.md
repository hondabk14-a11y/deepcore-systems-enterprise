# DeepCore Production Gate

The production gate is an automated minimum release barrier. A passing gate does not by itself certify the entire distributed system for production; it proves only the checks implemented by the workflow have passed.

## Required checks

- Event-sourced ledger unit tests
- Python source compilation
- Repository hygiene files present
- No tracked `.env`, private-key, certificate-keystore, secrets, credentials, or wallet paths

## Release rule

A production deployment must not be represented as verified unless the applicable production-gate workflow run is successful and the deployment environment has independently completed its operational, security, key-custody, observability, backup/recovery, and rollback validation.

## DeepCore safety boundary

AI agents may propose and test changes. They do not receive authority to bypass cryptographic verification, ledger invariants, authentication, authorization, consensus safety, or key custody.
