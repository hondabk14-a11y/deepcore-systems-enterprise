Bitcoin public-key inspector
============================

Run from the repository root:

    python -m BITCOIN.public_key_inspector 0279be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798
    python -m pytest -q tests/test_bitcoin_public_key_inspector.py

This module validates compressed secp256k1 public points and derives mainnet/testnet address encodings. It is read-only and does not access the Bitcoin network.

The example uses a publicly documented test vector, not a user-specific key. The results do not establish wallet control or identity. A separate OpenPGP fingerprint cannot be compared without its full OpenPGP public-key packet.
