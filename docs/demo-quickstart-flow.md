# Demo Quickstart Flow

This is the public demo path for technical evaluators. It uses the bundled SAP Customer / Business Partner example and does not require an AI provider key.

## Setup

```bash
python -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
.venv/bin/modelops --version
```

## 1. Validate Canonical Model Files

```bash
.venv/bin/modelops validate --repo examples/customer_bp_model
```

Expected result: zero validation errors. Methodology warnings may appear because the example intentionally leaves some enrichment gaps for reporting demos.

## 2. Build Generated Indexes

```bash
.venv/bin/modelops build-index --repo examples/customer_bp_model --jsonl
.venv/bin/modelops index-fresh --repo examples/customer_bp_model
```

Expected generated artifacts:

- `generated/modelops.db`
- `generated/search_documents.jsonl`
- `generated/lineage_edges.jsonl`

These files are disposable and rebuildable.

## 3. Search and Query

```bash
.venv/bin/modelops search "Customer Group" --repo examples/customer_bp_model
.venv/bin/modelops query --type Attribute --repo examples/customer_bp_model
```

Use this to show that canonical files can be indexed and searched without a UI or SaaS service.

## 4. Trace and Impact

```bash
.venv/bin/modelops trace ATTR-CUST-SALES-CUSTOMER-GROUP --repo examples/customer_bp_model
.venv/bin/modelops impact FEP-S4-KNVV-KDGRP --repo examples/customer_bp_model
```

Use this to show how a business attribute, physical SAP field endpoint, mappings, issues, decisions, and evidence stay connected.

## 5. Health and Governance Scorecard

```bash
.venv/bin/modelops health --repo examples/customer_bp_model
.venv/bin/modelops scorecard --repo examples/customer_bp_model
.venv/bin/modelops gap-report --repo examples/customer_bp_model
```

Use this to show what works today: deterministic checks, model coverage reporting, ownership/readiness signals, and model-side gaps.

## 6. Dataset Gaps

```bash
.venv/bin/modelops gaps \
  examples/customer_bp_model/data/samples/customer_sales_area_sample.csv \
  --repo examples/customer_bp_model \
  --check-model
```

Use this before mock loads or data readiness reviews to compare sample datasets with expected field endpoints.

## 7. Proposal-First AI Flow

```bash
cat >/tmp/martenweave-note.md <<'NOTE'
Update CUSTOMER GROUP mapping for KNVV-KDGRP based on the CH01-A17 decision.
Keep the change as a reviewable PatchProposal.
NOTE

.venv/bin/modelops propose-patch \
  --from /tmp/martenweave-note.md \
  --repo examples/customer_bp_model \
  --dry-run
```

The default adapter is deterministic and makes no external AI call. It demonstrates the governance shape: AI or automation proposes, validators check, humans approve.

## One-Command Release Smoke

```bash
bash scripts/release_smoke.sh
```

This runs the release-grade command matrix against all bundled examples and asserts stable JSON output.
