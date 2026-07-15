# Model Change Request Workflow

Version: 0.5.0
Status: Draft  
Scope: Lightweight end-to-end workflow for requesting, reviewing, approving, applying, and tracking model changes  

---

## 1. Core principle

```text
AI proposes.
Validators check.
Humans approve.
Canonical files change only after approval.
```

No workflow engine is required. The workflow is enforced by CLI commands, validation rules, and canonical object state transitions.

---

## 2. Workflow objects

| Object | Purpose | Created by |
|---|---|---|
| `PatchProposal` | Structured proposed change before human review | AI or user |
| `ChangeRequest` | Approved change ready for implementation | Human after review |
| `Issue` | Gap, problem, or concern discovered during review | Human or validator |
| `Decision` | Accepted rationale for a model choice | Human or agent |
| `Evidence` | Source material supporting a decision or change | Human or agent |
| `AuditEvent` | Immutable record of what happened | System |

---

## 3. ChangeRequest lifecycle

```text
draft
  -> requested          (submitted for review)
  -> triaged            (assigned, priority set)
  -> impact_reviewed    (impact analysis completed)
  -> approved           (approver signed off)
  -> applied            (canonical files updated)
  -> closed             (verified, audit log complete)

Any state -> rejected   (approver or reviewer declined)
Any state -> cancelled  (requester withdrew)
```

### State definitions

| State | Meaning | Who moves it |
|---|---|---|
| `draft` | Being written, not yet submitted | Requester |
| `requested` | Submitted, waiting for triage | Requester |
| `triaged` | Reviewer acknowledged, priority set | Triage owner |
| `impact_reviewed` | Impact analysis done, risks known | Impact reviewer |
| `approved` | All gates passed, ready to apply | Approver |
| `rejected` | Will not be applied, reason recorded | Approver or reviewer |
| `applied` | Canonical files updated, index rebuilt | Implementer |
| `closed` | Verified in generated index, audit complete | Closer |

### Current schema mapping

The canonical `ChangeRequest` schema uses a simplified status set:

| Schema status | Maps to workflow state |
|---|---|
| `pending` | `requested`, `triaged`, or `impact_reviewed` |
| `approved` | `approved` |
| `rejected` | `rejected` |
| `implemented` | `applied` or `closed` |

Future CLI commands may store the detailed state in a `workflow_state` field.

---

## 4. Required fields

### ChangeRequest

| Field | Required? | Description |
|---|---|---|
| `id` | Yes | Stable ID, prefix `CR-` |
| `type` | Yes | `ChangeRequest` |
| `status` | Yes | One of `pending`, `approved`, `rejected`, `implemented` |
| `name` / `title` | Yes | Short human-readable name |
| `requester` | Yes | Who asked for the change |
| `reason` | Yes | Why the change is needed |
| `affected_objects` | Yes | List of object IDs that change |
| `priority` | Recommended | `low`, `medium`, `high`, `critical` |
| `requested_change` | Yes | Summary of what should change |
| `expected_impact` | Recommended | What breaks or needs re-validation |
| `approvers` | Yes for high-risk | List of approver IDs |
| `source_evidence` | Recommended | File, note, or ticket that triggered this |
| `linked_proposals` | Recommended | `PatchProposal` IDs this CR resolves |
| `related_issues` | Optional | Issues this CR addresses |
| `related_decisions` | Optional | Decisions that justify this CR |

### PatchProposal

| Field | Required? | Description |
|---|---|---|
| `id` | Yes | Stable ID, prefix `PP-` |
| `type` | Yes | `PatchProposal` |
| `status` | Yes | `pending_review`, `accepted`, `rejected` |
| `title` | Yes | What the proposal does |
| `created_by` | Yes | `user`, `ai`, or `system` |
| `source_evidence` | Yes | What triggered the proposal |
| `affected_objects` | Yes | Objects touched by the proposal |
| `operations` | Yes | Structured create/update operations |
| `validation_status` | Recommended | `pending`, `valid`, `invalid` |
| `validation_results` | Recommended | Validation output if checked |

---

## 5. Relationship map

```text
Evidence + Decision
        \
         Issue
           |
     PatchProposal  <-- created_by: ai | user | system
           |
     ChangeRequest  <-- linked_proposals, requester, approvers
           |
    Affected objects (canonical files)
           |
     AuditEvent     <-- immutable log of apply action
```

---

## 6. Workflow flows

### 6.1 User-requested change from chat

```text
User describes change in chat
  -> Agent creates PatchProposal with affected_objects and operations
  -> Agent runs validation (dry-run)
  -> Agent presents proposal to user
  -> User reviews, asks questions, approves
  -> User or agent creates ChangeRequest
  -> ChangeRequest status: pending -> approved
  -> Agent applies changes to canonical files
  -> Agent runs validation (post-apply)
  -> Agent builds index
  -> System writes AuditEvent
  -> ChangeRequest status: implemented
```

### 6.2 Change inferred from file/spreadsheet import

```text
User imports dataset or spreadsheet
  -> System profiles columns, infers model
  -> System creates PatchProposal (create ops only)
  -> System runs validation
  -> System presents diff preview
  -> User reviews inferred objects
  -> User approves or edits proposal
  -> User creates ChangeRequest
  -> Apply, validate, build index, audit
```

### 6.3 Correction after validation/gap analysis

```text
Validation or gap analysis finds broken references, missing ownership, or flat structure
  -> System or agent creates Issue
  -> Agent creates PatchProposal to fix the Issue
  -> Agent links PatchProposal to Issue
  -> User reviews both Issue and PatchProposal
  -> User creates ChangeRequest referencing the Issue
  -> Apply, validate, build index, audit
  -> Issue status: resolved
```

### 6.4 Governance-driven change

```text
Governance review finds owner change, LoV update, rule change, or mapping change needed
  -> Reviewer creates PatchProposal with governance rationale
  -> PatchProposal includes required_approvers if high-risk
  -> Approver reviews and approves
  -> ChangeRequest created with approver recorded
  -> Apply, validate, build index, audit
```

---

## 7. Proposal-first safety rules

| Rule | Enforcement |
|---|---|
| No direct canonical file mutation from chat or inference | CLI `apply` only accepts `PatchProposal` or `ChangeRequest` |
| Every change must have a `ChangeRequest` | Audit events reference a CR ID |
| High-risk changes require explicit approval | Risk rules computed before apply (see issue #32) |
| Invalid proposals cannot be applied | Post-apply validation fails -> rollback |
| Applied files remain recoverable | Validated changes stage under `generated/patch-transactions/`; exact backups and a receipt are written before atomic replacement |
| All states are reversible until `applied` | Rejected CRs stay in repo for audit |

---

## 8. Lightweight path for low-risk changes

Small, low-risk changes can skip the full lifecycle:

```text
draft -> approved -> applied -> closed
```

Criteria for lightweight path:
- Affects fewer than 5 objects
- No active objects with downstream mappings
- No ownership changes
- No validation rule or LoV changes
- Validation passes with zero errors

High-risk criteria (must use full path):
- Changes to mapped fields
- Changes to ValueList or ValidationRule
- Ownership or stewardship changes
- Changes to active objects with >2 relationships
- Impact depth >1 hop

---

## 9. Audit trail

Every workflow action generates an `AuditEvent`:

| Event type | When | Data captured |
|---|---|---|
| `change_request_created` | CR submitted | requester, affected_objects, reason |
| `patch_proposal_created` | PP created | created_by, source_evidence, ops count |
| `patch_proposal_validated` | PP checked | validation_status, error_count, warning_count |
| `change_request_approved` | CR approved | approver, approval_timestamp |
| `change_request_rejected` | CR rejected | rejecter, rejection_reason |
| `change_applied` | Files updated | changed_files, old_hash, new_hash |
| `index_rebuilt` | Index refreshed | object_count, relationship_count |
| `issue_resolved` | Issue closed | resolution, linked_cr |

Audit events are append-only and written to `generated/audit_events.jsonl`.

---

## 10. CLI command mapping

| Workflow step | Planned CLI command |
|---|---|
| Create PatchProposal | `martenweave propose-patch --from <note>` |
| Create ChangeRequest | `modelops change-request create --title <title> --affected-object <id>` |
| List ChangeRequests | `modelops change-request list` |
| Show ChangeRequest | `modelops change-request show <id>` |
| Update status | `modelops change-request update-status <id> --status <status>` |
| Approve | `modelops change-request approve <id> --approver <person>` |
| Reject | `modelops change-request reject <id> --reason <reason>` |
| Apply proposal | `martenweave proposal apply <id>` |
| Preview impact | `martenweave impact <object-id>` |
| Validate | `martenweave validate --repo <repo>` |
| Build index | `martenweave build-index --repo <repo>` |
