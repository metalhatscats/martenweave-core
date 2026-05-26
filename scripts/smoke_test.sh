#!/usr/bin/env bash
# One-command smoke test for Martenweave Core v0.4.
# Runs full CLI workflow on a temp repo with stable JSON assertions.
# Fails if any command returns unexpected JSON structure.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
MODELOPS="${REPO_ROOT}/.venv/bin/modelops"
DEMO_REPO="$(mktemp -d)"

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
    local type="${3:-string}"

    if ! jq -e "${key}" "${file}" >/dev/null 2>&1; then
        echo "FAIL: missing key ${key} in ${file}"
        cat "${file}"
        exit 1
    fi

    if [[ "${type}" == "number" ]]; then
        if ! jq -e "${key} | type == \"number\"" "${file}" >/dev/null 2>&1; then
            echo "FAIL: ${key} is not a number in ${file}"
            exit 1
        fi
    elif [[ "${type}" == "boolean" ]]; then
        if ! jq -e "${key} | type == \"boolean\"" "${file}" >/dev/null 2>&1; then
            echo "FAIL: ${key} is not a boolean in ${file}"
            exit 1
        fi
    elif [[ "${type}" == "array" ]]; then
        if ! jq -e "${key} | type == \"array\"" "${file}" >/dev/null 2>&1; then
            echo "FAIL: ${key} is not an array in ${file}"
            exit 1
        fi
    elif [[ "${type}" == "object" ]]; then
        if ! jq -e "${key} | type == \"object\"" "${file}" >/dev/null 2>&1; then
            echo "FAIL: ${key} is not an object in ${file}"
            exit 1
        fi
    fi
}

cleanup() {
    rm -rf "${DEMO_REPO}"
}
trap cleanup EXIT

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

step "Initializing temp repository"
"${MODELOPS}" init "${DEMO_REPO}"

# ---------------------------------------------------------------------------
# Core workflow with JSON assertions
# ---------------------------------------------------------------------------

step "1. validate --json"
"${MODELOPS}" validate --repo "${DEMO_REPO}" --json >"${DEMO_REPO}/out_validate.json"
assert_json_key "${DEMO_REPO}/out_validate.json" ".is_valid" boolean
assert_json_key "${DEMO_REPO}/out_validate.json" ".error_count" number
assert_json_key "${DEMO_REPO}/out_validate.json" ".warning_count" number
assert_json_key "${DEMO_REPO}/out_validate.json" ".info_count" number
assert_json_key "${DEMO_REPO}/out_validate.json" ".results" array

step "2. build-index --jsonl"
"${MODELOPS}" build-index --repo "${DEMO_REPO}" --jsonl
if [[ ! -f "${DEMO_REPO}/generated/modelops.db" ]]; then
    echo "FAIL: modelops.db not created"
    exit 1
fi
if [[ ! -f "${DEMO_REPO}/generated/search_documents.jsonl" ]]; then
    echo "FAIL: search_documents.jsonl not created"
    exit 1
fi
if [[ ! -f "${DEMO_REPO}/generated/lineage_edges.jsonl" ]]; then
    echo "FAIL: lineage_edges.jsonl not created"
    exit 1
fi

step "3. health --json"
"${MODELOPS}" health --repo "${DEMO_REPO}" --json >"${DEMO_REPO}/out_health.json"
assert_json_key "${DEMO_REPO}/out_health.json" ".object_count" number
assert_json_key "${DEMO_REPO}/out_health.json" ".index_fresh" boolean
assert_json_key "${DEMO_REPO}/out_health.json" ".coverage_gaps" object
assert_json_key "${DEMO_REPO}/out_health.json" ".ownership_coverage" object
assert_json_key "${DEMO_REPO}/out_health.json" ".data_quality_coverage" object

step "4. scorecard --json"
"${MODELOPS}" scorecard --repo "${DEMO_REPO}" --json >"${DEMO_REPO}/out_scorecard.json"
assert_json_key "${DEMO_REPO}/out_scorecard.json" ".repo_name"
assert_json_key "${DEMO_REPO}/out_scorecard.json" ".readiness_level"
assert_json_key "${DEMO_REPO}/out_scorecard.json" ".object_count" number
assert_json_key "${DEMO_REPO}/out_scorecard.json" ".metrics" array
assert_json_key "${DEMO_REPO}/out_scorecard.json" ".summary"

step "5. analyze --json"
"${MODELOPS}" analyze --repo "${DEMO_REPO}" --json >"${DEMO_REPO}/out_analyze.json"
assert_json_key "${DEMO_REPO}/out_analyze.json" ".object_count" number
assert_json_key "${DEMO_REPO}/out_analyze.json" ".type_counts" object
assert_json_key "${DEMO_REPO}/out_analyze.json" ".orphan_fields" object
assert_json_key "${DEMO_REPO}/out_analyze.json" ".attribute_coverage" object
assert_json_key "${DEMO_REPO}/out_analyze.json" ".lifecycle_summary" object

step "6. trace --json"
"${MODELOPS}" trace DOMAIN-EXAMPLE --repo "${DEMO_REPO}" --json >"${DEMO_REPO}/out_trace.json"
assert_json_key "${DEMO_REPO}/out_trace.json" ".root_object_id"
assert_json_key "${DEMO_REPO}/out_trace.json" ".root_object_type"
assert_json_key "${DEMO_REPO}/out_trace.json" ".nodes" array
assert_json_key "${DEMO_REPO}/out_trace.json" ".edges" array

step "7. impact --json"
"${MODELOPS}" impact DOMAIN-EXAMPLE --repo "${DEMO_REPO}" --json >"${DEMO_REPO}/out_impact.json"
assert_json_key "${DEMO_REPO}/out_impact.json" ".root_object_id"
assert_json_key "${DEMO_REPO}/out_impact.json" ".affected_objects" array

step "8. audit-log --json"
"${MODELOPS}" audit-log --repo "${DEMO_REPO}" --json >"${DEMO_REPO}/out_audit.json"
# audit log returns a JSON array; verify it parses and is a list
if ! jq -e 'type == "array"' "${DEMO_REPO}/out_audit.json" >/dev/null 2>&1; then
    echo "FAIL: audit-log output is not a JSON array"
    cat "${DEMO_REPO}/out_audit.json"
    exit 1
fi

step "9. clean --dry-run --json"
"${MODELOPS}" clean --repo "${DEMO_REPO}" --dry-run --json >"${DEMO_REPO}/out_clean.json"
assert_json_key "${DEMO_REPO}/out_clean.json" ".dry_run" boolean
assert_json_key "${DEMO_REPO}/out_clean.json" ".generated_path"
assert_json_key "${DEMO_REPO}/out_clean.json" ".skipped_count" number

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

echo ""
echo "=========================================="
echo "  Smoke Test Complete — All JSON contracts stable"
echo "=========================================="
echo "  Repo:        ${DEMO_REPO}"
echo "  Commands:    9"
echo "  Assertions:  35+"
echo "=========================================="
