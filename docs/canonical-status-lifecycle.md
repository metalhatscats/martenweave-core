# Canonical Status Lifecycle

Martenweave uses distinct status enums for canonical objects, proposals, and change requests. There is no enforced workflow engine — statuses are validated for presence and type, but transitions are driven by human or agent decision.

---

## General Status

Used by most canonical object types (`Attribute`, `FieldEndpoint`, `BusinessEntity`, `Mapping`, etc.).

| Status | Meaning | Typical use |
|---|---|---|
| `proposed` | Suggested but not yet reviewed | New ideas, draft proposals from inference |
| `draft` | Under active development | Objects being edited before first review |
| `active` | Approved and in use | Production-ready model objects |
| `under_review` | Submitted for approval | Objects in a review cycle |
| `deprecated` | Still present, do not use for new work | Legacy objects scheduled for retirement |
| `retired` | No longer in use | Removed from active governance |
| `blocked` | Cannot progress without resolution | Waiting on a decision or external dependency |
| `planned` | Scheduled for future implementation | Roadmap items not yet started |
| `implemented` | Change has been applied | Used after a `ChangeRequest` is executed |
| `archived` | Preserved for audit only | Historical records |

### Examples by object kind

```yaml
# Attribute — typical lifecycle
status: draft      # → active → deprecated → retired

# BusinessEntity — stable conceptual object
status: active

# Mapping — may go through review
status: under_review  # → active

# ValidationRule — may be planned then implemented
status: planned    # → implemented → active
```

---

## Patch Proposal Status

Used only by `PatchProposal` objects. Controls whether a proposal can be applied.

| Status | Meaning |
|---|---|
| `pending_review` | Created, not yet evaluated |
| `accepted` | Approved for application |
| `rejected` | Declined, will not be applied |

### Lifecycle

```
pending_review → accepted → (apply operation creates ChangeRequest)
pending_review → rejected
```

A proposal must be `accepted` before `modelops proposal apply` will write any files.

---

## Change Request Status

Used only by `ChangeRequest` objects. Tracks governance approval.

| Status | Meaning |
|---|---|
| `pending` | Awaiting approval |
| `approved` | Cleared for implementation |
| `rejected` | Declined |
| `implemented` | Changes have been applied to canonical files |

### Lifecycle

```
pending → approved → implemented
pending → rejected
```

---

## Issue Status

Used only by `Issue` objects.

| Status | Meaning |
|---|---|
| `open` | Reported, not started |
| `in_progress` | Being worked on |
| `resolved` | Fix verified |
| `closed` | No longer tracking |

---

## Validation Notes

- Layer 1 validation checks that `status` is present and non-empty.
- Layer 1 does **not** enforce valid enum values for `status` on generic objects (strings are accepted).
- `PatchProposal` and `ChangeRequest` objects validate against their specific enums.
- There is no automatic state machine. Transitioning a status is a deliberate edit.

## See also

- [Canonical Model Format](canonical-model.md) — file format and mandatory fields
- [User Guide](user-guide.md) — proposal review and apply workflow
- [Schema and Validation Spec](architecture/SCHEMA_AND_VALIDATION_SPEC.md) — validation layer details
