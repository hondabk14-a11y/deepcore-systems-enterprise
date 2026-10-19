"""Read-only Bitcoin address derivation for compressed secp256k1 public keys.

This is NOT a wallet, key registry, ownership proof, or signing service.
No private keys or network/RPC calls are accepted.
"""

from __future__ import annotations

import argparse
import hashlib
import json

from cryptography.hazmat.primitives.asymmetric import ec

_BASE58 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
_BECH32 = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"
_GENERATORS = (0x3B6A57B2, 0x26508E6D, 0x1EA119FA, 0x3D4233DD, 0x2A1462B3)
_NETWORKS = {"mainnet": (b"\x00", b"\x05", "bc"), "testnet": (b"\x6f", b"\xc4", "tb")}


def _hash160(payload: bytes) -> bytes:
    sha = hashlib.sha256(payload).digest()
    try:
        return hashlib.new("ripemd160", sha).digest()
    except ValueError as exc:
        raise RuntimeError("RIPEMD160 is unavailable in this Python/OpenSSL build") from exc


def _base58check(payload: bytes) -> str:
    checksum = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
    encoded = payload + checksum
    n = int.from_bytes(encoded, "big")
    chars = ""
    while n:
        n, index = divmod(n, 58)
        chars = _BASE58[index] + chars
    return "1" * (len(encoded) - len(encoded.lstrip(b"\x00"))) + chars


def _polymod(values: list[int]) -> int:
    chk = 1
    for v in values:
        top = chk >> 25
        chk = ((chk & 0x1FFFFFF) << 5) ^ v
        for bit, generator in enumerate(_GENERATORS):
            if (top >> bit) & 1:
                chk ^= generator
    return chk


def _convertbits(data: bytes, from_bits: int, to_bits: int) -> list[int]:
    acc = bits = 0
    out: list[int] = []
    mask = (1 << to_bits) - 1
    for byte in data:
        acc = (acc << from_bits) | byte
        bits += from_bits
        while bits >= to_bits:
            bits -= to_bits
            out.append((acc >> bits) & mask)
    if bits:
        out.append((acc << (to_bits - bits)) & mask)
    return out


def _bech32_v0(hrp: str, witness_program: bytes) -> str:
    if len(witness_program) != 20:
        raise ValueError("P2WPKH witness program must be 20 bytes")
    values = [0] + _convertbits(witness_program, 8, 5)
    expand_hrp = [ord(c) >> 5 for c in hrp] + [0] + [ord(c) & 31 for c in hrp]
    checksum = _polymod(expand_hrp + values + [0] * 6) ^ 1
    check = [(checksum >> (5 * (5 - i))) & 31 for i in range(6)]
    return hrp + "1" + "".join(_BECH32[v] for v in values + check)


def inspect_public_key(pubkey_hex: str, network: str = "mainnet") -> dict[str, str]:
    """Validate SEC1 compressed secp256k1 point, derive three address encodings."""
    if network not in _NETWORKS:
        raise ValueError("network must be mainnet or testnet")
    try:
        pubkey = bytes.fromhex(pubkey_hex)
    except (TypeError, ValueError) as exc:
        raise ValueError("public key must be hexadecimal") from exc
    if len(pubkey) != 33 or pubkey[0] not in (2, 3):
        raise ValueError("expected a 33-byte compressed SEC1 public key (02/03 prefix)")
    try:
        ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256K1(), pubkey)
    except ValueError as exc:
        raise ValueError("public key is not a valid secp256k1 curve point") from exc

    p2pkh_prefix, p2sh_prefix, hrp = _NETWORKS[network]
    key_hash = _hash160(pubkey)
    redeem_script = b"\x00\x14" + key_hash
    return {
        "network": network,
        "compressed_public_key": pubkey.hex(),
        "hash160": key_hash.hex(),
        "p2pkh": _base58check(p2pkh_prefix + key_hash),
        "p2sh_p2wpkh": _base58check(p2sh_prefix + _hash160(redeem_script)),
        "p2wpkh": _bech32_v0(hrp, key_hash),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("public_key", help="compressed secp256k1 public key, 66 hex characters")
    parser.add_argument("--network", choices=tuple(_NETWORKS), default="mainnet")
    args = parser.parse_args()
    try:
        print(json.dumps(inspect_public_key(args.public_key, args.network), indent=2))
    except (ValueError, RuntimeError) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
