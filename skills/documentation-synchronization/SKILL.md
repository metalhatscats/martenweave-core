# Skill: Documentation Synchronization — Martenweave

## When to use
Use whenever a patch changes behavior, commands, structure, or conventions. Docs move in the same patch as the code, never as a follow-up.

## Inputs
- The behavior or structure change being shipped.
- The docs affected, or candidates to check.

## Read first
1. `skills/documentation-discipline/SKILL.md` — doc layer ownership rules.
2. `docs/factory/policies/QUALITY_GATES.md` — G10 documentation and website consistency.
3. `AGENTS.md` — the agent front door: structure, commands, conventions.
4. `docs/factory/memory/PROJECT_MEMORY.md` — current project truth index.

## Do not do
- Do not document behavior that does not exist; mark future work as planned (P3, P9).
- Do not duplicate detail — link to the owning doc instead.
- Do not cite CLI commands that do not exist; `scripts/validate_doc_commands.py` rejects them.
- Do not edit website files here — website claims follow `skills/website-claim-verification/SKILL.md`.
- Do not leave stale docs describing the old behavior after a change.

## Procedure
1. Map the change to its owning doc layer: `docs/ai` (AI/agent behavior), `docs/architecture` (boundaries, ADRs), `docs/developer` (contributor guides, testing), `docs/product` (scope, acceptance), `docs/operations` (import/export, runbooks).
2. Update the owning doc in the same commit as the code change.
3. Sync `README.md` when user-facing commands, install steps, or the Status section change.
4. Sync `AGENTS.md` when project structure, CLI commands, build/test commands, or conventions change.
5. Link rather than duplicate: one owning page holds the detail; other pages link to it.
6. If project truth changed (state, limitations, decisions, validation commands), update `docs/factory/memory/`: `PROJECT_MEMORY.md`, `KNOWN_LIMITATIONS.md`, `REJECTED_IDEAS.md`, or `VALIDATION_COMMANDS.md`.
7. Sweep for comments and docstrings that still describe the old behavior and align them.
8. Run the G10 checks below.

## Validation
```bash
.venv/bin/python scripts/validate_doc_commands.py
.venv/bin/python scripts/validate_skills.py
```
- Every `modelops <command>` snippet in `README.md` and `docs/**/*.md` resolves against the real CLI.
- Docs that state numbers (counts, outputs) are re-verified by running the command and quoting exact output (P9).

## Output format
Return:
- docs changed, per layer;
- `README.md` / `AGENTS.md` sync (or explicit "no change needed" with reason);
- memory docs updated;
- validator results.
