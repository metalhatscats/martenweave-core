# AGENTS.md — martenweave-core

> This file is for AI coding agents. It describes the project structure, conventions, and workflows you need to know before making changes.

---

## Project Overview

**martenweave-core** (Python package `modelops_core`) is a backend-first **agentic data model registry**. It turns data models into a structured, traceable, validated, AI-ready model knowledge layer. SAP migration and Master Data Management are the first domain pack and proof case, not the product boundary.

**Martenweave Core** is the authoritative backend and canonical model layer. **Martenweave Workbench**
is the official local browser UI for assessment, investigation, review, reports, and controlled
changes. The Workbench connects to Core through the local API and never stores canonical model truth
independently of the `model/` files. It is not a hosted SaaS platform, a generic chatbot, or a
replacement for the CLI-first workflow.

### Product Surfaces

| Surface | Responsibility |
|---|---|
| **Martenweave Core** | Canonical parsing, validation, indexing, gap/lineage/impact analysis, patch proposals, change requests, audit, CLI. |
| **Local API** | Bound FastAPI integration surface for the Workbench and agents (`martenweave serve`). |
| **Martenweave Workbench** | Local browser UI for assessment, object inspection, lineage, gaps, proposals, reports, and controlled changes. |

Agents should place canonical logic, validators, and model mutations in Core; visualization,
navigation, and user guidance in the Workbench; and HTTP adapters, path safety, and capability
reporting in the Local API.

### Core Principles

- **Canonical files are the source of truth.** Markdown + YAML frontmatter objects live in `model/`.
- **Generated index is disposable.** SQLite and JSONL outputs in `generated/` are rebuildable from canonical files.
- **Deterministic validation first.** Every object is validated for IDs, types, references, and SAP context rules before indexing.
- **AI must not silently mutate.** AI creates `PatchProposal` objects for human review. Approved changes become `ChangeRequest`s.
- **Local-first.** No cloud dependencies, no SaaS lock-in.
- **Workbench does not bypass Core.** The Workbench reads and mutates canonical files only through Core services and approval gates.

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
│   ├── __version__.py          # "0.6.1"
│   ├── cli.py                  # Typer CLI entry point (all commands)
│   ├── config.py               # RepoConfig, Settings, path resolution
│   ├── errors.py               # Custom exceptions
│   ├── mcp_server.py           # MCP server for agent integration
│   ├── paths.py                # Path utilities
│   ├── release_preflight.py    # Release packaging checks
│   ├── agents/                 # Agent orchestrators (product-owner, readiness, etc.)
│   ├── ai/                     # AI patch proposal services
│   │   ├── patch_proposal_service.py  # Build PatchProposal from notes
│   │   └── provider_adapter.py        # AI provider abstraction (NoProviderAdapter stub)
│   ├── api/                    # FastAPI server and route handlers
│   ├── approval/               # Approval gate and reviewer workflows
│   ├── assessment/             # Migration readiness assessment packages
│   ├── bundle/                 # GitHub-ready change bundles
│   ├── change_request/         # ChangeRequest lifecycle and validation
│   ├── connectors/             # External source connectors (Google Drive, Sheets, etc.)
│   ├── diff/                   # Repository diff utilities
│   ├── docs/                   # Static documentation and viewer generation
│   ├── domain_packs/           # Domain-specific rules (SAP context validation)
│   ├── exports/                # CSV/XLSX/JSON Schema export services
│   ├── fixtures/               # Canonical object fixture generation
│   ├── gaps/                   # Gap detection between datasets and model
│   ├── guardrails/             # Safety guardrails for AI-assisted workflows
│   ├── impact/                 # Impact analysis via BFS traversal
│   ├── imports/                # Dataset profiling, import sessions, privacy
│   ├── index/                  # SQLite index builder, search documents, lineage edges
│   ├── issue_draft/            # GitHub issue draft generation
│   ├── lineage/                # Lineage edge models and service
│   ├── notifications/          # Notification event generation
│   ├── patching/               # Patch proposal, change request, apply services
│   ├── reports/                # Health, ownership, scorecard, and audit reports
│   ├── repository/             # File parser (Markdown/YAML frontmatter), scanner
│   ├── run/                    # End-to-end workflow runners
│   ├── schemas/                # Pydantic models and object type registry
│   ├── telemetry/              # Audit and usage telemetry
│   ├── trace/                  # Object relationship tracing
│   └── validation/             # Deterministic validation pipeline (Layer 1–3)
│
├── tests/                      # pytest test suite
│   ├── conftest.py             # Shared fixtures: sample_repo, temp_model_dir
│   ├── test_cli.py             # CLI command tests
│   ├── test_e2e_demo.py        # End-to-end demo tests
│   ├── test_impact_service.py
│   ├── test_index_builder.py
│   ├── test_lineage_edges.py
│   ├── test_patch_apply.py
│   ├── test_patch_proposal_validation.py
│   ├── test_reference_validation.py
│   ├── test_repository_parser.py
│   ├── test_sap_context_validation.py
│   └── test_schema_validation.py
│
├── examples/customer_bp_model/ # Full canonical model slice (Business Partner → Customer)
│   ├── modelops.config.yaml
│   ├── model/                  # Canonical Markdown + YAML objects
│   ├── generated/              # SQLite DB, JSONL exports
│   └── data/samples/           # Sample datasets
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

After installation, the primary command is `martenweave`. The `modelops` alias
is also installed for backward compatibility. Run `martenweave --help` for the
full command list; the major groups are:

```bash
# Scaffold and maintain a repository
martenweave init ./my-model
martenweave clean --repo ./my-model
martenweave doctor --repo ./my-model
martenweave migrate --repo ./my-model

# Datasets and external sources
martenweave profile-dataset ./data/sample.csv --repo ./my-model
martenweave import-drive <file-id> --repo ./my-model
martenweave import-sheet <sheet-id> --repo ./my-model
martenweave sources --repo ./my-model
martenweave source-show <source-id> --repo ./my-model
martenweave infer-model --from-profile ./my-model/generated/profiles/sample.csv.json

# Validate, index, and query
martenweave validate --repo ./my-model
martenweave build-index --repo ./my-model --jsonl
martenweave index-fresh --repo ./my-model
martenweave search "customer group" --repo ./my-model
martenweave query --repo ./my-model

# Analysis, reports, impact, and lineage
martenweave health --repo ./my-model
martenweave scorecard --repo ./my-model
martenweave readiness --repo ./my-model
martenweave object-card <object-id> --repo ./my-model
martenweave model-summary --repo ./my-model --out summary.md
martenweave owners --repo ./my-model
martenweave analyze --repo ./my-model
martenweave risk-report --repo ./my-model
martenweave gap-report --repo ./my-model
martenweave trace <object-id> --repo ./my-model
martenweave impact <object-id> --repo ./my-model
martenweave executive-summary --repo ./my-model
martenweave pilot-outcome --repo ./my-model
martenweave diagnostics --repo ./my-model

# Proposals, change requests, reviews, and decisions
martenweave propose-patch --from ./note.md --repo ./my-model
martenweave agent-loop --goal ./goal.md --repo ./my-model
martenweave proposal review --proposal PP-0001 --repo ./my-model
martenweave change-request create --proposal PP-0001 --repo ./my-model
martenweave decisions --repo ./my-model
martenweave git-bundle --proposal PP-0001 --repo ./my-model

# Exports, assessment, and lifecycle
martenweave export-model --format xlsx --repo ./my-model
martenweave export-schema --repo ./my-model
martenweave export-sheets --repo ./my-model
martenweave import-model-sheet ./edits.xlsx --repo ./my-model
martenweave assessment --repo ./my-model
martenweave assessment-review --repo ./my-model
martenweave run dataset-readiness --repo ./my-model
martenweave run migration-assessment --mapping ./workbook.xlsx --out ./out --repo ./my-model
martenweave issue-draft --repo ./my-model
martenweave publish-issue --draft ID-123 --repo ./my-model
martenweave publish-pr --bundle ./bundle --repo ./my-model

# Local integration surfaces
martenweave serve --repo ./my-model --host 127.0.0.1 --port 8000
martenweave workbench --repo ./my-model
martenweave mcp --repo ./my-model

# Utilities
martenweave audit-log --repo ./my-model
martenweave usage-report --repo ./my-model
martenweave docs-build --repo ./my-model
martenweave config-guard --repo ./my-model
martenweave diff ./repo-a ./repo-b
martenweave pilot-preflight --repo ./my-model
martenweave demo-bundle --repo ./my-model
martenweave review-pack --repo ./my-model
martenweave ai-provider --repo ./my-model
martenweave agent product-owner ./note.md --repo ./my-model
martenweave agent readiness --profile pilot --repo ./my-model
martenweave notifications --repo ./my-model
```

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
  - `supplier_repo`: Copies `examples/supplier_vendor_model` into a temp directory
  - `temp_model_dir`: Creates a minimal temp model with DOMAIN and ATTR objects
  - `domain_factory`, `attribute_factory`, `entity_context_factory`,
    `field_endpoint_factory`, `mapping_factory`, `patch_proposal_factory`:
    Frontmatter dict factories for canonical object tests

### Test Coverage Areas

| Test File | Coverage |
|---|---|
| `test_cli.py` | Core CLI commands: init, validate, build-index, health, impact |
| `test_cli_structure.py` | CLI command discovery and argument contracts |
| `test_e2e_demo.py` | End-to-end repository workflow |
| `test_e2e_dataset_workflow.py` | Profile → gap → infer → propose workflow |
| `test_e2e_proposal_full_lifecycle.py` | Proposal → review → bundle → issue/PR lifecycle |
| `test_schema_validation.py` | Pydantic schema validation |
| `test_reference_validation.py` | Reference resolution and broken reference detection |
| `test_sap_context_validation.py` | SAP-specific context rules (KNVV, KNB1, KNVP, BUT000, LFA1, LFB1, LFM1) |
| `test_index_builder.py` | SQLite index generation |
| `test_search_documents.py` | Search document generation |
| `test_lineage_edges.py` | Lineage edge export |
| `test_impact_service.py` / `test_impact_report.py` | BFS impact traversal and report output |
| `test_trace.py` | Upstream/downstream relationship tracing |
| `test_patch_apply.py` | Patch application logic |
| `test_patch_proposal_validation.py` | Patch proposal safety checks |
| `test_proposal_cli.py` / `test_proposal_review_bundle.py` | Proposal review and bundle commands |
| `test_change_request_service.py` / `test_change_request_cli.py` | ChangeRequest lifecycle |
| `test_approval_gates.py` | Approval gate rules |
| `test_gaps.py` / `test_gap_summary_report.py` | Gap detection and reporting |
| `test_dataset_profiler.py` | CSV/XLSX profiling |
| `test_import_model_sheet.py` / `test_export_model.py` | Spreadsheet import/export |
| `test_git_bundle.py` / `test_issue_draft.py` | GitHub bundle and issue draft generation |
| `test_assessment_package.py` / `test_readiness_agent.py` | Assessment and readiness workflows |
| `test_audit_log.py` / `test_telemetry.py` / `test_usage_report.py` | Audit and telemetry |
| `test_repository_parser.py` | Frontmatter parsing |
| `test_secret_guardrails.py` | Safety and secret guardrails |
| `test_docs_build.py` / `test_static_viewer.py` | Documentation and viewer generation |
| `test_mcp_server.py` / `test_api.py` | API and MCP surfaces |

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
| `docs/architecture/WORKBENCH_BOUNDARY.md` | Workbench as an official local UI surface and Core/API responsibilities |
| `docs/architecture/DOMAIN_MODEL.md` | Conceptual domain model, object relationships, hierarchy |
| `docs/architecture/AI_PATCH_WORKFLOW.md` | AI patch proposal workflow |
| `docs/architecture/DATA_LINEAGE_AND_IMPACT_MODEL.md` | Lineage and impact analysis design |
| `docs/developer/TESTING_STRATEGY.md` | Testing approach and acceptance evidence |
| `docs/developer/CODE_STYLE.md` | Code style conventions (mostly TODO) |
| `docs/product/ACCEPTANCE_CRITERIA.md` | Product acceptance criteria |
| `docs/product/MVP_SCOPE.md` | MVP boundary and scope |
| `docs/factory/README.md` | Development AI Factory: agents, skills, gates, autonomy, memory |
| `docs/factory/NORTH_STAR.md` | Product north star agents must not drift from |
| `skills/README.md` | Operational skill cards for agents (validated by `scripts/validate_skills.py`) |

---

## Quick Reference for Agents

- **Work autonomously on the product?** Start with the Development AI Factory: read `docs/factory/memory/PROJECT_MEMORY.md`, then `docs/factory/README.md`, then run `./factory plan` for the next task.
- **Add a new canonical object type?** Update `src/modelops_core/schemas/common.py` (add to `ObjectType`) and `src/modelops_core/schemas/registry.py` (add `ObjectTypeEntry` with reference fields).
- **Add a new CLI command?** Add a new `@app.command()` function in `src/modelops_core/cli.py`.
- **Add a new validation rule?** Extend `src/modelops_core/validation/pipeline.py` and add tests in `tests/test_*.py`.
- **Change the generated index schema?** Update `src/modelops_core/index/sqlite_builder.py`.
- **Add a new SAP context rule?** Add to `_SAP_CONTEXT_RULES` in `src/modelops_core/domain_packs/sap.py`.
- **Add a new agent skill?** Create `skills/<name>/SKILL.md` (sections: When to use, Inputs, Read first, Do not do, Procedure, Validation, Output format), register it in `scripts/validate_skills.py` (`REQUIRED_SKILLS`) and `skills/README.md`, then run `python3 scripts/validate_skills.py`.
- **Never** edit files in `generated/` directly — they are rebuilt by `martenweave build-index`.
