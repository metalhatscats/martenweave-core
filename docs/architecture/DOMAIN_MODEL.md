# ModelOps for MDM — Domain Model

Version: `0.2-draft`  
Document type: Product domain model / conceptual object model  
Scope: SAP migration, MDM, data governance, and AMS model knowledge  
Initial focus: SAP Business Partner migration model, Customer role slice first  
Audience: product architects, data analysts, SAP consultants, coding agents, AI workflow designers

---

## 1. Purpose

This document defines the **domain model** for ModelOps for MDM.

## MVP Domain Boundary

The first implementation uses this domain boundary:

```text
Parent domain:
  Business Partner

First role-dependent slice:
  Customer

First implementation context:
  Customer Sales Area

First end-to-end attribute:
  Customer Group

First target endpoint:
  KNVV-KDGRP
```

Do not model full Business Partner role complexity in the first cut. Model only the Customer role slice needed to prove traceability, validation, impact, and AI patch review.

It describes the main business concepts the product works with, how they relate, and how users should think about them.

This is not a database schema.

This is not a UI specification.

This is not a Pydantic/Zod schema.

It is the conceptual model that should guide:

- repository structure;
- object schemas;
- UI screens;
- validation rules;
- lineage and impact analysis;
- AI patch workflow;
- demo scripts;
- acceptance criteria;
- product positioning.

The domain model should be understandable to SAP migration, MDM, data governance, and AMS teams.

---

## 2. Core product idea

ModelOps for MDM manages the knowledge around master data models.

It does not manage master data records directly.

It manages:

```text
what fields mean
where fields live
how fields are mapped
how values are transformed
which values are allowed
which rules apply
how correctness is validated
who owns the knowledge
which decisions explain the design
which issues affect the model
what changes impact downstream work
```

The product is a model knowledge layer around SAP migration and AMS delivery.

---

## 3. Domain model in one line

```text
Domain
  → MigrationObject
  → Entity
  → EntityContext
  → Attribute
  → AttributeUsage
  → FieldEndpoint
  → Mapping
  → ValueList / ValueMapping / Logic
  → Rule
  → Validation
  → Dataset
  → Issue / Risk
  → Decision
  → ChangeRequest
  → Evidence
  → Owner
```

A more practical view:

```text
Business meaning
  = Attribute

Business/SAP context
  = EntityContext + AttributeUsage

Physical representation
  = FieldEndpoint

Movement/change of data
  = Mapping + ValueMapping + TransformationLogic

Correctness
  = BusinessRule + ValidationRule + DataQualityCheck

Governance
  = Owner + Issue + Decision + ChangeRequest + Evidence

Operational intelligence
  = Lineage + Impact + Gap + Report + AI PatchProposal
```

---

## 4. Most important distinction

The product must separate these concepts:

```text
Attribute
  ≠ SAP field

Attribute
  ≠ dataset column

Attribute
  ≠ mapping row

Attribute
  ≠ validation rule

Attribute
  ≠ BP role

Attribute
  ≠ value list
```

Example:

```text
Customer Group
  = business Attribute

KNVV-KDGRP
  = SAP FieldEndpoint

CUSTOMER_GROUP in migration file
  = dataset FieldEndpoint

Legacy CRM CUSTOMER_SALES.CUST_GROUP
  = source FieldEndpoint

Legacy value A17 → target value 01
  = ValueMapping entry

Allowed values in S/4
  = ValueList

"Customer Group must be valid for sales area"
  = BusinessRule / ValidationRule

CH01/A17 exception
  = Decision + Issue + ChangeRequest
```

This separation is the backbone of the product.

---

## 5. Conceptual object groups

The product domain is made of seven groups.

```text
1. Scope objects
2. Semantic model objects
3. Physical representation objects
4. Movement and transformation objects
5. Quality and validation objects
6. Governance and history objects
7. AI and operational intelligence objects
```

---

## 6. Scope objects

Scope objects define where the model applies.

```text
MasterDataDomain
MigrationObject
BusinessEntity
EntityContext
```

They answer:

```text
Which domain?
Which migration object?
Which business entity?
Which SAP/business context?
At what grain?
```

---

## 7. Semantic model objects

Semantic objects define business meaning.

```text
Attribute
AttributeUsage
BusinessRule
```

They answer:

```text
What does this field mean?
Where is this meaning valid?
Is it central, company-code, sales-area, role-specific, source-specific, or target-specific?
Which business rule applies?
```

---

## 8. Physical representation objects

Physical objects define where data appears.

```text
System
SystemEnvironment
SAPObject
FieldEndpoint
Interface
Dataset
DatasetColumn
```

They answer:

```text
Where does the value physically exist?
Which SAP table/field/API/file/report contains it?
Which environment?
Which interface moves it?
Which dataset has it?
```

---

## 9. Movement and transformation objects

Movement objects define how data moves and changes.

```text
MappingSet
Mapping
ValueList
ValueMapping
TransformationLogic
DefaultingRule
DerivationRule
EnrichmentRule
```

They answer:

```text
How does source become target?
Is it direct, derived, defaulted, value-mapped, conditional, or not migrated?
Which source values map to which target values?
Which logic changes the value?
```

---

## 10. Quality and validation objects

Quality objects define how correctness is checked.

```text
ValidationRule
DataQualityCheck
ValidationRun
ValidationResult
DataProfile
Gap
GapReport
```

They answer:

```text
What should be true?
How do we check it?
Which dataset was checked?
What failed?
Which gaps exist?
```

---

## 11. Governance and history objects

Governance objects define ownership, decisions, and controlled change.

```text
Owner
OwnershipRole
Team
Person
Issue
Risk
Decision
ChangeRequest
Evidence
AuditEvent
```

They answer:

```text
Who owns it?
What problem exists?
What risk exists?
Why was this decision made?
What change was approved?
What evidence supports it?
What happened?
```

---

## 12. AI and operational intelligence objects

AI and operational intelligence objects support safe assistance and generated knowledge.

```text
PatchProposal
ContextBundle
SearchDocument
LineagePath
ImpactReport
ValidationChecklist
ReadinessReport
AMSHandoverSummary
```

They answer:

```text
What does AI propose?
What context was used?
What is affected?
What should be validated?
What should AMS know?
```

---

## 13. Primary hierarchy

The main conceptual hierarchy:

```text
MasterDataDomain
  contains MigrationObject
    contains BusinessEntity
      has EntityContext
        uses AttributeUsage
          references Attribute
            represented by FieldEndpoint
```

Example:

```text
DOMAIN-CUSTOMER-BP
  MIGOBJ-CUSTOMER-BP
    ENTITY-CUSTOMER-SALES-AREA
      CTX-CUSTOMER-SALES-AREA-S4
        USE-CUST-SALES-CUSTOMER-GROUP-S4
          ATTR-CUST-SALES-CUSTOMER-GROUP
            FEP-S4-KNVV-KDGRP
```

This hierarchy is important because SAP fields often depend on context.

---

## 14. Relationship overview

```text
Domain
  owns scope for MigrationObjects, Entities, Attributes

MigrationObject
  defines migration scope and target

BusinessEntity
  defines conceptual object, e.g. Customer Sales Area

EntityContext
  defines system/business grain and SAP context

Attribute
  defines business meaning

AttributeUsage
  places Attribute into EntityContext

FieldEndpoint
  represents Attribute physically in system/file/table/API/report

Mapping
  connects source FieldEndpoint(s) to target FieldEndpoint(s)

ValueMapping
  maps source values to target values

ValueList
  defines allowed/reference values

TransformationLogic
  explains derivation/defaulting/enrichment

BusinessRule
  states expected business behavior

ValidationRule
  defines how to check correctness

DataQualityCheck
  executes or describes actual check

Dataset
  provides profiled data to compare with model

Issue
  captures problem or gap

Decision
  captures accepted reasoning

ChangeRequest
  captures approved model change

Evidence
  supports issue, decision, or change

Owner
  defines accountability

PatchProposal
  proposes model update before approval

ImpactReport
  shows affected objects when something changes
```

---

## 15. MasterDataDomain

### Meaning

A `MasterDataDomain` groups model knowledge around a master data area.

Examples:

```text
Customer / Business Partner
Supplier / Vendor
Material / Product
Finance Master Data
Employee / Workforce BP
```

### Responsibilities

A domain defines:

```text
business scope
main owners
related migration objects
entities
attributes
rules
issues
reports
```

### Example

```text
DOMAIN-CUSTOMER-BP
  Customer / Business Partner model knowledge for SAP migration and AMS
```

### Key relationships

```text
Domain → MigrationObject
Domain → BusinessEntity
Domain → Attribute
Domain → Issue
Domain → Decision
Domain → Owner
```

---

## 16. MigrationObject

### Meaning

A `MigrationObject` represents migration scope, not a single SAP table.

Example:

```text
Customer Business Partner Migration
```

This may involve:

```text
BUT000
BUT020
ADRC
ADR6
BUT0ID
KNB1
KNVV
KNVP
BP roles
source extracts
migration files
validation reports
```

### Responsibilities

A MigrationObject defines:

```text
scope
target system
in-scope entities
datasets
mapping sets
validation scope
cutover/AMS relevance
```

### Example

```text
MIGOBJ-CUSTOMER-BP
  includes:
    Business Partner central data
    Customer Company Code
    Customer Sales Area
    Partner Functions
    Address
    Tax/Identification
```

### Key relationships

```text
MigrationObject → BusinessEntity
MigrationObject → Dataset
MigrationObject → MappingSet
MigrationObject → ValidationRule
MigrationObject → Issue
```

---

## 17. BusinessEntity

### Meaning

A `BusinessEntity` is a conceptual object within a domain.

Examples:

```text
Business Partner
Customer
Customer Company Code
Customer Sales Area
Customer Partner Function
Address
Tax Number
Contact Person
```

### Responsibilities

A BusinessEntity defines:

```text
business object
grain
related contexts
attributes
scope boundaries
```

### Example

```text
ENTITY-CUSTOMER-SALES-AREA

Meaning:
Sales-area-dependent customer data.

Grain:
Customer + Sales Org + Distribution Channel + Division
```

### Key relationships

```text
BusinessEntity → EntityContext
BusinessEntity → AttributeUsage
BusinessEntity → FieldEndpoint
```

---

## 18. EntityContext

### Meaning

An `EntityContext` describes where and how an entity exists in a business/SAP/system context.

It is critical for SAP correctness.

Examples:

```text
BP Central in S/4HANA
Customer Company Code in S/4HANA
Customer Sales Area in S/4HANA
Customer Partner Function in S/4HANA
Legacy Customer Sales context
Migration Staging context
Validation Report context
```

### Responsibilities

EntityContext defines:

```text
system
context category
SAP tables
BP roles/UI maintenance context
grain
lifecycle status
validation scope
```

### Example

```text
CTX-CUSTOMER-SALES-AREA-S4

System:
SAP S/4HANA

SAP table:
KNVV

Related BP role/UI context:
FLCU01 / Customer Sales Area

Grain:
KUNNR + VKORG + VTWEG + SPART
```

### Key relationships

```text
EntityContext → BusinessEntity
EntityContext → System
EntityContext → SAPObject
EntityContext → AttributeUsage
EntityContext → FieldEndpoint
```

### Important rule

```text
KNVV fields belong to Customer Sales Area context.
KNB1 fields belong to Customer Company Code context.
BP roles are maintenance/governance context, not physical storage.
```

---

## 19. Attribute

### Meaning

An `Attribute` is a business meaning.

It is the central semantic object in the product.

Examples:

```text
Customer Group
Payment Terms
Tax Number
Sales District
Account Group
Reconciliation Account
Partner Function
Incoterms
```

### Responsibilities

Attribute defines:

```text
business name
business meaning
semantic category
data classification
default context if applicable
owners/stewards
related rules
related validations
related issues
related decisions
```

### Example

```text
ATTR-CUST-SALES-CUSTOMER-GROUP

Meaning:
Sales-area-dependent customer grouping used in sales processes and reporting.
```

### Key relationships

```text
Attribute → AttributeUsage
Attribute → FieldEndpoint
Attribute → BusinessRule
Attribute → ValidationRule
Attribute → Mapping
Attribute → Issue
Attribute → Decision
Attribute → Owner
```

### Important rule

Attribute should not contain all physical details directly.

Physical details belong to FieldEndpoint.

Context-specific behavior belongs to AttributeUsage.

---

## 20. AttributeUsage

### Meaning

`AttributeUsage` describes how an Attribute behaves in a specific context.

This object prevents flat, incorrect field modeling.

### Responsibilities

AttributeUsage defines:

```text
attribute
entity context
grain
requiredness
condition
migration relevance
validation relevance
maintenance context
scope
```

### Example

```text
USE-CUST-SALES-CUSTOMER-GROUP-S4

Attribute:
Customer Group

Context:
S/4HANA Customer Sales Area

Requiredness:
Conditional

Scope:
In-scope for selected sales organizations

Maintenance:
Customer sales-related BP role / Customer Sales Area UI
```

### Key relationships

```text
AttributeUsage → Attribute
AttributeUsage → EntityContext
AttributeUsage → SAPObject
AttributeUsage → ValidationRule
```

### When to use it

Use AttributeUsage when:

```text
same attribute exists in multiple SAP contexts
same attribute has different requiredness by context
same attribute is source/target/staging/reporting-specific
same field has different business interpretation by scope
```

---

## 21. System

### Meaning

A `System` represents a logical source, target, staging, governance, reporting, or validation system.

Examples:

```text
SAP S/4HANA
SAP ECC
SAP MDG
Legacy CRM
Migration Staging
File Share
Validation Tool
Data Warehouse
```

### Responsibilities

System defines:

```text
system category
role in migration
owner
related environments
interfaces
field endpoints
datasets
```

### Key relationships

```text
System → SystemEnvironment
System → FieldEndpoint
System → Interface
System → Dataset
```

---

## 22. SystemEnvironment

### Meaning

A `SystemEnvironment` represents an environment/client of a logical system.

Examples:

```text
S4 RS4
S4 PS4
MDG AM4
Legacy QA
Legacy PROD
```

### Responsibilities

SystemEnvironment defines:

```text
environment type
client
status
environment-specific value lists
configuration snapshots
issues
```

### Why it matters

Value lists and configuration may differ between environments.

Example:

```text
Customer Group value exists in P* but not in R*.
```

This should be modeled as an environment/configuration issue, not a vague note.

---

## 23. SAPObject

### Meaning

A `SAPObject` represents SAP-specific objects.

Examples:

```text
SAP table: KNVV
SAP table: KNB1
SAP table: BUT000
SAP BP role: FLCU01
SAP BP role: FLVN00
SAP transaction
SAP API
SAP IDoc segment
SAP custom table
SAP validation report
```

### Responsibilities

SAPObject defines:

```text
SAP object type
technical name
description
related entity contexts
related field endpoints
```

### Important rule

```text
SAP table storage, BP role, and UI maintenance context are related but not identical.
```

Example:

```text
KNVV-KDGRP
  physical storage: KNVV
  entity context: Customer Sales Area
  possible maintenance/UI context: FLCU01-related customer sales area role
```

---

## 24. FieldEndpoint

### Meaning

A `FieldEndpoint` is a physical or technical representation of a value.

It can be:

```text
SAP table field
SAP API field
SAP IDoc segment field
legacy table field
migration file column
staging table column
interface field
report column
validation output field
manual input field
```

### Responsibilities

FieldEndpoint defines:

```text
system
environment
endpoint type
technical name
SAP table/field or dataset column
business attribute
entity context
grain
data type
length
status
```

### Example

```text
FEP-S4-KNVV-KDGRP

System:
S/4HANA

Endpoint:
SAP table field KNVV-KDGRP

Business Attribute:
Customer Group

Entity Context:
Customer Sales Area

Grain:
KUNNR + VKORG + VTWEG + SPART
```

### Key relationships

```text
FieldEndpoint → Attribute
FieldEndpoint → EntityContext
FieldEndpoint → System
FieldEndpoint → Dataset
FieldEndpoint → Mapping
FieldEndpoint → ValidationRule
```

---

## 25. Interface

### Meaning

An `Interface` describes how data moves between systems.

Examples:

```text
file extract
manual upload
migration cockpit
IDoc
BAPI
RFC
OData
CPI iFlow
DRFOUT
MDG replication
custom ABAP report
validation export
```

### Responsibilities

Interface defines:

```text
source system
target system
direction
frequency
datasets
field endpoints
technical owner
functional owner
known issues
```

### Key relationships

```text
Interface → System
Interface → Dataset
Interface → FieldEndpoint
Interface → TransformationLogic
Interface → Issue
```

---

## 26. Dataset

### Meaning

A `Dataset` represents a migration file, source extract, staging file, validation input/output, value list snapshot, or report export.

It is not the model itself.

### Responsibilities

Dataset defines:

```text
dataset type
file/source reference
source system
target system
entity context
profile summary
columns
observed values
gap results
```

### Example

```text
DATASET-CUSTOMER-SALES-AREA-LOAD

Type:
Migration file

Context:
Customer Sales Area

Profile:
12,500 rows
84 columns
17 unmapped values
3 unknown columns
```

### Key relationships

```text
Dataset → FieldEndpoint
Dataset → DataProfile
Dataset → Gap
Dataset → Issue
Dataset → ValidationRun
```

---

## 27. MappingSet

### Meaning

A `MappingSet` groups related mappings.

Example:

```text
Legacy CRM to S/4 Customer Sales Area Mapping
```

### Responsibilities

MappingSet defines:

```text
source system
target system
entity context
scope
owner
status
mappings
```

### Key relationships

```text
MappingSet → Mapping
MappingSet → System
MappingSet → EntityContext
MappingSet → Owner
```

---

## 28. Mapping

### Meaning

A `Mapping` links source FieldEndpoint(s) to target FieldEndpoint(s).

### Responsibilities

Mapping defines:

```text
source endpoint(s)
target endpoint(s)
mapping type
transformation logic
value mapping
validation rules
owner
status
```

### Mapping types

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

### Example

```text
MAP-CUST-GROUP-LEGACY-TO-KNVV-KDGRP

Source:
Legacy CRM CUSTOMER_SALES.CUST_GROUP

Target:
S/4HANA KNVV-KDGRP

Type:
value_mapped

Uses:
VMAP-LEGACY-CUST-GROUP-TO-S4-KDGRP
```

### Key relationships

```text
Mapping → FieldEndpoint source
Mapping → FieldEndpoint target
Mapping → ValueMapping
Mapping → TransformationLogic
Mapping → ValidationRule
Mapping → Issue
Mapping → Decision
```

---

## 29. ValueList

### Meaning

A `ValueList` defines allowed/reference values.

Examples:

```text
S/4 Customer Group values
S/4 Payment Terms values
Sales Organization values
Distribution Channel values
Country codes
Account Groups
Tax categories
```

### Responsibilities

ValueList defines:

```text
source system
environment
technical source table/field
snapshot date
allowed values
value statuses
owner
related attributes
```

### Example

```text
VLIST-S4-KNVV-KDGRP

Source:
S/4HANA RS4

SAP source:
TVV1-KDGRP

Values:
01 Retail
02 Wholesale
```

### Key relationships

```text
ValueList → Attribute
ValueList → FieldEndpoint
ValueList → ValueMapping
ValueList → ValidationRule
ValueList → SystemEnvironment
```

---

## 30. ValueMapping

### Meaning

A `ValueMapping` maps source values to target values.

### Responsibilities

ValueMapping defines:

```text
source endpoint
target endpoint
target value list
mapping entries
conditions
statuses
unresolved values
owner
issues
```

### Example

```text
VMAP-LEGACY-CUST-GROUP-TO-S4-KDGRP

A17 → 01
B20 → 02
X99 → unresolved
```

### Key relationships

```text
ValueMapping → FieldEndpoint source
ValueMapping → FieldEndpoint target
ValueMapping → ValueList
ValueMapping → Mapping
ValueMapping → Issue
ValueMapping → Decision
```

### Important rule

An approved target value in ValueMapping must exist in the target ValueList.

---

## 31. TransformationLogic

### Meaning

`TransformationLogic` describes how values are derived, defaulted, enriched, normalized, or changed.

### Responsibilities

TransformationLogic defines:

```text
logic type
input endpoints
output endpoints
pseudo logic
implementation reference
owner
validations
```

### Logic types

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

### Example

```text
If sales_org = CH01 and legacy_customer_group = A17,
then target Customer Group requires special mapping.
Otherwise use standard value mapping.
```

### Key relationships

```text
TransformationLogic → FieldEndpoint input
TransformationLogic → FieldEndpoint output
TransformationLogic → Mapping
TransformationLogic → Interface
TransformationLogic → ValidationRule
```

---

## 32. BusinessRule

### Meaning

A `BusinessRule` states what should be true from a business point of view.

It is not necessarily executable.

### Responsibilities

BusinessRule defines:

```text
business statement
applies-to attributes
contexts
priority
owner
status
```

### Example

```text
Customer Group must be maintained for in-scope customer sales area records where sales process requires customer classification.
```

### Key relationships

```text
BusinessRule → Attribute
BusinessRule → EntityContext
BusinessRule → ValidationRule
BusinessRule → Owner
```

---

## 33. ValidationRule

### Meaning

A `ValidationRule` defines how correctness is checked.

### Responsibilities

ValidationRule defines:

```text
validation type
attribute
field endpoint
value list
condition
severity
failure message
owner
dataset scope
```

### Validation types

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

### Example

```text
Customer Group must be in approved S/4 Customer Group value list.
```

### Key relationships

```text
ValidationRule → Attribute
ValidationRule → FieldEndpoint
ValidationRule → ValueList
ValidationRule → BusinessRule
ValidationRule → DataQualityCheck
ValidationRule → Issue
```

---

## 34. DataQualityCheck

### Meaning

A `DataQualityCheck` is an executable or semi-executable implementation of a ValidationRule.

### Responsibilities

DataQualityCheck defines:

```text
validation rule
check engine
input dataset
column
expression or implementation reference
severity
last run status
```

### Check engines

```text
manual
pandas
polars
duckdb
sql
python
external
```

### Key relationships

```text
DataQualityCheck → ValidationRule
DataQualityCheck → Dataset
DataQualityCheck → ValidationRun
DataQualityCheck → ValidationResult
```

---

## 35. DataProfile

### Meaning

A `DataProfile` summarizes what was found in a Dataset.

### Responsibilities

DataProfile defines:

```text
row count
column count
columns
data types
blank counts
distinct values
sample values
profile date
profile scope
```

### Key relationships

```text
DataProfile → Dataset
DataProfile → Gap
DataProfile → ValueMapping
DataProfile → ValidationRule
```

---

## 36. Gap

### Meaning

A `Gap` is a detected mismatch between model and reality.

Examples:

```text
dataset column not in model
model attribute not in dataset
source value not mapped
target value not in ValueList
attribute without owner
attribute without validation
SAP context mismatch
```

### Responsibilities

Gap defines:

```text
gap type
severity
affected object
detected from
suggested action
suggested owner
issue draft
```

### Key relationships

```text
Gap → Dataset
Gap → Attribute
Gap → FieldEndpoint
Gap → Mapping
Gap → ValueMapping
Gap → Issue
```

A Gap may become an Issue after review.

---

## 37. Issue

### Meaning

An `Issue` is a known problem, defect, gap, or open question.

### Responsibilities

Issue defines:

```text
title
severity
status
issue type
affected objects
owner
related evidence
related decision
related change request
resolution
```

### Issue types

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

### Key relationships

```text
Issue → Attribute
Issue → FieldEndpoint
Issue → Mapping
Issue → ValueMapping
Issue → Dataset
Issue → Decision
Issue → ChangeRequest
Issue → Evidence
Issue → Owner
```

---

## 38. Risk

### Meaning

A `Risk` is a potential future problem that may affect migration, cutover, or AMS.

### Responsibilities

Risk defines:

```text
title
severity
probability
impact
affected objects
mitigation
owner
status
```

### Key relationships

```text
Risk → Attribute
Risk → Mapping
Risk → ValidationRule
Risk → Dataset
Risk → Issue
Risk → Owner
```

---

## 39. Decision

### Meaning

A `Decision` records accepted reasoning.

It explains why the model is the way it is.

### Responsibilities

Decision defines:

```text
decision
rationale
alternatives
consequences
affected objects
decision date
approver/owner
evidence
```

### Example

```text
For CH01, A17 requires special Customer Group handling.
```

### Key relationships

```text
Decision → Attribute
Decision → Mapping
Decision → ValueMapping
Decision → ValidationRule
Decision → Issue
Decision → ChangeRequest
Decision → Evidence
```

---

## 40. ChangeRequest

### Meaning

A `ChangeRequest` captures a controlled business/model change.

It is the business-level change log object.

### Responsibilities

ChangeRequest defines:

```text
change summary
change type
status
affected objects
before/after
requested by
approved by
related issues
related decisions
evidence
approval date
implementation date
```

### Key relationships

```text
ChangeRequest → Attribute
ChangeRequest → FieldEndpoint
ChangeRequest → Mapping
ChangeRequest → ValueMapping
ChangeRequest → ValidationRule
ChangeRequest → Issue
ChangeRequest → Decision
ChangeRequest → Evidence
ChangeRequest → PatchProposal
```

### Important rule

Every approved model change should have a ChangeRequest.

---

## 41. Evidence

### Meaning

`Evidence` captures source material supporting an issue, decision, or change.

Examples:

```text
email summary
ticket
workshop note
meeting note
Confluence page
SAP screenshot reference
SAP config export
Excel file reference
validation report
chat summary
```

### Responsibilities

Evidence defines:

```text
evidence type
source system
source date
summary
related objects
sensitivity
storage reference
```

### Key relationships

```text
Evidence → Issue
Evidence → Decision
Evidence → ChangeRequest
Evidence → PatchProposal
Evidence → Attribute
```

Evidence should often store summaries or references rather than raw sensitive content.

---

## 42. Owner / OwnershipRole / Team / Person

### Meaning

Ownership objects define accountability.

Recommended MVP approach:

```text
Use role-based ownership first.
Use person-level ownership only when needed.
```

### Responsibilities

Owner model defines:

```text
accountable role
responsible role
consulted roles
informed roles
team
person if applicable
responsibilities
```

### RACI interpretation

```text
Responsible = does the work
Accountable = owns the decision
Consulted = gives input
Informed = must know
```

### Key relationships

```text
Owner → Attribute
Owner → Mapping
Owner → ValidationRule
Owner → Issue
Owner → Decision
Owner → ChangeRequest
```

---

## 43. PatchProposal

### Meaning

A `PatchProposal` is a proposed model update before approval.

It may be created by:

```text
user
AI
importer
system gap detection
```

### Responsibilities

PatchProposal defines:

```text
source evidence
affected objects
proposed changes
new objects
assumptions
questions
required human checks
validation result
review status
```

### Key relationships

```text
PatchProposal → Evidence
PatchProposal → ChangeRequest
PatchProposal → Issue
PatchProposal → Attribute
PatchProposal → Mapping
PatchProposal → ValueMapping
PatchProposal → ValidationRule
```

### Important rule

PatchProposal may propose changes, but canonical files change only after human approval.

---

## 44. ContextBundle

### Meaning

A `ContextBundle` is a bounded AI input package.

It is not a canonical business object, but it is important for AI safety.

### Responsibilities

ContextBundle defines:

```text
task
source evidence
primary objects
related objects
open issues
recent decisions
validation results
allowed actions
disallowed actions
output schema
```

### Key relationships

```text
ContextBundle → PatchProposal
ContextBundle → SearchDocument
ContextBundle → Evidence
```

---

## 45. SearchDocument

### Meaning

A `SearchDocument` is generated for search and AI retrieval.

It is not canonical.

### Responsibilities

SearchDocument includes:

```text
object ID
object type
title/name
domain
context
technical names
summary
related objects
search text
```

### Key relationships

```text
SearchDocument → canonical object
```

---

## 46. LineagePath

### Meaning

A `LineagePath` shows how data moves and changes.

It is generated from relationships.

### Responsibilities

LineagePath answers:

```text
Where does this value come from?
How is it transformed?
Where does it land?
Where is it validated?
Where is it used downstream?
```

### Example

```text
Legacy CRM CUSTOMER_SALES.CUST_GROUP
  → MAP-CUST-GROUP-LEGACY-TO-KNVV-KDGRP
  → VMAP-LEGACY-CUST-GROUP-TO-S4-KDGRP
  → Migration File CUSTOMER_GROUP
  → S/4 KNVV-KDGRP
  → VAL-CUST-GROUP-ALLOWED-VALUES
```

### Key relationships

```text
LineagePath → FieldEndpoint
LineagePath → Mapping
LineagePath → ValueMapping
LineagePath → TransformationLogic
LineagePath → ValidationRule
```

---

## 47. ImpactReport

### Meaning

An `ImpactReport` shows what is affected if an object changes.

It is generated from relationships.

### Responsibilities

ImpactReport answers:

```text
What mappings are affected?
What validations are affected?
What datasets are affected?
What issues are affected?
What owners must be notified?
What decisions explain this?
What reports/handover sections must change?
```

### Key relationships

```text
ImpactReport → changed object
ImpactReport → affected objects
ImpactReport → Owner
ImpactReport → Issue
ImpactReport → Decision
ImpactReport → ChangeRequest
```

---

## 48. Report objects

Generated or controlled report types:

```text
RepositoryHealthReport
GapReport
ImpactReport
ValidationChecklist
GoLiveReadinessReport
AMSHandoverSummary
AttributeDetailExport
LineageReport
```

Reports are usually generated artifacts.

They may reference canonical objects.

---

## 49. SAP Customer / BP domain example

### 49.1 Customer Group example

```text
Domain:
  DOMAIN-CUSTOMER-BP

MigrationObject:
  MIGOBJ-CUSTOMER-BP

BusinessEntity:
  ENTITY-CUSTOMER-SALES-AREA

EntityContext:
  CTX-CUSTOMER-SALES-AREA-S4

Attribute:
  ATTR-CUST-SALES-CUSTOMER-GROUP

AttributeUsage:
  USE-CUST-SALES-CUSTOMER-GROUP-S4

FieldEndpoint:
  FEP-S4-KNVV-KDGRP

Mapping:
  MAP-CUST-GROUP-LEGACY-TO-KNVV-KDGRP

ValueList:
  VLIST-S4-KNVV-KDGRP

ValueMapping:
  VMAP-LEGACY-CUST-GROUP-TO-S4-KDGRP

ValidationRule:
  VAL-CUST-GROUP-ALLOWED-VALUES

Issue:
  ISS-CH01-A17-CONFIG-GAP

Decision:
  DEC-CH01-A17-CUSTOMER-GROUP

ChangeRequest:
  CR-0021
```

### 49.2 Correct interpretation

```text
Customer Group is the business Attribute.
KNVV-KDGRP is one SAP FieldEndpoint.
The context is Customer Sales Area.
The grain is KUNNR + VKORG + VTWEG + SPART.
FLCU01 may be related as maintenance/BP role context, not physical storage.
```

---

## 50. Payment Terms example

Payment Terms may exist in more than one SAP context.

```text
KNB1-ZTERM
  company-code-dependent payment terms

KNVV-ZTERM
  sales-area-dependent payment terms
```

Modeling options:

### Option A — one Attribute, multiple usages

Use when business meaning is shared.

```text
ATTR-CUST-PAYMENT-TERMS
  USE-CUST-PAYMENT-TERMS-COMPANY-CODE
  USE-CUST-PAYMENT-TERMS-SALES-AREA
```

### Option B — separate Attributes

Use when ownership, rules, lifecycle, or process differs materially.

```text
ATTR-CUST-FI-PAYMENT-TERMS
ATTR-CUST-SD-PAYMENT-TERMS
```

Decision rule:

```text
If owner, rule, grain, or process differs strongly, separate attributes.
If only physical representation differs, use one attribute with multiple usages.
```

---

## 51. Data quality model

The domain model should support these quality dimensions:

```text
completeness
validity
consistency
uniqueness
accuracy
timeliness
conformity
referential_integrity
mapping_coverage
ownership_coverage
validation_coverage
```

Quality relationship:

```text
BusinessRule
  → ValidationRule
    → DataQualityCheck
      → ValidationRun
        → ValidationResult
          → Issue or Gap
```

Example:

```text
Rule:
Customer Group must be valid for sales area.

Validation:
Customer Group must be in approved S/4 value list.

Check:
Compare CUSTOMER_GROUP column against VLIST-S4-KNVV-KDGRP.

Result:
17 records contain unmapped or invalid values.

Issue:
Create value mapping gap issue.
```

---

## 52. Governance model

Governance is not an extra module.

It is part of every important object.

Every important object should be able to answer:

```text
Who owns it?
Who approved it?
What decision explains it?
What issue changed it?
What evidence supports it?
What ChangeRequest introduced it?
Is it active, draft, deprecated, or retired?
```

Governance relationships:

```text
Object
  → Owner
  → Issue
  → Decision
  → ChangeRequest
  → Evidence
```

---

## 53. Lifecycle model

Most canonical objects should support lifecycle.

Common statuses:

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

Example lifecycle flow:

```text
draft
  → under_review
  → approved
  → active
  → deprecated
  → retired
```

Patch lifecycle:

```text
pending_review
  → accepted
  → rejected
  → superseded
```

Issue lifecycle:

```text
open
  → in_progress
  → blocked
  → resolved
  → closed
```

---

## 54. Data lifecycle alignment

The domain model should support the migration-to-AMS lifecycle.

### 54.1 Discovery

Objects created:

```text
draft attributes
draft endpoints
draft mappings
evidence summaries
issues/open questions
```

### 54.2 Design

Objects matured:

```text
approved attributes
approved mappings
business rules
value lists
value mappings
decisions
owners
```

### 54.3 Build

Objects added:

```text
interfaces
transformation logic
data quality checks
extensions
configuration evidence
```

### 54.4 SIT/UAT

Objects updated:

```text
dataset profiles
validation results
issues
change requests
patch proposals
```

### 54.5 Cutover

Objects/reports generated:

```text
readiness report
open risk list
final mapping coverage
validation checklist
```

### 54.6 AMS handover

Objects/reports used:

```text
attribute catalog
lineage
known issues
decisions
owners
validation rules
AMS handover summary
```

---

## 55. Relationship types

Recommended relationship vocabulary:

```text
belongs_to_domain
part_of_migration_object
has_entity
has_context
used_in_context
represented_by
physical_representation_of
mapped_from
mapped_to
uses_mapping
uses_value_list
uses_value_mapping
uses_logic
validates
checked_by
owned_by
approved_by
affected_by
affects
explained_by
supported_by
changed_by
proposed_by
used_in_interface
used_in_dataset
used_in_report
depends_on
supersedes
```

Relationship examples:

```text
ATTR-CUST-SALES-CUSTOMER-GROUP
  represented_by FEP-S4-KNVV-KDGRP

MAP-CUST-GROUP-LEGACY-TO-KNVV-KDGRP
  mapped_from FEP-LEGACY-CUSTOMER-GROUP
  mapped_to FEP-S4-KNVV-KDGRP
  uses_value_mapping VMAP-LEGACY-CUST-GROUP-TO-S4-KDGRP

VAL-CUST-GROUP-ALLOWED-VALUES
  validates ATTR-CUST-SALES-CUSTOMER-GROUP
  uses_value_list VLIST-S4-KNVV-KDGRP

ISS-CH01-A17-CONFIG-GAP
  affects ATTR-CUST-SALES-CUSTOMER-GROUP

DEC-CH01-A17-CUSTOMER-GROUP
  explains VMAP-LEGACY-CUST-GROUP-TO-S4-KDGRP
```

---

## 56. Cardinality guidelines

This is conceptual cardinality, not strict database schema.

```text
Domain
  has many MigrationObjects
  has many Attributes

MigrationObject
  has many BusinessEntities
  has many Datasets
  has many MappingSets

BusinessEntity
  has many EntityContexts

EntityContext
  has many AttributeUsages
  has many FieldEndpoints

Attribute
  has many AttributeUsages
  has many FieldEndpoints
  has many ValidationRules
  has many Issues/Decisions

FieldEndpoint
  may represent one Attribute
  may appear in many Mappings
  may appear in many ValidationRules

Mapping
  has one or more source endpoints
  has one or more target endpoints
  may use ValueMapping
  may use TransformationLogic

ValueMapping
  has many mapping entries
  usually uses one target ValueList

ValidationRule
  may have many DataQualityChecks

Issue
  may affect many objects

Decision
  may explain many objects

ChangeRequest
  may change many objects

PatchProposal
  may propose changes to many objects
```

---

## 57. Domain model validation principles

The domain model should enforce these conceptual rules:

```text
Attribute must not be treated as a SAP field.
FieldEndpoint must not exist without system/dataset context.
SAP field endpoints should have EntityContext.
KNVV endpoints require Customer Sales Area context.
KNB1 endpoints require Customer Company Code context.
ValueMapping approved target values must exist in ValueList.
Mapping must connect source and target endpoints unless explicitly out of scope.
Active critical attributes should have owner and validation.
Approved model changes should have ChangeRequest.
AI suggestions should become PatchProposal before canonical update.
```

---

## 58. Domain model and UI

Primary UI object should usually be:

```text
Attribute
```

Because users often ask:

```text
What is this field?
Where is it used?
What maps to it?
What validates it?
Who owns it?
```

But the UI must also allow entry by:

```text
SAP field
dataset column
mapping
issue
decision
dataset
owner
```

Recommended UI navigation around Attribute:

```text
Attribute
  Overview
  Contexts
  Representations
  Mappings
  Values
  Logic
  Validations
  Datasets
  Lineage
  Impact
  Issues
  Decisions
  Changes
  Owners
```

---

## 59. Domain model and AI

AI should reason over this domain model.

AI should not receive random files only.

AI context should contain:

```text
primary object
related objects
relationship edges
open issues
recent decisions
validation results
evidence summaries
allowed actions
```

AI actions should produce:

```text
PatchProposal
Issue draft
Decision draft
ChangeRequest draft
Report draft
```

AI must not produce direct approved model changes.

---

## 60. Domain model and acceptance criteria

Acceptance criteria should be written against domain behavior.

Examples:

```text
Given a FieldEndpoint has sap_table = KNVV,
When repository validation runs,
Then the endpoint must reference a Customer Sales Area EntityContext.

Given a Dataset contains a source value not present in ValueMapping,
When gap detection runs,
Then the system creates a value_mapping_gap with affected Attribute, Mapping, Dataset, and suggested Issue.

Given a PatchProposal affects an active Mapping,
When user approves it,
Then the system creates/updates ChangeRequest and rebuilds impact index.
```

---

## 61. Domain model boundaries

### 61.1 Inside product scope

```text
model knowledge
field meanings
field representations
mappings
value lists
value mappings
transformation logic
validation rules
dataset profiles
issues
decisions
change requests
evidence summaries
AI patch proposals
lineage and impact
AMS handover knowledge
```

### 61.2 Outside MVP scope

```text
full SAP master data records
direct SAP write-back
full MDG workflow replacement
enterprise data catalog replacement
real-time integration monitoring
automatic ABAP reverse engineering
large raw data lake
full workflow engine
```

---

## 62. Modern evolution variants

### 62.1 Local-first model repository

MVP.

```text
file-based canonical repository
SQLite generated index
AI patch proposal
Git diff
```

### 62.2 Git-backed model governance

Later.

```text
PatchProposal → branch → pull request → validation → merge
```

### 62.3 Hosted team workspace

Later.

```text
same domain model
server-side repository/index
Postgres
RBAC
enterprise audit
AI gateway
```

### 62.4 AMS operational memory layer

Later.

```text
incidents
known errors
diagnostics
support playbooks
mapped back to Attributes, FieldEndpoints, Validations, Decisions
```

The domain model should be stable enough to support all four variants.

---

## 63. Minimal MVP domain scope

MVP should support these objects first:

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
Dataset
MappingSet
Mapping
ValueList
ValueMapping
TransformationLogic
BusinessRule
ValidationRule
DataQualityCheck
OwnershipRole
Issue
Decision
ChangeRequest
Evidence
PatchProposal
LineagePath
ImpactReport
GapReport
```

MVP can defer:

```text
Person-level ownership
full Team model
advanced Risk model
ValidationRun history
large report library
graph database
workflow engine
enterprise RBAC
```

---

## 64. Product language guide

Use these terms consistently.

Use:

```text
Attribute
FieldEndpoint
EntityContext
AttributeUsage
Mapping
ValueMapping
ValueList
ValidationRule
Issue
Decision
ChangeRequest
PatchProposal
```

Avoid vague terms:

```text
field
rule
note
data thing
mapping row
AI memory
object
```

When using “field”, clarify:

```text
business attribute
SAP field endpoint
dataset column
source field
target field
```

---

## 65. Final conceptual model

The product can be summarized as:

```text
ModelOps for MDM manages a graph of model knowledge.

The graph connects:
  business meaning
  SAP/system representations
  mappings
  values
  rules
  validations
  datasets
  owners
  issues
  decisions
  changes
  evidence
  AI proposals

The graph enables:
  catalog
  lineage
  impact analysis
  gap detection
  patch review
  readiness reports
  AMS handover
```

The most important object is the Attribute, but the most important design decision is separating the Attribute from its FieldEndpoints and AttributeUsages.

That separation allows the product to correctly model SAP complexity without becoming a flat data dictionary.
