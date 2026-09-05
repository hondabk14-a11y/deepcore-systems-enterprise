# DeepCore Pay

DeepCore Pay is the project's payment-interface architecture spanning local device payment handling, DeepCore settlement logic, and external Bitcoin settlement.

## Reference components

- Swift client/package integration.
- NFC tap handler.
- `L3Invoice` payment representation.
- `DC02Proof` integrity/anchoring evidence.
- Secure Enclave integration for device-bound key operations where supported.
- HSM-backed public-key identity at protected enterprise signing boundaries.
- `l3RPC` enterprise service interface.

## Layer model

- **L1: Bitcoin** — trust-minimized external settlement and independently verifiable chain state.
- **L2: DeepCore sovereign layer** — event-sourced state, cryptographic identity, deterministic processing, and protected signing/HSM boundaries.
- **L3: DeepCore Pay enterprise** — application/payment services with authorization, audit, reconciliation, and applicable compliance controls.

## Security requirements

Payment authorization, key custody, replay protection, invoice handling, device binding, and reconciliation must be explicitly tested. Private keys, wallet seeds, credentials, and production secrets must never be committed.

Edge-network integration, including 6G scenarios, remains an architectural exploration until security, interoperability, and deployment validation are complete.