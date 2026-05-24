# Martenweave Relationship Taxonomy

Version: 0.1  
Status: Draft  
Scope: Controlled vocabulary for model trace, lineage, impact, and governance

---

## 1. Principle

Every reference between canonical objects has a **semantic relationship type** and a **traversal class**. This makes trace, impact, and lineage reports consistent and filterable.

> **Relationship type** = what the edge means (e.g., `belongs_to_domain`).  
> **Traversal class** = how agents should treat the edge during traversal (e.g., `core_dependency`, `governance`).

---

## 2. Relationship types by category

### 2.1 Scope and hierarchy

| Relationship type | Source type | Target type | Direction | Meaning |
|---|---|---|---|---|
| `belongs_to_domain` | Any | MasterDataDomain | → | Object is part of this domain. |
| `part_of_migration` | Any | MigrationObject | → | Object is in this migration scope. |
| `belongs_to_entity` | Attribute, FieldEndpoint | BusinessEntity | → | Object belongs to this business entity. |
| `part_of_entity` | BusinessEntity | BusinessEntity | → | Child entity is part of parent entity. |
| `used_in_context` | Attribute, FieldEndpoint, AttributeUsage | EntityContext | → | Object is used in this system/business context. |
| `located_in_system` | FieldEndpoint, Interface, Dataset | System | → | Object is located in this system. |

### 2.2 Semantic and physical

| Relationship type | Source type | Target type | Direction | Meaning |
|---|---|---|---|---|
| `has_attribute` | BusinessEntity | Attribute | → | Entity has this attribute. |
| `represents_attribute` | FieldEndpoint | Attribute | → | Field endpoint represents this business attribute. |
| `implemented_by_field` | AttributeUsage | FieldEndpoint | → | Usage is implemented by this physical field. |

### 2.3 Mapping and transformation

| Relationship type | Source type | Target type | Direction | Meaning |
|---|---|---|---|---|
| `mapped_from` | Mapping | FieldEndpoint | → | Mapping starts from this source endpoint. |
| `mapped_to` | Mapping | FieldEndpoint | → | Mapping ends at this target endpoint. |
| `uses_mapping` | Attribute, FieldEndpoint | Mapping | → | Object uses this mapping. |
| `part_of_mapping_set` | Mapping | MappingSet | → | Mapping belongs to this set. |
| `uses_value_mapping` | Mapping | ValueMapping | → | Mapping uses this value mapping. |
| `maps_from_values` | ValueMapping | ValueList | → | Value mapping translates from this value list. |
| `maps_to_values` | ValueMapping | ValueList | → | Value mapping translates to this value list. |

### 2.4 Validation and quality

| Relationship type | Source type | Target type | Direction | Meaning |
|---|---|---|---|---|
| `validated_by` | Attribute, FieldEndpoint | ValidationRule | → | Object is validated by this rule. |
| `has_allowed_values` | Attribute, FieldEndpoint | ValueList | → | Object has this list of allowed values. |

### 2.5 Governance and ownership

| Relationship type | Source type | Target type | Direction | Meaning |
|---|---|---|---|---|
| `owned_by_business` | Any | Person | → | Business owner. |
| `owned_by_technical` | Any | Person | → | Technical owner. |
| `stewarded_by` | Any | Person | → | Data steward. |
| `approved_by` | Any | Person | → | Approver. |
| `accountable_to` | Any | Team | → | Accountable team. |
| `affected_by_issue` | Any | Issue | → | Object is affected by this issue. |
| `explained_by_decision` | Any | Decision | → | Object is explained by this decision. |
| `supported_by_evidence` | Any | Evidence | → | Object is supported by this evidence. |
| `affects` | ChangeRequest, PatchProposal | Any | → | Request/proposal affects these objects. |
| `proposed_by` | Any | PatchProposal | → | Object was proposed by this patch proposal. |
| `related_to` | Any | Any | → | Generic related object reference. |

---

## 3. Traversal classes

| Class | Description | Traversal default |
|---|---|---|
| `core_dependency` | Primary model structure (domain, entity, attribute, field). | **Include** |
| `context` | System, environment, or grain context. | **Include** |
| `mapping` | Data movement, transformation, value mapping. | **Include** |
| `validation` | Rules, value lists, quality checks. | **Include** |
| `governance` | Ownership, issues, decisions, approvals. | **Optional** — may create noise in deep traversal. |
| `evidence` | Supporting evidence and documentation. | **Optional** |
| `reference` | Generic or weak references. | **Optional** |

---

## 4. Directionality

All relationships are stored as **directed edges** from the source object (the one that declares the reference in its frontmatter) to the target object.

For bidirectional concepts, agents should infer the reverse direction when useful:

| Forward edge | Inferred reverse |
|---|---|
| Attribute → `belongs_to_entity` → BusinessEntity | BusinessEntity → `has_attribute` → Attribute |
| FieldEndpoint → `represents_attribute` → Attribute | Attribute → `implemented_by_field` → FieldEndpoint |
| Mapping → `mapped_to` → FieldEndpoint | FieldEndpoint → `mapped_from` → Mapping |

---

## 5. Validation

The validation pipeline checks:
- `REFERENCE_BROKEN` — target object does not exist.
- `REFERENCE_TYPE_MISMATCH` — target object type does not match `expected_target_type`.

Relationship types themselves are not validated independently; they are derived from the registered reference fields in `schemas/registry.py`.

---

## 6. Examples

### Simple Product table

```
ATTR-PRODUCT-NAME  --belongs_to_entity-->  ENTITY-PRODUCT
ATTR-PRODUCT-NAME  --belongs_to_domain-->  DOMAIN-PRODUCT
FEP-PRODUCT-NAME   --represents_attribute-->  ATTR-PRODUCT-NAME
FEP-PRODUCT-NAME   --belongs_to_domain-->  DOMAIN-PRODUCT
```

### Enterprise BP/Customer Sales Area

```
ATTR-CUST-SALES-CUSTOMER-GROUP  --belongs_to_entity-->  ENTITY-CUSTOMER-SALES-AREA
ATTR-CUST-SALES-CUSTOMER-GROUP  --used_in_context-->  CTX-CUSTOMER-SALES-AREA-S4
FEP-S4-KNVV-KDGRP               --represents_attribute-->  ATTR-CUST-SALES-CUSTOMER-GROUP
FEP-S4-KNVV-KDGRP               --used_in_context-->  CTX-CUSTOMER-SALES-AREA-S4
MAP-CUST-GROUP-LEGACY-TO-KNVV   --mapped_from-->  FEP-LEGACY-CUST-GROUP
MAP-CUST-GROUP-LEGACY-TO-KNVV   --mapped_to-->  FEP-S4-KNVV-KDGRP
```
