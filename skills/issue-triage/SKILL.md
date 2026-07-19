# Skill: Issue Creation and Prioritization — Martenweave

## When to use
You have verified, deduplicated gaps (skill: `gap-regression-detection`) and need to
maintain the GitHub backlog of `metalhatscats/martenweave-core` as the durable factory
work queue — stages 4–5 of `docs/factory/WORKFLOWS.md`.

## Inputs
- Ranked gap list with evidence (command → result) and north-star references
- GitHub CLI (`gh`) authenticated against the origin repository
- Labels in use: `agent-ready` on every agent task; `factory` for factory-infrastructure
  work (harness, skills, policies, memory docs)

## Read first
1. `.github/ISSUE_TEMPLATE/agent_task.yml` — the required issue structure.
2. `docs/factory/WORKFLOWS.md` §1 stages 4–5 — one gap → one issue; ranking rules.
3. `docs/factory/policies/AGENT_PREVENTIONS.md` — P3 (traceability), P9 (evidence), P10 (scope).
4. `docs/factory/policies/AUTONOMY_LEVELS.md` — flag L3 issues so agents stop and ask.

## Do not do
- Do not file an issue for an unverified or `suspected` finding (P9).
- Do not bundle several gaps into one issue, or split one gap across several.
- Do not create duplicates: search first, update the existing issue instead.
- Do not file issues for known limitations, rejected ideas, or non-goals (P3, P4).
- Do not start implementing; the issue itself is the deliverable of this skill.

## Procedure
1. **Dedupe** each gap:
   ```bash
   gh issue list --search "<distinctive terms>" --state all --limit 20
   gh issue view <n>        # for every candidate match
   ```
2. **Update vs create.** If an open issue already covers the gap, comment with the new
   evidence and refresh its acceptance criteria. Reopen a closed issue only when the
   same defect returned (a regression). Create a new issue only when no match exists.
3. **Write the issue** to the `agent_task` template — every field is required:
   - *Goal*: one sentence describing the desired outcome.
   - *Scope*: files, modules, docs, examples, or behavior that may change.
   - *Acceptance criteria*: testable bullets.
   - *Validation command*: the exact gate command(s) from
     `docs/factory/memory/VALIDATION_COMMANDS.md` that must pass at closeout.
   - *Out of scope*: explicit exclusions that keep the patch small (P10).
   - *Safety notes*: secrets, canonical data, generated artifacts, approval
     constraints; state the autonomy level when the work is L3.
   - Set both dropdown answers (core/domain-pack impact; generated/canonical boundary).
   ```bash
   gh issue create --title "[Agent] <short title>" --label agent-ready --body-file issue.md
   ```
   Add `--label factory` when the gap is in factory infrastructure.
4. **One gap = one issue.** If a drafted issue covers several gaps, split it before filing.
5. **Size discipline.** An issue must be completable in one focused session with its
   named gates. Too big? File the smallest valuable slice plus one follow-up issue.
6. **Rank the queue** (`WORKFLOWS.md` stage 5 order):
   (a) correctness/trust bugs in shipped behavior, (b) doc/claim drift,
   (c) test/CI health, (d) small UX clarity wins, (e) everything else — smallest first
   within a class. Broken factory tooling (validation scripts, gates) jumps the queue;
   everything depends on it.
7. **Select the next task**: the smallest valuable issue at the top of that order.
   Never skip the queue to work on something unfiled.
8. **Record linkage**: note which issue number each input gap became.

## Validation
- Every created issue has all six `agent_task` fields filled and `agent-ready` applied.
- A dedupe search (`gh issue list --search`) is quoted for each new issue.
- Every validation command cited in an issue exists and was run at least once.
- Each input gap maps to exactly one issue number (new, updated, or reopened).

## Output format
- Table: gap title → action (`created #n` / `updated #n` / `reopened #n`) → labels →
  severity class
- The recommended next task (smallest valuable) with its issue number
- Gaps intentionally not filed, with the reason (known limitation, rejected idea,
  out of scope)
