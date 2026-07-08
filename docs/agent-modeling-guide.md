# Agent Modeling Guide

Version: 0.4.1
Status: Draft  
Scope: Rules for AI agents creating and updating Martenweave canonical models  
Audience: Codex, Kimi, and LLM agents working in Martenweave repositories  

---

## 1. Non-negotiable rules

| # | Rule | Violation consequence |
|---|---|---|
| 1 | **Never mutate canonical files directly from chat, inference, or file scan.** | Produces untraceable changes that bypass validation and approval. |
| 2 | **Always produce a `PatchProposal` first.** | PatchProposal is the only path from AI output to canonical change. |
| 3 | **Record every assumption in the PatchProposal `assumptions` field or as a `Decision` object.** | Silent assumptions become invisible technical debt. |
| 4 | **Preserve existing IDs.** Never rename or re-ID an object to "improve" naming. | Breaks references, lineage, and external links. |
| 5 | **Run `martenweave validate` after every proposed change in your reasoning.** | Unvalidated proposals waste human review time. |

---

## 2. Simple mode vs enterprise mode: agent decision tree

```text
Is the source a single file or table with <10 fields?
  └── YES -> Simple mode (Domain → Entity → Attribute → FieldEndpoint)
      
Does the object exist in multiple systems, contexts, or perspectives?
  └── YES -> Enterprise mode (full stack with EntityContext, AttributeUsage)
      
Is there source-to-target mapping, governance, or approval required?
  └── YES -> Enterprise mode
      
Otherwise -> Simple mode is acceptable; enterprise mode is optional enrichment.
```

### Mode summary

| Aspect | Simple mode | Enterprise mode |
|---|---|---|
| Object count | <15 objects typical | 30+ objects typical |
| Context layer | None | `EntityContext` per grain |
| Attribute link | Direct `Attribute` → `FieldEndpoint` | `AttributeUsage` bridges context |
| Mapping | None | `Mapping` + `ValueMapping` |
| Governance | Optional ownership | Required ownership + `ChangeRequest` |
| When to choose | Quick file-to-model | SAP, multi-system, governed MDM |

---

## 3. Object inference rules

### 3.1 Domain (`MasterDataDomain`)
- **Always create first.** Every model needs at least one domain.
- Infer from the business area: Customer, Product, Supplier, Employee, Finance.
- ID prefix: `DOMAIN-`

### 3.2 Business object (`BusinessEntity`)
- In simple mode: the concrete thing being modeled (Product, Order Line).
- In enterprise mode: the top-level conceptual object (Business Partner, Customer).
- Use `parent_entity` only for Perspectives/Contexts under a BusinessObject.
- ID prefix: `ENTITY-` or `BO-`

### 3.3 Perspective / Context (`EntityContext`)
- Create when a BusinessObject has multiple system-specific grains.
- Example grains: SAP sales area, company code, partner function, central data.
- ID prefix: `CTX-`

### 3.4 Attribute (`Attribute`)
- Represents **business meaning**, not the physical field.
- One Attribute can link to many FieldEndpoints across systems.
- If a column name is cryptic (`KDGRP`), the Attribute name is descriptive (`Customer Group`).
- ID prefix: `ATTR-`

### 3.5 AttributeUsage (`AttributeUsage`)
- Create when the same Attribute behaves differently in different contexts.
- Links `Attribute` + `EntityContext` + `FieldEndpoint`.
- ID prefix: `USE-`

### 3.6 FieldEndpoint (`FieldEndpoint`)
- Physical representation: table column, file column, API field.
- Must link to an `Attribute` or `business_attribute` (or be covered by an `AttributeUsage`).
- `endpoint_type` values: `sap_table_field`, `file_column`, `api_property`, `database_column`.
- ID prefix: `FEP-`

### 3.7 Mapping (`Mapping`)
- Source-to-target link between two `FieldEndpoint`s.
- Create only when data moves between systems or transforms.
- ID prefix: `MAP-`

### 3.8 ValueList (`ValueList`)
- Closed set of allowed values for a field.
- Create when the source or target has a known enumeration.
- ID prefix: `VLIST-`

### 3.9 ValidationRule (`ValidationRule`)
- Constraint, quality check, or business rule.
- Link to the `Attribute` it governs.
- ID prefix: `VAL-`

### 3.10 Ownership and governance
- Add `business_owner`, `technical_owner`, or `data_steward` to active objects.
- Use `Issue` for gaps and `Decision` for accepted trade-offs.
- ID prefixes: `ISS-`, `DEC-`

### 3.11 ChangeRequest (`ChangeRequest`)
- Created by humans after approving a PatchProposal.
- Agents create `PatchProposal`; humans create `ChangeRequest`.
- ID prefix: `CR-`

---

## 4. Proposal-first editing protocol

```text
Agent receives input (chat, file, note, gap report)
  -> Analyze input against existing model (read canonical files)
  -> Build PatchProposal with:
       - title, description
       - affected_objects
       - proposed_operations (create, update, none)
       - assumptions
       - human_checks_needed
  -> Run martenweave validate --repo <repo> (dry-run mental or actual)
  -> Present PatchProposal to human
  -> Human approves -> ChangeRequest created -> canonical files updated
  -> Human rejects -> PatchProposal marked rejected, rationale recorded
```

### PatchProposal required fields

| Field | Agent responsibility |
|---|---|
| `title` | One-line summary of the change. |
| `description` | What changed and why. |
| `affected_objects` | List of existing IDs that are touched. |
| `proposed_operations` | Structured ops with object type, ID, and field changes. |
| `assumptions` | Every inference the agent made that a human should verify. |
| `human_checks_needed` | Explicit questions for the reviewer. |
| `source_evidence` | File path, note text, or ticket reference that triggered this. |

---

## 5. Good vs bad model proposals

### Good proposal: adding a new SAP field

```yaml
---
id: PP-2026-05-24-001
type: PatchProposal
status: draft
title: Add KNVV.KDGRP field to Customer Sales Area model
affected_objects:
  - ENTITY-CUSTOMER-SALES-AREA
  - CTX-CUSTOMER-SALES-AREA-S4
assumptions:
  - "KNVV.KDGRP is the authoritative S/4 field for Customer Group."
  - "Legacy system uses a different code set; mapping will be added separately."
human_checks_needed:
  - "Confirm KNVV is the correct table for sales-area customer group."
  - "Verify if a ValueList for customer groups already exists in another context."
source_evidence: "SAP migration workshop notes, page 4"
---
```

**Why it is good:**
- Links to existing objects.
- Records assumptions explicitly.
- Asks specific verification questions.
- Does not silently create files.

### Bad proposal: flat field catalog

```yaml
---
id: BAD-001
type: PatchProposal
status: draft
title: Add all customer fields
---
```

**Why it is bad:**
- No affected objects listed.
- No separation of Attribute vs FieldEndpoint.
- No assumptions or human checks.
- Likely to produce 50+ orphaned FieldEndpoints without Attributes.

---

## 6. Validation checkpoints for agents

Before presenting any PatchProposal, verify:

1. **No duplicate IDs.** Search the model directory for the proposed ID prefix.
2. **No broken references.** Every `attribute`, `domain`, `entity_context`, `value_list` points to an existing or concurrently proposed object.
3. **No orphaned FieldEndpoints.** Every active FieldEndpoint has an Attribute, business_attribute, or AttributeUsage.
4. **IDs match format.** `^[A-Z][A-Z0-9]*(-[A-Z0-9]+)*$`
5. **Simple mode is intentional.** If skipping EntityContext and AttributeUsage, confirm the model has <10 fields and one context.

---

## 7. File creation order

When building a new model from scratch, create objects in this order to avoid broken references:

```text
1. MasterDataDomain
2. BusinessEntity (top level)
3. EntityContext (if enterprise mode)
4. Attribute
5. FieldEndpoint
6. AttributeUsage (if enterprise mode)
7. ValueList
8. Mapping / ValueMapping
9. ValidationRule
10. Issue / Decision (for assumptions)
11. PatchProposal (summarizing the agent's work)
```

---

## 7.5 ProductOwner agentic loop

The `ProductOwnerAgent` (`modelops agent product-owner`) consumes raw product inputs and runs a validation-driven loop to produce human-reviewable `PatchProposal` objects.

### Supported inputs

| Source | Example | Handling |
|---|---|---|
| Note | `note.md` with free text | Passed directly to the proposal generator |
| Issue | GitHub issue Markdown | Frontmatter stripped; body used as evidence |
| ChangeRequest | Existing `CR-*.md` file | `reason`, `requested_change`, and `expected_impact` synthesize the note |

### Loop steps

1. **Normalize** input into a note and extract candidate object IDs.
2. **Generate** an initial `PatchProposal` using the configured AI adapter.
3. **Validate** the proposal deterministically (ID format, object existence, allowed operations).
4. **Refine** if validation fails: append errors to the note and regenerate (up to `--max-iterations`).
5. **Impact analysis**: compute affected objects from the SQLite index.
6. **Write** the validated proposal to `model/patch-proposals/`.
7. **Create ChangeRequest** when the proposal is high-risk, originated from a ChangeRequest, or failed final validation.
8. **Draft issue** and emit notification events for owners/approvers.

### CLI usage

```bash
modelops agent product-owner --from note.md --repo ./my-model --dry-run
modelops agent product-owner --from issue.md --repo ./my-model --source-type issue
modelops agent product-owner --from CR-0001 --repo ./my-model --source-type change_request
```

The agent never edits canonical model objects directly. All changes flow through `PatchProposal` and, when approved, `ChangeRequest`.

### ProductOwner agent vs Readiness agent

| Agent | Input | Output | Use when |
|---|---|---|---|
| `product-owner` | Note, issue, ChangeRequest | PatchProposal, ChangeRequest, issue draft | A human has a concrete change request |
| `readiness` | Repository state | Issue files, issue draft, notifications | You want to know if the repo is pilot-ready |

---

## 7.6 Readiness agentic loop

The `ReadinessAgent` (`modelops agent readiness`) runs deterministic trust gates against a repository and creates `Issue` objects for every blocker.

### Supported gates

| Gate | Trigger | Severity |
|---|---|---|
| `validation_errors` | Any validation `ERROR` | high |
| `stale_index` | Generated index is older than canonical files | medium |
| `scorecard_zero_coverage_pass` | A coverage metric is `0.0` but marked `pass` | high |
| `scorecard_untitled_repository` | Config has a name but scorecard shows "Untitled Repository" | medium |
| `invalid_open_proposal` | Open PatchProposal has `validation_status: invalid` | high |
| `high_risk_unapproved_proposal` | Open high-risk proposal lacks approved ChangeRequest | high |
| `active_object_missing_owner` | Active object has no ownership field | medium |

### CLI usage

```bash
modelops agent readiness --repo ./my-model --profile pilot
modelops agent readiness --repo ./my-model --profile demo --dry-run
modelops agent readiness --repo ./my-model --profile release --json
```

### Output

- Readiness report (human table or JSON).
- One `Issue` canonical file per blocker in `model/issues/`.
- A GitHub issue draft in `generated/issues/`.
- Notification events for affected owners.

The agent does not auto-apply fixes. It makes blockers trackable so the team can resolve them through the normal PatchProposal/ChangeRequest workflow.

---

## 8. Agent anti-patterns to avoid

| Anti-pattern | Why it hurts | Correct approach |
|---|---|---|
| One object per CSV column with no Attribute layer | Flat, untraceable catalog | Create Attribute for meaning, FieldEndpoint for physical |
| Guessing SAP table/field without evidence | Wrong physical mapping | Ask human or create Issue for uncertain fields |
| Reusing the same Attribute for unrelated concepts | Semantic collision | Create separate Attributes with clear names |
| Direct file creation without PatchProposal | Bypasses approval | Always emit PatchProposal first |
| Deleting objects to "clean up" | Breaks references and history | Archive status + ChangeRequest |
| Hard-coding system names in Attribute names | Not reusable | System names go in EntityContext or FieldEndpoint |
