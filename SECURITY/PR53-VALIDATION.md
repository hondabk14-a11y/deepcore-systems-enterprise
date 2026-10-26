# PR #53 remediation evidence

Base reviewed: `141bc5c596e96aa68166d27d7e2e9184258f4123`.
Validation date: 2026-10-25 (America/Chicago).
Local environment: Python 3.12.14; GnuPG 2.4.4 executable available, but agent
socket creation is denied by the execution environment.

## Changes

- Stage sign/encrypt/decrypt output privately; publish mode-0600 output atomically
  without overwriting, after process success and adapter policy checks.
- Bind decryption to the actual selected key and pinned primary, check local
  selected-key validity and integrity statuses, and reject expired signatures.
- Add real-GnuPG negative cases and separate simulated process-policy/I/O tests.
- Fix runtime script imports, require enough unique voters in the weighted quorum
  helper, and reject inconsistent block hashes or event roots in QC verification.
- Repair test fixtures that used different random keys for deterministic input,
  outdated resolver interfaces, invalid canonical hashes, or the wrong adapter.
- Restore the missing CoinGecko observation test invoked by CI; fix dynamic imports
  for hyphenated readiness scripts and dataclass test modules.
- Keep forbidden secret paths blocked: rename the blank `.env.example` template to
  `config.example`. Refine secret-literal detection so blank assignments do not
  consume subsequent lines and key-generation expressions/types are not treated
  as literal credentials. Add positive credential-detection regression tests.
- Document a proposed enrollment/custody/rotation/revocation/recovery procedure
  with human approval and real execution explicitly pending.

## Fresh local results

| Command/check | Result |
| --- | --- |
| `python -m pytest -q tests --ignore=tests/test_openpgp.py MARKET-DATA` | 174 passed |
| `python -m unittest discover -s CORE/event-sourced-ledger -p 'test_*.py' -q` | 97 passed |
| `python -m unittest discover -s SECURITY/SSIL -p 'test_ssil*.py' -q` | 51 passed |
| `python -m unittest PRODUCTION-READINESS-GATES/test-write-readiness-ssil-audit-record.py -q` | 4 passed |
| `python CORE/deepcore_runtime.py` | Pass; QC, signature, chain commitment, replay verified |
| Infrastructure, custody-boundary, synthetic backup/restore, synthetic rollback, observability preflights | Pass locally |
| Manifest validation, readiness chain, audit record scripts against a temporary synthetic manifest | Pass; not hosted evidence |
| Tracked secret-path check, Python compile checks, JS syntax checks, `git diff --check` | Pass |
| `python -m pytest -q tests/test_openpgp.py --tb=no` | 1 passed, 16 fixture errors: GnuPG agent cannot create socket |

The 30 simulated GnuPG policy tests are included in the 174 count. Against the
original adapter, those same tests yielded 20 failures and 10 passes; after the
fix all 30 pass. This demonstrates adapter policy/I/O regression coverage, not
cryptographic execution. The 17-case real-GnuPG suite remains mandatory in CI;
no skip or workflow bypass was added to hide the local agent restriction.

## External gates still open

- Resolve the account billing lock in Issue #2; demonstrate actual runner
  assignment, executed steps, and successful required workflows at the candidate
  commit. Local results do not establish hosted-CI success.
- Run the real-GnuPG suite and Termux smoke checks in a supported environment.
- Independently verify the pinned owner's identity and proof of key control.
- Obtain independent human cryptographic review and approve the proposed key
  lifecycle plan; validate production custody and recovery separately.
- Production remains **NOT_CERTIFIED**. No real operator private key was used,
  no private material was committed, and no merge or deployment is authorized by
  these local results alone.

References: [PR #53](https://github.com/hondabk14-a11y/deepcore-systems-enterprise/pull/53),
[Issue #2](https://github.com/hondabk14-a11y/deepcore-systems-enterprise/issues/2),
[PR #52](https://github.com/hondabk14-a11y/deepcore-systems-enterprise/pull/52),
[original PR #53 CI run](https://github.com/hondabk14-a11y/deepcore-systems-enterprise/actions/runs/39348186397).
