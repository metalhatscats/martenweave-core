# First 15 Minutes with Martenweave

> A copy-paste backend workflow from a fresh clone to your first insight.

## Prerequisites

- Python 3.11+
- A local clone of this repository

```bash
cd martenweave-core
python -m venv .venv
.venv/bin/python -m pip install -e .
```

## Pick your starting example

| Path | Best for |
|---|---|
| `examples/simple_product_model` | Generic onboarding — one domain, a few attributes, and a sample CSV |
| `examples/customer_bp_model` | SAP starter — Business Partner → Customer with real SAP context |

Not sure which to pick? See [What to Use First](what-to-use-first.md).

The commands below use `simple_product_model`. Replace the path if you want the SAP scenario.

## 1. Validate the canonical model

```bash
.venv/bin/martenweave validate --repo examples/simple_product_model
```

You should see zero errors. Warnings are normal for methodology checks and do not block the index.

## 2. Build the index

```bash
.venv/bin/martenweave build-index --repo examples/simple_product_model --jsonl
```

This creates:
- `generated/modelops.db` — SQLite index
- `generated/search_documents.jsonl` — search export
- `generated/lineage_edges.jsonl` — lineage export

## 3. Generate the local viewer

```bash
.venv/bin/martenweave docs-build --repo examples/simple_product_model --site docs_site
```

This creates generated Markdown plus a static read-only HTML viewer with `index.html`,
`objects.html`, object detail pages, `gaps.html`, `decisions.html`, `owners.html`,
`search-index.json`, and `viewer-manifest.json`. It is a disposable view over `modelops.db`;
canonical files in `model/` remain authoritative.

## 4. Search and query

```bash
# Keyword search
.venv/bin/martenweave search "product" --repo examples/simple_product_model

# Structured query
.venv/bin/martenweave query --type Attribute --repo examples/simple_product_model
```

## 5. Trace, impact, and object context

```bash
# Trace relationships for an object
.venv/bin/martenweave trace ATTR-PRODUCT-NAME --repo examples/simple_product_model

# Impact analysis
.venv/bin/martenweave impact DOMAIN-PRODUCT --repo examples/simple_product_model

# Compact object card: identity, relationships, issues, decisions, evidence, impact
.venv/bin/martenweave object-card ATTR-PRODUCT-NAME --repo examples/simple_product_model
.venv/bin/martenweave object-card ATTR-PRODUCT-NAME --repo examples/simple_product_model --json
```

## 6. Profile a dataset

```bash
.venv/bin/martenweave profile-dataset \
  examples/simple_product_model/data/samples/product_sample.csv \
  --repo examples/simple_product_model
```

## 7. Detect gaps

```bash
.venv/bin/martenweave gaps \
  examples/simple_product_model/data/samples/product_sample.csv \
  --repo examples/simple_product_model
```

This compares dataset columns against your model's FieldEndpoints and reports matches, gaps, and coverage.

## 7a. Realistic gap-detection demo (SAP customer data)

The `examples/customer_bp_model` includes two small synthetic datasets so you can compare a clean migration file with a messy legacy extract:

- `data/samples/customer_clean.csv` — canonical column names aligned with the model.
- `data/samples/customer_messy.csv` — renamed, duplicated, and extra columns.

Both files are synthetic; no real customer data is used.

```bash
.venv/bin/martenweave build-index --repo examples/customer_bp_model

# Messy extract: expect duplicate, renamed, and unmodeled columns
.venv/bin/martenweave gaps \
  examples/customer_bp_model/data/samples/customer_messy.csv \
  --repo examples/customer_bp_model
```

Expected gap highlights:

- `DUPLICATE_COLUMN_NAME` for `CUST_GRP`
- `UNMODELED_DATASET_COLUMN` for renamed columns such as `DIST_CHANNEL` and extra columns such as `EMAIL` and `PHONE`
- `NO_MATCHING_ENDPOINTS` because none of the messy columns map to a model FieldEndpoint

Compare with the clean extract:

```bash
.venv/bin/martenweave gaps \
  examples/customer_bp_model/data/samples/customer_clean.csv \
  --repo examples/customer_bp_model
```

Expected highlights:

- One exact match: `CUSTOMER_GROUP` → `FEP-MIGFILE-CUSTOMER-GROUP`
- No `DUPLICATE_COLUMN_NAME` or `NO_MATCHING_ENDPOINTS` gaps
- Remaining unmodeled columns show where the model still needs dataset FieldEndpoints

## 8. Run a dataset readiness report

```bash
.venv/bin/martenweave run dataset-readiness \
  examples/simple_product_model/data/samples/product_sample.csv \
  --repo examples/simple_product_model \
  --out /tmp/mw-readiness
```

This validates the model, profiles the dataset, detects gaps, and writes a consolidated `readiness.json` + `readiness.md` report with a ready / ready_with_warnings / blocked verdict.

Add `--promote-to-proposal` to turn dataset gaps into a draft PatchProposal for review, or `--issue-draft` to generate a GitHub-ready issue draft.

## 9. Review a proposal (dry-run)

If a PatchProposal exists in `model/patch-proposals/`:

```bash
.venv/bin/martenweave proposal list --repo examples/simple_product_model
.venv/bin/martenweave proposal diff PP-001 --repo examples/simple_product_model
.venv/bin/martenweave proposal apply PP-001 --repo examples/simple_product_model --dry-run
```

## 10. Health check

```bash
.venv/bin/martenweave health --repo examples/simple_product_model
```

## 11. Export a diagnostics bundle

For support handoffs, agent context, or pilot evidence, export a safe, redacted bundle of repository metadata:

```bash
.venv/bin/martenweave diagnostics export \
  --repo examples/simple_product_model \
  --out generated/diagnostics/simple-product \
  --include-outputs
```

The bundle includes validation, health, scorecard, source registry, generated manifest, pending changes, and dataset sample metadata. Secrets, raw dataset values, and full canonical contents are excluded by default. Add `--include-outputs` to snapshot key command outputs as JSON under `commands/`.

---

## What you have now

- A validated canonical model
- A searchable SQLite index
- A generated local static read-only viewer
- Dataset profiles and gap reports
- Traceability, impact analysis, and diagnostics bundles

## Next steps

- Read the [Local Static Viewer](local-static-viewer.md) guide for the exact `/tmp/martenweave-viewer` demo command and product boundaries.
- Read the [User Guide](user-guide.md) for the full Dataset → Model workflow.
- Try the [Pilot Package](pilot-package.md) for a 1–2 week team onboarding plan.
- Explore the [SAP starter](https://github.com/metalhatscats/martenweave-core/tree/main/examples/customer_bp_model) if you are working with Business Partner master data.
