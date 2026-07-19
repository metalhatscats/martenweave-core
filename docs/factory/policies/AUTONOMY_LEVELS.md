# Factory Policy — Autonomy Levels

> Binding policy for every factory agent run. Maps each change class to the maximum
> action an agent may take without explicit maintainer approval. Complements the
> runtime AI permission policy (`docs/ai/ai-permission-policy.md`, tiers 0–4), which
> governs canonical model mutations; this file governs **repository changes**
> (code, tests, docs, config, website).

## Levels

| Level | Change class | Agent may | Human must |
|---|---|---|---|
| **L0 — Inspect** | Read code, docs, issues, artifacts; run validations; produce findings. | Always, unsupervised. | — |
| **L1 — Polish** | Typo/clarity fixes in docs, comment/docstring corrections, test readability, dead-code removal in tests. No behavior change, no public text (website/README) meaning change. | Implement + commit after **all gates pass** (see `QUALITY_GATES.md`). | Review asynchronously via git history. |
| **L2 — Fix** | Bug fixes with a regression test; error-message improvements; performance fixes with no interface change; dependency patch bumps that pass CI; doc synchronization with verified behavior. | Implement + commit after all gates pass **and** the critical-review checklist (`factory review`) is clean. | Review asynchronously. |
| **L3 — Guarded** | New features; schema/object-model changes; API or MCP contract changes; security boundaries; licensing; CI workflow changes; destructive migrations; dependency major bumps; releases and version bumps; north-star or policy changes; canonical model data changes; public website claims about new capabilities. | Prepare a branch + patch + issue update + evidence. **Stop.** | Explicit approval before merge. |

## Rules

1. **Default branch policy.** Factory work happens on a feature branch with a pull
   request referencing the issue (`gh issue develop` or manual). Direct commits to
   `main` happen only when the maintainer explicitly instructs it for that session;
   the instruction is recorded in the issue and the session closeout.
2. **Gate ordering.** No commit happens before the applicable gates pass. A failing
   gate blocks, never "warns".
3. **Escalation is cheap.** When classification between L2 and L3 is unclear, treat
   the change as L3. Record the question in the issue for the maintainer.
4. **Releases are never automatic.** `release.yml` runs only on maintainer-pushed
   `v*` tags. `factory release-check` is read-only evidence gathering.
5. **Canonical model data** (anything under `model/` in any example or user repo)
   follows the product rule: changes arrive only via reviewed `PatchProposal` →
   approved `ChangeRequest`. The factory never edits canonical data directly — not
   even "to fix a typo". Intentional pilot fixtures are canonical data too.
6. **Rollback.** Every L1/L2 auto-commit must be revertable with a single
   `git revert <hash>`; the hash is recorded in the issue closeout.

## Autonomy ceiling per agent

| Agent | Ceiling |
|---|---|
| Product & Architecture | L0 (analysis, issues, ADR drafts) |
| Core Development | L2 |
| AI & MCP | L2 (L3 for any contract change) |
| SAP/MDM Domain Quality | L2 in code/tests; **L3 for canonical data** |
| Testing & Release | L2 (release itself is always L3) |
| Documentation & Website | L2 in Core docs; **L3 for website capability claims** |
| Security & Critical Review | L0 (veto power: can block any patch) |
