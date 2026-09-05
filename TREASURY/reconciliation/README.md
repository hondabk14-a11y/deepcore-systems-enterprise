# Treasury Reconciliation

The reconciliation engine compares DeepCore's event-sourced treasury state against external settlement and network observations.

## Responsibilities

- Compare expected and observed transaction states.
- Detect missing, duplicated, delayed, or conflicting observations.
- Produce deterministic reconciliation results where inputs are deterministic.
- Preserve discrepancies as auditable events rather than silently mutating balances.
- Support replay and investigation of historical reconciliation decisions.

## Control boundaries

Reconciliation is an observation and control mechanism. It does not grant authority to external data sources to rewrite the ledger. Material exceptions should require explicit policy handling and appropriate authorization.