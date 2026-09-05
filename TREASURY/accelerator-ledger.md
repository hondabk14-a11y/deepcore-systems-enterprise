# Treasury Accelerator Ledger

The accelerator interface is modeled as an event-sourced treasury component with reconciliation and SSIL controls.

Reference event shape:

- Event type: `ACCELERATOR_TOPUP`
- Treasury account: `treasury_001`
- Amount and resulting balance are recorded as ledger events
- Processing timestamp and event timestamp are retained
- Previous and consensus hashes bind the event into the audit chain

The repository records architecture only. Real account identifiers, credentials, signing keys, and live transaction secrets must never be committed.