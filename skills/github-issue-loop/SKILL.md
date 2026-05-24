# Skill: GitHub Issue Loop — Martenweave

## When to use
You are working from a GitHub issue (bug, feature, or refactoring) and need a repeatable workflow to implement, test, and submit changes.

## Inputs
- Issue number and title
- Issue body (requirements, acceptance criteria, repro steps)
- Current branch name

## Read first
1. The issue description and any linked PRs or comments.
2. `AGENTS.md` — core principles (canonical files are source of truth, validation first, AI must not silently mutate).
3. Relevant test file(s) in `tests/` for the area being changed.
4. `src/modelops_core/schemas/registry.py` if the issue touches object types or reference fields.

## Do not do
- Do not commit directly to `main`.
- Do not skip running `pytest` before pushing.
- Do not generate UI, SaaS features, workflow engines, chatbots, or SAP write-back logic.
- Do not add external dependencies without clear justification in the PR description.

## Procedure
1. **Branch**: Create a feature branch from latest `main`.
2. **Reproduce**: If it is a bug, write a failing test first; if a feature, add a test that defines the expected behavior.
3. **Implement**: Make the smallest change that satisfies the issue. Follow existing code style (line length 100, Python 3.11+ syntax).
4. **Validate**:
   ```bash
   pytest -v
   ruff check .
   ```
5. **Index check** (if schemas or validation changed): run `modelops validate --repo examples/customer_bp_model` to ensure canonical model still passes.
6. **Commit**: Write atomic commits with clear messages referencing the issue number.
7. **Push & PR**: Open a PR with a summary of changes, test evidence, and any breaking changes noted.

## Validation
- `pytest -v` passes (no new failures).
- `ruff check .` is clean.
- If the issue required a schema change, `modelops validate` on the example repo still passes.
- The PR description links the issue and includes test evidence.

## Output format
Return:
- Branch name
- Summary of changes (bulleted)
- Test results (`pytest` output snippet)
- PR link or ready-to-push status
