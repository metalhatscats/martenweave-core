# ModelOps for MDM — Model Repository Specification

Version: 0.6.1
Document type: Repository architecture / canonical model storage specification  
Scope: File-based canonical model repository for SAP migration, MDM, data governance, and AMS model knowledge  
Initial domain: SAP Business Partner migration model, Customer role slice first  
Repository style: Human-readable, Git-friendly, AI-ready, Obsidian-compatible, product-owned

---

## 1. Purpose

The ModelOps for MDM repository is the canonical source of truth for structured model knowledge.

## MVP Repository Boundary

The P0 repository only needs enough canonical files to prove the Customer Group / `KNVV-KDGRP` workflow.

Required P0 canonical areas:

```text
model/domains/
model/migration-objects/
model/entities/
model/entity-contexts/
model/attributes/
model/attribute-usages/
model/systems/
model/system-environments/
model/sap-objects/
model/field-endpoints/
model/datasets/
model/mappings/
model/value-lists/
model/value-mappings/
model/validations/
model/quality-checks/
model/owners/
model/issues/
model/decisions/
model/change-requests/
model/patch-proposals/
model/evidence/
generated/
schemas/
templates/
modelops.config.yaml
```

Do not add hosted workspace, connector, PR automation, or enterprise workflow folders to the MVP repository unless a P0 workflow requires a local placeholder.

It stores the model knowledge around SAP master data, not the master data records themselves.

The repository should capture:

- master data domains;
- migration objects;
- business entities;
- entity contexts;
- business attributes;
- attribute usages;
- physical field representations;
- systems and environments;
- SAP tables, fields, roles, APIs, reports, and interfaces;
- datasets and dataset profiles;
- mappings;
- value lists;
- value mappings;
- transformation logic;
- business rules;
- validation rules;
- executable or semi-executable quality checks;
- ownership and stewardship;
- issues;
- risks;
- decisions;
- evidence;
- change requests;
- AI patch proposals;
- generated indexes and reports.

The repository must make SAP migration model knowledge:

```text
structured
traceable
reviewable
versioned
validated
searchable
AI-ready
safe to change
useful for AMS handover
```

---

## 2. Repository positioning

The repository is not:

- a replacement for SAP MDG;
- a replacement for SAP S/4HANA;
- a replacement for enterprise MDM;
- a replacement for Jira or Confluence;
- a replacement for an enterprise data catalog;
- a database of SAP master data records;
- a raw data lake;
- an AI memory dump.

The repository is:

```text
A file-based operational model layer for SAP migration and AMS knowledge.
```

It keeps the knowledge around fields, mappings, rules, validations, ownership, decisions, and changes.

---

## 3. Core repository principle

The canonical model should be stored in small, typed, human-readable files.

Recommended rule:

```text
One governed model object = one canonical file.
```

Examples:

```text
One Attribute = one file.
One FieldEndpoint = one file.
One Mapping = one file.
One ValueMapping = one file.
One ValidationRule = one file.
One Issue = one file.
One Decision = one file.
One ChangeRequest = one file.
One PatchProposal = one file.
```

Bulk import and staging files may temporarily contain many objects, but approved canonical objects should be split into individual files.

---

## 4. Canonical vs generated layers

### 4.1 Canonical layer

Canonical files are the source of truth.

They live under:

```text
model/
```

They are:

- manually reviewable;
- Git-diffable;
- validated by schema;
- linked by stable IDs;
- safe to inspect without the product UI;
- optionally readable in Obsidian or VS Code.

### 4.2 Generated layer

Generated artifacts are rebuilt from canonical files.

They live under:

```text
generated/
```

They may include:

```text
generated/modelops.db
generated/search_documents.jsonl
generated/lineage_edges.jsonl
generated/validation_results.jsonl
generated/audit_events.jsonl
generated/reports/
```

Generated files are not the source of truth.

They can be deleted and rebuilt.

### 4.3 Raw data layer

Raw datasets should usually not be committed into the canonical repository.

They may live under:

```text
data/raw/
data/samples/
```

Rules:

```text
data/raw/       local or ignored by Git by default
data/samples/   small demo/sample files may be committed
```

---

## 5. Recommended top-level repository structure

```text
modelops-mdm/
  model/
    domains/
    migration-objects/
    entities/
    entity-contexts/
    attributes/
    attribute-usages/
    systems/
    system-environments/
    sap-objects/
    field-endpoints/
    interfaces/
    datasets/
    mappings/
    value-lists/
    value-mappings/
    rules/
    logic/
    validations/
    quality-checks/
    owners/
    issues/
    risks/
    decisions/
    change-requests/
    patch-proposals/
    evidence/

  imports/
    raw/
    parsed/
    proposed/
    reports/

  data/
    raw/
    processed/
    samples/

  generated/
    modelops.db
    search_documents.jsonl
    lineage_edges.jsonl
    validation_results.jsonl
    audit_events.jsonl
    reports/

  schemas/
    json-schema/
    examples/

  templates/
    domain.md
    migration-object.md
    entity.md
    entity-context.md
    attribute.md
    attribute-usage.md
    system.md
    field-endpoint.md
    mapping.md
    value-list.md
    value-mapping.md
    validation-rule.md
    issue.md
    decision.md
    change-request.md
    patch-proposal.md
    evidence.md

  docs/
    README.md

  modelops.config.yaml
  README.md
  .gitignore
```

---

## 6. Folder responsibilities

| Folder | Responsibility |
|---|---|
| `model/` | Canonical model objects |
| `imports/` | Temporary import/staging area for parsed Excel/CSV/notes |
| `data/` | Raw, processed, or sample datasets |
| `generated/` | Rebuildable database, indexes, reports, audit events |
| `schemas/` | JSON Schema exports, schema examples, validation references |
| `templates/` | Object templates for manual creation |
| `docs/` | Repository-specific documentation |
| `modelops.config.yaml` | Workspace configuration |

---

## 7. File format standard

### 7.1 Default format

Default canonical object format:

```text
Markdown file with YAML frontmatter
```

Example:

```markdown
---
id: ATTR-CUST-SALES-CUSTOMER-GROUP
type: Attribute
domain: DOMAIN-CUSTOMER-BP
name: Customer Group
status: active
---

# Customer Group

Sales-area-dependent customer grouping used for SAP sales processes and reporting.
```

### 7.2 Why Markdown + YAML frontmatter

Use this format because it is:

- readable in plain text;
- Git-friendly;
- Obsidian-friendly;
- suitable for human explanations;
- structured enough for schema validation;
- good for AI context generation;
- simple to edit manually.

### 7.3 When to use YAML-only

YAML-only files may be used for:

- workspace config;
- strict structured fixtures;
- large but manageable value lists;
- schema examples;
- generated exports if needed.

Example:

```text
modelops.config.yaml
schemas/examples/attribute.example.yaml
```

### 7.4 When to use JSON

JSON should mostly be generated/API-facing.

Use JSON for:

- API payloads;
- generated normalized objects;
- JSON Schema;
- machine-to-machine exchange.

Do not make JSON the default hand-authored canonical format unless there is a strong reason.

### 7.5 When to use JSONL

JSONL is useful for generated line-based artifacts:

```text
generated/search_documents.jsonl
generated/lineage_edges.jsonl
generated/validation_results.jsonl
generated/audit_events.jsonl
```

---

## 8. Object identity rules

Every canonical object must have a stable ID.

### 8.1 ID properties

Object IDs must be:

```text
globally unique inside repository
stable over time
human-readable
safe for file names
safe for URLs
independent from file path
```

### 8.2 Allowed ID characters

Recommended:

```text
A-Z
0-9
-
```

Avoid:

```text
spaces
slashes
special characters
non-ASCII characters
environment-specific prefixes unless needed
```

### 8.3 ID reuse

Do not reuse IDs after deletion or retirement.

If an object is no longer used, mark it:

```text
deprecated
retired
superseded
```

Do not silently replace it with a different meaning.

---

## 9. ID prefixes

Recommended prefixes:

```text
DOMAIN-     MasterDataDomain
MIGOBJ-     MigrationObject
ENTITY-     BusinessEntity
CTX-        EntityContext
ATTR-       Attribute
USE-        AttributeUsage
SYS-        System
ENV-        SystemEnvironment
SAP-        SAPObject
FEP-        FieldEndpoint
IFACE-      Interface
DATASET-    Dataset
MAPSET-     MappingSet
MAP-        Mapping
VLIST-      ValueList
VMAP-       ValueMapping
RULE-       BusinessRule
LOGIC-      TransformationLogic
VAL-        ValidationRule
DQ-         DataQualityCheck
ROLE-       OwnershipRole
PERSON-     Person
TEAM-       Team
ISS-        Issue
RISK-       Risk
DEC-        Decision
CR-         ChangeRequest
PATCH-      PatchProposal
EV-         Evidence
REPORT-     Generated or controlled report metadata
```

Examples:

```text
DOMAIN-CUSTOMER-BP
MIGOBJ-CUSTOMER-BP
ENTITY-CUSTOMER-SALES-AREA
CTX-CUSTOMER-SALES-AREA-S4
ATTR-CUST-SALES-CUSTOMER-GROUP
USE-CUST-SALES-CUSTOMER-GROUP-S4
SYS-S4HANA
ENV-S4-RS4
SAPTABLE-KNVV
SAPROLE-FLCU01
FEP-S4-KNVV-KDGRP
MAP-CUST-GROUP-LEGACY-TO-KNVV-KDGRP
VMAP-LEGACY-CUST-GROUP-TO-S4-KDGRP
VAL-CUST-GROUP-ALLOWED-VALUES
ISS-CH01-A17-CONFIG-GAP
DEC-CH01-A17-CUSTOMER-GROUP
CR-0021
PATCH-0021
EV-EMAIL-20260426-CH01-A17
```

---

## 10. File naming convention

File names should start with object ID.

Recommended:

```text
{OBJECT-ID}.md
```

or, when readability helps:

```text
{OBJECT-ID}-{short-slug}.md
```

Examples:

```text
ATTR-CUST-SALES-CUSTOMER-GROUP.md
FEP-S4-KNVV-KDGRP.md
MAP-CUST-GROUP-LEGACY-TO-KNVV-KDGRP.md
VMAP-LEGACY-CUST-GROUP-TO-S4-KDGRP.md
VAL-CUST-GROUP-ALLOWED-VALUES.md
ISS-CH01-A17-CONFIG-GAP.md
DEC-CH01-A17-CUSTOMER-GROUP.md
CR-0021-CUSTOMER-GROUP-CH01-A17.md
```

Rules:

```text
File name may change.
Object ID should not change.
Parser must use frontmatter id, not file name, as source of identity.
```

---

## 11. Common frontmatter fields

Every canonical object must include:

```yaml
id: ATTR-CUST-SALES-CUSTOMER-GROUP
type: Attribute
status: active
```

Most objects should include:

```yaml
domain: DOMAIN-CUSTOMER-BP
name: Customer Group
description: Sales-area-dependent customer grouping used in sales processes and reporting.
owners:
  accountable: ROLE-SALES-MD-OWNER
  responsible: ROLE-CUSTOMER-BP-STEWARD
```

For issue/decision/change objects, use `title` instead of or in addition to `name`.

Example:

```yaml
id: ISS-CH01-A17-CONFIG-GAP
type: Issue
title: Customer Group config missing for CH01 / A17
status: open
```

---

## 12. Lifecycle statuses

### 12.1 General object statuses

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

### 12.2 Issue statuses

```text
open
in_progress
blocked
resolved
closed
rejected
```

### 12.3 PatchProposal statuses

```text
pending_review
accepted
rejected
superseded
```

### 12.4 ChangeRequest statuses

```text
draft
under_review
approved
implemented
rejected
cancelled
```

### 12.5 Dataset statuses

```text
registered
profiled
validated
failed_validation
archived
```

### 12.6 Migration-specific statuses

```text
in_scope
out_of_scope
to_be_confirmed
blocked
ready_for_load
loaded
validated
failed_validation
accepted_for_cutover
ams_handover_ready
```

---

## 13. Common lifecycle block

Optional but recommended:

```yaml
lifecycle:
  status: active
  created_at: 2026-04-26
  created_by: ROLE-CUSTOMER-MIGRATION
  approved_at: 2026-04-27
  approved_by:
    - ROLE-CUSTOMER-BP-STEWARD
  effective_from: 2026-05-01
  deprecated_at: null
  retired_at: null
```

If both top-level `status` and `lifecycle.status` exist, they must match or validation should warn.

---

## 14. Relationship reference rules

Relationships must use stable object IDs.

Correct:

```yaml
related_attributes:
  - ATTR-CUST-SALES-CUSTOMER-GROUP
```

Incorrect:

```yaml
related_attributes:
  - Customer Group
```

Why:

```text
Names change.
IDs are stable.
The validator resolves IDs and builds relationship edges.
```

Markdown body may include human links, but frontmatter must contain canonical ID references.

Example:

```markdown
Related decision: [[DEC-CH01-A17-CUSTOMER-GROUP]]
```

Canonical frontmatter still required:

```yaml
related_decisions:
  - DEC-CH01-A17-CUSTOMER-GROUP
```

---

## 15. Obsidian and editor compatibility

The repository may be opened as an Obsidian vault, but must not depend on Obsidian.

Rules:

1. Use Markdown files with valid YAML frontmatter.
2. Keep object ID visible in file name.
3. Obsidian wikilinks may be used in body text.
4. Canonical relationships must be stored in frontmatter as IDs.
5. Do not require Obsidian plugins for repository correctness.
6. Do not store generated index files in a way that pollutes the user-facing vault.
7. Keep generated folders excluded or visually separated.

Recommended Obsidian-friendly folders:

```text
model/
templates/
docs/
```

Less Obsidian-friendly generated folders:

```text
generated/
data/raw/
```

These can be hidden/excluded in Obsidian if needed.

---

## 16. Git rules

Git is the technical trust layer.

Recommended `.gitignore`:

```gitignore
# generated artifacts
generated/
*.db
*.sqlite
*.duckdb
*.parquet

# local raw datasets
data/raw/
data/processed/

# local env/secrets
.env
.env.*
!.env.example

# OS/editor
.DS_Store
Thumbs.db

# Python/Node
.venv/
__pycache__/
node_modules/
.next/
dist/
```

Allowed to commit:

```text
model/
templates/
schemas/
docs/
modelops.config.yaml
data/samples/
```

Usually avoid committing:

```text
large raw Excel files
client data extracts
generated indexes
embeddings
local logs
secrets
```

### 16.1 Git LFS option

If the repository must keep sample Excel or large reference files, use Git LFS.

Do not require Git LFS for MVP unless necessary.

### 16.2 Branching model

MVP:

```text
main branch
local commits
manual review
```

Later:

```text
feature branches for model changes
pull request per ChangeRequest
AI patch proposals as branches
```

Recommended branch naming:

```text
cr/CR-0021-customer-group-ch01-a17
patch/PATCH-0021-customer-group-ch01-a17
```

---

## 17. Generated folder policy

Generated files must include metadata where practical.

Example metadata:

```json
{
  "generated_at": "2026-04-26T21:00:00+02:00",
  "source_repository_hash": "abc123",
  "modelops_version": "0.6.1"
}
```

Generated artifacts may include:

```text
modelops.db
search_documents.jsonl
lineage_edges.jsonl
validation_results.jsonl
audit_events.jsonl
repository-health.md
impact reports
gap reports
AMS handover reports
```

Rules:

1. Generated files must not be edited manually.
2. Generated files can be deleted and rebuilt.
3. Generated files must not override canonical files.
4. AI should use generated search documents and index where possible, not raw uncontrolled file dumps.

---

## 18. Import and staging rules

Imports are not automatically approved model objects.

Recommended flow:

```text
raw input
  → parsed draft
  → proposed objects
  → validation
  → human review
  → canonical model files
```

Import folder structure:

```text
imports/
  raw/
    customer_mapping_2026_04_26.xlsx

  parsed/
    customer_mapping_2026_04_26/
      parsed_attributes.yaml
      parsed_field_endpoints.yaml
      parsed_mappings.yaml
      parse_warnings.md

  proposed/
    PATCH-IMPORT-CUSTOMER-MAPPING-20260426.md

  reports/
    import_report_customer_mapping_20260426.md
```

Rules:

1. Imported objects start as draft/proposed.
2. Import parser must not overwrite approved canonical objects without patch workflow.
3. Import reports should list uncertain matches.
4. Human review is required before import becomes canonical.

---

## 19. Dataset storage rules

Datasets are inputs/evidence, not the model.

Dataset metadata belongs in `model/datasets/`.

Raw files usually belong in:

```text
data/raw/
```

Small demo files may belong in:

```text
data/samples/
```

Dataset metadata example:

```yaml
id: DATASET-CUSTOMER-SALES-AREA-LOAD
type: Dataset
domain: DOMAIN-CUSTOMER-BP
name: Customer Sales Area Load File
dataset_type: migration_file
path: ../data/raw/customer_sales_area_load.xlsx
source_system: SYS-LEGACY-CRM
target_system: SYS-S4HANA
entity_context: CTX-CUSTOMER-SALES-AREA-STAGING
status: profiled
profile:
  row_count: 12500
  column_count: 84
  last_profiled_at: 2026-04-26
```

Rules:

1. Do not store raw client data in canonical model files.
2. Do not send raw datasets to AI by default.
3. Store profiles, summaries, and references.
4. Large files should be ignored by Git or stored externally.
5. Profiles are generated and can be rebuilt.

---

## 20. Folder-specific object rules

### 20.1 `model/domains/`

Stores `MasterDataDomain`.

Example:

```yaml
id: DOMAIN-CUSTOMER-BP
type: MasterDataDomain
name: Customer / Business Partner
description: Customer and Business Partner model knowledge for SAP migration and AMS.
status: active
owners:
  accountable: ROLE-CUSTOMER-MD-OWNER
  responsible: ROLE-CUSTOMER-BP-STEWARD
```

### 20.2 `model/migration-objects/`

Stores `MigrationObject`.

Example:

```yaml
id: MIGOBJ-CUSTOMER-BP
type: MigrationObject
domain: DOMAIN-CUSTOMER-BP
name: Customer Business Partner Migration
target_system: SYS-S4HANA
status: active
entities:
  - ENTITY-BUSINESS-PARTNER
  - ENTITY-CUSTOMER-SALES-AREA
  - ENTITY-CUSTOMER-COMPANY-CODE
```

### 20.3 `model/entities/`

Stores `BusinessEntity`.

Example:

```yaml
id: ENTITY-CUSTOMER-SALES-AREA
type: BusinessEntity
domain: DOMAIN-CUSTOMER-BP
name: Customer Sales Area
description: Sales-area-dependent customer data.
grain:
  - customer_number
  - sales_org
  - distribution_channel
  - division
status: active
```

### 20.4 `model/entity-contexts/`

Stores `EntityContext`.

Example:

```yaml
id: CTX-CUSTOMER-SALES-AREA-S4
type: EntityContext
domain: DOMAIN-CUSTOMER-BP
entity: ENTITY-CUSTOMER-SALES-AREA
name: S/4HANA Customer Sales Area
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
status: active
```

### 20.5 `model/attributes/`

Stores `Attribute`.

Recommended path:

```text
model/attributes/{domain_slug}/{ATTR-ID}.md
```

Example:

```yaml
id: ATTR-CUST-SALES-CUSTOMER-GROUP
type: Attribute
domain: DOMAIN-CUSTOMER-BP
name: Customer Group
description: Sales-area-dependent customer grouping used in sales processes and reporting.
semantic_category: sales_classification
data_classification: internal
default_context: CTX-CUSTOMER-SALES-AREA-S4
status: active
owners:
  accountable: ROLE-SALES-MD-OWNER
  responsible: ROLE-CUSTOMER-BP-STEWARD
```

Rules:

1. Attribute defines business meaning.
2. Attribute must not be treated as physical SAP field.
3. Attribute should have at least one AttributeUsage.
4. Attribute should have owner/steward.
5. Attribute should link to validations when applicable.

### 20.6 `model/attribute-usages/`

Stores `AttributeUsage`.

Example:

```yaml
id: USE-CUST-SALES-CUSTOMER-GROUP-S4
type: AttributeUsage
attribute: ATTR-CUST-SALES-CUSTOMER-GROUP
entity_context: CTX-CUSTOMER-SALES-AREA-S4
usage_type: target_attribute
grain:
  - KUNNR
  - VKORG
  - VTWEG
  - SPART
requiredness: conditional
condition: Required for selected sales organizations and customer groups.
maintenance_context:
  sap_roles:
    - SAPROLE-FLCU01
  sap_ui_area: Customer Sales Area
migration_relevance: in_scope
validation_relevance: in_scope
status: active
```

Rules:

1. AttributeUsage connects business attribute to context.
2. Use AttributeUsage when the same attribute exists in multiple SAP contexts.
3. Use separate Attributes only if business meaning, owner, rule, or lifecycle materially differs.

### 20.7 `model/systems/`

Stores `System`.

Example:

```yaml
id: SYS-S4HANA
type: System
name: SAP S/4HANA
system_category: sap_s4hana
role: target
status: active
owners:
  functional_owner: ROLE-S4-FUNCTIONAL
  technical_owner: ROLE-BASIS-TEAM
```

### 20.8 `model/system-environments/`

Stores `SystemEnvironment`.

Example:

```yaml
id: ENV-S4-RS4
type: SystemEnvironment
system: SYS-S4HANA
name: RS4
environment_type: test
client: "100"
status: active
```

Rules:

1. Do not confuse logical system and environment.
2. Value lists/configuration may differ by environment.
3. Environment-specific gaps should be modeled explicitly.

### 20.9 `model/sap-objects/`

Stores SAP-specific objects.

Examples:

```yaml
id: SAPTABLE-KNVV
type: SAPObject
sap_object_type: table
name: KNVV
description: Customer master sales data.
domain: DOMAIN-CUSTOMER-BP
related_entity_contexts:
  - CTX-CUSTOMER-SALES-AREA-S4
status: active
```

```yaml
id: SAPROLE-FLCU01
type: SAPObject
sap_object_type: bp_role
name: FLCU01
description: Customer sales role / sales area maintenance context.
domain: DOMAIN-CUSTOMER-BP
related_entity_contexts:
  - CTX-CUSTOMER-SALES-AREA-S4
status: active
```

Rule:

```text
SAP table storage, BP role, and UI maintenance context are related but not identical.
```

### 20.10 `model/field-endpoints/`

Stores `FieldEndpoint`.

Example SAP endpoint:

```yaml
id: FEP-S4-KNVV-KDGRP
type: FieldEndpoint
domain: DOMAIN-CUSTOMER-BP
system: SYS-S4HANA
environment: ENV-S4-RS4
endpoint_type: sap_table_field
sap_table: KNVV
sap_field: KDGRP
technical_name: KNVV-KDGRP
business_attribute: ATTR-CUST-SALES-CUSTOMER-GROUP
entity_context: CTX-CUSTOMER-SALES-AREA-S4
grain:
  - KUNNR
  - VKORG
  - VTWEG
  - SPART
data_type: CHAR
length: 2
status: active
```

Example dataset column endpoint:

```yaml
id: FEP-DATASET-CUSTOMER-GROUP
type: FieldEndpoint
domain: DOMAIN-CUSTOMER-BP
system: SYS-MIGRATION-FILE
endpoint_type: dataset_column
dataset: DATASET-CUSTOMER-SALES-AREA-LOAD
column_name: CUSTOMER_GROUP
business_attribute: ATTR-CUST-SALES-CUSTOMER-GROUP
entity_context: CTX-CUSTOMER-SALES-AREA-STAGING
status: active
```

Rules:

1. FieldEndpoint is physical/system-specific.
2. FieldEndpoint must reference a System or Dataset.
3. FieldEndpoint should reference Attribute where known.
4. SAP FieldEndpoint must have correct EntityContext.
5. Do not collapse FieldEndpoint into Attribute.

### 20.11 `model/interfaces/`

Stores `Interface`.

Example:

```yaml
id: IFACE-LEGACY-CUSTOMER-SALES-EXTRACT
type: Interface
domain: DOMAIN-CUSTOMER-BP
name: Legacy Customer Sales Extract
interface_type: file_extract
source_system: SYS-LEGACY-CRM
target_system: SYS-MIGRATION-STAGING
direction: outbound
frequency: ad_hoc
datasets:
  - DATASET-CUSTOMER-SALES-AREA-LOAD
status: active
owners:
  functional_owner: ROLE-CUSTOMER-MIGRATION
  technical_owner: ROLE-INTERFACE-TEAM
```

Allowed interface types:

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
```

### 20.12 `model/datasets/`

Stores `Dataset` metadata.

Do not store raw data in this object.

See section 19.

### 20.13 `model/mappings/`

Stores `MappingSet` and `Mapping`.

MappingSet example:

```yaml
id: MAPSET-CUSTOMER-SALES-AREA-LEGACY-TO-S4
type: MappingSet
domain: DOMAIN-CUSTOMER-BP
name: Legacy CRM to S/4 Customer Sales Area Mapping
source_system: SYS-LEGACY-CRM
target_system: SYS-S4HANA
entity_context: CTX-CUSTOMER-SALES-AREA-S4
status: active
owner: ROLE-CUSTOMER-BP-STEWARD
```

Mapping example:

```yaml
id: MAP-CUST-GROUP-LEGACY-TO-KNVV-KDGRP
type: Mapping
mapping_set: MAPSET-CUSTOMER-SALES-AREA-LEGACY-TO-S4
domain: DOMAIN-CUSTOMER-BP
name: Legacy customer group to S/4 customer group
source_endpoints:
  - FEP-LEGACY-CUSTOMER-GROUP
target_endpoints:
  - FEP-S4-KNVV-KDGRP
mapping_type: value_mapped
value_mappings:
  - VMAP-LEGACY-CUST-GROUP-TO-S4-KDGRP
transformation_logic:
  - LOGIC-CUST-GROUP-DERIVATION
validations:
  - VAL-CUST-GROUP-ALLOWED-VALUES
status: approved
owner: ROLE-CUSTOMER-BP-STEWARD
```

Allowed mapping types:

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

### 20.14 `model/value-lists/`

Stores `ValueList`.

Example:

```yaml
id: VLIST-S4-KNVV-KDGRP
type: ValueList
domain: DOMAIN-CUSTOMER-BP
name: S/4 Customer Group Values
attribute: ATTR-CUST-SALES-CUSTOMER-GROUP
source:
  system: SYS-S4HANA
  environment: ENV-S4-RS4
  sap_table: TVV1
  sap_field: KDGRP
values:
  - code: "01"
    label: Retail
    status: active
  - code: "02"
    label: Wholesale
    status: active
status: active
owner: ROLE-CUSTOMER-BP-STEWARD
```

Rules:

1. ValueList can be environment-specific.
2. ValueList should include source and snapshot date when imported.
3. Large value lists may be split or stored as external referenced files.
4. ValueList should not be confused with ValueMapping.

### 20.15 `model/value-mappings/`

Stores `ValueMapping`.

Example:

```yaml
id: VMAP-LEGACY-CUST-GROUP-TO-S4-KDGRP
type: ValueMapping
domain: DOMAIN-CUSTOMER-BP
name: Legacy Customer Group to S/4 KDGRP
source_endpoint: FEP-LEGACY-CUSTOMER-GROUP
target_endpoint: FEP-S4-KNVV-KDGRP
target_value_list: VLIST-S4-KNVV-KDGRP
mappings:
  - source_value: A17
    target_value: "01"
    status: approved
    note: Footlocker handling for CH01 requires confirmation.
  - source_value: B20
    target_value: "02"
    status: approved
  - source_value: X99
    target_value: null
    status: unresolved
status: active
owner: ROLE-CUSTOMER-BP-STEWARD
related_issues:
  - ISS-UNMAPPED-X99
```

Validation rules:

```text
Every approved target_value must exist in target_value_list.
Every observed source value should have approved mapping or explicit exception.
Unresolved mappings should create warning or issue.
```

### 20.16 `model/rules/`

Stores `BusinessRule`.

Example:

```yaml
id: RULE-CUST-GROUP-SALES-AREA-REQUIRED
type: BusinessRule
domain: DOMAIN-CUSTOMER-BP
name: Customer Group required for relevant sales areas
statement: Customer Group must be maintained for in-scope customer sales area records where sales process requires customer classification.
applies_to:
  - ATTR-CUST-SALES-CUSTOMER-GROUP
contexts:
  - CTX-CUSTOMER-SALES-AREA-S4
priority: high
owner: ROLE-SALES-MD-OWNER
status: approved
```

### 20.17 `model/logic/`

Stores `TransformationLogic`, `DerivationRule`, `DefaultingRule`, or related logic.

Example:

```yaml
id: LOGIC-CUST-GROUP-DERIVATION
type: TransformationLogic
domain: DOMAIN-CUSTOMER-BP
name: Derive S/4 Customer Group
logic_type: conditional_derivation
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
status: approved
owners:
  business_owner: ROLE-SALES-MD-OWNER
  technical_owner: ROLE-INTERFACE-TEAM
```

### 20.18 `model/validations/`

Stores `ValidationRule`.

Example:

```yaml
id: VAL-CUST-GROUP-ALLOWED-VALUES
type: ValidationRule
domain: DOMAIN-CUSTOMER-BP
name: Customer Group must be in approved S/4 value list
validation_type: allowed_values
attribute: ATTR-CUST-SALES-CUSTOMER-GROUP
field_endpoint: FEP-S4-KNVV-KDGRP
value_list: VLIST-S4-KNVV-KDGRP
severity: error
failure_message: Customer Group is not in approved S/4 value list.
owner: ROLE-CUSTOMER-BP-STEWARD
status: active
```

### 20.19 `model/quality-checks/`

Stores `DataQualityCheck`.

Example:

```yaml
id: DQ-CHECK-CUST-GROUP-ALLOWED-VALUES
type: DataQualityCheck
validation_rule: VAL-CUST-GROUP-ALLOWED-VALUES
check_engine: pandas
input_dataset: DATASET-CUSTOMER-SALES-AREA-LOAD
column: CUSTOMER_GROUP
check_expression: value in VLIST-S4-KNVV-KDGRP.values.code
severity: error
status: active
```

### 20.20 `model/owners/`

Stores ownership roles, persons, and teams.

Recommended MVP: role-based ownership.

Example:

```yaml
id: ROLE-CUSTOMER-BP-STEWARD
type: OwnershipRole
name: Customer BP Data Steward
team: Master Data Governance
responsibilities:
  - Approves customer BP attribute definitions
  - Reviews value mappings
  - Owns validation rules
status: active
```

Avoid overloading MVP with personal data unless needed.

### 20.21 `model/issues/`

Stores `Issue`.

Example:

```yaml
id: ISS-CH01-A17-CONFIG-GAP
type: Issue
domain: DOMAIN-CUSTOMER-BP
title: Customer Group config missing for CH01 / A17
severity: medium
status: open
issue_type: configuration_gap
affected_objects:
  - ATTR-CUST-SALES-CUSTOMER-GROUP
  - FEP-S4-KNVV-KDGRP
  - VLIST-S4-KNVV-KDGRP
owners:
  responsible: ROLE-S4-SD-FUNCTIONAL
  accountable: ROLE-SALES-MD-OWNER
related_decisions:
  - DEC-CH01-A17-CUSTOMER-GROUP
```

### 20.22 `model/risks/`

Stores `Risk`.

Example:

```yaml
id: RISK-CUST-GROUP-CUTOVER-VALIDATION
type: Risk
domain: DOMAIN-CUSTOMER-BP
title: Customer Group validation gap may affect cutover readiness
severity: high
probability: medium
impact: high
status: open
affected_objects:
  - ATTR-CUST-SALES-CUSTOMER-GROUP
mitigation:
  - Re-run value mapping coverage.
  - Confirm S/4 customizing.
owner: ROLE-CUSTOMER-BP-STEWARD
```

### 20.23 `model/decisions/`

Stores `Decision`.

Example:

```yaml
id: DEC-CH01-A17-CUSTOMER-GROUP
type: Decision
domain: DOMAIN-CUSTOMER-BP
title: Special Customer Group handling for CH01 / A17
status: accepted
decision_date: 2026-04-26
related_attributes:
  - ATTR-CUST-SALES-CUSTOMER-GROUP
related_mappings:
  - MAP-CUST-GROUP-LEGACY-TO-KNVV-KDGRP
related_issues:
  - ISS-CH01-A17-CONFIG-GAP
```

Markdown body should explain:

```text
decision
rationale
alternatives considered
consequences
required actions
```

### 20.24 `model/change-requests/`

Stores `ChangeRequest`.

Example:

```yaml
id: CR-0021
type: ChangeRequest
domain: DOMAIN-CUSTOMER-BP
title: Update Customer Group handling for CH01 / A17
status: approved
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
  - VAL-CUST-GROUP-ALLOWED-VALUES
related_issues:
  - ISS-CH01-A17-CONFIG-GAP
related_decisions:
  - DEC-CH01-A17-CUSTOMER-GROUP
created_at: 2026-04-26
approved_at: 2026-04-26
```

Rules:

```text
Every approved model change should link to ChangeRequest.
ChangeRequest should link affected objects.
ChangeRequest should link issue, decision, or evidence.
```

### 20.25 `model/patch-proposals/`

Stores `PatchProposal`.

Example:

```yaml
id: PATCH-0021
type: PatchProposal
domain: DOMAIN-CUSTOMER-BP
status: pending_review
source_evidence:
  - EV-EMAIL-20260426-CH01-A17
proposed_change_request: CR-0021
affected_objects:
  - ATTR-CUST-SALES-CUSTOMER-GROUP
  - VMAP-LEGACY-CUST-GROUP-TO-S4-KDGRP
created_by: ai
created_at: 2026-04-26
```

Rules:

1. AI may create PatchProposal.
2. PatchProposal must be reviewed.
3. PatchProposal must pass deterministic validation before approval.
4. Approval updates canonical model files.
5. Rejection preserves review history.

### 20.26 `model/evidence/`

Stores `Evidence`.

Example:

```yaml
id: EV-EMAIL-20260426-CH01-A17
type: Evidence
domain: DOMAIN-CUSTOMER-BP
evidence_type: email_summary
source_system: Outlook
source_date: 2026-04-26
related_objects:
  - ISS-CH01-A17-CONFIG-GAP
  - ATTR-CUST-SALES-CUSTOMER-GROUP
status: active
```

Rules:

1. Store summaries or references if raw evidence is sensitive.
2. Do not store passwords or confidential raw datasets.
3. Link evidence to issue, decision, or change request.

---

## 21. SAP-specific repository rules

These rules are mandatory for SAP-aware modeling.

### 21.1 KNVV rule

If:

```yaml
sap_table: KNVV
```

Then:

```yaml
entity_context: CTX-CUSTOMER-SALES-AREA-S4
```

or another context explicitly classified as Customer Sales Area.

Required grain:

```text
customer
sales_org
distribution_channel
division
```

Example:

```yaml
grain:
  - KUNNR
  - VKORG
  - VTWEG
  - SPART
```

### 21.2 KNB1 rule

If:

```yaml
sap_table: KNB1
```

Then the endpoint must use Customer Company Code context.

Required grain:

```text
customer
company_code
```

### 21.3 KNVP rule

If:

```yaml
sap_table: KNVP
```

Then the endpoint must use Customer Partner Function context.

Required grain should include partner-function-relevant keys.

### 21.4 BP central rule

If the field belongs to BP central storage, such as `BUT000`, it should use BP Central context.

### 21.5 Address/contact rule

Address/contact fields should be modeled under Address/Contact context, not as generic central attributes without context.

Typical related SAP objects:

```text
BUT020
ADRC
ADR6
```

### 21.6 BP role rule

BP role is a maintenance/governance context, not automatically physical storage.

Example:

```text
FLCU01 may be related to customer sales area maintenance,
but KNVV remains the physical table context.
```

### 21.7 Same concept in multiple SAP contexts

Example:

```text
KNB1-ZTERM = company-code payment terms
KNVV-ZTERM = sales-area payment terms
```

Allowed modeling options:

Option A:

```text
One Attribute
Multiple AttributeUsages
Multiple FieldEndpoints
```

Use when business meaning is shared.

Option B:

```text
Separate Attributes
```

Use when owner, business meaning, rule, lifecycle, or process differs materially.

Decision rule:

```text
If owner/rule/grain/business process differs strongly, use separate attributes.
If only physical representation differs, use one attribute with multiple usages.
```

---

## 22. Relationship model

The parser should generate relationship edges from canonical references.

Examples:

```text
Attribute -> represented_by -> FieldEndpoint
Attribute -> used_in -> AttributeUsage
FieldEndpoint -> belongs_to_context -> EntityContext
Mapping -> maps_from -> FieldEndpoint
Mapping -> maps_to -> FieldEndpoint
Mapping -> uses_value_mapping -> ValueMapping
ValueMapping -> uses_value_list -> ValueList
ValidationRule -> validates -> Attribute
ValidationRule -> checks_endpoint -> FieldEndpoint
Issue -> affects -> Object
Decision -> explains -> Object
ChangeRequest -> changes -> Object
Evidence -> supports -> Issue/Decision/ChangeRequest
```

Generated relationship edge format:

```json
{
  "from_object_id": "ATTR-CUST-SALES-CUSTOMER-GROUP",
  "relationship_type": "represented_by",
  "to_object_id": "FEP-S4-KNVV-KDGRP",
  "source_object_id": "USE-CUST-SALES-CUSTOMER-GROUP-S4",
  "source_file": "model/attribute-usages/USE-CUST-SALES-CUSTOMER-GROUP-S4.md",
  "confidence": "explicit"
}
```

Relationship confidence values:

```text
explicit
derived
inferred
ai_suggested
```

MVP should mainly use `explicit` and `derived`.

AI-suggested relationships must not become canonical without review.

---

## 23. Repository validation policy

Validation levels:

```text
error
warning
info
```

### 23.1 Errors

Errors should block patch approval.

Examples:

```text
invalid frontmatter
duplicate ID
missing required field
broken reference
invalid object type
invalid status
FieldEndpoint without System
SAP FieldEndpoint without EntityContext
KNVV endpoint not assigned to Customer Sales Area context
KNB1 endpoint not assigned to Customer Company Code context
ValueMapping target value missing from target ValueList
PatchProposal attempts direct unapproved model mutation
```

### 23.2 Warnings

Warnings should not block browsing, but should be visible.

Examples:

```text
Attribute without owner
Attribute without validation
Attribute without AttributeUsage
Mapping without owner
Issue without affected object
Decision without related object
ChangeRequest without evidence
ValueList without snapshot date
Dataset without profile
```

### 23.3 Info

Examples:

```text
Generated index is older than latest model file.
Object has no recent change history.
AI is disabled.
Repository is not a Git repository.
```

---

## 24. Repository build order

Recommended parser/indexer order:

```text
1. Load modelops.config.yaml.
2. Scan canonical folders.
3. Parse Markdown/YAML files.
4. Extract YAML frontmatter.
5. Build ObjectRegistry.
6. Validate common fields.
7. Validate type-specific schemas.
8. Resolve references.
9. Apply SAP-specific validation.
10. Generate relationship edges.
11. Build generated database.
12. Generate AI search documents.
13. Generate validation results.
14. Generate repository health report.
```

If errors exist:

```text
Read-only browsing may continue.
Patch approval must be blocked.
Generated index should mark repository health as degraded.
```

---

## 25. Repository health report

The system should generate:

```text
generated/reports/repository-health.md
```

Report sections:

```text
Repository summary
Object counts by type
Validation errors
Validation warnings
Broken references
Missing owners
Missing validations
Missing mappings
SAP context violations
Unresolved value mappings
Open high-severity issues
Pending patch proposals
Recent change requests
Index metadata
```

---

## 26. AI-ready repository rules

The repository should be easy for AI to search, but AI should not consume the raw repository chaotically.

Rules:

1. Generate `search_documents.jsonl`.
2. Generate relationship edges.
3. Use context bundles for AI tasks.
4. Keep object summaries concise.
5. Include IDs and technical names.
6. Include SAP table/field names in search text.
7. Include related issues/decisions/evidence summaries.
8. Do not send large raw files to AI.
9. AI output must become PatchProposal, not direct model change.

Search document example:

```json
{
  "id": "ATTR-CUST-SALES-CUSTOMER-GROUP",
  "type": "Attribute",
  "title": "Customer Group",
  "domain": "DOMAIN-CUSTOMER-BP",
  "context": "Customer Sales Area",
  "technical_representations": [
    "S4HANA KNVV-KDGRP",
    "Legacy CRM CUSTOMER_SALES.CUST_GROUP",
    "Migration file CUSTOMER_GROUP"
  ],
  "related_objects": [
    "FEP-S4-KNVV-KDGRP",
    "VMAP-LEGACY-CUST-GROUP-TO-S4-KDGRP",
    "VAL-CUST-GROUP-ALLOWED-VALUES"
  ],
  "search_text": "Customer Group KDGRP KNVV sales area customer classification mapping validation CH01 A17"
}
```

---

## 27. Patch proposal and approval model

AI and import flows should create patch proposals.

Patch lifecycle:

```text
pending_review
accepted
rejected
superseded
```

Patch approval flow:

```text
1. PatchProposal created.
2. Proposed changes validated.
3. Diff preview generated.
4. User reviews.
5. User approves.
6. Canonical files updated.
7. ChangeRequest created/updated.
8. Audit event generated.
9. Index rebuilt.
```

Patch rejection flow:

```text
1. User rejects.
2. PatchProposal status becomes rejected.
3. Rejection reason is recorded.
4. No canonical model files are changed.
```

Patch files should capture:

```text
source evidence
affected objects
proposed changes
validation status
human review notes
approval status
```

---

## 28. Change governance model

The repository must support meaningful history, not only Git commits.

History layers:

```text
Git
  exact file diff

ChangeRequest
  business meaning of model change

Decision
  reason and accepted design

Issue
  problem or gap

Evidence
  source material

Object change_history
  local readable summary

Generated audit_events
  runtime action trail
```

Object-level change history example:

```yaml
change_history:
  - change_request: CR-0021
    date: 2026-04-26
    summary: Added CH01 / A17 special handling for Customer Group.
```

Do not use one global `CHANGELOG.md` as the primary model change log.

---

## 29. Versioning and schema migration

### 29.1 Repository version

`modelops.config.yaml` should include repository schema version.

Example:

```yaml
repository:
  schema_version: 0.1
```

### 29.2 Object schema version

Optional for MVP, useful later:

```yaml
schema_version: 0.1
```

### 29.3 Migration policy

If object schemas change:

1. Add migration script.
2. Preserve existing IDs.
3. Record migration in generated report.
4. Avoid destructive changes.
5. Keep backward compatibility for at least one minor version where practical.

Suggested migration folder:

```text
schemas/migrations/
  0001_initial.py
  0002_add_attribute_usage_requiredness.py
```

---

## 30. Config file specification

`modelops.config.yaml` controls workspace behavior.

Example:

```yaml
workspace:
  name: Customer BP Migration Model
  description: SAP Customer / Business Partner migration model workspace
  version: 0.1
  default_domain: DOMAIN-CUSTOMER-BP

repository:
  schema_version: 0.1
  model_path: model
  generated_path: generated
  data_path: data
  imports_path: imports
  templates_path: templates

index:
  engine: sqlite
  path: generated/modelops.db
  rebuild_mode: full

search:
  generate_documents: true
  output_path: generated/search_documents.jsonl

validation:
  block_patch_approval_on_errors: true
  warn_on_missing_owner: true
  warn_on_missing_validation: true
  sap_context_rules_enabled: true

ai:
  enabled: true
  require_patch_review: true
  allow_direct_model_write: false
  max_context_objects: 50

git:
  require_clean_worktree_for_patch_apply: true
  suggest_commit_message: true
```

Secrets must not be stored here.

Use `.env` for secrets.

---

## 31. Sensitive data and privacy rules

Rules:

1. Do not store credentials in repository.
2. Do not store raw personal data unless explicitly required and approved.
3. Do not send raw client data to AI by default.
4. Evidence should store summaries or references when raw material is sensitive.
5. Raw datasets should usually be ignored by Git.
6. AI context must be minimized.
7. Logs must not include secrets or full raw records.

Suggested `.env.example`:

```env
MODELOPS_REPOSITORY_PATH=./
AI_PROVIDER=openai
AI_MODEL=
AI_API_KEY=
```

Actual `.env` must be ignored by Git.

---

## 32. Template system

Templates should live under:

```text
templates/
```

Required MVP templates:

```text
domain.md
migration-object.md
entity.md
entity-context.md
attribute.md
attribute-usage.md
system.md
system-environment.md
sap-object.md
field-endpoint.md
interface.md
dataset.md
mapping.md
value-list.md
value-mapping.md
business-rule.md
transformation-logic.md
validation-rule.md
data-quality-check.md
ownership-role.md
issue.md
risk.md
decision.md
change-request.md
patch-proposal.md
evidence.md
```

Template variables:

```text
{{id}}
{{type}}
{{domain}}
{{name}}
{{title}}
{{created_at}}
{{owner}}
```

The product UI and CLI should use templates when creating new objects.

---

## 33. Import/export interoperability

### 33.1 Import sources

Supported MVP import sources:

```text
Excel mapping workbook
CSV migration file
YAML object draft
Markdown note
pasted email/ticket/workshop note
```

Later:

```text
Jira
Confluence
SAP metadata export
SAP customizing snapshot
Cloud ALM
SolMan
GitHub/GitLab
```

### 33.2 Export formats

Supported exports:

```text
Markdown report
JSON export
CSV catalog export
SQLite generated index
JSONL AI search corpus
```

Later:

```text
PDF
Excel
Confluence page
Jira issue
GitHub pull request
```

---

## 34. Repository examples

### 34.1 Example KNVV field repository objects

Attribute:

```text
model/attributes/customer_bp/ATTR-CUST-SALES-CUSTOMER-GROUP.md
```

AttributeUsage:

```text
model/attribute-usages/USE-CUST-SALES-CUSTOMER-GROUP-S4.md
```

FieldEndpoint:

```text
model/field-endpoints/FEP-S4-KNVV-KDGRP.md
```

Mapping:

```text
model/mappings/MAP-CUST-GROUP-LEGACY-TO-KNVV-KDGRP.md
```

ValueList:

```text
model/value-lists/VLIST-S4-KNVV-KDGRP.md
```

ValueMapping:

```text
model/value-mappings/VMAP-LEGACY-CUST-GROUP-TO-S4-KDGRP.md
```

Validation:

```text
model/validations/VAL-CUST-GROUP-ALLOWED-VALUES.md
```

Issue:

```text
model/issues/ISS-CH01-A17-CONFIG-GAP.md
```

Decision:

```text
model/decisions/DEC-CH01-A17-CUSTOMER-GROUP.md
```

ChangeRequest:

```text
model/change-requests/CR-0021-CUSTOMER-GROUP-CH01-A17.md
```

### 34.2 Correct interpretation

```text
KNVV-KDGRP
  is a FieldEndpoint.
  It belongs to Customer Sales Area context.
  It represents Customer Group attribute in S/4.
  It may be maintained via a customer sales-related BP role/UI context.
  It participates in mappings, value mappings, validations, issues, and impact analysis.
```

### 34.3 Incorrect interpretation

```text
KNVV-KDGRP = generic customer field
```

This is too flat and loses SAP context.

---

## 35. Repository quality gates

A repository object is ready when:

```text
frontmatter is valid YAML
id is globally unique
type matches schema
required fields are present
status is valid
references resolve
owner exists or exception is documented
SAP context rules pass where applicable
change is linked to ChangeRequest if approved
object appears in generated index
object contributes to search document where relevant
```

A repository is healthy when:

```text
no validation errors
few controlled warnings
no broken references
critical attributes have owners
critical attributes have validations
mappings have source and target endpoints
value mappings align to value lists
SAP contexts are correct
pending patch proposals are reviewed
high-severity issues are visible
```

---

## 36. Modern repository variants

### 36.1 Local file repository

Recommended MVP.

Pros:

```text
simple
transparent
fast to build
works with Git
works with Obsidian/VS Code
good for demos
low infrastructure
```

Cons:

```text
single-user by default
manual collaboration
limited access control
```

### 36.2 Git-backed repository

Recommended next.

Pros:

```text
review workflow
branches
pull requests
history
good trust story
AI patches can become PRs
```

Cons:

```text
requires Git literacy
merge conflicts possible
```

### 36.3 Hosted repository service

Later.

Pros:

```text
team collaboration
permissions
central audit
enterprise identity
controlled UI
```

Cons:

```text
more infrastructure
harder product build
requires migration from local mode
```

### 36.4 Database-first repository

Not recommended for MVP.

Pros:

```text
multi-user easier
querying easier
```

Cons:

```text
weak Git diff
less transparent
harder AI patch review
more hidden state
less local-first
```

### 36.5 Hybrid file + hosted index

Strong future option.

```text
Canonical model stays in Git/files.
Hosted service builds index, UI, search, reports, and AI patches.
```

This preserves trust while enabling team workflows.

---

## 37. Product-specific non-goals for repository

Do not use the repository for:

```text
full SAP master data record storage
large raw data lake
secret storage
generic document dump
unreviewed AI memory
direct SAP write-back commands
workflow engine state as primary architecture
binary-heavy project archive
```

The repository must stay focused on model knowledge.

---

## 38. Repository build and command expectations

CLI should support:

```bash
modelops init ./my-model
modelops validate --repo ./my-model
modelops build-index --repo ./my-model --jsonl
modelops health --repo ./my-model
modelops search "customer group" --repo ./my-model
modelops query --type Attribute --repo ./my-model
modelops import-model-sheet ./review-workbook.xlsx --repo ./my-model
modelops profile-dataset ./data/customer_sales_area.csv --repo ./my-model
modelops gaps ./data/customer_sales_area.csv --repo ./my-model --check-model
modelops impact ATTR-CUST-SALES-CUSTOMER-GROUP --repo ./my-model
modelops propose-patch --from note.md --repo ./my-model
modelops proposal accept PP-SCAFFOLD-001 --repo ./my-model --reviewer "reviewer@example.com"
modelops proposal apply PP-SCAFFOLD-001 --repo ./my-model --dry-run
modelops export-model --repo ./my-model --format xlsx
```

The UI should call the same core services.

---

## 39. Definition of done for this specification

This repository specification is successful if a developer can implement:

```text
file scanner
frontmatter parser
object registry
schema validator
reference resolver
SAP context validator
SQLite index builder
search document generator
repository health report
patch proposal workflow
```

without guessing:

```text
where objects live
how objects are named
which fields are required
what is canonical
what is generated
how SAP fields relate to attributes
how AI may propose changes
how approved changes are governed
```

---

## 40. Final repository recommendation

For MVP, use:

```text
Markdown + YAML frontmatter canonical files
one governed object per file
stable object IDs
Git diff as trust layer
SQLite generated index
JSONL search documents
relationship edge generation
PatchProposal before AI changes
ChangeRequest for approved changes
Obsidian/VS Code compatibility
SAP-specific validation rules
```

This gives the product the right balance:

```text
simple enough to build
structured enough to validate
transparent enough to trust
flexible enough for SAP complexity
ready enough for AI-assisted work
```

The repository should remain open and readable, but the product UI should provide the guided experience for SAP migration, MDM, and AMS teams.
