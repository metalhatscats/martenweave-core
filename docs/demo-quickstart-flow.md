# Demo Quickstart Flow

This is the public demo path for technical evaluators. It uses the bundled SAP Customer / Business Partner example and does not require an AI provider key.

## Setup

```bash
python -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
.venv/bin/martenweave --version
```

## 1. Validate Canonical Model Files

```bash
.venv/bin/martenweave validate --repo examples/customer_bp_model
```

Expected result: zero validation errors. Methodology warnings may appear because the example intentionally leaves some enrichment gaps for reporting demos.

## 2. Build Generated Indexes

```bash
.venv/bin/martenweave build-index --repo examples/customer_bp_model --jsonl
.venv/bin/martenweave index-fresh --repo examples/customer_bp_model
```

Expected generated artifacts:

- `generated/modelops.db`
- `generated/search_documents.jsonl`
- `generated/lineage_edges.jsonl`

These files are disposable and rebuildable.

## 3. Search and Query

```bash
.venv/bin/martenweave search "Customer Group" --repo examples/customer_bp_model
.venv/bin/martenweave query --type Attribute --repo examples/customer_bp_model
```

Use this to show that canonical files can be indexed and searched without a UI or SaaS service.

## 4. Generate Local Static Viewer

```bash
.venv/bin/martenweave docs-build \
  --repo examples/customer_bp_model \
  --site /tmp/martenweave-viewer
```

Open `/tmp/martenweave-viewer/index.html` directly or serve it locally:

```bash
cd /tmp/martenweave-viewer
python3 -m http.server 8000
```

Expected viewer outputs include `index.html`, `objects.html`, object detail pages,
`gaps.html`, `decisions.html`, `owners.html`, `assets/viewer.css`, `assets/viewer.js`,
`search-index.json`, and `viewer-manifest.json`. The viewer is static, local, read-only, and
generated from `modelops.db`; canonical files remain the source of truth. It does not add a hosted
UI, login, editor, SAP write-back, or AI auto-mutation path.

## 5. Trace and Impact

```bash
.venv/bin/martenweave trace ATTR-CUST-SALES-CUSTOMER-GROUP --repo examples/customer_bp_model
.venv/bin/martenweave impact FEP-S4-KNVV-KDGRP --repo examples/customer_bp_model
```

Use this to show how a business attribute, physical SAP field endpoint, mappings, issues, decisions, and evidence stay connected.

## 6. Health and Governance Scorecard

```bash
.venv/bin/martenweave health --repo examples/customer_bp_model
.venv/bin/martenweave scorecard --repo examples/customer_bp_model
.venv/bin/martenweave gap-report --repo examples/customer_bp_model
```

Use this to show what works today: deterministic checks, model coverage reporting, ownership/readiness signals, and model-side gaps.

## 7. Dataset Gaps

```bash
.venv/bin/martenweave gaps \
  examples/customer_bp_model/data/samples/customer_sales_area_sample.csv \
  --repo examples/customer_bp_model \
  --check-model
```

Use this before mock loads or data readiness reviews to compare sample datasets with expected field endpoints.

## 8. One-Command Dataset Readiness

```bash
.venv/bin/martenweave run dataset-readiness \
  --repo examples/customer_bp_model \
  --dataset examples/customer_bp_model/data/samples/customer_sales_area_sample.csv \
  --out /tmp/mw-readiness \
  --check-model
```

This produces a single shareable report (`readiness.json` + `readiness.md`) that combines validation, coverage, gaps, and a readiness verdict.

Promote dataset gaps directly to a draft PatchProposal for review:

```bash
.venv/bin/martenweave run dataset-readiness \
  --repo examples/customer_bp_model \
  --dataset examples/customer_bp_model/data/samples/customer_sales_area_sample.csv \
  --out /tmp/mw-readiness \
  --promote-to-proposal
```

The proposal is written to `model/patch-proposals/` in `pending_review` status and remains subject to human review.

Generate a GitHub-ready issue draft from the same readiness run:

```bash
.venv/bin/martenweave run dataset-readiness \
  --repo examples/customer_bp_model \
  --dataset examples/customer_bp_model/data/samples/customer_sales_area_sample.csv \
  --out /tmp/mw-readiness \
  --issue-draft
```

The draft is written to `generated/issues/readiness.md` and can be published with `martenweave publish-issue`.

## 9. Proposal-First AI Flow

```bash
cat >/tmp/martenweave-note.md <<'NOTE'
Update CUSTOMER GROUP mapping for KNVV-KDGRP based on the CH01-A17 decision.
Keep the change as a reviewable PatchProposal.
NOTE

.venv/bin/martenweave propose-patch \
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
