# DAMA-DMBOK Correlation Guide for Martenweave

This guide maps Martenweave concepts to data management disciplines without reproducing DAMA-DMBOK text. It is intended for data governance and MDM audiences who want to understand where Martenweave fits and what it does not cover.

## Mapping Overview

| Data Management Area | Martenweave Capability | Notes |
|---|---|---|
| Data Governance | Canonical model repository, ownership fields, validation pipeline, PatchProposal workflow | Lightweight governance layer embedded in version-controlled files |
| Metadata Management | Markdown + YAML frontmatter objects, SQLite index, search documents | Business and technical metadata are first-class canonical objects |
| Data Quality | ValidationRule, DataQualityCheck, ValueList, coverage analysis in health report | Deterministic validation before indexing; rule coverage tracked |
| Master and Reference Data | MasterDataDomain, ValueList, ValueMapping, BusinessEntity | Supports reference data governance and cross-system value mapping |
| Data Modeling and Design | Attribute, FieldEndpoint, EntityContext, Mapping, AttributeUsage | Separates business meaning from physical representation |
| Data Architecture | Domain packs, system landscape, lineage edges, impact analysis | Extensible domain-specific rules; traceable relationships |
| Data Integration / Interoperability | Mapping, ValueMapping, Dataset profiling, import-model-sheet | Maps source to target and tracks value-level translations |
| Data Security and Stewardship | OwnershipRole, business_owner, technical_owner, data_steward, approver | Ownership is validated and reported; no RBAC or ACL enforcement |
| Document / Content / Evidence Management | Evidence, Decision, Issue, ChangeRequest | Captures rationale and audit trail for model decisions |
| Data Lifecycle / Change Management | PatchProposal, ChangeRequest, audit log, proposal impact analysis | Proposal-first changes with human approval and append-only audit |

## Martenweave Object-to-Governance Mapping

| Martenweave Object | Governance Concept | Purpose |
|---|---|---|
| Attribute | Business semantic definition | Describes what a concept means, independent of any system |
| FieldEndpoint | Physical data element | Represents a column, field, or API property in a specific system |
| Dataset | Data asset | A file, table, or stream that can be profiled and mapped |
| Mapping | Integration contract | Links a source FieldEndpoint to a target FieldEndpoint |
| ValueList | Reference data | Defines allowed values for a field or attribute |
| ValueMapping | Cross-system reference translation | Maps codes from one ValueList to another |
| ValidationRule | Data quality rule | Asserts expected correctness for an Attribute or FieldEndpoint |
| DataQualityCheck | Quality measurement | Records the result of a concrete quality check run |
| Evidence | Supporting documentation | Links decisions and issues to external documents or analysis |
| Decision | Accepted reasoning | Captures why a model choice was made |
| OwnershipRole | Stewardship assignment | Defines who is accountable for a model object |
| ChangeRequest | Approved model change | Records a human-approved modification to the canonical model |
| PatchProposal | Suggested model change | AI or import-generated proposal awaiting review |

## Strengths

- **Canonical files as source of truth**: Everything is in version-controlled Markdown + YAML.
- **Deterministic validation**: No AI involved in validation; rules are explicit and testable.
- **Local-first**: No cloud dependencies or SaaS lock-in.
- **Traceability**: BFS traversal over relationships shows upstream and downstream impact.
- **Proposal-first workflow**: AI can suggest changes, but humans review and approve.

## Intentionally Lightweight

- No built-in workflow engine or BPMN-style state machines.
- No RBAC, ACL, or fine-grained permission system.
- No real-time data quality monitoring or streaming alerts.
- No ETL execution or data movement capabilities.

## Out of Scope

- Data platform infrastructure (warehouses, lakes, streaming).
- BI, reporting, or dashboarding.
- Data privacy compliance automation (GDPR deletion, etc.).
- Machine learning model registry or experiment tracking.

## SAP Mention

SAP is used in examples because it is a common source of complex master data models. Martenweave is not SAP-specific. The same modeling approach works for generic product catalogs, customer databases, healthcare records, or financial instruments.
