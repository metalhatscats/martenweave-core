# Chat-to-Model Command Contract

> This document defines how chat-based user instructions become safe, structured model edits. The contract is UI-independent and applies to CLI, API, and the one-screen workspace.

---

## Core Rule

**AI never mutates canonical files directly.** Every instruction produces a `PatchProposal` that must pass deterministic validation and receive human approval before apply.

---

## The Flow

```
User Instruction
       │
       ▼
Intent Classification
       │
       ▼
Context Bundle (minimized)
       │
       ▼
Candidate Operations
       │
       ▼
PatchProposal (pending_review)
       │
       ▼
Deterministic Validation
       │
       ├── Errors ──→ Human must fix or reject
       │
       └── Pass ────→ Human approves / rejects
                          │
                          ▼
                    Apply (write canonical files)
                          │
                          ▼
                    Audit Event + Index Rebuild
```

---

## Intent Classes (v1)

| Intent | Description | Example Prompt |
|---|---|---|
| `create_model_from_file` | Profile a dataset and infer draft model objects | "Create a model from customer_sample.csv" |
| `add_entity` | Add a new `BusinessEntity` or `Dataset` | "Add a Customer Sales Area entity" |
| `add_attribute` | Add an `Attribute` linked to an entity | "Add a Customer Group attribute to Customer" |
| `rename_attribute` | Rename an existing attribute | "Rename 'Cust Group' to 'Customer Group'" |
| `add_relationship` | Link two objects with a relationship | "Link Customer to Business Partner" |
| `add_mapping` | Create a `Mapping` between field endpoints | "Map KNVV-KDGRP to Customer Group" |
| `add_validation_rule` | Add a validation or data quality rule | "Add a rule that Customer Group must not be empty" |
| `explain_impact` | Show what would be affected by a change | "What breaks if I rename Customer Group?" |
| `export_model` | Export canonical model to CSV/XLSX | "Export the model to Excel" |

### Unsupported Intents

Any instruction that does not match a supported intent class returns:
- A clear message: *"This type of instruction is not yet supported."*
- A list of supported intents.
- Optionally, a generic `PatchProposal` with `human_checks` asking for clarification.

---

## Context Bundle

The agent receives a **minimized, privacy-safe** context bundle — never raw dataset rows.

```json
{
  "repo_path": "/examples/customer_bp_model",
  "model_summary": {
    "entity_count": 5,
    "attribute_count": 12,
    "dataset_count": 1,
    "validation_status": "valid_with_warnings"
  },
  "relevant_objects": [
    {
      "id": "ENTITY-CUSTOMER-SALES-AREA",
      "type": "BusinessEntity",
      "name": "Customer Sales Area",
      "status": "draft"
    },
    {
      "id": "ATTR-CUST-SALES-CUSTOMER-GROUP",
      "type": "Attribute",
      "name": "Customer Group",
      "domain": "DOMAIN-CUSTOMER-BP"
    }
  ],
  "dataset_profiles": [
    {
      "dataset_id": "DATASET-CUSTOMER-SAMPLE",
      "columns": ["customer_id", "sales_org", "customer_group"],
      "inferred_types": ["string", "string", "string"]
    }
  ],
  "recent_proposals": ["PP-001", "PP-002"]
}
```

### Privacy Rules

- **No raw data values** are sent in the context bundle. Only column names, inferred types, and object metadata.
- **Dataset profiles** include bounded samples (max 5 values) from the profiler, never full rows.
- **Sensitive fields** flagged in the model (e.g., PII markers) are redacted from the bundle.

---

## Structured Operation Format

Every candidate operation follows the `PatchOperation` schema used by the CLI, API, and UI:

```yaml
op: update_object          # or create_object, add_relationship, etc.
object_id: ATTR-CUST-SALES-CUSTOMER-GROUP
object_type: Attribute
target_path: name           # dot-notation for nested fields, e.g. "sap_context.table"
before: "Cust Group"
after: "Customer Group"
reason: "User requested clearer business name"
```

### Operation Types

| `op` | Purpose | Required Fields |
|---|---|---|
| `create_object` | Create a new canonical object | `object_id`, `object_type`, `after` (full frontmatter dict) |
| `update_object` | Change a field on an existing object | `object_id`, `target_path`, `after` |
| `add_relationship` | Link two objects | `object_id`, `target_path` (reference field), `after` (target ID) |
| `add_evidence_link` | Link an object to evidence | `object_id`, `target_path`, `after` |
| `create_issue` | Create an `Issue` object | `object_id`, `after` (full frontmatter dict) |

---

## Examples

### Example 1: Create model from file

**User:** "Create a model from customer_sample.csv"

**Agent response:**
- Runs `profile-dataset` + `infer-model`
- Generates `PatchProposal` with:
  - `create_object` ops for `Dataset`, `BusinessEntity`, `Attribute`, `FieldEndpoint`, `Mapping`
- Includes assumptions: *"All columns treated as strings pending confirmation."*
- Includes human checks: *"Verify 'customer_id' is the primary identifier."*

### Example 2: Rename attribute

**User:** "Rename 'Cust Group' to 'Customer Group'"

**Agent response:**
- Searches for attribute with name "Cust Group"
- Finds `ATTR-CUST-SALES-CUSTOMER-GROUP`
- Generates `PatchProposal` with single operation:

```yaml
op: update_object
object_id: ATTR-CUST-SALES-CUSTOMER-GROUP
object_type: Attribute
target_path: name
before: "Cust Group"
after: "Customer Group"
reason: "User requested clearer business name"
```

### Example 3: Explain impact

**User:** "What breaks if I rename Customer Group?"

**Agent response:**
- Runs impact analysis on `ATTR-CUST-SALES-CUSTOMER-GROUP`
- Returns impact report (no proposal created):
  - Downstream: `FEP-S4-KNVV-KDGRP`, `MAP-CUSTOMER-GROUP`
  - Mappings: 1 mapping uses this attribute
  - Proposals: `PP-003` also touches this attribute

### Example 4: Unsupported instruction

**User:** "Delete the entire Customer domain"

**Agent response:**
- Flags as unsupported destructive operation.
- Returns: *"Mass deletion is not supported via chat. Create a PatchProposal manually or break this into individual object removals."*
- No proposal generated.

---

## Assumptions and Human Checks

Every proposal generated from chat includes:

1. **Assumptions** — what the agent inferred without explicit confirmation.
2. **Human Checks** — questions the reviewer must answer before approving.

```yaml
assumptions:
  - "Column 'customer_group' is treated as a business Attribute."
  - "No ValueList is attached; values are free-text."

human_checks:
  - "Confirm 'customer_id' is the primary identifier."
  - "Should 'sales_org' link to an existing Organization entity?"
```

If a user instruction is ambiguous, the agent produces a proposal with **more human checks** rather than guessing.

---

## Validation Gate

Before any proposal is presented for approval, it passes through:

1. **Layer 1 — Proposal validation:** `validate_patch_proposal()`
   - ID format, type, status, operations non-empty, allowed ops.
2. **Layer 2 — Post-apply validation:** `validate_objects()`
   - Broken references, duplicate IDs, type mismatches.
3. **Layer 3 — Domain validation (optional):**
   - SAP context rules, ownership checks, LoV coverage.

Validation errors are shown to the user inline. The proposal cannot be applied until errors are resolved.

---

## Apply Gate

Only proposals with `status: accepted` and no validation errors can be applied. The apply action:

1. Backs up affected files.
2. Writes changes to canonical `.md` files.
3. Runs post-apply validation.
4. Rolls back on failure.
5. Writes an audit event.
6. Rebuilds the SQLite index.

---

## Contract Summary

| Concern | Rule |
|---|---|
| Direct mutation | Never. All changes go through PatchProposal. |
| Ambiguous instructions | Produce assumptions + human checks, not guesses. |
| Unsupported instructions | Reject with explanation, no proposal. |
| Privacy | Context bundle contains metadata only, no raw data. |
| Validation | Deterministic, layered, blocking. |
| Approval | Human must explicitly accept before apply. |
| Audit | Every apply writes an append-only audit event. |
| UI independence | Same contract used by CLI, API, and workspace. |
