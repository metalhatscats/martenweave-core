# Skill: Implementation Planning — Martenweave

## When to use
You have selected one `agent-ready` GitHub issue and must turn it into a minimal, verifiable implementation plan before touching any code.

## Inputs
- Issue number, goal, scope, acceptance criteria, and validation command
- Anything the issue links: earlier findings, related issues, PRs
- Current branch name

## Read first
1. The issue body; it follows `.github/ISSUE_TEMPLATE/agent_task.yml` (Goal, Scope, Acceptance criteria, Validation command).
2. `docs/factory/policies/QUALITY_GATES.md` — gate definitions G1–G11, selection rules, exact commands.
3. `docs/factory/policies/AUTONOMY_LEVELS.md` — L0–L3 classification and the stop rule for L3.
4. `docs/factory/policies/AGENT_PREVENTIONS.md` — especially P2 (search before writing) and P10 (no scope expansion).
5. `docs/factory/memory/KNOWN_LIMITATIONS.md` and `docs/factory/memory/REJECTED_IDEAS.md` — do not plan known dead ends.
6. The code you expect to touch: services under `src/modelops_core/`, tests under `tests/`.

## Do not do
- Do not write or edit production code or tests while planning.
- Do not plan around an existing service you have not searched for (P2).
- Do not plan anything outside the issue scope; side findings become new issues (P10).
- Do not plan direct edits to `generated/`, canonical `model/` data, or protected paths (P6, P8).
- Do not reference files or commands you have not confirmed exist (`ls`, `martenweave --help`).

## Procedure
1. **Restate acceptance criteria.** Copy them into the plan as checkboxes, plus the validation command exactly as written in the issue.
2. **Search before writing (P2).** Grep/Glob for the service, CLI command, or pattern that already does this; scan `martenweave --help` and `docs/`. Name the exact file(s) to extend (e.g. `src/modelops_core/gaps/gap_service.py`). If nothing exists, say so explicitly — that usually pushes the change toward L3.
3. **Define the failing test first.** Name the test file and test function that will fail before implementation, e.g. `tests/test_gap_service.py::test_gap_flags_unmapped_column`. The test must encode an acceptance criterion, not a tautology.
4. **List exact files to change.** One line per file: path + what changes in it. Verify each path exists (`ls`) or mark it as `new`.
5. **Name the gates that apply.** Every patch: G1–G3, G5, G6, G10. Add G4 (schemas/validation), G7 (API/MCP), G8 (demo paths), G9 (frontend) only when the patch touches that surface. Quote commands from `docs/factory/policies/QUALITY_GATES.md`.
6. **Classify autonomy.** L1 polish, L2 fix, or L3 guarded per `AUTONOMY_LEVELS.md`; when unclear between L2 and L3, treat as L3. For L3 the plan ends at branch + PR + issue comment requesting maintainer approval — do not plan a merge. Stop there.
7. **Size check.** If the plan needs more than 5 files or more than one session, stop: comment on the issue proposing a split, file follow-up issues, and plan only the first slice.

## Validation
- Every acceptance criterion maps to at least one planned test or gate.
- Every path in the plan exists or is explicitly marked `new`.
- Gates named match the touched surfaces per QUALITY_GATES.md rule 1.
- Autonomy level is recorded; an L3 plan has an explicit stop point.
- The plan fits one session: at most 5 files, no multi-session phases.

## Output format
Return the plan with exactly these parts, in order:
- **Acceptance criteria** — restated, as checkboxes
- **Files** — path (existing/`new`) + what changes
- **Interfaces** — functions, CLI flags, or schemas touched, with signatures
- **Steps** — ordered: failing test → minimal implementation → gates → review
- **Autonomy** — L1/L2/L3 with one-line justification, plus gates to run
