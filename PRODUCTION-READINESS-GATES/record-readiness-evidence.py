"""Compatibility CLI; implementation lives in an importable module."""
from record_readiness_evidence import *  # noqa: F401,F403

if __name__ == "__main__":
    raise SystemExit(main())
