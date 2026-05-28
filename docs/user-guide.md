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
modelops init ./my-model
```

### Dataset → Model

```bash
# Profile a CSV or XLSX file
modelops profile-dataset customer_sample.csv --repo ./my-model

# Infer draft model objects from the profile
modelops infer-model generated/dataset_profiles/customer_sample.json --repo ./my-model
```

### Model-Side Gaps

Detect missing source links and ownership gaps inside the model itself:

```bash
modelops gaps --check-model --repo ./my-model
```

This reports `MODEL_ATTRIBUTE_MISSING_SOURCE` (critical) and `MISSING_OWNER` (warning) without requiring a dataset file. See [Model-Side Gap Detection](model-side-gaps.md) for details and fix examples.

### Validation

```bash
# Validate all canonical files
modelops validate --repo ./my-model

# Strict mode — fail on warnings (exit 2) as well as errors (exit 1)
modelops validate --repo ./my-model --strict

# Show repository health
modelops health --repo ./my-model
```

**Exit codes:**
- `0` — clean (no errors, no warnings)
- `1` — errors found
- `2` — warnings found (only with `--strict`)

### Index and Search

```bash
# Build SQLite index and optional JSONL exports
modelops build-index --repo ./my-model --jsonl
```

### Impact Analysis

```bash
# Show what depends on an object
modelops impact FEP-S4-KNVV-KDGRP --repo ./my-model
```

### Proposal Review and Apply

```bash
# List proposals
modelops proposal list --repo ./my-model

# Show proposal details
modelops proposal show PP-001 --repo ./my-model

# Validate a proposal
modelops proposal validate PP-001 --repo ./my-model

# Review bundle: report + impact + validation in one view
modelops proposal review-bundle PP-001 --repo ./my-model

# Preview changes without writing files
modelops proposal apply PP-001 --repo ./my-model --dry-run

# Apply an accepted proposal
modelops proposal apply PP-001 --repo ./my-model --apply
```

### Export and Import

```bash
# Export model to CSV (one file per type)
modelops export-model --repo ./my-model --format csv

# Export model to XLSX (one workbook, one sheet per type)
modelops export-model --repo ./my-model --format xlsx

# Import spreadsheet edits as a new PatchProposal
modelops import-model-sheet generated/exports/csv --repo ./my-model --json
```

### API Server

```bash
# Start the local API for UI integration
modelops serve --repo ./my-model --host 127.0.0.1 --port 8000
```

---

## File-to-Model Flow

Starting from a dataset:

1. Place `customer_sample.csv` in `data/samples/`.
2. Run `modelops profile-dataset` to generate a deterministic JSON profile.
3. Run `modelops infer-model` to create a `PatchProposal` with draft:
   - `Dataset`
   - `BusinessEntity`
   - `Attribute`
   - `FieldEndpoint`
   - `Mapping`
4. Review the proposal in `model/patch-proposals/PP-INFER-...md`.
5. Transition status to `accepted` when ready.
6. Apply with `modelops proposal apply --apply`.

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
modelops proposal review-bundle PP-001 --repo ./my-model
```

It prints:

1. **Report** — proposal identity, risk level, staleness, and operation count.
2. **Impact** — affected objects and relationships (requires a built index).
3. **Validation** — deterministic safety check with error/warning counts.

Use `--json` to consume the bundle programmatically:

```bash
modelops proposal review-bundle PP-001 --repo ./my-model --json
```

The review bundle is read-only and does not modify any files. Run it before approval to confirm a proposal is safe and its scope is understood.

---

## Spreadsheet Export/Import Flow

Martenweave treats spreadsheets as **views**, not sources of truth.

### Export
```bash
modelops export-model --repo ./my-model --format xlsx
# → generated/exports/model.xlsx
```

### Edit in Excel
Open the workbook, edit names, descriptions, or statuses, then save.

### Import
```bash
modelops import-model-sheet generated/exports/csv --repo ./my-model --json
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
| Initialize repo | `modelops init <path>` |
| Profile dataset | `modelops profile-dataset <file> --repo <path>` |
| Infer model | `modelops infer-model <profile> --repo <path>` |
| Validate | `modelops validate --repo <path>` |
| Build index | `modelops build-index --repo <path> --jsonl` |
| List proposals | `modelops proposal list --repo <path>` |
| Dry-run apply | `modelops proposal apply <id> --repo <path> --dry-run` |
| Apply proposal | `modelops proposal apply <id> --repo <path> --apply` |
| Export CSV | `modelops export-model --repo <path> --format csv` |
| Export XLSX | `modelops export-model --repo <path> --format xlsx` |
| Import sheet | `modelops import-model-sheet <path> --repo <path> --json` |
| Start API | `modelops serve --repo <path> --host 127.0.0.1 --port 8000` |
