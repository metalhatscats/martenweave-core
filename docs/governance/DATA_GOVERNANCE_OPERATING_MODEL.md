# Martenweave Data Governance Operating Model

Version: 0.2
Status: Aligned with v0.4.0 implementation
Scope: Practical operating model for using Martenweave in data governance, SAP migration, MDM, and AMS work

---

## Implementation Status

| Capability | Status | Notes |
|---|---|---|
| Canonical file-based governance | Implemented | `model/` directory is the source of truth |
| Deterministic validation | Implemented | `validate` command enforces structure, references, SAP context, ownership |
| Proposal-first editing | Implemented | `propose-patch` → `proposal validate` → `proposal impact` → `proposal apply` |
| Human approval gates | Implemented | `change-request approve` requires explicit approver; `change-request reject` records reason |
| Disposable generated index | Implemented | `build-index` regenerates SQLite, JSONL, search docs, lineage edges |
| Append-only audit | Implemented | `audit-log` queries `generated/audit_events.jsonl` |
| Role definitions | Implemented | Seven roles documented; enforcement is by convention and CLI workflow, not RBAC |
| High-risk / low-risk change rules | Implemented | Risk computed by `compute_proposal_risk()` based on affected objects, mappings, value lists, impact depth |
| Lightweight path for small changes | Implemented | `proposal accept` for low-risk proposals; `change-request` for high-risk changes |
| SAP Business Partner example | Implemented | `examples/customer_bp_model/` contains working KNVV/KDGRP, KNB1, BUT000 model |
| AMS handover export | Target state | Manual or template-based; automated AI-generated handover is planned |

---

## Governance Principles

Martenweave governance is **file-based, Git-native, and validation-gated**. There is no workflow engine, no real-time collaboration server, and no enterprise identity system. Governance is enforced by:

1. **Canonical files as policy** — The `model/` directory is the source of truth. Every object is a Markdown + YAML file.
2. **Deterministic validation** — The validator checks structure, references, SAP context, ownership, and governance rules before any change is accepted.
3. **Proposal-first editing** — No direct canonical file mutation from chat, import, or AI inference. All changes flow through `PatchProposal` → review → `ChangeRequest` → approval → apply.
4. **Human approval gates** — High-risk changes require explicit approver sign-off. Low-risk changes may use a lightweight path.
5. **Disposable generated index** — SQLite index, JSONL exports, and search documents are rebuildable from canonical files. They are never manually edited.
6. **Append-only audit** — Every workflow action generates an `AuditEvent` in `generated/audit_events.jsonl`.

---

## Roles

Martenweave defines seven primary roles. One person may wear multiple hats, but **proposer and approver should never be the same person** for high-risk changes.

### Data Owner

- **Accountability:** Owns the business meaning of a domain or entity.
- **Typical title:** Business process owner, domain lead, functional lead.
- **Martenweave mapping:** `business_owner` on `MasterDataDomain`, `BusinessEntity`, `Attribute`.
- **Actions:**
  - Reviews and approves `ChangeRequest`s that affect their domain.
  - Provides context for mappings and value translations.
  - Validates that `Attribute` definitions match business reality.
- **CLI usage:** `modelops change-request approve CR-001 --approver PERSON-OWNER-001`

### Data Steward

- **Accountability:** Ensures business definitions are accurate, consistent, and current.
- **Typical title:** Data steward, MDM analyst, governance analyst.
- **Martenweave mapping:** `data_steward` on `Attribute`, `BusinessEntity`, `ValueList`, `Dataset`.
- **Actions:**
  - Reviews attribute definitions, value lists, and validation rules.
  - Approves semantic changes (e.g., adding a new Customer Group value).
  - Runs `modelops validate` and `modelops health` to monitor model quality.
  - Creates `PatchProposal`s for governance-driven changes.
- **CLI usage:** `modelops validate --repo ./my-model`, `modelops scorecard --repo ./my-model`

### SAP Functional Consultant

- **Accountability:** Ensures SAP context correctness (tables, fields, roles, customizing).
- **Typical title:** SAP functional consultant, MDG consultant, S/4HANA analyst.
- **Martenweave mapping:** `technical_owner` on `FieldEndpoint`, `EntityContext`, `System`.
- **Actions:**
  - Reviews `FieldEndpoint` objects for correct `sap_table`, `sap_field`, and `context_category`.
  - Validates that `KNVV` fields are in `customer_sales_area` context.
  - Reviews mapping correctness for cutover.
  - Runs `modelops trace` and `modelops impact` before approving technical changes.
- **CLI usage:** `modelops trace FEP-S4-KNVV-KDGRP --repo ./my-model`, `modelops impact FEP-S4-KNVV-KDGRP --repo ./my-model`

### Migration Lead

- **Accountability:** Delivers clean master data migration on time.
- **Typical title:** Migration lead, data migration manager, cutover lead.
- **Martenweave mapping:** `accountable_team` on `MigrationObject`, `MappingSet`.
- **Actions:**
  - Defines migration scope via `MigrationObject` and `MappingSet`.
  - Reviews `Dataset` profiles and gap reports.
  - Ensures all mapped fields have `ValidationRule`s before cutover.
  - Tracks open `Issue`s and `Decision`s for cutover readiness.
- **CLI usage:** `modelops gaps ./data/load.csv --repo ./my-model`, `modelops gap-report --repo ./my-model`

### Data Quality Analyst

- **Accountability:** Ensures model quality rules are complete and correct.
- **Typical title:** Data quality analyst, testing lead, validation engineer.
- **Martenweave mapping:** `technical_owner` on `ValidationRule`, `DataQualityCheck`.
- **Actions:**
  - Writes and reviews `ValidationRule` objects.
  - Reviews `ValueList` completeness.
  - Runs `modelops validate --strict` in CI pipelines.
  - Investigates `REFERENCE_BROKEN`, `SAP_CONTEXT_KNVV_REQUIRES_SALES_AREA`, and other validation errors.
- **CLI usage:** `modelops validate --repo ./my-model --strict`, `modelops health --repo ./my-model`

### AI Assistant / Agent Operator

- **Accountability:** Supervises AI-assisted modeling; validates AI output.
- **Typical title:** AI operator, automation engineer, tool administrator.
- **Martenweave mapping:** `PatchProposal.created_by = "ai"`, human approver on `ChangeRequest`.
- **Actions:**
  - Runs `modelops propose-patch --from note.md` to generate AI proposals.
  - Reviews AI-generated `PatchProposal`s for hallucinated SAP facts.
  - Adjusts AI assumptions and required human checks.
  - Ensures AI proposals pass deterministic validation before human review.
- **CLI usage:** `modelops propose-patch --from ./note.md --repo ./my-model`, `modelops proposal validate PP-001 --repo ./my-model`

### Validator (System Role)

- **Accountability:** Enforces deterministic rules with no human bias.
- **Nature:** Automated system role, not a person.
- **Actions:**
  - Checks ID format, uniqueness, and prefix/type alignment.
  - Resolves references and emits `REFERENCE_BROKEN` errors.
  - Enforces SAP context rules (e.g., `KNVV` → `customer_sales_area`).
  - Validates mapping coherence and value mapping completeness.
  - Checks ownership presence on active objects.
  - Validates `PatchProposal` operations against allow-lists.
- **CLI usage:** `modelops validate --repo ./my-model`

### Approver

- **Accountability:** Formal sign-off on changes before apply.
- **Typical title:** Same as Data Owner, Data Steward, or SAP Functional Consultant, but acting in approval capacity.
- **Martenweave mapping:** `ChangeRequest.approvers` list, `approver` field on objects.
- **Actions:**
  - Reviews `PatchProposal` impact analysis.
  - Confirms that validation passes with zero errors.
  - Signs off on `ChangeRequest` via CLI or GitHub PR merge.
- **CLI usage:** `modelops change-request approve CR-001 --approver PERSON-APPROVER-001`

---

## Model Change Lifecycle

Every change to the canonical model follows this lifecycle:

```
┌─────────────────┐
│  Source Evidence │  ← Email, ticket, workshop note, dataset profile, validation error
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   PatchProposal  │  ← AI or user creates structured proposal with affected_objects and operations
│  (pending_review)│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    Validation    │  ← Deterministic validation: schema, references, SAP context, governance rules
│   (valid/invalid) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│     Review       │  ← Human reviewer inspects diff, impact, assumptions, required checks
│  (approve/reject/ │
│   request revision)│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   ChangeRequest  │  ← Human creates CR linking proposal, affected objects, reason, approvers
│    (pending)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    Approval      │  ← Approver signs off; CR status → approved
│   (approved)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│      Apply       │  ← Proposal operations applied to canonical files; CR status → implemented
│  (implemented)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Index Rebuild   │  ← `modelops build-index` regenerates SQLite, JSONL, search docs, lineage
│  (fresh index)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Report Generation│  ← Health report, scorecard, impact report, AMS handover summary
│   (published)    │
└─────────────────┘
```

### State Definitions

| State | Meaning | Who Moves It |
|---|---|---|
| `pending_review` | Proposal created, not yet evaluated | System or AI |
| `valid` / `invalid` | Validation result on proposal | Validator (system) |
| `approved` | All gates passed, ready to apply | Human approver |
| `rejected` | Will not be applied, reason recorded | Human approver or reviewer |
| `implemented` | Canonical files updated, index rebuilt | Implementer (human or agent) |

---

## Human Approval Rules

### High-Risk Changes (Full Path Required)

The following changes **must** use the full lifecycle:

- Changes to mapped fields (any `FieldEndpoint` with an active `Mapping`).
- Changes to `ValueList` or `ValueMapping`.
- Ownership or stewardship changes.
- Changes to active objects with >2 relationships.
- Impact depth >1 hop.
- Changes to `ValidationRule` or `BusinessRule`.

### Low-Risk Changes (Lightweight Path Allowed)

Small changes may skip the full lifecycle if **all** of these are true:

- Affects fewer than 5 objects.
- No active objects with downstream mappings.
- No ownership changes.
- No validation rule or value list changes.
- Validation passes with zero errors.

Lightweight path:

```
draft → approved → applied → closed
```

### Approval Controls

| Control | Enforcement |
|---|---|
| No direct canonical file mutation from chat or inference | CLI `apply` only accepts `PatchProposal` or `ChangeRequest` |
| Every change must have a `ChangeRequest` | Audit events reference a CR ID |
| High-risk changes require explicit approval | Risk rules computed before apply |
| Invalid proposals cannot be applied | Post-apply validation fails → rollback |
| All states are reversible until `applied` | Rejected CRs stay in repo for audit |

---

## Audit Trail Expectations

Every workflow action generates an `AuditEvent` in `generated/audit_events.jsonl`:

| Event Type | When | Data Captured |
|---|---|---|
| `change_request_created` | CR submitted | requester, affected_objects, reason |
| `patch_proposal_created` | PP created | created_by, source_evidence, ops count |
| `patch_proposal_validated` | PP checked | validation_status, error_count, warning_count |
| `change_request_approved` | CR approved | approver, approval_timestamp |
| `change_request_rejected` | CR rejected | rejecter, rejection_reason |
| `change_applied` | Files updated | changed_files, old_hash, new_hash |
| `index_rebuilt` | Index refreshed | object_count, relationship_count |
| `issue_resolved` | Issue closed | resolution, linked_cr |

Audit events are **append-only**. They are never modified or deleted.

---

## Example Workflow: SAP Business Partner Migration Issue

### Scenario

During S/4HANA Business Partner migration testing, the team discovers that **Customer Group value `A17` for sales organization `CH01` is unmapped**. The legacy system sends `A17`, but the target S/4 value list does not include it. This blocks cutover readiness.

### Step-by-Step Workflow

**Step 1: Capture source evidence**

A functional consultant receives an email from the business team:

> "Customer Group 7 missing for CH01 / A17 Footlocker in RS4."

The consultant creates an `Evidence` object:

```yaml
---
id: EV-EMAIL-20260426-CH01-A17
type: Evidence
domain: DOMAIN-CUSTOMER-BP
evidence_type: email_summary
source_system: Outlook
source_date: 2026-04-26
related_objects:
  - ATTR-CUST-SALES-CUSTOMER-GROUP
  - ISS-CH01-A17-CONFIG-GAP
status: active
---

# Evidence: CH01 / A17 Customer Group Gap

Source email indicates that Customer Group handling for CH01 / A17 differs from current model assumption.
```

**Step 2: AI proposes a patch**

The consultant runs:

```bash
modelops propose-patch --from ./email-note.md --repo ./my-model
```

The AI provider (or `NoProviderAdapter`) creates a `PatchProposal`:

```yaml
---
id: PP-001
type: PatchProposal
domain: DOMAIN-CUSTOMER-BP
status: pending_review
created_by: ai
created_at: 2026-04-26
source_evidence:
  - EV-EMAIL-20260426-CH01-A17
affected_objects:
  - ATTR-CUST-SALES-CUSTOMER-GROUP
  - VMAP-LEGACY-CUST-GROUP-TO-S4-KDGRP
  - VAL-CUST-GROUP-ALLOWED-VALUES
proposed_change_request: CR-001
validation_status: pending
---

# Patch Proposal: Customer Group handling for CH01 / A17

## Proposed changes

1. Update `VMAP-LEGACY-CUST-GROUP-TO-S4-KDGRP` — add mapping entry for source value `A17`.
2. Update `VAL-CUST-GROUP-ALLOWED-VALUES` — re-run allowed value validation after confirming target value list.
3. Create or update `ISS-CH01-A17-CONFIG-GAP` — link to affected objects.

## Required human checks

- Confirm target S/4 customizing in RS4.
- Confirm owner approval.
- Confirm whether special handling applies only to CH01 or other sales orgs.
```

**Step 3: Deterministic validation**

The consultant runs:

```bash
modelops proposal validate PP-001 --repo ./my-model
```

The validator checks:
- `VMAP-LEGACY-CUST-GROUP-TO-S4-KDGRP` exists.
- `VAL-CUST-GROUP-ALLOWED-VALUES` exists.
- Proposed mapping entry does not violate `ValueList` constraints.
- No `REFERENCE_BROKEN` errors.

Result: `validation_status: valid` (with warnings: target value not yet confirmed).

**Step 4: Impact review**

The consultant runs:

```bash
modelops proposal impact PP-001 --repo ./my-model
```

Impact report shows:
- Directly affected: `ATTR-CUST-SALES-CUSTOMER-GROUP`, `FEP-S4-KNVV-KDGRP`, `VMAP-LEGACY-CUST-GROUP-TO-S4-KDGRP`
- Downstream: `VAL-CUST-GROUP-ALLOWED-VALUES`, `DS-CUST-SALES-AREA-LOAD`
- Owners to notify: `PERSON-SALES-MD-OWNER`, `PERSON-CUSTOMER-BP-STEWARD`
- Open issues: `ISS-CH01-A17-CONFIG-GAP`

**Step 5: Human review**

The data steward reviews the proposal:
- Reads source evidence.
- Confirms that `A17` is indeed a valid legacy value.
- Checks S/4 customizing in RS4 and finds that target value should be `01`.
- Approves the proposal.

**Step 6: Create ChangeRequest**

The steward creates:

```bash
modelops change-request create --id CR-001 --title "Update Customer Group handling for CH01 / A17" \
  --affected-object ATTR-CUST-SALES-CUSTOMER-GROUP \
  --affected-object VMAP-LEGACY-CUST-GROUP-TO-S4-KDGRP \
  --repo ./my-model
```

```yaml
---
id: CR-001
type: ChangeRequest
domain: DOMAIN-CUSTOMER-BP
title: Update Customer Group handling for CH01 / A17
status: pending
affected_objects:
  - ATTR-CUST-SALES-CUSTOMER-GROUP
  - FEP-S4-KNVV-KDGRP
  - VMAP-LEGACY-CUST-GROUP-TO-S4-KDGRP
related_issues:
  - ISS-CH01-A17-CONFIG-GAP
related_decisions:
  - DEC-CH01-A17-CUSTOMER-GROUP
approved_by:
  - ROLE-CUSTOMER-BP-STEWARD
---
```

**Step 7: Approval**

The business owner approves:

```bash
modelops change-request approve CR-001 --approver PERSON-SALES-MD-OWNER --repo ./my-model
```

Status: `approved`.

**Step 8: Apply**

The model maintainer applies:

```bash
modelops proposal apply PP-001 --repo ./my-model --apply
```

> **Note:** `proposal apply` defaults to dry-run. Pass `--apply` to actually mutate canonical files.

The system:
1. Re-validates patch against current repository state.
2. Applies changes to canonical files.
3. Updates `PatchProposal` status to `accepted`.
4. Creates `AuditEvent`.

**Step 9: Index rebuild**

```bash
modelops build-index --repo ./my-model --jsonl
```

SQLite index, lineage edges, and search documents are regenerated.

**Step 10: Post-apply validation**

```bash
modelops validate --repo ./my-model
```

Validation passes with zero errors. The `Issue` status is updated to `resolved`.

**Step 11: Report generation**

```bash
modelops health --repo ./my-model
modelops scorecard --repo ./my-model
```

Health report shows improved coverage. Scorecard reflects resolved gap.

---

## Responsibility Matrix

| Activity | Data Owner | Data Steward | SAP Functional Consultant | Migration Lead | Data Quality Analyst | AI Assistant | Validator | Approver |
|---|---|---|---|---|---|---|---|---|
| Validate model | ✓ | ✓ Lead | | | ✓ | | ✓ System | |
| Build index | | ✓ | | ✓ Lead | | | | |
| Define attribute | ✓ Input | ✓ Lead | | | | | | |
| Define field endpoint | | | ✓ Lead | | | | | |
| Create mapping | ✓ | ✓ | ✓ | ✓ Lead | | | | |
| Propose change | ✓ | ✓ | ✓ | ✓ | | ✓ Lead | | |
| Review proposal | ✓ | ✓ | ✓ | ✓ | ✓ | | | ✓ Lead |
| Create ChangeRequest | ✓ | ✓ | ✓ | ✓ | | | | |
| Approve ChangeRequest | ✓ Lead | | | | | | | ✓ Lead |
| Apply proposal | | | | | | | | ✓ Lead |
| Export workbook | | ✓ | | ✓ | | | | |
| Run impact analysis | | | ✓ Lead | ✓ | | | | ✓ |
| Run gap detection | | | | ✓ Lead | ✓ | | | |
| Supervise AI | | | | | | ✓ Lead | | |

---

## Anti-Patterns

| Anti-Pattern | Why It Fails | Correct Approach |
|---|---|---|
| One person creates and approves their own ChangeRequest | No governance; mistakes propagate | Separate proposer and approver roles |
| Editing `generated/` files directly | Lost on next `build-index` | Edit `model/` only; regenerate index |
| Storing the only copy of truth in Martenweave | Martenweave documents truth; systems own data | Use Martenweave as knowledge layer, not data store |
| Expecting real-time collaboration | Martenweave is async/Git-based | Use short PR cycles and frequent validation |
| Giving every user full repo access | Accidental mutation | File-system permissions or Git branch protection |
| Skipping validation before apply | Broken references, SAP context errors | Always run `modelops validate` before and after apply |

---

## Related Documents

- `docs/governance/DAMA_ALIGNMENT.md` — DAMA-DMBOK alignment overview
- `docs/governance/DATA_QUALITY_AND_METADATA_MODEL.md` — Data quality and metadata treatment
- `docs/governance/AI_READY_DATA_MODEL_LAYER.md` — AI-ready model layer design
- `docs/change-workflow.md` — Change request workflow design
- `docs/team-collaboration-model.md` — Roles, workflows, and collaboration patterns
- `docs/canonical-status-lifecycle.md` — Status meanings by object kind
- `docs/validation-methodology-warnings.md` — Validation warning codes and fixes
