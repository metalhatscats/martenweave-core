# Kimi GitHub Issue Loop

## Purpose

Kimi should be able to work issue-by-issue without drifting or asking unnecessary questions.

## Selection

Pick the highest-priority open issue that is agent-ready. Prefer this order:

1. safety and validation blockers;
2. broken docs or stale agent instructions;
3. core/domain-pack boundary cleanup;
4. skills layer gaps;
5. CI/test gaps;
6. CLI contract gaps;
7. generic example/demo gaps;
8. architecture boundary gaps;
9. product roadmap gaps;
10. future integration work.

If labels are missing, use the issue title/body and this order.

## Loop

1. Read the issue, comments, `AGENTS.md`, relevant skill, relevant docs, tests, and code.
2. Restate goal, scope, acceptance criteria, out of scope, and validation command.
3. Check `git status --short --branch`.
4. Create or switch to a non-main issue branch.
5. Implement the smallest complete solution.
6. Add or update tests if behavior changes.
7. Run the issue validation command.
8. Run the broader validation ladder when practical.
9. Inspect `git diff --check`, `git diff --stat`, and `git status --short`.
10. Avoid committing `generated/`, `.env`, raw data, caches, or local artifacts.
11. Commit with a clear issue-linked message.
12. Close the issue only when acceptance criteria pass.
13. Produce a closeout report.
14. Move to the next issue only after the repo is clean or intentionally dirty.

## Ask The Human Only If

- credentials are missing;
- external writes are required;
- destructive action is required;
- the issue conflicts with product rules;
- validation cannot run;
- acceptance criteria are mutually inconsistent;
- the issue requires a real product decision, not an implementation choice.

## Closeout

Use `CLOSEOUT_REPORT_TEMPLATE.md`. If blocked, use `FAILURE_REPORT_TEMPLATE.md`.
