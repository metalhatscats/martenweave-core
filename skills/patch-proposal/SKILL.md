# Skill: Patch Proposal — Martenweave

## When to use
You (the AI agent) want to propose a change to canonical model files. Humans must review and approve before application.

## Inputs
- A note, requirement, or structured diff describing the desired change
- Path to the model repository

## Read first
1. `src/modelops_core/patching/patch_proposal_service.py` — `build_patch_proposal`, `render`, `write`.
2. `src/modelops_core/patching/patch_validator.py` — deterministic validation of patch proposals.
3. `src/modelops_core/patching/apply_service.py` — atomic apply with rollback and audit.
4. `docs/architecture/AI_PATCH_WORKFLOW.md` — full workflow description.

## Do not do
- Do not directly edit `model/*.md` files when acting as an AI proposing changes.
- Do not bypass the `PatchProposal` → human approval → `ChangeRequest` → apply flow.
- Do not apply patches to blocked paths: `generated`, `data`, `imports`, `schemas`, `apps`, `docs`, `.env`.
- Do not silently mutate; always produce a reviewable artifact.

## Procedure
1. Build a patch proposal from a note or structured input:
   ```bash
   modelops propose-patch --from ./note.md --repo <path>
   ```
   Or programmatically via `build_patch_proposal()`.
2. The service writes a `PatchProposal` canonical object (Markdown + YAML frontmatter) into `model/`.
3. Run deterministic validation on the proposal:
   ```bash
   modelops validate --repo <path>
   pytest tests/test_patch_proposal_validation.py
   ```
4. Render the proposal for human review (the service generates a diff or summary).
5. Wait for human approval. Once approved, the human creates or promotes a `ChangeRequest`.
6. Apply the approved change request atomically. Use the documented repo apply command. If `modelops apply-change-request` is not yet implemented, report the gap and apply the change manually through the canonical file editing flow with human oversight.
7. The apply service writes to canonical files, logs an audit event, and triggers an index rebuild.

## Validation
- `PatchProposal` passes deterministic validation (`test_patch_proposal_validation.py`).
- No blocked paths are targeted by the proposal.
- After apply, `modelops validate` and `pytest` still pass.
- An audit event is appended to `generated/audit_events.jsonl`.

## Output format
Return:
- Patch proposal ID
- Files that would be created/modified/deleted
- Validation result (pass/fail)
- Status (`proposed`, `approved`, `applied`, or `rejected`)
- Audit event ID if applied
