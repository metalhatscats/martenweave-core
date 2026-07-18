#!/usr/bin/env bash
# Release smoke checks for Martenweave Core.
#
# This script exercises the public CLI against the bundled examples using JSON
# assertions where stable contracts exist. It intentionally writes only ignored
# generated artifacts under example repositories and temporary files under /tmp.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
DEFAULT_MODELOPS="${REPO_ROOT}/.venv/bin/modelops"
MODELOPS="${MODELOPS:-}"
SMOKE_DIR="$(mktemp -d)"

cleanup() {
    rm -rf "${SMOKE_DIR}"
}
trap cleanup EXIT

require_tool() {
    local tool="$1"
    if ! command -v "${tool}" >/dev/null 2>&1; then
        echo "FAIL: required tool not found: ${tool}"
        exit 1
    fi
}

run_step() {
    echo "SMOKE $*"
}

assert_jq() {
    local file="$1"
    local expression="$2"
    if ! jq -e "${expression}" "${file}" >/dev/null; then
        echo "FAIL: assertion failed for ${file}: ${expression}"
        cat "${file}"
        exit 1
    fi
}

require_tool jq
require_tool npm

if [[ -z "${MODELOPS}" ]]; then
    if [[ -x "${DEFAULT_MODELOPS}" ]]; then
        MODELOPS="${DEFAULT_MODELOPS}"
    elif command -v modelops >/dev/null 2>&1; then
        MODELOPS="$(command -v modelops)"
    else
        echo "FAIL: modelops not found or not executable"
        echo "Run: python -m venv .venv && .venv/bin/python -m pip install -e '.[dev]'"
        exit 1
    fi
elif [[ ! -x "${MODELOPS}" ]]; then
    if command -v "${MODELOPS}" >/dev/null 2>&1; then
        MODELOPS="$(command -v "${MODELOPS}")"
    else
        echo "FAIL: ${MODELOPS} not found or not executable"
        echo "Run: python -m venv .venv && .venv/bin/python -m pip install -e '.[dev]'"
        exit 1
    fi
fi

cd "${REPO_ROOT}"

for repo in \
    examples/simple_product_model \
    examples/customer_bp_model \
    examples/supplier_vendor_model \
    examples/generic_product_model \
    examples/sap_bp_customer_vendor_reference \
    examples/synthetic_customer_migration_demo \
    examples/synthetic_enterprise_portfolio_demo \
    examples/northstar_mobility_pilot
do
    repo_name="$(basename "${repo}")"

    run_step "validate ${repo}"
    "${MODELOPS}" validate --repo "${repo}" --json >"${SMOKE_DIR}/${repo_name}-validate.json"
    assert_jq "${SMOKE_DIR}/${repo_name}-validate.json" '.is_valid == true'

    run_step "build-index ${repo}"
    "${MODELOPS}" build-index --repo "${repo}" --jsonl --json \
        >"${SMOKE_DIR}/${repo_name}-build.json"
    assert_jq "${SMOKE_DIR}/${repo_name}-build.json" \
        '.valid == true and .objects_count >= 1'

    run_step "index-fresh ${repo}"
    "${MODELOPS}" index-fresh --repo "${repo}" --json \
        >"${SMOKE_DIR}/${repo_name}-fresh.json"
    assert_jq "${SMOKE_DIR}/${repo_name}-fresh.json" '.fresh == true'

    run_step "health ${repo}"
    "${MODELOPS}" health --repo "${repo}" --json >"${SMOKE_DIR}/${repo_name}-health.json"
    assert_jq "${SMOKE_DIR}/${repo_name}-health.json" \
        '.object_count >= 1 and (.index_fresh | type == "boolean")'

    run_step "scorecard ${repo}"
    "${MODELOPS}" scorecard --repo "${repo}" --json \
        >"${SMOKE_DIR}/${repo_name}-scorecard.json"
    assert_jq "${SMOKE_DIR}/${repo_name}-scorecard.json" \
        '.object_count >= 1 and (.metrics | type == "array")'
done

run_step "search customer_bp_model"
"${MODELOPS}" search "Customer Group" --repo examples/customer_bp_model --json \
    >"${SMOKE_DIR}/customer-search.json"
assert_jq "${SMOKE_DIR}/customer-search.json" '.results | length >= 1'

run_step "query customer_bp_model"
"${MODELOPS}" query --type Attribute --repo examples/customer_bp_model --json \
    >"${SMOKE_DIR}/customer-query.json"
assert_jq "${SMOKE_DIR}/customer-query.json" '.results | length >= 1'

run_step "trace customer_bp_model"
"${MODELOPS}" trace ATTR-CUST-SALES-CUSTOMER-GROUP --repo examples/customer_bp_model --json \
    >"${SMOKE_DIR}/customer-trace.json"
assert_jq "${SMOKE_DIR}/customer-trace.json" \
    '.root_object_id == "ATTR-CUST-SALES-CUSTOMER-GROUP" and (.nodes | length >= 1)'

run_step "impact customer_bp_model"
"${MODELOPS}" impact FEP-S4-KNVV-KDGRP --repo examples/customer_bp_model --json \
    >"${SMOKE_DIR}/customer-impact.json"
assert_jq "${SMOKE_DIR}/customer-impact.json" \
    '.root_object_id == "FEP-S4-KNVV-KDGRP" and (.affected_objects | type == "array")'

run_step "gaps customer_bp_model"
"${MODELOPS}" gaps examples/customer_bp_model/data/samples/customer_sales_area_sample.csv \
    --repo examples/customer_bp_model --check-model --json \
    >"${SMOKE_DIR}/customer-gaps.json"
assert_jq "${SMOKE_DIR}/customer-gaps.json" \
    '.coverage.total_columns >= 1 and (.gaps | type == "array") and (.matches | type == "array")'

run_step "gap-report customer_bp_model"
"${MODELOPS}" gap-report --repo examples/customer_bp_model --json \
    >"${SMOKE_DIR}/customer-gap-report.json"
assert_jq "${SMOKE_DIR}/customer-gap-report.json" \
    '.total_gap_count >= 0 and (.gaps_by_type | type == "object")'

run_step "risk-report customer_bp_model"
"${MODELOPS}" risk-report --repo examples/customer_bp_model --json \
    >"${SMOKE_DIR}/customer-risk-report.json"
assert_jq "${SMOKE_DIR}/customer-risk-report.json" \
    '(.risk_items | type == "array") and .repo_name != null and .generated_at != null'

run_step "review-pack create customer_bp_model"
"${MODELOPS}" review-pack create --repo examples/customer_bp_model --out "${SMOKE_DIR}/review-pack" --json \
    >"${SMOKE_DIR}/customer-review-pack.json"
assert_jq "${SMOKE_DIR}/customer-review-pack.json" \
    '(.artifacts | length == 6) and .artifact_count == 6'

run_step "docs-build local viewer customer_bp_model"
VIEWER_DIR="${SMOKE_DIR}/customer-viewer"
"${MODELOPS}" docs-build --repo examples/customer_bp_model --site "${VIEWER_DIR}" --json \
    >"${SMOKE_DIR}/customer-viewer.json"
assert_jq "${SMOKE_DIR}/customer-viewer.json" \
    '.files | index("index.html") and index("objects.html") and index("gaps.html")'
assert_jq "${SMOKE_DIR}/customer-viewer.json" \
    '.files | index("decisions.html") and index("owners.html") and index("search-index.json")'
assert_jq "${SMOKE_DIR}/customer-viewer.json" \
    '.viewer_manifest.product_boundary.local_static_read_only == true'
test -f "${VIEWER_DIR}/assets/viewer.css"
test -f "${VIEWER_DIR}/assets/viewer.js"
test -f "${VIEWER_DIR}/objects/fep-s4-knvv-kdgrp.html"
grep -q "Customer Group" "${VIEWER_DIR}/search-index.json"
grep -q "KNVV" "${VIEWER_DIR}/search-index.json"
grep -q "KDGRP" "${VIEWER_DIR}/search-index.json"

run_step "propose-patch dry-run customer_bp_model"
cat >"${SMOKE_DIR}/note.md" <<'NOTE'
Update CUSTOMER GROUP mapping for KNVV-KDGRP based on the CH01-A17 decision.
Keep the change as a reviewable PatchProposal.
NOTE
"${MODELOPS}" propose-patch --from "${SMOKE_DIR}/note.md" \
    --repo examples/customer_bp_model --dry-run --json \
    >"${SMOKE_DIR}/proposal.json"
assert_jq "${SMOKE_DIR}/proposal.json" \
    '.dry_run == true and .is_safe == true and .proposal.id == "PP-SCAFFOLD-001"'

run_step "config-guard release mode"
"${MODELOPS}" config-guard --repo . --mode release --json \
    >"${SMOKE_DIR}/config-guard-release.json"
assert_jq "${SMOKE_DIR}/config-guard-release.json" 'type == "object"'

run_step "northstar synthetic pilot reproduction"
bash "${SCRIPT_DIR}/demo_northstar_pilot.sh"

run_step "frontend tests"
cd "${REPO_ROOT}/frontend"
if [[ ! -x node_modules/.bin/vitest ]]; then
    npm ci
fi
npm test

echo "Release smoke checks passed"
