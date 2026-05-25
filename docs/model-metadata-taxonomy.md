# Model Metadata Taxonomy

This document defines the metadata taxonomy for Martenweave canonical objects. It is **generic** and applies to any domain pack, not only SAP. Use it to decide which metadata belongs on which object type, to drive validation warnings, scorecards, exports, and future UI panels.

## Design Principles

1. **Metadata follows the object** — business meaning lives on `Attribute`, physical detail lives on `FieldEndpoint`, context linkage lives on `AttributeUsage`.
2. **Optional by default** — all metadata fields are optional unless they are core identity fields (`id`, `type`, `status`).
3. **Validated, not free-form** — fields that drive validation rules (ownership, context, enrichment) should be declared in schemas so the deterministic pipeline can check them.
4. **Generic first, domain-pack second** — this taxonomy is domain-agnostic. SAP-specific fields (`sap_table`, `context_category`) are noted but not required.

---

## Metadata Categories

### 1. Identity & Lifecycle

Every canonical object carries these fields via `BaseObject`:

| Field | Purpose | Example |
|---|---|---|
| `id` | Globally unique stable identifier | `ATTR-CUST-SALES-CUSTOMER-GROUP` |
| `type` | Registered object type | `Attribute` |
| `status` | Lifecycle state | `draft`, `active`, `deprecated` |
| `schema_version` | Schema compatibility marker | `1.0` |
| `name` | Short display name | `Customer Group` |
| `title` | Human-readable title | `Customer Group in Sales Area` |
| `description` | Long-form business explanation | Markdown body |
| `target_release` | Planned release or milestone | `v0.2.0` |
| `roadmap_priority` | Planning priority | `high`, `medium`, `low` |

**Best practice**: Always set `name` or `title`. Validation warns when both are missing.

---

### 2. Domain & Structural

| Field | Typical Object | Purpose |
|---|---|---|
| `domain` | All | Owning `MasterDataDomain` ID |
| `entity` | Attribute, EntityContext, BusinessEntity | Business entity this belongs to |
| `parent_entity` | BusinessEntity | Hierarchical parent entity |
| `entity_context` | Attribute, AttributeUsage, FieldEndpoint | System/business grain context |
| `system` | FieldEndpoint, Interface, Dataset | Physical system |
| `mapping_set` | Mapping | Collection this mapping belongs to |

---

### 3. Physical / Technical

Physical metadata belongs on `FieldEndpoint` and `System` objects, not on business `Attribute` objects.

| Field | Typical Object | Purpose |
|---|---|---|
| `endpoint_type` | FieldEndpoint | `sap_table_field`, `file_column`, `api_field` |
| `technical_name` | FieldEndpoint | System-specific field name |
| `system_type` | System | `erp`, `crm`, `data_warehouse`, `api` |
| `grain` | EntityContext | Row-level grain (e.g. `customer_sales_area`) |

**SAP domain-pack extensions**:
- `sap_table` — SAP table name (e.g. `KNVV`)
- `sap_field` — SAP field name (e.g. `KDGRP`)
- `context_category` — Required context for SAP tables (`customer_sales_area` for `KNVV`, etc.)

---

### 4. Semantic & Business

| Field | Typical Object | Purpose |
|---|---|---|
| `semantic_category` | Attribute | Business category (e.g. `sales`, `finance`) |
| `data_classification` | Attribute | Sensitivity level (e.g. `internal`, `confidential`) |
| `default_context` | Attribute | Default `EntityContext` when none specified |

---

### 5. Governance & Ownership

Ownership fields drive the `OWNERSHIP_MISSING` validation warning on active/draft objects.

| Field | Typical Object | Purpose |
|---|---|---|
| `business_owner` | Attribute, FieldEndpoint, Mapping, ValueList, ValidationRule, Issue, Decision, BusinessEntity, Dataset | Accountable business owner |
| `technical_owner` | Attribute, FieldEndpoint, Mapping, ValueList, ValidationRule | Technical implementation owner |
| `data_steward` | Attribute, FieldEndpoint, Dataset | Data quality steward |
| `accountable_team` | Attribute, FieldEndpoint, Mapping, ValueList, ValidationRule, Dataset | Responsible team |
| `approver` | Attribute, FieldEndpoint, Mapping, ValueList, ValidationRule, Decision, ChangeRequest | Final approver |
| `watchers` | Attribute, FieldEndpoint, Mapping, ValueList, ValidationRule, BusinessEntity, BusinessRule, Dataset | Interested parties |

**Validation rule**: At least one ownership field should be present on active `Attribute`, `FieldEndpoint`, `Dataset`, `Mapping`, `ValidationRule`, `Issue`, `Decision`, `BusinessEntity`, `ValueList`, and `ValueMapping` objects.

---

### 6. Usage & Scope

Usage metadata explains *where* and *how* a field or attribute is used.

| Field | Typical Object | Purpose |
|---|---|---|
| `usage_type` | AttributeUsage | `primary`, `secondary`, `derived`, `reference` |
| `scope` | AttributeUsage | `sales_area`, `company_code`, `global`, `market` |
| `requiredness` | AttributeUsage | `mandatory`, `optional`, `conditional` |
| `business_process` | AttributeUsage | Process that uses this field |
| `use_case` | AttributeUsage | Specific use case |

**Validation rule**: Active/draft `AttributeUsage` objects should have `usage_type`.

---

### 7. Enrichment & Quality

Enrichment metadata links business meaning to physical controls.

| Field | Typical Object | Purpose |
|---|---|---|
| `value_list` | FieldEndpoint, ValidationRule, Mapping | Allowed values |
| `validation_rules` | Attribute | Linked validation rules |
| `rule_type` | ValidationRule | `format`, `range`, `regex`, `custom` |
| `mapping` | Attribute | Linked source-to-target mapping |
| `value_mapping` | Mapping | Value translation table |

**Validation rule**: In mature models (models that already have `ValueList`, `Mapping`, or `ValidationRule` objects), active `FieldEndpoint` objects should have at least one enrichment link (`value_list`, mapping, or validation rule).

---

### 8. Source & Target Lineage

Lineage metadata traces data from origin to consumer.

| Field | Typical Object | Purpose |
|---|---|---|
| `source_endpoint` | Mapping | Source `FieldEndpoint` |
| `target_endpoint` | Mapping | Target `FieldEndpoint` |
| `source_value_list` | Mapping, ValueMapping | Source value list |
| `target_value_list` | Mapping, ValueMapping | Target value list |
| `source_system` | Dataset, FieldEndpoint | Origin system |
| `target_system` | Mapping, Interface | Destination system |
| `downstream_consumers` | FieldEndpoint, Dataset | Known consumers |

---

### 9. Issue & Decision Governance

Issue and Decision objects capture problems and accepted reasoning.

| Field | Typical Object | Purpose |
|---|---|---|
| `issue_type` | Issue | `gap`, `risk`, `question`, `blocker` |
| `severity` | Issue, Risk | `low`, `medium`, `high`, `critical` |
| `priority` | Issue | Processing priority (not yet in schema) |
| `decision_category` | Decision | `architecture`, `data_model`, `process` |
| `affected_objects` | Issue, Risk, Decision, ChangeRequest | Objects impacted |
| `related_issues` | Decision, ChangeRequest | Linked issues |
| `related_decisions` | Decision, ChangeRequest | Linked decisions |
| `evidence` | Decision | Supporting evidence objects |
| `recommended_action` | Issue | Suggested remediation |

---

## Metadata by Object Type

### Attribute
- **Identity**: `id`, `type`, `status`, `name`, `title`, `description`, `schema_version`, `target_release`, `roadmap_priority`
- **Domain**: `domain`, `entity`, `default_context`
- **Semantic**: `semantic_category`, `data_classification`
- **Governance**: `business_owner`, `technical_owner`, `data_steward`, `accountable_team`, `approver`, `watchers`
- **Enrichment**: `validation_rules`, `mapping`, `value_list`

### AttributeUsage
- **Identity**: `id`, `type`, `status`, `name`, `description`
- **Links**: `attribute`, `entity_context`, `field_endpoint`
- **Usage**: `usage_type`, `scope`, `requiredness`

### FieldEndpoint
- **Identity**: `id`, `type`, `status`, `name`, `title`, `description`
- **Physical**: `endpoint_type`, `technical_name`, `system`
- **SAP**: `sap_table`, `sap_field`
- **Context**: `entity_context`, `business_attribute`
- **Governance**: ownership fields, `watchers`
- **Enrichment**: `value_list`, `mapping`, `validation_rules`
- **Lineage**: `source_system`, `downstream_consumers`

### EntityContext
- **Identity**: `id`, `type`, `status`, `name`, `description`
- **Structural**: `domain`, `entity`, `context_category`, `grain`

### Mapping
- **Identity**: `id`, `type`, `status`, `name`, `description`
- **Lineage**: `source_endpoint`, `target_endpoint`, `source_value_list`, `target_value_list`, `value_mapping`
- **Governance**: ownership fields, `watchers`

### ValueList
- **Identity**: `id`, `type`, `status`, `name`, `description`
- **Content**: `value_list_type`, `entries`, `parent_value_list`
- **Governance**: ownership fields, `watchers`

### ValidationRule
- **Identity**: `id`, `type`, `status`, `name`, `description`
- **Links**: `attribute`, `value_list`
- **Rule**: `rule_type`
- **Governance**: `business_owner`, `approver`

### System / Interface
- **Identity**: `id`, `type`, `status`, `name`, `description`
- **Technical**: `system_type`
- **Links**: `domain`, `system` (Interface only)

### Dataset
- **Identity**: `id`, `type`, `status`, `name`, `description`
- **Links**: `domain`, `system`
- **Governance**: ownership fields, `watchers`

### Issue / Risk / Decision
- **Identity**: `id`, `type`, `status`, `name`, `description`
- **Governance**: `severity`, `issue_type` / `risk_category` / `decision_category`, `affected_objects`, ownership fields
- **Links**: `attribute`, `related_issues`, `related_decisions`, `evidence`

### ChangeRequest / PatchProposal
- **Identity**: `id`, `type`, `status`, `name`, `description`
- **Workflow**: `requested_by`, `approval_status`, `implementation_status`, `created_by`, `created_at`, `applied_at`
- **Links**: `affected_objects`, `source_patch_proposals`, `related_issues`, `related_decisions`

---

## Validation-Driven Metadata

The following metadata gaps trigger validation warnings:

| Warning Code | Trigger | Fix |
|---|---|---|
| `DISPLAY_NAME_MISSING` | No `name` or `title` | Add `name` or `title` |
| `OWNERSHIP_MISSING` | Active object lacks ownership | Add `business_owner`, `technical_owner`, `data_steward`, `accountable_team`, or `approver` |
| `ATTRIBUTE_MISSING_CONTEXT` | Active `Attribute` lacks `entity_context` in enterprise models | Add `entity_context` or `default_context` |
| `FIELD_ENDPOINT_MISSING_ATTRIBUTE` | Active `FieldEndpoint` has no `attribute` or `AttributeUsage` | Link to business meaning |
| `FIELD_ENDPOINT_MISSING_ENRICHMENT` | Active `FieldEndpoint` lacks `value_list`, mapping, or validation rule in mature models | Add enrichment |
| `ATTRIBUTE_USAGE_MISSING_TYPE` | Active `AttributeUsage` lacks `usage_type` | Add `usage_type` |
| `LOV_EMPTY` | Active `ValueList` has no `entries` | Add allowed values |
| `VALUE_MAPPING_EMPTY` | Active `ValueMapping` has no `entries` | Add mapping entries |

---

## Simple Table Mode vs Enterprise Mode

### Simple Table Mode
- Small models (< 100 objects) with flat structure.
- Metadata minimum: `id`, `type`, `status`, `name`, `domain`.
- Ownership and enrichment warnings are still emitted but may be deferred.

### Enterprise / System Lineage Mode
- Large models with `EntityContext`, `System`, `Interface` objects.
- Metadata expectation: full taxonomy above.
- `EntityContext` objects group `FieldEndpoint`s by grain.
- `AttributeUsage` objects link `Attribute` → `EntityContext` → `FieldEndpoint`.
- Validation warnings are stricter (context checks, enrichment checks, ownership checks).

---

## Gaps & Future Work

The following fields are used in example canonical files but are **not yet declared in Pydantic schemas**:

- `requiredness` on `AttributeUsage`
- `priority` on `Issue`
- `role` on `Person`
- `related_issue` on `Decision`
- `business_entity`, `grain`, `sap_table` on `EntityContext`

These fields pass through frontmatter parsing silently today. Future schema work should either add them explicitly or document them as free-form conventions.

---

## Related Documents

- `docs/canonical-model.md` — Canonical object model overview
- `docs/relationship-taxonomy.md` — Relationship types between objects
- `docs/runtime-memory-and-resource-limits.md` — Sizing guidance
- `docs/modeling-methodology.md` — How to build a model repository
