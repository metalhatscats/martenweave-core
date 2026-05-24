# ModelOps for MDM — AI Patch Workflow

Version: `0.2-draft`  
Document type: AI workflow / patch governance specification  
Scope: AI-assisted model update workflow for SAP migration, MDM, data governance, and AMS model knowledge  
Initial product focus: SAP Business Partner migration model, Customer role slice first  
Repository style: File-based canonical model repository with human-approved AI patch proposals

---

## 1. Purpose

This document defines the AI-assisted patch workflow for **ModelOps for MDM**.

## MVP AI Boundary

P0 AI support is limited to the reviewed patch loop:

```text
pasted project note
  -> Evidence summary
  -> bounded context bundle
  -> structured PatchProposal
  -> deterministic validation
  -> diff preview
  -> human approve/reject
  -> ChangeRequest
  -> canonical file update after approval only
  -> generated index rebuild
```

Do not build autonomous agents, broad chat mode, direct canonical writes, raw dataset sharing with external AI providers, or multi-agent orchestration in MVP.

The goal is to let AI help users transform scattered SAP migration and MDM knowledge into structured model updates while preserving control, traceability, validation, and human approval.

AI may help with:

- extracting model-relevant facts from notes, emails, tickets, and workshop summaries;
- identifying affected attributes, field endpoints, mappings, value mappings, rules, validations, owners, issues, and decisions;
- proposing structured model updates;
- creating issue drafts;
- creating decision drafts;
- creating change request drafts;
- explaining impact;
- generating validation checklists;
- generating AMS handover summaries.

AI must not silently change approved model files.

The workflow must protect the repository from unreviewed, unvalidated, or hallucinated changes.

---

## 2. Core rule

```text
AI proposes.
Validators check.
Humans approve.
Canonical files change only after approval.
Git records the technical diff.
ChangeRequest records the business meaning.
```

This is the central safety and trust model.

---

## 3. Product principle

The AI patch workflow is not a chatbot feature.

It is a controlled model change workflow.

The product should not simply let users ask:

```text
"Update the model."
```

The product should guide the flow:

```text
Source note / ticket / email
  → AI extraction
  → structured PatchProposal
  → deterministic validation
  → diff preview
  → human review
  → ChangeRequest
  → approved canonical update
  → index rebuild
  → impact/health report update
```

---

## 4. Non-negotiable AI rules

1. AI must not directly modify approved canonical model files.

2. AI must create or update `PatchProposal` objects first.

3. PatchProposal must be validated before approval.

4. Patch approval must be a user action.

5. Approved changes must create or update a `ChangeRequest`.

6. Every AI-proposed change must have source evidence or user-provided source text.

7. AI-generated relationships should remain `ai_suggested` until approved.

8. AI must not invent SAP technical facts without evidence.

9. AI must not mark a validation as passed unless deterministic validation or explicit user evidence supports it.

10. AI must not silently delete approved objects.

11. AI must not send raw client datasets to external AI providers by default.

12. AI must operate from bounded context bundles, not uncontrolled repository dumps.

---

## 5. AI workflow positioning

AI sits between unstructured project knowledge and structured model repository.

Inputs:

```text
email
ticket
workshop note
chat message
Confluence excerpt
Jira issue
SAP validation error summary
dataset gap report
mapping workbook comment
AMS incident note
```

AI output:

```text
PatchProposal
Issue draft
Decision draft
ChangeRequest draft
Evidence summary
Impact explanation
Validation checklist
AMS handover summary
```

AI should not be the final authority.

---

## 6. Patch workflow overview

```text
1. Capture source material.
2. Normalize source material into Evidence.
3. Build AI context bundle.
4. Ask AI to extract model-relevant facts.
5. Ask AI to propose structured changes.
6. Parse AI output.
7. Validate proposed changes.
8. Create PatchProposal file.
9. Show patch review UI.
10. User approves, rejects, or requests revision.
11. On approval:
    - apply canonical file changes;
    - create/update ChangeRequest;
    - update object change history where applicable;
    - write audit event;
    - rebuild generated index;
    - show post-approval impact/health result.
```

---

## 7. Key objects

The AI patch workflow uses these object types.

```text
Evidence
PatchProposal
ChangeRequest
Issue
Decision
Attribute
AttributeUsage
FieldEndpoint
Mapping
ValueList
ValueMapping
TransformationLogic
ValidationRule
DataQualityCheck
Owner / OwnershipRole
Risk
```

### 7.1 Evidence

Evidence captures source material or a safe summary.

Example:

```yaml
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
```

### 7.2 PatchProposal

PatchProposal captures AI- or user-proposed model changes.

Example:

```yaml
id: PATCH-0021
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
proposed_change_request: CR-0021
validation_status: pending
```

### 7.3 ChangeRequest

ChangeRequest records the approved business/model change.

Example:

```yaml
id: CR-0021
type: ChangeRequest
domain: DOMAIN-CUSTOMER-BP
title: Update Customer Group handling for CH01 / A17
status: approved
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
```

---

## 8. PatchProposal file structure

A PatchProposal should be stored as Markdown with YAML frontmatter.

Recommended path:

```text
model/patch-proposals/PATCH-0021-CUSTOMER-GROUP-CH01-A17.md
```

Recommended structure:

```markdown
---
id: PATCH-0021
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
proposed_change_request: CR-0021
validation_status: pending
---

# Patch Proposal: Customer Group handling for CH01 / A17

## Source summary

The source note indicates that Customer Group handling for CH01 / A17 differs from the current model assumption.

## Proposed changes

### 1. Update value mapping

Object: `VMAP-LEGACY-CUST-GROUP-TO-S4-KDGRP`

Proposed change:
- Add or update mapping entry for source value `A17`.
- Mark status as `proposed` until steward approval.

### 2. Update validation coverage

Object: `VAL-CUST-GROUP-ALLOWED-VALUES`

Proposed change:
- Re-run allowed value validation after confirming target value list.

### 3. Create or update issue

Object: `ISS-CH01-A17-CONFIG-GAP`

Proposed change:
- Link issue to Customer Group attribute, KNVV-KDGRP endpoint, and value mapping.

## Required human checks

- Confirm target S/4 customizing.
- Confirm owner approval.
- Confirm whether special handling applies only to CH01 or other sales orgs.

## Validation result

Pending.
```

---

## 9. AI task types

MVP should support a small set of controlled AI task types.

```text
explain_attribute
explain_lineage
summarize_impact
propose_patch_from_note
create_issue_from_gap
create_decision_draft
create_change_request_draft
generate_validation_checklist
generate_ams_handover_summary
compare_model_versions
```

Do not start with broad “agent can do anything” mode.

Each task type should have:

```text
input contract
context bundle contract
allowed output actions
validation rules
UI review pattern
```

---

## 10. AI task: propose patch from note

### 10.1 Purpose

Convert unstructured text into a structured PatchProposal.

Input examples:

```text
email
ticket comment
workshop note
Teams message
Confluence excerpt
SAP validation note
```

### 10.2 Flow

```text
1. User pastes note.
2. System creates Evidence summary or temporary source object.
3. Search retrieves relevant model objects.
4. AI receives bounded context bundle.
5. AI outputs structured patch proposal.
6. System validates output.
7. PatchProposal is created.
8. User reviews patch.
```

### 10.3 Allowed actions

```text
create_issue
create_decision_draft
create_change_request_draft
update_attribute_draft
update_attribute_usage_draft
update_field_endpoint_draft
update_mapping_draft
update_value_mapping_draft
update_validation_rule_draft
create_evidence_summary
request_human_clarification
```

### 10.4 Disallowed actions

```text
approve_change
delete_approved_object
modify_active_model_directly
mark_validation_passed
write_generated_index
send_raw_dataset_to_ai
```

---

## 11. AI task: create issue from gap

### 11.1 Purpose

Turn deterministic gap detection into a clear issue draft.

Input:

```text
GapReport
affected objects
validation result
dataset profile summary
```

Output:

```text
Issue draft
affected object links
suggested owner
severity proposal
recommended actions
```

Example issue:

```yaml
id: ISS-UNMAPPED-A17-CUSTOMER-GROUP
type: Issue
domain: DOMAIN-CUSTOMER-BP
title: Unmapped Customer Group source value A17
status: open
severity: medium
issue_type: value_mapping_gap
affected_objects:
  - ATTR-CUST-SALES-CUSTOMER-GROUP
  - VMAP-LEGACY-CUST-GROUP-TO-S4-KDGRP
  - DATASET-CUSTOMER-SALES-AREA-LOAD
```

AI may suggest severity, but user or deterministic rules should confirm it.

---

## 12. AI task: summarize impact

### 12.1 Purpose

Explain deterministic impact analysis in business-readable language.

Input:

```text
ImpactReport
relationship edges
affected objects
owners
issues
decisions
datasets
validations
```

Output:

```text
plain-language summary
affected areas
recommended next actions
handover notes
```

Important rule:

```text
AI summarizes deterministic impact.
AI must not invent additional affected objects.
```

If AI believes something may be affected but is not in the deterministic graph, it must mark it as a hypothesis.

---

## 13. AI task: generate validation checklist

### 13.1 Purpose

Generate checklist for a changed attribute, mapping, or value list.

Input:

```text
Attribute
FieldEndpoint
Mapping
ValueMapping
ValidationRule
Dataset profile
ImpactReport
```

Output:

```text
checklist items
owner suggestions
validation scope
go/no-go concerns
```

Example:

```text
- Confirm target value exists in S/4 value list.
- Re-run allowed values check.
- Re-run unmapped source values check.
- Confirm affected sales organizations.
- Confirm owner approval.
- Update AMS handover note.
```

---

## 14. AI task: generate AMS handover summary

### 14.1 Purpose

Generate support-ready summary for AMS after migration.

Input:

```text
Attribute
Lineage
Mapping
ValidationRule
Open/closed issues
Decisions
Known exceptions
Owners
```

Output:

```text
support explanation
known risks
diagnostic steps
owner map
related decisions
validation references
```

AI must distinguish:

```text
approved model facts
open issues
assumptions
recommendations
```

---

## 15. AI context bundle

AI must receive a bounded context bundle.

Do not send the whole repository.

### 15.1 Context bundle structure

```json
{
  "task": "propose_patch_from_note",
  "source": {
    "evidence_id": "EV-EMAIL-20260426-CH01-A17",
    "source_text_summary": "...",
    "raw_text_included": false
  },
  "primary_objects": [],
  "related_objects": [],
  "lineage": [],
  "open_issues": [],
  "recent_decisions": [],
  "validation_results": [],
  "dataset_profile_summary": [],
  "allowed_actions": [],
  "disallowed_actions": [],
  "output_schema": "PatchProposalOutputV1"
}
```

### 15.2 Context bundle content

For patch proposal tasks, include:

```text
source evidence summary
top matching attributes
top matching field endpoints
relevant mappings
relevant value lists
relevant value mappings
relevant validation rules
open related issues
recent decisions
owners/stewards
repository health warnings for affected objects
```

### 15.3 Context limits

Recommended MVP limits:

```text
max primary objects: 10
max related objects: 50
max source text length: configurable
max validation results: 50
max open issues: 20
```

If context exceeds limit, the system should summarize or ask user to narrow scope.

---

## 16. Context retrieval strategy

Use structured retrieval first, semantic retrieval second.

Recommended order:

```text
1. Exact ID match.
2. SAP technical name match.
3. Attribute name match.
4. Dataset column match.
5. Mapping/value mapping match.
6. Open issue/decision match.
7. Keyword search.
8. Semantic search if enabled.
```

Example user note:

```text
Customer Group 7 missing for CH01 / A17 Footlocker in RS4.
```

Retrieval should search:

```text
Customer Group
CH01
A17
Footlocker
KNVV
KDGRP
sales area
RS4
value mapping
configuration gap
```

The context bundle should prefer objects with explicit SAP/attribute relationships.

---

## 17. AI output contract

AI output should be structured and schema-validated.

### 17.1 Patch proposal output schema

Example:

```json
{
  "proposal_type": "model_patch",
  "confidence": "medium",
  "summary": "Customer Group handling for CH01 / A17 may require mapping and validation update.",
  "affected_objects": [
    "ATTR-CUST-SALES-CUSTOMER-GROUP",
    "FEP-S4-KNVV-KDGRP"
  ],
  "proposed_changes": [
    {
      "action": "update_value_mapping_draft",
      "object_id": "VMAP-LEGACY-CUST-GROUP-TO-S4-KDGRP",
      "change_summary": "Add or review source value A17 mapping for CH01.",
      "fields": {
        "mappings": [
          {
            "source_value": "A17",
            "target_value": null,
            "status": "proposed",
            "condition": "sales_org == CH01"
          }
        ]
      }
    }
  ],
  "new_objects": [
    {
      "type": "Issue",
      "id": "ISS-CH01-A17-CUSTOMER-GROUP-GAP",
      "title": "Customer Group handling gap for CH01 / A17",
      "status": "open"
    }
  ],
  "questions": [
    "What is the approved target Customer Group value for A17 in CH01?"
  ],
  "required_human_checks": [
    "Confirm target S/4 customizing in RS4.",
    "Confirm whether this applies only to CH01."
  ],
  "assumptions": [
    "A17 refers to source customer group or customer classification from the source note."
  ]
}
```

### 17.2 Required output fields

```text
proposal_type
confidence
summary
affected_objects
proposed_changes
questions
required_human_checks
assumptions
```

### 17.3 Confidence values

```text
low
medium
high
```

Low-confidence patches should require explicit review and should not pre-fill active changes aggressively.

---

## 18. Allowed patch actions

MVP allowed patch actions:

```text
create_issue
create_decision_draft
create_change_request_draft
create_evidence_summary
update_attribute_draft
update_attribute_usage_draft
update_field_endpoint_draft
update_mapping_draft
update_value_mapping_draft
update_validation_rule_draft
update_transformation_logic_draft
link_existing_objects
request_human_clarification
```

Later allowed actions:

```text
create_risk
create_data_quality_check_draft
create_ams_handover_note
create_report
create_git_branch
prepare_pull_request
```

Never allow AI action:

```text
approve_change
delete_approved_object
change_status_to_approved
modify_generated_index_as_source
mark_validation_passed_without_run
send_data_to_external_system_without user action
```

---

## 19. Patch validation

PatchProposal must pass validation before approval.

### 19.1 Validation categories

```text
AI output schema validation
allowed action validation
object ID validation
object type validation
reference validation
SAP context validation
mapping/value-list validation
lifecycle validation
governance validation
security/privacy validation
diff conflict validation
```

### 19.2 Blocking errors

Patch approval must be blocked if:

```text
AI output is invalid.
Patch references missing objects.
Patch creates duplicate IDs.
Patch violates SAP context rules.
Patch maps value to target value missing from ValueList.
Patch updates approved object without ChangeRequest.
Patch attempts direct file write outside patch workflow.
Patch has no source evidence or user-provided source text.
Patch conflicts with uncommitted file changes.
Patch tries to modify generated files as canonical source.
```

### 19.3 Warnings

Patch may be reviewable with warnings:

```text
owner missing
validation missing
target value not yet confirmed
source evidence is summary only
low AI confidence
ambiguous object match
requires human clarification
```

---

## 20. Patch review UI

Patch review screen should show information in this order.

```text
1. Patch identity and status
2. Source evidence / source note
3. AI summary
4. Confidence and assumptions
5. Affected objects
6. Proposed object changes
7. New objects to create
8. Required human checks
9. Deterministic validation result
10. File diff preview
11. Related impact preview
12. Approval controls
```

Approval controls:

```text
Approve
Reject
Request revision
Split patch
Create issue only
Save as draft
```

MVP can start with:

```text
Approve
Reject
Save as draft
```

---

## 21. Diff generation

PatchService must generate a diff before approval.

Diff should show:

```text
new files
modified files
removed files
frontmatter changes
body changes
relationship changes
status changes
```

AI should not create opaque changes.

Preferred review format:

```text
object-level diff
file-level diff
business summary
validation result
```

For business users, show object-level diff first.

For technical users, show file-level Git diff.

---

## 22. Applying an approved patch

Approval flow:

```text
1. User clicks Approve.
2. System re-validates patch against current repository state.
3. System checks Git worktree if enabled.
4. System applies changes to canonical files.
5. System creates/updates ChangeRequest.
6. System updates object change_history where configured.
7. System updates PatchProposal status to accepted.
8. System writes audit event.
9. System rebuilds generated index.
10. System runs validation.
11. System shows post-approval result.
```

If validation fails after apply:

```text
rollback changes
or keep changes as applied with failed status only if explicitly configured
```

MVP recommendation:

```text
fail before apply if blocking validation errors exist
```

---

## 23. Rejecting a patch

Reject flow:

```text
1. User clicks Reject.
2. User optionally enters rejection reason.
3. PatchProposal status becomes rejected.
4. No canonical model objects are modified.
5. Audit event is written.
```

Recommended rejection reasons:

```text
incorrect_object_match
insufficient_evidence
wrong_sap_context
wrong_mapping_logic
duplicate_existing_change
out_of_scope
requires_more_information
```

---

## 24. Requesting patch revision

Revision flow:

```text
1. User adds review comments.
2. PatchProposal remains pending_review or becomes under_revision.
3. AI may generate revised proposal from comments.
4. Revised patch references previous patch.
```

Suggested fields:

```yaml
supersedes: PATCH-0021
revision_reason: Owner clarified that A17 applies only to CH01.
```

MVP can skip revision and simply create a new patch.

---

## 25. Patch splitting

Sometimes AI proposes too much.

The UI should eventually support splitting a patch.

Example:

```text
Patch contains:
- value mapping update
- validation update
- issue creation
- decision draft
```

User may approve:

```text
issue creation only
```

and reject or defer the rest.

MVP can handle this by asking user to create a revised patch.

---

## 26. Patch conflict handling

Conflicts can occur when repository files changed after patch creation.

Checks:

```text
source file hash changed
object status changed
object removed
object renamed
Git worktree dirty
related value list changed
validation rule changed
```

Conflict result:

```text
Patch requires refresh.
```

Validation code examples:

```text
PATCH_SOURCE_OBJECT_CHANGED
PATCH_TARGET_OBJECT_MISSING
PATCH_CONFLICT_WITH_UNCOMMITTED_CHANGE
PATCH_REVALIDATION_REQUIRED
```

---

## 27. AI safety and privacy

### 27.1 Data minimization

Send only necessary context.

Avoid sending:

```text
full raw datasets
personal data
credentials
confidential full emails
unrelated project files
large attachments
```

Prefer:

```text
summaries
object IDs
field names
technical names
validation result snippets
dataset profile aggregates
```

### 27.2 External provider warning

If using external AI provider, UI should show:

```text
AI provider: OpenAI / Anthropic / Azure / local / disabled
Raw source text included: yes/no
Raw dataset included: no
```

### 27.3 Sensitive evidence

Evidence should support summary/reference storage.

Example:

```yaml
evidence_type: email_summary
raw_content_stored: false
source_reference: Outlook message ID or external link
```

### 27.4 Local AI mode

Local AI may be used for:

- private draft generation;
- rough classification;
- summaries;
- less sensitive workflows.

But local model quality may be weaker. Deterministic validation remains required.

---

## 28. AI provider abstraction

The product should use provider adapters.

Recommended interface:

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
AIDIALProvider
NoAIProvider
GatewayProvider
```

### 28.1 Direct provider mode

Good for MVP.

Pros:

```text
simple
fewer moving parts
easy debugging
```

Cons:

```text
provider-specific handling
secrets per environment
less centralized governance
```

### 28.2 AI gateway mode

Later option.

Useful for:

```text
provider routing
fallbacks
budget control
central key management
audit
enterprise policy
```

Do not require gateway for MVP.

### 28.3 No-AI mode

The system must still work without AI.

No-AI mode supports:

```text
manual patch creation
deterministic validation
gap detection
lineage
impact
reports from templates
```

This matters for privacy-sensitive environments.

---

## 29. Prompt architecture

Prompts should be task-specific and versioned.

Recommended location:

```text
apps/api/src/modelops/ai/prompts/
  propose_patch_from_note.v1.md
  create_issue_from_gap.v1.md
  summarize_impact.v1.md
  generate_validation_checklist.v1.md
  generate_ams_handover_summary.v1.md
```

Prompt metadata:

```yaml
prompt_id: propose_patch_from_note.v1
task_type: propose_patch_from_note
output_schema: PatchProposalOutputV1
allowed_actions:
  - create_issue
  - update_value_mapping_draft
  - create_change_request_draft
```

Prompts must tell AI:

```text
Use only provided context.
Mark assumptions explicitly.
Do not invent SAP facts.
Return structured JSON.
Do not approve changes.
Do not request direct file writes.
```

---

## 30. Prompt skeleton: propose patch from note

```text
You are assisting with ModelOps for MDM.

Task:
Create a structured PatchProposal from the source note and provided repository context.

Rules:
- Use only the provided context.
- Do not invent SAP technical facts.
- If a fact is uncertain, place it in assumptions or questions.
- Do not approve changes.
- Do not request direct writes to canonical files.
- Propose draft changes only.
- Every affected object must use its stable ID.
- Return JSON matching PatchProposalOutputV1.

Source note:
{{source_note}}

Repository context:
{{context_bundle}}

Allowed actions:
{{allowed_actions}}

Output schema:
{{output_schema}}
```

---

## 31. Structured output parsing

AI output must be parsed and validated.

Parsing stages:

```text
raw model response
  → JSON extraction
  → schema validation
  → allowed action validation
  → reference validation
  → patch file creation
```

If parsing fails:

```text
do not create canonical changes
store failure as AI action result
show recoverable error to user
allow retry with stricter prompt
```

Validation code examples:

```text
AI_OUTPUT_NOT_JSON
AI_OUTPUT_SCHEMA_INVALID
AI_ACTION_NOT_ALLOWED
AI_REFERENCE_BROKEN
```

---

## 32. AI-generated relationship confidence

AI may suggest relationships, but they should be marked.

Example:

```yaml
suggested_relationships:
  - from: ATTR-CUST-SALES-CUSTOMER-GROUP
    relationship_type: affected_by
    to: ISS-CH01-A17-CONFIG-GAP
    confidence: ai_suggested
    reason: Source note mentions Customer Group and CH01 / A17 issue.
```

Only after approval should they become canonical explicit relationships.

---

## 33. Patch object change format

Internally, proposed changes should be represented as operations.

Recommended operation types:

```text
create_object
update_object_fields
append_list_item
remove_list_item
replace_list_item
link_objects
unlink_objects
update_status
add_markdown_section
replace_markdown_section
```

Example:

```json
{
  "operation": "append_list_item",
  "object_id": "VMAP-LEGACY-CUST-GROUP-TO-S4-KDGRP",
  "field_path": "mappings",
  "value": {
    "source_value": "A17",
    "target_value": null,
    "status": "proposed",
    "condition": "sales_org == CH01"
  }
}
```

Operations are easier to validate than free-form generated files.

---

## 34. Canonical file write strategy

PatchService should write files only after approval.

Recommended write process:

```text
1. Load current object.
2. Apply validated operations in memory.
3. Serialize updated frontmatter/body.
4. Generate diff.
5. Re-validate resulting files.
6. Write files atomically.
```

Use atomic writes where possible:

```text
write temp file
fsync if needed
rename
```

Avoid partial file updates.

---

## 35. Audit events

AI patch workflow should write audit events.

Example events:

```text
ai_patch_requested
ai_patch_generated
patch_validation_failed
patch_created
patch_approved
patch_rejected
patch_revised
patch_applied
index_rebuilt_after_patch
```

Example event:

```json
{
  "event_id": "EVT-20260426-00031",
  "timestamp": "2026-04-26T21:35:00+02:00",
  "actor": "user",
  "action": "patch_approved",
  "object_id": "PATCH-0021",
  "affected_objects": [
    "ATTR-CUST-SALES-CUSTOMER-GROUP",
    "VMAP-LEGACY-CUST-GROUP-TO-S4-KDGRP"
  ]
}
```

Audit events are generated runtime records, not the primary business history.

---

## 36. Git integration

### 36.1 MVP Git integration

Before applying patch:

```text
detect whether repository is Git repo
check worktree dirty state
show files to be changed
show diff
warn if files already modified
```

After applying patch:

```text
show changed files
suggest commit message
```

Suggested commit message:

```text
CR-0021 Update Customer Group handling for CH01 / A17

Patch: PATCH-0021

Affected:
- ATTR-CUST-SALES-CUSTOMER-GROUP
- VMAP-LEGACY-CUST-GROUP-TO-S4-KDGRP
- VAL-CUST-GROUP-ALLOWED-VALUES
```

### 36.2 Later Git integration

Later:

```text
create branch from PatchProposal
open pull request
link PR to ChangeRequest
run validation in CI
approve via PR
```

This is a strong team workflow option.

---

## 37. Patch workflow states

PatchProposal state machine:

```text
pending_review
  → accepted
  → rejected
  → superseded
```

Optional later:

```text
draft
pending_review
under_revision
accepted
rejected
superseded
applied
failed_apply
```

MVP can use simpler states.

Allowed transitions:

```text
pending_review → accepted
pending_review → rejected
pending_review → superseded
accepted → applied
accepted → failed_apply
```

Do not allow:

```text
rejected → accepted
```

Create a new revision instead.

---

## 38. ChangeRequest integration

On approval, PatchService should create or update ChangeRequest.

Rules:

```text
If PatchProposal has proposed_change_request, update it.
If not, create a new ChangeRequest draft or approved record depending flow.
Accepted patch should link to ChangeRequest.
ChangeRequest should link affected objects.
ChangeRequest should link source evidence.
```

Recommended ChangeRequest status after patch approval:

```text
approved
```

or:

```text
implemented
```

depending on whether approval and file application are separate steps.

MVP recommendation:

```text
Approve patch = implement file changes = ChangeRequest status implemented
```

For more controlled workflow:

```text
Approve patch = ChangeRequest approved
Apply patch = ChangeRequest implemented
```

Start simple.

---

## 39. Issue and decision integration

AI patch may propose:

```text
new Issue
new Decision draft
links to existing Issue
links to existing Decision
```

Rules:

```text
Issue creation can be approved separately.
Decision should remain proposed/accepted according to user action.
AI should not mark major business decisions as accepted without user approval.
```

Decision draft is useful when the note implies a design decision but evidence is incomplete.

---

## 40. Validation integration

Patch validation must call the same validators as repository validation.

Before patch approval:

```text
validate proposed object schemas
validate references
validate SAP context
validate mapping/value rules
validate governance rules
validate security/privacy rules
```

After patch approval:

```text
rebuild index
run repository validation
show new health state
```

If repository health worsens, show it clearly.

---

## 41. Lineage and impact integration

Patch review should show preliminary impact.

Example:

```text
This patch may affect:
- Attribute: Customer Group
- Endpoint: KNVV-KDGRP
- Mapping: Legacy Customer Group to S/4 KDGRP
- Value mapping: Legacy Customer Group to S/4 KDGRP
- Validation: Customer Group allowed values
- Dataset: Customer Sales Area Load File
- Owner: Customer BP Steward
```

Impact preview should be deterministic.

AI may summarize it.

---

## 42. Human review checklist

Every PatchProposal should include a review checklist.

Default checklist:

```text
Source evidence reviewed.
Affected objects are correct.
SAP context is correct.
Mapping/value mapping change is correct.
Target value exists or is explicitly unresolved.
Validation impact is understood.
Owner/steward approval is recorded if required.
Open questions are resolved or captured as issues.
ChangeRequest is linked.
```

For SAP Customer/BP:

```text
If KNVV field is affected, confirm sales-area context.
If KNB1 field is affected, confirm company-code context.
If BP role is referenced, confirm it is maintenance context, not physical storage.
If value mapping is changed, confirm target value list.
If dataset values are involved, rerun profiling/gap detection.
```

---

## 43. Example scenario: CH01 / A17 Customer Group

### 43.1 Source note

```text
Customer Group 7 in RS4 has no config for CH01 - A17 Footlocker. There is a difference between P* and R* environments. This should be handled by configuration/mapping.
```

### 43.2 Retrieval result

Relevant objects:

```text
ATTR-CUST-SALES-CUSTOMER-GROUP
FEP-S4-KNVV-KDGRP
VLIST-S4-KNVV-KDGRP
VMAP-LEGACY-CUST-GROUP-TO-S4-KDGRP
VAL-CUST-GROUP-ALLOWED-VALUES
CTX-CUSTOMER-SALES-AREA-S4
ENV-S4-RS4
```

### 43.3 AI patch proposal

AI should propose:

```text
Create/update issue for CH01 / A17 config gap.
Link issue to Customer Group attribute and KNVV-KDGRP endpoint.
Suggest review of value mapping for A17.
Suggest confirming S/4 value list/config in RS4.
Suggest rerunning allowed values validation.
Suggest ChangeRequest if mapping/validation changes are approved.
```

AI should not:

```text
invent the target customer group value;
mark the mapping as approved;
assume P* is correct without evidence;
change KNVV context to central BP;
mark validation as passed.
```

---

## 44. Example PatchProposal output

```json
{
  "proposal_type": "model_patch",
  "confidence": "medium",
  "summary": "The source note indicates a Customer Group configuration or value mapping gap for CH01 / A17 in RS4.",
  "affected_objects": [
    "ATTR-CUST-SALES-CUSTOMER-GROUP",
    "FEP-S4-KNVV-KDGRP",
    "VLIST-S4-KNVV-KDGRP",
    "VMAP-LEGACY-CUST-GROUP-TO-S4-KDGRP",
    "VAL-CUST-GROUP-ALLOWED-VALUES"
  ],
  "proposed_changes": [
    {
      "action": "create_issue",
      "object_id": "ISS-CH01-A17-CUSTOMER-GROUP-GAP",
      "change_summary": "Create issue for missing or inconsistent Customer Group configuration for CH01 / A17 in RS4.",
      "fields": {
        "title": "Customer Group config gap for CH01 / A17 in RS4",
        "severity": "medium",
        "issue_type": "configuration_gap",
        "affected_objects": [
          "ATTR-CUST-SALES-CUSTOMER-GROUP",
          "FEP-S4-KNVV-KDGRP",
          "VLIST-S4-KNVV-KDGRP",
          "VMAP-LEGACY-CUST-GROUP-TO-S4-KDGRP"
        ]
      }
    },
    {
      "action": "update_value_mapping_draft",
      "object_id": "VMAP-LEGACY-CUST-GROUP-TO-S4-KDGRP",
      "change_summary": "Add proposed unresolved mapping review item for A17 under CH01.",
      "fields": {
        "mappings": [
          {
            "source_value": "A17",
            "target_value": null,
            "condition": "sales_org == CH01",
            "status": "unresolved",
            "note": "Target value requires confirmation from RS4 configuration."
          }
        ]
      }
    }
  ],
  "questions": [
    "What is the approved target Customer Group value for A17 in CH01?",
    "Does the rule apply only to RS4 or also to production target environment?"
  ],
  "required_human_checks": [
    "Confirm RS4 target customizing.",
    "Confirm whether P* or R* environment is authoritative.",
    "Confirm owner approval from S/4 SD functional and Customer BP steward."
  ],
  "assumptions": [
    "A17 refers to a source or business customer group/classification value.",
    "KNVV-KDGRP is the affected S/4 target representation."
  ]
}
```

---

## 45. Modern advanced variants

### 45.1 Direct patch mode

MVP.

```text
AI creates PatchProposal inside repository.
User approves in local UI.
Files are updated locally.
```

Best for:

```text
local-first prototype
single-user workflow
demo
privacy-sensitive work
```

### 45.2 Git branch / pull request mode

Later.

```text
AI creates patch branch.
System opens pull request.
Validation runs in CI.
Reviewer approves PR.
Merge updates canonical repository.
```

Best for:

```text
team workflow
enterprise review
auditability
engineering-style governance
```

### 45.3 Hosted approval workflow

Later.

```text
PatchProposal stored in hosted backend.
Approvers review in UI.
Postgres stores approval events.
Canonical repo updated after approval.
```

Best for:

```text
multi-user enterprise workspace
role-based approval
central audit
```

### 45.4 AI gateway mode

Later.

```text
AI requests go through central gateway.
Gateway handles provider routing, policy, budget, logging, redaction.
```

Best for:

```text
enterprise deployment
multi-provider support
data policy enforcement
budget control
```

### 45.5 MCP/tool mode

Later.

```text
External agents can call deterministic ModelOps tools:
- find_attribute
- get_lineage
- validate_patch
- create_patch_proposal
- get_impact
```

Best after:

```text
API and CLI are stable
repository model is useful
validation rules are mature
```

Do not start with MCP before the core product works.

---

## 46. Implementation phases

### Phase 1 — Manual patch foundation

Deliver:

```text
PatchProposal schema
manual patch creation
patch validation
review UI
approve/reject status
```

No AI required yet.

### Phase 2 — AI structured output

Deliver:

```text
AIService
task-specific prompt
context bundle
structured JSON output
output parser
PatchProposal creation
```

### Phase 3 — Diff and apply

Deliver:

```text
operation-based patch representation
diff preview
safe file write
ChangeRequest update
audit event
index rebuild
```

### Phase 4 — Gap-to-issue workflow

Deliver:

```text
GapReport
AI issue draft
issue approval
affected object links
```

### Phase 5 — Impact-aware patch review

Deliver:

```text
impact preview
validation checklist
owner/steward suggestions
post-approval health report
```

### Phase 6 — Git/team workflow

Deliver later:

```text
branch creation
pull request generation
CI validation
review comments
merge integration
```

---

## 47. Testing strategy

### 47.1 Unit tests

```text
AI output parser rejects invalid JSON.
AI output parser rejects unknown actions.
PatchProposal schema validation works.
Patch operation validation works.
Patch cannot create duplicate IDs.
Patch cannot reference missing objects.
Patch cannot change generated files.
Patch cannot be approved with errors.
```

### 47.2 Integration tests

```text
Create patch from source note.
Validate patch.
Preview diff.
Approve patch.
Canonical file updates.
ChangeRequest created.
Index rebuilt.
Validation results updated.
```

### 47.3 SAP-specific patch tests

```text
Patch affecting KNVV endpoint keeps sales-area context.
Patch does not model FLCU01 as physical storage.
Patch adding value mapping checks target value list.
Patch updating KNB1 field keeps company-code context.
```

### 47.4 AI safety tests

```text
AI tries to approve change → rejected.
AI tries direct file write → rejected.
AI references unknown object → validation error.
AI invents target value without evidence → flagged as assumption/question.
AI output contains raw sensitive content → warning.
```

---

## 48. Minimal MVP acceptance criteria

The AI patch workflow is MVP-ready when:

```text
User can paste a project note.
System finds likely related objects.
AI creates a structured PatchProposal.
PatchProposal is saved as canonical pending-review object.
System validates proposed changes.
User can see affected objects and diff.
User can approve or reject.
Approved patch updates canonical files.
ChangeRequest is created or updated.
Index is rebuilt.
Repository health is recalculated.
AI never directly changes approved files.
```

---

## 49. Product quality bar

The AI patch workflow is good if it helps users move from this:

```text
"Customer Group 7 in RS4 has no config for CH01 - A17 Footlocker. Difference between P* and R*."
```

to this:

```text
Issue:
  Customer Group config gap for CH01 / A17

Affected objects:
  ATTR-CUST-SALES-CUSTOMER-GROUP
  FEP-S4-KNVV-KDGRP
  VMAP-LEGACY-CUST-GROUP-TO-S4-KDGRP
  VAL-CUST-GROUP-ALLOWED-VALUES

Required checks:
  confirm RS4 customizing
  confirm target value
  rerun allowed values validation
  update value mapping if approved

Governance:
  link decision
  create ChangeRequest
  assign owner
```

without letting AI corrupt the model.

---

## 50. Final recommendation

Implement the AI patch workflow as a controlled approval pipeline, not as a free-form assistant.

Recommended MVP architecture:

```text
Evidence
  → ContextBundle
  → AI structured output
  → PatchProposal
  → Deterministic validation
  → Diff preview
  → Human approval
  → ChangeRequest
  → Canonical file update
  → Git diff
  → Index rebuild
  → Impact/health report
```

This makes AI useful while preserving enterprise trust.

The AI feature should be positioned as:

```text
AI-assisted model update proposal and review.
```

Not:

```text
autonomous SAP model maintenance
```

The product value is not that AI writes everything. The product value is that scattered knowledge becomes structured, validated, traceable, and safely reviewable.
