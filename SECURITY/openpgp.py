"""Pinned-fingerprint GnuPG adapter for operator-managed artifacts.

This is deliberately independent of DeepCore ledger authority and PKI.
No key creation, secret import, network retrieval, or trust-on-first-use occurs here.
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Callable
from pathlib import Path


PINNED_FINGERPRINT = "DE4EFCA3E1AB9E41CE96CECB18C09E865EC948A1"
_FINGERPRINT = re.compile(r"[0-9A-F]{40}\Z")
_BAD_VALIDITY = frozenset("redi")  # revoked, expired, disabled, invalid


class OpenPGPError(RuntimeError):
    """Raised when a key or cryptographic operation fails closed."""


class OpenPGP:
    def __init__(self, fingerprint: str = PINNED_FINGERPRINT, homedir: str | Path | None = None):
        normalized = fingerprint.replace(" ", "").upper()
        if not _FINGERPRINT.fullmatch(normalized):
            raise ValueError("Expected a complete 40-character OpenPGP v4 fingerprint")
        self.fingerprint = normalized
        self.homedir = Path(homedir).expanduser() if homedir is not None else None

    def _run(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        if not shutil.which("gpg"):
            raise OpenPGPError("GnuPG executable 'gpg' is not installed")
        command = ["gpg", "--no-options", "--batch", "--no-tty", "--no-auto-key-retrieve"]
        if self.homedir is not None:
            if not self.homedir.is_dir():
                raise OpenPGPError("Configured GnuPG home directory does not exist")
            command.extend(["--homedir", str(self.homedir)])
        command.extend(arguments)
        try:
            return subprocess.run(command, capture_output=True, text=True, check=False)
        except OSError as exc:
            raise OpenPGPError("Unable to execute GnuPG") from exc

    def require_key(self, *, secret: bool = False) -> None:
        command = "--list-secret-keys" if secret else "--list-keys"
        result = self._run("--with-colons", "--fingerprint", command, self.fingerprint)
        if result.returncode:
            kind = "secret" if secret else "public"
            raise OpenPGPError(f"Pinned {kind} key is not available in the local GnuPG keyring")
        primary_tag = "sec" if secret else "pub"
        matching = False
        pending_validity = None
        for line in result.stdout.splitlines():
            fields = line.split(":")
            if fields[0] == primary_tag:
                pending_validity = fields[1]
            elif fields[0] in ("pub", "sec", "sub", "ssb"):
                pending_validity = None
            elif fields[0] == "fpr" and pending_validity is not None:
                if fields[9].upper() == self.fingerprint:
                    if any(flag in pending_validity.lower() for flag in _BAD_VALIDITY):
                        raise OpenPGPError("Pinned key is expired, revoked, disabled, or invalid")
                    matching = True
                pending_validity = None
        if not matching:
            raise OpenPGPError("GnuPG returned no matching primary key fingerprint")

    @staticmethod
    def _check_input(path: str | Path) -> Path:
        candidate = Path(path).expanduser()
        if not candidate.is_file():
            raise OpenPGPError(f"Input file does not exist: {candidate}")
        return candidate.resolve()

    @staticmethod
    def _check_output(path: str | Path) -> Path:
        candidate = Path(path).expanduser()
        if candidate.exists() or candidate.is_symlink() or candidate.name == "-":
            raise OpenPGPError(f"Refusing to overwrite an existing output: {candidate}")
        if not candidate.parent.is_dir():
            raise OpenPGPError(f"Output directory does not exist: {candidate.parent}")
        return candidate.resolve()

    @staticmethod
    def _require_success(result: subprocess.CompletedProcess[str], operation: str) -> None:
        if result.returncode != 0:
            # Avoid printing gpg diagnostics, which may include filenames or user IDs.
            raise OpenPGPError(f"GnuPG {operation} failed (exit code {result.returncode})")

    @staticmethod
    def _statuses(result: subprocess.CompletedProcess[str]) -> list[list[str]]:
        return [fields for line in result.stdout.splitlines()
                if line.startswith("[GNUPG:] ")
                if (fields := line[len("[GNUPG:] "):].split())]

    def _write_artifact(self, source: Path, dest: Path, operation: str,
                        arguments: tuple[str, ...],
                        validate: Callable[[subprocess.CompletedProcess[str]], None] | None = None) -> Path:
        # GnuPG may emit plaintext before reporting a bad integrity check. Keep
        # all output private until both GnuPG and our policy accept the result.
        try:
            with tempfile.TemporaryDirectory(prefix=".openpgp-", dir=dest.parent) as staging:
                staged = Path(staging) / "artifact"
                result = self._run(*arguments, "--output", str(staged), "--", str(source))
                self._require_success(result, operation)
                if validate is not None:
                    validate(result)
                staged.chmod(0o600)
                # Same-filesystem hard link publishes atomically and refuses a
                # destination created after _check_output (including symlinks).
                os.link(staged, dest)
        except OSError as exc:
            raise OpenPGPError(f"Unable to publish {operation} output without overwriting") from exc
        return dest

    def sign(self, data: str | Path, signature: str | Path) -> Path:
        self.require_key(secret=True)
        source = self._check_input(data)
        dest = self._check_output(signature)
        return self._write_artifact(source, dest, "signing",
                                    ("--armor", "--local-user", self.fingerprint, "--detach-sign"))

    def verify(self, data: str | Path, signature: str | Path) -> bool:
        self.require_key()
        source = self._check_input(data)
        detached = self._check_input(signature)
        result = self._run("--status-fd", "1", "--verify", "--", str(detached), str(source))
        if result.returncode:
            return False
        statuses = self._statuses(result)
        if any(s[0] in {"BADSIG", "ERRSIG", "REVKEYSIG", "EXPKEYSIG", "EXPSIG"} for s in statuses):
            return False
        valid = [s for s in statuses if s[0] == "VALIDSIG"]
        if len(valid) != 1:
            return False  # no valid signature, or ambiguous/multiple signatures
        record = valid[0]
        if len(record) < 10:
            return False
        # VALIDSIG includes the signing key and (when present) its primary fingerprint.
        # Subkey signatures must belong to our exact pinned primary key.
        signer = record[1].upper()
        primary = record[10].upper() if len(record) > 10 else signer
        return primary == self.fingerprint

    def encrypt(self, data: str | Path, ciphertext: str | Path) -> Path:
        self.require_key()
        source = self._check_input(data)
        dest = self._check_output(ciphertext)
        # The recipient is already pinned to a full fingerprint, not a user ID.
        # Independent out-of-band fingerprint verification is required at enrollment.
        return self._write_artifact(source, dest, "encryption",
                                    ("--trust-model", "always", "--armor", "--recipient",
                                     self.fingerprint, "--encrypt"))

    def _validate_decryption(self, result: subprocess.CompletedProcess[str]) -> None:
        statuses = self._statuses(result)
        keys = [s for s in statuses if s[0] == "DECRYPTION_KEY"]
        if len(keys) != 1 or len(keys[0]) < 3 or keys[0][2].upper() != self.fingerprint:
            raise OpenPGPError("Decryption did not use the pinned primary key or its subkey")
        # Check the actual selected primary/subkey against the local keyring's
        # current validity; possessing another secret key is not authorization.
        selected = keys[0][1].upper()
        listing = self._run("--with-colons", "--with-subkey-fingerprint", "--list-keys", self.fingerprint)
        self._require_success(listing, "decryption key validation")
        validity = None
        usable = False
        for line in listing.stdout.splitlines():
            fields = line.split(":")
            if fields[0] in {"pub", "sub"}:
                validity = fields[1]
            elif fields[0] == "fpr" and validity is not None:
                if len(fields) > 9 and fields[9].upper() == selected:
                    usable = not any(flag in validity.lower() for flag in _BAD_VALIDITY)
                validity = None
        if not usable:
            raise OpenPGPError("Decryption key is unavailable, expired, revoked, disabled, or invalid")
        tags = {s[0] for s in statuses}
        info = [s for s in statuses if s[0] == "DECRYPTION_INFO"]
        aead = (len(info) == 1 and len(info[0]) > 3
                and info[0][3].isdigit() and int(info[0][3]) > 0)
        if (tags & {"BADMDC", "ERRMDC", "DECRYPTION_FAILED", "ERROR", "FAILURE"}
                or "DECRYPTION_OKAY" not in tags
                or not ("GOODMDC" in tags or aead)):
            raise OpenPGPError("Decryption integrity was not confirmed")

    def decrypt(self, ciphertext: str | Path, plaintext: str | Path) -> Path:
        self.require_key(secret=True)
        source = self._check_input(ciphertext)
        dest = self._check_output(plaintext)
        # Decryption alone NEVER authenticates a sender or authorizes ledger actions.
        return self._write_artifact(source, dest, "decryption",
                                    ("--status-fd", "1", "--decrypt"), self._validate_decryption)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="DeepCore operator OpenPGP artifact utility")
    parser.add_argument("--homedir", help="Existing local GnuPG home, default GnuPG configuration")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("status", help="Check that the pinned public key is present")
    for name in ("sign", "verify", "encrypt", "decrypt"):
        cmd = sub.add_parser(name)
        cmd.add_argument("input", help="Artifact or ciphertext path")
        cmd.add_argument("output", help="Signature, plaintext, or ciphertext path")
    args = parser.parse_args(argv)
    adapter = OpenPGP(homedir=args.homedir)
    try:
        if args.command == "status":
            adapter.require_key()
            print(f"Pinned OpenPGP public key available: {adapter.fingerprint}")
        elif args.command == "sign":
            adapter.sign(args.input, args.output)
            print("Detached signature created")
        elif args.command == "verify":
            if not adapter.verify(args.input, args.output):
                raise OpenPGPError("Detached signature is invalid or signed by an unpinned key")
            print("Valid detached signature from pinned key")
        elif args.command == "encrypt":
            adapter.encrypt(args.input, args.output)
            print("Artifact encrypted to pinned recipient")
        else:
            adapter.decrypt(args.input, args.output)
            print("Artifact decrypted; sender identity is NOT verified")
        return 0
    except (OpenPGPError, ValueError) as exc:
        print(f"OpenPGP error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
