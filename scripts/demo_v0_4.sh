#!/usr/bin/env bash
# Acceptance demo for Martenweave v0.4 operational readiness features.
# Runs end-to-end without external services.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
MODELOPS="${REPO_ROOT}/.venv/bin/modelops"
DEMO_REPO="${REPO_ROOT}/examples/customer_bp_model"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

step() {
    echo ""
    echo "===> $1"
}

assert_json_key() {
    local file="$1"
    local key="$2"
    if ! grep -q "\"${key}\"" "${file}"; then
        echo "ERROR: Missing key '${key}' in ${file}"
        exit 1
    fi
}

# ---------------------------------------------------------------------------
# v0.4 Operational Readiness Workflow
# ---------------------------------------------------------------------------

step "1. Validate canonical model (with decision checks)"
"${MODELOPS}" validate --repo "${DEMO_REPO}" --check-decisions

step "2. Build index"
"${MODELOPS}" build-index --repo "${DEMO_REPO}" --jsonl

step "3. Health report"
"${MODELOPS}" health --repo "${DEMO_REPO}"

step "4. Scorecard"
SCORECARD_JSON="$(mktemp)"
"${MODELOPS}" scorecard --repo "${DEMO_REPO}" --json > "${SCORECARD_JSON}"
assert_json_key "${SCORECARD_JSON}" "readiness_level"
assert_json_key "${SCORECARD_JSON}" "evidence_coverage"
assert_json_key "${SCORECARD_JSON}" "sap_table_coverage"
rm "${SCORECARD_JSON}"

step "5. Gap report"
GAP_JSON="$(mktemp)"
"${MODELOPS}" gap-report --repo "${DEMO_REPO}" --json > "${GAP_JSON}"
assert_json_key "${GAP_JSON}" "total_gap_count"
assert_json_key "${GAP_JSON}" "gap_score"
rm "${GAP_JSON}"

step "6. Owners report"
OWNERS_JSON="$(mktemp)"
"${MODELOPS}" owners --repo "${DEMO_REPO}" --json > "${OWNERS_JSON}"
assert_json_key "${OWNERS_JSON}" "owners"
assert_json_key "${OWNERS_JSON}" "coverage_percent"
assert_json_key "${OWNERS_JSON}" "orphaned_objects"
rm "${OWNERS_JSON}"

step "7. Decisions list"
"${MODELOPS}" decisions list --repo "${DEMO_REPO}"

step "8. Decisions report"
DECISIONS_JSON="$(mktemp)"
"${MODELOPS}" decisions report --repo "${DEMO_REPO}" --json > "${DECISIONS_JSON}"
assert_json_key "${DECISIONS_JSON}" "evidence_coverage"
assert_json_key "${DECISIONS_JSON}" "uncovered_decisions"
assert_json_key "${DECISIONS_JSON}" "category_breakdown"
rm "${DECISIONS_JSON}"

step "9. Proposal report"
"${MODELOPS}" proposal report --repo "${DEMO_REPO}"

step "10. Audit log"
"${MODELOPS}" audit-log --repo "${DEMO_REPO}" --json

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

echo ""
echo "=========================================="
echo "  Martenweave v0.4 Demo Complete"
echo "=========================================="
echo "  Repo:        ${DEMO_REPO}"
echo "  Validation:  PASS"
echo "  Index:       BUILT"
echo "  Scorecard:   OK"
echo "  Gap Report:  OK"
echo "  Owners:      OK"
echo "  Decisions:   OK"
echo "  Audit Log:   OK"
echo "=========================================="
