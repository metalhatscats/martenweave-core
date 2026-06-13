# AI Permission Policy and Risk Tiers

## Risk Tiers

### Tier 0 — Read-Only Explanation
- trace explanation
- impact explanation
- health report narration
- **No approval required.**

### Tier 1 — Suggestion / Report Generation
- metadata gap analysis
- coverage analysis
- review note generation
- **No approval required.** Output is a report.

### Tier 2 — PatchProposal Creation
- file-to-model inference
- chat-to-model proposal
- LoV / rule / mapping suggestion
- documentation update suggestion
- **Approval required.** Proposal must be reviewed before apply.

### Tier 3 — Approval-Gated Apply
- applying a PatchProposal
- requires: validation pass, impact analysis, human approval

### Tier 4 — Forbidden / Destructive
- direct canonical file mutation
- auto-apply without approval
- destructive changes without rollback plan
- external data exfiltration

## Default Policy

| Channel | Max Tier |
|---|---|
| CLI (local) | Tier 3 (with `--yes` flag) |
| API | Tier 2 (apply requires explicit endpoint) |
| MCP | Tier 2 (tools can propose, not apply) |
| Future UI | Tier 3 (guided approval flow) |

## High-Risk Operations

Operations involving these object types are marked high-risk:
- Mapping
- ValidationRule
- ValueList
- ValueMapping

High-risk proposals require:
1. Impact analysis (`modelops proposal impact`)
2. Validation pass
3. Explicit approval
4. Audit logging

## Privacy Defaults for AI Context

By default, AI context bundles exclude raw dataset rows and sample values.
Only metadata, column names, row counts, and model objects are included.

To include raw sample values, explicitly opt in with `--include-raw-samples`:

```bash
modelops propose-patch --from note.md --include-raw-samples
```

When this flag is used, the CLI prints a warning that raw dataset rows may leave
the local environment depending on the configured provider.
