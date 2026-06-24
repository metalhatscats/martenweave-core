> **Deep-dive reference.** Start with [`AGENT_QUICK_REFERENCE.md`](AGENT_QUICK_REFERENCE.md) for a concise overview.

# Martenweave — System Architecture

Version: 0.4.1
Document type: Product/system architecture  
Initial product focus: General agentic data model registry, with SAP Business Partner migration as the first domain pack  
Architecture style: Local-first, file-based, AI-ready, domain-aware model workspace  
Status: Draft for product development

---

## 1. Purpose

This document defines the technical system architecture for **Martenweave**.

Martenweave is a lightweight operational model layer for data modeling, migration, governance, and agent-assisted delivery. It turns scattered model knowledge into a structured, traceable, validated, and AI-ready workspace. SAP migration and Master Data Management are the first domain pack and proof case, not the product boundary.

The product is not a replacement for:

- SAP S/4HANA;
- SAP MDG;
- SAP MDM;
- SAP migration cockpit;
- SAP Solution Manager;
- SAP Cloud ALM;
- Jira;
- Confluence;
- enterprise data catalog platforms;
- enterprise integration monitoring tools.

It sits around these systems as an operational model knowledge layer.

The system must support:

- file-based canonical model repository;
- business attributes separated from physical system fields;
- SAP-aware entity contexts;
- field representations across systems;
- source-to-target mappings;
- value lists and value mappings;
- transformation and derivation logic;
- deterministic validation;
- dataset profiling;
- gap detection;
- lineage;
- impact analysis;
- issue, decision, evidence, and change governance;
- AI-assisted patch proposal;
- human approval before model changes;
- generated query/search/index layers;
- CLI, local API, and IDE workflows.

---

## 2. Executive architecture decision

Recommended MVP architecture:

```text
Local file-based model repository
  + Markdown/YAML canonical objects
  + Python FastAPI backend
  + Pydantic validation
  + SQLite generated index
  + optional DuckDB profiling layer
  + generated static docs / IDE integration
  + Typer CLI
  + JSONL AI search documents
  + AI adapter with patch proposal workflow
  + Git diff as trust layer
```

Recommended later architecture:

```text
Same canonical repository model
  + optional Tauri desktop shell
  + optional GitHub/GitLab integration
  + optional Postgres hosted team workspace
  + optional AI gateway
  + optional Jira/Confluence/SAP metadata adapters
  + optional graph visualization
```

Do not start with:

```text
Neo4j
Kafka
enterprise workflow engine
multi-agent framework
direct SAP write-back
full enterprise RBAC
complex SaaS tenancy
automatic ABAP/CPI reverse engineering
```

Recommended MVP product boundary:

```text
General agentic data model registry
Business Partner parent domain (first domain pack)
Customer role-dependent slice
Customer Sales Area context
Customer Group / KNVV-KDGRP demo path
local-first file repository
schema validation before indexing and AI
AI patch proposal with human approval
```

Those are later options, not MVP foundations.

---

## 3. Core architectural thesis

The product should be built around this pipeline:

```text
Canonical model files
        ↓
Parser and object registry
        ↓
Schema validation
        ↓
Reference resolution
        ↓
SAP context validation
        ↓
Generated read/index layer
        ↓
Lineage, impact, catalog, search, reports
        ↓
AI-assisted explanation and patch proposal
        ↓
Human approval
        ↓
Canonical model update + Git diff + ChangeRequest
```

The system is not a “database-first MDM tool”.

It is a **model repository workspace** with generated indexes and AI-assisted workflows.

---

## 4. Non-negotiable product rules

1. **Business Attribute is not the same as FieldEndpoint.**

2. **SAP table storage is not the same as SAP BP role or UI maintenance context.**

3. **KNVV fields must be modeled as Customer Sales Area context.**

4. **KNB1 fields must be modeled as Customer Company Code context.**

5. **AI must not silently mutate approved model files.**

6. **Every approved model change should be linked to a ChangeRequest.**

7. **Every important object must have a stable ID.**

8. **Generated indexes are disposable. Canonical files are source of truth.**

9. **Dataset files are not the model. They are inputs/evidence checked against the model.**

10. **Deterministic validation comes before AI interpretation.**

---

## 5. System modes

The system should support several modes without changing the core model.

### 5.1 Local-first MVP mode

Primary MVP mode.

```text
User machine
  ├─ model repository folder
  ├─ FastAPI backend
  ├─ generated static docs / IDE integration
  ├─ SQLite generated index
  ├─ optional DuckDB profiling files
  └─ optional AI provider adapter
```

Best for:

- solo development;
- demo;
- SAP migration analyst workspace;
- internal prototype;
- Git-based review;
- data privacy-sensitive work.

### 5.2 Desktop wrapper mode

Later packaging option.

```text
Tauri shell
  ├─ bundled web frontend
  ├─ local backend process
  ├─ workspace picker
  ├─ local repository
  └─ local generated index
```

Use when:

- users want desktop-like launch;
- Windows/macOS convenience matters;
- local project folders are primary;
- no cloud deployment is desired.

Do not build this before the core web/CLI flow works.

### 5.3 Hosted team workspace mode

Later commercial/team option.

```text
Hosted web app
  ├─ repository service
  ├─ Postgres read/write store or Git-backed storage
  ├─ object storage for datasets/evidence
  ├─ AI gateway
  ├─ identity provider
  ├─ audit trail
  └─ integration adapters
```

Use when:

- multiple users need shared workspace;
- approval workflow matters;
- enterprise identity is required;
- repository needs server-side governance.

### 5.4 Hybrid Git-backed mode

Strong intermediate option.

```text
Hosted UI/API
  ├─ GitHub/GitLab repository as canonical source
  ├─ server-generated index
  ├─ pull request based review
  └─ AI patch proposals as branches/PRs
```

This is attractive because it preserves file-based trust while adding collaboration.

---

## 6. Architecture style

The system should use a pragmatic layered architecture.

```text
UI Layer
API Layer
Application Service Layer
Domain/Validation Layer
Data Access Layer
Storage/Index Layer
AI Adapter Layer
```

Recommended internal pattern:

```text
File repository as write/source model
Generated database as read model
```

This is close to CQRS, but do not over-formalize it in MVP.

Write side:

```text
Markdown/YAML canonical files
PatchProposal
ChangeRequest
Git diff
```

Read side:

```text
SQLite/DuckDB
relationship edges
search documents
report outputs
```

---

## 7. High-level component diagram

```text
┌───────────────────────────────────────────────────────────────┐
│                         User Interfaces                       │
│                                                               │
│  IDE / static docs    Typer CLI       Obsidian/VS Code/GitHub   │
└───────────────┬────────────────────┬──────────────────────────┘
                │                    │
                ▼                    ▼
┌───────────────────────────────────────────────────────────────┐
│                            API Layer                          │
│                                                               │
│  FastAPI routes for catalog, objects, validation, datasets,    │
│  lineage, impact, issues, decisions, changes, patches, AI      │
└───────────────────────────┬───────────────────────────────────┘
                            ▼
┌───────────────────────────────────────────────────────────────┐
│                      Application Services                     │
│                                                               │
│  RepositoryService        ObjectRegistry                      │
│  SchemaValidationService  ReferenceResolver                   │
│  SAPContextValidator      IndexService                        │
│  SearchDocumentService    CatalogService                      │
│  DatasetService           GapDetectionService                 │
│  MappingService           ValidationService                   │
│  LineageService           ImpactService                       │
│  IssueService             DecisionService                     │
│  ChangeRequestService     PatchService                        │
│  AIService                ReportService                       │
│  AuditService             GitService                          │
└───────────────────────────┬───────────────────────────────────┘
                            ▼
┌───────────────────────────────────────────────────────────────┐
│                       Data Access Layer                       │
│                                                               │
│  FileRepositoryAdapter     SQLiteIndexRepository              │
│  DuckDBProfileRepository   SearchDocumentStore                │
│  DatasetFileAdapter        GitAdapter                         │
│  AIProviderAdapter         ConnectorAdapters                  │
└───────────────────────────┬───────────────────────────────────┘
                            ▼
┌───────────────────────────────────────────────────────────────┐
│                            Storage                            │
│                                                               │
│  model/ canonical Markdown/YAML files                         │
│  data/ raw/sample datasets                                    │
│  generated/modelops.db                                        │
│  generated/search_documents.jsonl                             │
│  generated/lineage_edges.jsonl                                │
│  generated/validation_results.jsonl                           │
│  generated/reports/                                           │
└───────────────────────────────────────────────────────────────┘
```

---

## 8. Recommended technology stack

### 8.1 Recommended MVP stack

| Layer | Recommended choice | Reason |
|---|---|---|
| Frontend | Generated static docs + local API | Read-only local viewer, IDE integration, future optional UI |
| Styling | Tailwind + shadcn-style components | Fast clean enterprise UI |
| Backend | FastAPI | Strong Python API layer, practical for data tools |
| Schemas | Pydantic | Runtime validation, JSON schema export, strict models |
| CLI | Typer | Clean Python CLI using same services as API |
| Canonical storage | Markdown + YAML frontmatter | Human-readable, Git-friendly, Obsidian-friendly |
| Generated index | SQLite | Simple, embedded, local-first, zero-admin |
| Profiling/analytics | DuckDB optional | Better for larger CSV/Parquet/analytical workloads |
| AI search docs | JSONL | Simple, inspectable, provider-agnostic |
| AI adapter | Direct provider adapters first | Avoid early dependency on AI gateway |
| Git | CLI integration first | Trust, diff, rollback |
| Tests | Pytest, Vitest, Playwright | Backend, frontend, and end-to-end coverage |

### 8.2 Why not database-first?

Database-first is tempting but weaker for MVP trust.

Problems:

- harder to review model changes;
- harder to explain changes to business/data stewards;
- harder to keep model near project documentation;
- harder to support AI patch proposals as diffs;
- easier to create hidden state;
- weaker local-first story.

Database-first can be introduced later for hosted mode.

### 8.3 Why not graph DB first?

The product needs graph-like relationships, but not necessarily graph database infrastructure.

For MVP:

```text
object_relationships table in SQLite
+ generated lineage_edges.jsonl
+ traversal service
```

This is enough for:

- lineage path;
- impact analysis;
- affected objects;
- graph visualization later.

Use Neo4j or another graph DB only when:

- relationship traversal becomes too complex;
- the product has proven value;
- hosted enterprise deployment needs advanced graph querying.

### 8.4 Why not workflow engine first?

Change governance is needed, but full workflow engine is not.

MVP governance:

```text
PatchProposal status
ChangeRequest status
Issue status
Decision status
approval fields
Git diff
audit events
```

This is enough.

Add workflow engine only after real customer workflow complexity is known.

---

## 9. Architectural options and trade-offs

### 9.1 Storage options

| Option | Use now? | Comment |
|---|---:|---|
| Markdown + YAML frontmatter | Yes | Best canonical format for human-readable model repository |
| YAML-only | Selectively | Good for strict config, large structured lists |
| JSON | Generated/API | Better machine output than authoring format |
| SQLite | Yes | Best MVP generated index |
| DuckDB | Optional | Use for heavy profiling and analytical queries |
| Postgres | Later | Hosted/team mode |
| Neo4j | Later | Only after graph complexity proves need |
| Object storage | Later | Hosted datasets/evidence |

### 9.2 UI deployment options

| Option | Use now? | Comment |
|---|---:|---|
| Localhost web app | Yes | Fastest MVP |
| Static-only app | No | Backend/file access needed |
| Tauri desktop | Later | Good wrapper after core works |
| Electron | Avoid early | Heavier than needed |
| Hosted SaaS | Later | Only after product-market validation |
| GitHub app | Later | Strong collaboration path |

### 9.3 AI integration options

| Option | Use now? | Comment |
|---|---:|---|
| Direct OpenAI/Anthropic adapter | Yes | Simple and controllable |
| Local Ollama adapter | Yes, optional | Good for private/local mode, lower capability |
| LiteLLM-like gateway | Later/optional | Useful for enterprise multi-provider routing, but adds operational dependency |
| Custom AI gateway | Later | Only when team/enterprise deployment needs policy, routing, budgets |
| Multi-agent framework | No | Overkill for MVP |
| MCP adapters | Later | Add after repository tools are useful |

### 9.4 Indexing/search options

| Option | Use now? | Comment |
|---|---:|---|
| SQLite FTS | Yes | Simple keyword search |
| JSONL search documents | Yes | Good AI context source |
| Local embeddings | Optional | Useful later for semantic search |
| Vector DB | Later | Avoid unless search scale demands it |
| Hybrid search | Later | Combine keyword + semantic after corpus exists |

---

## 10. Canonical repository architecture

The model repository is the write/source layer.

Recommended structure:

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

  data/
    raw/
    processed/
    samples/

  generated/
    modelops.db
    search_documents.jsonl
    lineage_edges.jsonl
    validation_results.jsonl
    reports/

  schemas/
  templates/
  modelops.config.yaml
  README.md
```

Canonical files should be:

```text
small
typed
ID-based
human-readable
reviewable in Git
validated by schema
linked by stable IDs
```

---

## 11. Generated index architecture

The generated layer powers fast UI, search, reports, lineage, and impact.

Recommended generated artifacts:

```text
generated/modelops.db
generated/search_documents.jsonl
generated/lineage_edges.jsonl
generated/validation_results.jsonl
generated/audit_events.jsonl
generated/reports/repository-health.md
```

Generated database tables:

```text
objects
object_relationships
domains
migration_objects
entities
entity_contexts
attributes
attribute_usages
systems
system_environments
sap_objects
field_endpoints
interfaces
datasets
dataset_columns
mappings
mapping_endpoints
value_lists
value_list_entries
value_mappings
value_mapping_entries
rules
logic
validations
quality_checks
owners
issues
risks
decisions
change_requests
patch_proposals
evidence
validation_results
search_documents
audit_events
```

Universal `objects` table:

```text
object_id
object_type
name
title
domain_id
status
source_file
content_hash
last_modified_at
created_at
updated_at
```

Universal `object_relationships` table:

```text
from_object_id
relationship_type
to_object_id
source_object_id
source_file
confidence
created_from
```

This table should power lineage and impact without a graph database.

---

## 12. Domain service architecture

### 12.1 RepositoryService

Responsibilities:

- locate repository root;
- read config;
- scan canonical files;
- parse Markdown frontmatter;
- parse YAML;
- compute file hashes;
- track source file path;
- write approved changes;
- create files from templates;
- protect generated files from manual write operations.

### 12.2 ObjectRegistry

Responsibilities:

- build global object ID registry;
- enforce uniqueness;
- map ID to type and source file;
- support quick lookup;
- detect orphaned or duplicate objects.

### 12.3 SchemaValidationService

Responsibilities:

- validate object structure;
- check required fields;
- check enum values;
- validate object-specific fields;
- produce clear error/warning output.

### 12.4 ReferenceResolver

Responsibilities:

- resolve object ID references;
- detect broken references;
- create relationship edges;
- detect missing reverse links where useful;
- provide dependency graph for lineage/impact.

### 12.5 SAPContextValidationService

Responsibilities:

- enforce SAP-specific modeling rules;
- detect incorrect context assignment;
- detect physical field vs BP role confusion.

MVP SAP rules:

```text
KNVV -> Customer Sales Area context
KNB1 -> Customer Company Code context
KNVP -> Partner Function context
BUT000 -> BP Central context
BUT020/ADRC/ADR6 -> Address/contact context
BP role -> maintenance/governance context, not physical storage
```

### 12.6 IndexService

Responsibilities:

- build SQLite index;
- rebuild from canonical files;
- store normalized records;
- store relationship edges;
- store validation results;
- store search documents;
- support degraded read when warnings exist.

### 12.7 CatalogService

Responsibilities:

- return list views;
- aggregate status;
- show owner, validation, mapping, and issue coverage;
- support filters and search.

### 12.8 DatasetService

Responsibilities:

- register datasets;
- profile CSV/Excel;
- infer dataset columns;
- sample values;
- compute distinct values;
- detect blanks;
- match columns to endpoints/attributes;
- store generated dataset profile.

### 12.9 GapDetectionService

Responsibilities:

- compare datasets against model;
- detect unknown columns;
- detect missing mappings;
- detect unmapped values;
- detect invalid target values;
- detect missing owners;
- detect missing validations;
- create issue drafts.

### 12.10 MappingService

Responsibilities:

- resolve mappings;
- verify source/target endpoints;
- verify value mappings;
- verify target value list coverage;
- detect mapping lifecycle problems.

### 12.11 ValidationService

Responsibilities:

- run repository validation;
- run model validation;
- run dataset validation;
- run quality checks;
- generate validation result artifacts.

### 12.12 LineageService

Responsibilities:

- trace source to target paths;
- show upstream/downstream usage;
- generate lineage path output;
- expose graph edges for visualization later.

### 12.13 ImpactService

Responsibilities:

- start from any object;
- traverse relationships;
- classify affected objects;
- produce impact report;
- add recommended actions;
- call AI only for explanation, not discovery.

### 12.14 IssueService

Responsibilities:

- create issue from gap;
- link issue to affected objects;
- update issue status;
- show open issues per domain/object/context.

### 12.15 DecisionService

Responsibilities:

- create decisions;
- link decisions to attributes/mappings/rules/issues;
- show rationale history.

### 12.16 ChangeRequestService

Responsibilities:

- manage business-level model changes;
- link affected objects;
- record approvers;
- link evidence, decisions, issues;
- support before/after summary;
- update object-level change history.

### 12.17 PatchService

Responsibilities:

- create PatchProposal;
- validate proposed changes;
- render diff;
- apply approved patch;
- reject/supersede patch;
- update ChangeRequest;
- trigger index rebuild.

### 12.18 AIService

Responsibilities:

- build context bundles;
- call AI provider;
- parse structured AI output;
- enforce JSON/schema output;
- create PatchProposal;
- generate summaries/checklists;
- never directly mutate canonical files.

### 12.19 ReportService

Responsibilities:

- generate reports;
- write generated report files;
- export Markdown/PDF later;
- support AMS handover outputs.

### 12.20 AuditService

Responsibilities:

- record runtime events;
- store generated audit log;
- provide user-visible event history.

### 12.21 GitService

Responsibilities:

- inspect repository status;
- show changed files;
- show diffs;
- prepare commit message;
- block risky patch apply over uncommitted changes unless user confirms;
- later create branch/PR.

---

## 13. Main data flows

### 13.1 Repository build flow

```text
1. Load config.
2. Scan canonical files.
3. Parse Markdown/YAML.
4. Build ObjectRegistry.
5. Validate schemas.
6. Resolve references.
7. Apply SAP context validation.
8. Generate relationship edges.
9. Build SQLite index.
10. Generate search documents.
11. Generate health report.
```

### 13.2 Dataset profiling flow

```text
1. User selects dataset.
2. Dataset metadata is created/updated.
3. Dataset is read from local path.
4. Columns, types, blanks, distinct values, and samples are profiled.
5. Dataset columns are matched to FieldEndpoint/Attribute.
6. GapDetectionService runs checks.
7. Results are stored in generated index.
8. User may create issues or patch proposals from gaps.
```

### 13.3 Lineage flow

```text
1. User opens Attribute or FieldEndpoint.
2. LineageService loads relationship edges.
3. Upstream endpoints, mappings, value mappings, and logic are collected.
4. Target endpoints, validations, datasets, reports, and downstream usage are collected.
5. UI renders path view.
6. Optional AI explanation summarizes deterministic lineage.
```

### 13.4 Impact flow

```text
1. User selects object.
2. ImpactService traverses graph relationships.
3. Affected objects are grouped by type.
4. Owners, issues, decisions, validations, datasets, and interfaces are included.
5. Deterministic recommended actions are generated.
6. Optional AI summary converts impact into readable explanation.
```

### 13.5 AI patch flow

```text
1. User pastes note/email/ticket/workshop text.
2. AIService retrieves relevant context bundle.
3. AI extracts candidate model changes.
4. PatchService creates PatchProposal.
5. Validator checks proposed changes.
6. UI shows diff and validation results.
7. User approves or rejects.
8. On approval:
   - canonical files are updated;
   - ChangeRequest is created/updated;
   - object change_history is updated where applicable;
   - Git diff is available;
   - index is rebuilt.
```

---

## 14. AI architecture

### 14.1 AI design principle

AI is not the system of record.

AI is a proposal and explanation layer over a deterministic model.

### 14.2 AI capabilities

AI can:

- explain an attribute;
- explain lineage;
- summarize impact;
- propose model updates from pasted notes;
- create issue drafts from gap reports;
- generate validation checklist;
- generate AMS handover summary;
- normalize rough notes into structured candidate objects;
- compare two model versions.

AI cannot:

- approve changes;
- directly edit active canonical objects;
- bypass validators;
- invent source evidence;
- replace owner approval;
- decide SAP configuration truth without evidence.

### 14.3 AI provider abstraction

Use an internal adapter interface.

```python
class AIProvider:
    def complete(self, request: AIRequest) -> AIResponse:
        ...
```

Provider implementations:

```text
OpenAIProvider
AnthropicProvider
AzureOpenAIProvider
OllamaProvider
LiteLLMGatewayProvider later
NoAIProvider
```

### 14.4 AI context bundle

AI should receive controlled context, not the whole repository.

Context bundle structure:

```json
{
  "task": "propose_patch_from_note",
  "primary_objects": [],
  "related_objects": [],
  "open_issues": [],
  "recent_decisions": [],
  "validation_results": [],
  "source_evidence": {},
  "allowed_actions": [
    "create_issue",
    "update_attribute",
    "update_mapping",
    "update_value_mapping",
    "create_change_request"
  ]
}
```

### 14.5 AI output contract

AI output should be structured.

Example:

```json
{
  "proposal_type": "model_patch",
  "confidence": "medium",
  "affected_objects": [],
  "proposed_changes": [],
  "new_objects": [],
  "questions": [],
  "required_human_checks": []
}
```

The system validates this output before writing `PatchProposal`.

### 14.6 AI gateway option

A LiteLLM-like gateway or custom gateway can be added later for:

- provider routing;
- budget control;
- central credentials;
- audit;
- policy enforcement;
- enterprise deployment.

Do not require an AI gateway for local MVP.

Also apply supply-chain discipline if third-party gateways are used:

```text
pin versions
verify releases where practical
isolate secrets
disable unnecessary callbacks/logging
document provider data handling
```

---

## 15. Search architecture

### 15.1 Search layers

MVP:

```text
SQLite FTS
JSONL search documents
structured filters
```

Later:

```text
local embeddings
hybrid keyword + semantic search
vector index
query expansion
entity-aware retrieval
```

### 15.2 Search document generation

One important object should produce one search document.

Search document should include:

- ID;
- type;
- title/name;
- domain;
- entity context;
- technical references;
- SAP table/field names;
- business description;
- relationships;
- open issues;
- recent decisions;
- generated search text.

Example:

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
  "search_text": "Customer Group KDGRP KNVV sales area customer classification mapping validation"
}
```

---

## 16. API architecture

API route groups:

```text
/api/workspace
/api/repository
/api/objects
/api/catalog
/api/domains
/api/migration-objects
/api/entities
/api/entity-contexts
/api/attributes
/api/field-endpoints
/api/mappings
/api/value-lists
/api/value-mappings
/api/datasets
/api/validations
/api/lineage
/api/impact
/api/issues
/api/decisions
/api/change-requests
/api/patch-proposals
/api/ai
/api/reports
/api/settings
```

Example endpoints:

```text
GET  /api/workspace/status
POST /api/repository/validate
POST /api/repository/build-index
GET  /api/attributes
GET  /api/attributes/{id}
GET  /api/attributes/{id}/lineage
GET  /api/attributes/{id}/impact
GET  /api/attributes/{id}/history
POST /api/datasets/profile
GET  /api/datasets/{id}/gaps
POST /api/impact
POST /api/ai/propose-patch
GET  /api/patch-proposals
GET  /api/patch-proposals/{id}
POST /api/patch-proposals/{id}/approve
POST /api/patch-proposals/{id}/reject
```

API should read from generated index by default.

File writes should go through service layer, not direct route logic.

---

## 17. CLI architecture

CLI commands should call the same services as API.

Recommended commands:

```bash
modelops init ./my-model
modelops validate --repo ./my-model
modelops build-index --repo ./my-model --jsonl
modelops health --repo ./my-model
modelops search "customer group" --repo ./my-model
modelops query --type Attribute --repo ./my-model
modelops trace ATTR-CUST-SALES-CUSTOMER-GROUP --repo ./my-model
modelops impact FEP-S4-KNVV-KDGRP --repo ./my-model
modelops profile-dataset ./data/customer_sales_area.csv --repo ./my-model
modelops gaps ./data/customer_sales_area.csv --repo ./my-model --check-model
modelops propose-patch --from notes/ch01-a17.md --repo ./my-model
modelops proposal validate PP-SCAFFOLD-001 --repo ./my-model
modelops proposal impact PP-SCAFFOLD-001 --repo ./my-model
modelops serve --repo ./my-model
```

CLI is required for:

- automation;
- testing;
- reproducibility;
- agentic coding workflows;
- non-UI debugging.

---

## 18. UI architecture

The UI should represent the model in analyst-friendly order.

Main navigation:

```text
Workspace Home
Domains
Migration Objects
Entities / Contexts
Attribute Catalog
Attribute Detail
Lineage / Usage
Mappings
Value Lists / Value Mappings
Rules / Validations
Datasets / Gap Detection
Issues / Risks
Decisions / Change Requests
AI Patch Review
Reports / AMS Handover
Settings / Repository Health
```

### 18.1 Workspace Home

Show:

- repository path;
- last index build;
- validation status;
- object counts by type;
- broken references;
- missing owners;
- missing validations;
- open high-severity issues;
- pending patch proposals;
- recent change requests.

### 18.2 Attribute Catalog

Columns:

```text
ID
Name
Domain
Entity Context
SAP Target
Source Coverage
Mapping Status
Validation Status
Owner
Lifecycle Status
Open Issues
Last Changed
Risk Level
```

### 18.3 Attribute Detail

Display order:

```text
1. Identity
2. Business meaning
3. Context and grain
4. SAP/system representations
5. Source-to-target mappings
6. Value lists and value mappings
7. Transformation/defaulting logic
8. Business rules
9. Validation rules and DQ checks
10. Interfaces and datasets
11. Upstream/downstream lineage
12. Ownership and stewardship
13. Lifecycle status
14. Related issues, risks, decisions, evidence
15. Change history
16. AI summary and proposed actions
```

### 18.4 FieldEndpoint page

Show:

- system;
- environment;
- endpoint type;
- SAP table/field or file/API location;
- business attribute;
- entity context;
- grain;
- mapped sources;
- mapped targets;
- validations;
- datasets;
- issues;
- lineage.

### 18.5 Lineage view

MVP should show path/table first.

Example:

```text
Legacy CRM CUSTOMER_SALES.CUST_GROUP
  → MAP-CUST-GROUP-LEGACY-TO-KNVV-KDGRP
  → VMAP-LEGACY-CUST-GROUP-TO-S4-KDGRP
  → Migration File CUSTOMER_GROUP
  → S/4 KNVV-KDGRP
  → VAL-CUST-GROUP-ALLOWED-VALUES
  → Customer Sales Area Validation Report
```

Later add graph view.

### 18.6 Patch review

Show:

- source note/evidence;
- AI extracted facts;
- affected objects;
- proposed changes;
- validation result;
- file diff;
- required approvals;
- approve/reject buttons.

---

## 19. Configuration architecture

Use `modelops.config.yaml` for non-secret workspace settings.

Example:

```yaml
workspace:
  name: Customer BP Migration Model
  version: 0.4.1
  default_domain: DOMAIN-CUSTOMER-BP

repository:
  model_path: model
  generated_path: generated
  data_path: data
  templates_path: templates

index:
  engine: sqlite
  path: generated/modelops.db
  rebuild_mode: full

profiling:
  engine: duckdb
  sample_rows: 1000
  max_distinct_values: 500

ai:
  enabled: true
  provider: openai
  require_patch_review: true
  allow_direct_model_write: false
  max_context_objects: 50

validation:
  block_patch_approval_on_errors: true
  warn_on_missing_owner: true
  warn_on_missing_validation: true

sap_context_rules:
  enabled: true
```

Secrets should live in `.env`, not config.

---

## 20. Security and privacy architecture

### 20.1 MVP local security

Rules:

```text
Do not send raw client datasets to AI by default.
Do not store secrets in canonical files.
Exclude raw datasets from Git by default.
Store evidence summaries instead of full sensitive emails where possible.
Show clearly when AI provider is external.
Allow AI-disabled mode.
```

### 20.2 Data minimization

AI context should include:

- relevant object summaries;
- IDs;
- technical field names;
- issue summaries;
- decision summaries;
- validation summaries.

Avoid sending:

- full raw datasets;
- personal data;
- full confidential emails;
- credentials;
- unnecessary client records.

### 20.3 Future enterprise security

Later features:

- workspace users;
- RBAC;
- SSO/OIDC;
- audit trail;
- encryption at rest;
- private AI gateway;
- tenant isolation;
- policy-based AI context filtering;
- evidence redaction.

---

## 21. Audit and change governance

### 21.1 History layers

Use several history layers:

```text
Git
  exact technical diff

ChangeRequest
  business/model change meaning

Decision
  rationale

Issue
  problem or gap

Evidence
  source material

Object change_history
  local readable summary

Generated audit_events
  runtime event trail
```

### 21.2 Audit events

Generated audit event examples:

```json
{
  "event_id": "EVT-20260426-00031",
  "timestamp": "2026-04-26T21:35:00+02:00",
  "actor": "user",
  "action": "approve_patch",
  "object_type": "PatchProposal",
  "object_id": "PATCH-0021",
  "affected_objects": [
    "ATTR-CUST-SALES-CUSTOMER-GROUP",
    "FEP-S4-KNVV-KDGRP"
  ]
}
```

Audit events are runtime history, not the business source of truth.

---

## 22. Git integration architecture

MVP Git support:

```text
detect repository
show dirty state
show changed files
show file diff
warn before applying patch over uncommitted changes
generate suggested commit message
```

Later:

```text
create branch for patch
open pull request
link ChangeRequest to PR
sync with GitHub/GitLab
```

Recommended commit message:

```text
CR-0021 Update Customer Group handling for CH01 / A17

Affected:
- ATTR-CUST-SALES-CUSTOMER-GROUP
- FEP-S4-KNVV-KDGRP
- VMAP-LEGACY-CUST-GROUP-TO-S4-KDGRP
- VAL-CUST-GROUP-ALLOWED-VALUES
```

---

## 23. Observability

### 23.1 MVP observability

Log:

- repository scan duration;
- number of loaded objects;
- validation error/warning counts;
- index build duration;
- dataset profiling duration;
- AI request metadata;
- patch approval/rejection;
- report generation.

Do not log:

- secrets;
- raw sensitive dataset values;
- full AI prompt content by default.

### 23.2 Later observability

Use OpenTelemetry-compatible instrumentation when moving toward hosted/team mode.

Track:

```text
traces
metrics
logs
AI latency
AI token/cost metadata
validation performance
dataset profiling performance
index build duration
```

---

## 24. Performance and scale assumptions

MVP target:

```text
1-10 domains
10-100 entities/contexts
100-5,000 attributes
500-20,000 field endpoints
100-5,000 mappings
10-1,000 value lists
100-100,000 value mapping entries
10-500 datasets/profiles
100-10,000 issues/decisions/change records
```

SQLite is enough for this scale if generated indexes are designed cleanly.

DuckDB becomes useful for:

- large CSV/Parquet profiling;
- analytical queries;
- multi-file dataset analysis;
- repeated profiling workloads.

Performance risks:

```text
large Excel files
huge value mappings
full rebuild on every change
large AI context bundles
graph traversal over unbounded relationships
```

Mitigations:

```text
file hashes
manual rebuild in MVP
incremental rebuild later
profiling limits
sampling
context object limit
relationship traversal depth limit
```

---

## 25. Testing architecture

Required test groups:

```text
repository parsing tests
frontmatter parsing tests
schema validation tests
reference resolution tests
SAP context rule tests
index build tests
dataset profiling tests
gap detection tests
mapping/value-list tests
lineage tests
impact tests
patch proposal tests
patch approval tests
AI output parser tests
API route tests
CLI tests
UI smoke tests
```

Critical tests:

```text
KNVV endpoint without sales-area context fails.
KNB1 endpoint without company-code context fails.
ValueMapping target value missing in ValueList fails.
Attribute without AttributeUsage warns or fails according to config.
Approved mapping using draft logic fails.
PatchProposal cannot directly update canonical model.
Patch approval creates/updates ChangeRequest.
Index rebuild regenerates relationship edges.
Dataset column without endpoint produces gap.
Unmapped source value produces issue draft.
```

---

## 26. Suggested backend structure

```text
apps/api/
  src/modelops/
    main.py

    config/
      settings.py
      workspace.py

    repository/
      scanner.py
      frontmatter.py
      writer.py
      git_adapter.py

    schemas/
      base.py
      domain.py
      migration_object.py
      entity.py
      entity_context.py
      attribute.py
      attribute_usage.py
      system.py
      endpoint.py
      interface.py
      dataset.py
      mapping.py
      value_list.py
      value_mapping.py
      rule.py
      logic.py
      validation.py
      owner.py
      issue.py
      decision.py
      change_request.py
      patch.py
      evidence.py

    services/
      repository_service.py
      object_registry.py
      schema_validation_service.py
      reference_resolver.py
      sap_context_validation_service.py
      index_service.py
      search_document_service.py
      catalog_service.py
      dataset_service.py
      gap_detection_service.py
      mapping_service.py
      validation_service.py
      lineage_service.py
      impact_service.py
      issue_service.py
      decision_service.py
      change_request_service.py
      patch_service.py
      ai_service.py
      report_service.py
      audit_service.py
      git_service.py

    db/
      connection.py
      migrations.py
      repositories.py

    ai/
      providers/
        base.py
        openai_provider.py
        anthropic_provider.py
        ollama_provider.py
        no_ai_provider.py
      prompts/
      context_bundle.py
      output_parsers.py

    api/
      routes_workspace.py
      routes_repository.py
      routes_objects.py
      routes_attributes.py
      routes_lineage.py
      routes_impact.py
      routes_datasets.py
      routes_issues.py
      routes_decisions.py
      routes_changes.py
      routes_patches.py
      routes_ai.py
      routes_reports.py

    cli/
      main.py

    tests/
```

---

## 27. Suggested frontend structure

```text
apps/web/
  src/
    app/
      page.tsx
      workspace/
      domains/
      migration-objects/
      entities/
      attributes/
      attributes/[id]/
      field-endpoints/
      lineage/
      mappings/
      datasets/
      issues/
      decisions/
      change-requests/
      patch-proposals/
      reports/
      settings/

    components/
      layout/
      workspace/
      catalog/
      attributes/
      endpoints/
      lineage/
      impact/
      datasets/
      validation/
      mappings/
      patches/
      governance/
      reports/

    lib/
      api-client.ts
      types.ts
      formatters.ts
      route-helpers.ts
```

Recommended components:

```text
RepositoryStatusCard
ValidationSummaryCard
AttributeCatalogTable
AttributeDetailPanel
FieldRepresentationsTable
EntityContextBadge
MappingCoveragePanel
ValueMappingTable
LineagePathView
ImpactReportView
DatasetProfileView
GapReportView
PatchReviewDiff
IssueList
DecisionTimeline
ChangeHistoryPanel
AIActionsPanel
```

---

## 28. Deployment architecture

### 28.1 Local development

```text
Static docs generator
FastAPI dev server
local repository path
SQLite generated index
optional local AI/Ollama
```

### 28.2 Local packaged app

Later:

```text
Tauri wrapper
bundled frontend
managed backend process
workspace picker
local repository
```

### 28.3 Hosted team deployment

Later:

```text
frontend web app
API backend
Postgres
object storage
Git provider integration
AI gateway
SSO
audit trail
```

---

## 29. Integration architecture

### 29.1 MVP integrations

MVP should support manual and file-based integration:

```text
CSV
Excel
Markdown notes
YAML/JSON import
local folders
Git
```

### 29.2 Later integrations

Add only after MVP value is proven:

```text
Jira issues
Confluence pages
GitHub/GitLab
SAP metadata export
SAP table/field metadata import
SAP value list/customizing export
Cloud ALM references
SolMan references
MDG notes/workflow exports
email/ticket import
```

### 29.3 SAP integration caution

Do not start with direct SAP write-back.

Safer first SAP integration:

```text
import metadata
import value list snapshots
import validation exports
import configuration snapshots
link evidence to SAP objects
```

Direct writes create risk and scope explosion.

---

## 30. Example end-to-end product scenario

Scenario:

```text
Customer Group in KNVV-KDGRP needs special handling for CH01 / A17 Footlocker.
```

System flow:

```text
1. Attribute page shows Customer Group.
2. AttributeUsage shows Customer Sales Area context.
3. FieldEndpoint shows S/4 representation KNVV-KDGRP.
4. Mapping shows source customer group to target KNVV-KDGRP.
5. ValueMapping shows A17 source value.
6. ValueList shows allowed S/4 customer group values.
7. Dataset profiling detects A17 records.
8. Validation detects missing/invalid mapping or target value.
9. Issue is created for CH01 / A17 configuration gap.
10. Decision records accepted special handling.
11. ChangeRequest tracks approved model change.
12. AI PatchProposal is generated from pasted email/ticket.
13. User reviews diff and approves.
14. Canonical files are updated.
15. Index is rebuilt.
16. Impact report shows affected mapping, validation, dataset, owner, issue, and AMS handover action.
```

---

## 31. Product architecture quality bar

The system is good enough when a user can open one attribute and understand:

```text
what it means
where it exists in source/staging/target systems
whether it is central/company-code/sales-area/role/interface specific
how it is mapped
how values are transformed
which values are allowed
how it is validated
who owns it
which issues and decisions explain it
what changed recently
what breaks if it changes
```

The system is not good enough if:

```text
Attribute and SAP field are collapsed into one flat row.
KNVV fields are not modeled as sales-area-dependent.
AI directly mutates approved model files.
The generated database becomes the only source of truth.
Large raw datasets are mixed into canonical model files.
Issues, decisions, and changes are not linked to affected objects.
```

---

## 32. Product roadmap from architecture perspective

### Phase 1 — File repository and schemas

Deliver:

- repository structure;
- parser;
- object registry;
- Pydantic schemas;
- validation report;
- sample Customer/BP model.

### Phase 2 — Attribute and endpoint workspace

Deliver:

- Attribute;
- AttributeUsage;
- EntityContext;
- FieldEndpoint;
- SAP context checks;
- catalog UI;
- attribute detail UI.

### Phase 3 — Mapping and value governance

Deliver:

- MappingSet;
- Mapping;
- ValueList;
- ValueMapping;
- mapping coverage;
- value coverage.

### Phase 4 — Dataset profiling and gap detection

Deliver:

- CSV/Excel profiling;
- dataset metadata;
- column matching;
- unknown column detection;
- unmapped value detection;
- gap report;
- issue draft generation.

### Phase 5 — Lineage and impact

Deliver:

- relationship edge generation;
- lineage path view;
- impact report;
- owner/issue/decision impact.

### Phase 6 — Governance workflow

Deliver:

- issues;
- decisions;
- evidence;
- ChangeRequests;
- object change history;
- Git diff preview.

### Phase 7 — AI patch review

Deliver:

- context bundle;
- AI patch generation;
- structured output parser;
- PatchProposal files;
- review/approve/reject;
- index rebuild.

### Phase 8 — Packaging and team options

Deliver only after core value is proven:

- Tauri desktop shell;
- GitHub/GitLab integration;
- hosted team workspace;
- Postgres;
- AI gateway;
- enterprise identity.

---

## 33. Modern architecture options for later

### 33.1 Optional Tauri desktop shell

Use if local desktop UX matters.

Value:

```text
single app launcher
workspace picker
background process management
local folder access
cross-platform packaging
```

Risk:

```text
extra packaging complexity
updates and installers
platform-specific issues
```

Decision:

```text
Add after local web/CLI MVP works.
```

### 33.2 Optional DuckDB analytics layer

Use if dataset profiling becomes heavy.

Value:

```text
fast CSV/Parquet scans
local analytical SQL
larger-than-memory style workflows in some cases
easy data profiling
```

Risk:

```text
additional dependency
two local database concepts if SQLite also exists
```

Decision:

```text
SQLite for model index.
DuckDB for dataset profiling/analytics.
Do not replace canonical files with DuckDB.
```

### 33.3 Optional Postgres hosted read/write layer

Use for team/SaaS version.

Value:

```text
multi-user access
server-side indexes
central audit trail
team workflows
```

Risk:

```text
loss of simple local-first model if introduced too early
more DevOps
migration complexity
```

Decision:

```text
Introduce only for hosted/team mode.
```

### 33.4 Optional graph database

Use only if relationship complexity grows beyond simple edge tables.

Value:

```text
complex lineage queries
graph algorithms
large connected model analysis
```

Risk:

```text
over-engineering
higher operational burden
harder local install
```

Decision:

```text
Start with SQLite object_relationships.
Add graph DB later only with proof.
```

### 33.5 Optional AI gateway

Use for enterprise AI governance.

Value:

```text
provider routing
budget control
central policy
key management
logging
fallbacks
```

Risk:

```text
extra infrastructure
supply-chain/security review
debugging complexity
```

Decision:

```text
Start with direct provider adapters.
Add gateway for hosted/team mode.
```

### 33.6 Optional MCP tools

Use after repository API is useful.

Value:

```text
external agents can query model objects
coding agents can inspect architecture
AI tools can call deterministic functions
```

Risk:

```text
premature protocol work
tool surface can become unstable
```

Decision:

```text
Add MCP later around stable CLI/API tools.
```

---

## 34. Final architecture recommendation

Build the product in this order:

```text
1. File repository + schema validation.
2. Attribute / AttributeUsage / FieldEndpoint model.
3. SAP context validation.
4. SQLite generated index.
5. Attribute catalog and detail UI.
6. Mapping/value mapping/value list checks.
7. Dataset profiling and gap detection.
8. Lineage and impact.
9. Issues/decisions/change requests.
10. AI patch proposal workflow.
11. Reports and AMS handover.
12. Packaging/team features.
```

Best technical starting point:

```text
FastAPI + Pydantic + SQLite + generated static docs + Typer CLI + Markdown/YAML repository.
```

Keep this line strict:

```text
The product governs model knowledge.
It does not directly govern SAP master data records.
```

That distinction keeps the architecture realistic, sellable, and implementable.
