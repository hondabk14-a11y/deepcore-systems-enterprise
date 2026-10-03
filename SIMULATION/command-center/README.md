# Deepcore command center

Interactive frontend simulation integrated from ChatGPT task 01a0ffd1-6985-749a-8f04-f453f3ef1006. The supplied dashboard artwork is preserved in assets/command-center.svg, an SVG container embedding the original JPEG rather than a redrawn illustration.

## Run in BKILLINGS

From the repository root:

```sh
cd SIMULATION/command-center
npm run dev
```

Open port 4173 in your browser. Python 3 and Node are sufficient; no npm installation, external API credentials or network calls are required. For offline use, open index.html directly.

## Validation

```sh
npm run check
npm test
```

The dependency-free DOM harness checks module dialogs, scans, pause/resume, update interval, telemetry, diagnostics and the JSON export handler. It does not replace browser testing. Browser visual QA is pending; see design-qa.md.

## Boundaries

All telemetry, diagnostic outcomes and module capabilities are synthetic. This UI does not connect to the authoritative ledger, market observers, MCP bridge, quantum hardware or production services. Inspect 21 modules, export local event history, adjust the update interval, pause telemetry, or disable the energy pulse.

This package adds a self-contained frontend without modifying existing ledger or security behavior. See ../../docs/DEEPCORE-CONSOLIDATION.md for the discovered work inventory and integration status.
