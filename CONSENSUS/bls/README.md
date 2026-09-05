# BLS Signatures

DeepCore's consensus design includes BLS signatures for compact quorum authentication and aggregation.

## Baseline

- BLS signatures are intended for quorum-certificate construction and verification.
- The reference implementation target is `blst`.
- Key generation, custody, rotation, and validation remain separate security concerns.
- Aggregated signatures must be checked against the correct participant set and consensus context.
- Domain separation and message/context binding are required to prevent cross-protocol misuse.

## Validation requirements

Before production use, test serialization, subgroup checks, malformed inputs, aggregation behavior, key rotation, fault cases, interoperability, and performance. Cryptographic libraries and parameters must be pinned and reviewed rather than assumed safe because a package exists.