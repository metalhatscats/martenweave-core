# AI Development Operating System

## Purpose

Martenweave Core is built for disciplined AI-assisted development. Agents may inspect, plan, edit source, add tests, update docs, and run validation. They must preserve the product rules: canonical files are source of truth, generated indexes are disposable, validators are deterministic, AI proposes changes, and humans approve canonical model mutations.

## Operating Roles

| Role | Primary use |
|---|---|
| Kimi | Long GitHub issue loops: pick issue, implement, validate, commit, report. |
| Codex | Architecture audit, planning, focused refactors, validation hardening, repo preparation. |
| Human owner | Product decisions, credentials, external writes, destructive action approval, final acceptance. |

Do not fork separate workflows for different agents. Use the same skills and validation ladder.

## Standard Task Flow

1. Read `AGENTS.md`.
2. Load only the docs, tests, examples, and code relevant to the task.
3. Restate goal, scope, acceptance criteria, and validation command.
4. Make the smallest complete change.
5. Add or update tests when behavior changes.
6. Run the task-specific validation command.
7. Run the broader validation ladder when practical.
8. Inspect `git diff` and `git status`.
9. Exclude generated artifacts unless explicitly required.
10. Close with the standard closeout report.

## Stop Conditions

Stop and ask the human only when:

- required credentials are missing;
- external writes are required and not explicitly requested;
- destructive action is needed;
- acceptance criteria conflict with Martenweave product rules;
- a product or architecture decision is genuinely ambiguous;
- validation cannot be run due to environment or dependency failure;
- the task requires treating raw sensitive data as context or output.

## Source Of Truth

Canonical model files live in a model repository's `model/` directory. Generated SQLite, JSONL, reports, profiles, and audit logs are rebuildable outputs unless a task explicitly says otherwise.

AI-generated model changes must become `PatchProposal` objects first. Approved changes become `ChangeRequest`s and may then be applied through the documented approval path.
