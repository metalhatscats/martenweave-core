# AGENTS.md — martenweave-core

> This file is for AI coding agents. It describes the project structure, conventions, and workflows you need to know before making changes.

---

## Project Overview

**martenweave-core** (Python package `modelops_core`) is a backend-first **agentic data model registry**. It turns data models into a structured, traceable, validated, AI-ready model knowledge layer. SAP migration and Master Data Management are the first domain pack and proof case, not the product boundary.

**No UI is included.** This is a CLI-driven, backend/core library designed to be embedded in pipelines, IDEs, and agent workflows.

### Core Principles

- **Canonical files are the source of truth.** Markdown + YAML frontmatter objects live in `model/`.
- **Generated index is disposable.** SQLite and JSONL outputs in `generated/` are rebuildable from canonical files.
- **Deterministic validation first.** Every object is validated for IDs, types, references, and SAP context rules before indexing.
- **AI must not silently mutate.** AI creates `PatchProposal` objects for human review. Approved changes become `ChangeRequest`s.
- **Local-first.** No cloud dependencies, no SaaS lock-in.

---

## Technology Stack

| Layer | Choice | Notes |
|---|---|---|
| Language | Python >=3.11 | `from __future__ import annotations` is used throughout |
| Data Validation | Pydantic >=2.6 | Runtime validation, strict models |
| CLI Framework | Typer >=0.12 | Clean CLI using same services as API |
| Terminal Output | Rich >=13.0 | Tables, styled output |
| YAML Parsing | PyYAML >=6.0 | Frontmatter and config files |
| Testing | pytest >=8.0 | Backend tests only |
| Linting/Formatting | ruff >=0.4 | Line length 100, target py311 |
| Generated Index | SQLite | Embedded, local-first, zero-admin |
| AI Adapter | Direct provider adapters | Currently stubbed with `NoProviderAdapter` |

---

## Project Structure

```
.
├── pyproject.toml              # Package config, dependencies, tool settings
├── modelops.config.example.yaml # Example repository configuration
├── .env.example                # Environment variables example
├── src/modelops_core/          # Main Python package
│   ├── __init__.py             # Exports __version__
│   ├── __version__.py          # "0.4.0"
│   ├── cli.py                  # Typer CLI: all top-level commands and sub-apps
│   ├── config.py               # RepoConfig, Settings, path resolution
│   ├── errors.py               # Custom exceptions
│   ├── paths.py                # Path utilities
│   ├── ai/                     # AI patch proposal services and provider adapters
│   ├── api/                    # FastAPI server routes and lifespan
│   ├── approval/               # Approval gate and reviewer rules
│   ├── assessment/             # Migration model readiness assessment packs
│   ├── bundle/                 # Git bundle and review pack generation
│   ├── change_request/         # Change request services and CLI logic
│   ├── connectors/             # External source connectors (Google Drive, Sheets)
│   ├── diff/                   # Repository diff engine
│   ├── docs/                   # Static documentation generation from the index
│   ├── domain_packs/           # Domain-specific rules and templates (SAP, generic)
│   ├── exports/                # CSV, XLSX, Google Sheets, and schema exports
│   ├── fixtures/               # Canonical object fixture factories
│   ├── gaps/                   # Dataset-to-model gap detection
│   ├── guardrails/             # Secret/config guardrails and safety checks
│   ├── impact/                 # Impact analysis via BFS traversal
│   ├── imports/                # Dataset profiling, import sessions, privacy
│   ├── index/                  # SQLite index builder, search documents, lineage edges
│   ├── issue_draft/            # GitHub issue draft generation
│   ├── lineage/                # Lineage edge models and service
│   ├── mcp_server.py           # MCP (Model Context Protocol) server entry point
│   ├── notifications/          # Notification event generation and preview
│   ├── patching/               # Patch proposal, change request, apply services
│   ├── reports/                # Health reports, audit service, analysis, ownership
│   ├── repository/             # File parser (Markdown/YAML frontmatter), scanner
│   ├── schemas/                # Pydantic models and object type registry
│   ├── telemetry/              # AI usage and application usage telemetry
│   ├── trace/                  # Upstream/downstream trace service
│   └── validation/             # Deterministic validation pipeline (Layer 1–3)
│
├── tests/                      # pytest test suite
│   ├── conftest.py             # Shared fixtures: sample_repo, supplier_repo,
│   │                           # temp_model_dir, factories
│   ├── test_ai_patch_proposal_service.py
│   ├── test_ai_usage_telemetry.py
│   ├── test_analysis_service.py
│   ├── test_api.py
│   ├── test_approval_gates.py
│   ├── test_assessment_package.py
│   ├── test_audit_log.py
│   ├── test_change_request_*.py
│   ├── test_cli.py             # CLI command tests
│   ├── test_cli_contracts.py   # Stable JSON output contracts
│   ├── test_cli_structure.py   # Command registration smoke tests
│   ├── test_config.py
│   ├── test_connectors.py
│   ├── test_dataset_profiler.py
│   ├── test_decisions_*.py
│   ├── test_diff.py
│   ├── test_docs_build.py
│   ├── test_domain_packs.py
│   ├── test_e2e_demo.py        # End-to-end demo tests
│   ├── test_export_model.py
│   ├── test_export_schema.py
│   ├── test_gaps.py            # Dataset-to-model gap detection
│   ├── test_git_bundle.py
│   ├── test_google_*.py        # Google Drive/Sheets import/export
│   ├── test_health_report_coverage.py
│   ├── test_impact_service.py
│   ├── test_import_model_sheet.py
│   ├── test_index_builder.py
│   ├── test_issue_draft.py
│   ├── test_lineage_edges.py
│   ├── test_lov_governance.py
│   ├── test_mcp_server.py
│   ├── test_model_inference.py
│   ├── test_notification_*.py
│   ├── test_ownership*.py
│   ├── test_patch_apply.py
│   ├── test_patch_proposal_validation.py
│   ├── test_proposal_*.py
│   ├── test_provider_adapter.py
│   ├── test_reference_validation.py
│   ├── test_repository_parser.py
│   ├── test_sap_context_validation.py
│   ├── test_schema_validation.py
│   ├── test_scorecard.py
│   ├── test_secret_guardrails.py
│   ├── test_telemetry.py
│   ├── test_trace.py
│   └── test_usage_report.py
│
├── examples/customer_bp_model/ # Full canonical model slice (Business Partner → Customer)
│   ├── modelops.config.yaml
│   ├── model/                  # Canonical Markdown + YAML objects
│   ├── generated/              # SQLite DB, JSONL exports
│   └── data/samples/           # Sample datasets
│
├── examples/generic_product_model/ # Generic product domain example
│
├── examples/supplier_vendor_model/ # SAP Supplier / Vendor domain example
│
└── docs/                       # Architecture and developer documentation
    ├── architecture/           # SYSTEM_ARCHITECTURE.md, DOMAIN_MODEL.md, etc.
    ├── developer/              # CODE_STYLE.md, TESTING_STRATEGY.md
    ├── migration/              # Backend inventory, migration risks
    ├── operations/             # Import/export specs
    └── product/                # Acceptance criteria, MVP scope
```

---

## Build and Test Commands

```bash
# Install in editable mode
pip install -e .

# Run the full test suite
pytest

# Run with verbose output
pytest -v

# Lint the codebase
ruff check .

# Format the codebase (if configured)
ruff format .
```

### CLI Usage

After installation, the `modelops` command is available. Use `modelops --help`
and `modelops <command> --help` to see the current surface.

Core repository workflow:

```bash
# Scaffold a new repository
modelops init ./my-model

# Validate canonical files
modelops validate --repo ./my-model

# Build SQLite index + JSONL exports
modelops build-index --repo ./my-model --jsonl

# Check index freshness
modelops index-fresh --repo ./my-model

# Health, scorecard, and diagnostics
modelops health --repo ./my-model
modelops scorecard --repo ./my-model
modelops doctor --repo ./my-model

# Analysis and gap detection
modelops analyze --repo ./my-model
modelops gap-report --repo ./my-model
modelops gaps ./data.csv --repo ./my-model

# Trace, impact, and search
modelops trace ATTR-CUST-SALES-CUSTOMER-GROUP --repo ./my-model
modelops impact FEP-S4-KNVV-KDGRP --repo ./my-model
modelops search "Customer Group" --repo ./my-model
modelops query --type Attribute --repo ./my-model

# Patch proposals and change control
modelops propose-patch --from ./note.md --repo ./my-model
modelops proposal list --repo ./my-model
modelops proposal apply PP-001 --repo ./my-model --dry-run
modelops change-request create --from PP-001 --repo ./my-model
modelops change-request list --repo ./my-model

# Dataset imports and model inference
modelops profile-dataset ./data.csv --repo ./my-model
modelops infer-model --from-profile ./data.csv.profile.json --repo ./my-model
modelops import-model-sheet ./edits.xlsx --repo ./my-model
modelops import-drive <file-id> --repo ./my-model
modelops import-sheet <spreadsheet-id> --repo ./my-model

# Exports and bundles
modelops export-model --repo ./my-model --format xlsx
modelops export-schema --repo ./my-model
modelops export-sheets --repo ./my-model
modelops git-bundle PP-001 --repo ./my-model

# Governance and operations
modelops audit-log --repo ./my-model
modelops usage-report --repo ./my-model
modelops config-guard --repo ./my-model
modelops owners --repo ./my-model
modelops decisions list --repo ./my-model
modelops issue-draft --repo ./my-model
modelops notifications preview --repo ./my-model

# Repository maintenance
modelops diff ./my-model ./other-model
modelops migrate --repo ./my-model
modelops clean --repo ./my-model --dry-run

# Local integration servers (not a user-facing UI)
modelops serve --repo ./my-model
modelops mcp --repo ./my-model
```

> **Note on `serve` and `mcp`:** These start local, agent-facing integration
> servers. They expose the model registry over HTTP and MCP so that pipelines,
> IDEs, and other agents can query it. They are **not** a user-facing web UI.
> The core product remains CLI-driven and backend-first.

---

## Code Style Guidelines

See [`docs/developer/CODE_STYLE.md`](docs/developer/CODE_STYLE.md) for the full contributor guide.

Quick reference:
- **Line length**: 100 characters
- **Target version**: Python 3.11
- **Lint rules**: E, F, I, UP, B
- **Imports**: `from __future__ import annotations` at the top of every module
- **Type hints**: modern syntax (`str | None`, `list[str]`)
- **Naming**: modules `snake_case.py`, classes `PascalCase`, functions `snake_case`, constants `UPPER_SNAKE_CASE`

---

## Testing Instructions

- **Framework**: pytest
- **Configuration**: `testpaths = ["tests"]` and `pythonpath = ["src"]` in `pyproject.toml`
- **Fixtures** in `tests/conftest.py`:
  - `sample_repo`: Copies `examples/customer_bp_model` into a temp directory
  - `temp_model_dir`: Creates a minimal temp model with DOMAIN and ATTR objects

### Test Coverage Areas

| Test File | Coverage |
|---|---|
| `test_cli.py` | Core CLI commands: init, validate, build-index, health, impact |
| `test_cli_contracts.py` | Stable JSON output contracts for agent integrations |
| `test_cli_structure.py` | Command registration and help surface |
| `test_schema_validation.py` | Pydantic schema validation |
| `test_reference_validation.py` | Reference resolution and broken reference detection |
| `test_sap_context_validation.py` | SAP-specific context rules (KNVV, KNB1, KNVP, BUT000, LFA1, LFB1, LFM1) |
| `test_lov_governance.py` | ValueList code uniqueness and LoV governance |
| `test_index_builder.py` | SQLite index generation |
| `test_lineage_edges.py` | Lineage edge export |
| `test_impact_service.py` | BFS impact traversal |
| `test_trace.py` | Upstream/downstream trace |
| `test_patch_apply.py` | Patch application logic |
| `test_patch_proposal_validation.py` | Patch proposal safety checks |
| `test_ai_patch_proposal_service.py` | AI adapter and scaffold proposal behavior |
| `test_ai_usage_telemetry.py` | AI provider telemetry logging |
| `test_repository_parser.py` | Frontmatter parsing |
| `test_gaps.py` | Dataset-to-model gap detection |
| `test_dataset_profiler.py` | CSV/XLSX dataset profiling |
| `test_assessment_package.py` | Migration readiness assessment packs |
| `test_approval_gates.py` | Proposal approval gates |
| `test_change_request_*.py` | Change request service and CLI |
| `test_export_model.py`, `test_export_schema.py`, `test_google_sheets_export.py` | Export formats |
| `test_google_drive_import.py`, `test_google_sheets_import.py`, `test_import_model_sheet.py` | Spreadsheet imports |
| `test_git_bundle.py`, `test_issue_draft.py`, `test_publish_*.py` | GitHub integration |
| `test_mcp_server.py` | MCP server behavior |
| `test_api.py` | FastAPI server routes |
| `test_e2e_demo.py`, `test_e2e_proposal_lifecycle.py`, `test_e2e_proposal_full_lifecycle.py` | End-to-end workflows |

---

## Canonical Object Model

The system manages master data model knowledge through **canonical objects** stored as Markdown files with YAML frontmatter.

### File Format

Each canonical file is either:
- `.md` — Markdown with YAML frontmatter between `---` delimiters
- `.yaml` / `.yml` — YAML-only file

Example:
```markdown
---
id: ATTR-CUST-SALES-CUSTOMER-GROUP
type: Attribute
status: draft
name: Customer Group
domain: DOMAIN-CUSTOMER-BP
---

# Customer Group

Sales-area-dependent customer grouping used in sales processes and reporting.
```

### Object Types

Key object types (defined in `src/modelops_core/schemas/common.py` and `src/modelops_core/schemas/registry.py`):

| Type | Purpose |
|---|---|
| `MasterDataDomain` | Groups model knowledge around a master data area |
| `MigrationObject` | Migration scope, not a single SAP table |
| `BusinessEntity` | Conceptual object (e.g., Customer Sales Area) |
| `EntityContext` | System/business grain and SAP context |
| `Attribute` | Business meaning (semantic object) |
| `AttributeUsage` | How an Attribute behaves in a specific context |
| `FieldEndpoint` | Physical representation (SAP table/field, file column) |
| `Mapping` | Links source and target FieldEndpoints |
| `ValueList` | Defines allowed/reference values |
| `ValueMapping` | Maps source values to target values |
| `Issue` | Captures problems or gaps |
| `Decision` | Captures accepted reasoning |
| `ChangeRequest` | Captures approved model changes |
| `PatchProposal` | Proposes model updates before human approval |

### ID Format

- Must match regex: `^[A-Z][A-Z0-9]*(-[A-Z0-9]+)*$`
- Examples: `DOMAIN-CUSTOMER-BP`, `ATTR-CUST-SALES-CUSTOMER-GROUP`, `FEP-S4-KNVV-KDGRP`
- Every object must have a globally unique stable ID

### Repository Layout

```
model-repository/
  modelops.config.yaml        # Repository configuration
  model/                      # Canonical objects
    DOMAIN-*.md
    ENTITY-*.md
    ATTR-*.md
    FEP-*.md
    MAP-*.md
    ...
  generated/                  # Disposable artifacts (rebuildable)
    modelops.db               # SQLite index
    search_documents.jsonl    # Search export
    lineage_edges.jsonl       # Lineage export
    audit_events.jsonl        # Audit log
    usage_events.jsonl        # Application usage telemetry
    ai_usage_events.jsonl     # AI provider usage telemetry
  data/samples/               # Sample datasets for profiling
```

---

## Validation Pipeline

Validation runs in layers and is **deterministic** — no AI involvement:

1. **Layer 1 — Individual object validation**:
   - `id` is present and matches format
   - `type` is present and is a registered `ObjectType`
   - `status` is present and non-empty
   - `name` or `title` exists (warning if missing)
   - File parses without YAML/Markdown errors

2. **Layer 2 — Cross-object validation**:
   - Duplicate IDs across files
   - Broken references (field points to non-existent object)
   - Reference type mismatches (field expects `Attribute` but points to `System`)

3. **Layer 3 — SAP context validation**:
   - `FieldEndpoint` with `endpoint_type: sap_table_field` must have `entity_context`
   - SAP table → required `context_category` rules:
     - `KNVV` → `customer_sales_area`
     - `KNB1` → `customer_company_code`
     - `KNVP` → `customer_partner_function`
     - `BUT000` → `bp_central`
     - `LFA1` → `vendor_general`
     - `LFB1` → `vendor_company_code`
     - `LFM1` → `vendor_purchasing_org`

Validation results include severity (`ERROR`, `WARNING`, `INFO`), error codes, messages, and suggested fixes.

---

## Security Considerations

- **Local-first architecture**: No cloud dependencies, no network calls required for core operations
- **AI cannot silently mutate canonical files**: All AI-generated changes are `PatchProposal` objects that require human review and approval
- **Deterministic validation before indexing**: Invalid objects are blocked from the index by default (`--allow-invalid` to override)
- **No secrets in repository**: `.env` and `.env.example` only contain `MODELOPS_ENVIRONMENT` and `MODELOPS_LOG_LEVEL`
- **Generated files are disposable**: The `generated/` directory contains rebuildable artifacts and should not be manually edited
- **Dataset files are inputs only**: Raw data in `data/` is never treated as canonical model truth

---

## Key Documentation References

For deeper context, refer to the `docs/` directory:

| Document | Purpose |
|---|---|
| `docs/architecture/SYSTEM_ARCHITECTURE.md` | Full system architecture, data flows, component diagrams |
| `docs/architecture/DOMAIN_MODEL.md` | Conceptual domain model, object relationships, hierarchy |
| `docs/architecture/AI_PATCH_WORKFLOW.md` | AI patch proposal workflow |
| `docs/architecture/DATA_LINEAGE_AND_IMPACT_MODEL.md` | Lineage and impact analysis design |
| `docs/developer/TESTING_STRATEGY.md` | Testing approach and acceptance evidence |
| `docs/developer/CODE_STYLE.md` | Code style conventions (mostly TODO) |
| `docs/product/ACCEPTANCE_CRITERIA.md` | Product acceptance criteria |
| `docs/product/MVP_SCOPE.md` | MVP boundary and scope |

---

## Quick Reference for Agents

- **Add a new canonical object type?** Update `src/modelops_core/schemas/common.py` (add to `ObjectType`) and `src/modelops_core/schemas/registry.py` (add `ObjectTypeEntry` with reference fields).
- **Add a new CLI command?** Add a new `@app.command()` function in `src/modelops_core/cli.py`.
- **Add a new validation rule?** Extend `src/modelops_core/validation/pipeline.py` and add tests in `tests/test_*.py`.
- **Change the generated index schema?** Update `src/modelops_core/index/sqlite_builder.py`.
- **Add a new SAP context rule?** Add to `_SAP_CONTEXT_RULES` in `src/modelops_core/domain_packs/sap.py`.
- **Never** edit files in `generated/` directly — they are rebuilt by `modelops build-index`.
