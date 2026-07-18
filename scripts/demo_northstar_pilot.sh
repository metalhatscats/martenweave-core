#!/usr/bin/env bash
# Northstar Mobility Group — Synthetic Pilot: one-command reproduction.
#
# Runs the full pilot workflow against examples/northstar_mobility_pilot:
#   1. validate          2. build-index        3. dataset profiling
#   4. gap detection     5. health/scorecard   6. search/query
#   7. trace/impact      8. readiness gates    9. propose-patch
#  10. issue draft + git bundle               11. workbench instructions
#
# The canonical model is expected to stay valid; the intentional pilot problems
# surface through gaps, readiness blockers, and proposals. The script writes
# only ignored generated artifacts under the example repository and temporary
# files under a mktemp directory.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
PILOT_REPO="${REPO_ROOT}/examples/northstar_mobility_pilot"
DEFAULT_MODELOPS="${REPO_ROOT}/.venv/bin/martenweave"
MODELOPS="${MODELOPS:-}"
DEMO_DIR="$(mktemp -d)"

cleanup() {
    rm -rf "${DEMO_DIR}"
}
trap cleanup EXIT

require_tool() {
    local tool="$1"
    if ! command -v "${tool}" >/dev/null 2>&1; then
        echo "FAIL: required tool not found: ${tool}"
        exit 1
    fi
}

step() {
    echo ""
    echo "=== STEP $*"
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

if [[ -z "${MODELOPS}" ]]; then
    if [[ -x "${DEFAULT_MODELOPS}" ]]; then
        MODELOPS="${DEFAULT_MODELOPS}"
    elif command -v martenweave >/dev/null 2>&1; then
        MODELOPS="$(command -v martenweave)"
    else
        echo "FAIL: martenweave CLI not found or not executable"
        echo "Run: python -m venv .venv && .venv/bin/python -m pip install -e '.[dev]'"
        exit 1
    fi
fi

cd "${REPO_ROOT}"
REL_REPO="examples/northstar_mobility_pilot"

step "1/11 validate — canonical model must stay valid (0 errors)"
"${MODELOPS}" validate --repo "${REL_REPO}" --json >"${DEMO_DIR}/validate.json"
assert_jq "${DEMO_DIR}/validate.json" '.is_valid == true and .error_count == 0'
echo "valid; intentional warnings: $(jq '.warning_count' "${DEMO_DIR}/validate.json")"

step "2/11 build-index — disposable SQLite index + JSONL exports"
"${MODELOPS}" build-index --repo "${REL_REPO}" --jsonl --json >"${DEMO_DIR}/build.json"
assert_jq "${DEMO_DIR}/build.json" '.valid == true and .objects_count >= 150'
echo "indexed objects: $(jq '.objects_count' "${DEMO_DIR}/build.json")"

step "3/11 profile-dataset — profile all seven synthetic extracts"
for dataset in "${PILOT_REPO}"/data/samples/*; do
    name="$(basename "${dataset}")"
    "${MODELOPS}" profile-dataset "${dataset}" --repo "${REL_REPO}" --json \
        >"${DEMO_DIR}/profile-${name}.json"
    # CSV profiles are single objects; XLSX profiles nest sheets with row_count.
    assert_jq "${DEMO_DIR}/profile-${name}.json" \
        '(if type == "array" then .[0].row_count elif has("sheets") then .sheets[0].row_count else .row_count end) >= 1'
    rows="$(jq 'if type == "array" then .[0].row_count elif has("sheets") then .sheets[0].row_count else .row_count end' \
        "${DEMO_DIR}/profile-${name}.json")"
    echo "profiled ${name}: ${rows} rows"
done

step "4/11 gap detection — intentional dataset problems surface"
"${MODELOPS}" gaps "${REL_REPO}/data/samples/northstar_crm_sales_orders.csv" \
    --repo "${REL_REPO}" --check-model --json >"${DEMO_DIR}/gaps-orders.json"
assert_jq "${DEMO_DIR}/gaps-orders.json" \
    '[.gaps[].gap_code] | index("UNMODELED_DATASET_COLUMN") != null'
echo "sales orders gaps: $(jq '.gaps | length' "${DEMO_DIR}/gaps-orders.json") (missing net_value column)"
"${MODELOPS}" gaps "${REL_REPO}/data/samples/voyager_materials.csv" \
    --repo "${REL_REPO}" --check-model --json >"${DEMO_DIR}/gaps-materials.json"
assert_jq "${DEMO_DIR}/gaps-materials.json" \
    '[.gaps[].gap_code] | index("UNMODELED_DATASET_COLUMN") != null'
echo "materials gaps: $(jq '.gaps | length' "${DEMO_DIR}/gaps-materials.json") (invalid s4_material_type codes)"
"${MODELOPS}" gap-report --repo "${REL_REPO}" --json >"${DEMO_DIR}/gap-report.json"
assert_jq "${DEMO_DIR}/gap-report.json" '.total_gap_count >= 1'
echo "gap report total: $(jq '.total_gap_count' "${DEMO_DIR}/gap-report.json")"

step "5/11 health + scorecard — ownership coverage and readiness metrics"
"${MODELOPS}" health --repo "${REL_REPO}" --json >"${DEMO_DIR}/health.json"
assert_jq "${DEMO_DIR}/health.json" '.object_count >= 150'
echo "health objects: $(jq '.object_count' "${DEMO_DIR}/health.json")"
"${MODELOPS}" scorecard --repo "${REL_REPO}" --json >"${DEMO_DIR}/scorecard.json"
assert_jq "${DEMO_DIR}/scorecard.json" '.object_count >= 150 and (.metrics | type == "array")'
echo "scorecard computed (review status expected: not ready)"

step "6/11 search + query — cross-domain discovery"
"${MODELOPS}" search "payment terms" --repo "${REL_REPO}" --json >"${DEMO_DIR}/search.json"
assert_jq "${DEMO_DIR}/search.json" '.results | length >= 3'
echo "search hits for 'payment terms': $(jq '.results | length' "${DEMO_DIR}/search.json")"
"${MODELOPS}" query --type Attribute --repo "${REL_REPO}" --json >"${DEMO_DIR}/query.json"
assert_jq "${DEMO_DIR}/query.json" '.results | length >= 10'
echo "attributes: $(jq '.results | length' "${DEMO_DIR}/query.json")"

step "7/11 trace + impact — cross-domain blast radius of shared attributes"
"${MODELOPS}" trace ATTR-SHARED-PAYMENT-TERMS --repo "${REL_REPO}" --json \
    >"${DEMO_DIR}/trace.json"
assert_jq "${DEMO_DIR}/trace.json" \
    '.root_object_id == "ATTR-SHARED-PAYMENT-TERMS" and (.nodes | length >= 10)'
echo "trace nodes (Supplier + Procurement + Finance): $(jq '.nodes | length' "${DEMO_DIR}/trace.json")"
"${MODELOPS}" impact ATTR-SHARED-PAYMENT-TERMS --repo "${REL_REPO}" --json \
    >"${DEMO_DIR}/impact-payterms.json"
assert_jq "${DEMO_DIR}/impact-payterms.json" '.affected_objects | length >= 10'
echo "impact of payment terms change: $(jq '.affected_objects | length' "${DEMO_DIR}/impact-payterms.json") objects"
"${MODELOPS}" impact ATTR-SHARED-CUSTOMER-CREDIT-LIMIT --repo "${REL_REPO}" --json \
    >"${DEMO_DIR}/impact-credit.json"
assert_jq "${DEMO_DIR}/impact-credit.json" '.affected_objects | length >= 10'
echo "impact of credit limit change: $(jq '.affected_objects | length' "${DEMO_DIR}/impact-credit.json") objects"

step "8/11 readiness — pilot gates must fail on the intentional problems"
set +e
"${MODELOPS}" readiness --repo "${REL_REPO}" --dry-run --json >"${DEMO_DIR}/readiness.json"
readiness_exit=$?
set -e
if [[ ${readiness_exit} -eq 0 ]]; then
    echo "FAIL: readiness unexpectedly passed; the intentional pilot problems did not surface"
    exit 1
fi
assert_jq "${DEMO_DIR}/readiness.json" \
    '.ready == false and (.failed_gates | index("active_object_missing_owner") != null)'
echo "readiness gates failed as intended: $(jq -r '.failed_gates | join(", ")' "${DEMO_DIR}/readiness.json")"

step "9/11 propose-patch — no silent mutation without an AI provider"
set +e
"${MODELOPS}" propose-patch --from "${REL_REPO}/data/patch_notes/sales_net_value_note.md" \
    --repo "${REL_REPO}" --dry-run --json >"${DEMO_DIR}/propose.json"
propose_exit=$?
set -e
if [[ ${propose_exit} -eq 0 ]]; then
    # An AI provider is configured: a reviewable proposal was drafted.
    assert_jq "${DEMO_DIR}/propose.json" '.proposal != null'
    echo "AI provider configured: drafted $(jq -r '.proposal.id' "${DEMO_DIR}/propose.json") for human review"
else
    # Deterministic no-provider behavior: refuse to guess instead of mutating.
    assert_jq "${DEMO_DIR}/propose.json" '.proposal == null and (.assumptions | length >= 1)'
    echo "no AI provider: scaffold refused to guess (no silent mutation) — expected"
fi

step "10/11 issue draft + git bundle — GitHub-ready review artifacts"
"${MODELOPS}" issue-draft create --proposal PP-NORTHSTAR-NET-VALUE-VALIDATION-001 \
    --repo "${REL_REPO}" --json >"${DEMO_DIR}/issue-draft.json"
assert_jq "${DEMO_DIR}/issue-draft.json" '.source_id == "PP-NORTHSTAR-NET-VALUE-VALIDATION-001"'
echo "issue draft: $(jq -r '.title' "${DEMO_DIR}/issue-draft.json")"
"${MODELOPS}" git-bundle PP-NORTHSTAR-NET-VALUE-VALIDATION-001 \
    --repo "${REL_REPO}" --json >"${DEMO_DIR}/git-bundle.json"
assert_jq "${DEMO_DIR}/git-bundle.json" \
    '.proposal_id == "PP-NORTHSTAR-NET-VALUE-VALIDATION-001" and (.files | length >= 1)'
echo "git bundle: $(jq '.files | length' "${DEMO_DIR}/git-bundle.json") files under $(jq -r '.bundle_dir' "${DEMO_DIR}/git-bundle.json")"

step "11/11 workbench — explore the pilot in the local UI"
echo "Run:"
echo "  ${MODELOPS} workbench --repo ${REL_REPO}"
echo "then open http://127.0.0.1:8000 (add --no-open to suppress the browser)."

echo ""
echo "Northstar synthetic pilot reproduction passed (11/11 steps)."
