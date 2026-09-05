# DeepCore TRON Authentication Replay Protection v1

## Status

**Documented design.** This document does not claim that the protocol is implemented or production-ready.

## Objective

Provide replay-resistant wallet authentication using a TRON account signature without exposing mnemonic, passphrase, private key, or other signing secrets to the verifier.

## Trust boundaries

```text
Mnemonic / private key
        |
        v
   Signing service
        |
        | signature
        v
Canonical authentication challenge
        |
        v
DeepCore verifier
        |
        +-- domain validation
        +-- address validation
        +-- signature validation
        +-- issued/expiry validation
        +-- atomic nonce consumption
        |
        v
DeepCore authentication event ledger
```

The verifier must never receive the mnemonic, passphrase, or private key.

## Canonical challenge

Version 1 uses these fields:

```json
{
  "address": "TRON_ADDRESS",
  "domain": "auth.deepcore.local",
  "expires_at": "2026-09-05T10:05:00+00:00",
  "issued_at": "2026-09-05T10:00:00+00:00",
  "nonce": "ONE_TIME_RANDOM_VALUE",
  "version": 1
}
```

Before signing, object keys are sorted recursively and JSON is encoded without insignificant whitespace. The exact resulting UTF-8 bytes are the signed message.

## Verification order

1. Parse and validate the challenge.
2. Confirm the requested domain is an allowed DeepCore authentication domain.
3. Confirm the address is the expected account identity.
4. Confirm the current time is before `expires_at`.
5. Verify the wallet message signature against the supplied address.
6. Atomically consume the nonce for that address.
7. Emit the authenticated event only after all checks succeed.

## Replay invariant

```text
ONE nonce + ONE address + ONE valid challenge
                    |
                    +--> at most ONE successful authentication
```

A second request using the same nonce must fail, even if its signature is otherwise valid.

## Required failure events

- `TRON_AUTH_CHALLENGE_EXPIRED`
- `TRON_MESSAGE_SIGNATURE_INVALID`
- `TRON_AUTH_NONCE_INVALID_OR_REPLAYED`
- `TRON_AUTH_ADDRESS_MISMATCH`
- `TRON_AUTH_DOMAIN_MISMATCH`

## Required success events

- `TRON_AUTH_CHALLENGE_ISSUED`
- `TRON_AUTH_SIGNATURE_RECEIVED`
- `TRON_MESSAGE_SIGNATURE_VALID`
- `TRON_AUTH_NONCE_CONSUMED`
- `TRON_AUTHENTICATED`

## Storage requirement

The production nonce store must provide an atomic consume operation. An in-memory process-local array is acceptable only for isolated unit tests and must not be treated as a production replay-control mechanism.

Recommended production record:

```text
nonce_hash
address
issued_at
expires_at
consumed_at
status
```

Store a hash of the nonce rather than the raw nonce where practical.

## Secret handling

Never commit or emit to logs:

- `TRON_MNEMONIC`
- `TRON_PASSPHRASE`
- private keys
- xprv material
- raw signing secrets
- production credentials

Public addresses and public extended keys may be recorded only when required by the audit model.

## Test requirements

The implementation is not complete until automated tests demonstrate:

- valid signature succeeds
- modified message fails
- modified address fails
- modified domain fails
- expired challenge fails
- unknown nonce fails
- reused nonce fails
- wrong-address nonce consumption fails
- different nonces remain independent
- concurrent attempts consume a nonce exactly once
- authentication events are emitted only after verification
- secrets never appear in audit payloads

## Relationship to TRON transactions

Message authentication is separate from transaction authorization. A valid login signature must never be interpreted as authorization to transfer TRX or invoke a contract.

Transaction authorization remains subject to the separate DeepCore transaction lifecycle and broadcast policy.
