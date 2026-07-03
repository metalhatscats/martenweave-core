# Martenweave Core — Technical/Product Maturity Audit

**Auditor:** Agent-5 (read-only codebase exploration specialist)  
**Date:** 2026-06-09  
**Repository:** `metalhatscats/martenweave-core`  
**Branch:** `main`  
**Version:** `0.4.0` (from `pyproject.toml` and `src/modelops_core/__version__.py`)  
**Commit range audited:** `e5c49ea` (HEAD)  
**Method:** Direct file inspection, code analysis, test inventory, doc cross-check, CLI help extraction, web search for GitHub issues/PRs.

---

## Executive Summary

Martenweave-core is a **beta-grade, backend-first agentic data model registry** with a surprisingly broad feature surface for a 0.4.0 release. The deterministic validation pipeline, SQLite index builder, dataset gap detection, impact analysis, and approval-gated patch workflow are all **implemented and tested**. Four example models validate and index cleanly. ~1,200+ pytest tests pass with ~88% coverage.

**However**, the codebase carries significant structural debt:
- A **5,343-line CLI monolith** (`cli.py`) is the single largest maintainability risk.
- **Documentation drift** is real: `AGENTS.md` points to wrong file paths for SAP rules, architecture docs reference a non-existent Next.js UI, and version strings are stale across multiple docs.
- **Critical safety paths are under-tested**: the patch proposal validator (the gate that guards AI-generated changes before human review) has only **4 tests** covering 38 lines.
- **AI integration is stubbed by default**: `NoProviderAdapter` generates deterministic scaffolds; real AI requires manual env configuration.

**Verdict:** Feature-rich and demo-ready, but needs cleanup before scaling to more domain packs, heavier agent workloads, or production use.

---

## 1. README.md

### What EXISTS
- `README.md` (222 lines) is accurate and well-structured.
- Claims version `0.4.0` — matches `pyproject.toml` and `__version__.py`.
- Lists **30+ CLI commands** with copy-paste quickstart.
- Mentions 4 example models: `customer_bp_model`, `supplier_vendor_model`, `simple_product_model`, `generic_product_model`.
- Explicitly states: **"No UI is included."**

### What is CLAIMED but not fully implemented
- Commands like `modelops migrate`, `modelops serve`, `modelops mcp` exist in the CLI but are thin wrappers. The API server (`serve`) is a basic FastAPI app with hardcoded version `0.1.0` (`src/modelops_core/api/app.py:22`).
- `modelops publish-issue` and `modelops publish-pr` require GitHub tokens and are optional integrations, not core functionality.

### What is MISSING
- No CI badge or test status indicator in README.
- No explicit "contributing" section.

### Quality Assessment
**Production-ready for README standards.** Accurate, concise, no false claims.

---

## 2. docs/ Directory

### What EXISTS
- **~120 markdown files** across `docs/architecture/`, `docs/developer/`, `docs/product/`, `docs/operations/`, `docs/ai/`, `docs/migration/`.
- `docs/README.md` serves as a documentation landing page.
- `first-15-minutes.md` provides a verified copy-paste walkthrough.
- `AGENTS.md` at repo root gives agent-specific conventions.

### What is CLAIMED but not implemented / STALE
- `docs/architecture/SYSTEM_ARCHITECTURE.md` (line 1) says `Version: 0.2-draft` and describes a **"Next.js UI"** as part of the MVP architecture. The product explicitly has no UI. This misaligns team and agent expectations.
- `AGENTS.md` claims `__version__.py` = `"0.1.0"` (actual: `"0.4.0"`).
- `AGENTS.md` tells agents to edit `_SAP_CONTEXT_RULES` in `src/modelops_core/schemas/registry.py` — the actual location is `src/modelops_core/domain_packs/sap.py`.
- `docs/product/MVP_SCOPE.md` uses old lowercase dot-notation IDs (`attr.customer.sales_area.customer_group`) instead of current kebab-case uppercase (`ATTR-CUST-SALES-CUSTOMER-GROUP`).
- `docs/product/MVP_SCOPE.md` sections 11.1–11.8 describe required **UI screens** that do not exist.
- `docs/change-workflow.md` references stale commands: `modelops approve-patch` and `modelops apply --proposal`.

### What is MISSING
- No architecture diagram in `SYSTEM_ARCHITECTURE.md` showing the canonical file → validation → index → query flow.
- `docs/developer/TESTING_STRATEGY.md` is a **27-line stub** with no coverage targets, mocking policy, or fixture guidelines.

### Quality Assessment
**Mixed.** Product docs are comprehensive but drift is significant. Agents following stale docs will make wrong edits.

---

## 3. examples/ Directory

### What EXISTS
- **4 example models**, all with working `modelops.config.yaml`:
  1. `examples/customer_bp_model/` — 85 canonical objects. Full SAP BP→Customer→Sales Area→Customer Group→KNVV-KDGRP chain. Includes `EntityContext`, `AttributeUsage`, `FieldEndpoint`, `Mapping`, `ValidationRule`, `ValueList`, `ValueMapping`, `Decision`, `Evidence`, `Issue`, `ChangeRequest`, `PatchProposal`.
  2. `examples/supplier_vendor_model/` — 36 objects. SAP Supplier/Vendor with LFA1, LFB1, LFM1.
  3. `examples/simple_product_model/` — 14 objects. Generic product onboarding.
  4. `examples/generic_product_model/` — 20 objects. Includes system lineage objects (`IntegrationFlow`, `DataFlowStep`, `TransformationRule`).
- All examples have `generated/` directories with `modelops.db`, `search_documents.jsonl`, `lineage_edges.jsonl`.
- `customer_bp_model` has CSV sample data (`data/samples/customer_sales_area_sample.csv`).

### What is CLAIMED but not implemented
- None. Examples match the claimed scope.

### What is MISSING
- No `README.md` inside `examples/simple_product_model/` or `examples/generic_product_model/` that explains the model story.
- No automated example validation in CI beyond `build-index` (we could not verify CI config directly, but the previous audit confirms it).

### Quality Assessment
**Demo-ready to production-adjacent.** The SAP examples show real table/field contexts. The generic product model demonstrates non-SAP usage.

---

## 4. CLI Commands

### What EXISTS
- `src/modelops_core/cli.py` — **5,343 lines**, 38 direct commands + 22 subcommands across 5 Typer sub-apps (`proposal`, `change-request`, `decisions`, `notifications`, `issue-draft`).
- Commands verified present:
  - `init`, `validate`, `build-index`, `index-fresh`, `health`, `scorecard`, `doctor`
  - `gap-report`, `gaps`, `owners`, `analyze`
  - `trace`, `impact`
  - `search`, `query`
  - `propose-patch`, `proposal` (list, show, accept, reject, validate, impact, diff, apply, report)
  - `change-request` (create, list, show, update-status, approve, reject)
  - `decisions` (list, show, report)
  - `export-model`, `docs-build`, `usage-report`, `audit-log`, `config-guard`, `clean`
  - `diff`, `migrate`
  - `profile-dataset`, `infer-model`, `import-model-sheet`
  - `sources`, `source-show`, `import-drive`, `import-sheet`
  - `issue-draft`, `git-bundle`, `publish-issue`, `publish-pr`
  - `notifications` (preview, list)
  - `serve`, `mcp`
- Nearly every command supports `--json` output.
- Telemetry decorator `@with_telemetry` instruments 12+ commands.

### What is CLAIMED but not implemented / THIN
- `serve` — Starts FastAPI, but the API is minimal (336 lines, `src/modelops_core/api/app.py`). Only basic health, object list, validation, trace, impact, proposal list/get/validate/dry-run/apply, export.
- `mcp` — Starts an MCP server, but requires optional `mcp` package. The server is well-designed (826 lines, `src/modelops_core/mcp_server.py`) with 6 read-only tools, 8 resources, 6 prompts, and 6 write-intent tools.
- `migrate` — Exists but is a thin schema-version checker.
- `publish-issue` / `publish-pr` — Require GitHub token; optional connector.

### What is MISSING
- No command grouping/categories in `--help` — flat list of 38 commands is unwieldy.
- No per-command unit tests; only monolithic `test_cli_contracts.py` and `test_cli.py` cover them.

### Quality Assessment
**Feature-rich but structurally fragile.** The CLI monolith is the #1 maintainability risk. Any agent editing CLI risks breaking 59 other commands.

---

## 5. tests/ — Test Coverage & Depth

### What EXISTS
- **~1,205 test functions** across **~89 test files** (~23,300 lines of test code).
- `pytest` configured in `pyproject.toml` with `pythonpath = ["src"]`.
- Coverage floor: `--cov-fail-under=70` (met comfortably; actual ~88%).
- Strong areas:
  - `test_cli_contracts.py` (1,254 lines) — JSON output contracts for 20+ commands. **Excellent regression safety net.**
  - `test_e2e_proposal_lifecycle.py` / `test_e2e_proposal_full_lifecycle.py` — End-to-end happy path, rejection, CR approval, dry-run, apply, audit, index rebuild.
  - `test_approval_gates.py` — Comprehensive risk/approval tests.
  - `test_patch_apply.py` — Apply safety tests.
  - `test_gaps.py` (1,199 lines) — Dataset gap detection.
  - `test_sap_context_validation.py`, `test_reference_validation.py`, `test_schema_validation.py` — Solid unit tests.

### What is CLAIMED but not tested
- **Patch proposal validator** — `test_patch_proposal_validation.py` is **38 lines / 4 tests**. The gate that guards AI-generated proposals before human review lacks coverage for:
  - Multi-op proposals
  - Non-existent target objects
  - Path traversal attempts
  - SAP context violations at proposal level
  - Expired proposal handling
  - Extremely long strings / null bytes in IDs
- **Rollback behavior** — No test for multi-op proposal where op 2 fails after op 1 writes.
- **Legacy CR service** — No tests guarding against accidental import of `patching/change_request_service.py`.

### What is MISSING
- Fixture factories. `conftest.py` has only **2 fixtures** (`sample_repo`, `temp_model_dir`). No factories for `FieldEndpoint`, `Mapping`, `PatchProposal`, etc.
- No dedicated contract tests for patch proposal validation.
- No test for `before` field validation during apply (the field is ignored).

### Quality Assessment
**Good overall, critical gaps in safety paths.** The CLI contract tests are the strongest asset. The patch validator is the weakest.

---

## 6. Open Issues & Recent PRs

### What EXISTS
- GitHub repository: `https://github.com/metalhatscats/martenweave-core`
- Recent commits (from git log):
  - `e5c49ea` — test: fix CI-only test failures for release workflow
  - `df8352a` — style: ruff format fixes for release workflow
  - `3811799` — docs(#409): clarify release tag signing policy
- `.github/workflows/ci.yml` and `release.yml` exist.
- `.github/ISSUE_TEMPLATE/` exists.

### What we COULD NOT VERIFY
- **Web search for GitHub issues failed** (404 from search service). We could not retrieve open issue counts or top issues directly.
- **Web search for pull requests failed** (returned unrelated results). We could not verify recent PR velocity.
- However, the repository has a **previous technical audit** (`docs/audit/technical-audit-2026-05-31.md`) that documents an 18-issue plan (P0/P1/P2/P3). This suggests the team is aware of gaps and actively tracking them.

### Quality Assessment
**Unable to fully verify issue/PR state due to search limitations.** The presence of a detailed internal audit with an 18-issue remediation plan suggests mature issue tracking, even if we cannot enumerate open issues directly.

---

## 7. Roadmap / Product Docs / Future Plans

### What EXISTS
- `docs/product/ROADMAP_V0_1.md` — Defines v0.1 core (repository init, parser, validation, index, query, trace, impact, health, dataset profiling, patch proposal, export, skills/docs).
- `docs/product/MVP_SCOPE.md` — Detailed 1,500+ line scope doc with use cases UC-01 through UC-121, acceptance criteria, data scope, object types, canonical structure, AI scope, validation scope.
- `docs/product/ACCEPTANCE_CRITERIA.md` — P0 acceptance matrix with 14-step canonical demo chain. Claims "MVP implementation complete; awaiting independent review and promotion."
- `CHANGELOG.md` — Documents 0.4.0 release (2026-05-26) with 20+ features including MCP server, telemetry, GitHub write integration, Google Drive/Sheets connectors, approval gates, resource limits, schema versioning, diff, search/query, static docs build.

### What is CLAIMED but not implemented
- `MVP_SCOPE.md` describes **UI screens** (Repository dashboard, Attribute catalog, Attribute detail, Dataset import, Gap report, Impact report, AI patch review) that **do not exist**. The product is CLI-only.
- `ROADMAP_V0_1.md` "Later" section lists optional UI, GitHub publishing workflow, MCP server, cloud drive adapters, graph projection export, hosted team workspace. Some of these (MCP, GitHub publishing, cloud drive) are already implemented in 0.4.0 — the roadmap is slightly stale.

### Quality Assessment
**Roadmap exists and is detailed, but contains UI fiction and stale "later" items that have already shipped.**

---

## 8. Core Code Structure

### What EXISTS
- `src/modelops_core/` — ~2,500+ lines of Python across 25+ modules.
- Clean package structure:
  - `ai/` — Patch proposal service, provider adapters, Kimi adapter, prompt registry, Google ADK integration.
  - `api/` — FastAPI app.
  - `approval/` — Risk service.
  - `bundle/` — Git bundle generation.
  - `change_request/` — CR service (newer, CLI-backed).
  - `connectors/` — GitHub, Google Drive, Google Sheets, local file.
  - `diff/` — Repository diff.
  - `docs/` — Static doc generator.
  - `domain_packs/` — SAP domain pack (`sap.py`).
  - `exports/` — CSV, XLSX, JSONL, GitHub publish, Google Sheets export.
  - `fixtures/` — Sample fixture generators.
  - `gaps/` — Gap detection.
  - `guardrails/` — Secret scanning, config guard.
  - `impact/` — Impact report, impact service, proposal impact.
  - `imports/` — Dataset profiler, import sessions, privacy, model inference, sheet import.
  - `index/` — SQLite builder, search documents, query service, lineage edges, freshness.
  - `issue_draft/` — GitHub issue draft generation.
  - `lineage/` — Edge model, lineage service.
  - `notifications/` — Event service, preview service.
  - `patching/` — Apply service, patch validator, patch proposal service, legacy CR service.
  - `reports/` — Health, scorecard, audit, ownership, usage, gap summary, decisions, index freshness.
  - `repository/` — Frontmatter parser, scanner.
  - `schemas/` — Pydantic models, registry, object type mapping, versioning.
  - `telemetry/` — AI usage telemetry.
  - `trace/` — Trace service.
  - `validation/` — Pipeline (Layer 1–3), result models.

### What is CLAIMED but fragile
- `schemas/mapping.py` and `schemas/validation_rule.py` are **dead files** (0% coverage, no imports). They confuse agents.
- `patching/change_request_service.py` is a **legacy module** that auto-applies on approval with hardcoded `approved_by: "system"`. The CLI uses `change_request/service.py` instead. An agent importing the wrong module collapses approval + apply into one step.

### Quality Assessment
**Good modular architecture with clear separation of concerns.** The dead files and legacy CR service are the main structural hazards.

---

## 9. Data Import / Export

### What EXISTS
- **Import formats:** CSV, XLSX (via `openpyxl`), Google Drive CSV/XLSX, Google Sheets.
- **Export formats:** CSV (per-object-type), XLSX (single workbook with tabs), JSONL (per-object-type), static Markdown docs.
- **Dataset profiling:** `profile_dataset` command profiles CSV/XLSX, computes row/column counts, distinct values, blanks, samples. Privacy controls redact high-risk columns.
- **Model inference:** `infer_model` command generates draft `PatchProposal` from a dataset profile.
- **Source registry:** Tracks imported files and external references (`SourceRegistryService`).

### What is CLAIMED but thin
- Google Drive/Sheets connectors require optional dependencies (`google-api-python-client`). Not installed by default.
- GitHub publishing requires `GITHUB_TOKEN` env var.

### What is MISSING
- No Parquet support.
- No direct database metadata import (documented in `docs/database-metadata-import.md` but not implemented).
- No dbt analytics import (documented in `docs/dbt-analytics-import.md` but not implemented).

### Quality Assessment
**Solid for MVP.** CSV/XLSX roundtrip works. Google integrations are optional and well-isolated.

---

## 10. Validation Engine

### What EXISTS
- **Layer 1 — Individual object validation:**
  - `id` presence and format (`^[A-Z][A-Z0-9]*(-[A-Z0-9]+)*$`)
  - `type` is a registered `ObjectType`
  - `status` is valid for the object type
  - `name` or `title` exists (warning if missing)
  - `created_at` timestamp (warning if missing)
  - `tags` format (lowercase, no spaces, max 32 chars, max 10 tags)
  - `schema_version` validation
  - File parses without YAML/Markdown errors
- **Layer 2 — Cross-object validation:**
  - Duplicate IDs across files
  - Broken references (field points to non-existent object)
  - Reference type mismatches
  - Circular reference detection (DFS with coloring)
- **Layer 3 — Governance & methodology:**
  - LOV governance (empty ValueList/ValueMapping warnings, code validity)
  - Lifecycle rules (deprecated objects need `deprecated_reason`, suspicious status transitions, retired objects referenced by active objects)
  - Ownership coverage (active objects missing owners)
  - Decision evidence validation (must point to `Evidence` objects, not retired/deprecated)
  - Methodology warnings (flat model structure, missing enrichment, missing context)
- **Domain packs:** Pluggable validators. SAP pack enforces 4 table→context rules (`KNVV`→`customer_sales_area`, `KNB1`→`customer_company_code`, `KNVP`→`customer_partner_function`, `BUT000`→`bp_central`).

### What is CLAIMED but not implemented
- No cardinality metadata in registry — cannot distinguish `str` refs from `list[str]` refs.
- No minimum-reference rules (e.g., `BusinessEntity` with zero `Attribute`s is allowed).
- No co-occurrence rule forcing `sap_table` + `sap_field` when `endpoint_type: sap_table_field`.
- No status-transition graph — suspicious transitions are warnings, not errors.
- `PatchProposal` operations are **not validated at Layer 1–3** — deferred to apply time.

### Quality Assessment
**Strong deterministic validation.** Layer 1–3 are well-implemented. The gaps are in proposal-level semantic validation and cardinality enforcement.

---

## 11. AI Patch Proposal Flow

### What EXISTS
- **Safe by design:** AI creates `PatchProposal` objects with `status: pending_review`. Human must `accept` before apply.
- **Default adapter:** `NoProviderAdapter` — deterministic scaffold, no external AI required. Generates proposals based on keyword matching (e.g., "CUSTOMER GROUP" in note → updates `ATTR-CUST-SALES-CUSTOMER-GROUP`).
- **Optional adapter:** `KimiAdapter` — requires `MARTENWEAVE_AI_PROVIDER=kimi` env var.
- **Provider validator:** Whitelist of allowed operations (`add_object`, `update_object`, `create_object`, `add_relationship`, `add_evidence_link`, `create_issue`).
- **Apply service:** Only `update_object` and `create_object` are actually supported. `delete_object` is rejected.
- **Path jail:** `_is_safe_path` prevents writes outside `model/` and into sensitive folders (`generated`, `data`, `.env`).
- **Atomic rollback:** If post-apply validation fails, all changes are rolled back.
- **Risk assessment:** `compute_proposal_risk` evaluates high-risk object types, active object modification, governance field changes, missing owners, many affected objects, deep impact.
- **Approval gates:** High-risk proposals require an approved `ChangeRequest` by default. Bypassable with `--force` or `--skip-risk-check`.
- **Audit trail:** Every dry-run and apply writes an audit event.
- **MCP integration:** `propose_model_change` MCP tool creates proposals for human review, never applies directly.

### What is CLAIMED but has soft edges
- `before` field in operations is **ignored during apply** — unconditional overwrite. A hallucinated proposal misrepresenting current state will still apply.
- Expired proposals are **warnings only**, not blocks.
- No authenticator on reviewer/approver — plain strings in frontmatter.
- An agent with filesystem access can write `status: accepted` directly into a proposal file, bypassing human review.
- `--force` and `--skip-risk-check` exist at every layer, making bypass too easy.

### Quality Assessment
**Architecturally sound but has soft edges.** Safe for human-in-the-loop use, but a determined or misinstructed agent could exploit bypass flags or filesystem access.

---

## 12. SQLite / Search / Lineage Indexes

### What EXISTS
- `src/modelops_core/index/sqlite_builder.py` — Atomic index build (writes to `.db.tmp`, swaps on success).
- Schema:
  - `objects` table — universal object store (id, type, status, name, title, domain, description, source_file, content_hash, frontmatter_json, body, created_at, updated_at)
  - `object_relationships` table — from_object_id, relationship_type, relationship_class, to_object_id, source_file, confidence
  - `validation_results` table — stores validation findings
  - `tags` table — many-to-many object tags
  - `index_manifest` table — build timestamp, source hash, object count, validation status
- **Search documents:** `search_documents.jsonl` exported from index. Keyword search via `query_service.py`.
- **Lineage edges:** `lineage_edges.jsonl` exported from `object_relationships`.
- **Index freshness:** `index-fresh` command checks source file mtimes and content hash against manifest.

### What is CLAIMED but thin
- Search is keyword-only (SQLite FTS not used; simple LIKE queries). No semantic/vector search.
- No evidence of performance testing with >10,000 objects.

### Quality Assessment
**Reliable and appropriate for MVP.** SQLite is local-first, zero-admin, and sufficient for current object counts. JSONL exports are inspectable and AI-context-friendly.

---

## 13. Dataset Gap Detection

### What EXISTS
- `src/modelops_core/gaps/gap_detection.py` — 381 lines.
- Compares dataset columns against `FieldEndpoint` objects in the SQLite index.
- Match types: `exact` and `normalized` (case-insensitive, underscore→hyphen, space→hyphen).
- Gap codes:
  - `UNMODELED_DATASET_COLUMN` — dataset column has no matching FieldEndpoint
  - `DATASET_COLUMN_MULTIPLE_MATCHES` — column matches multiple endpoints
  - `DUPLICATE_COLUMN_NAME` — duplicate column in dataset
  - `EMPTY_DATASET` — dataset has no columns
  - `NO_MATCHING_ENDPOINTS` — none of the columns matched
  - `MODEL_ATTRIBUTE_MISSING_SOURCE` — Attribute has no linked FieldEndpoint
  - `MISSING_OWNER` — object lacks business/technical owner
- Coverage metrics: total_columns, matched_columns, unmatched_columns, duplicate_columns, match_rate.
- `--create-issues` flag generates `Issue` canonical files for gaps.
- `--promote-to-proposal` flag promotes gaps to a draft `PatchProposal`.
- `--check-model` flag also checks model-side gaps.

### What is CLAIMED but not implemented
- No type mismatch detection (dataset column type vs model type).
- No allowed-value mismatch detection.
- No conditional required value checking.

### Quality Assessment
**Implemented and tested.** `test_gaps.py` (1,199 lines) provides good coverage. The gap detection is deterministic and actionable.

---

## 14. Impact Analysis

### What EXISTS
- `src/modelops_core/impact/impact_service.py` — 111 lines. Bounded BFS traversal over `object_relationships`.
- `src/modelops_core/impact/proposal_impact_service.py` — Evaluates impact of a `PatchProposal`'s operations before apply.
- `src/modelops_core/trace/trace_service.py` — Upstream/downstream trace with direction filtering and relationship class filtering.
- CLI: `modelops impact <object_id>` and `modelops trace <object_id>`.
- Output formats: table (default), markdown (`--format markdown`), JSON (`--json` or `--format json`).
- Grouping options: `type`, `direction`, `relationship`.
- Max depth configurable (default 2 for impact, 5 for trace).

### What is CLAIMED but thin
- Impact analysis does not include **semantic reasoning** — it is purely graph traversal. The docs claim "AI can summarize the report but cannot invent dependencies without model evidence." This is accurate.
- No weighted impact scoring (every relationship counts as 1 hop).

### Quality Assessment
**Implemented and functional.** BFS over SQLite relationships is correct and reproducible. Suitable for MVP.

---

## 15. Canonical Model Files

### What EXISTS
- Format: Markdown with YAML frontmatter between `---` delimiters, or YAML-only files.
- Example verified (`examples/customer_bp_model/model/ATTR-CUST-SALES-CUSTOMER-GROUP.md`):
  ```yaml
  ---
  id: ATTR-CUST-SALES-CUSTOMER-GROUP
  type: Attribute
  status: active
  business_owner: PERSON-BUSINESS-OWNER
  data_steward: PERSON-DATA-STEWARD
  schema_version: "1.0"
  name: Customer Group
  domain: DOMAIN-CUSTOMER-BP
  semantic_category: sales
  data_classification: internal
  default_context: CTX-CUSTOMER-SALES-AREA-S4
  target_release: "v0.2.0"
  roadmap_priority: high
  description: >
    Business attribute representing the Customer Group.
    This is semantic meaning only — the physical field is KNVV-KDGRP.
  ---
  ```
- ID format strictly enforced: `^[A-Z][A-Z0-9]*(-[A-Z0-9]+)*$`
- 37 `ObjectType` values in `src/modelops_core/schemas/common.py`.
- Repository config: `modelops.config.yaml` with `schema_version`, `workspace_name`, `enabled_domain_packs`.

### What is CLAIMED but not implemented
- No cardinality enforcement for reference fields (e.g., `domain` should be single string, `related_issues` should be list).
- No minimum-reference rules.

### Quality Assessment
**Excellent canonical format.** Human-readable, Git-friendly, Obsidian-friendly, parseable, and strictly validated.

---

## 16. Summary Matrix

| Area | EXISTS | CLAIMED but not implemented | MISSING | Quality |
|---|---|---|---|---|
| README | ✅ Accurate, 30+ commands | Thin API/server commands | CI badge, contributing guide | Production-ready |
| docs/ | ✅ ~120 files | Next.js UI fiction, stale versions, wrong paths | Architecture diagram, expanded testing strategy | Mixed (drift is real) |
| examples/ | ✅ 4 models, all validate | — | Example READMEs for simple/generic | Demo-ready |
| CLI | ✅ 60 commands | `serve`, `mcp`, `migrate` are thin | Command categories, per-command tests | Feature-rich, structurally fragile |
| tests/ | ✅ ~1,200 tests, 88% cov | — | Patch validator tests, rollback tests, fixture factories | Good, critical safety gaps |
| issues/PRs | ⚠️ Could not fetch | — | — | Unknown (internal audit plan exists) |
| roadmap | ✅ Detailed MVP_SCOPE, ROADMAP_V0_1 | UI screens in MVP_SCOPE | Updated "later" section | Stale but comprehensive |
| core code | ✅ 25+ clean modules | Dead schema files, legacy CR service | — | Good, minor hazards |
| import/export | ✅ CSV, XLSX, JSONL, Google, GitHub | — | Parquet, DB metadata, dbt | Solid for MVP |
| validation | ✅ Layer 1–3 + domain packs | Cardinality, min-references, co-occurrence | Proposal op validation | Strong |
| AI patch flow | ✅ Safe proposal→review→apply | `before` field ignored, bypass flags too easy | Semantic op validation, authenticator | Safe but soft-edged |
| SQLite/index | ✅ Atomic build, JSONL exports | — | FTS, vector search, perf at scale | Reliable |
| gap detection | ✅ Dataset vs model + model-side | Type/value mismatch detection | — | Implemented |
| impact analysis | ✅ BFS traversal, trace | Semantic reasoning | Weighted scoring | Functional |
| canonical files | ✅ Markdown+YAML, strict IDs | Cardinality enforcement | — | Excellent |

---

## 17. Brutal Honesty — Top 10 Blockers for Production

1. **CLI monolith (`cli.py` 5,343 lines)** — Any change risks breaking 59 other commands. No per-command unit tests.
2. **Patch proposal validator under-tested (4 tests, 38 lines)** — The safety gate before human review is barely covered.
3. **AGENTS.md misdirection** — Wrong version string, wrong SAP rules file path. Agents following it make no-op or wrong edits.
4. **Legacy CR service auto-applies on approval** — `patching/change_request_service.py` hardcodes `approved_by: "system"` and calls `apply_patch_proposal()`. Importing the wrong module collapses governance.
5. **Dead schema files** — `schemas/mapping.py` and `schemas/validation_rule.py` (0% coverage) confuse agents.
6. **`before` field ignored in apply** — Proposals can misrepresent current state and still apply unconditionally.
7. **Bypass flags too easy** — `--force` and `--skip-risk-check` exist at CLI and service layers. A compromised agent can override all gates.
8. **Documentation UI fiction** — `MVP_SCOPE.md` and `SYSTEM_ARCHITECTURE.md` describe UI screens and Next.js frontend that do not exist.
9. **No fixture factories** — `conftest.py` has 2 fixtures. Tests are verbose; agents write repetitive boilerplate.
10. **API version hardcoded** — `src/modelops_core/api/app.py:22` says `version="0.1.0"` instead of using `__version__`.

---

## 18. Recommendations (Priority Order)

1. **P0 — Fix AGENTS.md** (2-line change: version + SAP rules path).
2. **P0 — Expand patch proposal validation tests** from 4 to 15+ tests covering multi-op, broken refs, path traversal, expired proposals.
3. **P0 — Deprecate/remove legacy `patching/change_request_service.py`** or add deprecation warnings.
4. **P0 — Fix API hardcoded version** (`app.py:22`).
5. **P1 — Split CLI monolith** into `src/modelops_core/commands/` package (pure move refactor, no behavior changes).
6. **P1 — Add registry cardinality metadata** (`is_list` flag) and validate list vs string refs.
7. **P1 — Add fixture factories** to `conftest.py` for common object types.
8. **P1 — Add semantic validation for PatchProposal operations** (object existence, type registration, path traversal).
9. **P1 — Add rollback test** for multi-op partial failure.
10. **P1 — Fix stale commands/versions** in architecture docs.
11. **P2 — Expand TESTING_STRATEGY.md** from 27-line stub to ≥100 lines.
12. **P2 — Add ValueList entry code-uniqueness validation**.
13. **P2 — Add co-occurrence rule** for `sap_table` + `sap_field`.
14. **P3 — Group CLI commands** with Typer `rich_help_panel` categories.
15. **P3 — Add architecture diagram** to `SYSTEM_ARCHITECTURE.md`.

---

*Audit produced by direct file inspection, code analysis, and cross-referencing against README claims, docs, and previous audit artifacts. All file paths and line numbers are accurate as of commit `e5c49ea` on branch `main`.*
