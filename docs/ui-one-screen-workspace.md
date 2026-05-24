# Minimal One-Screen Agentic Data Modeling Workspace

> This document defines the UI direction for Martenweave. The workspace is a thin interface over the core library — not a separate product surface.

---

## Principles

1. **One screen, three zones.** The primary interface is a single screen split into chat, data, and proposal panels.
2. **Chat-first, not forms-first.** Users instruct the agent; the agent proposes structured changes. Humans review and approve.
3. **Canonical files are the source of truth.** The UI reads from and writes through the same canonical Markdown/YAML files as the CLI.
4. **No dashboard bloat.** No admin screens, complex navigation, or generic SaaS chrome. Every pixel serves model-building or model-review.
5. **Docs as a secondary page.** A single docs page explains commands, concepts, and the canonical file format. Nothing more.

---

## Primary Screen: The Agentic Cockpit

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Martenweave — Agentic Data Model Registry                                  │
├──────────────────────┬──────────────────────────────┬───────────────────────┤
│                      │                              │                       │
│  Chat / Instructions │  Data / Model Panel          │  Proposals / Changes  │
│                      │                              │                       │
│  > "Add a Customer   │  ┌─ Entities ─────────┐     │  ┌─ Pending ────────┐ │
│    Sales Area entity  │  │ Customer            │     │  │ PP-001 add entity │ │
│    with KNVV fields"  │  │ Business Partner    │     │  │ PP-002 rename...  │ │
│                      │  └─────────────────────┘     │  └───────────────────┘ │
│  [Send]              │                              │                       │
│                      │  ┌─ Attributes ────────┐     │  ┌─ Dry-Run Diff ───┐ │
│  --- Agent replies ---│  │ Customer Group      │     │  │ + name: "..."    │ │
│  Proposal PP-003      │  │ Sales Org           │     │  │ + status: draft  │ │
│  ready for review.    │  └─────────────────────┘     │  └───────────────────┘ │
│                      │                              │                       │
│  [View Proposal] ->  │  ┌─ Datasets ──────────┐     │  [Apply] [Reject]    │
│                      │  │ customer_sample.csv  │     │  [Dry-Run]           │
│                      │  └─────────────────────┘     │                       │
│                      │                              │                       │
│                      │  ┌─ Validation Status ─┐     │  Warnings: 1          │
│                      │  │ 42 objects valid    │     │  │ missing mapping   │ │
│                      │  │ 3 warnings          │     │                       │
│                      │  └─────────────────────┘     │                       │
│                      │                              │                       │
├──────────────────────┴──────────────────────────────┴───────────────────────┤
│  Status: connected to /examples/customer_bp_model   [Validate] [Build Index]│
└─────────────────────────────────────────────────────────────────────────────┘
```

### Zone 1 — Chat / Instruction Panel (left, ~25% width)

- **Input:** Free-text chat box for model-building requests.
- **History:** Scrollable conversation with the agent.
- **Context awareness:** The agent receives a minimized context bundle of current model objects (entities, attributes, datasets) — never raw dataset rows.
- **Intent classes supported in v1:**
  - `create model from file`
  - `add entity`
  - `add attribute`
  - `rename attribute`
  - `add relationship`
  - `add mapping`
  - `add validation rule`
  - `explain impact`
  - `export model`
- **Agent replies** with:
  - A `PatchProposal` summary (ID, affected objects, assumptions, human checks).
  - Links to open the proposal in the Proposals panel.
  - Warnings if the instruction is ambiguous or unsupported.

### Zone 2 — Data / Model Panel (center, ~50% width)

- **Entity list:** Expandable cards showing `BusinessEntity`, `Dataset`, `System`, and `MasterDataDomain` objects.
- **Attribute list:** Linked to selected entity; shows `Attribute`, `FieldEndpoint`, and `Mapping` details.
- **Validation status:** Inline badges per object (valid / warning / error) with hover-to-see details.
- **Dataset profiles:** Shows imported datasets with column names, inferred types, and linkage to model objects.
- **Search:** Fast text search across all object IDs, names, and descriptions.
- **Click-through:** Selecting an object highlights its upstream and downstream relationships (traceability).

### Zone 3 — Proposals / Changes Panel (right, ~25% width)

- **Pending proposals:** List of `PatchProposal` objects from `model/patch-proposals/`.
- **Proposal detail:** Frontmatter, operations table, affected objects.
- **Dry-run diff:** Shows exact frontmatter fields and files that would change.
- **Actions per proposal:**
  - `Validate` — run deterministic validation
  - `Dry-Run` — preview changes
  - `Apply` — write to canonical files (only if status = `accepted`)
  - `Reject` — transition status to `rejected`
- **Impact summary:** For each proposal, show upstream/downstream objects that would be affected.
- **Warnings:** High-risk changes (mapped fields, active objects, missing owners) are visually highlighted.

---

## Secondary Page: Docs

A single scrollable docs page served at `/docs` (or equivalent) containing:

1. **Product overview** — what Martenweave is and is not.
2. **Core workflow** — file → profile → infer → propose → validate → apply.
3. **CLI commands** — one-line descriptions with links to canonical docs.
4. **Canonical file format** — frontmatter schema and ID conventions.
5. **Proposal review flow** — how to read, validate, dry-run, and apply proposals.
6. **Spreadsheet export/import** — how exports are views, imports become proposals.

No multi-page documentation site, no versioned docs, no search engine.

---

## Backend / API Capabilities Required from Core

The UI is a thin client. All heavy logic lives in `modelops_core` and is exposed through:

| Capability | Core Service | CLI Equivalent |
|---|---|---|
| List objects by type | `scan_repository`, `build-index` | `modelops build-index` |
| Object detail | `parse_file` | — |
| Search | SQLite index query | — |
| Validation | `validate_objects` | `modelops validate` |
| Impact analysis | `impact_service` | `modelops impact` |
| Dataset profile | `dataset_profiler` | `modelops profile-dataset` |
| Model inference | `model_inference_service` | `modelops infer-model` |
| Proposal list/detail | `patch_proposal_service` | `modelops proposal list/show` |
| Proposal validation | `patch_validator` | `modelops proposal validate` |
| Proposal dry-run | `dry_run_patch_proposal` | `modelops proposal apply --dry-run` |
| Proposal apply | `apply_patch_proposal` | `modelops proposal apply` |
| Export model | `export_service` (planned) | `modelops export-model` |
| Audit log query | `audit_service` (planned) | `modelops audit-log` |
| Traceability | `lineage_service` (planned) | `modelops trace` |
| Health report | `health_service` | `modelops health` |
| Analysis reports | `analyze_service` (planned) | `modelops analyze` |

The UI should call these services through a lightweight local API (see Issue #10) or directly import the Python services if embedded in a desktop/IDE context.

---

## What Is Explicitly Out of Scope

- Multi-tenant user management or authentication
- Admin dashboards, analytics, or metrics charts
- Drag-and-drop diagram editors (for v1)
- Real-time collaborative editing
- Cloud hosting or SaaS deployment concerns
- Forms-first CRUD for every object type
- Separate pages for every object type

---

## Canonical Files Remain the Source of Truth

The UI never holds hidden state. Everything it displays is derived from:
- `model/*.md` — canonical objects
- `model/patch-proposals/*.md` — proposed changes
- `generated/*.jsonl`, `generated/*.db` — disposable indexes and exports

If the UI is closed, the repository remains fully usable via CLI. If the CLI is run, the UI reflects the change on next refresh.
