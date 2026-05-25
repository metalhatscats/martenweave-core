# Patch Proposal And Approval Flow

## Core Rule

AI proposes, validators verify, humans approve, the system records.

## Flow

```text
Input note / dataset profile / spreadsheet / review comment
  -> PatchProposal
  -> deterministic proposal validation
  -> impact and risk review
  -> human approval
  -> ChangeRequest
  -> apply to canonical files
  -> validation
  -> generated index rebuild
  -> audit event
```

## PatchProposal

A `PatchProposal` is a reviewable artifact containing proposed operations, assumptions, evidence, affected objects, and validation status. It is not approval.

## ChangeRequest

A `ChangeRequest` records human-approved change intent. High-risk changes require explicit approval before apply.

## Forbidden

- Applying rejected proposals.
- Applying high-risk proposals without approval.
- Hidden canonical mutation from chat, import, or AI inference.
- Using generated files as the approval record.

## Validation

Use:

```bash
.venv/bin/modelops proposal validate <PROPOSAL_ID> --repo <repo>
.venv/bin/modelops proposal impact <PROPOSAL_ID> --repo <repo>
.venv/bin/modelops validate --repo <repo>
```
