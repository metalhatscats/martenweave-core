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

## 3. Search and query

```bash
# Keyword search
.venv/bin/martenweave search "product" --repo examples/simple_product_model

# Structured query
.venv/bin/martenweave query --type Attribute --repo examples/simple_product_model
```

## 4. Trace and impact

```bash
# Trace relationships for an object
.venv/bin/martenweave trace ATTR-PRODUCT-NAME --repo examples/simple_product_model

# Impact analysis
.venv/bin/martenweave impact DOMAIN-PRODUCT --repo examples/simple_product_model
```

## 5. Profile a dataset

```bash
.venv/bin/martenweave profile-dataset \
  examples/simple_product_model/data/samples/product_sample.csv \
  --repo examples/simple_product_model
```

## 6. Detect gaps

```bash
.venv/bin/martenweave gaps \
  examples/simple_product_model/data/samples/product_sample.csv \
  --repo examples/simple_product_model
```

This compares dataset columns against your model's FieldEndpoints and reports matches, gaps, and coverage.

## 7. Review a proposal (dry-run)

If a PatchProposal exists in `model/patch-proposals/`:

```bash
.venv/bin/martenweave proposal list --repo examples/simple_product_model
.venv/bin/martenweave proposal diff PP-001 --repo examples/simple_product_model
.venv/bin/martenweave proposal apply PP-001 --repo examples/simple_product_model --dry-run
```

## 8. Health check

```bash
.venv/bin/martenweave health --repo examples/simple_product_model
```

---

## What you have now

- A validated canonical model
- A searchable SQLite index
- Dataset profiles and gap reports
- A feel for traceability and impact analysis

## Next steps

- Read the [User Guide](user-guide.md) for the full Dataset → Model workflow.
- Try the [Pilot Package](pilot-package.md) for a 1–2 week team onboarding plan.
- Explore the [SAP starter](https://github.com/metalhatscats/martenweave-core/tree/main/examples/customer_bp_model) if you are working with Business Partner master data.
