# ModelOps for MDM — Schema and Validation Specification

Version: `0.2-draft`  
Document type: Schema and validation architecture  
Scope: Canonical object schemas, validation rules, validation pipeline, SAP-specific checks, AI patch validation, dataset/mapping checks  
Initial product focus: SAP Business Partner migration model, Customer role slice first  
Repository style: File-based canonical model repository with generated validation/index layer

---

## 1. Purpose

This document defines the schema and validation architecture for **ModelOps for MDM**.

## MVP Validation Boundary

P0 validation must be strict enough to protect the Customer Group / `KNVV-KDGRP` workflow.

Build these checks first:

```text
file parsing and frontmatter validity
required common fields
unique stable IDs
allowed object types and statuses
reference resolution
Business Partner / Customer / Customer Sales Area scope consistency
KNVV endpoint requires Customer Sales Area context
KNB1 endpoint requires Customer Company Code context
Attribute -> AttributeUsage -> FieldEndpoint links
Mapping and ValueMapping endpoint references
ValueMapping unresolved target values
Dataset column matching to model objects
missing owner warnings
missing validation warnings
PatchProposal allowed/disallowed actions
PatchProposal requires evidence and human approval before write
stale generated index warning
```

Defer advanced validation rules until the P0 repository, index, dataset gap, impact, and AI patch loop work end to end.

The goal is to make the model repository:

- structurally valid;
- referentially consistent;
- SAP-context aware;
- migration-useful;
- governance-ready;
- AI-safe;
- suitable for lineage, impact analysis, and AMS handover.

This specification describes:

- canonical object schema principles;
- common required fields;
- object-specific required fields;
- lifecycle/status validation;
- relationship validation;
- SAP-specific validation;
- mapping and value mapping validation;
- dataset and gap validation;
- ownership validation;
- change governance validation;
- AI patch proposal validation;
- validation severity levels;
- validation pipeline;
- error codes;
- testing strategy.

---

## 2. Validation philosophy

The system must use deterministic validation before AI interpretation.

```text
Schema validation
  → reference validation
  → SAP context validation
  → mapping/value validation
  → dataset/gap validation
  → governance validation
  → AI patch validation
```

AI may help explain, summarize, propose, and classify, but AI must not be the authority for whether the repository is valid.

The repository should remain usable in degraded read-only mode when warnings exist, but approved model changes must be blocked when critical errors exist.

---

## 3. Main validation principle

The product validates **model knowledge**, not raw SAP master data records.

The validation engine checks:

- whether model objects are structured correctly;
- whether object relationships are valid;
- whether SAP contexts are modeled correctly;
- whether mappings and value lists are coherent;
- whether datasets match the model;
- whether ownership and lifecycle are clear;
- whether AI-proposed changes are safe to apply.

It does not replace SAP validation, MDG checks, or S/4HANA data consistency checks.

---

## 4. Recommended schema technology

### 4.1 MVP recommendation

Use:

```text
Python Pydantic models as primary runtime schemas
JSON Schema generated from Pydantic for UI/reference
YAML/Markdown frontmatter as canonical source input
SQLite validation_results table as generated output
```

Recommended stack:

```text
Pydantic v2
PyYAML or ruamel.yaml
python-frontmatter or custom parser
pytest for validation tests
```

### 4.2 Why Pydantic first

Pydantic is suitable because it provides:

- strict runtime validation;
- typed models;
- clean error reporting;
- JSON Schema export;
- field validators;
- model validators;
- easy integration with FastAPI.

### 4.3 Zod option

If the project becomes TypeScript-first, Zod may be used for frontend/runtime schemas.

Recommended approach if both Python and TypeScript exist:

```text
Pydantic = backend source of validation
JSON Schema = generated contract
TypeScript types = generated from JSON Schema
```

Avoid maintaining two independent schema systems manually.

---

## 5. Validation layers

Validation should be organized into layers.

```text
Layer 1 — File and parsing validation
Layer 2 — Common object schema validation
Layer 3 — Type-specific schema validation
Layer 4 — Reference validation
Layer 5 — Lifecycle/status validation
Layer 6 — SAP context validation
Layer 7 — Mapping and value validation
Layer 8 — Dataset and gap validation
Layer 9 — Governance validation
Layer 10 — AI patch validation
Layer 11 — Repository health scoring
```

Each layer should produce structured validation results.

---

## 6. Validation severities

Use three severity levels.

```text
error
warning
info
```

### 6.1 Error

Errors block patch approval and should block “healthy” repository status.

Examples:

- invalid YAML frontmatter;
- duplicate ID;
- missing required field;
- broken reference;
- invalid object type;
- invalid lifecycle status;
- SAP endpoint with wrong context;
- value mapping target value missing from target value list;
- AI patch attempts direct unapproved write.

### 6.2 Warning

Warnings do not block browsing but require review.

Examples:

- attribute has no owner;
- attribute has no validation;
- value list has no snapshot date;
- issue has no affected objects;
- decision has no related objects;
- dataset is registered but not profiled;
- field endpoint has no linked attribute.

### 6.3 Info

Info is useful operational metadata.

Examples:

- generated index is outdated;
- AI is disabled;
- repository is not a Git repository;
- object has no recent changes;
- dataset profile was generated from sample rows only.

---

## 7. Validation result format

Every validation finding should have a stable code.

Recommended structure:

```json
{
  "severity": "error",
  "code": "SAP_CONTEXT_KNVV_REQUIRES_SALES_AREA",
  "message": "KNVV field endpoint must use Customer Sales Area context.",
  "object_id": "FEP-S4-KNVV-KDGRP",
  "object_type": "FieldEndpoint",
  "source_file": "model/field-endpoints/FEP-S4-KNVV-KDGRP.md",
  "field_path": "entity_context",
  "related_objects": [
    "CTX-CUSTOMER-SALES-AREA-S4"
  ],
  "suggested_fix": "Set entity_context to CTX-CUSTOMER-SALES-AREA-S4 or another context classified as Customer Sales Area."
}
```

Required fields:

```text
severity
code
message
object_id or source_file
```

Recommended fields:

```text
object_type
field_path
related_objects
suggested_fix
details
```

---

## 8. Common object schema

Every canonical object must have common fields.

### 8.1 Required common fields

```yaml
id: ATTR-CUST-SALES-CUSTOMER-GROUP
type: Attribute
status: active
```

Most objects should also have either:

```yaml
name: Customer Group
```

or:

```yaml
title: Customer Group config missing for CH01 / A17
```

### 8.2 Recommended common fields

```yaml
domain: DOMAIN-CUSTOMER-BP
description: Sales-area-dependent customer grouping used in sales processes and reporting.
owners:
  accountable: ROLE-SALES-MD-OWNER
  responsible: ROLE-CUSTOMER-BP-STEWARD
related_issues: []
related_decisions: []
evidence: []
change_history: []
```

### 8.3 Common field rules

| Field | Required | Rule |
|---|---:|---|
| `id` | Yes | Globally unique, stable, ID-safe |
| `type` | Yes | Must match known object type |
| `status` | Yes | Must be allowed for object type |
| `domain` | Recommended | Required for domain-scoped objects |
| `name` / `title` | Recommended | Required for UI display |
| `owners` | Recommended | Warning if missing for governed objects |
| `description` | Recommended | Warning for critical objects if missing |

---

## 9. ID validation

### 9.1 ID format

Recommended regex:

```regex
^[A-Z][A-Z0-9]*(-[A-Z0-9]+)*$
```

Examples:

```text
ATTR-CUST-SALES-CUSTOMER-GROUP
FEP-S4-KNVV-KDGRP
CR-0021
PATCH-0021
```

### 9.2 ID validation rules

| Code | Severity | Rule |
|---|---|---|
| `ID_MISSING` | error | Object has no ID |
| `ID_INVALID_FORMAT` | error | ID does not match allowed format |
| `ID_DUPLICATE` | error | Same ID appears in multiple files |
| `ID_PREFIX_TYPE_MISMATCH` | warning/error | ID prefix does not match object type |
| `ID_CHANGED_WITHOUT_MIGRATION` | warning | Existing object appears renamed without migration |

Prefix/type mismatch may be an error for MVP if strictness is desired.

---

## 10. Object type registry

Allowed object types:

```text
MasterDataDomain
MigrationObject
BusinessEntity
EntityContext
Attribute
AttributeUsage
System
SystemEnvironment
SAPObject
FieldEndpoint
Interface
Dataset
MappingSet
Mapping
ValueList
ValueMapping
BusinessRule
TransformationLogic
ValidationRule
DataQualityCheck
OwnershipRole
Person
Team
Issue
Risk
Decision
ChangeRequest
PatchProposal
Evidence
```

The validator must reject unknown object types unless explicitly configured as experimental.

---

## 11. Lifecycle and status validation

### 11.1 General statuses

Allowed general statuses:

```text
draft
proposed
under_review
approved
active
deprecated
retired
rejected
superseded
```

### 11.2 Issue statuses

```text
open
in_progress
blocked
resolved
closed
rejected
```

### 11.3 PatchProposal statuses

```text
pending_review
accepted
rejected
superseded
```

### 11.4 ChangeRequest statuses

```text
draft
under_review
approved
implemented
rejected
cancelled
```

### 11.5 Dataset statuses

```text
registered
profiled
validated
failed_validation
archived
```

### 11.6 Status rules

| Code | Severity | Rule |
|---|---|---|
| `STATUS_INVALID` | error | Status not allowed for object type |
| `STATUS_LIFECYCLE_MISMATCH` | warning | Top-level `status` differs from `lifecycle.status` |
| `ACTIVE_OBJECT_REFS_RETIRED_OBJECT` | warning/error | Active object references retired object |
| `APPROVED_OBJECT_REFS_DRAFT_OBJECT` | error | Approved mapping/validation references draft logic/value list |
| `RETIRED_OBJECT_USED_BY_ACTIVE_OBJECT` | warning/error | Retired object still used by active object |

---

## 12. Relationship validation

### 12.1 General rule

All canonical relationships must use stable object IDs.

Invalid:

```yaml
related_attributes:
  - Customer Group
```

Valid:

```yaml
related_attributes:
  - ATTR-CUST-SALES-CUSTOMER-GROUP
```

### 12.2 Relationship rules

| Code | Severity | Rule |
|---|---|---|
| `REFERENCE_BROKEN` | error | Referenced ID does not exist |
| `REFERENCE_TYPE_MISMATCH` | error | Referenced object type is not valid for field |
| `REFERENCE_TO_RETIRED_OBJECT` | warning/error | Active object references retired object |
| `RELATIONSHIP_EMPTY_REQUIRED` | error | Required relationship list is empty |
| `RELATIONSHIP_DUPLICATE` | warning | Same reference appears multiple times |
| `RELATIONSHIP_SELF_REFERENCE` | warning/error | Object references itself where not allowed |
| `RELATIONSHIP_CYCLE_DETECTED` | warning | Cycle exists where it may cause impact/lineage problems |

### 12.3 Relationship confidence

Generated relationship edges should use confidence:

```text
explicit
derived
inferred
ai_suggested
```

Validation rule:

```text
ai_suggested relationships must not become canonical without approval.
```

---

## 13. Domain schema

### 13.1 Required fields

```yaml
id: DOMAIN-CUSTOMER-BP
type: MasterDataDomain
name: Customer / Business Partner
status: active
```

### 13.2 Recommended fields

```yaml
description: Customer and Business Partner model knowledge for SAP migration and AMS.
owners:
  accountable: ROLE-CUSTOMER-MD-OWNER
  responsible: ROLE-CUSTOMER-BP-STEWARD
```

### 13.3 Validation rules

| Code | Severity | Rule |
|---|---|---|
| `DOMAIN_NAME_MISSING` | error | Domain must have name |
| `DOMAIN_WITHOUT_OWNER` | warning | Active domain should have owner |
| `DOMAIN_EMPTY` | warning | Domain has no migration objects/entities/attributes |

---

## 14. MigrationObject schema

### 14.1 Required fields

```yaml
id: MIGOBJ-CUSTOMER-BP
type: MigrationObject
domain: DOMAIN-CUSTOMER-BP
name: Customer Business Partner Migration
status: active
```

### 14.2 Recommended fields

```yaml
target_system: SYS-S4HANA
entities:
  - ENTITY-BUSINESS-PARTNER
  - ENTITY-CUSTOMER-SALES-AREA
  - ENTITY-CUSTOMER-COMPANY-CODE
```

### 14.3 Validation rules

| Code | Severity | Rule |
|---|---|---|
| `MIGOBJ_DOMAIN_MISSING` | error | MigrationObject must reference Domain |
| `MIGOBJ_TARGET_SYSTEM_MISSING` | warning | Active migration object should have target system |
| `MIGOBJ_ENTITY_REF_BROKEN` | error | Referenced entity does not exist |

---

## 15. BusinessEntity schema

### 15.1 Required fields

```yaml
id: ENTITY-CUSTOMER-SALES-AREA
type: BusinessEntity
domain: DOMAIN-CUSTOMER-BP
name: Customer Sales Area
status: active
```

### 15.2 Recommended fields

```yaml
description: Sales-area-dependent customer data.
grain:
  - customer_number
  - sales_org
  - distribution_channel
  - division
```

### 15.3 Validation rules

| Code | Severity | Rule |
|---|---|---|
| `ENTITY_DOMAIN_MISSING` | error | Entity must reference Domain |
| `ENTITY_GRAIN_MISSING` | warning | Context-dependent entity should define grain |
| `ENTITY_WITHOUT_CONTEXT` | warning | Entity has no EntityContext |

---

## 16. EntityContext schema

EntityContext is critical for SAP correctness.

### 16.1 Required fields

```yaml
id: CTX-CUSTOMER-SALES-AREA-S4
type: EntityContext
domain: DOMAIN-CUSTOMER-BP
entity: ENTITY-CUSTOMER-SALES-AREA
name: S/4HANA Customer Sales Area
status: active
```

### 16.2 Recommended fields

```yaml
system: SYS-S4HANA
sap_tables:
  - KNVV
related_bp_roles:
  - SAPROLE-FLCU01
grain:
  - KUNNR
  - VKORG
  - VTWEG
  - SPART
context_category: customer_sales_area
```

### 16.3 Allowed `context_category`

```text
bp_central
bp_address
bp_identification
customer_company_code
customer_sales_area
customer_partner_function
supplier_company_code
supplier_purchasing_org
material_general
material_plant
material_sales
material_valuation
finance_master
employee_bp
legacy_source
migration_staging
interface_specific
reporting
other
```

### 16.4 Validation rules

| Code | Severity | Rule |
|---|---|---|
| `CTX_ENTITY_REF_BROKEN` | error | EntityContext references missing entity |
| `CTX_SYSTEM_REF_BROKEN` | error | Referenced system does not exist |
| `CTX_CATEGORY_INVALID` | error | Invalid context category |
| `CTX_GRAIN_MISSING` | warning/error | Context-dependent context has no grain |
| `CTX_SAP_TABLE_WITHOUT_SYSTEM` | warning | SAP table context should reference SAP system |

---

## 17. Attribute schema

Attribute defines business meaning.

### 17.1 Required fields

```yaml
id: ATTR-CUST-SALES-CUSTOMER-GROUP
type: Attribute
domain: DOMAIN-CUSTOMER-BP
name: Customer Group
status: active
```

### 17.2 Recommended fields

```yaml
description: Sales-area-dependent customer grouping used in sales processes and reporting.
semantic_category: sales_classification
data_classification: internal
default_context: CTX-CUSTOMER-SALES-AREA-S4
owners:
  accountable: ROLE-SALES-MD-OWNER
  responsible: ROLE-CUSTOMER-BP-STEWARD
```

### 17.3 Allowed `data_classification`

```text
public
internal
confidential
restricted
personal_data
sensitive_personal_data
unknown
```

### 17.4 Validation rules

| Code | Severity | Rule |
|---|---|---|
| `ATTR_DOMAIN_MISSING` | error | Attribute must reference Domain |
| `ATTR_NAME_MISSING` | error | Attribute must have name |
| `ATTR_DESCRIPTION_MISSING` | warning | Active attribute should have description |
| `ATTR_WITHOUT_USAGE` | warning/error | Active attribute should have at least one AttributeUsage |
| `ATTR_WITHOUT_OWNER` | warning | Active attribute should have owner/steward |
| `ATTR_WITHOUT_VALIDATION` | warning | Critical/in-scope attribute should have validation |
| `ATTR_DEFAULT_CONTEXT_BROKEN` | error | Default context does not exist |
| `ATTR_DATA_CLASSIFICATION_INVALID` | error | Invalid data classification |

---

## 18. AttributeUsage schema

AttributeUsage places an Attribute into a specific business/SAP context.

### 18.1 Required fields

```yaml
id: USE-CUST-SALES-CUSTOMER-GROUP-S4
type: AttributeUsage
attribute: ATTR-CUST-SALES-CUSTOMER-GROUP
entity_context: CTX-CUSTOMER-SALES-AREA-S4
status: active
```

### 18.2 Recommended fields

```yaml
usage_type: target_attribute
grain:
  - KUNNR
  - VKORG
  - VTWEG
  - SPART
requiredness: conditional
condition: Required for selected sales organizations and customer groups.
migration_relevance: in_scope
validation_relevance: in_scope
maintenance_context:
  sap_roles:
    - SAPROLE-FLCU01
  sap_ui_area: Customer Sales Area
```

### 18.3 Allowed `usage_type`

```text
source_attribute
target_attribute
staging_attribute
reporting_attribute
validation_attribute
interface_attribute
derived_attribute
reference_attribute
```

### 18.4 Allowed `requiredness`

```text
required
optional
conditional
not_applicable
unknown
```

### 18.5 Validation rules

| Code | Severity | Rule |
|---|---|---|
| `USE_ATTRIBUTE_REF_BROKEN` | error | Referenced Attribute does not exist |
| `USE_CONTEXT_REF_BROKEN` | error | Referenced EntityContext does not exist |
| `USE_REQUIREDNESS_INVALID` | error | Invalid requiredness |
| `USE_CONDITIONAL_WITHOUT_CONDITION` | warning/error | Conditional usage should define condition |
| `USE_GRAIN_MISMATCH_CONTEXT` | warning | Usage grain differs from context grain without explanation |
| `USE_MAINTENANCE_ROLE_REF_BROKEN` | error | Referenced SAP role does not exist |

---

## 19. System schema

### 19.1 Required fields

```yaml
id: SYS-S4HANA
type: System
name: SAP S/4HANA
status: active
```

### 19.2 Recommended fields

```yaml
system_category: sap_s4hana
role: target
owners:
  functional_owner: ROLE-S4-FUNCTIONAL
  technical_owner: ROLE-BASIS-TEAM
```

### 19.3 Allowed `system_category`

```text
sap_s4hana
sap_ecc
sap_mdg
sap_bw
sap_cpi
sap_cloud_alm
solman
legacy
staging
file_share
data_warehouse
reporting
external
manual
other
```

### 19.4 Allowed `role`

```text
source
target
intermediate
governance
reporting
validation
reference
other
```

### 19.5 Validation rules

| Code | Severity | Rule |
|---|---|---|
| `SYSTEM_CATEGORY_INVALID` | error | Invalid system category |
| `SYSTEM_ROLE_INVALID` | error | Invalid system role |
| `SYSTEM_WITHOUT_OWNER` | warning | Active system should have owner |

---

## 20. SystemEnvironment schema

### 20.1 Required fields

```yaml
id: ENV-S4-RS4
type: SystemEnvironment
system: SYS-S4HANA
name: RS4
status: active
```

### 20.2 Recommended fields

```yaml
environment_type: test
client: "100"
```

### 20.3 Allowed `environment_type`

```text
development
test
quality
preprod
production
sandbox
training
unknown
```

### 20.4 Validation rules

| Code | Severity | Rule |
|---|---|---|
| `ENV_SYSTEM_REF_BROKEN` | error | Referenced System does not exist |
| `ENV_TYPE_INVALID` | error | Invalid environment type |
| `ENV_CLIENT_FORMAT_INVALID` | warning | SAP client should usually be 3 digits |

---

## 21. SAPObject schema

SAPObject describes SAP-specific tables, roles, APIs, transactions, reports, IDoc segments, configuration tables, etc.

### 21.1 Required fields

```yaml
id: SAPTABLE-KNVV
type: SAPObject
sap_object_type: table
name: KNVV
status: active
```

### 21.2 Allowed `sap_object_type`

```text
table
field
view
structure
bp_role
transaction
bapi
rfc
odata_service
idoc_type
idoc_segment
cpi_iflow
custom_table
custom_report
configuration_table
validation_report
other
```

### 21.3 Validation rules

| Code | Severity | Rule |
|---|---|---|
| `SAP_OBJECT_TYPE_INVALID` | error | Invalid SAP object type |
| `SAP_OBJECT_NAME_MISSING` | error | SAP object must have name |
| `SAP_TABLE_WITHOUT_RELATED_CONTEXT` | warning | SAP table should link related EntityContext |
| `SAP_ROLE_AS_PHYSICAL_STORAGE` | error | BP role must not be used as physical storage endpoint |

---

## 22. FieldEndpoint schema

FieldEndpoint is the physical/system-specific representation of a value.

### 22.1 Required fields

```yaml
id: FEP-S4-KNVV-KDGRP
type: FieldEndpoint
domain: DOMAIN-CUSTOMER-BP
system: SYS-S4HANA
endpoint_type: sap_table_field
status: active
```

### 22.2 SAP table field required fields

```yaml
sap_table: KNVV
sap_field: KDGRP
technical_name: KNVV-KDGRP
entity_context: CTX-CUSTOMER-SALES-AREA-S4
```

### 22.3 Dataset column required fields

```yaml
dataset: DATASET-CUSTOMER-SALES-AREA-LOAD
column_name: CUSTOMER_GROUP
```

### 22.4 Recommended fields

```yaml
business_attribute: ATTR-CUST-SALES-CUSTOMER-GROUP
grain:
  - KUNNR
  - VKORG
  - VTWEG
  - SPART
data_type: CHAR
length: 2
```

### 22.5 Allowed `endpoint_type`

```text
sap_table_field
sap_structure_field
sap_api_field
sap_idoc_field
sap_report_field
legacy_table_field
dataset_column
staging_column
api_field
interface_field
report_column
manual_input
other
```

### 22.6 Validation rules

| Code | Severity | Rule |
|---|---|---|
| `FEP_SYSTEM_REF_BROKEN` | error | Referenced System does not exist |
| `FEP_ENDPOINT_TYPE_INVALID` | error | Invalid endpoint type |
| `FEP_ATTRIBUTE_REF_BROKEN` | error | Referenced Attribute does not exist |
| `FEP_CONTEXT_REF_BROKEN` | error | Referenced EntityContext does not exist |
| `FEP_SAP_TABLE_FIELD_MISSING_TABLE` | error | SAP table field endpoint must have sap_table |
| `FEP_SAP_TABLE_FIELD_MISSING_FIELD` | error | SAP table field endpoint must have sap_field |
| `FEP_DATASET_COLUMN_MISSING_DATASET` | error | Dataset column endpoint must reference dataset |
| `FEP_DATASET_COLUMN_MISSING_COLUMN` | error | Dataset column endpoint must have column name |
| `FEP_WITHOUT_ATTRIBUTE` | warning | Endpoint has no linked business attribute |
| `FEP_WITHOUT_CONTEXT` | warning/error | SAP endpoint should have entity context |

---

## 23. Interface schema

### 23.1 Required fields

```yaml
id: IFACE-LEGACY-CUSTOMER-SALES-EXTRACT
type: Interface
domain: DOMAIN-CUSTOMER-BP
name: Legacy Customer Sales Extract
interface_type: file_extract
status: active
```

### 23.2 Recommended fields

```yaml
source_system: SYS-LEGACY-CRM
target_system: SYS-MIGRATION-STAGING
direction: outbound
frequency: ad_hoc
datasets:
  - DATASET-CUSTOMER-SALES-AREA-LOAD
owners:
  functional_owner: ROLE-CUSTOMER-MIGRATION
  technical_owner: ROLE-INTERFACE-TEAM
```

### 23.3 Allowed `interface_type`

```text
file_extract
manual_upload
migration_cockpit
idoc
bapi
rfc
odata
cpi_iflow
drfout
mdg_replication
custom_abap_report
validation_export
reporting_extract
other
```

### 23.4 Validation rules

| Code | Severity | Rule |
|---|---|---|
| `IFACE_TYPE_INVALID` | error | Invalid interface type |
| `IFACE_SOURCE_SYSTEM_BROKEN` | error | Source system reference broken |
| `IFACE_TARGET_SYSTEM_BROKEN` | error | Target system reference broken |
| `IFACE_WITHOUT_OWNER` | warning | Active interface should have owner |
| `IFACE_DATASET_REF_BROKEN` | error | Dataset reference broken |

---

## 24. Dataset schema

### 24.1 Required fields

```yaml
id: DATASET-CUSTOMER-SALES-AREA-LOAD
type: Dataset
domain: DOMAIN-CUSTOMER-BP
name: Customer Sales Area Load File
dataset_type: migration_file
status: registered
```

### 24.2 Recommended fields

```yaml
path: ../data/raw/customer_sales_area_load.xlsx
source_system: SYS-LEGACY-CRM
target_system: SYS-S4HANA
entity_context: CTX-CUSTOMER-SALES-AREA-STAGING
profile:
  row_count: 12500
  column_count: 84
  last_profiled_at: 2026-04-26
```

### 24.3 Allowed `dataset_type`

```text
migration_file
source_extract
staging_file
validation_input
validation_output
report_export
config_snapshot
value_list_snapshot
sample
other
```

### 24.4 Validation rules

| Code | Severity | Rule |
|---|---|---|
| `DATASET_TYPE_INVALID` | error | Invalid dataset type |
| `DATASET_PATH_MISSING` | warning | Dataset should reference source path unless abstract |
| `DATASET_NOT_PROFILED` | warning | Dataset has no profile |
| `DATASET_CONTEXT_REF_BROKEN` | error | Entity context reference broken |
| `DATASET_SOURCE_SYSTEM_BROKEN` | error | Source system reference broken |
| `DATASET_TARGET_SYSTEM_BROKEN` | error | Target system reference broken |

---

## 25. MappingSet and Mapping schemas

### 25.1 MappingSet required fields

```yaml
id: MAPSET-CUSTOMER-SALES-AREA-LEGACY-TO-S4
type: MappingSet
domain: DOMAIN-CUSTOMER-BP
name: Legacy CRM to S/4 Customer Sales Area Mapping
status: active
```

### 25.2 Mapping required fields

```yaml
id: MAP-CUST-GROUP-LEGACY-TO-KNVV-KDGRP
type: Mapping
domain: DOMAIN-CUSTOMER-BP
source_endpoints:
  - FEP-LEGACY-CUSTOMER-GROUP
target_endpoints:
  - FEP-S4-KNVV-KDGRP
mapping_type: value_mapped
status: approved
```

### 25.3 Allowed `mapping_type`

```text
direct
renamed
constant
defaulted
derived
value_mapped
concatenated
split
aggregated
conditional
manual
not_migrated
out_of_scope
```

### 25.4 Validation rules

| Code | Severity | Rule |
|---|---|---|
| `MAP_SOURCE_ENDPOINT_MISSING` | error | Mapping must have source endpoint unless type permits none |
| `MAP_TARGET_ENDPOINT_MISSING` | error | Mapping must have target endpoint unless out_of_scope |
| `MAP_SOURCE_ENDPOINT_BROKEN` | error | Source endpoint reference broken |
| `MAP_TARGET_ENDPOINT_BROKEN` | error | Target endpoint reference broken |
| `MAP_TYPE_INVALID` | error | Invalid mapping type |
| `MAP_VALUE_MAPPED_WITHOUT_VALUE_MAPPING` | warning/error | value_mapped mapping should reference ValueMapping |
| `MAP_DERIVED_WITHOUT_LOGIC` | warning/error | derived/conditional mapping should reference TransformationLogic |
| `MAP_APPROVED_REFS_DRAFT_LOGIC` | error | Approved mapping references draft logic |
| `MAP_WITHOUT_OWNER` | warning | Active/approved mapping should have owner |

---

## 26. ValueList schema

### 26.1 Required fields

```yaml
id: VLIST-S4-KNVV-KDGRP
type: ValueList
domain: DOMAIN-CUSTOMER-BP
name: S/4 Customer Group Values
status: active
```

### 26.2 Recommended fields

```yaml
attribute: ATTR-CUST-SALES-CUSTOMER-GROUP
source:
  system: SYS-S4HANA
  environment: ENV-S4-RS4
  sap_table: TVV1
  sap_field: KDGRP
snapshot_date: 2026-04-26
values:
  - code: "01"
    label: Retail
    status: active
```

### 26.3 Validation rules

| Code | Severity | Rule |
|---|---|---|
| `VLIST_VALUES_EMPTY` | warning/error | Active value list should have values or external source |
| `VLIST_DUPLICATE_CODE` | error | Duplicate value code |
| `VLIST_VALUE_STATUS_INVALID` | error | Invalid value status |
| `VLIST_ATTRIBUTE_REF_BROKEN` | error | Attribute reference broken |
| `VLIST_SOURCE_SYSTEM_BROKEN` | error | Source system reference broken |
| `VLIST_ENV_REF_BROKEN` | error | Environment reference broken |
| `VLIST_NO_SNAPSHOT_DATE` | warning | Imported/config value list should have snapshot date |

---

## 27. ValueMapping schema

### 27.1 Required fields

```yaml
id: VMAP-LEGACY-CUST-GROUP-TO-S4-KDGRP
type: ValueMapping
domain: DOMAIN-CUSTOMER-BP
name: Legacy Customer Group to S/4 KDGRP
source_endpoint: FEP-LEGACY-CUSTOMER-GROUP
target_endpoint: FEP-S4-KNVV-KDGRP
status: active
```

### 27.2 Recommended fields

```yaml
target_value_list: VLIST-S4-KNVV-KDGRP
mappings:
  - source_value: A17
    target_value: "01"
    status: approved
  - source_value: X99
    target_value: null
    status: unresolved
```

### 27.3 Allowed entry statuses

```text
draft
proposed
approved
rejected
unresolved
deprecated
exception
```

### 27.4 Validation rules

| Code | Severity | Rule |
|---|---|---|
| `VMAP_SOURCE_ENDPOINT_BROKEN` | error | Source endpoint reference broken |
| `VMAP_TARGET_ENDPOINT_BROKEN` | error | Target endpoint reference broken |
| `VMAP_TARGET_VLIST_BROKEN` | error | Target value list reference broken |
| `VMAP_ENTRY_DUPLICATE_SOURCE` | warning/error | Duplicate source value without condition |
| `VMAP_TARGET_VALUE_NOT_IN_VLIST` | error | Approved target value missing from target value list |
| `VMAP_APPROVED_ENTRY_WITH_NULL_TARGET` | error | Approved entry cannot have null target unless explicit exception |
| `VMAP_UNRESOLVED_VALUES` | warning | Unresolved mappings exist |
| `VMAP_WITHOUT_OWNER` | warning | Active value mapping should have owner |

---

## 28. BusinessRule schema

### 28.1 Required fields

```yaml
id: RULE-CUST-GROUP-SALES-AREA-REQUIRED
type: BusinessRule
domain: DOMAIN-CUSTOMER-BP
name: Customer Group required for relevant sales areas
statement: Customer Group must be maintained for in-scope customer sales area records where sales process requires customer classification.
status: approved
```

### 28.2 Recommended fields

```yaml
applies_to:
  - ATTR-CUST-SALES-CUSTOMER-GROUP
contexts:
  - CTX-CUSTOMER-SALES-AREA-S4
priority: high
owner: ROLE-SALES-MD-OWNER
```

### 28.3 Validation rules

| Code | Severity | Rule |
|---|---|---|
| `RULE_STATEMENT_MISSING` | error | BusinessRule must have statement |
| `RULE_APPLIES_TO_BROKEN` | error | applies_to reference broken |
| `RULE_CONTEXT_REF_BROKEN` | error | context reference broken |
| `RULE_WITHOUT_OWNER` | warning | Approved rule should have owner |

---

## 29. TransformationLogic schema

### 29.1 Required fields

```yaml
id: LOGIC-CUST-GROUP-DERIVATION
type: TransformationLogic
domain: DOMAIN-CUSTOMER-BP
name: Derive S/4 Customer Group
logic_type: conditional_derivation
status: approved
```

### 29.2 Recommended fields

```yaml
input_endpoints:
  - FEP-LEGACY-CUSTOMER-GROUP
  - FEP-LEGACY-SALES-ORG
output_endpoints:
  - FEP-S4-KNVV-KDGRP
pseudo_logic: |
  if sales_org == "CH01" and legacy_customer_group == "A17":
      target_customer_group = lookup_special_case("CH01", "A17")
  else:
      target_customer_group = lookup(VMAP-LEGACY-CUST-GROUP-TO-S4-KDGRP, legacy_customer_group)
implemented_in:
  - IFACE-LEGACY-CUSTOMER-SALES-EXTRACT
```

### 29.3 Allowed `logic_type`

```text
direct_copy
defaulting
derivation
conditional_derivation
lookup
value_mapping
formatting
normalization
concatenation
split
calculation
manual_enrichment
exception_handling
```

### 29.4 Validation rules

| Code | Severity | Rule |
|---|---|---|
| `LOGIC_TYPE_INVALID` | error | Invalid logic type |
| `LOGIC_INPUT_ENDPOINT_BROKEN` | error | Input endpoint reference broken |
| `LOGIC_OUTPUT_ENDPOINT_BROKEN` | error | Output endpoint reference broken |
| `LOGIC_CONDITIONAL_WITHOUT_DESCRIPTION` | warning/error | Conditional logic should have pseudo_logic or description |
| `LOGIC_IMPLEMENTED_IN_BROKEN` | error | referenced interface/extension broken |
| `LOGIC_WITHOUT_OWNER` | warning | Approved logic should have owner |

---

## 30. ValidationRule schema

### 30.1 Required fields

```yaml
id: VAL-CUST-GROUP-ALLOWED-VALUES
type: ValidationRule
domain: DOMAIN-CUSTOMER-BP
name: Customer Group must be in approved S/4 value list
validation_type: allowed_values
severity: error
status: active
```

### 30.2 Recommended fields

```yaml
attribute: ATTR-CUST-SALES-CUSTOMER-GROUP
field_endpoint: FEP-S4-KNVV-KDGRP
value_list: VLIST-S4-KNVV-KDGRP
failure_message: Customer Group is not in approved S/4 value list.
owner: ROLE-CUSTOMER-BP-STEWARD
```

### 30.3 Allowed `validation_type`

```text
required
allowed_values
format
length
range
regex
unique
referential_integrity
conditional_required
cross_field_consistency
mapping_coverage
value_mapping_coverage
not_deprecated_value
custom
```

### 30.4 Validation rules

| Code | Severity | Rule |
|---|---|---|
| `VAL_TYPE_INVALID` | error | Invalid validation type |
| `VAL_ATTRIBUTE_REF_BROKEN` | error | Attribute reference broken |
| `VAL_ENDPOINT_REF_BROKEN` | error | FieldEndpoint reference broken |
| `VAL_ALLOWED_VALUES_WITHOUT_VLIST` | error | allowed_values validation must reference ValueList |
| `VAL_REGEX_WITHOUT_PATTERN` | error | regex validation must define pattern |
| `VAL_REQUIRED_WITHOUT_SCOPE` | warning | required validation should define scope/context |
| `VAL_WITHOUT_OWNER` | warning | Active validation should have owner |

---

## 31. DataQualityCheck schema

### 31.1 Required fields

```yaml
id: DQ-CHECK-CUST-GROUP-ALLOWED-VALUES
type: DataQualityCheck
validation_rule: VAL-CUST-GROUP-ALLOWED-VALUES
status: active
```

### 31.2 Recommended fields

```yaml
check_engine: pandas
input_dataset: DATASET-CUSTOMER-SALES-AREA-LOAD
column: CUSTOMER_GROUP
check_expression: value in VLIST-S4-KNVV-KDGRP.values.code
severity: error
```

### 31.3 Allowed `check_engine`

```text
manual
pandas
polars
duckdb
sql
python
external
```

### 31.4 Validation rules

| Code | Severity | Rule |
|---|---|---|
| `DQ_VALIDATION_REF_BROKEN` | error | Referenced ValidationRule broken |
| `DQ_ENGINE_INVALID` | error | Invalid check engine |
| `DQ_INPUT_DATASET_BROKEN` | error | Dataset reference broken |
| `DQ_COLUMN_MISSING` | warning/error | Dataset check should define column where applicable |
| `DQ_EXPRESSION_MISSING` | warning | Automated check should define expression or implementation |

---

## 32. OwnershipRole / Person / Team schemas

### 32.1 OwnershipRole required fields

```yaml
id: ROLE-CUSTOMER-BP-STEWARD
type: OwnershipRole
name: Customer BP Data Steward
status: active
```

### 32.2 Recommended fields

```yaml
team: Master Data Governance
responsibilities:
  - Approves customer BP attribute definitions
  - Reviews value mappings
  - Owns validation rules
```

### 32.3 Validation rules

| Code | Severity | Rule |
|---|---|---|
| `OWNER_NAME_MISSING` | error | Role/person/team must have name |
| `OWNER_ROLE_WITHOUT_RESPONSIBILITIES` | warning | Ownership role should define responsibilities |
| `OWNER_REF_BROKEN` | error | Owner reference broken |
| `OWNER_PERSONAL_DATA_REVIEW` | info/warning | Person object may contain personal data; review policy |

---

## 33. Issue schema

### 33.1 Required fields

```yaml
id: ISS-CH01-A17-CONFIG-GAP
type: Issue
domain: DOMAIN-CUSTOMER-BP
title: Customer Group config missing for CH01 / A17
status: open
severity: medium
```

### 33.2 Recommended fields

```yaml
issue_type: configuration_gap
affected_objects:
  - ATTR-CUST-SALES-CUSTOMER-GROUP
  - FEP-S4-KNVV-KDGRP
owners:
  responsible: ROLE-S4-SD-FUNCTIONAL
  accountable: ROLE-SALES-MD-OWNER
```

### 33.3 Allowed `severity`

```text
low
medium
high
critical
```

### 33.4 Allowed `issue_type`

```text
mapping_gap
value_mapping_gap
configuration_gap
validation_gap
ownership_gap
dataset_gap
source_data_issue
target_data_issue
interface_issue
decision_needed
documentation_gap
other
```

### 33.5 Validation rules

| Code | Severity | Rule |
|---|---|---|
| `ISS_TITLE_MISSING` | error | Issue must have title |
| `ISS_SEVERITY_INVALID` | error | Invalid severity |
| `ISS_TYPE_INVALID` | error | Invalid issue type |
| `ISS_AFFECTED_OBJECT_BROKEN` | error | Affected object reference broken |
| `ISS_WITHOUT_AFFECTED_OBJECTS` | warning | Issue should link affected objects |
| `ISS_HIGH_WITHOUT_OWNER` | warning/error | High/critical issue should have responsible owner |

---

## 34. Risk schema

### 34.1 Required fields

```yaml
id: RISK-CUST-GROUP-CUTOVER-VALIDATION
type: Risk
domain: DOMAIN-CUSTOMER-BP
title: Customer Group validation gap may affect cutover readiness
severity: high
status: open
```

### 34.2 Recommended fields

```yaml
probability: medium
impact: high
affected_objects:
  - ATTR-CUST-SALES-CUSTOMER-GROUP
mitigation:
  - Re-run value mapping coverage.
  - Confirm S/4 customizing.
owner: ROLE-CUSTOMER-BP-STEWARD
```

### 34.3 Validation rules

| Code | Severity | Rule |
|---|---|---|
| `RISK_SEVERITY_INVALID` | error | Invalid risk severity |
| `RISK_WITHOUT_MITIGATION` | warning | Open high/critical risk should have mitigation |
| `RISK_AFFECTED_OBJECT_BROKEN` | error | Affected object reference broken |
| `RISK_HIGH_WITHOUT_OWNER` | warning/error | High risk should have owner |

---

## 35. Decision schema

### 35.1 Required fields

```yaml
id: DEC-CH01-A17-CUSTOMER-GROUP
type: Decision
domain: DOMAIN-CUSTOMER-BP
title: Special Customer Group handling for CH01 / A17
status: accepted
```

### 35.2 Recommended fields

```yaml
decision_date: 2026-04-26
related_attributes:
  - ATTR-CUST-SALES-CUSTOMER-GROUP
related_mappings:
  - MAP-CUST-GROUP-LEGACY-TO-KNVV-KDGRP
related_issues:
  - ISS-CH01-A17-CONFIG-GAP
```

### 35.3 Allowed `status`

```text
proposed
accepted
rejected
superseded
deprecated
```

### 35.4 Validation rules

| Code | Severity | Rule |
|---|---|---|
| `DEC_TITLE_MISSING` | error | Decision must have title |
| `DEC_STATUS_INVALID` | error | Invalid decision status |
| `DEC_WITHOUT_RELATED_OBJECTS` | warning | Decision should link affected objects |
| `DEC_WITHOUT_RATIONALE` | warning | Decision body should include rationale |
| `DEC_RELATED_OBJECT_BROKEN` | error | Related object reference broken |

---

## 36. ChangeRequest schema

### 36.1 Required fields

```yaml
id: CR-0021
type: ChangeRequest
domain: DOMAIN-CUSTOMER-BP
title: Update Customer Group handling for CH01 / A17
status: approved
```

### 36.2 Recommended fields

```yaml
change_type: mapping_and_validation_update
priority: medium
requested_by: ROLE-CUSTOMER-MIGRATION
approved_by:
  - ROLE-CUSTOMER-BP-STEWARD
  - ROLE-S4-SD-FUNCTIONAL
affected_objects:
  - ATTR-CUST-SALES-CUSTOMER-GROUP
  - FEP-S4-KNVV-KDGRP
  - VMAP-LEGACY-CUST-GROUP-TO-S4-KDGRP
related_issues:
  - ISS-CH01-A17-CONFIG-GAP
related_decisions:
  - DEC-CH01-A17-CUSTOMER-GROUP
created_at: 2026-04-26
approved_at: 2026-04-26
```

### 36.3 Allowed `change_type`

```text
attribute_update
mapping_update
value_mapping_update
validation_update
logic_update
owner_update
scope_change
configuration_update
issue_resolution
documentation_update
import_update
other
```

### 36.4 Validation rules

| Code | Severity | Rule |
|---|---|---|
| `CR_TITLE_MISSING` | error | ChangeRequest must have title |
| `CR_STATUS_INVALID` | error | Invalid ChangeRequest status |
| `CR_WITHOUT_AFFECTED_OBJECTS` | error/warning | Approved ChangeRequest must have affected objects |
| `CR_APPROVED_WITHOUT_APPROVER` | error/warning | Approved ChangeRequest should have approved_by |
| `CR_APPROVED_WITHOUT_REASON` | warning | Approved ChangeRequest should link issue, decision, or evidence |
| `CR_AFFECTED_OBJECT_BROKEN` | error | Affected object reference broken |

---

## 37. PatchProposal schema

### 37.1 Required fields

```yaml
id: PATCH-0021
type: PatchProposal
status: pending_review
created_by: ai
```

### 37.2 Recommended fields

```yaml
domain: DOMAIN-CUSTOMER-BP
source_evidence:
  - EV-EMAIL-20260426-CH01-A17
proposed_change_request: CR-0021
affected_objects:
  - ATTR-CUST-SALES-CUSTOMER-GROUP
  - VMAP-LEGACY-CUST-GROUP-TO-S4-KDGRP
created_at: 2026-04-26
validation_status: pending
```

### 37.3 Allowed `created_by`

```text
user
ai
importer
system
```

### 37.4 Validation rules

| Code | Severity | Rule |
|---|---|---|
| `PATCH_STATUS_INVALID` | error | Invalid patch status |
| `PATCH_WITHOUT_SOURCE` | warning/error | AI/import patch should have source evidence |
| `PATCH_AFFECTED_OBJECT_BROKEN` | error | Affected object reference broken |
| `PATCH_DIRECT_WRITE_NOT_ALLOWED` | error | Patch attempts to bypass proposal workflow |
| `PATCH_APPROVAL_WITH_ERRORS` | error | Patch cannot be approved with validation errors |
| `PATCH_APPROVED_WITHOUT_CR` | warning/error | Accepted patch should create/update ChangeRequest |

---

## 38. Evidence schema

### 38.1 Required fields

```yaml
id: EV-EMAIL-20260426-CH01-A17
type: Evidence
domain: DOMAIN-CUSTOMER-BP
evidence_type: email_summary
status: active
```

### 38.2 Recommended fields

```yaml
source_system: Outlook
source_date: 2026-04-26
related_objects:
  - ISS-CH01-A17-CONFIG-GAP
  - ATTR-CUST-SALES-CUSTOMER-GROUP
```

### 38.3 Allowed `evidence_type`

```text
email_summary
ticket
workshop_note
meeting_note
confluence_page
screenshot_reference
sap_config_export
excel_file
validation_report
chat_summary
other
```

### 38.4 Validation rules

| Code | Severity | Rule |
|---|---|---|
| `EV_TYPE_INVALID` | error | Invalid evidence type |
| `EV_WITHOUT_RELATED_OBJECTS` | warning | Evidence should link to object/issue/decision/change |
| `EV_RAW_SENSITIVE_CONTENT` | warning | Evidence may contain sensitive raw content |
| `EV_SOURCE_DATE_INVALID` | warning | Invalid source date |

---

## 39. SAP-specific validation rules

SAP-specific validation is critical.

### 39.1 KNVV validation

If:

```yaml
endpoint_type: sap_table_field
sap_table: KNVV
```

Then:

```text
entity_context must reference a context with category customer_sales_area.
grain should include KUNNR, VKORG, VTWEG, SPART.
```

Validation codes:

| Code | Severity | Rule |
|---|---|---|
| `SAP_CONTEXT_KNVV_REQUIRES_SALES_AREA` | error | KNVV endpoint must use Customer Sales Area context |
| `SAP_CONTEXT_KNVV_GRAIN_INCOMPLETE` | warning/error | KNVV grain should include customer + sales area keys |

### 39.2 KNB1 validation

If:

```yaml
sap_table: KNB1
```

Then:

```text
entity_context must be customer_company_code.
grain should include KUNNR and BUKRS.
```

Codes:

| Code | Severity | Rule |
|---|---|---|
| `SAP_CONTEXT_KNB1_REQUIRES_COMPANY_CODE` | error | KNB1 endpoint must use Customer Company Code context |
| `SAP_CONTEXT_KNB1_GRAIN_INCOMPLETE` | warning/error | KNB1 grain should include customer + company code |

### 39.3 KNVP validation

If:

```yaml
sap_table: KNVP
```

Then:

```text
entity_context must be customer_partner_function.
```

Code:

```text
SAP_CONTEXT_KNVP_REQUIRES_PARTNER_FUNCTION
```

### 39.4 BUT000 validation

If:

```yaml
sap_table: BUT000
```

Then:

```text
entity_context should be bp_central.
```

Code:

```text
SAP_CONTEXT_BUT000_REQUIRES_BP_CENTRAL
```

### 39.5 Address/contact validation

For address/contact related tables such as:

```text
BUT020
ADRC
ADR6
```

Context should be address/contact, not generic central customer context.

Code:

```text
SAP_CONTEXT_ADDRESS_REQUIRES_ADDRESS_CONTEXT
```

### 39.6 BP role validation

BP role must not be used as physical storage.

Invalid:

```yaml
endpoint_type: sap_table_field
sap_table: FLCU01
```

Correct:

```yaml
maintenance_context:
  sap_roles:
    - SAPROLE-FLCU01
```

Code:

```text
SAP_ROLE_NOT_PHYSICAL_STORAGE
```

### 39.7 Same concept in multiple SAP contexts

If one Attribute is linked to multiple SAP contexts, the system should require separate AttributeUsage objects.

Code:

```text
ATTR_MULTI_CONTEXT_REQUIRES_USAGE
```

If two endpoints have same technical field name but different context, do not automatically merge.

Code:

```text
FEP_SAME_FIELD_DIFFERENT_CONTEXT_REVIEW
```

---

## 40. Mapping and value validation

### 40.1 Mapping coverage checks

Checks:

```text
Every in-scope target endpoint should have mapping or explicit default/manual/out_of_scope rule.
Every active mapping should have valid source and target endpoints.
Every value_mapped mapping should reference ValueMapping.
Every derived/conditional mapping should reference TransformationLogic.
```

Codes:

```text
MAPPING_TARGET_WITHOUT_SOURCE
MAPPING_VALUE_MAPPED_WITHOUT_VMAP
MAPPING_DERIVED_WITHOUT_LOGIC
MAPPING_TARGET_ENDPOINT_UNMAPPED
MAPPING_SOURCE_ENDPOINT_UNUSED
```

### 40.2 Value list checks

Checks:

```text
ValueList has unique codes.
ValueList codes have statuses.
Imported ValueList has source and snapshot date.
Environment-specific ValueList references environment.
```

Codes:

```text
VLIST_DUPLICATE_CODE
VLIST_VALUE_STATUS_INVALID
VLIST_NO_SOURCE
VLIST_NO_SNAPSHOT_DATE
```

### 40.3 Value mapping checks

Checks:

```text
Approved target value exists in target ValueList.
Approved entry cannot have null target unless exception.
Source values observed in dataset should be mapped or explicitly unresolved/exception.
Deprecated target values should not be used by active mappings.
```

Codes:

```text
VMAP_TARGET_VALUE_NOT_IN_VLIST
VMAP_APPROVED_ENTRY_WITH_NULL_TARGET
VMAP_SOURCE_VALUE_UNMAPPED
VMAP_TARGET_VALUE_DEPRECATED
VMAP_DUPLICATE_SOURCE_WITHOUT_CONDITION
```

---

## 41. Dataset and gap validation

Dataset validation compares profiled datasets with model definitions.

### 41.1 Dataset column matching

Checks:

```text
Dataset column has matching FieldEndpoint.
Dataset column can be linked to Attribute.
Required model endpoint exists in dataset.
Unexpected dataset column is reviewed.
```

Codes:

```text
DATASET_COLUMN_UNKNOWN
DATASET_COLUMN_WITHOUT_ENDPOINT
DATASET_REQUIRED_COLUMN_MISSING
DATASET_COLUMN_AMBIGUOUS_MATCH
```

### 41.2 Dataset value checks

Checks:

```text
Observed source values exist in ValueMapping.
Observed target values exist in ValueList.
Blank values comply with requiredness rules.
Format complies with ValidationRule.
```

Codes:

```text
DATASET_VALUE_UNMAPPED
DATASET_VALUE_NOT_IN_VLIST
DATASET_REQUIRED_VALUE_BLANK
DATASET_VALUE_FORMAT_INVALID
DATASET_VALUE_LENGTH_INVALID
```

### 41.3 Dataset profiling checks

Checks:

```text
Profile exists.
Profile is not stale.
Row count available.
Column count available.
Distinct values available for mapped value fields.
```

Codes:

```text
DATASET_PROFILE_MISSING
DATASET_PROFILE_STALE
DATASET_PROFILE_INCOMPLETE
```

---

## 42. Ownership validation

Ownership is important for governance and AMS handover.

### 42.1 Checks

```text
Active Attribute should have owner/steward.
Active Mapping should have owner.
Active ValueMapping should have owner.
Active ValidationRule should have owner.
High/critical Issue should have responsible owner.
Approved ChangeRequest should have approver.
```

Codes:

```text
OWNER_MISSING_ATTRIBUTE
OWNER_MISSING_MAPPING
OWNER_MISSING_VALUE_MAPPING
OWNER_MISSING_VALIDATION
OWNER_MISSING_HIGH_ISSUE
OWNER_MISSING_CHANGE_APPROVER
OWNER_REF_BROKEN
```

### 42.2 Strictness

Recommended MVP behavior:

```text
missing owner = warning
missing owner on high-risk/critical object = error or high warning
```

Config should control strictness.

---

## 43. Change governance validation

### 43.1 Checks

```text
Approved model changes should link to ChangeRequest.
ChangeRequest should have affected objects.
ChangeRequest should link issue, decision, or evidence.
Accepted PatchProposal should link to ChangeRequest.
Decision should link related objects.
Issue should link affected objects.
```

Codes:

```text
CHANGE_WITHOUT_CR
CR_WITHOUT_AFFECTED_OBJECTS
CR_WITHOUT_REASON
PATCH_ACCEPTED_WITHOUT_CR
DECISION_WITHOUT_RELATED_OBJECTS
ISSUE_WITHOUT_AFFECTED_OBJECTS
```

### 43.2 Git-aware validation

Optional Git checks:

```text
Repository has uncommitted changes.
Patch apply would modify files already changed.
Generated index is older than latest canonical file.
```

Codes:

```text
GIT_WORKTREE_DIRTY
PATCH_CONFLICT_WITH_UNCOMMITTED_CHANGE
INDEX_OUTDATED
```

---

## 44. AI patch validation

AI output must be treated as untrusted until validated.

### 44.1 AI output checks

```text
AI output is valid JSON/structured format.
Proposed action is allowed.
Affected object IDs exist or new object IDs are valid.
Object type is allowed.
Required fields are present.
References resolve.
No direct model write is requested.
Patch has source evidence or user input.
Confidence and assumptions are visible.
```

Codes:

```text
AI_OUTPUT_INVALID_JSON
AI_ACTION_NOT_ALLOWED
AI_OBJECT_TYPE_INVALID
AI_OBJECT_ID_INVALID
AI_REFERENCE_BROKEN
AI_PATCH_MISSING_SOURCE
AI_PATCH_DIRECT_WRITE_ATTEMPT
AI_PATCH_ASSUMPTION_NOT_MARKED
AI_PATCH_LOW_CONFIDENCE_REQUIRES_REVIEW
```

### 44.2 Allowed AI actions

MVP allowed actions:

```text
create_issue
create_decision_draft
create_change_request_draft
update_attribute_draft
update_mapping_draft
update_value_mapping_draft
update_validation_draft
create_evidence_summary
generate_report
```

Disallowed actions:

```text
approve_change
delete_approved_object
write_directly_to_active_model
mark_validation_passed_without_run
modify_generated_index_as_source
```

### 44.3 Patch approval gates

A patch can be approved only if:

```text
PatchProposal status is pending_review.
Patch has source evidence or user-supplied source text.
All proposed object schemas are valid.
References resolve.
No blocking SAP context errors exist.
No mapping/value-list errors exist for proposed changes.
Patch links to or creates ChangeRequest.
User explicitly approves.
```

---

## 45. Repository health scoring

Repository health should summarize validation state.

### 45.1 Suggested score dimensions

```text
schema_health
reference_health
sap_context_health
mapping_health
value_mapping_health
validation_coverage
ownership_coverage
dataset_alignment
change_governance
ai_patch_safety
```

### 45.2 Score example

```json
{
  "overall_status": "degraded",
  "errors": 3,
  "warnings": 18,
  "dimensions": {
    "schema_health": "ok",
    "reference_health": "degraded",
    "sap_context_health": "failed",
    "mapping_health": "degraded",
    "ownership_coverage": "degraded"
  }
}
```

### 45.3 Status levels

```text
healthy
degraded
failed
unknown
```

---

## 46. Validation pipeline execution

Recommended CLI/API flow:

```text
1. Parse files.
2. Build object registry.
3. Run common schema validation.
4. Run type-specific validation.
5. Run reference validation.
6. Run lifecycle validation.
7. Run SAP context validation.
8. Run mapping/value validation.
9. Run dataset/gap validation if profiles exist.
10. Run governance validation.
11. Run AI patch validation if patches exist.
12. Write generated validation results.
13. Generate repository health report.
```

CLI:

```bash
modelops validate
modelops validate --strict
modelops validate --object FEP-S4-KNVV-KDGRP
modelops validate --patch PATCH-0021
```

API:

```text
POST /api/repository/validate
POST /api/patch-proposals/{id}/validate
GET  /api/repository/health
```

---

## 47. Validation configuration

`modelops.config.yaml` should control validation strictness.

Example:

```yaml
validation:
  mode: standard
  block_patch_approval_on_errors: true

  strictness:
    missing_owner: warning
    missing_validation: warning
    attribute_without_usage: warning
    active_refs_retired: error
    approved_refs_draft: error

  sap_context_rules:
    enabled: true
    knvv_requires_sales_area: error
    knb1_requires_company_code: error
    knvp_requires_partner_function: error
    bp_role_as_storage: error

  datasets:
    profile_stale_after_days: 14
    unknown_column: warning
    required_column_missing: error
    unmapped_value: warning

  ai:
    require_source_evidence: true
    require_patch_review: true
    allow_direct_model_write: false
```

Modes:

```text
relaxed
standard
strict
```

Recommended MVP default:

```text
standard
```

---

## 48. Error code naming convention

Use uppercase snake case.

Recommended format:

```text
{AREA}_{SPECIFIC_PROBLEM}
```

Examples:

```text
SCHEMA_REQUIRED_FIELD_MISSING
REFERENCE_BROKEN
SAP_CONTEXT_KNVV_REQUIRES_SALES_AREA
VMAP_TARGET_VALUE_NOT_IN_VLIST
DATASET_COLUMN_UNKNOWN
PATCH_DIRECT_WRITE_NOT_ALLOWED
```

Areas:

```text
FILE
SCHEMA
ID
STATUS
REFERENCE
LIFECYCLE
SAP_CONTEXT
ATTR
FEP
MAP
VMAP
VLIST
VAL
DQ
DATASET
OWNER
ISS
DEC
CR
PATCH
AI
GIT
INDEX
```

---

## 49. Suggested Pydantic model structure

Suggested backend schema layout:

```text
schemas/
  base.py
  enums.py
  domain.py
  migration_object.py
  entity.py
  entity_context.py
  attribute.py
  attribute_usage.py
  system.py
  sap_object.py
  field_endpoint.py
  interface.py
  dataset.py
  mapping.py
  value_list.py
  value_mapping.py
  rule.py
  logic.py
  validation.py
  quality_check.py
  owner.py
  issue.py
  risk.py
  decision.py
  change_request.py
  patch.py
  evidence.py
  validation_result.py
```

Base model fields:

```python
class BaseModelObject(BaseModel):
    id: str
    type: str
    status: str
    domain: str | None = None
    name: str | None = None
    title: str | None = None
    description: str | None = None
```

Use type-specific subclasses.

---

## 50. Generated JSON Schema

The system should generate JSON Schema files for documentation and tooling.

Output:

```text
schemas/json-schema/Attribute.schema.json
schemas/json-schema/FieldEndpoint.schema.json
schemas/json-schema/Mapping.schema.json
schemas/json-schema/ValueMapping.schema.json
schemas/json-schema/ValidationRule.schema.json
```

Use cases:

- frontend form validation;
- editor autocomplete later;
- documentation;
- AI output validation;
- import validation.

---

## 51. Testing strategy

### 51.1 Required unit tests

```text
parse valid frontmatter
reject invalid YAML
detect duplicate ID
validate common fields
validate each object type
detect broken reference
detect invalid status
detect invalid enum value
```

### 51.2 SAP context tests

```text
KNVV endpoint with Customer Sales Area context passes.
KNVV endpoint with BP Central context fails.
KNB1 endpoint with Company Code context passes.
KNB1 endpoint with Sales Area context fails.
BP role used as physical storage fails.
KNVP endpoint without Partner Function context fails.
```

### 51.3 Mapping/value tests

```text
ValueMapping target value exists in ValueList passes.
ValueMapping target value missing in ValueList fails.
Approved mapping with draft logic fails.
value_mapped mapping without ValueMapping warns/fails.
Duplicate source value without condition warns/fails.
```

### 51.4 Dataset/gap tests

```text
Unknown dataset column creates warning.
Required dataset column missing creates error.
Observed source value without mapping creates warning.
Observed target value not in ValueList creates error.
Blank required value creates error.
```

### 51.5 Patch tests

```text
AI PatchProposal with valid changes passes validation.
PatchProposal with broken reference fails.
PatchProposal attempting direct write fails.
Patch cannot be approved with errors.
Patch approval creates/updates ChangeRequest.
Rejected patch does not modify canonical files.
```

---

## 52. Minimal MVP validation set

For MVP, implement these first:

```text
file parsing
ID uniqueness
object type validation
required common fields
status validation
reference validation
Attribute schema
AttributeUsage schema
EntityContext schema
FieldEndpoint schema
Mapping schema
ValueList schema
ValueMapping schema
ValidationRule schema
Issue schema
Decision schema
ChangeRequest schema
PatchProposal schema
KNVV sales-area rule
KNB1 company-code rule
ValueMapping target value in ValueList check
Attribute without owner warning
Attribute without validation warning
Patch cannot approve with errors
```

Do not start with every advanced rule. Build a strict useful core first.

---

## 53. Validation examples

### 53.1 Invalid KNVV context

Object:

```yaml
id: FEP-S4-KNVV-KDGRP
type: FieldEndpoint
endpoint_type: sap_table_field
sap_table: KNVV
sap_field: KDGRP
entity_context: CTX-BP-CENTRAL-S4
```

Validation result:

```json
{
  "severity": "error",
  "code": "SAP_CONTEXT_KNVV_REQUIRES_SALES_AREA",
  "message": "KNVV field endpoint must use Customer Sales Area context.",
  "object_id": "FEP-S4-KNVV-KDGRP",
  "field_path": "entity_context",
  "suggested_fix": "Use CTX-CUSTOMER-SALES-AREA-S4."
}
```

### 53.2 ValueMapping target value missing

Object:

```yaml
target_value_list: VLIST-S4-KNVV-KDGRP
mappings:
  - source_value: A17
    target_value: "99"
    status: approved
```

If `"99"` is not in the ValueList:

```json
{
  "severity": "error",
  "code": "VMAP_TARGET_VALUE_NOT_IN_VLIST",
  "message": "Approved target value 99 is not present in VLIST-S4-KNVV-KDGRP.",
  "object_id": "VMAP-LEGACY-CUST-GROUP-TO-S4-KDGRP"
}
```

### 53.3 AI patch direct write attempt

```json
{
  "severity": "error",
  "code": "PATCH_DIRECT_WRITE_NOT_ALLOWED",
  "message": "AI patch attempts to directly modify active model files without review.",
  "object_id": "PATCH-0021"
}
```

---

## 54. Product quality bar

The validation system is good enough when it can prevent these mistakes:

```text
Treating KNVV field as central BP attribute.
Using BP role as physical storage.
Approving value mapping to target value not present in S/4 value list.
Using draft logic inside approved mapping.
Changing model files without ChangeRequest.
Letting AI directly update approved objects.
Ignoring unmapped source values in migration dataset.
Having active critical attributes without owner or validation.
```

The validation system is not good enough if it only checks YAML syntax.

---

## 55. Final recommendation

Build the schema and validation layer as a first-class product capability.

Recommended implementation order:

```text
1. Common schema and object registry.
2. Type-specific Pydantic models.
3. Reference resolver.
4. ValidationResult format and error codes.
5. SAP context validators.
6. Mapping/value validators.
7. Dataset/gap validators.
8. Governance validators.
9. PatchProposal validators.
10. Repository health report.
11. JSON Schema export.
12. Test suite.
```

This validation layer is not internal plumbing only. It is part of the product value.

It allows the product to say:

```text
Your SAP migration model is structured.
Your field contexts are correct.
Your mappings are traceable.
Your value mappings are checked.
Your validation gaps are visible.
Your ownership gaps are visible.
Your AI updates are reviewable and safe.
```

That is the operational value of ModelOps for MDM.
