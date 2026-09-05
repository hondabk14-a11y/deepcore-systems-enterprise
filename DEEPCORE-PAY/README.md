# DeepCore Pay

DeepCore Pay architecture includes a Swift client package with NFC tap handling, `L3Invoice`, and `DC02Proof` structures.

Security boundaries include Secure Enclave integration, HSM public-key identity, and an `l3RPC` endpoint.

Layering:

- L1: Bitcoin trustless settlement/anchoring
- L2: DeepCore sovereign state and HSM-backed identity
- L3: enterprise payment services with required compliance controls

Edge-network integration, including future 6G scenarios, remains subject to security and deployment validation.