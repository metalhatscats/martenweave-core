# Agent Quick Reference

> Concise guide for AI agents working in the Martenweave Core repository.  
> For deep dives, see the linked documents below.

---

## Canonical Object Types (1-line)

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
| `System` | Logical system (e.g., S/4HANA) |
| `ValidationRule` | Expected correctness rule |
| `Dataset` | Input/evidence, not model truth |

---

## ID Format

- Regex: `^[A-Z][A-Z0-9]*(-[A-Z0-9]+)*$`
- Examples: `DOMAIN-CUSTOMER-BP`, `ATTR-CUST-SALES-CUSTOMER-GROUP`, `FEP-S4-KNVV-KDGRP`
- Must be globally unique and stable.

---

## File Layout

```
model-repository/
  modelops.config.yaml        # Repo config (enabled_domain_packs, etc.)
  model/                      # Canonical objects (source of truth)
    DOMAIN-*.md
    ENTITY-*.md
    ATTR-*.md
    FEP-*.md
    MAP-*.md
    ...
  generated/                  # Disposable artifacts (rebuildable)
    modelops.db
    search_documents.jsonl
    lineage_edges.jsonl
  data/samples/               # Sample datasets for profiling
```

---

## Validation Layers (1–3)

| Layer | What it checks |
|---|---|
| **1 — Individual** | ID format, type registered, status non-empty, frontmatter valid |
| **2 — Cross-object** | Duplicate IDs, broken references, reference type mismatches, cycles |
| **3 — Domain / Context** | SAP context rules (e.g., `KNVV` → `customer_sales_area`), lifecycle, ownership, methodology |

Entry point: `validate_objects(parsed_objects, enabled_domain_packs)` in `src/modelops_core/validation/pipeline.py`.

---

## Key CLI Commands

```bash
martenweave init ./my-model
martenweave validate --repo ./my-model
martenweave build-index --repo ./my-model --jsonl
martenweave health --repo ./my-model
martenweave impact <OBJECT_ID> --repo ./my-model
martenweave propose-patch --from ./note.md --repo ./my-model
martenweave proposal accept <PP-ID> --reviewer <name> [--skip-cr-creation]
martenweave export-schema --type Attribute --output schema.json
```

---

## Common Relationships

- `Attribute` → `AttributeUsage` → `FieldEndpoint`
- `Mapping` links `FieldEndpoint` (source) → `FieldEndpoint` (target)
- `ValueMapping` links `ValueList` (source) → `ValueList` (target)
- `Decision.evidence` → `Evidence`
- `PatchProposal` → `ChangeRequest` (linked via `linked_proposals`)
- `FieldEndpoint` with `endpoint_type: sap_table_field` requires `entity_context`

---

## Patch Proposal Lifecycle

1. **Generate** — `build_patch_proposal_from_note()` uses repository context bundle.
2. **Review** — Human reviews; status becomes `accepted` or `rejected`.
3. **Auto-CR** — On accept, a `ChangeRequest` is created and approved automatically (unless `--skip-cr-creation`).
4. **Apply** — `apply_patch_proposal()` runs **pre-write validation** before writing any file, then post-apply validation, with rollback on failure.

---

## Technology Stack

- Python ≥3.11, Pydantic ≥2.6, Typer ≥0.12, Rich ≥13, PyYAML ≥6
- SQLite generated index, pytest, ruff (line length 100)

---

## Deep-Dive Links

| Topic | Document |
|---|---|
| Full system architecture | [`SYSTEM_ARCHITECTURE.md`](SYSTEM_ARCHITECTURE.md) |
| Conceptual domain model | [`DOMAIN_MODEL.md`](DOMAIN_MODEL.md) |
| Schema & validation spec | [`SCHEMA_AND_VALIDATION_SPEC.md`](SCHEMA_AND_VALIDATION_SPEC.md) |
| Core domain boundaries | [`CORE_DOMAIN_MODEL.md`](CORE_DOMAIN_MODEL.md) |
| AI patch workflow | [`AI_PATCH_WORKFLOW.md`](AI_PATCH_WORKFLOW.md) |
| Patch & approval flow | [`PATCH_PROPOSAL_AND_APPROVAL_FLOW.md`](PATCH_PROPOSAL_AND_APPROVAL_FLOW.md) |
| Lineage & impact | [`DATA_LINEAGE_AND_IMPACT_MODEL.md`](DATA_LINEAGE_AND_IMPACT_MODEL.md) |
| Testing strategy | [`../developer/TESTING_STRATEGY.md`](../developer/TESTING_STRATEGY.md) |
