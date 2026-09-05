# DeepCore U.S. Treasury Settlement Node

## Scope

`UST-0001` is the DeepCore reference/simulation node representing a U.S.-Treasury-style settlement authority inside the project's distributed-ledger model. It is **not** the U.S. Department of the Treasury and does not imply government affiliation, authorization, custody, or access to government systems.

## Node profile

| Field | Value |
|---|---|
| Node ID | `0001` |
| Logical name | `UST-0001` |
| Role | Root Ledger Authority (reference model) |
| Consensus weight | 35% |
| Trust baseline | 1.00 |
| Settlement domain | Treasury reference settlement |

## Control boundaries

```text
Settlement Event
      |
      v
SSIL Integrity / Risk Evaluation
      |
      +---- FAIL_CLOSED ----> Reject
      |
      +---- REVIEW/DEFER ---> Hold for policy decision
      |
      +---- ALLOW ----------> Consensus validation
                                   |
                                   v
                            Treasury Ledger
                                   |
                                   v
                              Reconciliation
```

## Settlement lifecycle

`TX_EVENT_STREAM -> TX_CREATED -> TX_VALIDATION_PASSED -> TX_BROADCAST_ATTEMPTED -> TX_MEMPOOL_ACCEPTED -> TX_CONFIRMED`

## Security requirements

- Cryptographic identity and authenticated transport are prerequisites for consensus participation.
- SSIL may block unsafe operations but does not rewrite authoritative ledger history.
- Consensus quorum remains independent from SSIL risk scoring.
- Settlement state must be reconstructable from deterministic events.
- Persistent state must pass integrity and rollback checks after restart.
- Private keys, wallet seeds, credentials, and other secrets are never stored in this reference module.
- External government integration must be separately authorized and independently verified.

## Status

Reference architecture only. This module documents DeepCore's simulated treasury-settlement role and its security boundaries. It is not a production government settlement system.
