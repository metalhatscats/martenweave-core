# First Public Release Candidate Notes

Draft date: 2026-06-22

This is the draft release note for the first serious public release candidate of Martenweave Core.

## Positioning

Martenweave is a backend-first agentic data model registry. It turns scattered model knowledge from
Excel mappings, tickets, datasets, validation reports, decisions, SAP context, and project history
into a traceable, validated, AI-ready model truth layer.

SAP migration, Master Data Management, data governance, data quality, and AMS/support are the first
proof scenarios. SAP Business Partner, Customer, Supplier, and Vendor examples are starter domain
packs, not the product boundary.

## What Is Ready To Show

- Canonical Markdown/YAML model files remain the source of truth.
- Deterministic validation checks object IDs, types, references, ownership/readiness warnings, and
  SAP context rules.
- Generated SQLite and JSONL artifacts are disposable and rebuildable from canonical files.
- `modelops` CLI supports validation, indexing, search, query, trace, impact, health, scorecard,
  gap reporting, assessment packages, and proposal review flows.
- Bundled examples cover Customer / Business Partner, Supplier / Vendor, simple product, and generic
  product scenarios.
- AI-assisted work stays proposal-first: automation creates `PatchProposal` objects; validators and
  humans review before canonical files change.
- The release smoke script exercises validation, indexing, freshness, health, scorecards, search,
  query, trace, impact, dataset gaps, gap report, proposal dry-run, and config guard release mode.

## Demo Path

Recommended evaluator path:

```bash
python -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
.venv/bin/modelops validate --repo examples/customer_bp_model
.venv/bin/modelops build-index --repo examples/customer_bp_model --jsonl
.venv/bin/modelops search "Customer Group" --repo examples/customer_bp_model
.venv/bin/modelops trace ATTR-CUST-SALES-CUSTOMER-GROUP --repo examples/customer_bp_model
.venv/bin/modelops impact FEP-S4-KNVV-KDGRP --repo examples/customer_bp_model
.venv/bin/modelops gaps examples/customer_bp_model/data/samples/customer_sales_area_sample.csv \
  --repo examples/customer_bp_model \
  --check-model
.venv/bin/modelops propose-patch --from /tmp/martenweave-note.md \
  --repo examples/customer_bp_model \
  --dry-run
bash scripts/release_smoke.sh
```

For a fuller walkthrough, use `docs/demo-quickstart-flow.md` and
`scripts/demo_v0_3_gap_to_proposal.sh`.

## Known Limitations

- No production UI is included in the core package.
- No hosted SaaS tenant, managed workflow engine, or direct SAP write-back is included.
- The default AI adapter is deterministic and makes no provider call.
- Provider-backed AI workflows are optional and still need careful review with synthetic data first.
- Bundled examples intentionally include some warnings so health, scorecard, ownership, and gap
  reporting have visible material.
- Some integration docs describe design direction or optional surfaces; verify current command
  availability with `modelops --help`.

## Validation Evidence

See `docs/release-validation-evidence.md` for the current local validation run and blockers.
