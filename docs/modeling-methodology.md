# Martenweave Modeling Methodology

Version: 0.1  
Status: Draft  
Scope: How to model data in Martenweave, from simple files to large enterprise objects

---

## 1. Core principle: meaning is separate from fields

A Martenweave model is **not** a list of columns or tables. The primary rule is:

> **Business meaning (`Attribute`) is separate from physical representation (`FieldEndpoint`).**

This separation is what makes the model traceable, portable, and understandable by non-technical users. A single `Attribute` (e.g., "Customer Group") can have many `FieldEndpoint`s (e.g., `KNVV.KDGRP` in SAP S/4, a column in a legacy CSV, a field in a CRM API). The `Attribute` carries the business definition; each `FieldEndpoint` carries the system-specific implementation.

**Anti-pattern:** Creating one object per table column with no semantic layer. This produces a flat, untraceable field catalog that breaks as soon as the underlying system changes.

---

## 2. Modeling layers

Martenweave supports a full hierarchy. Use as many layers as the complexity of your data demands.

```
Domain (MasterDataDomain)
  └── Model / Subject Area (MigrationObject)
        └── BusinessObject (BusinessEntity)
              └── Perspective / Context (EntityContext)
                    └── Entity (BusinessEntity, nested)
                          └── AttributeUsage
                                └── Attribute
                                      └── FieldEndpoint
                                            └── Mapping
                                            └── ValidationRule
                                            └── ValueList
```

### Layer reference

| Layer | Object type | When to use |
|---|---|---|
| **Domain** | `MasterDataDomain` | Top-level grouping for a business data area. Always create at least one. |
| **Model / Subject Area** | `MigrationObject` | Migration or transformation scope that cuts across systems. Optional for simple models. |
| **Business Object** | `BusinessEntity` | Large conceptual object made of multiple perspectives (e.g., Business Partner, Product). |
| **Perspective / Context** | `EntityContext` | System-specific grain or view of a Business Object (e.g., S/4 sales area, company code). |
| **Entity** | `BusinessEntity` (nested) | Sub-entity within a perspective when further decomposition is needed. Often skipped. |
| **AttributeUsage** | `AttributeUsage` | How an `Attribute` behaves in a specific `EntityContext`. Links semantic to physical. |
| **Attribute** | `Attribute` | The business meaning. Reusable across contexts. |
| **FieldEndpoint** | `FieldEndpoint` | Physical column, table field, file column, or API property. |
| **Mapping** | `Mapping` | Source-to-target relationship between `FieldEndpoint`s. |
| **Rule / LoV** | `ValidationRule`, `ValueList` | Allowed values, constraints, quality checks. |
| **Governance** | `OwnershipRole`, `Issue`, `Decision`, `ChangeRequest`, `Evidence` | Accountability, gaps, rationale, and controlled change. |

---

## 3. Simple mode: collapsed layers

For a single CSV, JSON file, or simple database table, the full hierarchy is overkill. In **simple mode**, collapse layers aggressively:

```
Domain (MasterDataDomain)
  └── Dataset (Dataset)
        └── Entity (BusinessEntity)
              └── Attribute
                    └── FieldEndpoint
```

### Collapsing rules

| Full layer | Simple mode replacement | Rule |
|---|---|---|
| `MigrationObject` | Skip | Not needed if there is no migration scope. |
| `BusinessObject` | `BusinessEntity` at top | The entity itself is the object. |
| `EntityContext` | Skip | Implicit: the dataset/file is the only context. |
| `AttributeUsage` | Skip | Direct `Attribute` → `FieldEndpoint` link. |
| `Mapping` | Skip | No source-to-target movement to model. |
| `ValueList` | Optional | Add only if the column has a closed set of values. |
| `ValidationRule` | Optional | Add only if there is a known constraint. |

A simple model still validates and indexes correctly. The validation pipeline treats missing optional references as acceptable, not errors.

---

## 4. Practical example: simple Product table

A `products.csv` with columns `product_id`, `name`, `category`, `unit_price`, `active`.

### Canonical files

```yaml
# model/DOMAIN-PRODUCT.md
---
id: DOMAIN-PRODUCT
type: MasterDataDomain
status: active
name: Product Domain
---

# Product Domain

Covers product catalog data.
```

```yaml
# model/ENTITY-PRODUCT.md
---
id: ENTITY-PRODUCT
type: BusinessEntity
status: active
name: Product
domain: DOMAIN-PRODUCT
---

# Product

A product in the catalog.
```

```yaml
# model/ATTR-PRODUCT-NAME.md
---
id: ATTR-PRODUCT-NAME
type: Attribute
status: active
name: Product Name
domain: DOMAIN-PRODUCT
---

# Product Name

Human-readable product name.
```

```yaml
# model/FEP-PRODUCT-NAME.md
---
id: FEP-PRODUCT-NAME
type: FieldEndpoint
status: active
name: name
domain: DOMAIN-PRODUCT
attribute: ATTR-PRODUCT-NAME
endpoint_type: file_column
dataset: DS-PRODUCT-CSV
---

# name column

Source: products.csv
```

Repeat for `category`, `unit_price`, and `active`. Add a `Dataset` object `DS-PRODUCT-CSV` and a `ValueList` for `category` if the set is closed.

---

## 5. Practical example: Business Partner / Customer Sales Area

This is the enterprise mode used in `examples/customer_bp_model`. It demonstrates full layer usage.

### Hierarchy

```
DOMAIN-CUSTOMER-BP
  └── MIGOBJ-CUSTOMER-BP
        └── ENTITY-CUSTOMER-SALES-AREA (BusinessEntity)
              └── CTX-CUSTOMER-SALES-AREA-S4 (EntityContext)
                    └── USE-CUST-SALES-CUSTOMER-GROUP-S4 (AttributeUsage)
                          └── ATTR-CUST-SALES-CUSTOMER-GROUP (Attribute)
                                └── FEP-S4-KNVV-KDGRP (FieldEndpoint)
                                      └── MAP-CUST-GROUP-LEGACY-TO-KNVV-KDGRP (Mapping)
                                      └── VLIST-S4-CUST-GROUP (ValueList)
                                      └── VAL-CUST-GROUP-ALLOWED-VALUES (ValidationRule)
```

### Why the full stack matters here

1. `Attribute` (`ATTR-CUST-SALES-CUSTOMER-GROUP`) defines **what** Customer Group means in business terms.
2. `EntityContext` (`CTX-CUSTOMER-SALES-AREA-S4`) defines **where** it lives: SAP S/4, table `KNVV`, grain `KUNNR+VKORG+VTWEG+SPART`.
3. `AttributeUsage` (`USE-CUST-SALES-CUSTOMER-GROUP-S4`) defines **how** it behaves in that context: required, single-value, etc.
4. `FieldEndpoint` (`FEP-S4-KNVV-KDGRP`) is the **physical** field.
5. `Mapping`, `ValueList`, and `ValidationRule` define movement, allowed values, and constraints.

If the SAP table changes or a new target system is added, the `Attribute` stays stable. Only the `FieldEndpoint`, `EntityContext`, and `AttributeUsage` need new objects.

---

## 6. Choosing simple vs enterprise mode

| Criterion | Simple mode | Enterprise mode |
|---|---|---|
| Source is a single file or table | ✅ | |
| No migration or transformation scope | ✅ | |
| One system, one context | ✅ | |
| Object has >1 perspective or context | | ✅ |
| Source-to-target mapping exists | | ✅ |
| Governance, ownership, or approval required | | ✅ |
| Same business concept in multiple systems | | ✅ |
| Value lists, validation rules, or quality checks | Optional | ✅ |

---

## 7. Agent modeling rules

1. **Always create a `MasterDataDomain` first.** Every model must have a domain.
2. **Never create `FieldEndpoint` without an `Attribute` unless in simple mode.** Even in simple mode, prefer creating `Attribute` objects.
3. **Prefer `AttributeUsage` over direct `Attribute` → `FieldEndpoint` links** when there are multiple contexts.
4. **Use `EntityContext` for SAP table/field objects.** This enables SAP context validation.
5. **Keep IDs stable.** Use `DOMAIN-`, `ENTITY-`, `ATTR-`, `FEP-`, `MAP-`, `VLIST-`, `VAL-`, `ISS-`, `DEC-`, `CR-`, `PP-` prefixes.
6. **Document assumptions in `Issue` or `Decision` objects.** Do not bury rationale in Markdown body only.
7. **Use `PatchProposal` for AI-generated changes.** Never mutate canonical files directly from chat or file inference.
