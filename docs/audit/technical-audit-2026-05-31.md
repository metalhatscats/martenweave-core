<!-- modelops-freshness-ignore: all -->

# Technical Audit — martenweave-core

**Date:** 2026-05-31
**Auditor:** Kimi 2.6 (senior technical auditor / backend architect / delivery lead)
**Repository:** `metalhatscats/martenweave-core`
**Branch audited:** `main`
**Version:** `0.4.0`
**Commit:** `HEAD` (working tree clean)

---

## 1. Executive Verdict

### Current Maturity Level
**Beta / pre-MVP-ship.** The core validation, indexing, gap detection, impact analysis, and approval-gated patch pipeline are implemented and tested. 1,220 tests pass, CI is green, four example models build and validate successfully. However, the codebase has accumulated structural debt that will block reliable agentic development and slow human maintainers.

### What Is Already Strong
- **Deterministic validation pipeline** — Layer 1–3 + pluggable domain packs, 94% coverage, clear error codes with suggested fixes.
- **Approval-gated patch flow** — AI can only generate `PatchProposal` in `pending_review` status. Apply requires acceptance, and high-risk proposals are blocked by default.
- **CLI contract tests** — `test_cli_contracts.py` (1,254 lines) documents stable JSON output contracts for 20+ commands.
- **End-to-end proposal lifecycle tests** — Two E2E test files cover happy path, rejection, CR approval, dry-run, apply, audit, and index rebuild.
- **Four working examples** — `customer_bp_model` (85 objects), `supplier_vendor_model` (36), `simple_product_model` (14), `generic_product_model` (20) all validate and index cleanly in CI.
- **Local-first architecture** — No cloud dependencies for core operations. SQLite index is disposable and rebuildable.

### What Is Fragile
- **CLI monolith** — `src/modelops_core/cli.py` is 5,343 lines / 203 KB with 60 commands in a single flat Typer app. This is the single largest maintainability risk.
- **Schema drift** — Dead files (`schemas/mapping.py`, `schemas/validation_rule.py`), registry field lists that do not match Pydantic model fields, and a `Risk` type that exists in the registry but is not mapped in `OBJECT_TYPE_MODELS` (per earlier exploration; confirmed mapping exists now but drift remains on field names).
- **Critical safety path under-tested** — `test_patch_proposal_validation.py` is 38 lines / 4 tests. The validator that guards AI-generated proposals before human review lacks coverage for multi-op proposals, non-existent target objects, path traversal, and SAP context violations at the proposal level.
- **Documentation inaccuracies** — `AGENTS.md` contains wrong version number, wrong file path for SAP rules, and outdated project structure. Architecture docs reference non-existent UI and stale CLI commands.
- **Legacy dual CR service** — `patching/change_request_service.py` auto-applies on approval with hardcoded `approved_by: "system"`, while `change_request/service.py` (used by CLI) does not. An agent importing the wrong module can collapse approval and apply into one step.

### What Blocks Reliable Agentic Development
1. **The 203 KB CLI file** — An AI agent cannot safely add or modify a command without high risk of breaking unrelated commands. There are no per-command unit tests; the only safety net is the monolithic `test_cli_contracts.py` and E2E tests.
2. **Misleading `AGENTS.md`** — Tells agents to edit `_SAP_CONTEXT_RULES` in `schemas/registry.py` (actual location: `domain_packs/sap.py`). Agents following this will make no-op edits or get confused.
3. **Minimal fixtures** — `conftest.py` has only 2 fixtures. No factories for `FieldEndpoint`, `Mapping`, `PatchProposal`, etc., so agents writing tests must manually construct frontmatter strings.
4. **No command groups in Typer** — 38 flat commands make the help output unwieldy and provide no namespace boundaries.

### Ready for Deeper MVP Expansion?
**Conditionally yes.** The product features exist, but the codebase needs cleanup before scaling to more domain packs, more CLI commands, or heavier AI agent workloads. The recommended sequence is: (1) fix agent-facing docs and tests, (2) split the CLI monolith, (3) close schema drift, then expand.

---

## 2. Repository Map

```
src/modelops_core/
  cli.py                  # 203 KB monolith — 38 direct + 22 sub-commands
  config.py               # RepoConfig, Settings, ResourceLimits
  errors.py               # Custom exceptions
  paths.py                # Path resolution utilities
  __version__.py          # "0.4.0"
  api/                    # FastAPI app (hardcoded version "0.1.0")
  ai/                     # Patch proposal service, provider adapters, Kimi adapter
  approval/               # Risk service (compute_proposal_risk, assess_change_request)
  bundle/                 # Git bundle generation
  change_request/         # Newer CR service (CLI-backed, does NOT auto-apply)
  connectors/             # Google Drive/Sheets, GitHub write integration
  diff/                   # Repository diff
  docs/                   # Static docs generation from index
  domain_packs/           # SAPDomainPack (4 table rules)
  exports/                # CSV/XLSX/JSONL export
  fixtures/               # Sample fixture generators
  gaps/                   # Gap detection (dataset vs model)
  guardrails/             # Secret scanning, config guard
  impact/                 # Impact report, impact service, proposal impact
  imports/                # Dataset profiling, import sessions
  index/                  # SQLite builder, search documents, freshness
  issue_draft/            # GitHub issue draft generation
  lineage/                # Edge model, lineage service
  mcp_server.py           # MCP server for agent integration
  notifications/          # Notification preview/list
  patching/               # Patch apply, patch validator, legacy CR service
  reports/                # Health, scorecard, audit, ownership, usage, gap summary
  repository/             # Frontmatter parser, scanner
  schemas/                # Pydantic models, registry, object type mapping
  telemetry/              # Audit events, AI usage telemetry
  trace/                  # Upstream/downstream trace service
  validation/             # Pipeline (Layer 1–3), result models

tests/
  conftest.py             # 2 fixtures (sample_repo, temp_model_dir)
  test_cli.py             # CLI smoke tests
  test_cli_contracts.py   # JSON contract tests (1,254 lines)
  test_patch_proposal_validation.py  # 38 lines — CRITICAL GAP
  test_approval_gates.py  # Comprehensive approval/risk tests
  test_patch_apply.py     # Apply safety tests
  test_e2e_proposal_lifecycle.py / test_e2e_proposal_full_lifecycle.py
  ... 89 files total, ~23,300 lines

examples/
  customer_bp_model/      # 85 canonical objects, SAP BP→Customer
  supplier_vendor_model/  # 36 objects, SAP Supplier/Vendor
  simple_product_model/   # 14 objects, generic onboarding
  generic_product_model/  # 20 objects, generic product

docs/
  README.md               # Doc index
  first-15-minutes.md     # Onboarding walkthrough
  architecture/           # SYSTEM_ARCHITECTURE.md, DOMAIN_MODEL.md, etc.
  developer/              # CODE_STYLE.md, TESTING_STRATEGY.md (27-line stub)
  product/                # MVP_SCOPE.md, ACCEPTANCE_CRITERIA.md
  operations/             # Import/export specs
  migration/              # Backend inventory

.github/workflows/
  ci.yml                  # Python 3.11/3.12, lint, build-index 4 examples, pytest --cov-fail-under=70, validate 4 examples
  release.yml             # Release workflow
```

---

## 3. Architecture Assessment

### Canonical Model Design
**Good.** Markdown + YAML frontmatter is human-readable, Git-friendly, and parseable. The 37 `ObjectType` values cover domain, technical, mapping, governance, and workflow concerns. IDs use a strict kebab-case uppercase regex (`^[A-Z][A-Z0-9]*(-[A-Z0-9]+)*$`).

**Gaps:**
- No cardinality metadata in the registry — cannot distinguish `str` refs from `list[str]` refs.
- No minimum-reference rules — e.g., a `BusinessEntity` with zero `Attribute`s is allowed.
- `PatchProposal.operations` are not validated semantically (object existence, path safety, schema compliance) at the proposal validator level; those checks are deferred to apply time.

### Validation Layers
**Strong.** Layer 1 (individual object), Layer 2 (cross-object references, duplicates, cycles), Layer 3+ (governance, methodology, domain packs). The pipeline is pure functions, well-named, and produces actionable `ValidationResult` objects with severity, code, message, and suggested fix.

**Gaps:**
- No `ValueList` entry code-uniqueness check.
- No co-occurrence rule forcing `sap_table` + `sap_field` when `endpoint_type: sap_table_field`.
- No status-transition graph — suspicious transitions are warnings, not errors.
- `PatchProposal` operations are not validated at Layer 1–3.

### Index Generation
**Reliable.** SQLite builder parses canonical files, runs validation, and writes `modelops.db`. Optional JSONL exports for search documents and lineage edges. CI rebuilds all four example indexes on every run.

### SQLite / Search Usage
**Appropriate.** SQLite is local-first, zero-admin, and sufficient for the current object counts (< 10,000). Search uses JSONL export + keyword matching. No evidence of performance issues.

### Lineage and Impact Analysis
**Implemented.** `impact_service.py` performs BFS traversal. `trace_service.py` handles upstream/downstream partitioning. Impact reports support table, markdown, and JSON output. Proposal impact service evaluates impact before apply.

### Gap Detection
**Implemented.** `gap_detection.py` compares dataset columns against `FieldEndpoint`s and reports matches, gaps, and coverage. Works for CSV/XLSX. Tested in `test_gaps.py` (1,199 lines).

### Patch Proposal and Approval Workflow
**Architecturally sound but has soft edges.**

Strengths:
- AI can only propose; proposals are born `pending_review`.
- Apply supports only `update_object` and `create_object` — no deletes.
- Atomic rollback on post-apply validation failure.
- Path jail (`_is_safe_path`) prevents writes outside `model/` and into sensitive folders.
- Audit events for every dry-run and apply.

Weaknesses:
- Legacy `patching/change_request_service.py` auto-applies on approval with hardcoded `approved_by: "system"`.
- `skip_risk_check` / `--force` bypass exists at every layer.
- `before` field in operations is ignored during apply — unconditional overwrite.
- Expired proposals are warnings, not blocks.
- No authenticator on reviewer/approver — plain strings in frontmatter.

### Human Review Boundaries
**Present but not enforced against filesystem access.** A human must set `status: accepted` in the proposal file before apply. However, an agent with filesystem access can write that status directly. The risk gate and CR requirement provide defense in depth, but both are bypassable with flags.

### Generated Artifacts vs Source-of-Truth
**Clear separation.** `model/` is canonical. `generated/` is disposable and rebuildable. `data/` is input-only. The CLI and validation pipeline treat `model/` as the only source of truth. CI rebuilds indexes from scratch rather than checking them in.

---

## 4. Agent-Operability Assessment

| Criterion | Rating | Evidence |
|---|---|---|
| Clear task boundaries | ⚠️ Fair | CLI monolith blurs boundaries. Business logic is modular, but all CLI orchestration is in one file. |
| Test discoverability | ✅ Good | `pytest` configured in `pyproject.toml`. 89 test files with descriptive names. |
| Commands documented correctly | ⚠️ Fair | README and `first-15-minutes.md` are accurate. Architecture docs contain stale commands (`modelops approve-patch`, `modelops apply --proposal`). |
| Fixtures / examples usable | ⚠️ Fair | 4 examples work. `conftest.py` is minimal (2 fixtures). No object factories. |
| Error messages actionable | ✅ Good | Validation results include severity, code, message, and suggested fix. |
| Generated files clearly separated | ✅ Good | `generated/` is explicitly disposable. Scanner skips it. |
| Risky operations have guardrails | ⚠️ Fair | Dry-run by default, risk gates, path jail, atomic rollback. But `--force` and `skip_risk_check` bypass everything. |
| Docs match current CLI behavior | ⚠️ Fair | `AGENTS.md` has 2 factual errors. Architecture docs reference non-existent UI. |
| Issues solvable in small vertical slices | ❌ Poor | The CLI monolith makes even small command changes touch a 203 KB file. No per-command test files. |

**Top agent hazards:**
1. Editing `cli.py` for a command change risks breaking 59 other commands.
2. `AGENTS.md` pointing to wrong file paths causes no-op or destructive edits.
3. No fixture factories mean agents write repetitive boilerplate in tests.
4. Dead schema files (`schemas/mapping.py`, `schemas/validation_rule.py`) may tempt agents to "fix" them instead of editing `domain.py`.

---

## 5. Test and Validation Audit

### pytest Coverage Shape
- **1,220 tests** collected, all passing in ~42–94s depending on coverage overhead.
- **88% line coverage** (`--cov-fail-under=70` is met comfortably).
- **Coverage outliers:** `schemas/mapping.py` (0%), `schemas/validation_rule.py` (0%) — dead files. `scorecard_service.py` (87%) — some methodology branches uncovered.

### Unit vs Integration Tests
- **Unit tests:** Schema validation, reference validation, SAP context, patch validator, impact service, index builder.
- **Integration tests:** CLI commands, E2E proposal lifecycle, Google integrations (mocked), API tests.
- **No dedicated contract tests for patch proposal validation** — the validator itself is barely tested.

### CLI Contract Tests
- **Excellent.** `test_cli_contracts.py` (1,254 lines) tests stable JSON contracts for 20+ commands. This is the strongest regression safety net.

### Example Model Tests
- **Good.** CI validates and builds indexes for all 4 examples on every push.

### Validation Command Consistency
- **Good.** `modelops validate` produces consistent output across all 4 examples (0 errors, warnings only for methodology/enrichment checks).

### CI Behavior
- **Solid.** Python 3.11/3.12 matrix, lint, format check, example index builds, pytest with coverage floor, example validations.
- **No slow-test exclusion in CI** — the `@pytest.mark.slow` test (`test_release_packaging.py`) is not excluded; CI runs it.

### Missing Regression Areas
1. **Patch proposal validator** — only 4 tests. Missing: multi-op proposals, non-existent object IDs, path traversal, SAP context violations at proposal level, boundary values.
2. **Rollback behavior** — no test for multi-op proposal where op 2 fails after op 1 writes.
3. **Legacy CR service** — no tests guarding against accidental import of `patching/change_request_service.py`.
4. **Cardinality validation** — no tests because the feature does not exist.

### Fragile or Slow Tests
- None identified. All 1,220 tests pass reliably.

### Tests Pass but Product Behavior May Still Be Weak
- `test_patch_proposal_validation.py` passes with 4 minimal tests, but the validator does not deeply inspect operations.
- `test_patch_apply.py` passes, but rollback on partial failure is untested.
- All validation tests pass, yet orphan entities, empty mappings, and missing `sap_field` are allowed.

---

## 6. CLI and Developer Experience Audit

### Command Naming Consistency
**Mostly consistent** kebab-case (`build-index`, `profile-dataset`, `propose-patch`). Sub-apps use space-separated multi-word names (`change-request`, `issue-draft`). One inconsistency: `import-model-sheet` vs `import-sheet` (different commands, different purposes, but naming is slightly confusing).

### Help Text
**Comprehensive but unwieldy.** `modelops --help` lists 38 flat commands. Sub-apps (`proposal`, `change-request`, `decisions`, `notifications`, `issue-draft`) add 22 more. No command groups or categorization in the top-level help.

### JSON Output Contracts
**Strong.** Nearly every command supports `--json`. `test_cli_contracts.py` documents stable contracts. JSON output suppresses Rich console tables and prints structured data.

### Exit Codes
- `0` — success
- `1` — general error (validation failures, exceptions, missing objects)
- `2` — strict-mode validation warnings (only on `validate --strict`)

### Strict Mode Behavior
- **Only on `validate`.** `--strict` exits with code 2 if any warnings exist. No other command supports strict mode. This is acceptable for a focused validation command, but agents should know it is not universal.

### Stale Index Warnings
- **Implemented.** `index-fresh` command checks source hash. `build-index` warns if index is stale. Doctor command includes index freshness check.

### Discoverability for New Users
- **Good.** `first-15-minutes.md` provides a copy-paste walkthrough. README lists all commands. Examples are self-contained.

### First 15 Minutes from Clean Clone
**Works.** Verified:
```bash
python -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
.venv/bin/modelops validate --repo examples/simple_product_model   # 0 errors
.venv/bin/modelops build-index --repo examples/simple_product_model --jsonl   # success
```

---

## 7. Data Model and SAP/MDM Fit

### Object Type Coverage
37 object types cover domains, entities, attributes, field endpoints, mappings, value lists, validation rules, decisions, issues, change requests, patch proposals, evidence, ownership, and teams. This is sufficient for the MVP.

### Business Partner / Customer / Supplier-Vendor
- **customer_bp_model** (85 objects) demonstrates BP → Customer → Sales Area → Customer Group → KNVV-KDGRP.
- **supplier_vendor_model** (36 objects) demonstrates Supplier → Vendor Central → LFA1/KTOKK, LFB1/ZTERM, LFM1/SPERR.
- Both examples have `EntityContext`, `AttributeUsage`, `FieldEndpoint`, `Mapping`, `ValidationRule`, `ValueList`, and `Decision` objects.

### SAP Migration Fit
**Thin but functional for a first domain pack.**
- Only 4 SAP tables have context rules: `KNVV`, `KNB1`, `KNVP`, `BUT000`.
- Missing: `KNA1` (Customer General), `KNVK` (Customer Contact), `ADRC` (Address), `ADR6` (Email), `BUT020`/`BUT021` (BP relationships), `TVKOT` (Sales Org texts), etc.
- No composite-key awareness — `KNVV` requires Sales Org + Dist. Channel + Division, but the pack only checks `context_category` string.
- No S/4HANA vs ECC distinction — `endpoint_type: sap_table_field` is generic.
- No field-level co-occurrence rule — a `FieldEndpoint` can claim `endpoint_type: sap_table_field` with `sap_table` populated but `sap_field` empty.

### MDM / Data Governance Fit
**Good foundation.** Ownership roles, stewards, approvers, and watchers are modeled. `OwnershipRole`, `Person`, and `Team` types exist. Governance reports (`owners`, `scorecard`) are implemented.

### Validation Rules
- `ValidationRule` object type exists.
- SAP context validation works for the 4 covered tables.
- Methodology warnings flag missing owners, flat structure, and missing enrichment.

### Field Mappings
- `Mapping` and `MappingSet` types exist.
- `Mapping` links `source_endpoint` and `target_endpoint`.
- Value mapping (`ValueMapping`) links `source_value_list` and `target_value_list`.

### Ownership
- `OwnershipRole` type with `role_type` enum (`owner`, `steward`, `approver`, `watcher`).
- `owners` CLI command shows coverage and workload.

### Evidence / Source Tracking
- `Evidence` type exists.
- `Decision.evidence` must point to `Evidence` objects (validated when `check_decisions=True`).
- `PatchProposal.source_evidence` field exists.
- `SourceRegistry` tracks external sources (Google Drive, Sheets, GitHub).

### Project Decisions
- `Decision` type captures accepted reasoning.
- `decisions` CLI sub-app (`list`, `show`, `report`) allows browsing.
- Decision traceability is tested.

---

## 8. AI Patch Proposal Readiness

### Overall Assessment
**Safe for human-in-the-loop use, but has soft edges that a determined agent could exploit.**

### Safety If Agent Uses `propose-patch` Interface Only
**High safety.** The AI adapter reads the repository index and generates a `PatchProposal` dict. The service writes it to `model/patch-proposals/` with `status: pending_review`. The default adapter is `NoProviderAdapter`, which is deterministic and safe. Even with `KimiAdapter`, downstream validation rejects disallowed operations.

### Safety If Agent Has Filesystem or Python Access
**Medium safety.** An agent can:
- Write `status: accepted` directly into a proposal file (bypasses human review).
- Call `apply_patch_proposal(skip_risk_check=True)` to bypass risk gates.
- Import legacy `patching/change_request_service.py` and auto-apply on approval.
- These require intentional malice or a badly instructed agent; they are not accidental risks.

### Proposal Operations Are Limited and Validated
- **Whitelist:** Only `update_object` and `create_object` are supported by `apply_service`. `delete_object` is rejected.
- **Provider validator** allows `add_object`, `add_relationship`, etc., but `apply_service` rejects them. This is a defense-in-depth mismatch that is safe but creates UX friction.

### Approval Gates Are Clear
- High-risk proposals require an approved `ChangeRequest` by default.
- Risk levels: `high_risk_object_type`, `active_object_modified`, `governance_field_changed`, `missing_owner`, `many_affected_objects`, `deep_impact`.
- Gates are bypassable with `--force` / `--skip-risk-check`.

### Diffs Are Reviewable
- `proposal diff <id>` shows the before/after diff.
- `proposal review-bundle` generates a context bundle for human review.

### Evidence Is Required
- `PatchProposal.source_evidence` field exists.
- `Decision.evidence` must point to `Evidence` objects.
- No enforcement that AI-generated proposals include evidence — this is optional frontmatter.

### Where Hallucinated Model Changes Could Slip Through
1. **Prompt injection in Kimi adapter** — A malicious note could manipulate the LLM to generate many invalid or misleading proposals. Mitigated by downstream validation, but could cause DoS-like noise.
2. **No semantic validation of `after` values** — The provider validator checks types but not schema compliance. A hallucinated `FieldEndpoint` with `endpoint_type: sap_table_field` but no `sap_table` would be created and only caught at Layer 3 validation after apply (or during dry-run).
3. **`before` field ignored** — The proposal can claim any before state; apply overwrites unconditionally. This means a hallucinated proposal that misrepresents the current state will still apply.
4. **No operation count limit** — A compromised AI could generate thousands of operations. The system would attempt them sequentially.

---

## 9. Documentation Audit

### README
**Accurate.** Version 0.4.0 mentioned. Command reference is up to date. Quickstart works.

### Getting Started Docs
- `first-15-minutes.md` — Accurate, copy-paste friendly.
- `docs/what-to-use-first.md` — Points users to the right example.

### Examples
- All 4 examples have working `modelops.config.yaml` and validate cleanly.

### Architecture Docs
- `SYSTEM_ARCHITECTURE.md` — **Stale.** Says `Version: 0.2-draft`. Mentions "Next.js UI" in MVP architecture, but product explicitly has no UI. Contains stale command `modelops approve-patch`.
- `DOMAIN_MODEL.md` — Accurate conceptual model.
- `AI_PATCH_WORKFLOW.md` — Needs verification for command names.
- `DATA_LINEAGE_AND_IMPACT_MODEL.md` — Accurate.

### Validation Docs
- `validation-methodology-warnings.md` — Explains why warnings exist and how to resolve them. Accurate.

### AI / Contributor Docs
- `AGENTS.md` — **2 factual errors:**
  1. Claims `__version__.py` = `"0.1.0"` (actual: `"0.4.0"`).
  2. Tells agents to edit `_SAP_CONTEXT_RULES` in `schemas/registry.py` (actual: `domain_packs/sap.py`).
- `agent-modeling-guide.md` — `Version: 0.1`. Needs update.
- `mcp-server-design.md` — Accurate about `NoProviderAdapter` stub.

### Stale Commands
| Document | Stale Reference | Correct Command |
|---|---|---|
| `docs/architecture/SYSTEM_ARCHITECTURE.md` | `modelops approve-patch PATCH-0021` | `modelops proposal accept PP-0021` |
| `docs/change-workflow.md` | `modelops apply --proposal <id>` | `modelops proposal apply <id> --apply` |
| `docs/architecture/MODEL_REPOSITORY_SPEC.md` | `modelops approve-patch PATCH-0021` | `modelops proposal accept PP-0021` |

### Incorrect Package Names / Versions
| Location | Issue |
|---|---|
| `src/modelops_core/api/app.py:22` | Hardcoded `version="0.1.0"` — should use `__version__` |
| `AGENTS.md` | Claims `__version__.py` = `"0.1.0"` |
| `docs/product/MVP_SCOPE.md` | `Version: 0.1` |
| `docs/architecture/SYSTEM_ARCHITECTURE.md` | `Version: 0.2-draft` |
| `docs/change-workflow.md` | `Version: 0.1` |

### Broken Assumptions
- `MVP_SCOPE.md` schema examples use old lowercase dot-notation IDs (`attr.customer.sales_area.customer_group`) instead of current kebab-case uppercase (`ATTR-CUST-SALES-CUSTOMER-GROUP`).
- `MVP_SCOPE.md` sections 11.1–11.8 describe required UI screens that do not exist.
- `docs/migration/MIGRATION_RISKS.md` claims "The original CLI is a placeholder" — no longer true.

### Missing Diagrams or Mental Models
- No architecture diagram in `SYSTEM_ARCHITECTURE.md` that shows the canonical file → validation → index → query flow.
- No mental model diagram for the proposal → approval → apply → audit flow.

---

## 10. Risk Register

| Risk | Severity | Evidence | Why It Matters | Suggested Fix |
|---|---|---|---|---|
| CLI monolith (`cli.py` 203 KB) | **High** | 5,343 lines, 60 commands, no modules | Any agent editing CLI risks breaking unrelated commands; impossible to review | Split into `commands/` package with one module per domain |
| `AGENTS.md` wrong pointers | **High** | Version says 0.1.0; SAP rules path wrong | Agents following docs make no-op or wrong edits | Fix version and SAP rules path; add CI check |
| Patch proposal validation under-tested | **High** | `test_patch_proposal_validation.py` = 38 lines / 4 tests | Critical safety gate before human review lacks coverage | Expand to 15–20 tests covering multi-op, broken refs, path traversal, SAP context |
| Legacy CR service auto-applies on approval | **Medium** | `patching/change_request_service.py` calls `apply_patch_proposal()` inside `approve_change_request()` | Agent importing wrong module collapses approval + apply | Deprecate/remove legacy module; add import guard test |
| Schema drift (registry vs domain.py) | **Medium** | `Attribute` missing `mapping`; `FieldEndpoint` missing `attribute`; dead files exist | Agents edit wrong files; validation cannot catch field mismatches | Align registry fields to models; delete dead files |
| API version hardcoded 0.1.0 | **Medium** | `src/modelops_core/api/app.py:22` | API docs/reporting show wrong version | Use `__version__` dynamically |
| Stale architecture docs reference non-existent UI | **Medium** | `SYSTEM_ARCHITECTURE.md` mentions Next.js UI; `MVP_SCOPE.md` lists UI screens | Misaligns team and agent expectations | Add disclaimer or remove UI references |
| Missing cardinality metadata in registry | **Medium** | `ReferenceField` has no `is_list` flag | Cannot validate list-field syntax (e.g., `related_issues`) | Add `is_list: bool` to `ReferenceField` |
| `--force` / `skip_risk_check` bypass at every layer | **Medium** | CLI `--force`, `--skip-risk-check`; service `skip_risk_check=True` | A compromised agent can override all safety gates | Require env var or config flag to enable bypass (not CLI arg) |
| `before` field ignored in apply | **Low** | `apply_service.py` overwrites unconditionally | Proposals can misrepresent current state and still apply | Validate `before` matches actual current state before write |
| Expired proposals are warnings only | **Low** | `patch_validator.py` emits `PATCH_PROPOSAL_EXPIRED` as WARNING | Old accepted proposals can be applied accidentally | Promote to ERROR or require explicit `--allow-expired` |
| Minimal conftest.py (2 fixtures) | **Low** | No factories for FieldEndpoint, Mapping, etc. | Agents write repetitive boilerplate; tests are verbose | Add fixture factories for common object types |

---

## 11. MVP Gap Map

| MVP Capability | Current State | Gap | Priority | Suggested Issue |
|---|---|---|---|---|
| Init model repository | ✅ Implemented | None | — | — |
| Load canonical model files | ✅ Implemented | None | — | — |
| Validate objects and references | ✅ Implemented | Cardinality validation missing; proposal op validation missing | P1 | Add registry cardinality + proposal op validation |
| Build generated index | ✅ Implemented | None | — | — |
| Detect dataset/model gaps | ✅ Implemented | None | — | — |
| Show impact for fields/attributes | ✅ Implemented | None | — | — |
| Create issues and patch proposals | ✅ Implemented | Proposal validator under-tested; no semantic op validation | P0 | Expand patch proposal validation tests |
| Apply changes only after review | ✅ Implemented | Legacy CR service auto-applies; `--force` bypass too easy | P1 | Deprecate legacy CR service; tighten bypass |
| First 15 minutes works | ✅ Works | Docs have stale commands | P2 | Fix stale commands in architecture docs |
| Stable CLI JSON contracts | ✅ Tested | CLI monolith makes maintenance hard | P1 | Split CLI into command modules |
| Agent-ready documentation | ⚠️ Partial | `AGENTS.md` has wrong pointers | P0 | Fix `AGENTS.md` inaccuracies |
| SAP domain pack | ✅ 4 tables | Missing KNA1, KNVK, ADRC, etc.; no composite keys | P2 | Expand SAP table coverage |
| Ownership and governance | ✅ Implemented | None significant | — | — |
| Evidence and decision tracking | ✅ Implemented | None significant | — | — |
| Audit trail | ✅ Implemented | None significant | — | — |

---

## 12. Issue Plan

### P0 — Critical

#### Issue 1: Fix AGENTS.md version and SAP rules path
- **Priority:** P0
- **Goal:** Remove factual errors that misdirect AI agents.
- **Scope:** Update `AGENTS.md` version reference from `"0.1.0"` to `"0.4.0"`. Update SAP rules pointer from `schemas/registry.py` to `domain_packs/sap.py`. Verify no other stale paths exist.
- **Out of scope:** Rewriting `AGENTS.md` entirely; adding new content.
- **Acceptance criteria:** `grep -n "0.1.0" AGENTS.md` returns no false matches for version. `grep -n "registry.py" AGENTS.md` in SAP context returns nothing.
- **Validation command:** `grep -n "_SAP_CONTEXT_RULES" AGENTS.md` should point to `domain_packs/sap.py`.
- **Suggested files:** `AGENTS.md`
- **Agent notes:** This is a 2-line change. Do not restructure the file. Just fix the inaccuracies.

#### Issue 2: Expand patch proposal validation tests from 4 to 15+
- **Priority:** P0
- **Goal:** Cover critical safety paths in the proposal validator before human review.
- **Scope:** Add tests to `tests/test_patch_proposal_validation.py` for: multi-op proposals, `object_id` format validation, non-existent `object_id` references, `target_path` format/path traversal attempts, `create_object` with unregistered type, `create_object` with missing required fields, expired proposal handling, extremely long strings/null bytes in IDs.
- **Out of scope:** Testing apply_service (already covered in `test_patch_apply.py`); testing provider adapter output.
- **Acceptance criteria:** File grows from 38 lines to 200+ lines with ≥15 test functions. All tests pass. Coverage of `patch_validator.py` reaches 95%+.
- **Validation command:** `pytest tests/test_patch_proposal_validation.py -v`
- **Suggested files:** `tests/test_patch_proposal_validation.py`, `src/modelops_core/patching/patch_validator.py`
- **Agent notes:** Use `temp_model_dir` fixture and construct proposal dicts manually. Do not refactor the validator unless a bug is found.

#### Issue 3: Deprecate or remove legacy patching/change_request_service.py
- **Priority:** P0
- **Goal:** Eliminate the dual CR service that auto-applies on approval.
- **Scope:** Determine if `patching/change_request_service.py` is imported anywhere in `src/` or `tests/`. If unused, delete it and update `patching/__init__.py`. If used, add deprecation warnings and redirect callers to `change_request/service.py`.
- **Out of scope:** Changing `change_request/service.py` behavior; modifying CLI.
- **Acceptance criteria:** No code path in `src/` or `tests/` imports `patching.change_request_service` without a deprecation warning. If deleted, all tests still pass.
- **Validation command:** `grep -r "from modelops_core.patching.change_request_service" src tests || echo "No imports found"`
- **Suggested files:** `src/modelops_core/patching/change_request_service.py`, `src/modelops_core/patching/__init__.py`
- **Agent notes:** Search carefully for imports. The CLI uses `change_request.service`, not `patching.change_request_service`, but scripts or notebooks may reference it.

#### Issue 4: Fix API hardcoded version
- **Priority:** P0
- **Goal:** API reports correct package version.
- **Scope:** Change `version="0.1.0"` in `src/modelops_core/api/app.py` to import and use `__version__` from `modelops_core`.
- **Out of scope:** Changing API routes or behavior.
- **Acceptance criteria:** API `/docs` or version endpoint shows `0.4.0`. No hardcoded version strings remain in `src/modelops_core/api/`.
- **Validation command:** `grep -r "0.1.0" src/modelops_core/api/`
- **Suggested files:** `src/modelops_core/api/app.py`
- **Agent notes:** One-line change. Import `from modelops_core import __version__` and use it.

### P1 — Important

#### Issue 5: Split CLI monolith into commands/ package
- **Priority:** P1
- **Goal:** Make CLI commands maintainable and safe for agents to edit.
- **Scope:** Create `src/modelops_core/commands/` with modules: `init.py`, `validate.py`, `index.py`, `health.py`, `impact.py`, `proposal.py`, `change_request.py`, `export.py`, `import_.py`, `query.py`, `diff.py`, `audit.py`, `serve.py`, `mcp.py`, `docs.py`, `guardrails.py`, `gap.py`, `trace.py`, `decisions.py`, `notifications.py`, `issue_draft.py`, `migrate.py`, `clean.py`, `doctor.py`, `analyze.py`, `scorecard.py`, `owners.py`, `git_bundle.py`, `publish.py`, `config_guard.py`, `usage_report.py`, `search.py`. Move each command function and its helpers into the appropriate module. Register sub-apps in a central `cli.py` that becomes a thin router.
- **Out of scope:** Changing command behavior, signatures, or JSON contracts. This is a pure move refactor.
- **Acceptance criteria:** All 1,220 tests pass. `test_cli_contracts.py` passes unchanged. `ruff check src tests` passes. No command is missing from `--help`.
- **Validation command:** `pytest tests/test_cli_contracts.py tests/test_cli.py -v`
- **Suggested files:** New `src/modelops_core/commands/` directory; `src/modelops_core/cli.py`
- **Agent notes:** This is a large refactor. Do it incrementally — move one command group at a time and run tests. Keep Typer app instances and decorators identical. Do not change function signatures.

#### Issue 6: Add registry cardinality metadata (is_list flag)
- **Priority:** P1
- **Goal:** Enable validation of list-field syntax in frontmatter.
- **Scope:** Add `is_list: bool = False` to `ReferenceField` dataclass. Update all `_REGISTRY` entries to set `is_list=True` for list-valued refs (`related_issues`, `affected_objects`, etc.). Update reference validation in `validation/pipeline.py` to check that list-valued fields are actually lists and single-valued fields are strings.
- **Out of scope:** Changing Pydantic models; this is registry + validation only.
- **Acceptance criteria:** A canonical file with `related_issues: ISSUE-001` (string instead of list) produces an ERROR. A file with `domain: [DOMAIN-TEST]` (list instead of string) produces an ERROR. All existing tests pass.
- **Validation command:** `pytest tests/test_reference_validation.py -v`
- **Suggested files:** `src/modelops_core/schemas/registry.py`, `src/modelops_core/validation/pipeline.py`, `tests/test_reference_validation.py`
- **Agent notes:** Inspect `_REGISTRY` construction carefully. Some fields are clearly lists (e.g., `affected_objects`), others are ambiguous. When in doubt, check the Pydantic model in `domain.py`.

#### Issue 7: Add fixture factories to conftest.py
- **Priority:** P1
- **Goal:** Reduce test boilerplate and agent mistakes.
- **Scope:** Add pytest fixtures that generate canonical object dicts or frontmatter strings: `domain_factory`, `attribute_factory`, `field_endpoint_factory`, `mapping_factory`, `patch_proposal_factory`, `entity_context_factory`. Each factory should accept overrides via kwargs and return a valid object dict.
- **Out of scope:** Refactoring existing tests to use factories (can be follow-up).
- **Acceptance criteria:** At least 5 new factories exist in `conftest.py`. Each returns a dict that passes `validate_objects()` when added to a valid object set.
- **Validation command:** `pytest tests/test_schema_validation.py tests/test_reference_validation.py -v`
- **Suggested files:** `tests/conftest.py`
- **Agent notes:** Use the existing `temp_model_dir` pattern as inspiration. Return plain dicts, not Pydantic models, to match how the parser works.

#### Issue 8: Add semantic validation for PatchProposal operations
- **Priority:** P1
- **Goal:** Catch bad proposals before they reach human review or apply.
- **Scope:** In `patch_validator.py`, validate that each `update_object` operation's `object_id` exists in the repository. Validate that `create_object` operations specify a registered `type`. Validate that `target_path` does not contain path traversal (`../`, absolute paths). Validate that `after` values are non-empty for `update_object`.
- **Out of scope:** Full schema validation of `after` (that is apply_service's job); SAP context validation at proposal time.
- **Acceptance criteria:** Proposals with non-existent `object_id`, unregistered type, or path traversal fail validation with clear error codes. Tests added to `test_patch_proposal_validation.py`.
- **Validation command:** `pytest tests/test_patch_proposal_validation.py -v`
- **Suggested files:** `src/modelops_core/patching/patch_validator.py`, `tests/test_patch_proposal_validation.py`
- **Agent notes:** The validator currently receives only the proposal dict. To check object existence, you may need to pass the scanned object list or index. Check how `apply_service` resolves objects for reference.

#### Issue 9: Add rollback test for multi-op patch apply
- **Priority:** P1
- **Goal:** Ensure atomicity when partial failure occurs.
- **Scope:** In `test_patch_apply.py`, add a test where a 2-operation proposal succeeds on op 1 but op 2 fails (e.g., due to a broken reference or SAP context violation). Assert that op 1's file change is rolled back and the original content is restored.
- **Out of scope:** Changing rollback logic (only test it).
- **Acceptance criteria:** New test passes. Original file content is unchanged after failed apply.
- **Validation command:** `pytest tests/test_patch_apply.py -v`
- **Suggested files:** `tests/test_patch_apply.py`, `src/modelops_core/patching/apply_service.py`
- **Agent notes:** Use `sample_repo` fixture. Create a proposal that updates two objects. Make the second operation reference a non-existent object so apply_service's post-write validation fails and triggers rollback.

#### Issue 10: Fix stale commands and versions in architecture docs
- **Priority:** P1
- **Goal:** Remove documentation that misleads users and agents.
- **Scope:** Fix `modelops approve-patch` → `modelops proposal accept` in `SYSTEM_ARCHITECTURE.md` and `MODEL_REPOSITORY_SPEC.md`. Fix `modelops apply --proposal` → `modelops proposal apply --apply` in `change-workflow.md`. Update version headers in `MVP_SCOPE.md`, `SYSTEM_ARCHITECTURE.md`, `change-workflow.md`, `agent-modeling-guide.md`, `modeling-methodology.md` to `0.4.0` or remove version. Remove "Next.js UI" references from `SYSTEM_ARCHITECTURE.md` or add "out of scope" disclaimer. Fix ID examples in `MVP_SCOPE.md` to use kebab-case uppercase.
- **Out of scope:** Rewriting doc content; only fixing inaccuracies.
- **Acceptance criteria:** `grep -r "approve-patch" docs/` returns nothing. `grep -r "0.1\." docs/product/MVP_SCOPE.md` returns nothing for version. `grep -r "attr\.customer\." docs/product/MVP_SCOPE.md` returns nothing.
- **Validation command:** `grep -rn "approve-patch" docs/; grep -rn "apply --proposal" docs/`
- **Suggested files:** `docs/architecture/SYSTEM_ARCHITECTURE.md`, `docs/architecture/MODEL_REPOSITORY_SPEC.md`, `docs/change-workflow.md`, `docs/product/MVP_SCOPE.md`, `docs/agent-modeling-guide.md`, `docs/modeling-methodology.md`
- **Agent notes:** Use `StrReplaceFile` for precise replacements. Do not change meaning — only fix stale commands, versions, and ID formats.

#### Issue 11: Delete dead schema files (mapping.py, validation_rule.py)
- **Priority:** P1
- **Goal:** Remove files that confuse agents and inflate coverage noise.
- **Scope:** Delete `src/modelops_core/schemas/mapping.py` and `src/modelops_core/schemas/validation_rule.py`. Verify zero imports anywhere in `src/` or `tests/`.
- **Out of scope:** Any other file deletions.
- **Acceptance criteria:** Files deleted. `grep -r "from modelops_core.schemas.mapping" src tests` returns nothing. All tests pass.
- **Validation command:** `pytest -q`
- **Suggested files:** `src/modelops_core/schemas/mapping.py`, `src/modelops_core/schemas/validation_rule.py`
- **Agent notes:** Double-check imports with grep before deleting. These files show 0% coverage and are confirmed dead.

#### Issue 12: Add `before` state validation to patch apply
- **Priority:** P1
- **Goal:** Prevent proposals that misrepresent current state from applying unconditionally.
- **Scope:** In `apply_service.py`, before executing an `update_object` operation, compare the operation's `before` field (if present) to the actual current file content or parsed object. If they differ, abort with an error indicating the object has changed since the proposal was created.
- **Out of scope:** Changing the proposal format; this is an optional guard.
- **Acceptance criteria:** A proposal with a mismatched `before` value is rejected. A proposal with matching or absent `before` value applies normally. Tests added.
- **Validation command:** `pytest tests/test_patch_apply.py -v`
- **Suggested files:** `src/modelops_core/patching/apply_service.py`, `tests/test_patch_apply.py`
- **Agent notes:** `before` is a field in the operation dict. If it is `None` or missing, skip the check (backward compatibility).

### P2 — Cleanup and Hardening

#### Issue 13: Expand TESTING_STRATEGY.md from 27-line stub
- **Priority:** P2
- **Goal:** Give agents and contributors clear testing guidance.
- **Scope:** Expand `docs/developer/TESTING_STRATEGY.md` to include: coverage target (70% floor, 90% for critical paths), mocking policy (mock external APIs only), contract test requirements (add to `test_cli_contracts.py` for new CLI JSON outputs), fixture usage guidelines, and instructions for adding tests when modifying validation rules.
- **Out of scope:** Changing actual tests.
- **Acceptance criteria:** Document is ≥100 lines and covers the topics above. No stale commands or versions.
- **Validation command:** `wc -l docs/developer/TESTING_STRATEGY.md`
- **Suggested files:** `docs/developer/TESTING_STRATEGY.md`
- **Agent notes:** Use existing test files as examples. Keep it actionable.

#### Issue 14: Add ValueList entry code-uniqueness validation
- **Priority:** P2
- **Goal:** Prevent duplicate codes within a value list.
- **Scope:** In `validation/pipeline.py`, when validating a `ValueList` object, check that `entries` (if present) has unique `code` values. Emit `ERROR` if duplicates exist.
- **Out of scope:** Changing `ValueList` model.
- **Acceptance criteria:** A `ValueList` with duplicate `code` values fails validation. Tests added to `test_schema_validation.py` or `test_reference_validation.py`.
- **Validation command:** `pytest tests/test_schema_validation.py -v -k value_list`
- **Suggested files:** `src/modelops_core/validation/pipeline.py`, `tests/test_schema_validation.py`
- **Agent notes:** `entries` is likely a list of dicts. Extract `code` from each and use a set to detect duplicates.

#### Issue 15: Add co-occurrence rule for sap_table + sap_field
- **Priority:** P2
- **Goal:** Enforce that SAP table field endpoints specify both table and field.
- **Scope:** In `domain_packs/sap.py` or `validation/pipeline.py`, add a rule: if `endpoint_type == "sap_table_field"`, then both `sap_table` and `sap_field` must be present and non-empty.
- **Out of scope:** Adding new SAP tables.
- **Acceptance criteria:** A `FieldEndpoint` with `endpoint_type: sap_table_field` but missing `sap_field` fails validation with a clear error code. Tests pass.
- **Validation command:** `pytest tests/test_sap_context_validation.py -v`
- **Suggested files:** `src/modelops_core/domain_packs/sap.py` or `src/modelops_core/validation/pipeline.py`, `tests/test_sap_context_validation.py`
- **Agent notes:** Check if this should be a generic rule (in pipeline.py) or SAP-specific (in sap.py). Since `sap_table` and `sap_field` are SAP-specific fields, `sap.py` is appropriate.

#### Issue 16: Add minimum object-count rules for key types
- **Priority:** P2
- **Goal:** Prevent orphan entities and incomplete mappings.
- **Scope:** In `validation/pipeline.py`, add optional (WARNING-level) checks: `BusinessEntity` with zero `Attribute`s or `FieldEndpoint`s; `Mapping` with only one side populated; `Attribute` with zero `FieldEndpoint`s. These should be warnings, not errors, to avoid breaking existing models.
- **Out of scope:** Changing object types or registry.
- **Acceptance criteria:** Warnings emitted for orphan entities. Tests added. Existing examples still validate (warnings are acceptable).
- **Validation command:** `pytest tests/test_reference_validation.py tests/test_schema_validation.py -v`
- **Suggested files:** `src/modelops_core/validation/pipeline.py`, `tests/test_reference_validation.py`
- **Agent notes:** These are methodology warnings, similar to existing enrichment warnings. Use WARNING severity.

### P3 — Polish

#### Issue 17: Group CLI commands with Typer command categories
- **Priority:** P3
- **Goal:** Improve help output discoverability.
- **Scope:** After Issue 5 (CLI split), add `rich_help_panel` to Typer command decorators to group commands into panels: "Repository", "Validation", "Index", "Analysis", "Proposal", "Export/Import", "Admin". This makes `modelops --help` show categorized groups instead of a flat list.
- **Out of scope:** Issue 5 must be completed first.
- **Acceptance criteria:** `modelops --help` shows categorized command groups. All tests pass.
- **Validation command:** `.venv/bin/modelops --help`
- **Suggested files:** `src/modelops_core/cli.py` or `src/modelops_core/commands/*.py`
- **Agent notes:** Typer supports `rich_help_panel="Category"` in `@app.command()`.

#### Issue 18: Add architecture diagram for canonical → validation → index → query flow
- **Priority:** P3
- **Goal:** Provide a visual mental model for agents and contributors.
- **Scope:** Add a Mermaid diagram to `docs/architecture/SYSTEM_ARCHITECTURE.md` showing: `model/` files → `repository/parser` → `validation/pipeline` → `index/sqlite_builder` → `generated/modelops.db` → `query`/`search`/`impact`/`trace`.
- **Out of scope:** Rewriting architecture text.
- **Acceptance criteria:** Diagram renders correctly in GitHub Markdown preview.
- **Validation command:** View file in GitHub preview.
- **Suggested files:** `docs/architecture/SYSTEM_ARCHITECTURE.md`
- **Agent notes:** Use Mermaid flowchart syntax. Keep it simple.

---

*Audit produced by automated inspection plus manual evidence review. All commands run on 2026-05-31 against commit `HEAD` on branch `main`.*
