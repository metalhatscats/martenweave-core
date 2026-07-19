# Martenweave Product North Star

> Factory memory document. Derived from `README.md`, `docs/product/MVP_SCOPE.md`,
> `docs/architecture/WORKBENCH_BOUNDARY.md`, and `AGENTS.md`. This file does not
> redefine the product; it consolidates the existing scope decisions into one
> reference that agents must not drift from. **Changing this file requires
> maintainer approval** (see `policies/AGENT_PREVENTIONS.md`).

## Product sentence

Martenweave is an open-source, backend-first **model governance and evidence layer**
for SAP migration, MDM, data governance, and AMS. It turns data models into a
structured, traceable, validated, AI-ready model knowledge layer.

Core MVP sentence (from `docs/product/MVP_SCOPE.md`, unchanged):

> The MVP proves that data model knowledge can be versioned, validated, traced, and
> prepared for safe AI-assisted delivery. SAP Business Partner migration is the first
> domain pack used to prove this.

## The question the product answers

> When a model object, mapping, rule, or dataset changes, can the team quickly see
> what is affected and what must be updated?

## Product surfaces

| Surface | Responsibility |
|---|---|
| **Martenweave Core** (`modelops_core`) | Canonical parsing, deterministic validation, indexing, gap/lineage/impact analysis, patch proposals, change requests, audit, CLI (`martenweave`, alias `modelops`). |
| **Local API** | Bound FastAPI integration surface for the Workbench and agents (`martenweave serve`). |
| **Martenweave Workbench** | Local browser UI for assessment, investigation, review, reports, and controlled changes. Reads and mutates canonical files only through Core services and approval gates. |

## Primary users

1. **SAP migration data analyst** — mapping, field rules, dataset quality, issue follow-up.
2. **MDM / data governance specialist** — ownership, definitions, stewardship gaps.
3. **SAP functional consultant** — business attribute ↔ SAP table/field connections.
4. **AMS handover recipient** — clean model explanation after go-live.

## Core principles (binding)

- **Canonical files are the source of truth.** Markdown + YAML frontmatter objects in `model/`.
- **Generated index is disposable.** SQLite/JSONL in `generated/` is rebuildable; never edited.
- **Deterministic validation first.** No AI involvement in validation.
- **AI must not silently mutate.** AI creates `PatchProposal` objects; humans approve; approved changes become `ChangeRequest`s.
- **Local-first.** No cloud dependencies, no SaaS lock-in.
- **Workbench does not bypass Core.** All reads/mutations go through Core services and approval gates.

## Non-goals (permanent unless the maintainer decides otherwise)

- Not an enterprise MDM platform, not an SAP MDG replacement, not a workflow engine,
  not a full data catalog.
- No direct SAP system integration or write-back, no transport management.
- No hosted/multi-tenant SaaS, no authentication or RBAC, no cloud dependencies.
- No autonomous mutation: no model change without human review.
- No generic chatbot, no broad "chat with your data" surface.
- No master-data record storage, no raw data lake, no ETL, no graph DB/Kafka infrastructure.
- No real-time SAP lineage, no ABAP extraction.
- No full DAMA compliance claims or certification language.

## Current proof benchmark

The **Northstar Mobility Group synthetic pilot** (`examples/northstar_mobility_pilot`)
is the main product regression and user-journey benchmark: seven domains, 187 canonical
objects, deterministic datasets with intentional problems, reproducible via
`bash scripts/demo_northstar_pilot.sh` (11 self-verifying steps). Every product change
must keep this benchmark green and truthful.

## Success measures

- A clean checkout reproduces the pilot end-to-end (validate → index → profile → gaps →
  reports → impact → readiness → proposal → bundle → Workbench).
- Deterministic gates (tests, lint, build, contracts) pass locally and in CI.
- The public website claims match verified Core behavior exactly.
