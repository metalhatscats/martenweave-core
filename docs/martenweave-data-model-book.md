# Martenweave Data Model Book

> A practical playbook for creating, maintaining, reviewing, governing, and evolving data models in Martenweave.

---

## Philosophy

Martenweave treats the **canonical model as source of truth**.  
It is not a database schema, not a data catalog, and not a BI semantic layer.  
It is a structured, versioned, human-readable knowledge layer that sits between business language and physical implementation.

---

## Model Layers

### Layer 1: Domain

A `MasterDataDomain` groups model knowledge around a master data area.

```yaml
---
id: DOMAIN-CUSTOMER-BP
type: MasterDataDomain
status: active
name: Customer and Business Partner
---
```

**Rule**: Every object belongs to exactly one domain.  
**Anti-pattern**: Creating a single "Enterprise" domain that contains everything.

### Layer 2: Business Entity

A `BusinessEntity` is a conceptual object with business meaning.

```yaml
---
id: ENTITY-CUSTOMER-SALES-AREA
type: BusinessEntity
status: active
name: Customer Sales Area
domain: DOMAIN-CUSTOMER-BP
---
```

**Rule**: Name entities with business language, not table names.  
"Customer Sales Area" is better than "KNVV".

### Layer 3: Attribute

An `Attribute` is a semantic property with business meaning.

```yaml
---
id: ATTR-CUST-SALES-CUSTOMER-GROUP
type: Attribute
status: active
name: Customer Group
domain: DOMAIN-CUSTOMER-BP
---
```

**Rule**: Attributes should have `entity_context` linking them to a system/business grain.  
**Minimum metadata**: `id`, `type`, `status`, `name`, `domain`

### Layer 4: Field Endpoint

A `FieldEndpoint` is the physical representation (table/field, file column).

```yaml
---
id: FEP-S4-KNVV-KDGRP
type: FieldEndpoint
status: active
name: Customer Group (KNVV)
domain: DOMAIN-CUSTOMER-BP
endpoint_type: sap_table_field
sap_table: KNVV
sap_field: KDGRP
entity_context: ENTITY-CUSTOMER-SALES-AREA
---
```

**Rule**: SAP table fields must have `entity_context` and correct `context_category`:
- `KNVV` → `customer_sales_area`
- `KNB1` → `customer_company_code`
- `KNVP` → `customer_partner_function`
- `BUT000` → `bp_central`

### Layer 5: Mapping

A `Mapping` links source and target FieldEndpoints.

```yaml
---
id: MAP-CUST-GROUP-S4-TO-LEGACY
type: Mapping
status: active
name: Customer Group S/4 to Legacy
domain: DOMAIN-CUSTOMER-BP
source: FEP-LEGACY-CUST-GROUP
target: FEP-S4-KNVV-KDGRP
---
```

---

## Naming Principles

| Element | Convention | Example |
|---|---|---|
| Domain | `DOMAIN-{AREA}` | `DOMAIN-CUSTOMER-BP` |
| Entity | `ENTITY-{AREA}-{CONCEPT}` | `ENTITY-CUSTOMER-SALES-AREA` |
| Attribute | `ATTR-{AREA}-{CONCEPT}-{PROPERTY}` | `ATTR-CUST-SALES-CUSTOMER-GROUP` |
| Field Endpoint | `FEP-{SYSTEM}-{TABLE}-{FIELD}` | `FEP-S4-KNVV-KDGRP` |
| Mapping | `MAP-{AREA}-{SOURCE}-TO-{TARGET}` | `MAP-CUST-GROUP-S4-TO-LEGACY` |
| Value List | `VL-{AREA}-{CONCEPT}` | `VL-CUST-GROUP-CODES` |
| Change Request | `CR-{NNN}` | `CR-001` |
| Patch Proposal | `PP-{NNN}` | `PP-001` |

**Rule**: IDs must match `^[A-Z][A-Z0-9]*(-[A-Z0-9]+)*$`

---

## Simple Table vs Enterprise Object Modeling

### Simple Table Mode

Use when:
- You have a single CSV or spreadsheet
- No complex relationships
- Quick documentation is the goal

Create `Attribute` objects directly from column names.  
Skip `BusinessEntity` and `EntityContext` if the table is self-contained.

### Enterprise Object Mode

Use when:
- Multiple systems share the same business concept
- Traceability and lineage matter
- Governance and approval workflows are required

Create the full hierarchy: Domain → Entity → Attribute → FieldEndpoint → Mapping

---

## Ownership and Stewardship

### Minimum Ownership

Every object that participates in governance should have at least one of:
- `business_owner`
- `technical_owner`
- `data_steward`

```yaml
---
id: ATTR-CUST-SALES-CUSTOMER-GROUP
type: Attribute
status: active
name: Customer Group
domain: DOMAIN-CUSTOMER-BP
business_owner: sarah.smith@example.com
technical_owner: alex.dev@example.com
data_steward: jordan.gov@example.com
---
```

### Ownership Coverage Goal

- **Pilot**: >60% of active objects have an owner
- **Production**: >90% of active objects have an owner

---

## Value Lists and Reference Data

### ValueList

Define allowed values for fields that use codes.

```yaml
---
id: VL-CUST-GROUP-CODES
type: ValueList
status: active
name: Customer Group Codes
domain: DOMAIN-CUSTOMER-BP
values:
  - code: "01"
    description: "Key Account"
  - code: "02"
    description: "National"
---
```

### ValueMapping

Map source values to target values.

```yaml
---
id: VM-CUST-GROUP-LEGACY-TO-S4
type: ValueMapping
status: active
name: Customer Group Legacy to S/4
domain: DOMAIN-CUSTOMER-BP
value_list: VL-CUST-GROUP-CODES
mappings:
  - from: "KA"
    to: "01"
  - from: "NA"
    to: "02"
---
```

---

## Validation and Data Quality

### Validation Layers

1. **Layer 1 — Individual object**: ID format, required fields, YAML syntax
2. **Layer 2 — Cross-object**: Duplicate IDs, broken references, type mismatches
3. **Layer 3 — SAP context**: Table → context_category rules

### Running Validation

```bash
modelops validate --repo ./my-model
```

### Fixing Errors

```bash
# See detailed errors
modelops validate --repo ./my-model --json

# Build index even with warnings
modelops build-index --repo ./my-model --allow-invalid
```

---

## System Lineage and Interface Flows

### Lineage Edges

Lineage is generated automatically from references in canonical files:
- `Attribute` → `EntityContext`
- `FieldEndpoint` → `AttributeUsage`
- `Mapping` → `FieldEndpoint` (source/target)
- `IntegrationFlow` → `System`

### Tracing

```bash
# Full trace upstream and downstream
modelops trace FEP-S4-KNVV-KDGRP --direction both --repo ./my-model

# Impact analysis
modelops impact FEP-S4-KNVV-KDGRP --repo ./my-model
```

---

## Evidence, Decisions, and Audit

### Decision

Capture accepted reasoning so future team members understand why a model choice was made.

```yaml
---
id: DEC-001-CUSTOMER-GROUP-MAPPING
type: Decision
status: accepted
name: Customer Group Mapping Approach
domain: DOMAIN-CUSTOMER-BP
decision: "Map legacy KA/NA codes to S/4 01/02 via ValueMapping"
rationale: "Business confirmed one-to-one relationship; no splitting needed"
decided_by: sarah.smith@example.com
decided_on: "2026-01-15"
---
```

### Issue

Track problems or gaps.

```yaml
---
id: ISS-001-MISSING-OWNERSHIP
type: Issue
status: open
name: Missing Ownership on Customer Attributes
domain: DOMAIN-CUSTOMER-BP
severity: medium
description: "15 active attributes lack business_owner"
---
```

---

## Change Requests and Proposal Workflow

### Proposing a Change

1. Write a note describing the desired change
2. Generate a PatchProposal
   ```bash
   modelops propose-patch --from ./my-note.md --repo ./my-model
   ```
3. Review the proposal
   ```bash
   modelops proposal-impact PP-001 --repo ./my-model
   modelops proposal-validate PP-001 --repo ./my-model
   ```

### Creating a ChangeRequest

```bash
modelops cr-create \
  --id CR-001 \
  --title "Update Customer Group descriptions" \
  --reason "Business terminology changed in Q1" \
  --affected-objects ATTR-CUST-SALES-CUSTOMER-GROUP \
  --repo ./my-model
```

### Approval and Apply

```bash
# Approve
modelops cr-approve CR-001 --repo ./my-model

# Apply (dry-run first)
modelops proposal-apply PP-001 --dry-run --repo ./my-model
modelops proposal-apply PP-001 --repo ./my-model
```

---

## Scorecards and Readiness Reviews

### Scorecard

```bash
modelops scorecard --repo ./my-model
```

Outputs readiness metrics:
- Documentation coverage
- Ownership coverage
- Validation status
- Data quality rule coverage

### Readiness Review Checklist

Before declaring a model "production ready":

- [ ] All objects pass Layer 1 validation
- [ ] No broken references (Layer 2)
- [ ] SAP context rules satisfied (Layer 3)
- [ ] >90% ownership coverage
- [ ] All active attributes have entity_context
- [ ] All FieldEndpoints have enrichment (value_list, mapping, or validation_rule)
- [ ] ChangeRequest process documented for the team
- [ ] Audit events are being emitted
- [ ] Index builds successfully
- [ ] Review workbook exported and signed off

---

## Excel / Sheets / GitHub Collaboration Patterns

### Excel Review Cycle

1. Export model to Excel
   ```bash
   modelops export-model --format xlsx --business-review --repo ./my-model
   ```
2. Share workbook with business owners
3. Collect comments in Excel
4. Convert feedback to PatchProposals or direct edits
5. Validate and rebuild index

### Google Sheets Sync

```bash
# Export to Google Sheets
modelops export-sheets --repo ./my-model

# Import changes back
modelops import-sheet --from ./updated_sheet.xlsx --repo ./my-model
```

### GitHub PR Review

1. Create a branch for model changes
2. Edit canonical files
3. Run `modelops validate` and `modelops build-index`
4. Open a PR
5. Reviewers use `modelops trace` and `modelops impact` to assess changes
6. Merge after approval

---

## AI-Assisted Modeling Rules

### What AI Can Do

- Generate draft PatchProposals from free-text notes
- Suggest attribute definitions from dataset profiles
- Identify gaps between dataset columns and existing model

### What AI Cannot Do

- Approve changes (human review required)
- Directly edit canonical files (proposals only)
- Guarantee correctness (assumptions must be verified)

### Safe AI Workflow

1. Human writes a clear, scoped note
2. AI generates a PatchProposal
3. Human reviews operations, assumptions, and human_checks
4. Human runs `proposal-impact` and `proposal-validate`
5. Human creates a ChangeRequest
6. Approver reviews and approves
7. Human applies the proposal

---

## Anti-Patterns

| Anti-Pattern | Why It Hurts | Correct Approach |
|---|---|---|
| Flat model (all objects in one domain) | No organisational structure; impossible to navigate | Create domains by business area |
| Missing `entity_context` on attributes | Cannot trace business meaning to system grain | Always link attributes to entity_context |
| Direct table names as entity names | Business users cannot read the model | Use business language for entities |
| Storing data values in canonical files | Bloats model; privacy risk | Store only definitions and mappings |
| Editing `generated/` files | Lost on next `build-index` | Edit `model/` only |
| Skipping validation before commit | Broken references propagate | Run `modelops validate` before every PR |
| One person proposes and approves | No governance | Separate proposer and approver |
| Ignoring audit events | No traceability for compliance | Review `generated/audit_events.jsonl` regularly |

---

## Quick Start: Minimum Viable Model

For a single migration object, create these files in `model/`:

1. `DOMAIN-*.md` — your domain
2. `ENTITY-*.md` — the business concept
3. `ATTR-*.md` — 3–5 key attributes
4. `FEP-*.md` — source and target field endpoints
5. `MAP-*.md` — at least one source-to-target mapping

Then run:

```bash
modelops validate --repo ./my-model
modelops build-index --repo ./my-model --jsonl
modelops scorecard --repo ./my-model
```

You now have a searchable, valid, scorecarded model.

