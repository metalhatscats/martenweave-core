# Agent Loop Checklist

> Safety rules for AI coding agents working in the Martenweave Core repository.

---

## Before Starting Any Work

1. **Sync main.** Run `git fetch --all --prune`, `git checkout main`, `git pull --ff-only`.
2. **Read the issue.** Understand Goal, Scope, Acceptance Criteria, Out of Scope, and Safety Notes.
3. **Inspect the affected area.** Read relevant package/module files and existing tests.
4. **Create a branch.** Use format `issue-<number>-short-slug`. Never commit directly to `main`.
5. **Validate baseline.** Run `pytest` and `ruff check .` to confirm the repo is clean before making changes.

## During Implementation

6. **Reuse existing architecture.** Prefer extending existing services over introducing new subsystems.
7. **Dry-run first.** For any command that mutates files or indexes, test `--dry-run` before `--apply`.
8. **Clean generated artifacts.** Run `modelops clean --dry-run` to preview, then `modelops clean` to remove stale `generated/` files before rebuilding.
9. **Validate before indexing.** Always run `modelops validate` before `modelops build-index`.
10. **Never commit generated files.** The `generated/` directory contains rebuildable artifacts. Only canonical files in `model/` are source of truth.
11. **Test every new behavior.** Add tests for happy paths and negative/safety cases. Run narrow tests first, then the full suite.
12. **Keep machine-readable output stable.** CLI commands should emit predictable JSON when passed `--json`. Do not break existing JSON contracts without updating tests.

## Before Committing

13. **Run the validation ladder:**
    - `python -m pytest relevant_tests -v`
    - `python -m pytest -v`
    - `ruff check .`
    - Any new CLI command with `--help` or sample invocation
14. **Review diff scope.** `git diff` should be limited to the issue. No unrelated changes.
15. **Commit with reference.** Use format `feat(#NNN): concise description` or `fix(#NNN): concise description`.

## After Merging

16. **Return to main.** `git checkout main && git pull --ff-only`.
17. **Delete the branch.** `git branch -d issue-<number>-short-slug`.
18. **Close the issue.** Comment with an end report: summary, changed files, validation results, behavior added, risk notes, git references.

---

## Hard Constraints (Never Violate)

- Do **not** work on #42 or any credential/auth/GitHub workflow issue.
- Do **not** edit `.github/workflows/` files.
- Do **not** introduce external AI provider logic beyond existing `NoProviderAdapter` unless explicitly required.
- Do **not** create new repos.
- Do **not** mutate canonical model files during dry-run commands.
- Do **not** perform recursive deletion outside the repository root.
- Generated artifact cleanup must be **preview-first** and **deterministic**.
