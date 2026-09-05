# DeepCore Source Recovery Gate

Before any historical package is promoted into `src/` or deployment paths, run:

1. secret scan
2. dependency audit
3. unit and contract tests
4. security tests
5. static analysis
6. deterministic replay checks
7. integration tests
8. deployment dry run

Only then may the implementation be considered for production-readiness review.
