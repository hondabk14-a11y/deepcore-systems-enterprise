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
python -m pytest -q tests/test_openpgp.py tests/test_openpgp_policy.py
```

Tests use disposable local GnuPG fixture keys only, and cover signature creation, verification, tampering, other-key rejection, subkey verification, encryption/decryption, missing keys, and no-overwrite behavior. Fixture private keys have no passphrases, **only in tests**. The real-GnuPG suite also covers wrong-recipient decryption, damaged ciphertext, encryption subkeys, and expired/revoked keys. `test_openpgp_policy.py` separately simulates process status and output to test policy, cleanup, permissions, and publication races; it is not cryptographic execution evidence.

This is not wired into production transaction approval or the event ledger. Production rollout still requires key ownership verification, rotation, revocation monitoring, hardware custody where appropriate, audit logging, recovery procedures, and independent security review.

## Output and decryption policy

Signing, encryption, and decryption first write inside a private temporary directory
in the destination directory. Decryption additionally requires a successful GnuPG
result, integrity status, and `DECRYPTION_KEY` identifying the pinned primary key
or a currently usable subkey of that primary. An unrelated secret key in the same
keyring cannot authorize output. Expired/revoked/disabled/invalid selected keys are
rejected using the current local keyring; this does not discover new revocations
from a disconnected owner.

Only accepted output is published, with mode `0600`, using an atomic hard link
that cannot replace an existing destination. Handled failures remove the staging
directory. Use a trusted directory on a filesystem supporting hard links (on
Termux, use the app's private home, not Android shared storage). Unsupported
filesystems fail closed. A process or machine crash can leave a private staging
directory; cleanup is not a secure-erasure guarantee. Decryption still does not
authenticate a sender or grant ledger authority.

## Key lifecycle approval checklist — pending

This is the proposed procedure, not evidence of completed enrollment or production
key custody. Before merge, the operator and human cryptographic reviewer must
approve it and record the outstanding decisions. Before production use, execute
and independently verify the procedures in the intended environment.

- **Enrollment:** independently contact the intended owner; compare the complete
  primary fingerprint and public-key packet; verify a fresh, context-bound signed
  challenge. Record the channel, reviewer, date, fingerprint, and proof result.
  A keyserver result or disposable test key does not establish ownership.
- **Custody:** name the responsible operator and backup custodian; decide hardware
  or isolated signing storage, passphrase and access policy, and audit access.
  Keep private keys, passphrases, revocation certificates, and backups outside Git
  and CI. No custody assignment is asserted by this document.
- **Rotation:** approve a replacement identity independently, review the pin
  change through a PR, rerun negative tests, and verify real hosted CI. Define
  cutover and old-artifact handling explicitly; do not silently accept both pins.
- **Revocation:** assign responsibility and a refresh schedule for obtaining
  authenticated revocation information. Stop use on suspected compromise; import
  the revocation into every verifier keyring and demonstrate rejection. This
  utility does not poll keyservers and cannot detect an unseen revocation.
- **Recovery:** test restoration of protected key backups in isolation; verify
  access controls and approved decrypt/sign behavior without exposing secrets.
  Lost signing keys must not be replaced by claiming another key has the same pin.
- **Approval evidence:** record real GnuPG and Termux results, successful hosted
  runs for the candidate commit, and independent human cryptographic review.
  Production remains **NOT_CERTIFIED** until environment-specific evidence exists.
