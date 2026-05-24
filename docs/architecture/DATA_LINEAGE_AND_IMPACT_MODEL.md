# ModelOps for MDM — Data Lineage and Impact Model

Version: `0.2-draft`  
Document type: Product lineage / impact architecture  
Scope: Data lineage, usage tracing, change impact analysis, affected object discovery, and impact reporting  
Initial product focus: SAP Business Partner migration model, Customer role slice first  
Product type: File-based, SAP-aware, AI-ready ModelOps workspace for migration, MDM, governance, and AMS

---

## 1. Purpose

This document defines the **data lineage and impact model** for ModelOps for MDM.

## MVP Lineage Boundary

P0 lineage and impact must be deterministic and repository-derived.

Build this first:

```text
Customer Group Attribute
  -> Customer Sales Area AttributeUsage
  -> source dataset FieldEndpoint / DatasetColumn
  -> Mapping / ValueMapping
  -> target FieldEndpoint KNVV-KDGRP
  -> ValidationRule / DataQualityCheck
  -> Issue / Decision / ChangeRequest / PatchProposal
  -> owner and evidence links
```

Use generated relationship edges and SQLite traversal. Do not start with graph database infrastructure, runtime SAP lineage extraction, or AI-inferred impact as source of truth.

Lineage and impact analysis are core product capabilities.

The product must help users answer:

```text
Where does this field come from?
Where does it go?
How is it transformed?
Which values are allowed?
Which value mappings affect it?
Which validation rules check it?
Which datasets contain it?
Which interfaces move it?
Which SAP contexts does it belong to?
Which owners are responsible?
Which issues and decisions explain it?
What breaks if it changes?
What must be updated for AMS handover?
```

This document describes:

- lineage concepts;
- impact concepts;
- lineage node types;
- relationship/edge types;
- SAP-specific lineage rules;
- impact traversal rules;
- impact severity model;
- generated edge/index model;
- UI presentation rules;
- report structure;
- deterministic vs AI-assisted impact;
- MVP implementation phases;
- future architecture options.

---

## 2. Core distinction

Lineage and impact are related but not the same.

### 2.1 Lineage

Lineage answers:

```text
How does data move, change, and get used?
```

Example:

```text
Legacy CRM CUSTOMER_SALES.CUST_GROUP
  → Value Mapping
  → Migration File CUSTOMER_GROUP
  → S/4HANA KNVV-KDGRP
  → Validation Rule
  → AMS Handover Summary
```

### 2.2 Impact

Impact answers:

```text
What is affected if something changes?
```

Example:

```text
If VLIST-S4-KNVV-KDGRP changes:
  affected attributes
  affected value mappings
  affected validations
  affected datasets
  affected issues
  affected decisions
  affected owners
  affected reports
```

### 2.3 Practical difference

```text
Lineage = path of data and knowledge relationships.
Impact = consequence analysis from a changed object.
```

Both use the same relationship graph, but they ask different questions.

---

## 3. Product principle

The product should not start with a complex graph database.

For MVP:

```text
Canonical files
  → generated relationship edges
  → SQLite object_relationships table
  → LineageService
  → ImpactService
  → UI/report output
```

A graph database may be added later only if relationship complexity and scale justify it.

---

## 4. Main lineage promise

For any important Attribute or FieldEndpoint, the user should be able to see:

```text
Upstream:
  source systems
  source fields
  source datasets
  source value lists
  source issues

Transformation:
  mapping
  value mapping
  defaulting
  derivation
  enrichment
  interface logic

Target:
  SAP table/field
  SAP context
  target value list
  validation rules
  data quality checks

Downstream:
  reports
  validations
  datasets
  AMS handover
  known issues
  decisions
  owners
```

---

## 5. Main impact promise

For any changed object, the user should be able to see:

```text
What objects are directly affected?
What objects are indirectly affected?
Which validations must be rerun?
Which datasets must be reprofiled?
Which mappings/value mappings must be reviewed?
Which owners must approve?
Which issues/risks may be impacted?
Which decisions explain the current model?
Which reports and AMS handover outputs must be updated?
```

---

## 6. Supported starting points

Lineage and impact analysis should start from many object types, not only attributes.

Supported MVP starting objects:

```text
Attribute
AttributeUsage
FieldEndpoint
Mapping
ValueList
ValueMapping
TransformationLogic
BusinessRule
ValidationRule
DataQualityCheck
Dataset
Interface
Issue
Decision
ChangeRequest
PatchProposal
Evidence
Owner / OwnershipRole
System
SystemEnvironment
SAPObject
```

Priority MVP start points:

```text
Attribute
FieldEndpoint
Mapping
ValueMapping
ValueList
ValidationRule
Dataset
Issue
ChangeRequest
```

---

## 7. Core object graph

The lineage and impact graph connects these core object groups.

```text
Scope:
  Domain
  MigrationObject
  BusinessEntity
  EntityContext

Semantic model:
  Attribute
  AttributeUsage
  BusinessRule

Physical representation:
  System
  SystemEnvironment
  SAPObject
  FieldEndpoint
  Interface
  Dataset

Movement/transformation:
  MappingSet
  Mapping
  ValueList
  ValueMapping
  TransformationLogic

Quality:
  ValidationRule
  DataQualityCheck
  ValidationRun
  ValidationResult
  DataProfile
  Gap
  GapReport

Governance:
  Owner
  Issue
  Risk
  Decision
  ChangeRequest
  Evidence
  PatchProposal

Generated intelligence:
  LineagePath
  ImpactReport
  SearchDocument
  ContextBundle
  AMSHandoverSummary
```

---

## 8. Lineage node types

Every node in lineage/impact should have a typed identity.

Recommended node model:

```json
{
  "node_id": "FEP-S4-KNVV-KDGRP",
  "node_type": "FieldEndpoint",
  "label": "S/4HANA KNVV-KDGRP",
  "domain": "DOMAIN-CUSTOMER-BP",
  "status": "active",
  "source_file": "model/field-endpoints/FEP-S4-KNVV-KDGRP.md"
}
```

### 8.1 Node categories

```text
semantic
physical
mapping
value
logic
validation
dataset
interface
governance
report
owner
evidence
```

### 8.2 Node display labels

Examples:

```text
Attribute:
  Customer Group

FieldEndpoint:
  S/4HANA KNVV-KDGRP

Mapping:
  Legacy Customer Group → S/4 KDGRP

ValueMapping:
  Legacy CUST_GROUP → S/4 KDGRP

ValidationRule:
  Customer Group must be in approved S/4 value list

Dataset:
  Customer Sales Area Load File

Issue:
  CH01 / A17 Customer Group config gap
```

---

## 9. Relationship / edge model

Lineage and impact depend on explicit or generated edges.

Recommended edge structure:

```json
{
  "from_object_id": "ATTR-CUST-SALES-CUSTOMER-GROUP",
  "relationship_type": "represented_by",
  "to_object_id": "FEP-S4-KNVV-KDGRP",
  "source_object_id": "USE-CUST-SALES-CUSTOMER-GROUP-S4",
  "source_file": "model/attribute-usages/USE-CUST-SALES-CUSTOMER-GROUP-S4.md",
  "confidence": "explicit",
  "direction": "outbound"
}
```

### 9.1 Edge confidence

Allowed values:

```text
explicit
derived
inferred
ai_suggested
```

Definitions:

```text
explicit:
  Relationship is directly declared in canonical files.

derived:
  Relationship is generated from structured fields.

inferred:
  Relationship is inferred by deterministic logic and should be reviewed.

ai_suggested:
  Relationship is proposed by AI and not canonical until approved.
```

MVP should mainly use:

```text
explicit
derived
```

AI-suggested relationships must not be treated as canonical until approved.

---

## 10. Core relationship types

### 10.1 Scope relationships

```text
belongs_to_domain
part_of_migration_object
has_entity
has_context
uses_context
```

### 10.2 Semantic relationships

```text
defines_attribute
uses_attribute
used_in_context
has_usage
represented_by
physical_representation_of
```

### 10.3 Physical relationships

```text
located_in_system
located_in_environment
uses_sap_object
has_field_endpoint
used_in_interface
used_in_dataset
used_in_report
```

### 10.4 Mapping relationships

```text
mapped_from
mapped_to
maps_source_to_target
uses_mapping
uses_mapping_set
uses_value_mapping
uses_value_list
uses_logic
transformed_by
defaulted_by
derived_by
```

### 10.5 Validation relationships

```text
has_business_rule
validates
checked_by
uses_data_quality_check
has_validation_result
failed_by
passed_by
```

### 10.6 Governance relationships

```text
owned_by
accountable_to
responsible_for
affected_by
affects
explained_by
supported_by
changed_by
proposed_by
approved_by
superseded_by
```

### 10.7 Report relationships

```text
included_in_report
included_in_handover
included_in_readiness_summary
included_in_gap_report
included_in_impact_report
```

---

## 11. Directionality rules

Lineage edges should have meaningful direction.

### 11.1 Data movement direction

```text
source endpoint → mapping → target endpoint
```

Example:

```text
FEP-LEGACY-CUSTOMER-GROUP
  mapped_to
MAP-CUST-GROUP-LEGACY-TO-KNVV-KDGRP

MAP-CUST-GROUP-LEGACY-TO-KNVV-KDGRP
  mapped_to
FEP-S4-KNVV-KDGRP
```

### 11.2 Semantic representation direction

```text
Attribute → represented_by → FieldEndpoint
```

Reverse query may use:

```text
FieldEndpoint → physical_representation_of → Attribute
```

### 11.3 Validation direction

```text
ValidationRule → validates → Attribute
ValidationRule → checks_endpoint → FieldEndpoint
DataQualityCheck → implements → ValidationRule
```

### 11.4 Governance direction

```text
Issue → affects → Attribute
Decision → explains → Mapping
ChangeRequest → changes → ValueMapping
Evidence → supports → Decision
```

Impact traversal may traverse both directions, depending on query type.

---

## 12. SAP-specific lineage principles

SAP lineage must respect context and grain.

### 12.1 KNVV rule

If a FieldEndpoint has:

```text
sap_table = KNVV
```

It belongs to:

```text
Customer Sales Area context
```

Expected grain:

```text
KUNNR + VKORG + VTWEG + SPART
```

Lineage should display this clearly.

Example:

```text
S/4HANA KNVV-KDGRP
Context: Customer Sales Area
Grain: Customer + Sales Org + Distribution Channel + Division
```

### 12.2 KNB1 rule

If a FieldEndpoint has:

```text
sap_table = KNB1
```

It belongs to:

```text
Customer Company Code context
```

Expected grain:

```text
KUNNR + BUKRS
```

### 12.3 KNVP rule

If a FieldEndpoint has:

```text
sap_table = KNVP
```

It belongs to:

```text
Customer Partner Function context
```

### 12.4 BUT000 rule

If a FieldEndpoint has:

```text
sap_table = BUT000
```

It belongs to:

```text
Business Partner Central context
```

### 12.5 BP role caution

BP role is not physical storage.

Example:

```text
FLCU01
  may describe maintenance/governance/UI context
  but it is not the same as KNVV physical field storage
```

Lineage UI must not show BP role as if it is a table field.

### 12.6 Same attribute in multiple SAP contexts

Some concepts exist in multiple contexts.

Example:

```text
Payment Terms:
  KNB1-ZTERM = company-code context
  KNVV-ZTERM = sales-area context
```

Lineage must not merge these blindly.

Use:

```text
AttributeUsage
FieldEndpoint
EntityContext
```

to keep context-specific paths separate.

---

## 13. Lineage levels

Lineage should support several levels of detail.

### 13.1 Level 1 — Business lineage

For business users.

Shows:

```text
Source business concept
Mapping/logic
Target business attribute
Validation
Owner
```

Example:

```text
Legacy Customer Group
  → mapped to
Customer Group in S/4 Sales Area
  → checked by
Allowed Values Validation
```

### 13.2 Level 2 — Technical field lineage

For analysts/consultants.

Shows:

```text
Legacy CRM CUSTOMER_SALES.CUST_GROUP
  → MAP-CUST-GROUP-LEGACY-TO-KNVV-KDGRP
  → S/4HANA KNVV-KDGRP
```

### 13.3 Level 3 — Value lineage

For value mapping issues.

Shows:

```text
A17
  → unresolved / mapped to 01
  → target ValueList VLIST-S4-KNVV-KDGRP
  → validation result
```

### 13.4 Level 4 — Validation lineage

For testing.

Shows:

```text
Attribute
  → ValidationRule
  → DataQualityCheck
  → Dataset
  → ValidationResult
  → Issue
```

### 13.5 Level 5 — Governance lineage

For stewards/AMS.

Shows:

```text
Attribute
  → Issue
  → Decision
  → ChangeRequest
  → Evidence
  → Owner
```

MVP should implement levels 1–3 first, then 4–5.

---

## 14. Lineage path model

A lineage path is an ordered chain of nodes and edges.

Recommended internal shape:

```json
{
  "path_id": "LP-ATTR-CUST-SALES-CUSTOMER-GROUP-001",
  "start_object_id": "ATTR-CUST-SALES-CUSTOMER-GROUP",
  "path_type": "source_to_target",
  "nodes": [
    "FEP-LEGACY-CUSTOMER-GROUP",
    "MAP-CUST-GROUP-LEGACY-TO-KNVV-KDGRP",
    "VMAP-LEGACY-CUST-GROUP-TO-S4-KDGRP",
    "FEP-DATASET-CUSTOMER-GROUP",
    "FEP-S4-KNVV-KDGRP",
    "VAL-CUST-GROUP-ALLOWED-VALUES"
  ],
  "edges": [],
  "confidence": "explicit"
}
```

### 14.1 Path types

```text
source_to_target
target_to_source
attribute_to_representations
attribute_to_validations
attribute_to_datasets
attribute_to_governance
value_mapping_path
interface_path
support_diagnostic_path
```

---

## 15. Impact model

Impact starts from a changed object and finds affected objects.

### 15.1 Impact start object

Examples:

```text
Attribute changed
FieldEndpoint changed
ValueList changed
ValueMapping changed
Mapping changed
TransformationLogic changed
ValidationRule changed
Dataset changed
Interface changed
Owner changed
Decision changed
Issue resolved
```

### 15.2 Impact categories

Impact should be grouped by category.

```text
semantic impact
physical field impact
mapping impact
value mapping impact
validation impact
dataset impact
interface impact
governance impact
owner impact
issue/risk impact
decision impact
report/handover impact
AI context impact
```

### 15.3 Impact depth

Use traversal depth to avoid noisy reports.

Recommended MVP depth:

```text
depth 1 = directly connected objects
depth 2 = affected dependencies
depth 3 = broader downstream objects
```

MVP default:

```text
depth 2
```

Allow advanced users to expand depth.

---

## 16. Impact direction modes

Impact traversal should support direction modes.

### 16.1 Downstream impact

Question:

```text
What depends on this object?
```

Example:

```text
ValueList changed
  → ValueMapping affected
  → ValidationRule affected
  → Dataset checks affected
  → Issues/reports affected
```

### 16.2 Upstream impact

Question:

```text
What does this object depend on?
```

Example:

```text
ValidationRule failed
  → FieldEndpoint checked
  → Attribute validated
  → ValueList used
  → Mapping/value mapping used
```

### 16.3 Bidirectional impact

Question:

```text
What is connected to this object and may require review?
```

Useful for:

```text
Attribute
Issue
ChangeRequest
PatchProposal
```

### 16.4 Governance impact

Question:

```text
Who needs to know or approve?
```

Traverses:

```text
owner
decision
issue
risk
change request
evidence
```

---

## 17. Impact severity model

Impact should not only list objects. It should classify risk.

### 17.1 Severity levels

```text
low
medium
high
critical
```

### 17.2 Suggested severity rules

Critical:

```text
Change affects approved mapping used for cutover.
Change affects active validation for critical attribute.
Change affects target value list used by many records.
Change affects unresolved high-severity issue.
Change breaks SAP context rule.
```

High:

```text
Change affects multiple datasets.
Change affects owner-approved value mapping.
Change affects active transformation logic.
Change affects AMS handover-critical attribute.
```

Medium:

```text
Change affects one mapping or validation.
Change affects draft issue or decision.
Change requires owner review.
```

Low:

```text
Documentation-only change.
Description update.
Non-critical evidence link update.
```

### 17.3 Impact confidence

Impact should also have confidence:

```text
certain
likely
possible
unknown
```

Deterministic relationships produce `certain`.

AI-suggested relationships produce `possible` until approved.

---

## 18. Change type model

Impact depends on what kind of change happened.

### 18.1 Attribute changes

Examples:

```text
business meaning changed
name changed
context changed
owner changed
status changed
data classification changed
```

Impact should check:

```text
AttributeUsage
FieldEndpoint
Mapping
ValidationRule
Issue
Decision
Owner
SearchDocument
AMS handover
```

### 18.2 FieldEndpoint changes

Examples:

```text
SAP table changed
SAP field changed
entity context changed
data type changed
length changed
system/environment changed
```

Impact should check:

```text
Attribute
AttributeUsage
Mapping
ValueMapping
ValidationRule
Dataset
Interface
SAP context validation
```

### 18.3 Mapping changes

Examples:

```text
source endpoint changed
target endpoint changed
mapping type changed
logic changed
status changed
```

Impact should check:

```text
source/target endpoints
value mappings
transformation logic
validations
datasets
issues
owners
```

### 18.4 ValueList changes

Examples:

```text
new target value
removed target value
deprecated value
environment changed
snapshot updated
```

Impact should check:

```text
ValueMapping entries
ValidationRule allowed values
Dataset values
Open unresolved values
Configuration issues
AMS handover
```

### 18.5 ValueMapping changes

Examples:

```text
source value mapped
target value changed
condition changed
entry approved/deprecated
```

Impact should check:

```text
Mapping
ValueList
ValidationRule
Dataset observed values
Issue
Decision
ChangeRequest
```

### 18.6 ValidationRule changes

Examples:

```text
severity changed
condition changed
value list changed
field endpoint changed
rule activated/deprecated
```

Impact should check:

```text
DataQualityCheck
Dataset
GapReport
Issue
ReadinessReport
AMS handover
```

### 18.7 Dataset changes

Examples:

```text
new extract received
column added
column removed
values changed
profile updated
```

Impact should check:

```text
FieldEndpoint matches
Mappings
ValueMappings
ValidationRules
GapReport
Issues
```

### 18.8 Owner changes

Impact should check:

```text
Attributes
Mappings
Validations
Issues
Decisions
Approvals
AMS handover owner map
```

### 18.9 Decision changes

Impact should check:

```text
Objects explained by decision
ChangeRequests
Issues
Evidence
Reports
```

---

## 19. Impact report structure

A standard ImpactReport should contain:

```text
1. Changed object
2. Change type
3. Impact summary
4. Directly affected objects
5. Indirectly affected objects
6. Affected mappings
7. Affected value mappings
8. Affected validations/checks
9. Affected datasets/profiles
10. Affected interfaces
11. Affected issues/risks
12. Affected decisions/change requests
13. Affected owners/stewards
14. Affected reports/handover outputs
15. Recommended actions
16. Human review checklist
17. AI summary if enabled
18. Generated metadata
```

### 19.1 Impact report JSON shape

```json
{
  "report_id": "IMPACT-20260426-ATTR-CUST-SALES-CUSTOMER-GROUP",
  "start_object_id": "ATTR-CUST-SALES-CUSTOMER-GROUP",
  "change_type": "attribute_logic_change",
  "generated_at": "2026-04-26T21:00:00+02:00",
  "impact_depth": 2,
  "summary": "Customer Group change affects mapping, value mapping, validation, dataset profiling, and owner review.",
  "affected": {
    "attributes": [],
    "field_endpoints": [],
    "mappings": [],
    "value_mappings": [],
    "value_lists": [],
    "logic": [],
    "validations": [],
    "datasets": [],
    "interfaces": [],
    "issues": [],
    "decisions": [],
    "owners": [],
    "reports": []
  },
  "recommended_actions": [],
  "validation_warnings": [],
  "confidence": "certain"
}
```

---

## 20. Recommended actions model

Impact reports should generate deterministic recommended actions.

Examples:

### 20.1 ValueList changed

Recommended actions:

```text
Re-check target values in ValueMapping.
Re-run allowed values validation.
Check unresolved source values.
Review environment-specific configuration evidence.
Notify responsible data steward.
Update AMS handover if value behavior changed.
```

### 20.2 Mapping changed

Recommended actions:

```text
Re-run dataset mapping coverage.
Review related transformation logic.
Re-run affected validation rules.
Check open issues linked to mapping.
Confirm owner approval.
Create/attach ChangeRequest.
```

### 20.3 Attribute context changed

Recommended actions:

```text
Re-check SAP context.
Re-check grain.
Review FieldEndpoints.
Review requiredness rules.
Review validations.
Check downstream reports/handover.
```

### 20.4 Dataset changed

Recommended actions:

```text
Reprofile dataset.
Detect unknown columns.
Detect missing required columns.
Detect unmapped source values.
Create issues for high-severity gaps.
```

---

## 21. Lineage and impact graph generation

The graph should be generated from canonical files.

### 21.1 Build process

```text
1. Parse canonical objects.
2. Build ObjectRegistry.
3. Resolve references.
4. Generate explicit edges.
5. Generate derived edges.
6. Validate edge targets.
7. Store edges in SQLite and JSONL.
8. Generate search documents.
9. Make graph available to LineageService and ImpactService.
```

### 21.2 Edge generation examples

From AttributeUsage:

```text
AttributeUsage.attribute
  → Attribute

AttributeUsage.entity_context
  → EntityContext

Attribute
  → used_in_context
  → EntityContext
```

From FieldEndpoint:

```text
FieldEndpoint.business_attribute
  → Attribute

Attribute
  → represented_by
  → FieldEndpoint

FieldEndpoint.entity_context
  → EntityContext
```

From Mapping:

```text
Mapping.source_endpoints
  → mapped_from
  → FieldEndpoint

Mapping.target_endpoints
  → mapped_to
  → FieldEndpoint

Mapping.value_mappings
  → uses_value_mapping
  → ValueMapping
```

From ValidationRule:

```text
ValidationRule.attribute
  → validates
  → Attribute

ValidationRule.field_endpoint
  → checks_endpoint
  → FieldEndpoint

ValidationRule.value_list
  → uses_value_list
  → ValueList
```

From Issue:

```text
Issue.affected_objects
  → affects
  → Object
```

From Decision:

```text
Decision.related_objects
  → explains
  → Object
```

From ChangeRequest:

```text
ChangeRequest.affected_objects
  → changes
  → Object
```

---

## 22. Generated storage model

### 22.1 SQLite table: `object_relationships`

Recommended columns:

```text
id
from_object_id
from_object_type
relationship_type
to_object_id
to_object_type
source_object_id
source_file
confidence
direction
created_from
created_at
```

### 22.2 SQLite table: `lineage_paths`

Optional generated/cache table.

```text
path_id
start_object_id
path_type
depth
nodes_json
edges_json
confidence
generated_at
```

MVP can compute paths on demand.

### 22.3 SQLite table: `impact_reports`

Optional generated/cache table.

```text
report_id
start_object_id
change_type
impact_depth
affected_json
recommended_actions_json
generated_at
```

MVP can write reports under:

```text
generated/reports/impact/
```

### 22.4 JSONL edge export

```text
generated/lineage_edges.jsonl
```

Each line:

```json
{
  "from_object_id": "ATTR-CUST-SALES-CUSTOMER-GROUP",
  "relationship_type": "represented_by",
  "to_object_id": "FEP-S4-KNVV-KDGRP",
  "confidence": "explicit"
}
```

---

## 23. Traversal rules

### 23.1 Default traversal depth

```text
lineage: path-specific, usually up to full source-to-target chain
impact: default depth 2
```

### 23.2 Avoid noisy traversal

Do not automatically traverse into every loosely related object.

Example:

```text
Attribute → Domain → all domain objects
```

This would make impact reports useless.

Mark some relationships as traversal-limited.

### 23.3 Relationship traversal classes

Classify edges:

```text
core_dependency
context
governance
evidence
reporting
weak_reference
```

Default impact should traverse:

```text
core_dependency
context
governance
```

But avoid broad traversal through:

```text
Domain
MigrationObject
generic report inclusion
weak evidence references
```

unless explicitly requested.

### 23.4 Traversal stop nodes

Default stop nodes may include:

```text
Domain
MigrationObject
System
Owner
Evidence
Report
```

They can be included in report, but should not expand to all their neighbors automatically.

---

## 24. Lineage query types

Supported MVP queries:

```text
get_attribute_lineage(attribute_id)
get_endpoint_lineage(endpoint_id)
get_source_to_target_paths(attribute_id or endpoint_id)
get_value_mapping_lineage(value_mapping_id)
get_validation_lineage(validation_rule_id)
get_dataset_lineage(dataset_id)
```

### 24.1 Attribute lineage

Input:

```text
ATTR-CUST-SALES-CUSTOMER-GROUP
```

Output:

```text
all usages
all field endpoints
source endpoints
target endpoints
mappings
value mappings
logic
validations
datasets
issues/decisions
```

### 24.2 FieldEndpoint lineage

Input:

```text
FEP-S4-KNVV-KDGRP
```

Output:

```text
business attribute
entity context
source mappings
target usage
validations
value list
datasets
issues
```

### 24.3 Dataset lineage

Input:

```text
DATASET-CUSTOMER-SALES-AREA-LOAD
```

Output:

```text
columns
matched endpoints
matched attributes
mappings
validations
gaps
issues
```

---

## 25. Impact query types

Supported MVP queries:

```text
impact_of_attribute_change(attribute_id)
impact_of_endpoint_change(endpoint_id)
impact_of_mapping_change(mapping_id)
impact_of_value_list_change(value_list_id)
impact_of_value_mapping_change(value_mapping_id)
impact_of_validation_change(validation_rule_id)
impact_of_dataset_change(dataset_id)
impact_of_issue_resolution(issue_id)
impact_of_change_request(change_request_id)
```

### 25.1 Attribute change impact

Include:

```text
AttributeUsage
FieldEndpoint
Mapping
ValueMapping
ValidationRule
Dataset
Issue
Decision
Owner
Reports
AI search document
```

### 25.2 ValueList change impact

Include:

```text
ValueMapping entries using values
ValidationRule using value list
DataQualityCheck
Dataset values
Issues
Owners
Handover reports
```

### 25.3 Dataset change impact

Include:

```text
FieldEndpoint matches
Attribute matches
Mapping coverage
ValueMapping coverage
Validation rules
Gaps
Issues
```

---

## 26. Deterministic vs AI-assisted impact

### 26.1 Deterministic impact

The system must determine affected objects from:

```text
explicit relationships
derived relationships
validated references
dataset profiles
validation results
```

This is the authoritative impact base.

### 26.2 AI-assisted impact

AI may:

```text
summarize deterministic impact
explain business implications
suggest review checklist
draft issue/change request wording
identify possible missing relationships as hypotheses
```

AI must not:

```text
invent affected objects as confirmed
override deterministic graph
silently create canonical relationships
mark impact as complete if graph is incomplete
```

### 26.3 UI labeling

AI output should be labeled:

```text
AI summary
Assumptions
Possible additional impacts
Requires review
```

---

## 27. Gap-to-impact relationship

A Gap is often an impact trigger.

Example:

```text
Dataset contains unmapped value A17
```

This should create impact:

```text
ValueMapping affected
Attribute affected
Validation affected
Dataset affected
Owner affected
Issue suggested
Decision may be required
```

Gap types and impacts:

| Gap type | Likely affected objects |
|---|---|
| Unknown dataset column | Dataset, FieldEndpoint, Attribute |
| Missing required column | Dataset, FieldEndpoint, ValidationRule |
| Unmapped source value | ValueMapping, Mapping, Attribute, Issue |
| Target value not in ValueList | ValueList, ValueMapping, ValidationRule |
| Missing owner | Attribute/Mapping/Validation, Owner map |
| Missing validation | Attribute, ValidationRule, DataQualityCheck |
| Wrong SAP context | FieldEndpoint, EntityContext, AttributeUsage |

---

## 28. Integration with ChangeRequest

A ChangeRequest should include impact output.

When a ChangeRequest is created or approved, system should show:

```text
affected objects
impact summary
required validation reruns
required owner approvals
related issues/decisions
reports to update
```

ChangeRequest should link to ImpactReport when available.

Example:

```yaml
related_impact_reports:
  - IMPACT-CR-0021
```

---

## 29. Integration with PatchProposal

AI PatchProposal review should include impact preview.

Patch detail should show:

```text
proposed affected objects
deterministic impact preview
validation warnings
owner approval requirements
reports/handover affected
```

Patch cannot rely only on AI impact. It must run deterministic impact.

---

## 30. Integration with AMS handover

Impact analysis should support AMS handover.

When a field/rule/mapping changes, check if it affects:

```text
known issues
support diagnostics
validation checklist
owner map
decision history
AMS handover summary
```

AMS handover impact section:

```text
Support relevance:
  high / medium / low

Diagnostic impact:
  which checks or explanations must change

Known issue impact:
  which known issues become obsolete or need update

Owner impact:
  who AMS should contact after go-live
```

---

## 31. UI model for lineage

### 31.1 Attribute lineage view

Recommended sections:

```text
1. Summary path
2. Upstream sources
3. Mappings and logic
4. Target representations
5. Validations
6. Datasets
7. Downstream reports/handover
8. Issues/decisions
```

### 31.2 Path display

Use compact visual text first:

```text
Legacy CRM CUSTOMER_SALES.CUST_GROUP
  → Mapping: Legacy Customer Group to S/4 KDGRP
  → Value Mapping: Legacy CUST_GROUP to S/4 KDGRP
  → Dataset: CUSTOMER_GROUP
  → Target: S/4 KNVV-KDGRP
  → Validation: Allowed Values
```

### 31.3 Table display

Also provide table:

| Step | Type | Object | Context | Status |
|---|---|---|---|---|
| 1 | Source endpoint | Legacy CRM `CUSTOMER_SALES.CUST_GROUP` | Legacy sales | Active |
| 2 | Mapping | Legacy Customer Group → S/4 KDGRP | Customer Sales Area | Approved |
| 3 | Value Mapping | A17 → unresolved | CH01 | Open |
| 4 | Target endpoint | S/4 `KNVV-KDGRP` | Customer Sales Area | Active |
| 5 | Validation | Allowed Values | RS4 value list | Active |

### 31.4 Later graph display

Later, add graph view with:

```text
node filters
edge filters
depth control
impact highlighting
owner highlighting
issue highlighting
```

Graph should be optional, not mandatory.

---

## 32. UI model for impact

### 32.1 Impact report page

Sections:

```text
1. Changed object
2. Change type
3. Summary
4. Critical impact
5. Affected mappings
6. Affected validations
7. Affected datasets
8. Affected issues/risks
9. Affected decisions/change requests
10. Affected owners
11. Affected reports/handover
12. Recommended actions
13. AI explanation
```

### 32.2 Impact badges

Use badges:

```text
Direct
Indirect
Critical
Validation Required
Owner Review Required
Dataset Reprofile Required
AMS Handover Update
Open Issue
Decision Required
```

### 32.3 Impact actions

Actions:

```text
Create issue
Create ChangeRequest
Generate validation checklist
Generate AMS handover update
Create PatchProposal
Export impact report
```

---

## 33. Example: Customer Group CH01 / A17

### 33.1 Starting note

```text
Customer Group 7 in RS4 has no config for CH01 - A17 Footlocker.
There is a difference between P* and R* environments.
```

### 33.2 Related objects

```text
ATTR-CUST-SALES-CUSTOMER-GROUP
USE-CUST-SALES-CUSTOMER-GROUP-S4
CTX-CUSTOMER-SALES-AREA-S4
FEP-S4-KNVV-KDGRP
VLIST-S4-KNVV-KDGRP
VMAP-LEGACY-CUST-GROUP-TO-S4-KDGRP
VAL-CUST-GROUP-ALLOWED-VALUES
DATASET-CUSTOMER-SALES-AREA-LOAD
ISS-CH01-A17-CONFIG-GAP
```

### 33.3 Lineage path

```text
Legacy CRM CUSTOMER_SALES.CUST_GROUP
  → MAP-CUST-GROUP-LEGACY-TO-KNVV-KDGRP
  → VMAP-LEGACY-CUST-GROUP-TO-S4-KDGRP
  → Migration File CUSTOMER_GROUP
  → S/4HANA KNVV-KDGRP
  → VAL-CUST-GROUP-ALLOWED-VALUES
```

### 33.4 Impact if value list changes

Affected:

```text
ValueMapping:
  VMAP-LEGACY-CUST-GROUP-TO-S4-KDGRP

Validation:
  VAL-CUST-GROUP-ALLOWED-VALUES

Dataset:
  DATASET-CUSTOMER-SALES-AREA-LOAD

Issue:
  ISS-CH01-A17-CONFIG-GAP

Owner:
  ROLE-CUSTOMER-BP-STEWARD
  ROLE-S4-SD-FUNCTIONAL

Reports:
  Gap Report
  Impact Report
  AMS Handover Summary
```

Recommended actions:

```text
Confirm RS4 target configuration.
Confirm whether A17 target value exists.
Update ValueMapping if approved.
Re-run allowed value validation.
Update issue status.
Create/approve ChangeRequest.
Update AMS handover note.
```

---

## 34. Example: Payment Terms in two SAP contexts

Payment Terms may exist in:

```text
KNB1-ZTERM
  Customer Company Code context

KNVV-ZTERM
  Customer Sales Area context
```

Lineage model must show separate paths:

```text
ATTR-CUST-PAYMENT-TERMS
  → USE-CUST-PAYMENT-TERMS-COMPANY-CODE
    → FEP-S4-KNB1-ZTERM

  → USE-CUST-PAYMENT-TERMS-SALES-AREA
    → FEP-S4-KNVV-ZTERM
```

Impact model must separate:

```text
Change to KNB1-ZTERM logic
  impacts company-code validations and finance owner

Change to KNVV-ZTERM logic
  impacts sales-area validations and sales owner
```

Do not collapse both into one generic field path unless the business explicitly approves shared semantics.

---

## 35. Report output examples

### 35.1 Simple impact report

```markdown
# Impact Report: Customer Group

Changed object:
ATTR-CUST-SALES-CUSTOMER-GROUP

Primary SAP target:
S/4HANA KNVV-KDGRP

Context:
Customer Sales Area

Directly affected:
- FEP-S4-KNVV-KDGRP
- MAP-CUST-GROUP-LEGACY-TO-KNVV-KDGRP
- VMAP-LEGACY-CUST-GROUP-TO-S4-KDGRP
- VAL-CUST-GROUP-ALLOWED-VALUES

Open issues:
- ISS-CH01-A17-CONFIG-GAP

Owners:
- ROLE-CUSTOMER-BP-STEWARD
- ROLE-S4-SD-FUNCTIONAL

Recommended actions:
- Confirm target value list.
- Re-run allowed values validation.
- Review unresolved source value A17.
- Create or update ChangeRequest.
```

### 35.2 Lineage report

```markdown
# Lineage Report: Customer Group

Business Attribute:
Customer Group

Context:
Customer Sales Area

Source:
Legacy CRM CUSTOMER_SALES.CUST_GROUP

Mapping:
Legacy Customer Group to S/4 KDGRP

Value Mapping:
Legacy CUST_GROUP → S/4 KDGRP

Target:
S/4HANA KNVV-KDGRP

Validation:
Customer Group must be in approved S/4 value list
```

---

## 36. API design

Recommended lineage endpoints:

```text
GET  /api/lineage/attributes/{id}
GET  /api/lineage/endpoints/{id}
GET  /api/lineage/datasets/{id}
GET  /api/lineage/path?from={id}&to={id}
```

Recommended impact endpoints:

```text
POST /api/impact
GET  /api/impact/reports/{id}
POST /api/impact/objects/{id}
```

Example impact request:

```json
{
  "object_id": "VLIST-S4-KNVV-KDGRP",
  "change_type": "value_list_updated",
  "direction": "downstream",
  "depth": 2,
  "include_governance": true,
  "include_reports": true
}
```

Example response:

```json
{
  "start_object_id": "VLIST-S4-KNVV-KDGRP",
  "change_type": "value_list_updated",
  "affected": {
    "value_mappings": ["VMAP-LEGACY-CUST-GROUP-TO-S4-KDGRP"],
    "validations": ["VAL-CUST-GROUP-ALLOWED-VALUES"],
    "datasets": ["DATASET-CUSTOMER-SALES-AREA-LOAD"],
    "issues": ["ISS-CH01-A17-CONFIG-GAP"],
    "owners": ["ROLE-CUSTOMER-BP-STEWARD"]
  },
  "recommended_actions": []
}
```

---

## 37. CLI design

Recommended commands:

```bash
modelops lineage ATTR-CUST-SALES-CUSTOMER-GROUP
modelops lineage FEP-S4-KNVV-KDGRP
modelops lineage --from FEP-LEGACY-CUSTOMER-GROUP --to FEP-S4-KNVV-KDGRP

modelops impact ATTR-CUST-SALES-CUSTOMER-GROUP
modelops impact VLIST-S4-KNVV-KDGRP --change-type value_list_updated
modelops impact DATASET-CUSTOMER-SALES-AREA-LOAD --direction downstream

modelops report impact ATTR-CUST-SALES-CUSTOMER-GROUP --out generated/reports/impact/
```

---

## 38. Acceptance criteria examples

These examples should be mirrored in `ACCEPTANCE_CRITERIA.md`.

### 38.1 Attribute lineage

```text
Given an Attribute has related FieldEndpoints, Mapping, ValueMapping, and ValidationRule
When the user opens lineage for the Attribute
Then the system shows source endpoint, mapping, target endpoint, value mapping, and validation rule in order.
```

### 38.2 KNVV context impact

```text
Given a FieldEndpoint has sap_table = KNVV
When lineage is displayed
Then the UI shows Customer Sales Area context and grain KUNNR + VKORG + VTWEG + SPART.
```

### 38.3 ValueList impact

```text
Given a ValueList is changed
When impact analysis runs
Then the system shows affected ValueMappings, Validations, Datasets, Issues, and Owners.
```

### 38.4 Dataset gap impact

```text
Given a dataset profile contains unmapped source value A17
When gap detection runs
Then the system links the gap to affected Attribute, ValueMapping, Dataset, and suggested Issue.
```

### 38.5 AI summary boundary

```text
Given impact analysis returns deterministic affected objects
When AI summary is generated
Then AI may summarize those objects but must not add unconfirmed affected objects as facts.
```

---

## 39. Testing strategy

### 39.1 Edge generation tests

```text
AttributeUsage creates Attribute → EntityContext relationship.
FieldEndpoint creates Attribute → FieldEndpoint relationship.
Mapping creates source → mapping → target relationships.
ValueMapping creates mapping → value list relationship.
ValidationRule creates validation → attribute/endpoint relationship.
Issue creates issue → affected object relationships.
Decision creates decision → explained object relationships.
ChangeRequest creates change → affected object relationships.
```

### 39.2 Lineage tests

```text
Attribute lineage returns all expected endpoints.
FieldEndpoint lineage returns source mappings and validations.
Dataset lineage returns matched attributes and gaps.
Payment Terms contexts remain separate for KNB1 and KNVV.
```

### 39.3 Impact tests

```text
ValueList change returns affected ValueMappings and Validations.
Mapping change returns affected target endpoint and validation.
Dataset change returns affected mappings and gaps.
Owner change returns affected attributes/issues/validations.
Issue resolution returns related ChangeRequest/Decision updates.
```

### 39.4 SAP-specific tests

```text
KNVV lineage displays sales-area context.
KNB1 lineage displays company-code context.
BP role is not shown as physical storage.
KNVV field impact includes sales-area datasets/validations.
```

### 39.5 AI boundary tests

```text
AI summary cannot add unconfirmed affected objects as facts.
AI-suggested relationship remains ai_suggested until approved.
PatchProposal impact preview uses deterministic graph.
```

---

## 40. MVP implementation phases

### Phase 1 — Relationship edge generation

Deliver:

```text
object_relationships generation
relationship JSONL export
basic graph traversal
```

### Phase 2 — Attribute and endpoint lineage

Deliver:

```text
attribute lineage
field endpoint lineage
source-target path
SAP context display
```

### Phase 3 — Mapping/value lineage

Deliver:

```text
mapping lineage
value mapping lineage
value list relationship
unresolved value impact
```

### Phase 4 — Dataset/gap impact

Deliver:

```text
dataset profile relationship
gap to affected objects
gap to issue draft
```

### Phase 5 — Impact reports

Deliver:

```text
impact query
impact report grouping
recommended actions
export to Markdown
```

### Phase 6 — Governance impact

Deliver:

```text
owners
issues
decisions
change requests
evidence
AMS handover impact
```

### Phase 7 — UI graph and advanced traversal

Deliver later:

```text
optional graph visualization
filters
depth control
relationship class control
```

### Phase 8 — Team/Git/PR impact

Deliver later:

```text
impact preview in patch review
impact report attached to ChangeRequest
impact check in CI/PR workflow
```

---

## 41. Modern architecture options

### 41.1 SQLite edge table

Recommended MVP.

Pros:

```text
simple
local-first
fast enough
easy to inspect
no extra infrastructure
```

Cons:

```text
less expressive than graph DB for complex traversal
manual traversal logic required
```

### 41.2 DuckDB analytical layer

Useful for dataset/profile impact.

Pros:

```text
fast profiling
good for CSV/Parquet
good local analytics
```

Cons:

```text
not necessary for relationship graph itself
```

Recommended use:

```text
DuckDB for dataset profiling and analytical checks.
SQLite for object index and relationships.
```

### 41.3 Graph database

Later option.

Pros:

```text
advanced graph queries
large relationship analysis
graph algorithms
```

Cons:

```text
overkill for MVP
more operational complexity
harder local packaging
```

Recommendation:

```text
Do not use graph DB until edge-table traversal becomes insufficient.
```

### 41.4 Open lineage export

Later option.

The product may later export lineage in an interoperable lineage-oriented format for enterprise tools.

Use only after internal model is stable.

Do not design MVP around external lineage standards before proving product workflows.

### 41.5 Git/PR impact checks

Later option.

```text
On pull request:
  run model validation
  generate impact report
  attach report to PR
  block merge on critical errors
```

This is a strong team governance pattern after local MVP.

### 41.6 MCP/tool access

Later option.

Expose deterministic tools:

```text
get_lineage
get_impact
validate_patch
find_affected_objects
```

Useful for external agents after API/CLI stabilizes.

---

## 42. Non-goals for MVP

Do not build in MVP:

```text
real-time runtime lineage from SAP systems
automatic ABAP code lineage extraction
automatic CPI iFlow reverse engineering
automatic SAP write-back
enterprise data catalog replacement
full graph database platform
Kafka/event-stream lineage
complex workflow engine
autonomous AI impact decisions
```

MVP lineage can be manually/semantically modeled and deterministically generated from repository objects.

That is enough to prove value.

---

## 43. Product quality bar

The lineage and impact model is good enough when a user can answer these questions quickly:

```text
Where does this field come from?
Where does it land in SAP?
Is the SAP context correct?
Which mapping and value mapping affect it?
Which validation checks it?
Which dataset contains it?
What issue/decision explains current behavior?
Who owns it?
What changes if this value list/mapping/rule changes?
What must AMS know?
```

The model is not good enough if:

```text
attribute and SAP field are collapsed
KNVV fields are not shown as sales-area-dependent
value mappings are disconnected from value lists
validation rules are disconnected from mappings/datasets
issues are not linked to affected objects
impact reports are generic text with no object links
AI invents impact without deterministic graph support
```

---

## 44. Final recommendation

Build lineage and impact as a deterministic graph over the file-based model repository.

Recommended MVP architecture:

```text
Canonical model files
  → Reference resolver
  → Relationship edge generator
  → SQLite object_relationships table
  → LineageService
  → ImpactService
  → UI path/table views
  → Markdown impact reports
  → AI summaries only on top of deterministic results
```

Start with:

```text
Attribute lineage
FieldEndpoint lineage
Mapping/value mapping lineage
Dataset gap impact
ValueList impact
Validation impact
Issue/decision/change impact
```

Avoid starting with:

```text
graph database
complex visual graph editor
real-time SAP lineage
AI-only impact analysis
```

The product value is not a pretty graph.

The product value is that a SAP migration team can see:

```text
what changed
what is affected
who owns it
what validation must run
which issue/decision explains it
what must be updated for cutover and AMS
```

That is the core of ModelOps for MDM.
