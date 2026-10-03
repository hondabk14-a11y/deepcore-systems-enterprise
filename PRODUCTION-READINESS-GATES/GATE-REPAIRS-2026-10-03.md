# Repository gate repairs

Prepared against main `44c06aca0fe0b6a682b7a40bea530312e27c6888`.

Checkpoint verification supports configured resolver objects and callables,
with resolution failures and unknown keys rejected. The malformed JSON test
now places invalid JSON after a valid record, so it exercises JSON parsing
instead of stopping first on a missing hash.

Readiness implementations and tests have importable underscore filenames;
existing hyphenated CLI entry points remain available. Evidence recording
rejects invalid existing history before append and returns the actual stored
record. Audit generation uses isolated temporary directories instead of
deleting a shared fixed file.

Production gate runs the ledger, SSIL, and readiness regression suites.
Runtime workflows invoke the runtime as a module. The missing CoinGecko
observation suite is supplied, and dynamic market-test imports register their
modules before executing dataclass definitions.

Production, security, and key-custody checks share the tracked-file checker.
Only `.env.example` templates with empty credential assignments are exempted
from environment-path rejection. Private-key material, populated credential
templates, forbidden key paths, and obvious literal secrets remain rejected.
Source expressions are distinguished from secret literals. Missing tracked
inventory and symbolic links fail closed. This is a repository heuristic,
not comprehensive secret detection or an HSM/KMS certification.

## Validation

An isolated Git index built from the complete GitHub source inventory and the
gate changes was used for tracked-file checks. No signing keys or tokens were
included. Local environment: Python 3.12.14, cryptography 50.0.0.

- Ledger: 99 unittest checks passed.
- SSIL: 51 unittest checks passed.
- Readiness and secret checks: 19 unittest checks passed.
- CoinGecko observation: 4 unittest checks passed.
- Market risk: 5 test functions passed directly; this was not pytest execution.
- Runtime: signatures, quorum certificate, chain commitment, and replay passed.
- Tracked-file and key-custody boundary checks passed.
- Infrastructure, synthetic backup/restore, synthetic rollback, and observability
  contract preflights passed. These are reference preflights, not live drills.
- Python compilation, workflow YAML parsing, and workflow shell syntax passed.

The full pytest suite, CodeQL, container execution, and GitHub semantic workflow
validation were not verified locally. Dependency installation failed in this
environment. CI pins cryptography 46.0.1; local results do not reproduce that
pin. Passing a repository gate still requires an executed successful CI run.

## Release boundary

Production certification remains **NOT_CERTIFIED**. Live infrastructure,
external key custody, environment-specific recovery/rollback, observability,
and independent review evidence are still required. Gate summary no longer
labels the core CI-verified merely because control files exist.
