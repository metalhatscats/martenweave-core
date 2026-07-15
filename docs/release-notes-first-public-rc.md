# Martenweave Core v0.4.1 — Public Source Release Notes

> **Historical release notes.** Version 0.4.1 shipped on 2026-06-23 as the first public source release.
> The current supported release is **0.6.0**; see [`CHANGELOG.md`](../CHANGELOG.md) and
> [`docs/release-validation-evidence.md`](release-validation-evidence.md) for the latest evidence.

Release date: 2026-06-23

This is the first public source release of Martenweave Core.

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
.venv/bin/martenweave validate --repo examples/customer_bp_model
.venv/bin/martenweave build-index --repo examples/customer_bp_model --jsonl
.venv/bin/martenweave search "Customer Group" --repo examples/customer_bp_model
.venv/bin/martenweave trace ATTR-CUST-SALES-CUSTOMER-GROUP --repo examples/customer_bp_model
.venv/bin/martenweave impact FEP-S4-KNVV-KDGRP --repo examples/customer_bp_model
.venv/bin/martenweave gaps examples/customer_bp_model/data/samples/customer_sales_area_sample.csv \
  --repo examples/customer_bp_model \
  --check-model
.venv/bin/martenweave propose-patch --from /tmp/martenweave-note.md \
  --repo examples/customer_bp_model \
  --dry-run
bash scripts/release_smoke.sh
```

For a fuller walkthrough, use `docs/first-15-minutes.md` and
`scripts/demo_v0_3_gap_to_proposal.sh`.

## Known Limitations

- No production UI is included in the core package.
- No hosted SaaS tenant, managed workflow engine, or direct SAP write-back is included.
- The default AI adapter is deterministic and makes no provider call.
- Provider-backed AI workflows are optional and still need careful review with synthetic data first.
- Bundled examples intentionally include some warnings so health, scorecard, ownership, and gap
  reporting have visible material.
- Some integration docs describe design direction or optional surfaces; verify current command
  availability with `martenweave --help`.

## License at the Time of the 0.4.1 Release

Version 0.4.1 was originally distributed under MIT. Existing copies retain those terms.

The current supported release and all active development are licensed under Apache License 2.0.
Optional commercial services include implementation, private SAP/MDM domain packs, enterprise
validation packs, hosted Workbench work, integrations, training, and support.

See `docs/licensing-and-commercial-use.md`.

## Safe Tagging Policy

```bash
git tag -a v0.4.1 -m "Release v0.4.1"
git push origin v0.4.1
```

The `v0.4.1` tag has been used for the public release. Do not move or reuse the existing remote
`v0.4.0` tag; it points to an older commit and must remain untouched.

Because `v0.4.0` already exists on the wrong commit, `v0.4.1` is the safe patch release that
carries the validated public source readiness changes without rewriting any existing tags.

## GitHub Release Notes Draft

Martenweave Core v0.4.1 is the first public source release of the backend-first model registry.

Highlights:

- canonical Markdown/YAML model files as source of truth
- deterministic validation for objects, references, ownership/readiness warnings, and SAP context
- generated SQLite and JSONL indexes for search, lineage, reports, and agent context
- CLI workflows for validate, build-index, search, query, trace, impact, gaps, health, scorecard,
  ownership, audit, import/export, and proposal review
- example model repositories for Customer / Business Partner, Supplier / Vendor, simple product,
  and generic product scenarios
- proposal-first AI workflow: AI can draft `PatchProposal` objects, but humans approve canonical
  changes
- release smoke coverage across bundled examples and config-guard release mode
- `serve` and `mcp` remain local integration surfaces; no hosted product UI

Known limits:

- backend/core only; no production UI or hosted SaaS
- no direct SAP write-back
- provider-backed AI is optional and must be tested with synthetic data first
- PyPI publishing must continue to go through the trusted-publisher release workflow

## Short Public Announcement

Martenweave Core is ready as a public source release: a backend-first model registry that turns
scattered migration, MDM, governance, and AMS model knowledge into validated canonical files,
generated indexes, trace/impact reports, gap checks, and human-approved patch proposals.

## LinkedIn Post Draft

I have prepared Martenweave Core as a first public source release.

It is a backend-first model registry for SAP migration, MDM, data governance, data quality, and AMS
support contexts. The idea is simple: canonical model files are the source of truth, validators
check consistency, generated indexes support search/trace/impact/gaps, and AI can propose changes
without silently mutating the model.

I am open to feedback and practical pilot conversations around SAP MDM / migration readiness,
model governance, dataset gaps, validation evidence, and AMS knowledge continuity.

Core repo: https://github.com/metalhatscats/martenweave-core
Website: https://martenweave.github.io/

## Pilot Invitation Text

Good pilot scenarios include customer/BP mapping control, supplier/vendor model control, dataset
gaps before mock load, validation report triage, ownership/rule traceability, and AMS knowledge
continuity. A useful pilot should provide sample mappings, small synthetic or approved dataset
extracts, validation findings, tickets/decisions, and field/rule context. Martenweave should
produce a validated model repository, gap report, impact examples, evidence links, patch proposal
examples, and readiness summary.

## Resolved Release Setup

- [#411](https://github.com/metalhatscats/martenweave-core/issues/411) is resolved: PyPI trusted
  publishing is configured and `martenweave-core 0.4.1` is published.

## Validation Evidence

See `docs/release-validation-evidence.md` for the current local validation run and blockers.
