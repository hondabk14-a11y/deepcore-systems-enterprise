#!/bin/bash
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$REPO_ROOT"

EXECUTION_ID="deepcore-verification-$(date -u +%Y%m%dT%H%M%SZ)-$$"
EXECUTED_AT="$(date -u +'%Y-%m-%dT%H:%M:%SZ')"
ACTUAL_COMMIT_SHA="$(git rev-parse HEAD 2>/dev/null || echo unknown)"
BRANCH="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo unknown)"
PYTHON_VERSION="$(python --version 2>&1)"
PYTEST_VERSION="$(python -m pytest --version 2>&1 || echo unavailable)"
RESULTS_FILE="${REPO_ROOT}/verification-results.tsv"
EVIDENCE_FILE="${REPO_ROOT}/verification-results.json"

: > "$RESULTS_FILE"

TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
FAILURES=()

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

record_result() {
    local test_name="$1"
    local status="$2"
    printf '%s\t%s\n' "$status" "$test_name" >> "$RESULTS_FILE"
}

run_test() {
    local test_name="$1"
    local test_cmd="$2"
    local output_file
    local status

    output_file="$(mktemp)"
    echo ""
    echo ">>> Running: $test_name"

    set +e
    bash -o pipefail -c "$test_cmd" > >(tee "$output_file") 2>&1
    status=$?
    set -e

    ((++TOTAL_TESTS))
    if [ "$status" -eq 0 ]; then
        echo -e "${GREEN}✓ PASS${NC}: $test_name"
        ((++PASSED_TESTS))
        record_result "$test_name" "PASS"
    else
        echo -e "${RED}✗ FAIL${NC}: $test_name (exit=$status)"
        ((++FAILED_TESTS))
        FAILURES+=("$test_name")
        record_result "$test_name" "FAIL"
    fi

    rm -f "$output_file"
}

cat <<EOF
==========================================
DeepCore Production Verification Suite
==========================================
Branch: $BRANCH
Commit: $ACTUAL_COMMIT_SHA
Execution ID: $EXECUTION_ID
Date: $EXECUTED_AT
Python: $PYTHON_VERSION
Pytest: $PYTEST_VERSION
==========================================
EOF

# Install dependencies. Installation failures are fatal and are never converted to PASS.
echo "Installing dependencies..."
python -m pip install --disable-pip-version-check --upgrade -q -r requirements.txt
python -m pip install --disable-pip-version-check -q pytest

# PRODUCTION GATE: Event-sourced ledger tests
echo ""
echo "========== PRODUCTION GATE: EVENT-SOURCED LEDGER =========="
cd CORE/event-sourced-ledger
python -m pip install --disable-pip-version-check -q -r requirements-test.txt
run_test "Event-sourced ledger unit tests" "python -m unittest discover -s . -p 'test_*.py' -v"
python -m py_compile ledger.py test_ledger.py
cd ../..

# CORE VERIFICATION SUITE
echo ""
echo "========== CORE VERIFICATION SUITE =========="
run_test "DeepCore reference runtime" "python CORE/deepcore_runtime.py"

# Require the runtime's explicit verification marker in addition to exit code.
if python CORE/deepcore_runtime.py 2>&1 | grep -q 'runtime_status=REFERENCE_IMPLEMENTATION_VERIFIED'; then
    echo "✓ Reference runtime verification marker present"
else
    echo "✗ Reference runtime verification marker missing"
    ((++FAILED_TESTS))
    FAILURES+=("DeepCore reference runtime verification marker")
    record_result "DeepCore reference runtime verification marker" "FAIL"
fi

run_test "DeepCore runtime tests" "python -m pytest -q tests/test_deepcore_runtime.py"
run_test "DeepCore crypto tests" "python -m pytest -q tests/test_deepcore_crypto.py"
run_test "DeepCore consensus tests" "python -m pytest -q tests/test_deepcore_consensus.py"
run_test "DeepCore HotStuff tests" "python -m pytest -q tests/test_deepcore_hotstuff.py"
run_test "DeepCore transport tests" "python -m pytest -q tests/test_deepcore_transport.py"
run_test "DeepCore persistence tests" "python -m pytest -q tests/test_deepcore_persistence.py"
run_test "DeepCore fault injection tests" "python -m pytest -q tests/test_deepcore_fault_injection.py"
run_test "DeepCore key registry tests" "python -m pytest -q tests/test_deepcore_key_registry.py"

# CONSENSUS VERIFICATION
echo ""
echo "========== CONSENSUS VERIFICATION =========="
run_test "DeepCore consensus commitment tests" "python -m pytest -q CORE/test_deepcore_consensus_commitment.py"

# UST/SSIL VERIFICATION
echo ""
echo "========== UST & SSIL VERIFICATION =========="
run_test "UST settlement tests" "python -m pytest -q tests/test_ust_settlement.py"
run_test "UST SSIL gate tests" "python -m pytest -q tests/test_ust_ssil_gate.py"
run_test "UST controller tests" "python -m pytest -q tests/test_ust_controller.py"
run_test "DeepCore SSIL systemic integrity tests" "python -m pytest -q tests/test_deepcore_ssil_systemic_integrity.py"

# MARKET DATA VERIFICATION SUITE
echo ""
echo "========== MARKET DATA VERIFICATION SUITE =========="
run_test "CoinGecko SDK adapter tests" "python -m pytest -q MARKET-DATA/test_coingecko_sdk_adapter.py"
run_test "CoinGecko observation tests" "python -m pytest -q MARKET-DATA/test_coingecko_observation.py"
run_test "Market verification tests" "python -m pytest -q MARKET-DATA/test_market_verification.py"
run_test "Market risk tests" "python -m pytest -q MARKET-DATA/test_market_risk.py"
run_test "Market policy tests" "python -m pytest -q MARKET-DATA/test_market_policy.py"
run_test "Market authorization tests" "python -m pytest -q MARKET-DATA/test_market_authorization.py"
run_test "Ledger admission tests" "python -m pytest -q MARKET-DATA/test_ledger_admission.py"
run_test "Authorization validator tests" "python -m pytest -q MARKET-DATA/test_authorization_validator.py"

# Generate deterministic, machine-readable evidence from the actual execution.
python - "$RESULTS_FILE" "$EVIDENCE_FILE" <<'PY'
import json
import os
import platform
import sys
from datetime import datetime, timezone

results_file, evidence_file = sys.argv[1:]
results = []
with open(results_file, encoding="utf-8") as handle:
    for line in handle:
        status, name = line.rstrip("\n").split("\t", 1)
        results.append({"name": name, "status": status})

passed = sum(item["status"] == "PASS" for item in results)
failed = sum(item["status"] == "FAIL" for item in results)

payload = {
    "schema": "deepcore.verification-results.v1",
    "execution_id": os.environ.get("EXECUTION_ID", ""),
    "executed_at": os.environ.get("EXECUTED_AT", ""),
    "branch": os.environ.get("BRANCH", ""),
    "commit_sha": os.environ.get("ACTUAL_COMMIT_SHA", ""),
    "python": platform.python_version(),
    "platform": platform.platform(),
    "results": results,
    "summary": {
        "total": len(results),
        "passed": passed,
        "failed": failed,
        "overall": "PASS" if failed == 0 and results else "FAIL",
    },
}

with open(evidence_file, "w", encoding="utf-8") as handle:
    json.dump(payload, handle, sort_keys=True, indent=2)
    handle.write("\n")
PY

# Export runtime metadata for the evidence-generation subprocess.
# Rebuild evidence with shell metadata available to Python.
EXECUTION_ID="$EXECUTION_ID" EXECUTED_AT="$EXECUTED_AT" BRANCH="$BRANCH" ACTUAL_COMMIT_SHA="$ACTUAL_COMMIT_SHA" \
python - "$RESULTS_FILE" "$EVIDENCE_FILE" <<'PY'
import json
import os
import platform
import sys

results_file, evidence_file = sys.argv[1:]
results = []
with open(results_file, encoding="utf-8") as handle:
    for line in handle:
        status, name = line.rstrip("\n").split("\t", 1)
        results.append({"name": name, "status": status})

failed = sum(item["status"] == "FAIL" for item in results)
payload = {
    "schema": "deepcore.verification-results.v1",
    "execution_id": os.environ["EXECUTION_ID"],
    "executed_at": os.environ["EXECUTED_AT"],
    "branch": os.environ["BRANCH"],
    "commit_sha": os.environ["ACTUAL_COMMIT_SHA"],
    "python": platform.python_version(),
    "platform": platform.platform(),
    "results": results,
    "summary": {
        "total": len(results),
        "passed": len(results) - failed,
        "failed": failed,
        "overall": "PASS" if failed == 0 and results else "FAIL",
    },
}
with open(evidence_file, "w", encoding="utf-8") as handle:
    json.dump(payload, handle, sort_keys=True, indent=2)
    handle.write("\n")
PY

# SUMMARY
echo ""
echo "=========================================="
echo "VERIFICATION SUITE SUMMARY"
echo "=========================================="
echo "Total tests run: $TOTAL_TESTS"
echo -e "Passed: ${GREEN}$PASSED_TESTS${NC}"
echo -e "Failed: ${RED}$FAILED_TESTS${NC}"
echo "Evidence: $EVIDENCE_FILE"
echo ""

if [ "$FAILED_TESTS" -gt 0 ]; then
    echo "Failed test suites:"
    for failure in "${FAILURES[@]}"; do
        echo "  - $failure"
    done
    exit 1
fi

echo "✓ ALL VERIFICATION SUITES PASSED"
exit 0
