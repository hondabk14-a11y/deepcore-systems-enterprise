# Checkpoint Freshness and Rollback Protection

## Purpose

A checkpoint can be authentic and structurally valid while still being old.
The freshness policy prevents an accepted checkpoint from moving backward and
rejects conflicting heads at the same sequence.

## Policy

`CheckpointFreshnessPolicy` binds accepted state to an explicit `ledger_id`.
The current `LedgerCheckpoint` schema contains `event_count` rather than a
separate sequence field, so `event_count` is treated as the monotonic sequence
for this layer.

The policy:

1. accepts the first valid checkpoint;
2. accepts a checkpoint with a greater `event_count`;
3. rejects a lower `event_count` as rollback;
4. accepts an exact repeat idempotently;
5. rejects a different head at the same `event_count` as a conflict;
6. rejects malformed checkpoint metadata before state mutation.

Rejected candidates never replace the last accepted checkpoint.

## Trust boundary

This module does not authenticate checkpoints, establish the organizational
trust root, persist the accepted state, or provide distributed consensus.
Those responsibilities remain separate. Signed checkpoint verification and
authenticated key resolution must happen before a checkpoint is treated as
trusted input. Durable storage must protect the last accepted freshness state
against local rollback or deletion.

## Production requirements

A production implementation still needs:

- durable authenticated storage for the accepted checkpoint;
- signed checkpoint verification with authenticated key distribution;
- key rotation and revocation policy;
- protection against rollback of the freshness store itself;
- explicit recovery behavior after state loss;
- distributed conflict resolution when multiple authorities can issue
  checkpoints;
- monitoring and audit records for rejected rollback/conflict attempts.

This is a reference implementation and test boundary, not a production trust
service.
