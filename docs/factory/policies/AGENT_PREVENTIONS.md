# Factory Policy — Agent Preventions

> Hard prohibitions for every factory agent. Each rule names its enforcement point.
> A patch that violates any rule is rejected regardless of gate results; the
> Security & Critical Review agent checks these explicitly on every review.

## Prohibitions

| # | Rule | Enforcement |
|---|---|---|
| P1 | **Never weaken tests.** No deleting/skipping tests, loosening assertions, lowering coverage floors, or editing fixtures/examples to make a failing check pass. Tests may be strengthened or rewritten to test *more*. | G3/G5 gate review; diff check in `factory review`; Security agent sign-off. |
| P2 | **Never duplicate existing functionality.** Before implementing, search the codebase (`Grep`/`Glob`), the CLI command list, and `docs/` for an existing service that already does it. Extend the existing service instead. | Implementation-planning skill checklist; architecture gate (G2). |
| P3 | **Never invent product capabilities.** Every change traces to the north star (`../NORTH_STAR.md`) and a GitHub issue with acceptance criteria. Undocumented new commands, endpoints, object types, or website claims are rejected. | Product-scope gate (G1); issue template requires the link. |
| P4 | **Never change the north star.** `docs/factory/NORTH_STAR.md`, the Core Principles in `README.md`/`AGENTS.md`, and the MVP boundaries are maintainer-owned. Agents flag drift; they do not "fix" scope. | L3 approval requirement (`AUTONOMY_LEVELS.md`). |
| P5 | **Never build forbidden product shapes.** No generic chatbot, no workflow engine, no SaaS/hosted platform, no auth/RBAC, no SAP write-back, no new infrastructure classes (message queues, graph DBs, schedulers, plugin systems). The factory itself is documentation plus one stdlib Python harness — no orchestration platform. | G1/G2 gates; Security agent veto. |
| P6 | **Never modify canonical model data without review.** `model/` files in any example or repository change only via the product path (`PatchProposal` → approval → `ChangeRequest`). The factory harness, skills, and tests must not write to `model/` directories. | Code review + existing `patching/` safety tests; L3 for any fixture change. |
| P7 | **Never publish releases automatically.** No `git tag`, no PyPI upload, no version bump commit without explicit maintainer instruction. `release.yml` stays tag-triggered by a human. | L3 approval; `factory release-check` is read-only. |
| P8 | **Never touch protected paths without L3 approval.** `.github/workflows/`, `LICENSE`, `NOTICE`, `pyproject.toml` metadata (name/license/classifiers), `.env*`, secrets, and `generated/` artifacts (rebuild instead of editing). | Diff check in `factory review`; AGENT_LOOP_CHECKLIST alignment. |
| P9 | **Never fabricate evidence.** Claims in issues, docs, website, and closeouts must come from commands actually run in the session, with counts quoted exactly. Unverified work is reported as unverified. | Closeout report template; website-claim-verification skill. |
| P10 | **Never expand session scope.** Work on the selected issue only. Noticed a side problem? File a new issue; do not fold it into the current patch. | `factory run-next` brief; review checklist. |

## Violation handling

1. Stop work on the patch immediately.
2. Record the violation and evidence in the issue.
3. If the violation came from ambiguity in these rules, open a `factory`-labeled issue
   proposing a policy clarification (L3 — maintainer decides).
4. Revert any committed violating change with `git revert` and note the revert hash.
