# Repository Security and Release Controls

## Purpose

This document defines the security baseline for the DeepCore Systems Enterprise repository. It is a repository policy and engineering checklist, not evidence that every control is currently automated or production-deployed.

## Secrets and credentials

Never commit API keys, private keys, wallet seeds or mnemonics, passwords, production certificates, signing material, cloud credentials, database credentials, or other operational secrets.

Use environment variables or an approved secret-management system at runtime. `.env.example` may document required variable names and safe placeholder values, but `.env` and real secret values remain outside version control.

`.gitignore` is a convenience control, not a security boundary. Review staged changes before every commit and treat accidental secret exposure as an incident requiring credential rotation.

## Cryptographic key custody

Private keys must be generated and stored in an appropriate protected environment. Where hardware-backed custody is specified, the implementation must demonstrate the actual hardware or secure service boundary before claiming that control is implemented.

Public keys, certificate chains, trust anchors, and test fixtures may be committed only when they contain no private or operational secret material.

## Least privilege

Repository access, CI credentials, cloud identities, signing identities, and runtime service accounts should receive only the permissions required for their function. Administrative repository access must not be treated as evidence of organization-wide or GitHub-wide administrative authority.

## Fail-closed behavior

Security-sensitive verification paths should fail closed on malformed input, invalid signatures, missing trust configuration, expired or otherwise unacceptable credentials, policy violations, and ambiguous authorization state.

## Supply-chain security

Dependencies must be pinned or constrained appropriately for the release environment and reviewed for known vulnerabilities. Build and deployment actions should use trusted, maintained actions and minimal permissions. Third-party code must not be granted broader privileges than required.

## GitHub Actions and CI

Future workflows should:

- use least-privilege `GITHUB_TOKEN` permissions;
- keep secrets in GitHub or an external secret manager rather than source files;
- pin security-sensitive actions to reviewed versions or immutable references where practical;
- prevent untrusted pull-request code from receiving privileged secrets;
- verify dependencies and build artifacts before release; and
- preserve auditable logs for security-relevant release decisions.

No CI workflow is considered production security evidence until it has been executed and its results reviewed.

## Verification and release gates

DeepCore status terminology is explicit:

- **Documented:** described in repository documentation.
- **Implemented:** executable code exists for the capability.
- **Tested:** executable tests have demonstrated the stated behavior.
- **Production-ready:** implementation, testing, security review, operational controls, and release criteria have all been satisfied.

Documentation alone must never promote a capability to `Implemented`, `Tested`, or `Production-ready`.

## Incident response

If a secret is committed:

1. Stop using the exposed credential.
2. Revoke or rotate it immediately.
3. Determine whether the secret was accessible to unauthorized parties.
4. Remove the secret from the working tree and prevent recurrence.
5. Review repository history and logs as appropriate.
6. Record the incident and corrective action.

Removing a secret from the latest commit does not necessarily remove it from Git history or external caches.

## Backup and recovery

Event history is authoritative for DeepCore state. Backups of critical state must preserve integrity, provenance, and recovery procedures. Snapshot files are acceleration artifacts and must not silently replace authoritative event history.

Recovery procedures should be tested before they are described as operationally proven.

## Security claims

Terms such as `BIP`, `verified`, `deployed`, `live`, `quantum`, `6G`, `production`, or `production-ready` must be used precisely. A research concept, architecture proposal, simulator, or documentation baseline is not equivalent to a deployed production control.

External standards and specifications should be referenced by their actual status. A project-specific proposal must not be presented as an accepted external standard.

## Pre-release checklist

Before an executable release:

- [ ] No secrets or sensitive local state are staged.
- [ ] Dependencies and build inputs are reviewed.
- [ ] Cryptographic algorithms and parameters are explicitly identified.
- [ ] Authentication and authorization paths fail closed.
- [ ] Replay, rollback, and state-integrity behavior is tested where applicable.
- [ ] Event replay and recovery are tested.
- [ ] Security-sensitive logs are auditable without leaking secrets.
- [ ] CI results are reviewed.
- [ ] Documentation matches the actual implementation status.
- [ ] Production claims are supported by evidence.

## Scope

This baseline applies to the private DeepCore repository and its future executable artifacts. It should evolve as implementation, threat modeling, deployment, and verification mature.