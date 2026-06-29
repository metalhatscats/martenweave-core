# Martenweave User Guide

> Practical guide to using Martenweave: from your first dataset to reviewed model changes.

---

## What Martenweave Is

Martenweave is a local-first, agentic data model registry. It turns datasets and business knowledge into structured, traceable, validated canonical files that both humans and agents can read, review, and evolve safely.

**It is not:**
- A cloud SaaS with multi-tenant login
- A drag-and-drop diagram tool
- A database that hides your model behind a proprietary UI
- An AI that silently rewrites your files

**It is:**
- Canonical Markdown + YAML files in a folder
- A CLI and local API for building, validating, and changing models
- A proposal-first workflow where every edit becomes a reviewable PatchProposal
- Deterministic validation before any file is written

---

## Core Workflow

```
Dataset → Profile → Infer → Propose → Validate → Approve → Apply
```

1. **Profile** a dataset to understand its shape.
2. **Infer** draft model objects from the profile.
3. **Review** the generated PatchProposal.
4. **Validate** the proposal against deterministic rules.
5. **Apply** the proposal to canonical files (after human approval).
6. **Export** the model to spreadsheets for workshops.
7. **Import** spreadsheet edits back as new proposals.

---

## Canonical Files Are the Source of Truth

Every model object lives as a Markdown file with YAML frontmatter:

```markdown
---
id: ATTR-CUST-SALES-CUSTOMER-GROUP
type: Attribute
status: draft
name: Customer Group
domain: DOMAIN-CUSTOMER-BP
---

# Customer Group

Sales-area-dependent customer grouping used in sales processes.
```

**Key rules:**
- IDs are uppercase with hyphens: `^[A-Z][A-Z0-9]*(-[A-Z0-9]+)*$`
- Every object has `id`, `type`, and `status`
- Files are organized in `model/` by convention, not rigid subfolders
- `generated/` contains disposable indexes and exports — rebuildable anytime

---

## CLI Commands

### Repository Setup

```bash
# Scaffold a new repository
martenweave init ./my-model
```

### Dataset → Model

```bash
# Profile a CSV or XLSX file
martenweave profile-dataset customer_sample.csv --repo ./my-model

# Infer draft model objects from the profile
martenweave infer-model generated/dataset_profiles/customer_sample.json --repo ./my-model
```

### Model-Side Gaps

Detect missing source links and ownership gaps inside the model itself:

```bash
martenweave gaps --check-model --repo ./my-model
```

This reports `MODEL_ATTRIBUTE_MISSING_SOURCE` (critical) and `MISSING_OWNER` (warning) without requiring a dataset file. See [Model-Side Gap Detection](model-side-gaps.md) for details and fix examples.

### Validation

```bash
# Validate all canonical files
martenweave validate --repo ./my-model

# Strict mode — fail on warnings (exit 2) as well as errors (exit 1)
martenweave validate --repo ./my-model --strict

# Suppress noisy methodology warnings for simple models
martenweave validate --repo ./my-model --suppress-methodology-warnings

# Show repository health
martenweave health --repo ./my-model
```

**Exit codes:**
- `0` — clean (no errors, no warnings)
- `1` — errors found
- `2` — warnings found (only with `--strict`)

### Index and Search

```bash
# Build SQLite index and optional JSONL exports
martenweave build-index --repo ./my-model --jsonl

# Generate Markdown docs and the local static read-only HTML viewer
martenweave docs-build --repo ./my-model --site /tmp/martenweave-viewer
```

The viewer is generated from `generated/modelops.db` and includes `index.html`, `objects.html`,
per-object detail pages, `gaps.html`, `decisions.html`, `owners.html`, `search-index.json`, and
`viewer-manifest.json`. It is local/static/read-only and disposable. Use it to inspect the current
index, not to edit the model.

Boundaries:

- Canonical files in `model/` remain the source of truth.
- The viewer has no hosted service, login, editor, workflow engine, SAP write-back, or AI
  auto-mutation path.
- If the index is stale, the viewer still builds but shows a stale-index warning and records the
  freshness state in `viewer-manifest.json`.
- If the index is missing, `docs-build` fails clearly; run `martenweave build-index` first.

See [Local Static Viewer](local-static-viewer.md) for the full generated-file list and preview
commands.

### Impact Analysis

```bash
# Show what depends on an object
martenweave impact FEP-S4-KNVV-KDGRP --repo ./my-model
```

### Proposal Review and Apply

```bash
# List proposals
martenweave proposal list --repo ./my-model

# Show proposal details
martenweave proposal show PP-001 --repo ./my-model

# Validate a proposal
martenweave proposal validate PP-001 --repo ./my-model

# Review bundle: report + impact + validation in one view
martenweave proposal review-bundle PP-001 --repo ./my-model

# Preview changes without writing files
martenweave proposal apply PP-001 --repo ./my-model --dry-run

# Apply an accepted proposal
martenweave proposal apply PP-001 --repo ./my-model --apply
```

### Export and Import

```bash
# Export model to CSV (one file per type)
martenweave export-model --repo ./my-model --format csv

# Export model to XLSX (one workbook, one sheet per type)
martenweave export-model --repo ./my-model --format xlsx

# Export JSON Schema for all canonical object types
martenweave export-schema --repo ./my-model --type all --output generated/schemas/canonical_objects.json

# Export JSON Schema for a single type
martenweave export-schema --repo ./my-model --type Attribute --json

# Import spreadsheet edits as a new PatchProposal
martenweave import-model-sheet generated/exports/csv --repo ./my-model --json
```

### API Server

```bash
# Start the local API for UI integration
martenweave serve --repo ./my-model --host 127.0.0.1 --port 8000
```

---

## File-to-Model Flow

Starting from a dataset:

1. Place `customer_sample.csv` in `data/samples/`.
2. Run `martenweave profile-dataset` to generate a deterministic JSON profile.
3. Run `martenweave infer-model` to create a `PatchProposal` with draft:
   - `Dataset`
   - `BusinessEntity`
   - `Attribute`
   - `FieldEndpoint`
   - `Mapping`
4. Review the proposal in `model/patch-proposals/PP-INFER-...md`.
5. Transition status to `accepted` when ready.
6. Apply with `martenweave proposal apply --apply`.

The inferred proposal includes:
- **Assumptions** the agent made (e.g., "all columns treated as strings")
- **Human checks** you should verify (e.g., "confirm customer_id is the primary key")

---

## Proposal Review Flow

Every model edit goes through the same safe path:

1. **Generation** — chat instruction, spreadsheet import, or inference creates a `PatchProposal`
2. **Validation** — deterministic rules check IDs, types, references, and domain constraints
3. **Dry-run** — preview exactly which files and fields would change
4. **Approval** — human changes status to `accepted`
5. **Apply** — atomic write with rollback, audit event, and index rebuild

**You cannot apply a proposal that:**
- Has validation errors
- Has status other than `accepted`
- Has already been applied

### Review Bundle

The `proposal review-bundle` command combines three review steps into a single output:

```bash
martenweave proposal review-bundle PP-001 --repo ./my-model
```

It prints:

1. **Report** — proposal identity, risk level, staleness, and operation count.
2. **Impact** — affected objects and relationships (requires a built index).
3. **Validation** — deterministic safety check with error/warning counts.

Use `--json` to consume the bundle programmatically:

```bash
martenweave proposal review-bundle PP-001 --repo ./my-model --json
```

The review bundle is read-only and does not modify any files. Run it before approval to confirm a proposal is safe and its scope is understood.

---

## Spreadsheet Export/Import Flow

Martenweave treats spreadsheets as **views**, not sources of truth.

### Export
```bash
martenweave export-model --repo ./my-model --format xlsx
# → generated/exports/model.xlsx
```

### Edit in Excel
Open the workbook, edit names, descriptions, or statuses, then save.

### Import
```bash
martenweave import-model-sheet generated/exports/csv --repo ./my-model --json
# → Generates a new PatchProposal with update_object and create_object ops
```

**Import rules:**
- Detected changes become `update_object` operations
- New rows become `create_object` operations
- Duplicate IDs trigger warnings
- **Deletes are never generated automatically**

---

## Validation Layers

Validation is deterministic and runs in three layers:

1. **Layer 1 — Individual object:**
   - ID format, type registration, status presence
2. **Layer 2 — Cross-object:**
   - Duplicate IDs, broken references, type mismatches
3. **Layer 3 — Domain context:**
   - SAP-specific rules (optional), ownership checks, LoV coverage

Invalid objects are blocked from the index by default. Use `--allow-invalid` to override.

---

## Quick Reference

| Task | Command |
|---|---|
| Initialize repo | `martenweave init <path>` |
| Profile dataset | `martenweave profile-dataset <file> --repo <path>` |
| Infer model | `martenweave infer-model <profile> --repo <path>` |
| Validate | `martenweave validate --repo <path>` |
| Build index | `martenweave build-index --repo <path> --jsonl` |
| List proposals | `martenweave proposal list --repo <path>` |
| Dry-run apply | `martenweave proposal apply <id> --repo <path> --dry-run` |
| Apply proposal | `martenweave proposal apply <id> --repo <path> --apply` |
| Export CSV | `martenweave export-model --repo <path> --format csv` |
| Export XLSX | `martenweave export-model --repo <path> --format xlsx` |
| Import sheet | `martenweave import-model-sheet <path> --repo <path> --json` |
| Start API | `martenweave serve --repo <path> --host 127.0.0.1 --port 8000` |
