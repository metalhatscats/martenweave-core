# Martenweave Development AI Factory

A **repository-native** development factory: the conventions, definitions, and a small
harness that let Kimi agents safely analyze, improve, test, document, and prepare
Martenweave with minimal maintainer involvement.

The factory is deliberately **not** a platform. It is:

1. **Versioned documentation** (this directory) — the durable context every agent
   loads: north star, policies, agent definitions, workflows, and project memory.
2. **Reusable skills** (`../../skills/`) — procedure cards agents follow for each
   kind of work, structurally validated by `scripts/validate_skills.py`.
3. **A work queue** — GitHub issues in `metalhatscats/martenweave-core` (and
   `Martenweave/martenweave.github.io` for website work), written to the
   `.github/ISSUE_TEMPLATE/agent_task.yml` standard: Goal, Scope, Acceptance
   criteria, Validation command, labeled `agent-ready`.
4. **One harness** — `./factory` at the repository root, a stdlib-only Python script
   that runs audits, selects the next task, executes deterministic gates, and gathers
   release evidence. It orchestrates existing commands (`pytest`, `ruff`,
   `martenweave`, demo scripts, npm); it implements no product logic of its own.
5. **Existing product machinery** — `PatchProposal`/`ChangeRequest` approval flow,
   `ReadinessAgent` gates, CI workflows. The factory uses these; it does not replace them.

## Layout

```
factory                       # executable harness (repo root, stdlib Python 3.11+)
docs/factory/
  README.md                   # this file
  NORTH_STAR.md               # product scope agents must not drift from
  WORKFLOWS.md                # autonomous loop, patch lifecycle, recovery rules
  agents/                     # specialist agent definitions (7)
  policies/
    AUTONOMY_LEVELS.md        # L0–L3: what may ship automatically vs needs approval
    QUALITY_GATES.md          # G1–G11 gate definitions and exact commands
    AGENT_PREVENTIONS.md      # P1–P10 hard prohibitions and enforcement
  memory/
    PROJECT_MEMORY.md         # current state index — read first every session
    KNOWN_LIMITATIONS.md      # verified product limitations (do not re-report as bugs)
    REJECTED_IDEAS.md         # ideas already decided against, with reasons
    LESSONS_LEARNED.md        # dated lessons from completed factory work
    VALIDATION_COMMANDS.md    # the exact command set with expected outputs
skills/<factory skills>/      # 13 procedure cards (see skills/README.md)
```

## The loop

```text
inspect repositories → compare with product north star → detect verified gaps →
create or update issues → select the smallest valuable task → produce a patch →
run deterministic gates → perform critical review → update documentation and
website → merge or request human approval → continue
```

Full lifecycle, escalation, and recovery rules: `WORKFLOWS.md`.
Gate list and commands: `policies/QUALITY_GATES.md`.
What may ship without a human: `policies/AUTONOMY_LEVELS.md`.
Hard prohibitions: `policies/AGENT_PREVENTIONS.md`.

## Harness commands

Run from the Core repository root (`./factory`, or `python3 factory`):

```text
factory audit          # L0 inspection: repos, backlog, docs drift → findings report
factory plan           # rank open agent-ready issues → recommended next task
factory run-next       # pick the smallest valuable issue and print its execution brief
factory review         # critical-review checklist + diff checks on current work
factory validate       # run deterministic gates G3–G10 (see policies/QUALITY_GATES.md)
factory release-check  # G11 release evidence (read-only; never tags or publishes)
```

`--json` is available on every command for machine consumption. The harness never
writes code, canonical data, or GitHub state by itself; `plan`/`run-next`/`review`
print instructions and briefs for the agent (you) to execute.

## Running the factory with Kimi K3

Kimi K3 (this CLI) is the factory's execution engine. Standard session:

1. **Orient.** Read `docs/factory/memory/PROJECT_MEMORY.md`, then
   `docs/factory/NORTH_STAR.md` and the three policies. Skill: `project-orientation`.
2. **Pick work.** Run `./factory plan` (or open the issue the maintainer assigned).
   Confirm the issue has Goal / Scope / Acceptance criteria / Validation command.
3. **Brief.** Run `./factory run-next` to get the execution brief: responsible agent
   definition, skills to load, files to read, gates that will apply.
4. **Load your role.** Read the agent definition in `docs/factory/agents/` that owns
   the task and the skill cards it lists. Follow them exactly.
5. **Implement** the smallest change that satisfies the acceptance criteria, with
   tests first (TDD) for behavior changes.
6. **Gate.** Run `./factory validate` (or the exact subset named in the issue).
   Fix failures; never weaken a check.
7. **Review.** Run `./factory review` and answer its checklist honestly. For L2+
   changes, re-read the patch as the Security & Critical Review agent would.
8. **Close out.** Update the issue with evidence (commands, counts, commit hashes),
   update memory docs if the work changed project truth, and open the next issue
   for anything noticed on the way.

If the task is L3 (see `policies/AUTONOMY_LEVELS.md`), stop after step 7 with a
branch, a pull request, and an issue comment requesting maintainer approval.

## Design constraints

- Reuses Python, GitHub issues, the existing CLI/services/tests, and Markdown/YAML.
- No background daemons, no databases, no new dependencies, no orchestration server.
- The harness is tested by `tests/test_factory_cli.py` like any other change.
- Everything an agent needs to know is in this repository — if it is not, the fix is
  a memory-doc update, not tribal knowledge.
