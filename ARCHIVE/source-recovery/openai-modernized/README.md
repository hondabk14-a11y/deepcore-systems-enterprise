# DeepCore Systems Enterprise Source Restoration

Status: archive/source recovery in progress

The connected project library contains multiple historical DeepCore packages. They overlap substantially, so the repository will preserve provenance rather than silently merge conflicting implementations.

## Safety rules

- Never commit secrets or credentials.
- Never commit wallet mnemonics/private keys.
- Never commit `.env` files containing secrets.
- Exclude `__pycache__` and `*.pyc` artifacts.
- Preserve historical packages under `ARCHIVE/source-recovery/<artifact>/` until reviewed.
- Production-ready is an evidence state, not a label applied by packaging.

## Current binary archive

`ARCHIVE/zips/deepcore-enterprise-openai-modernized.zip`

The source tree will be promoted only after provenance, dependency, security, and CI review.
