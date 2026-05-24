# AI Context Memory Budgets and Compaction

## Context Bundle Types

| Type | Use Case | Budget |
|---|---|---|
| Object summary | Quick lookup | 1K tokens |
| Trace summary | Lineage explanation | 2K tokens |
| Source profile | Dataset inference | 4K tokens |
| Proposal context | Patch review | 4K tokens |
| Governance gap | Gap analysis | 6K tokens |
| Export/report | Scorecard narration | 4K tokens |

## Compaction Rules

1. **Include**: IDs, names, types, statuses, relationships, key metadata
2. **Summarize**: descriptions longer than 200 chars
3. **Exclude**: raw dataset rows, full object bodies, secrets
4. **Pointer**: link to source file instead of inlining

## Fallback

If context exceeds budget after compaction:
1. Return summary-only bundle
2. Add warning: "Context exceeded budget; truncated to N objects"
3. AI must cite included object IDs

## Provenance

Every AI response should reference `bundle_id` so context can be audited.
