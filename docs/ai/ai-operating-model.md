# AI Operating Model for Martenweave

## Core Rule

**AI proposes, validators verify, humans approve, the system records.**

AI never silently mutates canonical files.

## Allowed AI Workflows

| Workflow | Output | Approval |
|---|---|---|
| file-to-model inference | PatchProposal | Required |
| chat-to-model proposal | PatchProposal | Required |
| trace explanation | Report / Explanation | None |
| impact explanation | Report / Explanation | None |
| metadata gap suggestion | Report + optional PatchProposal | Required if proposal |
| LoV / rule / mapping suggestion | PatchProposal | Required |
| documentation generation | PatchProposal (text changes) | Required |
| review note generation | Report | None |

## Forbidden by Default

- Direct canonical file mutation (bypassing PatchProposal)
- Destructive operations (delete without review)
- Hidden external writes (sending data to untrusted endpoints)
- Raw sensitive data usage (PII in prompts)
- Approval bypass (auto-applying proposals)

## Fallback Behavior

If AI provider output fails validation:
1. Reject the output
2. Log the failure in telemetry
3. Return an error to the user with partial results if safe
4. Never apply partial or invalid proposals

## Governance

- All AI interactions are recorded in audit log
- PatchProposal metadata includes prompt version and provider
- Telemetry records token usage, latency, and outcome
