# Martenweave User Scenario Catalog

Version: 0.4.1  
Status: Living document  
Owner: Product / Engineering  

This catalog defines the end-to-end user scenarios Martenweave supports across the Core CLI, the local API, and the Workbench UI. It is the authoritative reference for prioritizing pilot work, naming mock-only behavior, and tracking coverage.

> **Scope boundary.** Scenario templates that *initialize* a repository belong to [#434](https://github.com/metalhatscats/martenweave-core/issues/434). This document defines *user journeys* on top of an initialized repository.

---

## Status legend

| Status | Meaning |
|---|---|
| `complete` | Works end-to-end through CLI and backend services; UI may still be static/mock but the canonical behavior is real. |
| `partial` | Core logic and CLI are present; API surface or UI integration is incomplete, or one step of the workflow is still pending in an open PR/issue. |
| `mocked` | The UI screen exists and demonstrates the workflow, but the data and actions are static demo data or local React state only. |
| `missing` | No implementation exists in `main` yet; tracked by an open issue/PR. |

---

## Scenario catalog

### S01 — Open an existing model repository and inspect health

| Field | Value |
|---|---|
| **Persona** | SAP migration data analyst |
| **Trigger** | Opening the project workspace or onboarding a new team member. |
| **Required inputs** | Path to a Martenweave repository with `model/` and `modelops.config.yaml`. |
| **UI entry point** | `home` (Workspace) or `settings` (Workspace settings). |
| **Core / API operations** | `modelops doctor --repo <path>`, `modelops health --repo <path>`, `modelops validate --repo <path>`, `GET /health`, `GET /validate`. |
| **Generated artifacts** | Repository health report, deterministic validation summary, index freshness status. |
| **Safety boundary** | Read-only. No canonical files are changed. |
| **Success metric** | User sees object count, validation status, and index freshness within 3 seconds of loading the workspace. |
| **Status** | **partial** — CLI and API are live; Workbench home currently renders static demo data. |

### S02 — Start a migration assessment from an Excel mapping workbook

| Field | Value |
|---|---|
| **Persona** | Migration lead / pilot owner |
| **Trigger** | A new SAP migration pilot starts with an existing source-to-target mapping workbook. |
| **Required inputs** | XLSX mapping workbook, repository name, output directory, optional dataset sample. |
| **UI entry point** | `import` overlay → "Excel mapping workbook" source. |
| **Core / API operations** | `martenweave bootstrap-assessment --mapping <workbook.xlsx> --name <pilot> --out-repo <path>`; `martenweave assessment run --repo <path> --out <dir>`. |
| **Generated artifacts** | Initialized repository, a draft `PatchProposal`, and bootstrap report with assumptions and warnings. Inferred objects remain proposal operations until approved. |
| **Safety boundary** | Inferred objects become proposals; canonical files are not mutated until a proposal is explicitly applied. |
| **Success metric** | A valid repository is produced from a synthetic SAP workbook and at least one proposal is ready for review. |
| **Status** | **partial** — CLI workbook-first bootstrap is available; live UI import remains in progress. |

### S03 — Add a dataset extract and detect model/data gaps

| Field | Value |
|---|---|
| **Persona** | Data analyst |
| **Trigger** | A new CSV/XLSX dataset extract arrives and must be checked against the model. |
| **Required inputs** | Dataset file path; existing canonical model and index. |
| **UI entry point** | `import` overlay → "Dataset extracts" source; results surface in `gaps`. |
| **Core / API operations** | `modelops profile-dataset <file> --repo <path>`, `modelops gaps --repo <path>`, `modelops run dataset-readiness --repo <path>`, `POST /gaps`, `POST /dataset-readiness`. |
| **Generated artifacts** | Dataset profile JSON, gap report, readiness report with missing/extra columns and model-side gaps. |
| **Safety boundary** | Dataset files are inputs/evidence only; they never become canonical truth. |
| **Success metric** | Missing required columns, extra dataset columns, and unmapped model attributes are identified with stable object IDs. |
| **Status** | **partial** — CLI and API are complete; Workbench Gaps screen uses static data. |

### S04 — Search for a model object and inspect evidence

| Field | Value |
|---|---|
| **Persona** | Migration data analyst |
| **Trigger** | Need to locate a business attribute, SAP field, or mapping by name or stable ID. |
| **Required inputs** | Search term (e.g., `Customer Group`, `KNVV`, `KDGRP`, `ATTR-CUST-SALES-CUSTOMER-GROUP`). |
| **UI entry point** | `models` (global search) → `object` (object detail). |
| **Core / API operations** | `modelops search <term> --repo <path>`, `modelops query --repo <path>`, `modelops object-card <id> --repo <path>`, `GET /objects`, `GET /objects/{id}`. |
| **Generated artifacts** | Search result list, object detail card with identity, relationships, validation, ownership, and evidence. |
| **Safety boundary** | Read-only. |
| **Success metric** | Searching for an SAP table-field such as `KNVV-KDGRP` returns the matching attribute and shows source/target representations. |
| **Status** | **partial** — CLI and API are live; Workbench Models/Object screens currently use static demo data. |

### S05 — Trace lineage and analyze downstream impact before a change

| Field | Value |
|---|---|
| **Persona** | Data steward / SAP functional consultant |
| **Trigger** | A model object, mapping, or rule is about to change and the team needs to know what is affected. |
| **Required inputs** | Stable object ID; optional traversal direction and depth. |
| **UI entry point** | `lineage` or `object` → "Impact" tab. |
| **Core / API operations** | `modelops trace <id> --repo <path>`, `modelops impact <id> --repo <path>`, `GET /trace/{id}`, `GET /impact/{id}`. |
| **Generated artifacts** | Trace report (upstream/downstream nodes and edges), impact report (affected objects by category). |
| **Safety boundary** | Read-only deterministic traversal from the generated index. |
| **Success metric** | `Customer Group` / `FEP-S4-KNVV-KDGRP` can be traced through source → canonical → target with bounded depth and every edge exposes its relationship type. |
| **Status** | **partial** — CLI and API are complete; Workbench Lineage screen is a static React Flow graph. |

### S06 — Review and disposition an assessment finding

| Field | Value |
|---|---|
| **Persona** | Data steward / reviewer |
| **Trigger** | Assessment findings need human triage before they become issues or proposals. |
| **Required inputs** | Finding ID; reviewer disposition (`confirmed`, `false_positive`, `accepted_risk`, `deferred`, `resolved`). |
| **UI entry point** | `gaps` → expanded finding card → disposition controls. |
| **Core / API operations** | `martenweave assessment review` records a human disposition against a stable finding ID; `martenweave pilot-outcome` summarizes reviewed findings without inventing unavailable baselines. |
| **Generated artifacts** | Updated finding record with disposition, reviewer note, and timestamp; disposition history. |
| **Safety boundary** | Review metadata only; no canonical model mutation. |
| **Success metric** | A reviewer can inspect evidence, set a disposition, refresh the screen, and see the persisted state with source evidence links intact. |
| **Status** | **partial** — backend review and pilot-outcome commands are available; UI disposition controls are not wired. |

### S07 — Promote evidence or a finding into an Issue or PatchProposal

| Field | Value |
|---|---|
| **Persona** | Data steward / migration analyst |
| **Trigger** | A confirmed gap or piece of project evidence needs to become actionable. |
| **Required inputs** | Gap/finding ID or evidence file; chosen target (`issue` or `proposal`). |
| **UI entry point** | `gaps` detail panel → "Create proposal" / "Create issue"; `import` overlay for evidence ingestion. |
| **Core / API operations** | `modelops issue-draft --repo <path>`, `modelops infer-model --from-profile <path> --repo <path>`, `modelops propose-patch --from <note> --repo <path>`, `POST /dataset-readiness?promote_to_proposal=true`. |
| **Generated artifacts** | `Issue` or `PatchProposal` canonical file with evidence source metadata. |
| **Safety boundary** | Promotion creates reviewable artifacts; it never applies changes to canonical model files directly. |
| **Success metric** | Generated artifact references the source finding/evidence and passes deterministic validation before review. |
| **Status** | **partial** — CLI and API can generate proposals and issue drafts; live UI promotion is mocked. |

### S08 — Review, approve, and explicitly apply a PatchProposal

| Field | Value |
|---|---|
| **Persona** | Data owner / data steward |
| **Trigger** | A PatchProposal has been created and is ready for governance review. |
| **Required inputs** | Proposal ID; reviewer decision; approved ChangeRequest for high-risk proposals. |
| **UI entry point** | `proposals` → `proposal` review screen. |
| **Core / API operations** | `modelops proposal show <id>`, `modelops proposal validate <id>`, `modelops proposal impact <id>`, `modelops proposal diff <id>`, `modelops proposal accept <id>`, `modelops change-request create --proposal <id>`, `modelops proposal apply <id>`, `GET /proposals/{id}`, `POST /proposals/{id}/validate`, `POST /proposals/{id}/dry-run`, `POST /proposals/{id}/apply`. |
| **Generated artifacts** | Reviewed proposal status, ChangeRequest, applied file changes, audit event. |
| **Safety boundary** | Apply is a separate explicit step; high-risk proposals require an approved ChangeRequest; rejected proposals never modify files. |
| **Success metric** | A proposal is applied only after acceptance (and an approved ChangeRequest when required), and the audit log records the apply event. |
| **Status** | **partial** — CLI and API are complete; Workbench proposal approval is local React state only and does not call the API. |

### S09 — Generate and download a business review pack

| Field | Value |
|---|---|
| **Persona** | Project manager / migration lead |
| **Trigger** | Stakeholders need a reviewable artifact that separates facts from narrative. |
| **Required inputs** | Repository path; optional scope (domain/entity/object). |
| **UI entry point** | `reports` → "Review pack" or "Evidence summary" export. |
| **Core / API operations** | `modelops review-pack create --repo <path>`, `modelops export-model --repo <path> --format xlsx`, `modelops assessment run --repo <path> --out <dir>`, `POST /export`. |
| **Generated artifacts** | Business review pack (XLSX/Markdown), model index export, executive summary. |
| **Safety boundary** | Read-only export; canonical files remain unchanged. |
| **Success metric** | Pack contains model summary, open gaps, impact evidence, and proposal status with stable object IDs. |
| **Status** | **partial** — CLI review-pack exists; API export exists; Workbench Reports screen is mocked. |

### S10 — Import a reviewed Excel workbook and preview proposed changes

| Field | Value |
|---|---|
| **Persona** | Business reviewer |
| **Trigger** | A business review workbook has been edited and returned. |
| **Required inputs** | Reviewed XLSX with stable object IDs; repository path. |
| **UI entry point** | `import` overlay → "Excel mapping files" source → review preview. |
| **Core / API operations** | `modelops import-model-sheet --from <xlsx> --repo <path>`, `modelops proposal validate <id> --repo <path>`, `modelops proposal diff <id> --repo <path>`. |
| **Generated artifacts** | `PatchProposal` from edited rows; diff preview. |
| **Safety boundary** | Edited workbook becomes a proposal; canonical files are not changed until the proposal is approved and applied. |
| **Success metric** | Imported edits create a schema-valid proposal with a clear before/after diff and no silent model mutation. |
| **Status** | **partial** — CLI import-model-sheet and proposal diff/validate are complete; live UI preview is not wired. |

### S11 — Compare model versions and inspect change history

| Field | Value |
|---|---|
| **Persona** | Data governance specialist / release manager |
| **Trigger** | Need to understand what changed, when, and who approved it. |
| **Required inputs** | Two repository paths or a repository with audit events. |
| **UI entry point** | `changelog` screen. |
| **Core / API operations** | `modelops diff --from <repo> --to <repo>`, `modelops audit-log --repo <path>`, `modelops migrate --repo <path>`. |
| **Generated artifacts** | Diff report, audit log query results, changelog. |
| **Safety boundary** | Read-only; `migrate` creates proposals when schema changes are needed. |
| **Success metric** | User can list changed objects, trace each change to an audit event, and identify schema-version drift. |
| **Status** | **implemented** — CLI diff, audit-log, and migrate are available; the Workbench Changelog keeps product release notes separate from append-only local repository activity. |

### S12 — Produce a sanitized pilot outcome/demo bundle

| Field | Value |
|---|---|
| **Persona** | Product / demo lead |
| **Trigger** | Pilot is complete and a public demo bundle must be published. |
| **Required inputs** | Assessment output folder; optional review dispositions. |
| **UI entry point** | `reports` → "Export project output" with sanitization option. |
| **Core / API operations** | `martenweave config-guard --repo <path> --json`, `martenweave assessment sanitize`, `martenweave pilot-outcome`, and `martenweave demo-bundle build`. |
| **Generated artifacts** | Sanitized bundle, `sanitization-manifest.json`, pilot outcome report, bundle manifest with checksums. |
| **Safety boundary** | Absolute paths, raw datasets, secrets, and identifying metadata are excluded or redacted; source folder is never modified. |
| **Success metric** | Bundle passes config-guard checks, contains no raw source data or local paths, and two runs from the same commit produce byte-stable text outputs. |
| **Status** | **partial** — the local CLI workflow is implemented and verified; the Workbench Reports route does not yet expose it. |

---

## Coverage matrix

| # | Scenario | Core command(s) | API endpoint(s) | UI route(s) | Tests | Status | Open issue(s) |
|---|---|---|---|---|---|---|---|
| S01 | Open repository and inspect health | `modelops doctor`, `modelops health`, `modelops validate` | `GET /health`, `GET /validate` | `home`, `settings` | `test_cli.py`, `test_health_report_coverage.py`, `test_api.py` | partial | [#492](https://github.com/metalhatscats/martenweave-core/issues/492) |
| S02 | Start assessment from Excel workbook | `modelops assessment run` | `POST /export` (for reports) | `import` | `test_assessment_package.py`, `test_readiness_command.py` | partial | [#489](https://github.com/metalhatscats/martenweave-core/issues/489), [#498](https://github.com/metalhatscats/martenweave-core/issues/498) |
| S03 | Add dataset and detect gaps | `modelops profile-dataset`, `modelops gaps`, `modelops run dataset-readiness` | `POST /gaps`, `POST /dataset-readiness` | `import`, `gaps` | `test_gaps.py`, `test_run_dataset_readiness.py`, `test_e2e_dataset_workflow.py` | partial | [#499](https://github.com/metalhatscats/martenweave-core/issues/499) |
| S04 | Search object and inspect evidence | `modelops search`, `modelops query`, `modelops object-card` | `GET /objects`, `GET /objects/{id}` | `models`, `object` | `test_search_documents.py`, `test_query_service.py`, `test_object_card_command.py`, `test_api.py` | partial | [#492](https://github.com/metalhatscats/martenweave-core/issues/492) |
| S05 | Trace lineage and impact | `modelops trace`, `modelops impact` | `GET /trace/{id}`, `GET /impact/{id}` | `lineage`, `object` → Impact | `test_trace.py`, `test_impact_service.py`, `test_impact_report.py`, `test_system_lineage.py`, `test_api.py` | partial | [#500](https://github.com/metalhatscats/martenweave-core/issues/500) |
| S06 | Review and disposition finding | `assessment review`, `pilot-outcome` | planned | `gaps` | `test_assessment_review.py`, `test_pilot_outcome.py` | partial | [#499](https://github.com/metalhatscats/martenweave-core/issues/499) |
| S07 | Promote evidence to Issue/Proposal | `modelops issue-draft`, `modelops infer-model`, `modelops propose-patch` | `POST /dataset-readiness?promote_to_proposal=true` | `import`, `gaps` | `test_issue_draft.py`, `test_ai_patch_proposal_service.py`, `test_e2e_proposal_lifecycle.py`, `test_import_model_sheet.py` | partial | [#430](https://github.com/metalhatscats/martenweave-core/issues/430), [#499](https://github.com/metalhatscats/martenweave-core/issues/499) |
| S08 | Review, approve, apply Proposal | `modelops proposal *`, `modelops change-request *` | `GET /proposals/{id}`, `POST /proposals/{id}/validate`, `POST /proposals/{id}/dry-run`, `POST /proposals/{id}/apply` | `proposals`, `proposal` | `test_e2e_proposal_full_lifecycle.py`, `test_patch_apply.py`, `test_patch_proposal_validation.py`, `test_change_request_service.py`, `test_approval_gates.py`, `test_proposal_cli.py`, `test_api.py` | partial | [#492](https://github.com/metalhatscats/martenweave-core/issues/492) |
| S09 | Generate business review pack | `modelops review-pack create`, `modelops export-model` | `POST /export` | `reports` | `test_review_pack.py`, `test_export_model.py` | partial | — |
| S10 | Import reviewed Excel and preview changes | `modelops import-model-sheet`, `modelops proposal validate`, `modelops proposal diff` | planned | `import` | `test_import_model_sheet.py`, `test_patch_proposal_validation.py` | partial | [#427](https://github.com/metalhatscats/martenweave-core/issues/427) |
| S11 | Compare versions and change history | `modelops diff`, `modelops audit-log`, `modelops migrate` | planned | `changelog` | `test_diff.py`, `test_audit_log.py`, `test_schema_versioning.py` | partial | — |
| S12 | Sanitized pilot outcome/demo bundle | `martenweave config-guard`, `assessment sanitize`, `pilot-outcome`, `demo-bundle build` | planned | `reports` | `test_demo_bundle.py`, `test_pilot_outcome.py` | partial | [#502](https://github.com/metalhatscats/martenweave-core/issues/502) |

### Matrix status summary

- `complete`: 0 scenarios (no UI route is fully live end-to-end yet).
- `partial`: 11 scenarios (CLI + API present; UI is static or one step is pending in an open issue).
- `mocked`: 0 scenarios at the scenario level; individual UI screens use static data.
- `missing`: 0 scenarios.

### Mock-only UI behavior

The following Workbench screens render static demo data. They demonstrate the intended UX but do not yet call the local API:

- `home` (Workspace dashboard)
- `models` (global search)
- `object` (object detail)
- `lineage` (React Flow graph)
- `gaps` (gap triage)
- `proposals` / `proposal` (proposal list and review)
- `reports` (reports and exports)
- `changelog` (release notes)
- `settings` (local toggles only)

The `import` overlay simulates parsing progress and ends with static summary numbers.

---

## First five pilot-ready scenarios

For the first pilot-ready release, the following five scenarios must be end-to-end through the CLI and local API, with the Workbench showing at least read-only live data:

1. **S01 — Open an existing model repository and inspect health.** Foundation for every other workflow.
2. **S04 — Search for a model object and inspect evidence.** Proves the model is queryable and traceable.
3. **S05 — Trace lineage and analyze downstream impact.** Core differentiator for migration impact analysis.
4. **S08 — Review, approve, and explicitly apply a PatchProposal.** Proves the AI-proposes/humans-approve safety model.
5. **S03 — Add a dataset extract and detect model/data gaps.** Closes the dataset-to-model loop.

These five cover repository load → search → trace → governance → dataset alignment, which is the minimum credible pilot story for a SAP migration team.

---

## UI screen-to-scenario mapping

| UI route | Scenario(s) | Notes |
|---|---|---|
| `home` | S01 | Static demo; should load real workspace health and recent activity. |
| `models` | S04 | Static demo; should query `GET /objects`. |
| `object` | S04, S05 | Static demo; should load `GET /objects/{id}` and impact context. |
| `lineage` | S05 | Static React Flow graph; should load `GET /trace/{id}`. |
| `gaps` | S03, S06, S07 | Static demo; should load live findings and support disposition. |
| `proposals` / `proposal` | S07, S08 | Static demo; proposal approval is local state only. |
| `reports` | S09, S12 | Static demo; exports generate client-side placeholders. |
| `changelog` | S11 | Product release notes plus append-only local repository activity when connected to the local API. |
| `settings` | S01 | Local-only toggles; repository paths are hard-coded demo values. |

---

## Design principles preserved across scenarios

1. **Canonical model files remain the source of truth.** Datasets, workbooks, and AI outputs are inputs or proposals, never canonical truth.
2. **Deterministic validators verify results.** Validation, trace, impact, and gap detection run without provider keys or LLM calls.
3. **AI and imports create proposals, never silently mutate model truth.** Every model mutation flows through a `PatchProposal` or `ChangeRequest`.
4. **Humans approve changes.** Apply requires explicit acceptance; high-risk proposals require an approved `ChangeRequest`.
5. **No hosted SaaS platform, generic chatbot, workflow engine, direct SAP write-back, or unnecessary infrastructure.** All scenarios run locally.

---

## Validation

```bash
.venv/bin/python scripts/validate_doc_commands.py
.venv/bin/python -m pytest tests/test_doc_command_freshness.py
.venv/bin/python -m ruff check .
```
