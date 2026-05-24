# Martenweave Canonical Model Contract

Version: 0.1  
Status: Draft  
Scope: Generic data model registry objects and conventions

---

## 1. Purpose

This document defines the **canonical model contract** for Martenweave. It explains the core generic objects, how they relate, and how to author them as Markdown + YAML frontmatter files.

You do not need SAP knowledge to understand or use the core contract. SAP-specific concepts (tables, fields, contexts) are treated as an optional **domain pack** layered on top of the generic model.

---

## 2. File format

Every canonical object is stored as a small file:

- **`.md`** — Markdown with YAML frontmatter between `---` delimiters
- **`.yaml`** or **`.yml`** — YAML-only file

Frontmatter contains the machine-readable identity and relationships. Markdown body contains the human-readable definition.

```markdown
---
id: DOMAIN-CUSTOMER-BP
type: MasterDataDomain
status: active
name: Business Partner / Customer
---

# Business Partner / Customer Domain

The Business Partner domain covers the unified partner model.
```

---

## 3. Core generic objects

### 3.1 Scope objects

| Type | Purpose | Example ID |
|---|---|---|
| `MasterDataDomain` | Top-level grouping for a data area | `DOMAIN-CUSTOMER-BP` |
| `MigrationObject` | Migration or transformation scope | `MIGOBJ-CUSTOMER-BP` |
| `BusinessEntity` | Conceptual business object | `ENTITY-CUSTOMER-SALES-AREA` |
| `EntityContext` | System or business grain | `CTX-CUSTOMER-SALES-AREA-S4` |

### 3.2 Semantic objects

| Type | Purpose | Example ID |
|---|---|---|
| `Attribute` | Business meaning (semantic object) | `ATTR-CUST-SALES-CUSTOMER-GROUP` |
| `AttributeUsage` | How an Attribute behaves in a specific context | `USE-CUST-SALES-CUSTOMER-GROUP-S4` |
| `BusinessRule` | Expected business behavior | `BR-CUST-GROUP-REQUIRED` |

### 3.3 Physical representation objects

| Type | Purpose | Example ID |
|---|---|---|
| `System` | Logical source, target, or staging system | `SYS-S4HANA` |
| `SystemEnvironment` | Environment or client of a System | `SYSENV-S4-PROD` |
| `FieldEndpoint` | Physical representation (table, field, file column) | `FEP-S4-KNVV-KDGRP` |
| `Interface` | Data movement interface | `IF-CUST-BP-CDC` |
| `Dataset` | Profiled data source | `DS-CUST-SALES-AREA-CSV` |

### 3.4 Movement and transformation objects

| Type | Purpose | Example ID |
|---|---|---|
| `MappingSet` | Group of related Mappings | `MAPSET-CUSTOMER-BP` |
| `Mapping` | Link from source to target FieldEndpoint | `MAP-CUST-GROUP-LEGACY-TO-KNVV` |
| `ValueList` | Allowed or reference values | `VLIST-S4-CUST-GROUP` |
| `ValueMapping` | Source-to-target value mapping | `VMAP-CUST-GROUP-LEGACY-TO-S4` |
| `TransformationLogic` | Derivation, defaulting, or enrichment | `XFORM-CUST-GROUP-NORMALIZE` |

### 3.5 Quality and validation objects

| Type | Purpose | Example ID |
|---|---|---|
| `ValidationRule` | How to check correctness | `VAL-CUST-GROUP-ALLOWED-VALUES` |
| `DataQualityCheck` | Executed or described quality check | `DQC-CUST-GROUP-COMPLETENESS` |

### 3.6 Governance and history objects

| Type | Purpose | Example ID |
|---|---|---|
| `OwnershipRole` | Accountability for an object | `OWN-CUST-GROUP-STEWARD` |
| `Person` | Individual stakeholder | `PERSON-ALICE-SMITH` |
| `Team` | Team or group owner | `TEAM-CUSTOMER-MASTER-DATA` |
| `Issue` | Problem or gap | `ISS-CH01-A17-CONFIG-GAP` |
| `Risk` | Known risk | `RISK-CUST-GROUP-MISSING-LOV` |
| `Decision` | Accepted reasoning | `DEC-CH01-A17-CUSTOMER-GROUP` |
| `ChangeRequest` | Approved model change | `CR-001` |
| `PatchProposal` | Proposed model update (pre-approval) | `PP-001` |
| `Evidence` | Supporting evidence | `EVID-MEETING-NOTES-2026-05-20` |

---

## 4. ID conventions

All canonical object IDs must match:

```regex
^[A-Z][A-Z0-9]*(-[A-Z0-9]+)*$
```

Rules:
- Start with an uppercase letter.
- Use only uppercase letters, digits, and hyphens.
- No consecutive hyphens.
- Must be globally unique within a repository.
- Must be stable: once assigned, do not change.

Examples:
- `DOMAIN-CUSTOMER-BP`
- `ATTR-CUST-SALES-CUSTOMER-GROUP`
- `FEP-S4-KNVV-KDGRP`

---

## 5. Minimal frontmatter examples

### Domain

```yaml
---
id: DOMAIN-CUSTOMER-BP
type: MasterDataDomain
status: active
name: Business Partner / Customer
description: Master data domain for Business Partner and Customer.
---
```

### Entity

```yaml
---
id: ENTITY-CUSTOMER-SALES-AREA
type: BusinessEntity
status: active
name: Customer Sales Area
domain: DOMAIN-CUSTOMER-BP
entity_context: CTX-CUSTOMER-SALES-AREA-S4
description: Sales-area-dependent customer data.
---
```

### Attribute

```yaml
---
id: ATTR-CUST-SALES-CUSTOMER-GROUP
type: Attribute
status: active
name: Customer Group
domain: DOMAIN-CUSTOMER-BP
semantic_category: sales
data_classification: internal
default_context: CTX-CUSTOMER-SALES-AREA-S4
description: Business attribute representing the Customer Group.
---
```

### FieldEndpoint (generic)

```yaml
---
id: FEP-S4-KNVV-KDGRP
type: FieldEndpoint
status: active
name: KNVV Customer Group
domain: DOMAIN-CUSTOMER-BP
system: SYS-S4HANA
endpoint_type: sap_table_field
entity_context: CTX-CUSTOMER-SALES-AREA-S4
business_attribute: ATTR-CUST-SALES-CUSTOMER-GROUP
description: S/4HANA target field for Customer Group.
---
```

> **Domain-pack note:** `sap_table` and `sap_field` are optional domain-pack fields used by the SAP context validator. They are not required for generic data models.

### Mapping

```yaml
---
id: MAP-CUST-GROUP-LEGACY-TO-KNVV-KDGRP
type: Mapping
status: draft
name: Legacy Customer Group to KNVV-KDGRP
domain: DOMAIN-CUSTOMER-BP
source_endpoint: FEP-LEGACY-CUST-GROUP
target_endpoint: FEP-S4-KNVV-KDGRP
mapping_set: MAPSET-CUSTOMER-BP
description: Maps legacy CRM customer group to S/4HANA target field.
---
```

### ValueList

```yaml
---
id: VLIST-S4-CUST-GROUP
type: ValueList
status: active
name: S/4HANA Customer Group Values
domain: DOMAIN-CUSTOMER-BP
description: Allowed customer group values in S/4HANA.
---
```

### ValidationRule

```yaml
---
id: VAL-CUST-GROUP-ALLOWED-VALUES
type: ValidationRule
status: active
name: Customer Group Allowed Values
domain: DOMAIN-CUSTOMER-BP
attribute: ATTR-CUST-SALES-CUSTOMER-GROUP
description: Customer Group must be in the allowed value list.
---
```

### Issue

```yaml
---
id: ISS-CH01-A17-CONFIG-GAP
type: Issue
status: open
name: Customer Group config gap for CH01/A17
domain: DOMAIN-CUSTOMER-BP
related_objects:
  - ATTR-CUST-SALES-CUSTOMER-GROUP
  - VAL-CUST-GROUP-ALLOWED-VALUES
description: Missing validation rule for CH01 / A17 sales area.
---
```

### PatchProposal

```yaml
---
id: PP-001
type: PatchProposal
status: pending_review
name: Add CH01/A17 customer group rule
domain: DOMAIN-CUSTOMER-BP
affected_objects:
  - ATTR-CUST-SALES-CUSTOMER-GROUP
  - VAL-CUST-GROUP-ALLOWED-VALUES
description: Proposes adding a conditional validation rule.
---
```

---

## 6. Generic vs domain-pack fields

Core fields (required or recommended for all models):
- `id`, `type`, `status`, `name`, `description`, `domain`
- `entity`, `entity_context`, `attribute`, `system`
- `source_endpoint`, `target_endpoint`, `mapping_set`
- `value_list`, `value_mapping`
- `related_objects`, `affected_objects`, `evidence`

SAP domain-pack fields (optional, validated only when present):
- `sap_table`, `sap_field`, `sap_object`
- `context_category` with SAP-specific values (`customer_sales_area`, `customer_company_code`, etc.)

Future domain packs (analytics, finance, CRM, etc.) can add their own optional fields and validation rules without changing core concepts.

---

## 7. Validation alignment

The canonical model contract aligns with the object type registry in `src/modelops_core/schemas/registry.py`. Each `ObjectTypeEntry` defines:

- `type_id` — canonical type name
- `reference_fields` — which frontmatter fields are references to other objects
- `search_fields` — which fields are indexed for search
- `sap_context_rules` — optional SAP-specific rules (only `FieldEndpoint` currently)

When you add a new canonical object, the validator checks:
1. `id` format and uniqueness
2. `type` is a registered `ObjectType`
3. `status` is present and non-empty
4. All reference fields point to existing objects
5. SAP context rules pass (if applicable)

---

## 8. Relationship summary

```text
MasterDataDomain
  → MigrationObject
  → BusinessEntity
    → EntityContext
      → AttributeUsage
        → Attribute
          → FieldEndpoint (physical representation)
          → Mapping (source → target)
          → ValueList / ValueMapping
          → ValidationRule
          → Issue / Decision / ChangeRequest
```

---

## 9. Status values

Generic lifecycle statuses:
- `draft`
- `active`
- `deprecated`
- `archived`

Issue-specific statuses:
- `open`, `in_progress`, `resolved`, `closed`

PatchProposal statuses:
- `pending_review`, `accepted`, `rejected`

ChangeRequest statuses:
- `pending`, `approved`, `rejected`, `implemented`

---

## 10. Related documents

- `docs/architecture/DOMAIN_MODEL.md` — full conceptual domain model
- `docs/architecture/SYSTEM_ARCHITECTURE.md` — system architecture
- `src/modelops_core/schemas/common.py` — base Pydantic schemas
- `src/modelops_core/schemas/registry.py` — object type registry and reference fields
