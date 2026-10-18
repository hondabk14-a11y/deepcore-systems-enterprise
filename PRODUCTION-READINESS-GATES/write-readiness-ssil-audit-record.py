"""Compatibility CLI; implementation lives in an importable module."""
from write_readiness_ssil_audit_record import *  # noqa: F401,F403

if __name__ == "__main__":
    raise SystemExit(main())
