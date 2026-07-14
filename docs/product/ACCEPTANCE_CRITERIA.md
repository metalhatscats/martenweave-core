# ModelOps for MDM - Acceptance Criteria

Status: Canonical MVP acceptance gate  
Scope: P0 implementation criteria for the local-first MVP  
Parent domain: Business Partner  
First slice: Customer role-dependent model  
First context: Customer Sales Area  
Canonical demo attribute: Customer Group / `KNVV-KDGRP`

## Purpose

This document is the implementation readiness checklist for coding agents.

Detailed use-case flows remain in `USE_CASES.md`. This file defines the minimum observable behavior required before the MVP can be considered complete.

## Global MVP Acceptance Rules

The MVP is accepted only if:

- canonical model objects are stored as local files;
- generated indexes are rebuildable and not treated as source of truth;
- schemas validate canonical files before indexing or AI interpretation;
- Business Partner is the parent domain and Customer is the first role-dependent slice;
- Customer Sales Area is modeled as a context, not collapsed into a generic customer field;
- `KNVV-KDGRP` is represented as a FieldEndpoint linked to the Customer Group Attribute;
- AI never writes approved canonical files directly;
- AI creates a PatchProposal first;
- validators check proposed changes before approval;
- a human approve/reject action is required before canonical writes;
- approved changes create or update a ChangeRequest and show a diff.

## P0 Acceptance Matrix

| Use case | Acceptance criteria |
|---|---|
| UC-001 Create a new model repository | Repository creation produces required folders, config, starter templates, initial validation result, and generated index without errors. |
| UC-002 Open an existing model repository | Opening a repository shows object counts, schema version, validation state, and index freshness. |
| UC-003 Build or rebuild generated index | Rebuild reads canonical files and produces a queryable SQLite index plus generated search/relationship artifacts. |
| UC-010 Browse Attribute Catalog | User can search/filter attributes and identify owner, validation, mapping, issue, SAP endpoint, and lifecycle coverage. |
| UC-011 View Attribute Detail | User can inspect Customer Group business meaning, Customer Sales Area context, source endpoint, target endpoint, mappings, validations, owner, issues, decisions, and impact links. |
| UC-020 View FieldEndpoint Detail | User can open `KNVV-KDGRP` and see SAP table, field, system, environment, entity context, linked Attribute, and related mappings/validations. |
| UC-021 Validate SAP context rules | Validator raises an error if a `KNVV` endpoint is not linked to Customer Sales Area context or if a `KNB1` endpoint is not linked to Customer Company Code context. |
| UC-030 View Mapping Detail | User can inspect source endpoint, target endpoint, transformation/defaulting logic, related Attribute, and status. |
| UC-031 Check mapping coverage | System reports modeled attributes without mappings and dataset columns without resolved Attribute/FieldEndpoint relationships. |
| UC-032 View ValueMapping Detail | User can inspect source values, target values, conditions such as `CH01` / `A17`, target value-list coverage, and unresolved entries. |
| UC-040 Register and profile dataset | User can register a CSV/XLSX sample dataset, detect columns, calculate row/column counts, and store dataset metadata/profile. |
| UC-041 Detect dataset-model gaps | System reports missing expected columns, extra columns, unmatched columns, missing mappings, missing owners, and missing validations. |
| UC-042 Create issue from detected gap | User can create or generate an issue draft linked to affected Attribute, FieldEndpoint, Dataset, Mapping, ValueMapping, and ValidationRule. |
| UC-050 View validation coverage | User can see which attributes have validation coverage and which P0 attributes lack required validation. |
| UC-060 Show Attribute lineage | User can view ordered lineage from source endpoint through mapping/value mapping to `KNVV-KDGRP`, validation rules, dataset evidence, and handover/report outputs. |
| UC-061 Generate impact report | User can select changed Customer Group or value list/rule and see affected mappings, validations, datasets, issues, decisions, owners, and reports. |
| UC-072 Create ChangeRequest | Approved model changes produce a ChangeRequest linked to affected objects, evidence, PatchProposal, and validation result. |
| UC-080 Create AI PatchProposal from pasted note | User can paste a project note about `CH01` / `A17`; AI returns a structured PatchProposal with assumptions, affected objects, proposed changes, and human checks. |
| UC-081 Review and approve AI PatchProposal | User can review validation results and diff, approve or reject, and verify rejected patches do not modify canonical files. |
| UC-090 Generate Repository Health Report | Health report shows parse/schema errors, broken references, SAP context violations, missing owners, missing validations, stale index, and AI availability. |
| UC-100 Search by SAP field, attribute, value, or issue | Searching `KNVV-KDGRP`, Customer Group, `CH01`, or `A17` returns the expected Attribute, FieldEndpoint, mapping/value mapping, issue, and decision objects. |
| UC-120 Validate repository | Validation detects invalid frontmatter, duplicate IDs, broken references, invalid statuses, SAP context errors, and unsafe AI patch attempts. |
| UC-121 Detect stale index | System warns when generated index artifacts are older than canonical model files and offers rebuild. |
| UC-130 Open Martenweave Workbench | User can launch the local Workbench from the installed package, bind it to a repository, and view repository status without running Node.js setup. |
| UC-131 Workbench respects Core boundaries | Workbench displays canonical objects, reports, and proposals; it does not store canonical truth independently or bypass approval gates. |

## Canonical Demo Acceptance

The MVP demo is accepted when the user can complete this chain:

1. Open a local Business Partner model repository.
2. Search for Customer Group or `KNVV-KDGRP`.
3. Open Customer Group Attribute Detail.
4. See Customer role slice and Customer Sales Area context.
5. See target FieldEndpoint `KNVV-KDGRP`.
6. Register/profile a Customer Sales Area sample dataset.
7. Detect a gap or unresolved condition for `CH01` / `A17`.
8. Create an issue from the gap.
9. Generate an impact report for Customer Group.
10. Paste a project note into AI Patch Review.
11. Review the structured PatchProposal, validation result, assumptions, and diff.
12. Approve the patch manually.
13. Confirm canonical files changed only after approval.
14. Confirm a ChangeRequest links the approved change to affected objects.

## MVP Completion Status

Current product-owner status:

```text
MVP implementation complete; awaiting independent review and promotion.
```

The MVP is complete only when the full 14-step canonical demo chain above can be completed locally from a fresh checkout, using the Customer Group / `KNVV-KDGRP` repository path, without adding out-of-scope platform capabilities.

P0 completion tasks:

| Task | Status | Outcome |
|---|---|---|
| `TASK-0029` | review | Approving a ChangeRequest applies linked accepted PatchProposal changes, records implementation status, exposes changed files, validation/index/audit evidence, and rolls back on failure. |
| `TASK-0030` | review | User can view source endpoint -> mapping -> value mapping -> `KNVV-KDGRP` -> validation path in the UI. |
| `TASK-0031` | review | User can persist a gap-derived Issue to canonical `model/issues/` files, then list and inspect it. |
| `TASK-0033` | review | User sees structured before/after diff and read-only Git dirty-state before canonical mutation. |
| `TASK-0034` | review | User sees schema/version basics, object counts, validation state, index fresh/stale/missing state, and rebuild action. |
| `TASK-0035` | review | Attribute, FieldEndpoint, Mapping, ValidationRule, PatchProposal, and ChangeRequest render as business-readable sections, with raw frontmatter secondary. |
| `TASK-0036` | review | Pasting a `CH01` / `A17` / Customer Group note returns a deterministic PatchProposal scaffold without external AI dependencies. |

Acceptance verification now includes a browser E2E smoke test:

```bash
pnpm --dir apps/web test:e2e
```

The E2E test runs the local Customer Group workflow against a copied temporary model repository so canonical sample files are not mutated.

Product-owner definition of done:

- all P0 blocker tasks above are implemented and reviewed;
- the complete canonical demo chain is reproducible from a fresh local checkout;
- backend tests, frontend tests, API lint, web lint, and frontend typecheck pass;
- canonical model files mutate only after approved ChangeRequest workflow;
- rejected patches and rejected ChangeRequests do not mutate canonical model files;
- generated SQLite remains disposable and rebuildable from canonical files;
- no SaaS tenancy, SAP write-back, required graph database, enterprise workflow engine, or real AI provider is required for the MVP;
- the Workbench is local-only and does not mutate canonical files outside the approved proposal flow.

## Completion Evidence

Coding agents should provide:

- command output or screenshots showing repository validation;
- generated index status;
- sample dataset profile and gap report;
- Customer Group attribute detail evidence;
- impact report evidence;
- PatchProposal review evidence;
- approved ChangeRequest evidence;
- test results for validators and core services.
