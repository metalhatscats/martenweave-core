<!-- modelops-freshness-ignore: all -->

# ModelOps for MDM — Import / Export Specification

Version: `0.1-draft`  
Document type: Operations specification  
Scope: Import/export behavior for model repositories, datasets, mappings, SAP metadata snapshots, evidence, reports, and AI patch inputs  
Product focus: SAP migration, MDM, data governance, validation, impact analysis, and AMS handover

---

## 1. Purpose

This document defines how ModelOps for MDM imports and exports information.

Import/export is not a secondary feature. It is one of the main operational entry points because SAP migration model knowledge usually starts outside the product:

```text
Excel mapping files
CSV/Excel migration datasets
SAP metadata exports
SAP value list/configuration snapshots
Jira/Confluence/ticket notes
emails and workshop notes
validation reports
local project folders
```

The product must bring this information into a structured model repository without corrupting approved model knowledge.

Core rule:

```text
Imported information is not automatically trusted.
It becomes staged input, evidence, a dataset profile, a gap report, or a PatchProposal.
Canonical model objects are updated only after validation and human approval.
```

---

## 2. Import / export design principles

### 2.1 File-first

MVP should prioritize file-based import/export:

```text
CSV
Excel
YAML
JSON
Markdown
JSONL
SQLite generated index
```

Do not start with live SAP/Jira/Confluence synchronization.

### 2.2 Snapshot-first

For SAP metadata, value lists, configuration, and validation outputs, import snapshots first.

Example:

```text
SAP value list export from RS4
  → ValueList snapshot
  → ValueMapping validation
  → issue/gap if mismatch exists
```

### 2.3 Patch-proposal-first

Imports that would affect canonical model objects must create:

```text
ImportReport
staged objects
PatchProposal
validation results
```

not direct edits.

### 2.4 Human approval

The system may propose changes, but the user approves them.

```text
External input
  → parse
  → normalize
  → validate
  → show report
  → create PatchProposal
  → human review
  → canonical update
```

### 2.5 Preserve source provenance

Every import should record:

```text
source file
source system
source environment
import timestamp
file hash
importer version
row/sheet/source reference where useful
```

### 2.6 Export from canonical/indexed model

Exports should be generated from:

```text
canonical model files
generated SQLite index
generated relationship edges
validation results
```

Exports are not the source of truth.

---

## 3. Import object lifecycle

Recommended import lifecycle:

```text
raw_input
  → parsed
  → normalized
  → validated
  → staged
  → proposed
  → approved
  → canonical
```

Operational meaning:

```text
raw_input:
  original file/text/source as provided

parsed:
  extracted rows/fields/text sections

normalized:
  converted into ModelOps object candidates

validated:
  checked against schemas, references, SAP rules, value lists

staged:
  saved under imports/ for review

proposed:
  PatchProposal created

approved:
  user approved changes

canonical:
  model/ files updated
```

---

## 4. Repository folders for import/export

Recommended folder structure:

```text
imports/
  raw/
  parsed/
  proposed/
  reports/
  rejected/

exports/
  catalogs/
  reports/
  handover/
  validation/
  impact/
  ai-context/
```

Generated exports may also live under:

```text
generated/reports/
generated/search_documents.jsonl
generated/lineage_edges.jsonl
generated/validation_results.jsonl
```

Suggested `.gitignore` policy:

```gitignore
# raw client inputs
imports/raw/
data/raw/

# generated exports unless intentionally committed
exports/
generated/

# local large/profiling artifacts
*.duckdb
*.sqlite
*.db
*.parquet
```

Small sample imports/exports may be committed under:

```text
data/samples/
schemas/examples/
docs/examples/
```

---

## 5. Import source types

MVP import sources:

```text
Excel mapping workbook
CSV/Excel dataset
YAML/Markdown canonical object
SAP value list/configuration snapshot
Validation report
Pasted note/email/ticket text
```

Later import sources:

```text
Jira issue
Confluence page
GitHub/GitLab file or PR
SAP read-only metadata API
Cloud ALM item
SolMan ticket
Data catalog export
```

Do not implement later connectors before file-based import proves useful.

---

## 6. Import type: Excel mapping workbook

### 6.1 Purpose

Convert existing mapping workbooks into structured model objects.

### 6.2 Typical input

Excel workbook containing columns such as:

```text
source system
source table/file
source field
target system
target table
target field
business name
mapping rule
transformation rule
value mapping reference
requiredness
validation note
owner
comments
status
```

### 6.3 Output candidates

```text
Attribute
AttributeUsage
FieldEndpoint
MappingSet
Mapping
ValueList
ValueMapping
TransformationLogic
BusinessRule
ValidationRule
Owner
Issue
Evidence
PatchProposal
ImportReport
```

### 6.4 Import flow

```text
1. User selects workbook.
2. System reads sheets.
3. System detects candidate header rows.
4. User maps workbook columns to internal import contract.
5. System parses rows.
6. System normalizes candidate objects.
7. System detects duplicates and conflicts.
8. System validates candidates.
9. System creates ImportReport.
10. User reviews.
11. System creates PatchProposal for approved candidates.
```

### 6.5 Matching logic

Preferred matching order:

```text
1. Existing object ID if present.
2. Exact SAP table-field match.
3. Exact source system + source field match.
4. Exact target system + target table + target field match.
5. Attribute name match.
6. Fuzzy match only as low-confidence suggestion.
```

### 6.6 Conflict examples

```text
Imported row maps KNVV-KDGRP to different Attribute than current model.
Imported row changes mapping type from direct to value_mapped.
Imported row references target value not in ValueList.
Imported row has target table KNVV but wrong context.
```

### 6.7 Acceptance criteria

```text
Given a mapping workbook contains source field, target table, target field, and mapping type,
When imported,
Then the system proposes FieldEndpoints and Mapping objects,
And does not overwrite approved canonical files directly.
```

---

## 7. Import type: CSV/Excel dataset

### 7.1 Purpose

Profile migration data files and compare them with the model.

### 7.2 Input

```text
CSV source extract
Excel load file
staging file
validation input file
validation output file
sample dataset
```

### 7.3 Output

```text
Dataset
DataProfile
Dataset column summary
Column-to-FieldEndpoint matches
GapReport
Issue drafts
ValueMapping gap findings
Validation input for DQ checks
```

### 7.4 Profiling flow

```text
1. User selects dataset file.
2. User chooses dataset type and domain/context.
3. System profiles row count and column count.
4. System profiles column names, blank counts, inferred types.
5. System optionally profiles distinct values for selected columns.
6. System matches columns to FieldEndpoints.
7. System detects unknown columns.
8. System detects missing required columns.
9. System detects unmapped source values.
10. System generates GapReport.
```

### 7.5 Privacy policy

Default behavior:

```text
Do not commit raw datasets.
Do not send raw records to AI.
Store profile summaries, not full client data.
Allow sample files only under data/samples/.
```

### 7.6 Acceptance criteria

```text
Given a profiled dataset contains column CUSTOMER_GROUP,
And no matching FieldEndpoint exists,
When gap detection runs,
Then the system creates a dataset-model gap with severity, dataset, column name, suggested match if any, proposed issue title, and suggested owner if available.
```

---

## 8. Import type: SAP value list / configuration snapshot

### 8.1 Purpose

Capture target configuration/reference values for validation and value mapping checks.

### 8.2 Typical input

```text
SAP table export
customizing export
manual Excel export
validation report export
configuration screenshot summary
```

Examples:

```text
Customer Group value list
Payment Terms value list
Sales Office / Group / District values
Distribution Channel values
Country values
Account Group values
```

### 8.3 Output

```text
ValueList
ValueList entries
SystemEnvironment reference
Evidence
ImportReport
Validation results for affected ValueMappings
```

### 8.4 Required snapshot metadata

```yaml
source_system: SYS-S4HANA
environment: ENV-S4-RS4
source_table: TVV1
source_field: KDGRP
snapshot_date: 2026-04-27
source_file: tvv1_rs4_export_20260427.xlsx
hash: ...
```

### 8.5 Acceptance criteria

```text
Given a ValueList snapshot is imported for ENV-S4-RS4,
When ValueMapping validation runs,
Then approved target values are checked against that environment-specific ValueList.
```

---

## 9. Import type: pasted note / email / ticket text

### 9.1 Purpose

Turn unstructured project communication into structured evidence and proposed model updates.

### 9.2 Input examples

```text
email
Teams/Slack note
Jira comment
workshop note
SAP defect summary
migration issue description
```

### 9.3 Output

```text
Evidence
PatchProposal
Issue draft
Decision draft
ChangeRequest draft
AI assumptions/questions
```

### 9.4 Flow

```text
1. User pastes text.
2. System creates Evidence summary.
3. System retrieves likely related objects.
4. AI creates structured proposal.
5. System validates proposal.
6. PatchProposal is created.
7. User reviews and approves/rejects.
```

### 9.5 Acceptance criteria

```text
Given user pastes a note about CH01 / A17 Customer Group gap,
When AI patch proposal is generated,
Then the system creates Evidence and PatchProposal with affected objects, assumptions, questions, and required human checks,
And does not update canonical model files before approval.
```

---

## 10. Import type: existing YAML/Markdown model objects

### 10.1 Purpose

Allow object files created outside the UI to be validated and added.

### 10.2 Input

```text
Markdown with YAML frontmatter
YAML object file
JSON object file
```

### 10.3 Flow

```text
1. User places file in model/ or imports through UI.
2. System parses object.
3. System validates common and type-specific schema.
4. System resolves references.
5. System shows result in Repository Health.
```

### 10.4 Acceptance criteria

```text
Given a Markdown object has valid frontmatter and unique ID,
When repository validation runs,
Then it is indexed and available in catalog/search.
```

---

## 11. Import reports

Every meaningful import should create an ImportReport.

Recommended path:

```text
imports/reports/IMPORT-20260427-CUSTOMER-MAPPING.md
```

Report sections:

```text
source file / source text
import timestamp
importer version
detected sheets/columns
parsed rows
candidate objects
matched existing objects
new proposed objects
conflicts
validation errors
warnings
low-confidence matches
recommended actions
PatchProposal link
```

ImportReport should be human-readable and machine-referenceable.

---

## 12. Import conflict handling

Conflict handling modes:

```text
skip
flag_conflict
create_draft
create_patch
create_new_version
reject
```

Default MVP behavior:

```text
flag_conflict
create ImportReport
allow PatchProposal after review
```

Common conflicts:

```text
duplicate ID
same technical field linked to different Attribute
mapping type changed
target value not in ValueList
SAP context mismatch
owner mismatch
status downgrade
attempt to overwrite active approved object
```

---

## 13. Import confidence levels

Every parsed candidate should have confidence.

```text
high
medium
low
unknown
```

Examples:

High confidence:

```text
exact ID match
exact SAP table-field match
explicit source-to-target mapping row
```

Medium confidence:

```text
exact field name but ambiguous context
business name match with one likely Attribute
```

Low confidence:

```text
AI inferred from free text
fuzzy label match
ambiguous source value
```

Low-confidence candidates should require explicit review.

---

## 14. Export types

MVP exports:

```text
Attribute Catalog CSV
Attribute Detail Markdown
Mapping Catalog CSV
ValueMapping CSV
Repository Health Markdown
GapReport Markdown/CSV
ImpactReport Markdown
ValidationChecklist Markdown
GoLiveReadinessReport Markdown
AMSHandoverSummary Markdown
JSON export for objects
JSONL search documents
SQLite generated index
```

Later exports:

```text
Excel workbook
PDF report
Confluence page
Jira issue
GitHub/GitLab PR summary
Data catalog export
OpenLineage-like export
```

---

## 15. Export: Attribute Catalog

### Purpose

Share catalog status outside product.

### Fields

```text
ID
Name
Domain
Entity Context
Primary SAP Target
Source Coverage
Mapping Status
Value Mapping Status
Validation Status
Owner
Lifecycle Status
Open Issues
Risk
Last Changed
```

### Acceptance criteria

```text
Given user filters Attribute Catalog by missing validation,
When exporting to CSV,
Then exported file contains only filtered rows and visible catalog columns.
```

---

## 16. Export: ImpactReport

### Purpose

Communicate consequences of a change.

### Sections

```text
changed object
change type
directly affected objects
indirectly affected objects
affected mappings
affected validations
affected datasets
affected owners
related issues/risks
related decisions/change requests
recommended actions
human review checklist
```

### Acceptance criteria

```text
Given user generates impact report for ValueList change,
When exporting to Markdown,
Then report includes affected ValueMappings, ValidationRules, Datasets, Issues, Owners, and recommended actions.
```

---

## 17. Export: AMS Handover Summary

### Purpose

Create support-ready knowledge for AMS.

### Sections

```text
domain/migration scope
key attributes
field representations
mappings and logic
validation checks
known issues
decisions
owners
diagnostic steps
open risks
handover actions
```

### Acceptance criteria

```text
Given an AMS handover summary is exported for Customer/BP domain,
Then it includes key attributes, SAP target fields, validations, known issues, decisions, owners, and support actions.
```

---

## 18. Export naming conventions

Recommended:

```text
exports/reports/impact/IMPACT-ATTR-CUST-SALES-CUSTOMER-GROUP-20260427.md
exports/handover/AMS-HANDOVER-CUSTOMER-BP-20260427.md
exports/catalogs/ATTRIBUTE-CATALOG-20260427.csv
exports/validation/VALIDATION-CHECKLIST-CUSTOMER-GROUP-20260427.md
```

File names should include:

```text
report type
scope/object ID
date
```

Avoid names like:

```text
final.xlsx
new_final_v2.xlsx
handover_latest.docx
```

---

## 19. Export provenance

Each export should include metadata:

```yaml
generated_at: 2026-04-27T12:00:00+02:00
generated_by: user/system
repository_schema_version: 0.1
source_repository_hash: ...
source_index_hash: ...
scope:
  domain: DOMAIN-CUSTOMER-BP
  objects:
    - ATTR-CUST-SALES-CUSTOMER-GROUP
```

This matters for audit and handover.

---

## 20. Import/export validation gates

Before import becomes canonical:

```text
schema validation must pass
references must resolve or be explicitly staged
SAP context checks must pass for SAP endpoints
value mapping checks must pass or create unresolved gap
owner/validation warnings must be visible
PatchProposal must be approved
```

Before export:

```text
repository health status should be shown
index freshness should be checked
report should state if warnings/errors exist
```

If repository is unhealthy, exports should include a warning.

---

## 21. CLI commands

Suggested MVP commands:

```bash
modelops import dataset path/to/file.xlsx
modelops import mapping path/to/mapping.xlsx
modelops import value-list path/to/tvv1.xlsx --env ENV-S4-RS4
modelops import note path/to/note.md

modelops export catalog attributes --format csv
modelops export impact ATTR-CUST-SALES-CUSTOMER-GROUP --format md
modelops export handover DOMAIN-CUSTOMER-BP --format md
modelops export health --format md
```

---

## 22. API endpoints

Suggested endpoints:

```text
POST /api/import/dataset
POST /api/import/mapping-workbook
POST /api/import/value-list
POST /api/import/note
GET  /api/import/reports/{id}

POST /api/export/catalog
POST /api/export/impact
POST /api/export/handover
POST /api/export/health
GET  /api/export/files/{id}
```

---

## 23. UI requirements

Import UI should show:

```text
source selection
detected structure
column mapping
preview rows
candidate objects
confidence
validation errors/warnings
ImportReport
create PatchProposal action
```

Export UI should show:

```text
scope selection
format selection
repository health warning
preview
download/export action
source metadata
```

---

## 24. Security and privacy

Rules:

```text
Do not commit raw client data by default.
Do not send raw imported datasets to external AI by default.
Do not store credentials in import files.
Do not export secrets.
Mark exports generated from unhealthy repositories.
Redact sensitive evidence where needed.
```

Future improvements:

```text
PII detection
data classification-based export filtering
export approval workflow
encrypted export package
```

---

## 25. Testing strategy

Required tests:

```text
Excel mapping import parses expected rows.
Invalid workbook creates ImportReport with errors.
Dataset profiling handles CSV and XLSX.
Unknown dataset columns create gaps.
ValueList import records environment and snapshot date.
ValueMapping target value is checked against ValueList.
Pasted note creates Evidence and PatchProposal.
Exported catalog respects filters.
Exported impact report includes required sections.
Raw datasets are not committed by default.
```

---

## 26. MVP scope

Must-have:

```text
CSV/Excel dataset profiling
dataset-model gap detection
ImportReport
Attribute Catalog CSV export
ImpactReport Markdown export
Repository Health export
AI note import to PatchProposal
```

Should-have:

```text
Excel mapping workbook import
ValueList snapshot import
AMSHandoverSummary export
ValidationChecklist export
JSON object export
```

Later:

```text
Jira/Confluence import/export
Git PR export
SAP live read connector
data catalog export
PDF export
```

---

## 27. Final recommendation

Import/export should be built as a controlled operational pipeline:

```text
Input
  → parse
  → normalize
  → validate
  → stage
  → report
  → propose
  → approve
  → canonical update
  → export/report
```

Do not allow imports to silently mutate approved model objects.

Do not treat exports as source of truth.

The product wins if it can safely convert messy project artifacts into structured, validated, traceable model knowledge.
