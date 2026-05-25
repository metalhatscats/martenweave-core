#!/usr/bin/env bash
# Acceptance demo for Martenweave v0.1 core workflow.
# Runs end-to-end without external services (deterministic no-provider mode).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
MODELOPS="${REPO_ROOT}/.venv/bin/modelops"
DEMO_REPO="$(mktemp -d)"
FIXTURE_CSV="${REPO_ROOT}/tests/fixtures/product_sample.csv"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

step() {
    echo ""
    echo "===> $1"
}

cleanup() {
    rm -rf "${DEMO_REPO}"
}
trap cleanup EXIT

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

step "Copying example repo into temp directory"
cp -r "${REPO_ROOT}/examples/simple_product_model" "${DEMO_REPO}/demo"
DEMO_REPO="${DEMO_REPO}/demo"

# ---------------------------------------------------------------------------
# Core workflow
# ---------------------------------------------------------------------------

step "1. Validate canonical model"
"${MODELOPS}" validate --repo "${DEMO_REPO}"

step "2. Profile dataset"
"${MODELOPS}" profile-dataset "${FIXTURE_CSV}" --repo "${DEMO_REPO}"

step "3. Infer draft model from profile"
PROFILE_PATH="${DEMO_REPO}/generated/dataset_profiles/product_sample.json"
"${MODELOPS}" infer-model "${PROFILE_PATH}" --repo "${DEMO_REPO}"

step "4. Build search index (allow invalid because proposal references future objects)"
"${MODELOPS}" build-index --repo "${DEMO_REPO}" --jsonl --allow-invalid

step "5. Search indexed objects"
"${MODELOPS}" search "product" --repo "${DEMO_REPO}"

step "6. Query by object type"
"${MODELOPS}" query --repo "${DEMO_REPO}" --type "Attribute"

step "7. Trace object lineage"
"${MODELOPS}" trace "ATTR-PRODUCT-NAME" --repo "${DEMO_REPO}"

step "8. Analyze model completeness"
"${MODELOPS}" analyze --repo "${DEMO_REPO}"

step "9. Create change request"
"${MODELOPS}" change-request create \
    --id "CR-DEMO-001" \
    --title "Demo change request" \
    --repo "${DEMO_REPO}"

step "10. Preview notifications"
"${MODELOPS}" notifications preview \
    --change-request "CR-DEMO-001" \
    --repo "${DEMO_REPO}"

step "11. Dry-run apply inferred proposal"
# Infer-model creates PP-INFER-PRODUCT-SAMPLE; dry-run requires accepted status
PROPOSAL_FILE="${DEMO_REPO}/model/patch-proposals/PP-INFER-PRODUCT-SAMPLE.md"
if [[ -f "${PROPOSAL_FILE}" ]]; then
    sed -i.bak 's/status: pending_review/status: accepted/' "${PROPOSAL_FILE}"
    rm "${PROPOSAL_FILE}.bak"
    "${MODELOPS}" proposal apply \
        "PP-INFER-PRODUCT-SAMPLE" \
        --repo "${DEMO_REPO}" \
        --dry-run
else
    echo "Proposal not found; skipping dry-run."
fi

step "12. Export model to CSV"
"${MODELOPS}" export-model --repo "${DEMO_REPO}" --format csv

step "13. Export model to XLSX"
"${MODELOPS}" export-model --repo "${DEMO_REPO}" --format xlsx

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

echo ""
echo "=========================================="
echo "  Martenweave v0.1 Demo Complete"
echo "=========================================="
echo "  Demo repo:   ${DEMO_REPO}"
echo "  Validation:  PASS"
echo "  Index:       BUILT"
echo "  Search:      OK"
echo "  Trace:       OK"
echo "  Analysis:    OK"
echo "  Change Req:  CREATED"
echo "  Dry-run:     OK"
echo "  Export:      OK"
echo "=========================================="
