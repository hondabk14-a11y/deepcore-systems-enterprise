---
title: DeepCore Systems Enterprise
emoji: 🔐
colorFrom: blue
colorTo: gray
sdk: docker
app_port: 7860
---

# DeepCore Systems Enterprise reference service

Runs the existing DeepCore signed-ledger reference implementation and exposes
read-only verification evidence at `/api/status`. `/healthz` checks liveness;
`/readyz` checks successful startup verification. Verification failure aborts startup.

This is a single-process simulation, not an independently distributed validator
network or a production financial system. Balances are synthetic. Identities and
state are ephemeral and replaced on restart. External transaction submission,
payments, wallet keys and authoritative AI decisions are not exposed.

The Space must remain private. No real funds or private operational data belong here.
The GitHub source commit is recorded in `deployment.json` and the status response.
