"""Isolated GnuPG integration tests using generated disposable keys only."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from SECURITY.openpgp import OpenPGP, OpenPGPError, PINNED_FINGERPRINT, main

pytestmark = pytest.mark.skipif(not shutil.which("gpg"), reason="GnuPG is required")


def _gpg(home: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["gpg", "--no-options", "--batch", "--no-tty", "--homedir", str(home),
                           *args], capture_output=True, text=True, check=True)


def _make_key(home: Path, name: str) -> str:
    _gpg(home, "--pinentry-mode", "loopback", "--passphrase", "", "--quick-gen-key",
         f"{name} <test@example.invalid>", "rsa2048", "sign,encrypt", "0")
    listing = _gpg(home, "--with-colons", "--fingerprint", "--list-secret-keys")
    fingerprints = [line.split(":")[9] for line in listing.stdout.splitlines() if line.startswith("fpr:")]
    return fingerprints[-1]


@pytest.fixture
def keys(tmp_path: Path):
    home = tmp_path / "gnupg"
    home.mkdir(mode=0o700)
    first = _make_key(home, "DeepCore fixture")
    client = OpenPGP(first, homedir=home)
    payload = tmp_path / "sample.txt"
    payload.write_text("DeepCore fixture artifact\n", encoding="utf-8")
    return home, client, payload


def test_pinned_fingerprint_is_public_hex():
    assert len(PINNED_FINGERPRINT) == 40
    assert PINNED_FINGERPRINT == PINNED_FINGERPRINT.upper()
    with pytest.raises(ValueError):
        OpenPGP("short")


def test_sign_verify_and_tamper(keys, tmp_path: Path):
    _, client, payload = keys
    signature = client.sign(payload, tmp_path / "sample.asc")
    assert client.verify(payload, signature)
    payload.write_text("Modified artifact\n", encoding="utf-8")
    assert not client.verify(payload, signature)


def test_encrypt_decrypt_and_no_clobber(keys, tmp_path: Path):
    _, client, payload = keys
    encrypted = client.encrypt(payload, tmp_path / "sample.gpg.asc")
    assert "DeepCore fixture artifact" not in encrypted.read_text(encoding="utf-8")
    decrypted = client.decrypt(encrypted, tmp_path / "restored.txt")
    assert decrypted.read_bytes() == payload.read_bytes()
    with pytest.raises(OpenPGPError, match="Refusing to overwrite"):
        client.decrypt(encrypted, decrypted)


def test_wrong_key_rejected(keys, tmp_path: Path):
    home, client, payload = keys
    signature = client.sign(payload, tmp_path / "correct.asc")
    other = _make_key(home, "Unpinned fixture")
    wrong = OpenPGP(other, homedir=home)
    assert not wrong.verify(payload, signature)
    bad_sig = wrong.sign(payload, tmp_path / "wrong.asc")
    assert not client.verify(payload, bad_sig)


def test_missing_fingerprint_fails_closed(keys, tmp_path: Path):
    home, _, payload = keys
    missing = OpenPGP("F" * 40, homedir=home)
    with pytest.raises(OpenPGPError, match="not available"):
        missing.encrypt(payload, tmp_path / "never.asc")
    assert not (tmp_path / "never.asc").exists()


def test_cli_status_missing_key_returns_error(keys, capsys):
    home, _, _ = keys
    assert main(["--homedir", str(home), "status"]) == 1
    assert "Pinned public key" not in capsys.readouterr().out


def test_valid_signing_subkey_is_bound_to_pinned_primary(keys, tmp_path: Path):
    home, client, payload = keys
    _gpg(home, "--pinentry-mode", "loopback", "--passphrase", "", "--quick-add-key",
         client.fingerprint, "ed25519", "sign", "0")
    listing = _gpg(home, "--with-colons", "--fingerprint", "--list-secret-keys", client.fingerprint)
    subkey = [line.split(":")[9] for line in listing.stdout.splitlines()
              if line.startswith("fpr:")][-1]
    signature = tmp_path / "subkey.asc"
    _gpg(home, "--local-user", subkey + "!", "--detach-sign", "--output",
         str(signature), str(payload))
    assert client.verify(payload, signature)
