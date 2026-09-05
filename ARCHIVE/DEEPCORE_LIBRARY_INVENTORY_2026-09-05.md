# DeepCore Systems Enterprise Library Inventory

Date: 2026-09-05

This inventory records the DeepCore ZIP artifacts recovered from the connected project library. SHA-256 values are included so uploaded or restored archives can be verified byte-for-byte.

| Artifact | Size | SHA-256 |
|---|---:|---|
| `DeepCore_Spark_Addon.zip` | 1,115 B | `b701fbb55e64c5a2ae90b54946c793b65b88890e5d2e58720c976028c3e7e781` |
| `deepcore-acos-repo.zip` | 2,329 B | `84eff85b6bd35f75aab9970b27f9c91a6a9e6f98f68b2f495cc2c5f747d8992d` |
| `deepcore-acos-docker-compose.zip` | 4,128 B | `0733b1cd830e1c650607285169945a45fcfac64cbbe92670664bab01a3698dfe` |
| `deepcore-systems-enterprise-dc-asr-v1.4.zip` | 12,604 B | `7081a0b9b4fac52ee211facc9c0a4b79a91d22cc8bb6deae60f4dc8172d70469` |
| `deepcore-enterprise-reference.zip` | 20,209 B | `ef81a196398da0fbd6eaf6a3e275e8ec455dcf2bd24e1560dd9ecfea05858d17` |
| `deepcore-enterprise-upgraded.zip` | 29,543 B | `d5acbd79fc6aa4bb2d62308e97f6352157be1cfa7db57179b4aec68653862a84` |
| `launch-desk.zip` | 31,642 B | `585c89839d6a24dd677813efb2c7a045d356e3b57ce69035e0243706a345997d` |
| `deepcore-enterprise-agents-upgraded.zip` | 36,159 B | `b216953de6780cef7df20813592a4aa94c7882875779be08c3ad00b47ba8b1da` |
| `deepcore-enterprise-finished.zip` | 43,774 B | `9667822417e06b3d9149150ebcb73515fc9eb2ecd75404f669b51f9f7126f0a8` |
| `deepcore-enterprise-openai-modernized.zip` | 85,616 B | `c038164288421658af7a5b7bdd855b2bda62fc066023737cec00b1e8283d7a01` |

## Security handling

- Archives may contain development configuration, example environment files, or deployment material.
- No secrets, API keys, private keys, wallet seeds, passwords, production certificates, or `.env` secrets should be committed.
- Generated or simulated values must not be represented as production evidence.
- The repository remains private.
- This inventory is an evidence index, not a claim that every artifact has been executed or validated.

## Recovery note

The connected GitHub file interface can create UTF-8 repository files and Git blobs, but binary archive transfer is handled separately from normal source-file commits. The SHA-256 values above provide the verification manifest for the original library ZIPs while source restoration proceeds through Git-compatible content commits.
