"""BIP173, secp256k1 and Base58Check regression cases for read-only inspector."""
import pytest

from BITCOIN.public_key_inspector import inspect_public_key

# Standard secp256k1 generator, not a user or wallet key.
GENERATOR = "0279be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798"


def test_mainnet_bip173_and_legacy_known_vectors():
    result = inspect_public_key(GENERATOR)
    assert result["hash160"] == "751e76e8199196d454941c45d1b3a323f1433bd6"
    assert result["p2pkh"] == "1BgGZ9tcN4rm9KBzDn7KprQz87SZ26SAMH"
    assert result["p2wpkh"] == "bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kv8f3t4"
    assert result["p2sh_p2wpkh"].startswith("3")


def test_testnet_bip173_known_vector():
    result = inspect_public_key(GENERATOR, network="testnet")
    assert result["p2wpkh"] == "tb1qw508d6qejxtdg4y5r3zarvary0c5xw7kxpjzsx"
    assert result["p2pkh"].startswith(("m", "n"))
    assert result["p2sh_p2wpkh"].startswith("2")


@pytest.mark.parametrize("bad", ["", "xyz", "02" + "00" * 31, "04" + "00" * 32, "02" + "ff" * 32])
def test_invalid_public_keys_are_rejected(bad):
    with pytest.raises(ValueError):
        inspect_public_key(bad)


def test_invalid_network_is_rejected():
    with pytest.raises(ValueError, match="network"):
        inspect_public_key(GENERATOR, network="regtest")


def test_uncompressed_key_is_rejected():
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import ec
    public = ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256K1(), bytes.fromhex(GENERATOR))
    uncompressed = public.public_bytes(serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint)
    with pytest.raises(ValueError, match="33-byte"):
        inspect_public_key(uncompressed.hex())
