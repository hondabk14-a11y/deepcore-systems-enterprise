# DeepCore Production Gate

The automated production gate is installed. It runs on pushes to `main`, pull requests targeting `main`, and manual dispatch. It validates the event-sourced ledger tests, Python compilation, tracked-secret detection, and required repository controls.

A successful run is required evidence for these checks. It is not a claim that the entire distributed production deployment is certified.