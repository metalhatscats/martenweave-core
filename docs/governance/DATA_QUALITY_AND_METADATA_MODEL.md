# Martenweave Data Quality and Metadata Model

Version: 0.2
Status: Aligned with v0.6.1 implementation
Scope: How Martenweave captures metadata, supports data quality dimensions, detects gaps, and records validation results

---

## Implementation Status

| Capability | Status | Notes |
|---|---|---|
| Metadata taxonomy | Implemented | Identity, domain, physical, semantic, governance, usage, enrichment, lineage, and issue/decision categories are all supported in frontmatter |
| Schema-validated fields | Implemented | `id`, `type`, `status`, `name`, `title`, `description`, `domain`, `target_release`, `roadmap_priority`, `tags`, `created_at`, `updated_at` are validated by Pydantic |
| Convention fields (not yet schema-validated) | Partial | `requiredness`, `priority` (on Issue), `role`, `grain` pass through frontmatter parsing and are used by convention; full schema enforcement is target state |
| Data quality dimensions | Implemented | Completeness, validity, consistency, uniqueness, referential integrity, traceability, and conformity to model rules are all documented and partially enforced |
| Dataset-to-model gap detection | Implemented | `gaps <dataset.csv> --repo ./my-model` detects unmodeled columns, duplicate columns, and multiple matches |
| Model-to-dataset gap detection | Implemented | `gap-report --repo ./my-model --check-model` finds Attributes without FieldEndpoints and missing owners |
| Gap-to-proposal promotion | Implemented | `gaps <dataset.csv> --repo ./my-model --promote-to-proposal` creates a draft PatchProposal |
| Validation result model | Implemented | Structured results with `severity`, `code`, `message`, `object_id`, `source_file`, `field_path`, `related_objects`, `suggested_fix` |
| Evidence and lineage | Implemented | `trace` and `impact` return upstream/downstream relationships; `Decision.evidence` is validated with `--check-decisions` |
| Health/scorecard coverage | Implemented | `health` and `scorecard` compute ownership, validation-rule, LOV, mapping-logic, dataset-profile, traceability, and SAP-table coverage |

---

## Metadata Captured by Martenweave

Martenweave is a metadata-first system. Every canonical object is metadata. The following categories are captured:

### 1. Identity and Lifecycle Metadata

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

### 2. Domain and Structural Metadata

| Field | Typical Object | Purpose |
|---|---|---|
| `domain` | All | Owning `MasterDataDomain` ID |
| `entity` | Attribute, EntityContext, BusinessEntity | Business entity this belongs to |
| `parent_entity` | BusinessEntity | Hierarchical parent entity |
| `entity_context` | Attribute, AttributeUsage, FieldEndpoint | System/business grain context |
| `system` | FieldEndpoint, Interface, Dataset | Physical system |
| `mapping_set` | Mapping | Collection this mapping belongs to |

### 3. Physical and Technical Metadata

Physical metadata belongs on `FieldEndpoint` and `System` objects, not on business `Attribute` objects.

| Field | Typical Object | Purpose |
|---|---|---|
| `endpoint_type` | FieldEndpoint | `sap_table_field`, `file_column`, `api_field` |
| `technical_name` | FieldEndpoint | System-specific field name |
| `system_type` | System | `erp`, `crm`, `data_warehouse`, `api` |
| `grain` | EntityContext | Row-level grain (e.g., `customer_sales_area`) | **Convention field.** Listed in registry search fields but not yet enforced by Pydantic schema. |

**SAP domain-pack extensions:**
- `sap_table` — SAP table name (e.g., `KNVV`)
- `sap_field` — SAP field name (e.g., `KDGRP`)
- `context_category` — Required context for SAP tables (`customer_sales_area` for `KNVV`, etc.)

### 4. Semantic and Business Metadata

| Field | Typical Object | Purpose |
|---|---|---|
| `semantic_category` | Attribute | Business category (e.g., `sales`, `finance`) |
| `data_classification` | Attribute | Sensitivity level (e.g., `internal`, `confidential`) |
| `default_context` | Attribute | Default `EntityContext` when none specified |

### 5. Governance and Ownership Metadata

Ownership fields drive the `OWNERSHIP_MISSING` validation warning on active/draft objects.

| Field | Typical Object | Purpose |
|---|---|---|
| `business_owner` | Attribute, FieldEndpoint, Mapping, ValueList, ValidationRule, Issue, Decision, BusinessEntity, Dataset | Accountable business owner |
| `technical_owner` | Attribute, FieldEndpoint, Mapping, ValueList, ValidationRule | Technical implementation owner |
| `data_steward` | Attribute, FieldEndpoint, Dataset | Data quality steward |
| `accountable_team` | Attribute, FieldEndpoint, Mapping, ValueList, ValidationRule, Dataset | Responsible team |
| `approver` | Attribute, FieldEndpoint, Mapping, ValueList, ValidationRule, Decision, ChangeRequest | Final approver |
| `watchers` | Attribute, FieldEndpoint, Mapping, ValueList, ValidationRule, BusinessEntity, BusinessRule, Dataset | Interested parties |

**Validation rule:** At least one ownership field should be present on active `Attribute`, `FieldEndpoint`, `Dataset`, `Mapping`, `ValidationRule`, `Issue`, `Decision`, `BusinessEntity`, `ValueList`, and `ValueMapping` objects.

### 6. Usage and Scope Metadata

| Field | Typical Object | Purpose |
|---|---|---|
| `usage_type` | AttributeUsage | `primary`, `secondary`, `derived`, `reference` |
| `scope` | AttributeUsage | `sales_area`, `company_code`, `global`, `market` |
| `requiredness` | AttributeUsage | `mandatory`, `optional`, `conditional` | **Convention field.** Not yet enforced by Pydantic schema. Passes through frontmatter parsing. |
| `business_process` | AttributeUsage | Process that uses this field | **Convention field.** Not yet enforced by Pydantic schema. |
| `use_case` | AttributeUsage | Specific use case | **Convention field.** Not yet enforced by Pydantic schema. |

### 7. Enrichment and Quality Metadata

| Field | Typical Object | Purpose |
|---|---|---|
| `value_list` | FieldEndpoint, ValidationRule, Mapping | Allowed values |
| `validation_rules` | Attribute | Linked validation rules |
| `rule_type` | ValidationRule | `format`, `range`, `regex`, `custom` |
| `mapping` | Attribute | Linked source-to-target mapping |
| `value_mapping` | Mapping | Value translation table |

### 8. Source and Target Lineage Metadata

| Field | Typical Object | Purpose |
|---|---|---|
| `source_endpoint` | Mapping | Source `FieldEndpoint` |
| `target_endpoint` | Mapping | Target `FieldEndpoint` |
| `source_value_list` | Mapping, ValueMapping | Source value list |
| `target_value_list` | Mapping, ValueMapping | Target value list |
| `source_system` | Dataset, FieldEndpoint | Origin system |
| `target_system` | Mapping, Interface | Destination system |
| `downstream_consumers` | FieldEndpoint, Dataset | Known consumers |

### 9. Issue and Decision Governance Metadata

| Field | Typical Object | Purpose |
|---|---|---|
| `issue_type` | Issue | `gap`, `risk`, `question`, `blocker` |
| `severity` | Issue, Risk | `low`, `medium`, `high`, `critical` |
| `priority` | Issue | Processing priority | **Convention field.** Not yet enforced by Pydantic schema. Use `roadmap_priority` on BaseObject for schema-validated priority. |
| `decision_category` | Decision | `architecture`, `data_model`, `process` |
| `affected_objects` | Issue, Risk, Decision, ChangeRequest | Objects impacted |
| `related_issues` | Decision, ChangeRequest | Linked issues |
| `related_decisions` | Decision, ChangeRequest | Linked decisions |
| `evidence` | Decision | Supporting evidence objects |
| `recommended_action` | Issue | Suggested remediation |

---

## Data Quality Dimensions Martenweave Can Support

Martenweave supports data quality at the **model layer**, not the **data layer**. It documents the rules, constraints, and checks that define quality — but it does not run profiling against production databases or monitor KPIs over time.

| DQ Dimension | Martenweave Support | How | Limitation |
|---|---|---|---|
| **Completeness** | Partial | Dataset gap detection finds unmodeled columns; model gap detection finds Attributes without FieldEndpoints | Does not check if production data has nulls |
| **Validity** | Partial | `ValidationRule` and `ValueList` document expected constraints; validator checks mapping coherence | Does not execute rules against actual data records |
| **Consistency** | Partial | Reference validation ensures no broken links; SAP context rules enforce table-context alignment | Does not check cross-record consistency |
| **Uniqueness** | Partial | ID uniqueness is enforced; duplicate dataset columns are flagged | Does not check duplicate records in source systems |
| **Referential Integrity** | Partial | Broken references emit `REFERENCE_BROKEN` errors | Validates model references, not database foreign keys |
| **Traceability** | Strong | Full lineage from source to target via relationship graph | — |
| **Conformity to Model Rules** | Strong | Deterministic validation enforces schema, context, and governance rules | — |

### SAP Example: Customer Group Quality

```yaml
# Attribute — business meaning
---
id: ATTR-CUST-SALES-CUSTOMER-GROUP
type: Attribute
status: active
name: Customer Group
domain: DOMAIN-CUSTOMER-BP
semantic_category: sales
data_classification: internal
validation_rules:
  - VAL-CUST-GROUP-ALLOWED-VALUES
---

# ValidationRule — constraint definition
---
id: VAL-CUST-GROUP-ALLOWED-VALUES
type: ValidationRule
status: active
name: Customer Group Allowed Values
domain: DOMAIN-CUSTOMER-BP
attribute: ATTR-CUST-SALES-CUSTOMER-GROUP
value_list: VLIST-S4-CUST-GROUP
rule_type: allowed_values
---

# ValueList — reference data
---
id: VLIST-S4-CUST-GROUP
type: ValueList
status: active
name: S/4HANA Customer Group Values
domain: DOMAIN-CUSTOMER-BP
values:
  - code: "01"
    label: Key Account
  - code: "02"
    label: National Account
  - code: "03"
    label: Regional Account
---

# ValueMapping — cross-system translation
---
id: VMAP-LEGACY-CUST-GROUP-TO-S4-KDGRP
type: ValueMapping
status: active
name: Legacy Customer Group to S/4 KDGRP
domain: DOMAIN-CUSTOMER-BP
value_list: VLIST-S4-CUST-GROUP
mappings:
  - from: A17
    to: "01"
    condition: sales_org == CH01
  - from: B22
    to: "02"
```

**Quality coverage:**
- `ValidationRule` defines that Customer Group must be in the allowed value list.
- `ValueList` documents the allowed S/4 values.
- `ValueMapping` documents the translation from legacy codes.
- The validator checks that `VMAP` target values exist in `VLIST`.
- The validator checks that `VAL-CUST-GROUP-ALLOWED-VALUES` references an existing `Attribute` and `ValueList`.

**What Martenweave does not do:** It does not run a SQL query against the legacy database to check if `A17` exists in production data. That is the job of the data migration team and SAP Migration Cockpit.

---

## Dataset/Model Gap Detection

Martenweave detects gaps in two directions:

### 1. Dataset-to-Model Gaps ("What's in the data that we haven't modeled?")

The `gaps` command profiles a CSV/XLSX dataset and compares columns against `FieldEndpoint` objects:

```bash
martenweave gaps ./data/customer_sales_area_load.csv --repo ./my-model
```

| Gap Code | Severity | Meaning | Example |
|---|---|---|---|
| `UNMODELED_DATASET_COLUMN` | warning | Dataset column has no matching FieldEndpoint | Column `CUST_GRP_2` exists in CSV but no `FEP-*` object references it |
| `DATASET_COLUMN_MULTIPLE_MATCHES` | warning | Column matches multiple endpoints | `GROUP` matches both `FEP-LEGACY-CUST-GROUP` and `FEP-LEGACY-PROD-GROUP` |
| `DUPLICATE_COLUMN_NAME` | warning | Duplicate column name in dataset | Two columns named `STATUS` |
| `EMPTY_DATASET` | info | Dataset has no columns | Empty CSV file |
| `NO_MATCHING_ENDPOINTS` | warning | None of the dataset columns matched any FieldEndpoint | Completely unmodeled dataset |

**Auto-proposal:** The system can promote gaps to a `PatchProposal`:

```bash
martenweave gaps ./data/load.csv --repo ./my-model --promote-to-proposal
```

This creates a draft `PatchProposal` with `create_object` operations for unmodeled columns.

### 2. Model-to-Dataset Gaps ("What have we modeled that has no source?")

The `gaps` command (with `--check-model`) detects model-side gaps:

```bash
martenweave gaps ./data/load.csv --repo ./my-model --check-model
```

| Gap Code | Severity | Meaning | Example |
|---|---|---|---|
| `MODEL_ATTRIBUTE_MISSING_SOURCE` | critical | Attribute has no linked FieldEndpoint | `ATTR-CUST-SALES-CUSTOMER-GROUP` has no `represents_attribute` relationship |
| `MISSING_OWNER` | warning | Active object lacks ownership | `FEP-S4-KNVV-KDGRP` has no `business_owner` or `technical_owner` |

---

## Validation Result Model

Every validation run produces structured results with stable codes:

### Severity Levels

| Level | Blocks Indexing? | Blocks Apply? | Example |
|---|---|---|---|
| `error` | Yes | Yes | `REFERENCE_BROKEN`, `SAP_CONTEXT_KNVV_REQUIRES_SALES_AREA` |
| `warning` | No | No (unless `--strict`) | `OWNERSHIP_MISSING`, `ATTRIBUTE_MISSING_CONTEXT` |
| `info` | No | No | `SCHEMA_VERSION_MISSING`, `INDEX_STALE` |

### Validation Result Structure

```json
{
  "severity": "error",
  "code": "SAP_CONTEXT_KNVV_REQUIRES_SALES_AREA",
  "message": "KNVV field endpoint must use Customer Sales Area context.",
  "object_id": "FEP-S4-KNVV-KDGRP",
  "object_type": "FieldEndpoint",
  "source_file": "model/field-endpoints/FEP-S4-KNVV-KDGRP.md",
  "field_path": "entity_context",
  "related_objects": ["CTX-CUSTOMER-SALES-AREA-S4"],
  "suggested_fix": "Set entity_context to CTX-CUSTOMER-SALES-AREA-S4 or another context classified as Customer Sales Area."
}
```

### Key Validation Codes

| Code | Severity | Layer | Meaning |
|---|---|---|---|
| `ID_MISSING` | error | Layer 1 | Object has no ID |
| `ID_INVALID_FORMAT` | error | Layer 1 | ID does not match `^[A-Z][A-Z0-9]*(-[A-Z0-9]+)*$` |
| `ID_DUPLICATE` | error | Layer 1 | Same ID appears in multiple files |
| `REFERENCE_BROKEN` | error | Layer 4 | Referenced ID does not exist |
| `REFERENCE_TYPE_MISMATCH` | error | Layer 4 | Referenced object type does not match expected target type |
| `SAP_CONTEXT_KNVV_REQUIRES_SALES_AREA` | error | Layer 6 | KNVV field endpoint must use `customer_sales_area` context |
| `SAP_CONTEXT_KNB1_REQUIRES_COMPANY_CODE` | error | Layer 6 | KNB1 field endpoint must use `customer_company_code` context |
| `OWNERSHIP_MISSING` | warning | Layer 9 | Active object lacks ownership field |
| `ATTRIBUTE_MISSING_CONTEXT` | warning | Layer 6 | Active Attribute lacks `entity_context` or `default_context` |
| `FIELD_ENDPOINT_MISSING_ENRICHMENT` | warning | Layer 7 | Active FieldEndpoint lacks `value_list`, mapping, or validation rule |
| `LOV_EMPTY` | warning | Layer 7 | Active ValueList has no values |
| `VALUE_MAPPING_EMPTY` | warning | Layer 7 | Active ValueMapping has no mappings |
| `FLAT_MODEL_STRUCTURE` | warning | Layer 11 | Repository has very few objects |
| `INDEX_STALE` | info | Layer 11 | Generated index is older than canonical files |

---

## Evidence and Lineage Expectations

### Evidence

Every significant model decision should be backed by evidence:

- **Source material:** Email, ticket, workshop note, SAP validation report, dataset profile.
- **Evidence object:** `Evidence` canonical file with `evidence_type`, `source_system`, `source_date`, and `related_objects`.
- **Linking:** `Decision` objects reference `Evidence` via `evidence` field. `Issue` objects reference `Evidence` via `related_objects`.

### Lineage

Lineage is generated from canonical references and stored as directed edges:

| Relationship Type | Source | Target | Meaning |
|---|---|---|---|
| `represents_attribute` | FieldEndpoint | Attribute | Physical field represents business meaning |
| `mapped_from` | Mapping | FieldEndpoint | Mapping starts from source endpoint |
| `mapped_to` | Mapping | FieldEndpoint | Mapping ends at target endpoint |
| `validated_by` | Attribute | ValidationRule | Object is validated by this rule |
| `has_allowed_values` | Attribute | ValueList | Object has this list of allowed values |
| `affects` | ChangeRequest | Any | Request affects these objects |
| `explained_by_decision` | Any | Decision | Object is explained by this decision |
| `supported_by_evidence` | Any | Evidence | Object is supported by this evidence |

**Lineage query example:**

```bash
martenweave trace ATTR-CUST-SALES-CUSTOMER-GROUP --repo ./my-model
```

Returns upstream (source systems, source fields, source datasets) and downstream (target fields, validations, mappings, issues, decisions, owners).

---

## Limitations

1. **Model-layer only:** Martenweave validates the *model*, not the *data*. It does not run SQL queries, check production data quality, or monitor streaming pipelines.
2. **No real-time monitoring:** No KPI dashboards, no alerting, no trend analysis over time.
3. **No data profiling against databases:** Dataset profiling works on CSV/XLSX files, not live database connections.
4. **Schema gaps:** Some documented fields (`requiredness`, `priority`, `role`, `grain`) pass through frontmatter parsing silently because they are not yet declared in Pydantic schemas.
5. **No automated rule execution:** `ValidationRule` objects document rules; they are not executed against data records.
6. **No cross-repository validation:** Validation is scoped to a single repository. Cross-repo consistency is manual.

---

## Future Enhancements

| Enhancement | Description | Priority |
|---|---|---|
| **Add `requiredness` to Pydantic schema** | Close gap between documented taxonomy and runtime validation | High |
| **Add `priority` to Issue schema** | Enable issue triage and workload management | Medium |
| **Health report scoring** | Numeric scorecard with trend tracking across releases | Medium |
| **Dataset profiling against databases** | Connect to JDBC/ODBC sources for live profiling | Low |
| **Validation rule execution engine** | Execute documented rules against sample data or test databases | Low |
| **Cross-repository diff** | Compare two model repositories for consistency | Medium |
| **Time-series gap tracking** | Track gap resolution over time | Low |

---

## Related Documents

- `docs/governance/DAMA_ALIGNMENT.md` — DAMA-DMBOK alignment overview
- `docs/governance/DATA_GOVERNANCE_OPERATING_MODEL.md` — Practical operating model for governance work
- `docs/governance/AI_READY_DATA_MODEL_LAYER.md` — AI-ready model layer design
- `docs/model-metadata-taxonomy.md` — Full metadata taxonomy reference
- `docs/validation-methodology-warnings.md` — Validation warning codes and fixes
- `docs/model-side-gaps.md` — Model-side gap detection with `--check-model`
- `docs/canonical-model.md` — Canonical object model reference
