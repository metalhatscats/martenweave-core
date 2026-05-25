# Martenweave — Bulk Refactor Operations

Version: `0.1-draft`  
Document type: Architecture / workflow design  
Scope: Safe bulk cleanup operations for large model repositories  
Depends on: `docs/integration-architecture.md`, `docs/AI_PATCH_WORKFLOW.md`  
Status: Draft for implementation

---

## 1. Purpose

This document defines **bulk refactor operations** for Martenweave. Large model repositories accumulate technical debt over time: inconsistent naming, outdated owners, redundant attributes, and stale mappings. Bulk refactor operations provide a safe, proposal-first way to clean up models at scale without direct mass mutation of canonical files.

Every bulk operation generates a **PatchProposal** with impact analysis and dry-run output. Canonical files change only after human review and approval.

---

## 2. Design principles

### 2.1 Proposal-first for all bulk changes

```text
User selects bulk operation + parameters
      │
      ▼
Dry-run preview (no file changes)
      │
      ▼
Generate PatchProposal with all affected objects
      │
      ▼
Impact analysis + validation
      │
      ▼
Human review and approval
      │
      ▼
Apply as ChangeRequest → canonical file update
```

### 2.2 Dry-run by default

- Every bulk command shows a preview before generating a proposal.
- The `--dry-run` flag is implicit; `--apply` is required to generate a real proposal.

### 2.3 Conflict detection

- If an affected object has an open PatchProposal or ChangeRequest, the operation warns.
- If two bulk operations target the same objects, the second must wait for the first to resolve.

### 2.4 Idempotency

- Running the same bulk operation twice with the same parameters should produce the same PatchProposal (or a no-op if already applied).

---

## 3. Supported operations

### 3.1 Rename object

Change the `id`, `name`, or `title` of a canonical object and update all references.

**Parameters:**

| Parameter | Description |
|---|---|
| `old_id` | Current object ID |
| `new_id` | New object ID (must pass ID format validation) |
| `update_references` | Update all objects that reference `old_id` |

**Scope:**

- Updates the object's own file name and frontmatter.
- Updates `domain`, `entity`, `attribute`, `mapping`, `parent`, `related` fields in other objects.
- Updates `source_file` references in the index.

**Risk:** High. Requires approval gate if >10 references affected.

### 3.2 Move object

Change the `domain` or `entity_context` of an object, moving it to a different business scope.

**Parameters:**

| Parameter | Description |
|---|---|
| `object_id` | Object to move |
| `target_domain` | New domain ID |
| `target_entity` | New entity ID (optional) |

**Scope:**

- Updates the object's `domain` and `entity_context` fields.
- Updates related mappings and attribute usages.

**Risk:** Medium. Impact analysis required.

### 3.3 Split attribute

Divide one attribute into multiple attributes, preserving mappings.

**Parameters:**

| Parameter | Description |
|---|---|
| `source_attr_id` | Attribute to split |
| `new_attrs` | List of new attribute definitions |
| `mapping_strategy` | How to redistribute mappings |

**Scope:**

- Creates new attribute objects.
- Updates or duplicates existing mappings.
- Marks original attribute as deprecated or deletes it.

**Risk:** High. Requires approval gate.

### 3.4 Merge attributes

Combine multiple attributes into one, consolidating mappings.

**Parameters:**

| Parameter | Description |
|---|---|
| `source_attr_ids` | List of attributes to merge |
| `target_attr_id` | New or existing target attribute |
| `conflict_strategy` | How to handle differing descriptions, domains, etc. |

**Scope:**

- Creates or updates the target attribute.
- Redirects all mappings to the target.
- Deprecates or deletes source attributes.

**Risk:** High. Requires approval gate.

### 3.5 Change owner

Update the `owner` field across multiple objects.

**Parameters:**

| Parameter | Description |
|---|---|
| `old_owner` | Current owner identifier |
| `new_owner` | New owner identifier |
| `filter_type` | Limit to specific object types |
| `filter_domain` | Limit to specific domain |

**Scope:**

- Updates `owner` field in matching objects.

**Risk:** Low. No reference changes.

### 3.6 Attach value list

Link a `ValueList` to one or more attributes or field endpoints.

**Parameters:**

| Parameter | Description |
|---|---|
| `value_list_id` | ValueList to attach |
| `target_ids` | Attributes or FieldEndpoints to link |

**Scope:**

- Updates `value_list` or `allowed_values` field in targets.

**Risk:** Low.

### 3.7 Replace mapping target

Change the target of one or more mappings.

**Parameters:**

| Parameter | Description |
|---|---|
| `old_target_id` | Current target FieldEndpoint or Attribute |
| `new_target_id` | New target |
| `filter_source` | Limit to mappings from a specific source |

**Scope:**

- Updates `target` field in matching `Mapping` objects.

**Risk:** Medium.

### 3.8 Deprecate field

Mark a field endpoint or attribute as deprecated with a migration note.

**Parameters:**

| Parameter | Description |
|---|---|
| `object_id` | Object to deprecate |
| `replacement_id` | Recommended replacement (optional) |
| `deprecation_reason` | Why it is deprecated |
| `effective_date` | When deprecation takes effect |

**Scope:**

- Updates `status` to `deprecated`.
- Adds `deprecation` metadata block.
- Creates an `Issue` or `Decision` record.

**Risk:** Medium.

### 3.9 Normalize relationship type

Standardize relationship type references across the model.

**Parameters:**

| Parameter | Description |
|---|---|
| `old_type` | Current relationship type string |
| `new_type` | Standardized relationship type string |

**Scope:**

- Updates `relationship_type` in all matching objects.

**Risk:** Low.

---

## 4. Operation risk levels

| Operation | Default Risk | Approval Required If |
|---|---|---|
| Rename object | High | >5 references affected |
| Move object | Medium | Any mappings affected |
| Split attribute | High | Always |
| Merge attributes | High | Always |
| Change owner | Low | >20 objects affected |
| Attach value list | Low | Always (explicit action) |
| Replace mapping target | Medium | >3 mappings affected |
| Deprecate field | Medium | Any downstream consumers |
| Normalize relationship type | Low | >10 objects affected |

---

## 5. CLI design (future)

### 5.1 Generic bulk command

```bash
modelops bulk <operation> --repo ./my-model [parameters]
```

Examples:

```bash
# Rename an object
modelops bulk rename \
  --old-id ATTR-CUST-SALES-CUSTOMER-GROUP \
  --new-id ATTR-CUST-SALES-CUST-GROUP \
  --repo ./my-model

# Change owner for all attributes in a domain
modelops bulk change-owner \
  --old-owner "legacy_team" \
  --new-owner "customer_data_team" \
  --filter-type Attribute \
  --filter-domain DOMAIN-CUSTOMER-BP \
  --repo ./my-model

# Deprecate a field
modelops bulk deprecate \
  --object-id FEP-S4-KNVV-KDGRP-OLD \
  --replacement-id FEP-S4-KNVV-KDGRP \
  --reason "Replaced by consolidated field" \
  --repo ./my-model
```

### 5.2 Dry-run output

```text
$ modelops bulk rename --old-id ATTR-OLD --new-id ATTR-NEW --repo ./my-model

Dry-run preview:
  Objects to modify: 1
  References to update: 7
  New files: 1
  Files to delete: 1

Affected objects:
  - ATTR-OLD → ATTR-NEW (rename)
  - MAP-1 (update target reference)
  - FEP-S4-... (update attribute reference)
  ...

Impact analysis:
  - 3 mappings affected
  - 2 validation rules reference this attribute
  - 1 open Issue linked to ATTR-OLD

Run with --apply to generate a PatchProposal.
```

### 5.3 Apply flow

```bash
modelops bulk rename --old-id ATTR-OLD --new-id ATTR-NEW --repo ./my-model --apply
```

**Behavior:**

1. Generate PatchProposal `PROP-BULK-RENAME-20260525-001`.
2. Run validation on the proposal.
3. Run impact analysis.
4. Store the proposal in `model/`.
5. Print proposal ID and next steps.

---

## 6. Validation and conflict checks

### 6.1 Pre-operation checks

- **ID format**: New IDs must match `^[A-Z][A-Z0-9]*(-[A-Z0-9]+)*$`.
- **Duplicate prevention**: New IDs must not already exist.
- **Reference integrity**: All referenced objects must exist (or be created in the same proposal).
- **Open proposals**: Warn if any affected object has an open PatchProposal.

### 6.2 Post-operation validation

- Run full Layer 1–3 validation on the proposed state.
- Report any broken references introduced by the operation.
- Report any SAP context rule violations.

### 6.3 Conflict matrix

| Conflict | Detection | Resolution |
|---|---|---|
| Two bulk ops target same object | Check open proposals | Block second operation |
| Bulk op vs. manual edit | Check file modification times | Warn and require --force |
| Bulk op vs. import proposal | Check proposal overlap | Merge or block |

---

## 7. Examples

### 7.1 Simple model cleanup

A small team wants to standardize attribute naming:

```bash
# Preview
modelops bulk rename --old-id ATTR-CUST-GROUP --new-id ATTR-CUSTOMER-GROUP --repo ./my-model

# Apply
modelops bulk rename --old-id ATTR-CUST-GROUP --new-id ATTR-CUSTOMER-GROUP --repo ./my-model --apply

# Review and approve
modelops validate --repo ./my-model
modelops impact ATTR-CUSTOMER-GROUP --repo ./my-model
```

### 7.2 Enterprise Business Partner cleanup

A large SAP migration project needs to restructure 200+ attributes:

```bash
# Step 1: Change all legacy owners
modelops bulk change-owner \
  --old-owner "legacy_sap_team" \
  --new-owner "bp_migration_team" \
  --repo ./my-model \
  --apply

# Step 2: Deprecate old field endpoints
modelops bulk deprecate \
  --object-id FEP-ECC-KNA1-KDGRP \
  --replacement-id FEP-S4-KNVV-KDGRP \
  --reason "ECC decommissioned" \
  --repo ./my-model \
  --apply

# Step 3: Review all generated proposals
modelops proposals list --repo ./my-model
```

---

## 8. Related issues

| Issue | Description | Status |
|---|---|---|
| #46 | Integration architecture | Completed |
| #52 | GitHub-ready change bundles | Completed |
| #55 | Connector adapter interface | Completed |
| #71 | Portable model package | Design doc |
| #72 | Source refresh and stale detection | Design doc |
| #74 | This document | Design doc |

---

## 9. Validation

```bash
pytest && ruff check .
```
