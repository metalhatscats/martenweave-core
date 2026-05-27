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

assert_exit_code() {
    local cmd_desc="$1"
    local code="$2"
    if [ "${code}" -ne 0 ]; then
        echo "ERROR: Command failed: ${cmd_desc}"
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

step "3. Index freshness check"
FRESH_JSON="$(mktemp)"
"${MODELOPS}" index-fresh --repo "${DEMO_REPO}" --json > "${FRESH_JSON}"
assert_json_key "${FRESH_JSON}" "fresh"
rm "${FRESH_JSON}"

step "4. Health report"
"${MODELOPS}" health --repo "${DEMO_REPO}"

step "5. Scorecard"
SCORECARD_JSON="$(mktemp)"
"${MODELOPS}" scorecard --repo "${DEMO_REPO}" --json > "${SCORECARD_JSON}"
assert_json_key "${SCORECARD_JSON}" "readiness_level"
assert_json_key "${SCORECARD_JSON}" "evidence_coverage"
assert_json_key "${SCORECARD_JSON}" "sap_table_coverage"
rm "${SCORECARD_JSON}"

step "6. Gap report"
GAP_JSON="$(mktemp)"
"${MODELOPS}" gap-report --repo "${DEMO_REPO}" --json > "${GAP_JSON}"
assert_json_key "${GAP_JSON}" "total_gap_count"
assert_json_key "${GAP_JSON}" "gap_score"
rm "${GAP_JSON}"

step "7. Owners report"
OWNERS_JSON="$(mktemp)"
"${MODELOPS}" owners --repo "${DEMO_REPO}" --json > "${OWNERS_JSON}"
assert_json_key "${OWNERS_JSON}" "owners"
assert_json_key "${OWNERS_JSON}" "coverage_percent"
assert_json_key "${OWNERS_JSON}" "orphaned_objects"
rm "${OWNERS_JSON}"

step "8. Decisions list"
"${MODELOPS}" decisions list --repo "${DEMO_REPO}"

step "9. Decisions report"
DECISIONS_JSON="$(mktemp)"
"${MODELOPS}" decisions report --repo "${DEMO_REPO}" --json > "${DECISIONS_JSON}"
assert_json_key "${DECISIONS_JSON}" "evidence_coverage"
assert_json_key "${DECISIONS_JSON}" "uncovered_decisions"
assert_json_key "${DECISIONS_JSON}" "category_breakdown"
rm "${DECISIONS_JSON}"

step "10. Proposal report"
"${MODELOPS}" proposal report --repo "${DEMO_REPO}"

step "11. Audit log"
"${MODELOPS}" audit-log --repo "${DEMO_REPO}" --json

# ---------------------------------------------------------------------------
# Discovery, Trace, and Export Surface
# ---------------------------------------------------------------------------

step "12. Impact analysis (FieldEndpoint)"
IMPACT_JSON="$(mktemp)"
"${MODELOPS}" impact FEP-S4-KNVV-KDGRP --repo "${DEMO_REPO}" --json > "${IMPACT_JSON}"
assert_json_key "${IMPACT_JSON}" "root_object_id"
assert_json_key "${IMPACT_JSON}" "affected_objects"
rm "${IMPACT_JSON}"

step "13. Trace lineage (Attribute)"
TRACE_JSON="$(mktemp)"
"${MODELOPS}" trace ATTR-CUST-SALES-CUSTOMER-GROUP --repo "${DEMO_REPO}" --json > "${TRACE_JSON}"
assert_json_key "${TRACE_JSON}" "root_object_id"
assert_json_key "${TRACE_JSON}" "nodes"
assert_json_key "${TRACE_JSON}" "edges"
rm "${TRACE_JSON}"

step "14. Search"
SEARCH_JSON="$(mktemp)"
"${MODELOPS}" search "Customer Group" --repo "${DEMO_REPO}" --json > "${SEARCH_JSON}"
assert_json_key "${SEARCH_JSON}" "object_id"
rm "${SEARCH_JSON}"

step "15. Query by type"
QUERY_JSON="$(mktemp)"
"${MODELOPS}" query --type Attribute --repo "${DEMO_REPO}" --json > "${QUERY_JSON}"
assert_json_key "${QUERY_JSON}" "object_id"
rm "${QUERY_JSON}"

step "16. Diff (smoke test against self)"
DIFF_JSON="$(mktemp)"
"${MODELOPS}" diff "${DEMO_REPO}" "${DEMO_REPO}" --json > "${DIFF_JSON}"
assert_json_key "${DIFF_JSON}" "has_changes"
rm "${DIFF_JSON}"

step "17. Export model (CSV)"
"${MODELOPS}" export-model --repo "${DEMO_REPO}" --format csv

step "18. Export model (XLSX)"
"${MODELOPS}" export-model --repo "${DEMO_REPO}" --format xlsx

step "19. Clean dry-run"
"${MODELOPS}" clean --repo "${DEMO_REPO}" --dry-run

step "20. Build static docs"
"${MODELOPS}" docs-build --repo "${DEMO_REPO}"

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
echo "  Index Fresh: OK"
echo "  Scorecard:   OK"
echo "  Gap Report:  OK"
echo "  Owners:      OK"
echo "  Decisions:   OK"
echo "  Impact:      OK"
echo "  Trace:       OK"
echo "  Search:      OK"
echo "  Query:       OK"
echo "  Diff:        OK"
echo "  Export:      OK"
echo "  Clean:       OK"
echo "  Docs Build:  OK"
echo "  Audit Log:   OK"
echo "=========================================="
