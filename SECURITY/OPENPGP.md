# OpenPGP operator artifact security (experimental)

This is an **operator-facing, isolated adapter**, not a replacement for DeepCore's Ed25519 identities, private PKI, SSIL authorization, event ledger, or consensus certificates. It supports detached file signing and signature verification, as well as file encryption and decryption with a local GnuPG keyring. It does **not** enroll a user, authorize transactions, or sign Git commits automatically.

## Pinned key enrollment

The public fingerprint is configured in `SECURITY/openpgp.py`:

`DE4EFCA3E1AB9E41CE96CECB18C09E865EC948A1`

**Ownership and authenticity of this key are not independently established.** Verify the full 40-character fingerprint with the actual owner over a trusted independent channel before accepting signatures or encrypting sensitive data. A fingerprint by itself is neither the public key nor proof of control. Production trust requires separate identity and key-custody review.

On Android Termux:

```sh
pkg install -y python gnupg git
cd "$HOME/deepcore-systems-enterprise"
gpg --keyserver hkps://keys.openpgp.org --recv-keys DE4EFCA3E1AB9E41CE96CECB18C09E865EC948A1
gpg --fingerprint DE4EFCA3E1AB9E41CE96CECB18C09E865EC948A1
python -m SECURITY.openpgp status
```

If the key is not on the keyserver, get the public key from a verified owner and import it using `gpg --import /path/to/public-key.asc`. Recheck the fingerprint. Do not generate another key and claim it matches this fingerprint. Never paste or commit secret keys, tokens, passwords, recovery material, or passphrases. A locally unlocked private key and GnuPG agent may be needed for signing or decryption.

## Example commands

Keep your local artifacts outside the Git repository.

```sh
printf 'DeepCore operator artifact\n' > "$HOME/deepcore-artifact.txt"

# Private key must already exist for signing.
python -m SECURITY.openpgp sign "$HOME/deepcore-artifact.txt" "$HOME/deepcore-artifact.txt.asc"

# Only the pinned public key is needed for verification and encryption.
python -m SECURITY.openpgp verify "$HOME/deepcore-artifact.txt" "$HOME/deepcore-artifact.txt.asc"
python -m SECURITY.openpgp encrypt "$HOME/deepcore-artifact.txt" "$HOME/deepcore-artifact.pgp.asc"

# Matching private key is required for decryption.
python -m SECURITY.openpgp decrypt "$HOME/deepcore-artifact.pgp.asc" "$HOME/deepcore-restored.txt"
```

Use `--homedir /existing/path` **before** the subcommand to select another existing GnuPG keyring.

The utility neither creates nor imports keys automatically; it never transmits secrets. It refuses overwriting output files. A missing/expired/revoked key, tampered data, or a wrong-signing-key signature fails closed.

Encryption to the exact pinned fingerprint uses the GnuPG `always` trust model, relying on **independent manual fingerprint enrollment** rather than a web-of-trust assertion. Encryption provides confidentiality, **not sender authentication**; signatures authenticate possession of a key only after key ownership is independently validated. Decrypted content must not bypass any DeepCore policy or ledger authorization boundary.

## Testing and remaining work

```sh
python -m pytest -q tests/test_openpgp.py
```

Tests use disposable local GnuPG fixture keys only, and cover signature creation, verification, tampering, other-key rejection, subkey verification, encryption/decryption, missing keys, and no-overwrite behavior. Fixture private keys have no passphrases, **only in tests**.

This is not wired into production transaction approval or the event ledger. Production rollout still requires key ownership verification, rotation, revocation monitoring, hardware custody where appropriate, audit logging, recovery procedures, and independent security review.
