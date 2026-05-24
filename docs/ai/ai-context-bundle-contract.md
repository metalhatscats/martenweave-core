# AI Context Bundle Contract

## Purpose

Define what model evidence AI workflows receive, within token and privacy limits.

## Bundle Types

| Type | Use Case | Typical Size |
|---|---|---|
| `file-to-model` | Infer model from dataset profile | 4K–16K tokens |
| `chat-to-model` | Respond to user query about model | 2K–8K tokens |
| `trace-explanation` | Explain lineage for an object | 2K–8K tokens |
| `impact-explanation` | Explain impact of a change | 2K–8K tokens |
| `metadata-gap` | Suggest missing metadata | 4K–12K tokens |
| `lov-rule-suggestion` | Suggest values or rules | 4K–12K tokens |
| `proposal-review` | Review a PatchProposal | 4K–16K tokens |

## Required Fields

```python
class ContextBundle:
    bundle_id: str
    workflow: str
    included_objects: list[dict]  # id, type, name, status, key fields
    included_sources: list[dict]  # source profile summaries
    evidence_refs: list[str]      # object IDs cited
    relationship_refs: list[dict] # from -> to -> rel_type
    excluded_sections: list[str]  # what was left out
    token_budget: int
    size_budget: int
    redaction_policy: str         # "full", "summary_only", "none"
    created_at: str
```

## Compaction Rules

1. If total size exceeds budget, exclude `description` and `notes` fields first.
2. If still over budget, exclude objects beyond relationship distance 2.
3. If still over budget, return a fallback message with summary only.

## Redaction

- Raw dataset values are excluded by default.
- PII fields are summarized or hashed.
- Secrets and credentials are never included.

## Citation

AI output must cite object IDs from the bundle:
```json
{
  "suggestion": "Add AttributeUsage for ATTR-1 in context CTX-1",
  "evidence": ["ATTR-1", "CTX-1"]
}
```
