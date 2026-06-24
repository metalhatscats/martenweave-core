# Martenweave DAMA-DMBOK Alignment Guide

Version: 0.2
Status: Aligned with v0.4.1 implementation
Scope: How Martenweave aligns with DAMA-DMBOK knowledge areas for data governance, MDM, and SAP migration teams

---

## Implementation Status

| Capability | Status | Notes |
|---|---|---|
| Canonical model files | Implemented | Markdown + YAML frontmatter under `model/` |
| Deterministic validation | Implemented | `validate` command checks schema, references, SAP context, governance warnings |
| SQLite index + JSONL exports | Implemented | `build-index` generates rebuildable artifacts |
| Dataset-to-model gap detection | Implemented | `gaps` command profiles CSV/XLSX and compares columns against FieldEndpoints |
| Gap-to-proposal promotion | Implemented | `gaps --promote-to-proposal` creates draft PatchProposal from unmodeled columns |
| Model-side gap detection | Implemented | `gaps <dataset.csv> --repo ./my-model --check-model` finds Attributes without FieldEndpoints and missing owners |
| Impact and trace analysis | Implemented | `trace` and `impact` use BFS traversal over relationship graph |
| Health report | Implemented | `health` shows object counts, coverage gaps, ownership, and data-quality coverage |
| Governance scorecard | Implemented | `scorecard` shows readiness metrics with pass/warning/fail status |
| PatchProposal workflow | Implemented | `propose-patch`, `proposal validate`, `proposal impact`, `proposal apply` |
| ChangeRequest workflow | Implemented | `change-request create`, `approve`, `reject`, `list`, `show`, `update-status` |
| Audit trail | Implemented | `audit-log` queries append-only `audit_events.jsonl` |
| AI provider adapter | Partial | `NoProviderAdapter` (deterministic scaffold) and `KimiAdapter` implemented; `GoogleADKAdapter` and `OllamaAdapter` are target state |
| Decision evidence validation | Implemented | `validate --check-decisions` validates Decision.evidence references |
| Lifecycle validation | Implemented | Checks deprecated_reason, suspicious status transitions, retired-object references |
| Circular reference detection | Implemented | `REFERENCE_CIRCULAR` error detected in validation pipeline |
| Value mapping governance | Implemented | `VALUE_MAPPING_SOURCE_CODE_INVALID` and `VALUE_MAPPING_TARGET_CODE_INVALID` errors |
| Dataset profiling | Implemented | `profile-dataset` analyzes CSV/XLSX columns and distributions |
| Model inference from dataset | Implemented | `infer-model` creates draft objects from dataset profile |
| Static docs generation | Implemented | `docs-build` generates Markdown docs from index |
| Export to CSV/XLSX | Implemented | `export-model` and `export-sheets` |
| Config guard | Implemented | `config-guard` scans for secrets and configuration issues |
| Local API server | Implemented | `serve` starts FastAPI server |
| MCP server | Implemented | `mcp` starts MCP server for agent integration |
| Semantic search | Target state | Keyword + exact match only; vector/semantic search is planned |
| Cross-repository diff | Implemented | `diff` compares two model repositories |
| AMS handover export | Target state | Manual or template-based; AI-generated handover is planned |

---

## Executive Summary

Martenweave is a backend-first, agentic data model registry that turns scattered model knowledge into a traceable, validated, AI-ready model layer. It is designed for SAP migration, Master Data Management (MDM), data governance, and Application Management Services (AMS) teams who need structured model knowledge without enterprise platform overhead.

This guide maps Martenweave capabilities to DAMA-DMBOK knowledge areas. It does not claim full DAMA compliance. Instead, it uses DAMA as a conceptual framework to show where Martenweave aligns strongly, where it partially supports professional data management practice, and what remains out of scope for the current product boundary.

**Key principle:** Martenweave is a *model knowledge layer*, not a data platform. It governs the *definitions, relationships, mappings, rules, and decisions* that describe data — not the data records themselves.

---

## What Martenweave Is

| Capability | Description |
|---|---|
| **Canonical model registry** | Markdown + YAML frontmatter objects stored in `model/`, version-controlled, human-readable |
| **Deterministic validation engine** | Multi-layer validation (file parsing, schema, references, SAP context, mapping coherence, ownership, governance) |
| **Generated index layer** | SQLite index, JSONL exports, search documents, lineage edges — all rebuildable from canonical files |
| **Dataset-to-model gap detection** | Profiles CSV/XLSX datasets and detects unmodeled columns, missing endpoints, ownership gaps |
| **Impact and trace analysis** | BFS traversal over relationship graph to find upstream/downstream effects of changes |
| **Proposal-first change workflow** | AI or user creates `PatchProposal` → deterministic validation → human review → `ChangeRequest` → approved apply |
| **Audit trail** | Append-only `audit_events.jsonl` recording every proposal, validation, approval, and index rebuild |
| **Local-first, embeddable** | CLI-driven, no cloud dependency, fits into Git workflows, CI pipelines, and agent toolchains |

---

## What Martenweave Is Not

| Misconception | Reality |
|---|---|
| A SAP-only tool | SAP is the first domain pack. The core works for any data model: product catalogs, CRM, finance, healthcare |
| A database-first MDM platform | It is a *file-first* model knowledge layer. It does not store master data records |
| A workflow engine | No BPMN, no state machines. Workflow is enforced by CLI commands, validation rules, and Git |
| A SaaS platform | No cloud lock-in. Runs locally, in CI, or embedded in other tools |
| An autonomous AI agent | AI proposes changes; validators verify; humans approve. No silent mutation |
| A data catalog | It catalogs *model objects* (attributes, fields, mappings), not datasets or tables |
| A data quality monitoring system | It validates *model correctness*, not streaming data quality metrics |
| An ETL tool | It documents mappings and transformations; it does not execute them |
| A replacement for SAP MDG / Datasphere / Migration Cockpit | Complements them by structuring the *knowledge* that feeds into them |

---

## DAMA Knowledge Area Alignment Table

| DAMA Knowledge Area | Martenweave Alignment | Strength | Notes |
|---|---|---|---|
| **Data Governance** | Strong | Canonical files as policy, ownership fields, validation pipeline, proposal workflow | Lightweight governance embedded in version-controlled files |
| **Data Architecture** | Strong | Domain packs, system landscape, lineage edges, impact analysis | Extensible domain-specific rules; traceable relationships |
| **Data Modeling and Design** | Strong | Attribute/FieldEndpoint separation, EntityContext, Mapping, AttributeUsage | Separates business meaning from physical representation |
| **Metadata Management** | Strong | Markdown + YAML frontmatter, SQLite index, search documents, relationship taxonomy | Business and technical metadata are first-class canonical objects |
| **Data Quality** | Partial | ValidationRule, DataQualityCheck, ValueList, coverage analysis, gap detection | Validates *model* quality, not runtime data quality |
| **Reference and Master Data** | Partial | MasterDataDomain, ValueList, ValueMapping, BusinessEntity | Supports reference data governance; does not store master data records |
| **Data Integration and Interoperability** | Partial | Mapping, ValueMapping, Dataset profiling, import-model-sheet | Documents integration contracts; does not execute data movement |
| **Data Security** | Partial | OwnershipRole, data_classification, business_owner, technical_owner | Ownership is validated and reported; no RBAC or ACL enforcement |
| **Data Lifecycle** | Partial | PatchProposal, ChangeRequest, audit log, proposal impact analysis | Proposal-first changes with human approval and append-only audit |
| **Document / Content / Evidence** | Partial | Evidence, Decision, Issue, ChangeRequest | Captures rationale and audit trail for model decisions |
| **Data Warehousing / BI** | Out of scope | — | Not a warehouse, lake, or BI platform |
| **Data Storage and Operations** | Out of scope | — | No database administration or infrastructure management |
| **Big Data / AI / ML** | Out of scope | — | No ML model registry or experiment tracking |

---

## Strong Alignment Areas

### 1. Data Governance

Martenweave embeds governance into the model layer itself:

- **Policy as code:** Validation rules are deterministic, testable, and version-controlled. A rule like "KNVV fields must be in `customer_sales_area` context" is enforced by the validator, not by convention.
- **Ownership accountability:** Every active `Attribute`, `FieldEndpoint`, `Mapping`, `ValueList`, and `ValidationRule` should declare a `business_owner`, `technical_owner`, `data_steward`, or `accountable_team`. The validator emits `OWNERSHIP_MISSING` warnings.
- **Change control:** The `PatchProposal` → `ChangeRequest` → approval → apply → audit workflow ensures no model change happens without traceability.
- **Audit trail:** `generated/audit_events.jsonl` records `change_request_created`, `patch_proposal_validated`, `change_applied`, `index_rebuilt`, and `issue_resolved` events.

**SAP example:** When a Business Partner migration requires adding a new sales organization (CH01), the `ChangeRequest` records who requested it, which `PatchProposal` it came from, which `affected_objects` were modified, and who approved it.

### 2. Data Architecture

Martenweave models data architecture explicitly:

- **Domain packs** encapsulate system-specific rules. The SAP domain pack knows that `KNVV` = Customer Sales Area, `KNB1` = Customer Company Code, `BUT000` = BP Central.
- **System landscape** is modeled via `System`, `SystemEnvironment`, and `Interface` objects.
- **Lineage** is generated from canonical references and stored as directed edges in SQLite.
- **Impact analysis** uses BFS traversal to answer "what breaks if I change this?"

**SAP example:** Changing `VLIST-S4-CUST-GROUP` (allowed Customer Group values) triggers impact analysis that finds affected `ValueMapping`s, `ValidationRule`s, `Dataset`s, and `Issue`s — all traceable through the relationship graph.

### 3. Data Modeling and Design

Martenweave enforces a layered modeling approach:

| Layer | Object | Purpose |
|---|---|---|
| Business meaning | `Attribute` | What a concept means, independent of any system |
| Business context | `EntityContext` | Where the concept lives (e.g., S/4 sales area) |
| Usage linkage | `AttributeUsage` | How the attribute behaves in that context |
| Physical representation | `FieldEndpoint` | Column, field, or API property in a specific system |
| Movement | `Mapping` | Source-to-target link between FieldEndpoints |
| Rules | `ValidationRule`, `ValueList` | Constraints and allowed values |

**SAP example:** `ATTR-CUST-SALES-CUSTOMER-GROUP` (business meaning) is represented by `FEP-S4-KNVV-KDGRP` (S/4 field), `FEP-LEGACY-CUST-GROUP` (legacy field), and linked by `MAP-CUST-GROUP-LEGACY-TO-KNVV` (migration mapping). If S/4 table changes, only the FieldEndpoint changes; the Attribute stays stable.

### 4. Metadata Management

Every canonical object is metadata:

- **Business metadata:** `name`, `description`, `semantic_category`, `data_classification`
- **Technical metadata:** `endpoint_type`, `technical_name`, `sap_table`, `sap_field`, `system`
- **Governance metadata:** `business_owner`, `data_steward`, `approver`, `status`, `created_at`
- **Relationship metadata:** `domain`, `entity`, `entity_context`, `attribute`, `source_endpoint`, `target_endpoint`

The SQLite index makes this metadata queryable. The search document export makes it searchable.

---

## Partial Alignment Areas

### 5. Data Quality

Martenweave supports data quality *modeling* but not runtime monitoring:

| DQ Dimension | Martenweave Support | How |
|---|---|---|
| **Completeness** | Partial | Dataset gap detection finds unmodeled columns; model gap detection finds Attributes without FieldEndpoints |
| **Validity** | Partial | `ValidationRule` and `ValueList` document expected constraints; validator checks mapping coherence |
| **Consistency** | Partial | Reference validation ensures no broken links; SAP context rules enforce table-context alignment |
| **Uniqueness** | Partial | ID uniqueness is enforced; duplicate dataset columns are flagged |
| **Referential integrity** | Partial | Broken references emit `REFERENCE_BROKEN` errors |
| **Traceability** | Strong | Full lineage from source to target via relationship graph |
| **Conformity to model rules** | Strong | Deterministic validation enforces schema, context, and governance rules |

**Limitation:** Martenweave does not run data profiling against production databases, monitor data quality KPIs over time, or trigger alerts. It documents the *rules* and *checks* that a data quality system should run.

### 6. Reference and Master Data

Martenweave governs reference data definitions but does not store the data:

- **ValueList** documents allowed values (e.g., S/4 Customer Group codes).
- **ValueMapping** documents cross-system translations (e.g., legacy code `A17` → S/4 code `01`).
- **MasterDataDomain** groups related master data objects.
- **BusinessEntity** defines conceptual master data objects.

**Limitation:** The actual master data records live in SAP, the legacy system, or the data warehouse. Martenweave governs the *model* that describes them.

### 7. Data Integration and Interoperability

Martenweave documents integration contracts:

- **Mapping** links source and target FieldEndpoints.
- **ValueMapping** translates codes between systems.
- **TransformationLogic** documents derivation, defaulting, or enrichment rules.
- **Interface** documents data movement interfaces.
- **Dataset** profiles and maps data assets.

**Limitation:** Martenweave does not execute ETL, run data pipelines, or move data. It produces the *knowledge layer* that integration teams use to build and verify pipelines.

### 8. Data Security

Martenweave handles security at the model layer:

- **data_classification** field on `Attribute` supports `public`, `internal`, `confidential`, `restricted`, `personal_data`, `sensitive_personal_data`.
- **Ownership fields** define accountability.
- **Secret guardrails** prevent API keys from leaking into canonical files or generated artifacts.
- **Privacy scrubbing** prevents raw dataset samples from being sent to AI providers by default.

**Limitation:** No RBAC, ACL, encryption-at-rest, or fine-grained permission system. Access control is delegated to Git, file system permissions, and the hosting environment.

### 9. Data Lifecycle / Change Management

Martenweave has a proposal-first change lifecycle:

```
Source evidence → PatchProposal → validation → review → ChangeRequest → approval → apply → index rebuild → audit
```

**Limitation:** There is no automatic state machine or workflow engine. Status transitions are deliberate edits. The lightweight path allows small changes to skip the full lifecycle, but high-risk changes (mapped fields, value lists, validation rules, ownership changes) must use the full path.

### 10. Document / Content / Evidence Management

Martenweave captures rationale:

- **Evidence** links decisions and issues to external documents or analysis.
- **Decision** records why a model choice was made.
- **Issue** documents gaps, risks, and blockers.
- **ChangeRequest** records approved intent.

**Limitation:** No document storage, version control for attachments, or full document management system. Evidence objects reference external sources.

---

## Explicitly Out-of-Scope Areas for MVP

| Area | Why Out of Scope | Future Consideration |
|---|---|---|
| **Data Warehousing / BI** | Martenweave is not a warehouse, lake, or reporting platform | Export to dbt, OpenLineage, or BI metadata layers |
| **Data Storage and Operations** | No database administration, backup, or infrastructure management | Delegate to Git, SQLite, and hosting environment |
| **Big Data / AI / ML** | No ML model registry, experiment tracking, or feature store | Integrate with ML metadata standards if needed |
| **Real-time data quality monitoring** | No streaming, no alerts, no KPI dashboards | Integrate with data quality tools via export |
| **Data privacy compliance automation** | No GDPR deletion workflows, no DLP | Document data classification; integrate with privacy tools |
| **Enterprise identity and access management** | No RBAC, no SSO, no LDAP | Use Git/GitHub identity; add basic auth to API server if needed |
| **Workflow engine / BPMN** | No state machines, no orchestration | Keep lightweight; possibly integrate with external workflow tools |

---

## SAP Migration / MDM Interpretation

Martenweave is particularly useful for SAP teams because SAP master data is inherently complex, context-dependent, and poorly documented in scattered Excel files and tickets.

### Why SAP Teams Need This

| SAP Challenge | Martenweave Response |
|---|---|
| Field meanings buried in Excel | `Attribute` objects with business definitions |
| Table-context rules learned by trial and error | Deterministic validation: `KNVV` → `customer_sales_area`, `KNB1` → `customer_company_code` |
| Mapping spreadsheets with no lineage | `Mapping` and `ValueMapping` objects with traceable relationships |
| Cutover readiness unclear | `Issue`, `Decision`, `ValidationRule`, and health scorecard |
| AMS handover loses knowledge | Canonical files + generated docs + audit trail |
| AI assistants hallucinate SAP facts | Bounded context bundles, deterministic validation, human approval gates |

### What Martenweave Does Not Replace

| SAP Tool | Martenweave Relationship |
|---|---|
| **SAP MDG** | MDG governs master data records. Martenweave governs the *model knowledge* that describes them. |
| **SAP Datasphere** | Datasphere is a data warehouse. Martenweave can export lineage to it but is not a warehouse. |
| **SAP Migration Cockpit** | The Cockpit executes migration. Martenweave documents the mapping and validation rules that feed into it. |
| **SAP S/4HANA** | S/4 is the system of record. Martenweave is the knowledge layer *about* that system. |

---

## Risks and Gaps

| Gap | Risk | Mitigation |
|---|---|---|
| **No RBAC/ACL** | Unauthorized model changes in shared environments | Git branch protection, file system permissions, separate proposer/approver roles |
| **No real-time data quality monitoring** | Model may drift from actual data | Periodic dataset profiling, gap detection, health reports |
| **AI provider not fully implemented** | KimiAdapter and GoogleADKAdapter are planned but not complete | `NoProviderAdapter` works deterministically; `KimiAdapter` is implemented; AI is optional |
| **Schema fields not fully declared** | Some fields (`requiredness`, `priority`, `role`) pass through silently | Document as conventions; add to Pydantic schemas in future |
| **No graph database** | Large models may hit SQLite traversal limits | Current BFS is sufficient for MVP; evaluate Neo4j only if scale demands |
| **No enterprise SSO** | Identity management delegated to Git/GitHub | Acceptable for backend-first, CLI-driven tool |
| **Validation does not check actual SAP data** | Model may claim a field is valid while SAP data is dirty | Martenweave validates the *model*, not the data. Use SAP tools for data validation. |

---

## Recommended Next Product Slices

1. **Complete AI provider adapters** — Implement `KimiAdapter` and `GoogleADKAdapter` with full structured output validation and fallback to `NoProviderAdapter`.
2. **Add `requiredness` and `priority` to Pydantic schemas** — Close the gap between documented taxonomy and runtime schema validation.
3. **Dataset profiling integration** — Connect `profile-dataset` and `gaps` commands to the proposal workflow so gap detection auto-creates `PatchProposal` drafts.
4. **Health report scoring** — Turn the `health` command output into a numeric scorecard with trend tracking across releases.
5. **AMS handover export** — Generate a static Markdown or XLSX handover package from a domain's canonical objects, issues, decisions, and validation rules.

---

## Related Documents

- `docs/governance/DATA_GOVERNANCE_OPERATING_MODEL.md` — Practical operating model for governance work
- `docs/governance/DATA_QUALITY_AND_METADATA_MODEL.md` — Data quality and metadata treatment
- `docs/governance/AI_READY_DATA_MODEL_LAYER.md` — AI-ready model layer design
- `docs/dama-correlation.md` — Lightweight object-to-governance mapping
- `docs/canonical-model.md` — Canonical object model reference
- `docs/change-workflow.md` — Change request workflow design
- `docs/validation-methodology-warnings.md` — Validation warning codes and fixes
