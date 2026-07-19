# Skill: Patch Generation — Martenweave

## When to use
You have an implementation plan (skill: `implementation-planning`) for one issue and must turn it into a minimal, reviewable patch.

## Inputs
- The implementation plan (Files / Interfaces / Steps, autonomy level, gates)
- Issue number for commit references
- A feature branch checked out from latest `main`

## Read first
1. The implementation plan; re-confirm scope before each edit.
2. Every file you will modify — read it fully before editing it.
3. `pyproject.toml` — ruff settings: line length 100, target py311, rules E, F, I, UP, B.
4. `docs/factory/policies/AGENT_PREVENTIONS.md` — P1 (never weaken tests), P6, P8, P10.
5. `tests/conftest.py` — reuse existing fixtures before writing new ones.

## Do not do
- Do not make drive-by changes: no renames, reformats, or cleanups outside the plan (P10). Noticed something? File a new issue.
- Do not edit `generated/` artifacts; rebuild them with `modelops build-index --repo <path>` or leave them (P8).
- Do not edit canonical `model/` data in any example or repo; that path is `PatchProposal` → approval → `ChangeRequest` only (P6).
- Do not weaken, skip, or delete a test to get to green (P1).
- Do not add a dependency; that is L3 and needs explicit maintainer approval.
- Do not commit before the applicable gates pass.

## Procedure
1. **Red.** Write the failing test named in the plan. Run it and confirm it fails for the right reason:
   ```bash
   pytest tests/test_<area>.py::test_<name> -v
   ```
2. **Green.** Write the smallest implementation that passes. Extend the existing service named in the plan; no new abstraction for a single caller.
3. **Match surrounding style.** `from __future__ import annotations` at the top of every module; modern hints (`str | None`, `list[str]`); line length 100; naming per the file you are in. Verify:
   ```bash
   ruff check .
   ruff format --check src tests
   ```
4. **Sweep comments.** Update docstrings, comments, and CLI help that now describe old behavior. A behavior change without its doc change is an incomplete patch.
5. **Repeat** red → green for each planned step, then run the full suite:
   ```bash
   pytest -q
   ```
6. **Schema/validation touch?** Also run `modelops validate --repo examples/customer_bp_model` (gate G4) to prove canonical examples still pass.
7. **Commit atomically.** One logical change per commit, revertable with a single `git revert`. Conventional message with issue reference, matching repo history:
   ```
   fix: reject mappings without target endpoint (#512)
   feat: add gap summary counts to gap-report (#520)
   docs: sync readiness output with scorecard (#525)
   test: cover broken partner-function reference (#518)
   ```
8. **Stop and re-plan** when the change grows past the planned file list, a gate fails for a reason the plan did not predict, or the fix requires a protected path. Post the blocker on the issue and return to `implementation-planning`.

## Validation
- The planned test failed before implementation and passes now.
- `pytest -q` is green; `ruff check .` and `ruff format --check src tests` are clean.
- `git status` shows only files from the plan — nothing in `generated/`, `model/`, `.env`, or `.github/workflows/`.
- Every commit is atomic and references the issue number.
- Each gate named in the plan was run; results recorded as command → pass/fail → counts.

## Output format
Return:
- Commit hashes with their one-line messages
- Files changed (matching the plan, or deviations explained)
- Test evidence: failing-before output, passing-after counts
- Gates run with exact results
- Re-plan trigger if hit: what blocked and where the plan was wrong
