"""Tests for the fail-closed ledger admission boundary."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent


def _load(name: str):
    path = ROOT / name
    spec = importlib.util.spec_from_file_location(name.removesuffix(".py"), path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


ledger_admission = _load("ledger_admission.py")


class Request:
    policy_decision = "ALLOW"
    action = "market.execute"
    risk_assessment_hash = "risk-hash"

    def __init__(self):
        self.request_hash = ledger_admission.canonical_hash(self.canonical_dict())

    def canonical_dict(self):
        return {
            "policy_decision": self.policy_decision,
            "action": self.action,
            "risk_assessment_hash": self.risk_assessment_hash,
        }


class Validation:
    valid = True
    request_hash = Request().request_hash


def _admit(request=None, validation=None):
    request = request or Request()
    validation = validation or Validation()
    return ledger_admission.admit_authorized_request(
        request,
        validation,
        expected_action="market.execute",
        expected_risk_hash="risk-hash",
    )


def test_valid_request_is_admitted_only_after_authorization():
    result = _admit()
    assert result.admitted is True
    assert result.reason == "request admitted to consensus"


def test_failed_authorization_is_rejected():
    validation = Validation()
    validation.valid = False
    result = _admit(validation=validation)
    assert result.admitted is False


@pytest.mark.parametrize("field,value", [
    ("policy_decision", "REVIEW"),
    ("policy_decision", "ESCALATE"),
    ("policy_decision", "BLOCK"),
])
def test_non_allow_policy_is_rejected(field, value):
    request = Request()
    setattr(request, field, value)
    result = _admit(request=request)
    assert result.admitted is False


def test_action_mismatch_is_rejected():
    request = Request()
    request.action = "ledger.transfer"
    assert _admit(request=request).admitted is False


def test_risk_evidence_mismatch_is_rejected():
    request = Request()
    request.risk_assessment_hash = "other-risk-hash"
    assert _admit(request=request).admitted is False


def test_validation_hash_mismatch_is_rejected():
    validation = Validation()
    validation.request_hash = "different"
    assert _admit(validation=validation).admitted is False


def test_admission_does_not_create_signature_or_private_key_material():
    result = _admit()
    assert result.admitted is True
    assert not hasattr(result, "signature")
    assert not hasattr(result, "private_key")
