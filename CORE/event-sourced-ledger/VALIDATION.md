# Ledger Validation Contract

## Purpose

This document defines the verification boundary for the DeepCore reference event-sourced ledger.

## Validation order

Persisted history must pass these gates in order:

1. **Parse:** every non-empty JSONL line must decode to an object.
2. **Structural integrity:** each record must link to the preceding record and its SHA-256 content commitment must match.
3. **Domain invariants:** the reducer-domain event schema must be valid. The reference domain currently permits `CREDIT` and `DEBIT` events with non-negative integer `amount` values.
4. **Reduction:** only validated history may be converted into `LedgerState`.

A failure at any earlier gate prevents later processing.

## API contract

`EventSourcedLedger.replay()` always performs structural verification. It accepts an optional validator for domain-specific invariants.

`reduce_ledger()` supplies `verify_invariants` as that validator. This keeps the base ledger reusable while making the reducer path fail closed on invalid domain history.

## Security properties

- Ledger-managed `hash` and `previous_hash` fields cannot be supplied by callers during append.
- Invalid JSON cannot be replayed.
- Broken hash linkage cannot be replayed.
- Hash tampering cannot be replayed.
- Unsupported reducer events cannot reach state reconstruction through `reduce_ledger()`.
- Validation occurs before deterministic reduction.

## Scope

This is a reference implementation and validation contract. It is not a claim of production readiness, distributed consensus, crash-safe multi-writer semantics, hardware-backed key custody, or external financial settlement.
