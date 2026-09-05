# DeepCore Systems Enterprise Source Restoration Manifest

Date: 2026-09-05
Branch: `archive/deepcore-library-2026-09-v2`

## Purpose

This manifest defines the controlled restoration of historical DeepCore Systems Enterprise source packages into GitHub. Historical implementations are preserved under versioned archive paths and are not treated as the current production implementation.

## Source packages

| Package | Restoration policy |
|---|---|
| `DeepCore_Spark_Addon.zip` | Restore under `ARCHIVE/SOURCE/DeepCore_Spark_Addon/` |
| `deepcore-acos-repo.zip` | Restore under `ARCHIVE/SOURCE/ACOS-Repo/` |
| `deepcore-acos-docker-compose.zip` | Restore under `ARCHIVE/SOURCE/ACOS-Docker-Compose/` |
| `deepcore-systems-enterprise-dc-asr-v1.4.zip` | Restore under `ARCHIVE/SOURCE/DC-ASR-v1.4/` |
| `deepcore-enterprise-reference.zip` | Restore under `ARCHIVE/SOURCE/Enterprise-Reference/` |
| `deepcore-enterprise-upgraded.zip` | Restore under `ARCHIVE/SOURCE/Enterprise-Upgraded/` |
| `launch-desk.zip` | Restore under `ARCHIVE/SOURCE/Launch-Desk/` |
| `deepcore-enterprise-agents-upgraded.zip` | Restore under `ARCHIVE/SOURCE/Enterprise-Agents-Upgraded/` |
| `deepcore-enterprise-finished.zip` | Restore under `ARCHIVE/SOURCE/Enterprise-Finished/` |
| `deepcore-enterprise-openai-modernized.zip` | Restore under `ARCHIVE/SOURCE/Enterprise-OpenAI-Modernized/` |

## Restoration gates

1. Preserve archive SHA-256 values from `ARCHIVE/DEEPCORE_LIBRARY_INVENTORY_2026-09-05.md`.
2. Preserve historical versions without overwriting reviewed production source.
3. Exclude `__pycache__/`, `*.pyc`, generated build output, local databases, credentials, private keys, wallet seeds, passwords, and production certificates containing sensitive material.
4. Inspect `.env.example` files before restoration and retain only non-secret placeholders.
5. Run secret scanning before considering restored source mergeable.
6. Run applicable unit, integration, contract, and security tests after restoration.
7. Production readiness requires executable test evidence, not archive presence or documentation alone.
8. Do not merge this archival branch into `main` automatically.

## Status

- Library inventory: RECORDED
- Archive provenance: RECORDED
- Source restoration: IN PROGRESS
- Secret scan: NOT YET EXECUTED
- Test suite: NOT YET EXECUTED
- Production readiness: NOT CLAIMED
