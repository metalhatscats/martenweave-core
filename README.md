# martenweave-core

[![CI](https://github.com/metalhatscats/martenweave-core/actions/workflows/ci.yml/badge.svg)](https://github.com/metalhatscats/martenweave-core/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

Backend-first, open-source model governance pipeline for SAP migration and Master Data Management.

Martenweave turns spreadsheets, datasets, tickets, validation reports, decisions, and SAP context
into canonical model files, deterministic validation, dataset gap reports, lineage, impact
analysis, and human-approved AI patch proposals. The model registry is the source-of-truth layer
inside this pipeline, not the whole product category.

SAP migration and Master Data Management are the **first domain pack** and proof case, not the
product boundary. The open-source core also works with generic data models: domains, entities,
attributes, relationships, datasets, mappings, rules, evidence, decisions, and change proposals.

**No hosted or editable product UI is included.** This is a CLI-driven, backend/core library
designed to be embedded in pipelines, IDEs, local API processes, MCP servers, and agent workflows.
It can generate a local static read-only viewer from the disposable SQLite index for inspection and
demo purposes.

For an interactive **local frontend prototype**, see [`frontend/README.md`](frontend/README.md).
It can be run locally for demo and review; it is **not a hosted production app** and does not
replace the CLI-first core workflow.

## Status

- Current source version: `0.4.1`
- Package / PyPI name: `martenweave-core`
- Install from PyPI: `pip install martenweave-core`
- Source install remains available for contributors and local development.
- Public site and docs: <https://martenweave.github.io/>

## Naming

- Product: **Martenweave**
- Open-source core / PyPI package: `martenweave-core`
- Python module: `modelops_core`
- CLI commands: `modelops` and `martenweave`

`martenweave-core` is the backend-first open-source core package for the Martenweave product. Use
`martenweave` for new terminal examples and documentation. The existing `modelops` command remains
supported for backward compatibility with scripts, CI jobs, and early adopters.

## Core Principles

- **Canonical files are the source of truth.** Markdown + YAML frontmatter objects live in `model/`.
- **Generated index is disposable.** SQLite and JSONL outputs are rebuildable from canonical files.
- **Deterministic validation first.** Every object is validated for IDs, types, references, and domain context rules before indexing.
- **AI must not silently mutate.** AI creates `PatchProposal` objects for human review. Approved changes become `ChangeRequest`s.
- **Local-first.** No cloud dependencies, no SaaS lock-in.

## What Martenweave is / is not

| Is | Is not |
|---|---|
| A backend-first model governance pipeline | A generic workflow platform |
| A canonical file registry with disposable generated indexes | A hosted MDM platform |
| A validator-gated, proposal-first model change workflow | A workflow engine or n8n/Zapier/Dify competitor |
| A local-first CLI and embeddable open-source core | Generic B2B SaaS or a chatbot |
| AI-assisted, with human approval required for changes | Autonomous mutation or direct SAP write-back |

## Why pipeline, not SaaS

Martenweave is built for controlled model change workflows:

```text
evidence → proposal → validation → gaps/impact → review → GitHub issue/PR
```

It coordinates existing CLI services around canonical files and Git. It does not add a hosted
editable UI, tenant platform, generic workflow engine, or direct SAP write-back path.

**Agents propose. Validators verify. Humans approve. Git records.**

## Pipeline workflow

1. Import or profile source evidence.
2. Validate canonical model files.
3. Build the generated SQLite and search index.
4. Detect dataset/model gaps.
5. Run lineage and impact analysis.
6. Generate AI patch proposals.
7. Publish a GitHub issue or pull request only for human review.

Proposed roadmap workflow — this command is **not implemented**:

```bash
martenweave run dataset-readiness --repo ./model --dataset customers.xlsx --out ./reports/readiness
```

## Quickstart

Martenweave Core requires Python 3.11+.

### Install from PyPI

```bash
python -m pip install martenweave-core
martenweave --help
```

### Install from Source

Use a source install when contributing to the core repository or testing local changes:

```bash
git clone https://github.com/metalhatscats/martenweave-core.git
cd martenweave-core
python -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
.venv/bin/martenweave --help
```

### Setup

Choose one style and use it throughout:

**Option A — use the venv executable directly (recommended for copy-paste):**
```bash
python -m venv .venv
.venv/bin/python -m pip install -e .
# Then use .venv/bin/martenweave for every command
```

**Option B — activate the venv once:**
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
# Then use bare martenweave for every command
```

The examples below use Option A. Replace `.venv/bin/martenweave` with `martenweave` if you chose
Option B. `.venv/bin/modelops` and `modelops` still work as compatibility aliases.

```bash
# Install
.venv/bin/python -m pip install -e .

# Scaffold a new repository
.venv/bin/martenweave init ./my-model

# Validate canonical files
.venv/bin/martenweave validate --repo ./my-model

# Build SQLite index + JSONL exports
.venv/bin/martenweave build-index --repo ./my-model --jsonl

# Check index freshness
.venv/bin/martenweave index-fresh --repo ./my-model

# Health report and scorecard
.venv/bin/martenweave health --repo ./my-model
.venv/bin/martenweave scorecard --repo ./my-model

# Impact and trace analysis
.venv/bin/martenweave impact FEP-S4-KNVV-KDGRP --repo ./my-model
.venv/bin/martenweave trace ATTR-CUST-SALES-CUSTOMER-GROUP --repo ./my-model

# Search and query
.venv/bin/martenweave search "Customer Group" --repo ./my-model
.venv/bin/martenweave query --type Attribute --repo ./my-model

# Generate local static Markdown docs and read-only HTML viewer
.venv/bin/martenweave docs-build --repo ./my-model --site /tmp/martenweave-viewer

# Diff against another repository
.venv/bin/martenweave diff ./my-model ./other-model

# Propose a patch from a note
.venv/bin/martenweave propose-patch --from ./note.md --repo ./my-model

# Clean generated artifacts (dry-run first)
.venv/bin/martenweave clean --repo ./my-model --dry-run
```

## First 15 Minutes

For a step-by-step walkthrough using the included examples, see [docs/first-15-minutes.md](docs/first-15-minutes.md).

For a release-grade demo path that exercises validation, indexing, search, trace, impact, gaps, scorecards, and proposal dry-runs, see [docs/demo-quickstart-flow.md](docs/demo-quickstart-flow.md).

## Command Reference

| Command | Purpose |
|---|---|
| `init` | Scaffold a new model repository |
| `profile-dataset` | Profile a CSV/XLSX dataset and save the profile |
| `gaps` | Detect dataset-to-model gaps against FieldEndpoints |
| `import-drive` | Import a CSV/XLSX file from Google Drive and profile it |
| `import-sheet` | Import a Google Sheet as a PatchProposal |
| `sources` | List registered external sources |
| `source-show` | Show one registered source |
| `infer-model` | Infer draft model objects from a dataset profile |
| `validate` | Run deterministic validation on canonical files |
| `build-index` | Build SQLite index and optional JSONL exports |
| `clean` | Remove generated artifacts from a repository |
| `index-fresh` | Check whether the generated index is stale |
| `health` | Show repository health report |
| `doctor` | Run diagnostics for version, config, paths, index freshness, and validation |
| `scorecard` | Show governance readiness scorecard |
| `owners` | Ownership coverage and steward workload |
| `analyze` | Analyze model completeness, risk, and readiness |
| `gap-report` | Consolidated gap summary across all sources |
| `trace` | Trace upstream/downstream relationships for an object |
| `impact` | Generate impact report for an object or proposal |
| `propose-patch` | Create a PatchProposal from a note |
| `serve` | Start the optional local API server |
| `mcp` | Start the optional MCP server for agent integration |
| `import-model-sheet` | Import spreadsheet edits as a PatchProposal |
| `export-model` | Export canonical objects to CSV or XLSX |
| `export-schema` | Export JSON Schema for canonical object types |
| `export-sheets` | Export canonical model objects to Google Sheets |
| `git-bundle` | Generate a GitHub-ready change bundle |
| `publish-issue` | Publish an issue draft to GitHub |
| `publish-pr` | Publish a git bundle as a GitHub pull request |
| `audit-log` | Query the append-only audit log |
| `usage-report` | Show aggregated usage report from telemetry |
| `docs-build` | Generate static Markdown docs and a local read-only HTML viewer from the index |
| `config-guard` | Scan for secrets and configuration guardrail issues |
| `diff` | Compare two model repositories |
| `search` | Search indexed objects by keyword |
| `query` | Run structured queries over the index |
| `migrate` | Migrate canonical objects to the current schema version |
| `issue-draft` | Generate GitHub-ready issue drafts |
| `change-request` | Create and manage ChangeRequests |
| `notifications` | Preview notification recipients |
| `decisions` | Browse and inspect Decision objects |
| `proposal` | Review and apply PatchProposals |
| `assessment` | Run migration model readiness assessment workflows |

`docs-build` produces disposable generated files such as `index.html`, `objects.html`,
`gaps.html`, `decisions.html`, `owners.html`, object detail pages, `search-index.json`, and
`viewer-manifest.json`. The viewer is static and read-only: canonical files remain authoritative,
and there is no hosted UI, login, editing workflow, SAP write-back, or AI auto-mutation path.

`serve` and `mcp` are local integration surfaces for APIs, tools, and agents. They do not provide a
hosted product UI or browser application.

Use `--help` on any command for full options:

```bash
.venv/bin/martenweave <command> --help
```

### Assessment Example

```bash
.venv/bin/martenweave assessment run --repo examples/customer_bp_model --out generated/assessment/customer-bp
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
.venv/bin/martenweave validate --repo examples/customer_bp_model
.venv/bin/martenweave validate --repo examples/supplier_vendor_model
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
- [docs/local-static-viewer.md](docs/local-static-viewer.md)

## Licensing and commercial use

Martenweave Core is MIT-licensed open source. Commercial offerings may include implementation
support, private SAP/MDM domain packs, enterprise validation packs, a hosted workbench, custom
integrations, and support SLAs. Future extensions, templates, packs, or hosted services may be
distributed under separate commercial terms.

By contributing to Martenweave Core, contributors agree their contribution is licensed under the
same MIT License as the project. No separate contributor license agreement is required at this
stage.

## License

MIT. See [docs/licensing-and-commercial-use.md](docs/licensing-and-commercial-use.md) for the
current commercial-use clarification and future licensing options.
