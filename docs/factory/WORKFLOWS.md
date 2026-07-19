# Factory Workflows — Loop, Patch Lifecycle, Recovery

> Operating procedures for factory runs. Read after `README.md` and the policies.
> The loop is executed by a Kimi agent using the `./factory` harness and the skills;
> the harness enforces determinism, the agent exercises judgment inside it.

## 1. The autonomous loop

```text
inspect repositories → compare with product north star → detect verified gaps →
create or update issues → select the smallest valuable task → produce a patch →
run deterministic gates → perform critical review → update documentation and
website → merge or request human approval → continue
```

Stage by stage:

1. **Inspect** (`factory audit`, L0). Run validations, test suite, doc checks,
   website checks; read open issues; skim recent commits. Output: findings with
   evidence (command → result), each marked `verified` (reproduced) or `suspected`.
2. **Compare with north star.** For each finding, ask: is this in scope per
   `NORTH_STAR.md`? Is it already a known limitation (`memory/KNOWN_LIMITATIONS.md`)
   or a rejected idea (`memory/REJECTED_IDEAS.md`)? Drop findings that fail this —
   and record why in memory if the decision was non-obvious.
3. **Detect verified gaps.** Only `verified` findings become gaps. A gap needs:
   what is true now (evidence), what should be true (north star/docs reference),
   and why it matters to a primary user.
4. **Create or update issues.** One gap → one issue using the `agent_task`
   structure: Goal, Scope, Acceptance criteria, Validation command, plus Out of
   scope and Safety notes. Check for duplicates first (`gh issue list`, search
   terms). Update existing issues rather than opening near-duplicates.
5. **Select the smallest valuable task** (`factory plan` → `factory run-next`).
   Ranking: (a) correctness/trust bugs in shipped behavior, (b) doc/claim drift,
   (c) test/CI health, (d) small UX clarity wins, (e) everything else. Within a
   class, smallest first. Never skip the queue to work on something unfiled.
6. **Produce a patch.** Follow the responsible agent definition + skills. TDD for
   behavior changes: failing test → minimal implementation → green. Keep the diff
   scoped to the issue (P10).
7. **Run deterministic gates** (`factory validate`). All applicable gates pass, or
   the patch does not proceed. Fix causes, not checks (P1).
8. **Critical review** (`factory review`). Re-read the diff as the Security &
   Critical Review agent: preventions P1–P10, gates G1–G3 checklists, scope,
   necessity. Findings block until resolved or explicitly waived by the maintainer.
9. **Update documentation and website.** If behavior changed, docs change in the
   same patch (documentation-synchronization skill). Website changes only after the
   implementation is verified (website-claim-verification skill).
10. **Merge or request approval.** L1/L2: commit (branch+PR by default; `main` only
    on explicit maintainer instruction) with the gate evidence in the message. L3:
    open PR, comment on the issue requesting approval, **stop**.
11. **Continue.** Close out the issue (evidence, hashes), update memory docs, loop
    back to 1 or 5.

## 2. Patch lifecycle states

```text
draft (local changes)
  → gated (factory validate green)
  → reviewed (factory review clean)
  → shipped (L1/L2: merged; evidence posted) | awaiting-approval (L3: PR open)
  → closed (issue updated, memory synced)
```

Every transition is recorded in the issue. A patch that fails any gate goes back to
`draft`; a patch abandoned mid-way gets an issue comment with state and blockers so
the next agent can resume (see recovery below).

## 3. Human approval points (always L3)

- New features, new CLI commands, new API/MCP surface.
- Schema, object-model, or registry changes.
- Security boundaries, guardrail changes, secret handling.
- Licensing (`LICENSE`, `NOTICE`, headers, dependency license changes).
- Destructive migrations or data loss risks.
- Releases: version bumps, tags, PyPI, release notes.
- North star, factory policies, agent definitions' scope sections.
- Canonical model data changes (must also follow the product PatchProposal path).
- Public website capability claims.

## 4. Recovery rules

| Situation | Recovery |
|---|---|
| Session interrupted mid-task | Leave the working tree as-is; comment on the issue with: state (`draft`/`gated`), what is done, exact next step, and any failing gate output. Never force-push or delete the branch. |
| A gate fails for environmental reasons (missing tool, network) | Report the environment gap in the issue; do not skip the gate. Retry once after fixing the environment. |
| `main` moved under the branch | Rebase or merge `main` into the feature branch; re-run `factory validate`; never force-push shared branches. |
| Patch turns out bigger than the issue | Stop. Split: land the in-scope part, file follow-up issues for the rest. |
| Review finds a prevention violation | Follow `policies/AGENT_PREVENTIONS.md` → Violation handling. |
| Factory harness itself broken | Fix the harness as an L2 task with `tests/test_factory_cli.py` coverage; harness bugs are always queue-top priority because everything depends on them. |
| Two sessions conflict on one issue | The issue is the lock: comment before starting (`taking this`), and do not start an issue someone commented on in the last 24h without maintainer direction. |

## 5. Session closeout (required)

Post to the issue (and mirror into `memory/LESSONS_LEARNED.md` when there is a
durable lesson):

- What changed: files + commit hash(es).
- Gates run: each command and its exact result counts.
- Review outcome: checklist answers, waivers (none without maintainer).
- Follow-ups: new issues created (numbers).
- Anything the next agent must know.
