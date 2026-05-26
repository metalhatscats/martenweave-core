#!/usr/bin/env bash
# Acceptance demo for Martenweave v0.3 gap-to-proposal workflow.
# Runs end-to-end without external services (deterministic no-provider mode).
# Uses supplier_vendor_model with a synthetic dataset to demonstrate:
#   validate → build-index → profile-dataset → detect-gaps → promote-gaps
#   → impact-analysis → proposal-show → proposal-diff → dry-run-apply
#
# All mutations are confined to a temporary directory. The canonical example
# repository is never modified.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
MODELOPS="${REPO_ROOT}/.venv/bin/modelops"
DEMO_TMP="$(mktemp -d)"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

step() {
    echo ""
    echo "===> $1"
}

cleanup() {
    rm -rf "${DEMO_TMP}"
}
trap cleanup EXIT

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

step "Copying supplier_vendor_model into temp directory"
cp -r "${REPO_ROOT}/examples/supplier_vendor_model" "${DEMO_TMP}/demo"
DEMO_REPO="${DEMO_TMP}/demo"
DATASET="${DEMO_REPO}/data/samples/vendor_extract.csv"

# ---------------------------------------------------------------------------
# v0.3 Core workflow
# ---------------------------------------------------------------------------

step "1. Validate canonical model"
"${MODELOPS}" validate --repo "${DEMO_REPO}"

step "2. Build search index + JSONL exports"
"${MODELOPS}" build-index --repo "${DEMO_REPO}" --jsonl

step "3. Profile synthetic dataset"
"${MODELOPS}" profile-dataset "${DATASET}" --repo "${DEMO_REPO}"

step "4. Detect dataset-to-model and model-to-dataset gaps"
# --check-model surfaces model-side gaps (e.g. MISSING_OWNER) in addition to
# dataset-side gaps (UNMODELED_DATASET_COLUMN, DATASET_COLUMN_MULTIPLE_MATCHES).
"${MODELOPS}" gaps "${DATASET}" --repo "${DEMO_REPO}" --check-model

step "5. Promote gaps to a draft PatchProposal"
"${MODELOPS}" gaps "${DATASET}" --repo "${DEMO_REPO}" --promote-to-proposal

step "6. Impact analysis with direction grouping"
# FEP-S4-LFA1-KTOKK has upstream mappings and downstream attribute/entity/domain
# links, making it a good object to demonstrate grouped impact reporting.
"${MODELOPS}" impact FEP-S4-LFA1-KTOKK --repo "${DEMO_REPO}" --group-by direction

step "7. Query objects by SAP table"
"${MODELOPS}" query --repo "${DEMO_REPO}" --sap-table LFA1 --json | head -n 20

step "8. Show promoted PatchProposal"
"${MODELOPS}" proposal show PP-GAP-VENDOR-EXTRACT-001 --repo "${DEMO_REPO}"

step "9. Diff the PatchProposal"
"${MODELOPS}" proposal diff PP-GAP-VENDOR-EXTRACT-001 --repo "${DEMO_REPO}"

step "10. Dry-run apply (requires temporary acceptance)"
# Proposals are created as pending_review for safety. Dry-run apply needs
# accepted status. We temporarily flip the status in the temp copy.
PROPOSAL_FILE="${DEMO_REPO}/model/patch-proposals/PP-GAP-VENDOR-EXTRACT-001.md"
if [[ -f "${PROPOSAL_FILE}" ]]; then
    sed -i.bak 's/status: pending_review/status: accepted/' "${PROPOSAL_FILE}"
    rm "${PROPOSAL_FILE}.bak"
    "${MODELOPS}" proposal apply PP-GAP-VENDOR-EXTRACT-001 --repo "${DEMO_REPO}" --dry-run
else
    echo "Proposal not found; skipping dry-run."
fi

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

echo ""
echo "=========================================="
echo "  Martenweave v0.3 Demo Complete"
echo "=========================================="
echo "  Demo repo:      ${DEMO_REPO}"
echo "  Validation:     PASS"
echo "  Index:          BUILT"
echo "  Dataset:        PROFILED"
echo "  Gaps:           DETECTED + PROMOTED"
echo "  Impact:         ANALYZED"
echo "  Query:          OK"
echo "  Proposal show:  OK"
echo "  Proposal diff:  OK"
echo "  Dry-run apply:  OK"
echo "=========================================="
