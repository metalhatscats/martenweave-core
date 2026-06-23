# martenweave-core

[![CI](https://github.com/metalhatscats/martenweave-core/actions/workflows/ci.yml/badge.svg)](https://github.com/metalhatscats/martenweave-core/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

Backend-first agentic data model registry.

Turns data models into a structured, traceable, validated, AI-ready model knowledge layer. This repository contains the canonical model registry, deterministic validation, generated SQLite index, safe AI patch proposals, and Git-friendly model files.

SAP migration and Master Data Management are the **first domain pack** and proof case, not the product boundary. The core works for generic data models: domains, entities, attributes, relationships, datasets, mappings, rules, evidence, decisions, and change proposals.

**No UI is included.** This is a CLI-driven, backend/core library designed to be embedded in pipelines, IDEs, and agent workflows.

## Status

- Current source version: `0.4.0`
- Package name: `martenweave-core`
- Public site and docs: <https://martenweave.github.io/>
- PyPI publishing is intentionally gated by the trusted-publisher release workflow. Until a package is published, install from source as shown below.

## Core Principles

- **Canonical files are the source of truth.** Markdown + YAML frontmatter objects live in `model/`.
- **Generated index is disposable.** SQLite and JSONL outputs are rebuildable from canonical files.
- **Deterministic validation first.** Every object is validated for IDs, types, references, and domain context rules before indexing.
- **AI must not silently mutate.** AI creates `PatchProposal` objects for human review. Approved changes become `ChangeRequest`s.
- **Local-first.** No cloud dependencies, no SaaS lock-in.

## What Martenweave is / is not

| Is | Is not |
|---|---|
| A backend-first model registry for data modeling, migration, and governance | A SAP-only tool |
| A canonical file store with generated indexes | A database-first MDM platform |
| A validator-gated, proposal-first editing workflow | A workflow engine |
| A local-first CLI and embeddable library | A SaaS platform |
| AI-assisted, with human approval required for changes | An autonomous AI agent that mutates models |

## Quickstart

Martenweave Core requires Python 3.11+.

### Install from Source

```bash
git clone https://github.com/metalhatscats/martenweave-core.git
cd martenweave-core
python -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
.venv/bin/modelops --help
```

### Setup

Choose one style and use it throughout:

**Option A — use the venv executable directly (recommended for copy-paste):**
```bash
python -m venv .venv
.venv/bin/python -m pip install -e .
# Then use .venv/bin/modelops for every command
```

**Option B — activate the venv once:**
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
# Then use bare modelops for every command
```

The examples below use Option A. Replace `.venv/bin/modelops` with `modelops` if you chose Option B.

```bash
# Install
.venv/bin/python -m pip install -e .

# Scaffold a new repository
.venv/bin/modelops init ./my-model

# Validate canonical files
.venv/bin/modelops validate --repo ./my-model

# Build SQLite index + JSONL exports
.venv/bin/modelops build-index --repo ./my-model --jsonl

# Check index freshness
.venv/bin/modelops index-fresh --repo ./my-model

# Health report and scorecard
.venv/bin/modelops health --repo ./my-model
.venv/bin/modelops scorecard --repo ./my-model

# Impact and trace analysis
.venv/bin/modelops impact FEP-S4-KNVV-KDGRP --repo ./my-model
.venv/bin/modelops trace ATTR-CUST-SALES-CUSTOMER-GROUP --repo ./my-model

# Search and query
.venv/bin/modelops search "Customer Group" --repo ./my-model
.venv/bin/modelops query --type Attribute --repo ./my-model

# Diff against another repository
.venv/bin/modelops diff ./my-model ./other-model

# Propose a patch from a note
.venv/bin/modelops propose-patch --from ./note.md --repo ./my-model

# Clean generated artifacts (dry-run first)
.venv/bin/modelops clean --repo ./my-model --dry-run
```

## First 15 Minutes

For a step-by-step walkthrough using the included examples, see [docs/first-15-minutes.md](docs/first-15-minutes.md).

For a release-grade demo path that exercises validation, indexing, search, trace, impact, gaps, scorecards, and proposal dry-runs, see [docs/demo-quickstart-flow.md](docs/demo-quickstart-flow.md).

## Command Reference

| Command | Purpose |
|---|---|
| `init` | Scaffold a new model repository |
| `validate` | Run deterministic validation on canonical files |
| `build-index` | Build SQLite index and optional JSONL exports |
| `health` | Show repository health report |
| `scorecard` | Show governance readiness scorecard |
| `gap-report` | Consolidated gap summary across all sources (model coverage) |
| `gaps` | Dataset-to-model gap detection (requires a dataset path) |
| `owners` | Ownership coverage and steward workload |
| `analyze` | Analyze model completeness, risk, and readiness |
| `trace` | Trace upstream/downstream relationships for an object |
| `impact` | Generate impact report for an object or proposal |
| `search` | Search indexed objects by keyword |
| `query` | Run structured queries over the index |
| `propose-patch` | Create a PatchProposal from a note |
| `proposal` | Review and apply PatchProposals (subcommands: `impact`, `apply`, `validate`, `report`) |
| `change-request` | Create and manage ChangeRequests (subcommands: `create`, `approve`, `reject`, `list`, `show`, `update-status`) |
| `decisions` | Browse and inspect Decision objects (subcommands: `list`, `show`, `report`) |
| `export-model` | Export canonical objects to CSV or XLSX |
| `docs-build` | Generate static Markdown docs from the index |
| `usage-report` | Show aggregated usage report from telemetry |
| `audit-log` | Query the append-only audit log |
| `config-guard` | Scan for secrets and configuration guardrail issues |
| `clean` | Remove generated artifacts from a repository |
| `diff` | Compare two model repositories |
| `migrate` | Migrate canonical objects to the current schema version |
| `profile-dataset` | Profile a CSV/XLSX dataset |
| `infer-model` | Infer draft model objects from a dataset profile |
| `import-model-sheet` | Import spreadsheet edits as a PatchProposal |
| `sources` | List registered external sources |
| `issue-draft` | Generate GitHub-ready issue drafts |
| `git-bundle` | Generate a GitHub-ready change bundle |
| `publish-issue` | Publish an issue draft to GitHub |
| `publish-pr` | Publish a git bundle as a GitHub pull request |
| `notifications` | Preview notification recipients |
| `serve` | Start the local API server |
| `mcp` | Start the MCP server for agent integration |

Use `--help` on any command for full options:

```bash
.venv/bin/modelops <command> --help
```

## Example Models

Both example directories contain a working `modelops.config.yaml` and can be run without `init`.

### Customer / Business Partner Model

The `examples/customer_bp_model/` directory contains the first domain pack: a full canonical model slice for SAP Business Partner → Customer:

```
Business Partner -> Customer -> Customer Sales Area -> Customer Group -> KNVV-KDGRP
```

### Supplier / Vendor Model

The `examples/supplier_vendor_model/` directory contains a second domain pack for SAP Supplier / Vendor master data:

```
Supplier -> Vendor Central -> LFA1/KTOKK, LFB1/ZTERM, LFM1/SPERR
```

Run validation against either:

```bash
.venv/bin/modelops validate --repo examples/customer_bp_model
.venv/bin/modelops validate --repo examples/supplier_vendor_model
```

## Architecture

```
modelops.config.yaml        # Repository configuration
model/                      # Canonical Markdown + YAML objects
  DOMAIN-*.md
  ENTITY-*.md
  ATTR-*.md
  FEP-*.md
  MAP-*.md
  ...
generated/                  # Disposable artifacts
  modelops.db               # SQLite index
  search_documents.jsonl    # Search export
  lineage_edges.jsonl       # Lineage export
  audit_events.jsonl        # Audit log
  usage_events.jsonl        # Application usage telemetry
  ai_usage_events.jsonl     # AI provider usage telemetry
data/samples/               # Sample datasets for profiling
```

## Domain Rules (SAP example)

The first domain pack includes SAP-specific context rules:

- `Attribute` is business meaning.
- `FieldEndpoint` is physical representation.
- `AttributeUsage` links an `Attribute` to a specific business context.
- `Mapping` links source and target `FieldEndpoint`s.
- `KNVV` fields must be in `customer_sales_area` context.
- `KNB1` fields must be in `customer_company_code` context.
- `KNVP` fields must be in `customer_partner_function` context.
- `BUT000` fields must be in `bp_central` context.

Future domain packs can add their own validation rules without changing core concepts.

## Documentation

See [docs/README.md](docs/README.md) for the full documentation index, including architecture docs, developer guides, product playbooks, and the Data Model Book.

## Development

```bash
# Run tests
.venv/bin/python -m pytest

# Lint
.venv/bin/python -m ruff check .

# Release smoke across bundled examples
bash scripts/release_smoke.sh
```

Release and public-readiness docs:

- [docs/release-checklist.md](docs/release-checklist.md)
- [docs/release-notes-first-public-rc.md](docs/release-notes-first-public-rc.md)
- [docs/release-validation-evidence.md](docs/release-validation-evidence.md)
- [docs/open-source-readiness.md](docs/open-source-readiness.md)
- [docs/known-limitations.md](docs/known-limitations.md)

## License

MIT. See [docs/licensing-and-commercial-use.md](docs/licensing-and-commercial-use.md) for the
current commercial-use clarification and future licensing options.
