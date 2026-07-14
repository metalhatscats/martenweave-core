# GitHub Issue Reconciliation Audit

> **Scope:** `metalhatscats/martenweave-core`  
> **Audited commit:** `origin/main` @ `a8992d6f146e91e62c5dc363be884b6c14f61a28`  
> **Audit date:** 2026-07-14

## Summary

This audit reconciled every open issue and open pull request, plus all issues closed after 2026-07-01, against the actual state of `main`. The goal was to ensure GitHub issue/PR states reflect what is really implemented, tested, and documented on `origin/main`.

**No backlog was implemented during this task.** Only inspection, classification, commenting, and state corrections were performed.

## Items Inspected

| Category | Count | Numbers |
|---|---|---|
| Open issues | 33 | #518, #517, #516, #515, #514, #513, #512, #511, #510, #509, #508, #507, #506, #505, #504, #503, #502, #501, #500, #499, #498, #497, #496, #495, #493, #492, #491, #489, #434, #430, #428, #427, #416 |
| Open PRs | 20 | #538, #537, #536, #535, #534, #533, #532, #531, #530, #529, #528, #527, #526, #525, #524, #523, #522, #521, #520, #519 |
| Recently closed issues (closed after 2026-07-01) | 25 | #494, #490, #488, #487, #486, #485, #483, #484, #482, #477, #476, #475, #474, #473, #472, #471, #467, #456, #455, #453, #449, #448, #435, #431, #429 |
| **Total inspected** | **78** | — |

## Classification Method

For each item, the audit:

1. Read the issue/PR body and acceptance criteria.
2. Inspected `origin/main` code, tests, docs, CLI help, and frontend source.
3. Ran focused tests or validation commands from the issue/PR body.
4. Classified each item as: `implemented`, `partially-implemented`, `not-implemented`, `duplicate`, `obsolete`, or `blocked`.

Evidence was required to include file paths, test names, command output, commit SHAs, or PR numbers. Classifications were **not** based on commit messages, file existence, mocks, or documentation claims alone.

## Issues Reopened

Eight recently-closed issues were reopened because important acceptance criteria are still missing on `origin/main`.

| Issue | Title | Reason |
|---|---|---|
| #485 | Define a pilot-first product roadmap and scope guardrails | `docs/product/ROADMAP_PILOT.md` does not exist on `main`; implementing commit `c5cbb27` is on unmerged branch `batch/1-pilot-roadmap-assessment`. |
| #486 | Add one-command SAP migration assessment workflow | `run migration-assessment` command and `src/modelops_core/run/migration_assessment.py` do not exist on `main`; implementing commits `63f459d`, `910771e` are on unmerged branch. |
| #487 | Add a realistic SAP mapping workbook pilot fixture and golden assessment test | `tests/fixtures/pilot/` and `tests/test_pilot_mapping_workbook.py` do not exist on `main`; implementing commits are on unmerged branch `batch/2-pilot-mapping-fixture`. |
| #488 | Add a design-partner pilot runbook and outcome report template | `docs/pilots/design-partner-runbook.md` does not exist on `main`; implementing commit `f0f5a9b` is on unmerged branch. |
| #490 | Add human disposition workflow for assessment findings | `assessment-review` command and `src/modelops_core/pilot/review.py` do not exist on `main`; implementing commit `6d59c9e` is on unmerged branch `batch/4-assessment-review`. |
| #494 | Add pilot input privacy preflight before assessment execution | `pilot-preflight` command and `src/modelops_core/pilot/preflight.py` do not exist on `main`; implementing commits `45c1a30`, `b3449ed` are on unmerged branch `batch/3-pilot-preflight`. |
| #477 | Add model summary report command | Command and service exist, but the full-repository Markdown path crashes with `AttributeError: 'FieldEndpointSummary' object has no attribute 'field_name'`. |
| #449 | [MEDIUM] Update AGENTS.md to reflect v0.4.0 module and command surface | `AGENTS.md` CLI Usage example list is still stale relative to `modelops --help` on `main`. |

Each reopened issue received an evidence comment before the state change.

## Issues Closed During This Audit

No open issues or PRs were closed as completed, duplicate, or obsolete during this audit, because none of the 53 open items were fully satisfied on `origin/main`.

## Real Remaining Backlog

After reopening the prematurely closed issues, the repository now has **41 open issues** and **20 open PRs**.

### Open issues not implemented on `main`

These issues have no implementation (or only unrelated infrastructure) on `origin/main`:

#518, #516, #513, #507, #506, #505, #504, #503, #499, #498, #497, #496, #495, #493, #492, #491, #489, #485, #486, #487, #488, #490, #494, #428, #434, #430, #416

### Open issues partially implemented on `main`

These issues have real backend or CLI foundations, but important acceptance criteria remain open (mostly frontend/UI wiring or missing safety/receipt features):

| Issue | What is present | What is missing |
|---|---|---|
| #517 | Core proposal-only write boundary; imports/gaps produce PatchProposals | `SourceState` enum, `source_state` API labels, UI badges, architecture doc transitions |
| #515 | Schema-version metadata, `migrate --dry-run`, basic migration registry | Empty `MIGRATIONS` registry, no backup/Git checkpoint, no rollback, no compatibility-range policy |
| #514 | Pre/post validation, in-memory rollback, idempotency guard, audit events | Isolated staging copy, atomic file replacement, Git checkpoint, dedicated write-receipt artifact |
| #502 | Backend `review-pack create`, export services | Frontend `/reports` API and UI wiring, reviewed-workbook return/preview/proposal flow |
| #501 | Backend proposal API (`/proposals`, validate, dry-run, apply), approval gates | Frontend proposal screen live data, diff preview, apply receipt, refresh |
| #427 | `export-model --business-review`, `import-model-sheet` round-trip | `import-excel-review` alias, `export-model --out`, strict error handling for invalid IDs |
| #477 | `model-summary` command and service | Full-repo Markdown renderer (`FieldEndpointSummary.field_name` bug) |
| #449 | Module list and version updated in `AGENTS.md` | CLI Usage command list still stale |

### Open PRs

All 20 open PRs remain open. Their changes are **not** on `origin/main`. Many are stacked dependencies that should land in order.

| PR | Linked issue(s) | Status vs `main` | Notes |
|---|---|---|---|
| #519 | #485, #486, #488 | not-implemented | Pilot roadmap, assessment command, runbook |
| #520 | #487 | not-implemented | Mapping workbook fixture and golden test |
| #521 | #494 | not-implemented | Pilot-preflight command |
| #522 | #490 | not-implemented | Assessment-review disposition workflow |
| #523 | #518 | not-implemented | Executive summary command |
| #524 | #508 | not-implemented | Workbench as official product surface (docs) |
| #525 | #510 | not-implemented | API workspace/filesystem boundary |
| #526 | #491, #493 | not-implemented | Assessment sanitize and pilot-outcome |
| #527 | #489 | not-implemented | Bootstrap-assessment command |
| #528 | #495 | not-implemented | Deterministic demo bundle |
| #529 | #496 | not-implemented | User scenario catalog |
| #530 | #428 | not-implemented | SAP BP/Customer/Vendor reference model |
| #531 | #427, #430 | partially-implemented | Excel round-trip present; evidence ingest missing |
| #532 | #497 | not-implemented | Versioned `/api/v1` contract |
| #533 | #492 | not-implemented | Frontend API wiring for Models/Object |
| #534 | #500 | not-implemented | Frontend Lineage wiring |
| #535 | #511, #512 | not-implemented | Finding provenance and run identities |
| #536 | #509 | not-implemented | One-command workbench launch |
| #537 | #517 | partially-implemented | Source-state classification missing on `main` |
| #538 | #434 | not-implemented | Scenario templates |

### Closed issues verified and kept closed

The following 17 recently closed issues were confirmed as implemented on `origin/main`:

#483, #484, #482, #476, #475, #474, #473, #472, #471, #467, #456, #455, #453, #448, #435, #431, #429

## Duplicates and Obsolete Tasks

No issues or PRs were classified as duplicate or obsolete during this audit.

## Validation Results

Final validation was run from a clean `origin/main` worktree using the repository's existing `.venv`:

```bash
cd .worktrees/verify-main
/Users/dzmitryikharlanau/Developments/martenweave/.venv/bin/python -m pytest tests/ --ignore=tests/test_docs_build.py -q
/Users/dzmitryikharlanau/Developments/martenweave/.venv/bin/python -m ruff check .
```

| Check | Result |
|---|---|
| pytest (excluding `test_docs_build.py`) | **1459 passed, 3 skipped, 7 warnings** |
| ruff | **All checks passed** |

`tests/test_docs_build.py::test_docs_first_15_minutes_filenames_match_disk` is a known pre-existing failure on `main` (references `/tmp/mw-readiness` path not present on disk) and was excluded.

## Recommended Execution Order

1. **Merge the stacked pilot foundation first** — #519 → #520 → #521 → #522 → #523. These reopen six prematurely closed issues and unblock most pilot functionality.
2. **Close the CLI monolith split (#416)** early, because it will conflict with every new CLI command being added.
3. **Land backend/API contracts before frontend wiring** — #532 (`/api/v1`) must precede #533 (Models/Object UI) and #534 (Lineage UI), which must precede #536 (workbench launch).
4. **Land security boundary before workbench launch** — #525 (API workspace boundary) before #536.
5. **Resolve small partial defects quickly** — #477 (`FieldEndpointSummary.field_name` bug) and #449 (stale `AGENTS.md` CLI list) are low-risk fixes that can close two reopened issues.
6. **Then tackle remaining backend features** — #526, #527, #528, #530, #531, #535, #538.
7. **Finally wire the remaining UI screens** — #499, #498, #502, #501, #504, #503, #507, #506, #505, #516.

## Audit Artifacts

- This document: `docs/audits/github-issue-reconciliation.md`
- GitHub state changes: 8 issues reopened with evidence comments; 6 partial issues received gap comments.
