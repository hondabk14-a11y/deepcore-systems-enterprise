# DeepCore Enterprise / BKILLINGS production release

Current release decision: **BLOCKED**. No production deployment is running.
The implemented HTTP service is a simulation with deliberately public test
validator keys. It must not be promoted into real signing, payment settlement,
or a production validator simply by changing its label or configuration.

BKILLINGS identifies the workspace and connected Hugging Face account. It is
not an authenticated enterprise tenant, bank account, Binance trading account,
or authorized validator identity.

## Prerequisites

1. Select and bind the deployment account, target environment, identities,
   TLS endpoint, storage, and external secrets using supported configuration.
2. Merge reviewed gate fixes and obtain successful CI with the pinned
   dependencies. Resolve the GitHub startup failure first; zero executed jobs
   provide no passing evidence. Complete security/CodeQL and required packaging.
3. Implement and test a persistent authoritative service with authenticated
   identities, authorization, durable transactions, recovery, and health checks.
   Existing simulation results do not constitute durable enterprise state.
4. Establish external HSM/KMS key custody, validator enrollment/revocation,
   authenticated distributed transport, and partition/restart safety tests.
5. Implement the enterprise integrations included in the requested release,
   with transaction lifecycles, replay protection, and reconciliation. Architecture
   documents do not fulfill this requirement.
6. Verify actual environment health, restore and rollback drills, monitoring,
   alerts, resource/capacity limits, and incident procedures against the release.
7. Have an independently authorized reviewer attest the evidence. Release and
   deployment authorization remain separate from this repository verifier.

## Signed evidence validation

`production_release_evidence.py` requires a signed manifest, independent
reviewer public key, ten distinct evidence artifacts, and explicit expected
commit/environment/deployment identifiers. The trusted reviewer key must come
from an independently controlled trust channel; a key supplied within the
evidence bundle is not sufficient. No production private keys are generated
by this verifier or committed here.

Manifest fields are exactly:

- `schema_version`: `1.0`
- `repository`: `hondabk14-a11y/deepcore-systems-enterprise`
- `commit_sha`: the 40-character lowercase Git commit
- `environment`, `deployment_id`, `reviewer_id`: explicit identities
- `release_scope`: `full-enterprise`
- `mode`: `production`
- `issued_at`, `expires_at`: Unix seconds; validity at most seven days
- `controls`: exactly `ci`, `security`, `infrastructure`, `key_custody`,
  `backup_restore`, `rollback`, `observability`, `distributed_recovery`,
  `enterprise_integrations`, and `independent_review`

Each control contains only `status` (`PASS`), `artifact` (relative path under
the evidence directory), and `sha256` (lowercase hexadecimal). Artifacts must
be nonempty, distinct regular files, without symbolic links, at most 64 MiB
each. These records must describe executed checks for this production release.

The reviewer signs the following exact bytes with Ed25519:

```python
DOMAIN + canonical_bytes(manifest)
```

Both definitions are exported by `production_release_evidence.py`. The
signature file contains the raw 64-byte signature; the trusted public key is
PEM. The earlier generic file-signing utility uses a different signing domain
and cannot be substituted for a release attestation.

```sh
python PRODUCTION-READINESS-GATES/production_release_evidence.py \
  --manifest /secure/evidence/manifest.json \
  --signature /secure/evidence/reviewer.sig \
  --trusted-reviewer-key /trusted/reviewer-public.pem \
  --evidence-dir /secure/evidence/artifacts \
  --commit RELEASE_COMMIT \
  --environment PRODUCTION_ENVIRONMENT \
  --deployment-id RELEASE_DEPLOYMENT_ID
```

Replace the identifiers with real release values. Missing evidence exits
nonzero. Altered signatures, artifacts, mismatched targets, expired evidence,
missing controls, and simulation scope are rejected. No artifact bundle or
reviewer key for production currently exists in this workspace.

A successful result verifies the reviewer's attestation and artifact integrity.
It does not independently execute or establish the truth of operational checks,
certify production, grant deployment approval, or deploy a service. The validator
is not currently wired to a production deployment pipeline; none exists here.

## Current blockers

GitHub main remains `44c06aca0fe0b6a682b7a40bea530312e27c6888`.
Gate repairs are proposed in PR #40 and have not been merged. The last observed
run `37093061099` ended in `startup_failure` with zero jobs. Local dependency
installation failed; full pytest and cryptography 46.0.1 remain unverified.
The managed environment reports no deployment identities or secret bindings.
Hosting selection is pending. Local networking and Docker execution were
previously blocked; no successful live service verification is recorded.

The eight adversarial release-evidence tests use ephemeral test keys and
temporary fixtures only. They establish verifier behavior, not production
evidence. Production certification remains **NOT_CERTIFIED**.
