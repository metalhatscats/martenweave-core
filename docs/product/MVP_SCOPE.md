# MVP_SCOPE.md

# ModelOps for MDM — MVP Scope

Version: 0.1  
Status: Working MVP scope  
Product: ModelOps for MDM  
Category: MDM ModelOps Workspace  
Initial domain: SAP Business Partner migration  
Primary goal: prove that a lightweight model repository can reduce SAP migration model drift, validation gaps, and manual impact analysis.

---

## 1. MVP Summary

The MVP is a local-first workspace for managing a structured SAP Business Partner migration model.

Canonical MVP scope decision:

```text
MVP parent domain: Business Partner
First role-dependent slice: Customer
First implementation context: Customer Sales Area
First end-to-end attribute: Customer Group
First SAP target endpoint: KNVV-KDGRP
First demo change: CH01 / A17 Customer Group handling
```

It should let a migration or MDM team define core model objects, import sample datasets, compare datasets against the model, detect gaps, inspect attribute-level traceability, generate change impact reports, and use AI to propose structured updates from project notes or tickets.

The MVP is not an enterprise MDM platform, not an SAP MDG replacement, not a workflow engine, and not a full data catalog. It is a small operational model layer around migration knowledge.

Core MVP sentence:

> The MVP proves that SAP migration data model knowledge can be versioned, validated, traced, and prepared for safe AI-assisted delivery.

---

## 2. MVP Objective

The MVP must answer one practical question:

> When a field, mapping, rule, or dataset changes, can the team quickly see what is affected and what must be updated?

Success means the product can show:

- which business attribute is involved;
- which source and target fields represent it;
- which mappings and transformation rules depend on it;
- which validation checks use it;
- which dataset columns are missing, extra, or inconsistent;
- which owner or steward should review it;
- which issue or task should be created;
- which model update AI proposes, without applying it silently.

---

## 3. MVP Product Boundaries

### 3.1 In scope

The MVP includes:

1. Model repository creation and loading.
2. Structured files for domains, entities, attributes, mappings, validation rules, datasets, issues, and decisions.
3. SAP Business Partner starter model with Customer as the first role-dependent slice.
4. Attribute catalog and attribute detail view.
5. CSV/XLSX dataset import.
6. Dataset-to-model gap detection.
7. Basic deterministic validation checks.
8. Change impact report for one selected attribute or rule.
9. Issue/task creation from detected gaps.
10. AI-assisted patch proposal from pasted notes, emails, or tickets.
11. Human review before applying AI-generated changes.
12. Generated SQLite or DuckDB index for search, joins, and reporting.
13. Git-friendly file changes.

### 3.2 Out of scope

The MVP does not include:

1. Direct SAP system integration.
2. SAP MDG workflow replacement.
3. SAP transport management.
4. Direct Jira, Confluence, SolMan, or Cloud ALM integration.
5. Full enterprise data catalog functionality.
6. Role-based enterprise authorization.
7. Complex approval workflows.
8. Neo4j, Kafka, event streaming, or enterprise graph infrastructure.
9. Multi-tenant SaaS architecture.
10. Production-grade data profiling at scale.
11. Automated model changes without human approval.
12. Full DAMA compliance claims or official DAMA certification language.
13. All SAP master data domains.
14. Full Business Partner role complexity.
15. Full SAP customizing extraction.

The MVP should stay narrow. The first proof point is Business Partner model traceability through the Customer Sales Area slice, not broad enterprise governance.

---

## 4. Primary Users

### 4.1 Main MVP user

**SAP migration data analyst**

Responsible for migration templates, source-to-target mapping, field-level rules, dataset quality, and issue follow-up.

Needs to answer:

- Is the dataset aligned with the model?
- Which fields are missing or unexpected?
- Which mapping or validation rule changed?
- What is affected by this change?
- What task should be created?

### 4.2 Secondary MVP users

**MDM / data governance specialist**

Needs to understand ownership, definitions, data quality expectations, and stewardship gaps.

**SAP functional consultant**

Needs to connect business attributes to SAP tables, fields, roles, and migration objects.

**AMS handover recipient**

Needs a clean model explanation after go-live.

---

## 5. MVP Scenario

### 5.1 Main demo story

A migration team prepared a Business Partner model with the Customer role slice. During testing, the team discovers that a sales-area-related field has changed.

Example:

- `KNVV-KDGRP` Customer Group is required for selected sales areas.
- Source file contains `customer_group`, but the model marks the attribute as optional.
- A project note says Customer Group must now be mandatory for Sales Org `CH01` and Distribution Channel `01`.
- Existing validation rules do not cover this condition.

The MVP should:

1. Show the attribute in the catalog.
2. Show its business meaning, SAP representation, mappings, validation rules, owner, and related issues.
3. Detect that the dataset has a field or rule mismatch.
4. Generate impact report for the changed attribute.
5. Show affected mappings, validation checks, datasets, owners, and issues.
6. Let the user paste the project note.
7. Let AI propose a structured patch.
8. Show the patch for review.
9. Apply approved changes to structured files.
10. Create an issue/task for validation rule follow-up.

---

## 6. MVP Use Cases

### UC-01 — Create or load model repository

The user can create a new local model repository or load an existing one.

Minimum behavior:

- select repository path;
- validate folder structure;
- show repository status;
- show schema version;
- show last index generation time;
- show validation errors if files are malformed.

Acceptance criteria:

- valid repository loads successfully;
- missing folders are reported clearly;
- invalid YAML/JSON files are identified by path and object ID;
- app does not silently ignore corrupted model files.

---

### UC-02 — Show attribute catalog

The user can see all modeled attributes for Customer / Business Partner migration.

Minimum behavior:

- list attributes;
- filter by domain, entity, SAP table, source system, target system, status, owner, lifecycle state;
- search by name, stable ID, SAP field, source field, or business meaning;
- show completeness indicators.

Recommended columns:

- Attribute ID;
- Name;
- Entity;
- Domain;
- Business meaning;
- SAP representation;
- Source representation;
- Owner;
- Lifecycle status;
- Validation coverage;
- Mapping coverage;
- Issue count.

Acceptance criteria:

- user can find an attribute by SAP table-field name, for example `KNVV-KDGRP`;
- user can identify attributes without owner;
- user can identify attributes without validation rules;
- user can open attribute detail page.

---

### UC-03 — Show attribute detail

The user can inspect one attribute as a traceable model object.

Minimum behavior:

- show stable ID, name, domain, entity, business definition;
- show source-system representation;
- show target SAP representation;
- show mappings;
- show transformation rules;
- show validation rules;
- show ownership and stewardship;
- show related datasets;
- show decisions, issues, and evidence links;
- show impact relationships.

Acceptance criteria:

- user can understand what the attribute means;
- user can see where it comes from and where it lands in SAP;
- user can see whether it is validated;
- user can see who owns it;
- user can see what will be affected if it changes.

---

### UC-04 — Import dataset

The user can import a CSV or Excel migration dataset.

Minimum behavior:

- upload or select file;
- detect columns;
- store dataset metadata;
- calculate basic row and column profile;
- map dataset columns to known attributes if names match;
- show unmatched columns.

Dataset metadata should include:

- dataset ID;
- file name;
- import timestamp;
- source system;
- migration object;
- entity;
- row count;
- column count;
- checksum/hash;
- detected columns;
- mapped attributes;
- unmatched columns.

Acceptance criteria:

- user can import at least CSV;
- XLSX support is recommended but can be implemented after CSV if necessary;
- imported dataset does not become the canonical model;
- dataset is treated as evidence/input for analysis.

---

### UC-05 — Detect dataset-model gaps

The user can compare imported dataset columns against the model.

Minimum behavior:

- detect missing required attributes;
- detect extra dataset columns not represented in model;
- detect model attributes without source mapping;
- detect model attributes without target SAP representation;
- detect attributes without owner;
- detect attributes without validation rule;
- detect simple type or allowed-value mismatches if configured.

Gap categories:

1. Missing required column.
2. Unmodeled dataset column.
3. Missing mapping.
4. Missing validation rule.
5. Missing owner.
6. Missing SAP target field.
7. Missing business definition.
8. Inconsistent lifecycle status.
9. Suspicious duplicate representation.

Acceptance criteria:

- output is deterministic;
- each gap has severity;
- each gap references object IDs;
- each gap can be converted into an issue/task;
- AI may explain a gap, but deterministic logic must detect it.

---

### UC-06 — Generate change impact report

The user can select an attribute or validation rule and generate an impact report.

Minimum behavior:

- input: object ID;
- output: affected attributes, mappings, rules, datasets, issues, decisions, owners, and downstream checks;
- show direct and indirect relationships;
- explain why each item is affected.

Impact report sections:

1. Changed object.
2. Business meaning.
3. Technical representations.
4. Direct dependencies.
5. Validation impact.
6. Dataset impact.
7. Ownership impact.
8. Open issues and risks.
9. Recommended actions.
10. Suggested tasks.

Acceptance criteria:

- impact report is reproducible from the model index;
- report does not rely only on LLM reasoning;
- AI can summarize the report but cannot invent dependencies without model evidence;
- report can be exported as Markdown.

---

### UC-07 — Create issue/task from gap

The user can convert a detected gap into a structured issue.

Minimum behavior:

- choose gap;
- generate issue draft;
- edit title, description, severity, owner, due date, linked objects;
- save issue file;
- link issue back to affected model objects.

Issue fields:

- issue ID;
- title;
- type;
- severity;
- status;
- related object IDs;
- owner;
- source evidence;
- recommended action;
- created date;
- updated date.

Acceptance criteria:

- issue is stored as structured file;
- issue references the gap and related objects;
- issue appears on attribute detail and impact report;
- issue can be closed with resolution notes.

---

### UC-08 — AI proposes model update from pasted note

The user can paste a note, email, ticket, or workshop decision. AI proposes structured model changes.

Minimum behavior:

- user pastes text;
- user selects context: domain/entity/dataset/attribute if known;
- AI extracts possible changes;
- AI proposes patch operations;
- app validates patch against schema;
- user reviews patch diff;
- user approves or rejects;
- approved patch updates files.

Patch operation examples:

- add validation rule;
- update attribute lifecycle status;
- update mandatory condition;
- add evidence link;
- add decision;
- add issue;
- link mapping to attribute;
- add owner/steward;
- update business definition.

Acceptance criteria:

- AI output is never applied silently;
- patch must be schema-valid;
- patch must show before/after diff;
- rejected patch does not modify files;
- approved patch creates traceable change.

---

### UC-09 — Generate AMS handover summary

The user can generate a compact handover summary for a migration object or domain.

Minimum behavior:

- select domain/entity/migration object;
- include attributes, rules, known issues, decisions, ownership, validation scope, and open risks;
- generate Markdown report.

Acceptance criteria:

- report cites model objects by ID;
- report includes unresolved gaps;
- report separates facts from AI-generated narrative;
- report is useful for AMS support onboarding.

This use case is useful for demo, but not mandatory for the first internal MVP cut if time is limited.

---

## 7. MVP Data Scope

### 7.1 Initial master data domain

Start with:

- Customer / Business Partner

Do not start with all domains.

Later domains:

- Supplier / Vendor;
- Material / Product;
- Finance master data;
- Employee/workforce-related BP where relevant.

### 7.2 Initial SAP object scope

The MVP should support a simplified Customer / BP migration model with selected representations from:

- Business Partner general data;
- Customer general data;
- Company code data;
- Sales area data.

Representative SAP structures:

- `BUT000` for Business Partner core/general data;
- `KNA1` for customer general data;
- `KNB1` for company code customer data;
- `KNVV` for sales area customer data;
- optional: `KNVP` for partner functions;
- optional: address/contact structures if needed for demo.

The MVP should not attempt to model every SAP BP table or role relationship in full depth.

### 7.3 Initial attribute examples

Starter model should include around 20–40 attributes, enough to show real traceability without becoming heavy.

Example attributes:

- Business Partner ID;
- Customer Number;
- BP Category;
- BP Grouping;
- Name 1;
- Search Term;
- Country;
- City;
- Postal Code;
- Street;
- Language;
- Company Code;
- Reconciliation Account;
- Payment Terms;
- Sales Organization;
- Distribution Channel;
- Division;
- Customer Group;
- Sales District;
- Sales Office;
- Sales Group;
- Currency;
- Shipping Conditions;
- Partner Function.

Each starter attribute should have at least:

- stable ID;
- name;
- domain;
- entity;
- business meaning;
- source representation;
- target SAP representation;
- lifecycle status;
- owner or owner placeholder;
- mapping reference;
- validation coverage flag.

---

## 8. MVP Object Types

### 8.1 Required object types

The MVP needs these objects:

1. `MasterDataDomain`
2. `MigrationObject`
3. `Entity`
4. `Attribute`
5. `SourceSystem`
6. `TargetSystem`
7. `SourceField`
8. `SAPTable`
9. `SAPField`
10. `Mapping`
11. `TransformationRule`
12. `ValidationRule`
13. `DataQualityCheck`
14. `Owner`
15. `Steward`
16. `Dataset`
17. `Decision`
18. `Issue`
19. `Evidence`
20. `ChangeRequest`

### 8.2 Optional for MVP, useful later

These can be delayed:

- `BusinessGlossaryTerm`
- `CustomizingDependency`
- `SAPRole`
- `PartnerFunction`
- `CodeList`
- `ValueMapping`
- `TestCase`
- `Defect`
- `Release`
- `Control`
- `Policy`

Do not overbuild the object model before the first demo works.

---

## 9. Canonical Repository Structure

The MVP repository should use small structured files.

Recommended structure:

```text
domains/
  customer_bp.yaml

migration_objects/
  customer_bp_migration.yaml

entities/
  bp_general.yaml
  customer_general.yaml
  customer_company_code.yaml
  customer_sales_area.yaml

attributes/
  bp_general/
    bp_id.yaml
    bp_grouping.yaml
  customer_general/
    customer_number.yaml
    country.yaml
  customer_sales_area/
    sales_org.yaml
    distribution_channel.yaml
    division.yaml
    customer_group.yaml

mappings/
  customer_bp/
    legacy_customer_to_bp.yaml
    legacy_sales_area_to_knvv.yaml

rules/
  transformations/
    normalize_customer_group.yaml
  validations/
    customer_group_required_for_ch01.yaml
    payment_terms_required.yaml

validations/
  validation_sets/
    customer_bp_preload.yaml

datasets/
  imports/
  metadata/

issues/
  open/
  closed/

decisions/
  customer_bp/

evidence/
  notes/
  files/

generated/
  model_index.sqlite
  reports/
  gap_reports/
  impact_reports/

schemas/
  attribute.schema.json
  mapping.schema.json
  validation_rule.schema.json
  issue.schema.json
```

Rules:

- canonical truth lives in structured files;
- generated files can be deleted and rebuilt;
- no single giant model file;
- all important objects have stable IDs;
- all references use IDs, not display names;
- user-facing names can change, stable IDs should not.

---

## 10. Core Schemas

### 10.1 Attribute minimum fields

```yaml
id: attr.customer.sales_area.customer_group
object_type: Attribute
name: Customer Group
domain_id: domain.customer_bp
entity_id: entity.customer_sales_area
migration_object_id: mo.customer_bp
business_meaning: Customer classification used for sales reporting and sales-area-specific processing.
lifecycle_status: active
criticality: medium

source_representations:
  - source_system_id: source.legacy_crm
    field_name: customer_group
    file_name: customer_sales_area.csv
    data_type: string

sap_representations:
  - target_system_id: target.s4hana
    table: KNVV
    field: KDGRP
    context: Sales area customer data

mapping_ids:
  - map.legacy_sales_area.customer_group_to_knvv_kdgrp

validation_rule_ids:
  - val.customer_group_required_for_ch01

owner_id: owner.sales_data_team
steward_id: steward.customer_master_data
related_issue_ids: []
evidence_ids: []
tags:
  - sales-area
  - customer
  - migration
```

### 10.2 Mapping minimum fields

```yaml
id: map.legacy_sales_area.customer_group_to_knvv_kdgrp
object_type: Mapping
name: Map legacy customer group to KNVV-KDGRP
source_system_id: source.legacy_crm
target_system_id: target.s4hana
source_fields:
  - customer_group
target_fields:
  - table: KNVV
    field: KDGRP
attribute_ids:
  - attr.customer.sales_area.customer_group
transformation_rule_ids:
  - rule.normalize_customer_group
lifecycle_status: active
owner_id: owner.sales_data_team
evidence_ids: []
```

### 10.3 Validation rule minimum fields

```yaml
id: val.customer_group_required_for_ch01
object_type: ValidationRule
name: Customer Group required for CH01 sales area
rule_type: conditional_required
severity: error
attribute_ids:
  - attr.customer.sales_area.customer_group
condition:
  all:
    - field: sales_org
      operator: equals
      value: CH01
    - field: distribution_channel
      operator: equals
      value: "01"
expectation:
  field: customer_group
  operator: not_empty
owner_id: owner.sales_data_team
lifecycle_status: active
evidence_ids: []
```

### 10.4 Issue minimum fields

```yaml
id: issue.customer_group.validation_missing.001
object_type: Issue
title: Customer Group validation missing for CH01
issue_type: validation_gap
severity: high
status: open
related_object_ids:
  - attr.customer.sales_area.customer_group
  - val.customer_group_required_for_ch01
source_gap_id: gap.dataset.customer_bp.001
owner_id: owner.sales_data_team
recommended_action: Add or confirm validation rule before next preload cycle.
created_at: "2026-04-26"
updated_at: "2026-04-26"
```

---

## 11. MVP UI Scope

### 11.1 Required screens

The MVP needs these screens:

1. Repository dashboard.
2. Attribute catalog.
3. Attribute detail.
4. Dataset import.
5. Gap report.
6. Impact report.
7. Issue list and issue detail.
8. AI patch review.
9. Reports/export page.

### 11.2 Repository dashboard

Shows:

- repository path;
- schema version;
- object counts;
- validation status;
- latest imported datasets;
- open gaps;
- open issues;
- attributes missing owner;
- attributes missing validation;
- latest generated reports.

### 11.3 Attribute catalog

Shows searchable and filterable attribute list.

Important filters:

- domain;
- entity;
- SAP table;
- lifecycle status;
- owner;
- missing validation;
- missing mapping;
- missing target field;
- has open issue.

### 11.4 Attribute detail

Shows complete traceability for one attribute.

Required sections:

- summary;
- business meaning;
- source representation;
- SAP target representation;
- mappings;
- rules;
- validations;
- datasets;
- owners/stewards;
- decisions;
- issues;
- impact links;
- evidence.

### 11.5 Dataset import page

Shows:

- import file selector;
- detected columns;
- row count;
- column count;
- proposed column-to-attribute matches;
- unmatched columns;
- import metadata.

### 11.6 Gap report page

Shows:

- gap severity;
- gap type;
- affected object;
- explanation;
- recommended action;
- create issue button.

### 11.7 Impact report page

Shows:

- selected object;
- direct dependencies;
- indirect dependencies;
- affected validations;
- affected datasets;
- related issues;
- recommended actions;
- export Markdown button.

### 11.8 AI patch review page

Shows:

- pasted source text;
- extracted findings;
- proposed patch operations;
- validation result;
- before/after diff;
- approve/reject controls.

---

## 12. MVP AI Scope

AI should assist with interpretation and patch proposal. It should not be the source of truth.

### 12.1 AI commands in MVP

Required:

1. Explain this attribute.
2. Find change impact.
3. Compare dataset with model summary.
4. Detect missing owners.
5. Detect missing validation rules.
6. Create issue from this gap.
7. Propose model update from this note.
8. Generate validation checklist.
9. Generate AMS handover summary.

Optional:

1. Suggest better business definition.
2. Suggest missing evidence links.
3. Suggest test cases.
4. Draft stakeholder email.

### 12.2 AI guardrails

AI must follow these rules:

- never modify canonical files directly;
- always produce a proposed patch;
- always include affected object IDs;
- separate facts from assumptions;
- mark uncertain findings;
- avoid claiming SAP behavior unless supported by model evidence or user-provided text;
- do not invent owners, systems, or rules;
- ask for user review when confidence is low;
- patch must pass schema validation before approval.

### 12.3 Patch proposal format

```json
{
  "proposal_id": "proposal.customer_group.001",
  "source_text_summary": "Customer Group must be mandatory for CH01 / 01 sales area.",
  "confidence": "medium",
  "operations": [
    {
      "op": "add_validation_rule",
      "object_id": "val.customer_group_required_for_ch01",
      "target_file": "rules/validations/customer_group_required_for_ch01.yaml",
      "payload": {}
    },
    {
      "op": "link_validation_to_attribute",
      "object_id": "attr.customer.sales_area.customer_group",
      "target_file": "attributes/customer_sales_area/customer_group.yaml",
      "payload": {
        "validation_rule_ids_add": ["val.customer_group_required_for_ch01"]
      }
    }
  ],
  "questions_for_reviewer": [
    "Confirm whether this rule applies only to CH01 / 01 or to all CH01 sales areas."
  ]
}
```

---

## 13. Deterministic Validation Scope

The MVP must have deterministic checks independent of AI.

### 13.1 Repository validation

Checks:

- required fields exist;
- IDs are unique;
- referenced IDs exist;
- object type matches schema;
- lifecycle status is valid;
- no broken links;
- generated index is up to date or marked stale.

### 13.2 Model completeness validation

Checks:

- attribute has business meaning;
- attribute has owner or explicit owner placeholder;
- attribute has at least one source representation or accepted reason why not;
- attribute has at least one SAP representation or accepted reason why not;
- attribute has mapping coverage;
- required attribute has validation coverage.

### 13.3 Dataset-model validation

Checks:

- required model attributes missing from dataset;
- dataset columns not mapped to model;
- duplicate columns;
- type mismatch where type is configured;
- allowed-value mismatch where code list is configured;
- conditional required values where rule exists.

---

## 14. Technical MVP Architecture

### 14.1 Recommended stack

Good MVP stack:

- Frontend: Next.js or simple React app.
- Backend: Python FastAPI or Node.js API.
- Schemas: Pydantic or Zod.
- Canonical storage: YAML/JSON/Markdown files.
- Generated index: SQLite or DuckDB.
- Dataset processing: Python pandas or DuckDB.
- AI adapter: provider-agnostic wrapper.
- Versioning: Git diff.

Do not add enterprise infrastructure before the repository model proves value.

### 14.2 Local-first flow

1. User selects repository folder.
2. App validates structured files.
3. App generates SQLite/DuckDB index.
4. UI reads mostly from generated index.
5. File changes go through controlled write services.
6. AI produces patch proposals.
7. Approved patch updates canonical files.
8. Index is regenerated.
9. Reports are generated to `generated/reports/`.

### 14.3 Data write principle

All writes should go through a model service.

The service must:

- validate schema;
- check references;
- write small files;
- preserve stable IDs;
- update timestamps;
- regenerate index or mark it stale;
- produce clear errors.

---

## 15. MVP API Scope

These API endpoints or service functions are enough for MVP.

### Repository

- `GET /repository/status`
- `POST /repository/load`
- `POST /repository/validate`
- `POST /repository/reindex`

### Attributes

- `GET /attributes`
- `GET /attributes/{id}`
- `GET /attributes/{id}/impact`

### Datasets

- `POST /datasets/import`
- `GET /datasets`
- `GET /datasets/{id}`
- `POST /datasets/{id}/gap-detection`

### Gaps and issues

- `GET /gaps`
- `POST /gaps/{id}/create-issue`
- `GET /issues`
- `GET /issues/{id}`
- `PATCH /issues/{id}`

### AI proposals

- `POST /ai/explain-attribute`
- `POST /ai/propose-model-update`
- `POST /ai/generate-validation-checklist`
- `POST /ai/generate-handover-summary`

### Patch review

- `GET /proposals`
- `GET /proposals/{id}`
- `POST /proposals/{id}/validate`
- `POST /proposals/{id}/apply`
- `POST /proposals/{id}/reject`

---

## 16. MVP Reports

### 16.1 Required reports

1. Gap report.
2. Attribute impact report.
3. Validation coverage report.
4. Ownership gaps report.
5. AMS handover summary.

### 16.2 Report format

Markdown first.

Later formats:

- HTML;
- PDF;
- Excel export;
- Jira-ready issue CSV.

### 16.3 Report quality rules

Reports must:

- include generation timestamp;
- include repository version or commit hash if available;
- include object IDs;
- separate model facts from AI summary;
- show unresolved questions;
- show recommended next actions.

---

## 17. MVP Build Order

### Phase 0 — Repository skeleton

Deliver:

- folder structure;
- starter schemas;
- starter Customer / BP sample model;
- repository validator;
- generated index builder.

Exit criteria:

- app can load sample repository;
- schema validation works;
- index can be rebuilt.

### Phase 1 — Attribute catalog and detail

Deliver:

- attribute list;
- filters and search;
- attribute detail page;
- relationship display.

Exit criteria:

- user can find `KNVV-KDGRP` or similar field;
- user can see business meaning, mapping, validation, owner, issues.

### Phase 2 — Dataset import and gap detection

Deliver:

- CSV import;
- dataset metadata;
- dataset column matching;
- gap detection report;
- create issue from gap.

Exit criteria:

- user can import sample dataset;
- app detects missing/extra columns and missing model coverage;
- gap can become issue.

### Phase 3 — Impact analysis

Deliver:

- attribute impact endpoint;
- impact report UI;
- Markdown export.

Exit criteria:

- user selects attribute;
- app shows affected mappings, rules, datasets, owners, issues, decisions.

### Phase 4 — AI patch proposal

Deliver:

- paste note screen;
- AI extraction;
- patch proposal format;
- schema validation;
- diff review;
- approve/reject flow.

Exit criteria:

- user pastes a note about a changed rule;
- AI proposes structured patch;
- patch is reviewed and applied only after approval.

### Phase 5 — Demo hardening

Deliver:

- stable demo dataset;
- seeded gaps;
- clean reports;
- error handling;
- README and demo script.

Exit criteria:

- 10–15 minute demo works end-to-end;
- no manual file edits required during demo;
- clear before/after state.

---

## 18. MVP Success Metrics

### 18.1 Product success metrics

For a demo or pilot, measure:

- time to find affected attributes after a rule change;
- number of detected dataset-model gaps;
- percentage of attributes with owner assigned;
- percentage of required attributes with validation rules;
- number of manual cross-checks avoided;
- number of AI proposals accepted after review;
- time to generate AMS handover summary.

### 18.2 MVP health metrics

Track:

- schema validation error count;
- broken reference count;
- unmapped dataset column count;
- attributes without owner;
- attributes without validation;
- open issue count by severity;
- rejected AI patch proposals;
- manually edited files that break validation.

---

## 19. MVP Non-Functional Requirements

### 19.1 Performance

For MVP scale:

- 1 domain;
- 3–5 entities;
- 20–100 attributes;
- 5–20 mappings;
- 5–30 validation rules;
- datasets up to 50,000 rows for local testing.

The MVP does not need enterprise-scale profiling.

### 19.2 Reliability

Requirements:

- invalid files must not crash the app;
- partial AI output must not corrupt repository;
- generated index can be rebuilt from canonical files;
- dataset imports should preserve original file metadata;
- patch application should be atomic where practical.

### 19.3 Security and privacy

For local MVP:

- no external upload by default;
- AI provider can be configured;
- user must understand when data is sent to an external model;
- local model option should be possible later;
- sensitive datasets should be avoidable in demo.

---

## 20. Demo Data Requirements

The MVP should include synthetic demo data.

Minimum demo assets:

1. Starter Customer / BP model repository.
2. Sample customer general dataset.
3. Sample customer sales area dataset.
4. At least one missing required column.
5. At least one extra dataset column.
6. At least one attribute missing owner.
7. At least one attribute missing validation rule.
8. At least one project note that changes a rule.
9. At least one AI patch proposal.
10. One final impact report.

Do not use real client data.

---

## 21. Demo Script

### Step 1 — Open repository dashboard

Show model counts, validation status, open gaps, and repository health.

### Step 2 — Open attribute catalog

Search for Customer Group or `KNVV-KDGRP`.

### Step 3 — Open attribute detail

Show source field, SAP target field, mapping, validation coverage, owner, and related issues.

### Step 4 — Import dataset

Import sales area dataset.

### Step 5 — Run gap detection

Show missing validation or mismatched column coverage.

### Step 6 — Generate impact report

Select Customer Group and show affected mappings, rules, datasets, owners, and issues.

### Step 7 — Paste project note

Example note:

> Customer Group is mandatory for CH01 / 01 sales area. Please ensure this is checked before next preload.

### Step 8 — Review AI patch

Show proposed validation rule and link to attribute.

### Step 9 — Approve patch

Apply patch, regenerate index, show diff.

### Step 10 — Export report

Generate Markdown report for migration lead or AMS handover.

---

## 22. Key Product Decisions

### Decision 1 — File-first repository

Use structured files as canonical truth. This keeps the MVP transparent, Git-friendly, and easy to inspect.

### Decision 2 — SQLite/DuckDB as generated layer

Use a generated database for query and reporting. Do not make the database the canonical source of truth in MVP.

### Decision 3 — Deterministic checks before AI

Gap detection and relationship traversal should be deterministic. AI explains and proposes; it does not replace validation logic.

### Decision 4 — Human approval for AI changes

AI must never silently change the model. The workflow is proposal → validation → diff → approval → write.

### Decision 5 — Narrow SAP scope

Start with Customer / BP and selected SAP tables. Do not model the full SAP universe.

---

## 23. Risks and Mitigations

### Risk 1 — MVP becomes too broad

Mitigation:

- limit to Customer / BP;
- limit starter attributes;
- avoid integrations;
- demo one strong scenario end-to-end.

### Risk 2 — Object model becomes over-engineered

Mitigation:

- keep only required object types;
- add optional objects only when needed by demo;
- prefer simple references over complex graph infrastructure.

### Risk 3 — AI output looks impressive but is not trustworthy

Mitigation:

- separate AI narrative from model facts;
- require schema-valid patches;
- show diff;
- enforce human approval.

### Risk 4 — SAP complexity is simplified too much

Mitigation:

- use realistic SAP table/field examples;
- clearly mark simplifications;
- focus on operational traceability rather than complete SAP modeling.

### Risk 5 — Dataset import becomes a full ETL tool

Mitigation:

- only import metadata and basic profiles;
- do not build full transformation engine;
- keep dataset as evidence for model validation.

---

## 24. What Not To Build Yet

Do not build these in MVP:

- full enterprise RBAC;
- workflow approval engine;
- SAP connector;
- Jira connector;
- Confluence connector;
- graph database;
- event streaming;
- multi-agent orchestration platform;
- automatic remediation;
- full data quality engine;
- semantic search over all documents;
- complete SAP BP data model;
- generic data catalog;
- SaaS billing;
- multi-tenant admin console.

These may matter later, but they are distractions for the first proof.

---

## 25. MVP Acceptance Criteria

The MVP is acceptable when the following flow works end-to-end:

1. Load sample Customer / BP model repository.
2. Show attribute catalog.
3. Open attribute detail for a sales-area attribute.
4. Import sample dataset.
5. Run dataset-model gap detection.
6. Convert one gap into issue.
7. Generate impact report for changed attribute.
8. Paste project note about rule change.
9. AI proposes schema-valid patch.
10. User reviews and approves patch.
11. Canonical files are updated.
12. Generated index is refreshed.
13. Updated attribute detail shows new rule.
14. Final report is exported as Markdown.

If this flow is strong, the MVP is useful even without integrations.

---

## 26. Implementation Decisions And Open Questions

Resolved decisions:

| Decision | Status | Implementation implication |
|---|---|---|
| Canonical storage format | Decided | Use Markdown files with YAML frontmatter for governed objects. Use YAML for config and selected structured fixtures. |
| Generated index | Decided | Use SQLite first. DuckDB is optional for heavier profiling, not required for P0. |
| Runtime schemas | Decided | Use Pydantic as the backend source of validation truth. Generate JSON Schema for UI/contracts later. |
| Architecture mode | Decided | Local-first web/API/CLI workspace. No hosted team workspace in MVP. |
| AI patch workflow | Decided | AI proposes, validators check, humans approve, canonical files change only after approval. |
| Git behavior | Decided | Show diff before approved writes. Automatic commit creation is not required for P0. |
| First domain/slice | Decided | Business Partner parent domain, Customer role-dependent slice, Customer Sales Area context. |

Open questions that remain for implementation:

1. Should P0 dataset import store raw files in the workspace, or only metadata and profiles?
2. Which AI provider adapter should be used for the first demo?
3. How much SAP table/field reference data is enough for the Customer Group scenario?
4. Should P0 validation rules use a YAML DSL only, or allow controlled Python checks after the YAML path works?

---

## 27. Recommended First Implementation Cut

For fastest proof, build this first:

1. File repository schema.
2. Customer / BP sample model.
3. Repository validator.
4. SQLite index generator.
5. Attribute catalog.
6. Attribute detail.
7. CSV import.
8. Gap detection.
9. Impact report.
10. AI patch proposal review.

Delay everything else.

The MVP should feel like a practical migration model control room, not an enterprise platform.
