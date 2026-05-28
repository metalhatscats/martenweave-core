# One-Issue Agent Execution Prompt

Copy and paste this prompt into Kimi/Codex to execute a single Martenweave issue safely.

```text
You are working in metalhatscats/martenweave-core.

Current priority order:
1. <issue_number> — <issue_title>

Rules:
- Work one issue at a time.
- Do not ask questions unless blocked.
- Create one branch/PR per issue.
- Keep changes small and mergeable.
- Preserve existing JSON contracts; only additive JSON fields are allowed unless the issue explicitly requires otherwise.
- Do not redesign architecture.
- Do not add external services, telemetry upload, cloud checks, or generated artifacts unless explicitly required.
- Run the issue validation command first.
- Run related contract/docs tests when relevant.
- Run ruff.
- Run full test suite before final closeout if practical.
- Merge only when tests pass.
- Close each issue with a concise closeout comment.

Validation:
- <issue_validation_command>

Before starting:
1. Read AGENTS.md for project conventions.
2. Read the issue body, comments, and linked docs.
3. Check git status and switch to main.
4. Create a branch: issue-<number>-<short-description>.

While working:
- Do not commit generated/, .env, raw data, caches, or local artifacts.
- Do not mutate canonical model files without PatchProposal → approval flow.
- Do not hard-code secrets or expose credential values.

Before closeout:
1. Run the issue validation command.
2. Run ruff check src tests.
3. Run pytest if practical.
4. Verify git diff is minimal and focused.
5. Squash-merge the PR only after CI passes.
6. Post a closeout comment on the issue: PR number, what changed, validation evidence.
```

## Customisation

Replace the placeholders:

| Placeholder | Source |
|---|---|
| `<issue_number>` | GitHub issue number |
| `<issue_title>` | GitHub issue title |
| `<issue_validation_command>` | Issue body validation command line |

## Safety Reminders

- **Generated artifacts are disposable.** Rebuild them with `modelops build-index` instead of editing directly.
- **Canonical files are source of truth.** AI changes must go through `PatchProposal → validation → human approval → ChangeRequest → apply → audit`.
- **Do not bypass validation.** If tests fail, fix the root cause; do not skip or disable checks.
