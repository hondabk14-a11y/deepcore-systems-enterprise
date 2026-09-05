# DeepCore Security Policy

## Production security boundary

DeepCore production changes require automated validation and appropriate human review. Cryptographic, consensus, payment, treasury, identity, PKI, and production-infrastructure changes require explicit review before release.

## Secrets

Never commit API keys, access tokens, passwords, wallet seeds, private keys, signing material, or `.env` files containing secrets. Use the deployment environment's secret-management mechanism.

## Fail-closed requirements

Do not disable authentication, authorization, signature verification, certificate validation, replay protection, consensus safety, or ledger invariants to make a build or test pass.

## Reporting

Security issues should be handled privately and should not be disclosed publicly with exploit details before remediation is coordinated.
