# Lessons Learned

> Dated, durable lessons from completed work — newest first. Record what a future
> agent would otherwise have to rediscover. One entry per lesson, with evidence.

## 2026-07-19 — Dogfood the planner immediately; ranking rules drift from reality fast

The factory planner's first live run exposed two ranking gaps within minutes:
`type:*` labels unmapped to classes, and L3-blocked issues recommended as next
work. Both were invisible in fixture tests and obvious against the real backlog.
**Lesson: after building any queue/ranking tool, run it against the live backlog
before trusting it; fixture data never has the awkward cases (an issue whose body
discusses L3 triggered the naive L3 marker — declarations must be explicit:
`(L3` in title or `Autonomy: L3` line).**

## 2026-07-19 — Maintainer priority labels are the steering wheel

The planner originally ranked purely by work class, ignoring `priority:*` labels
— so a `priority:low` cosmetic bug outranked a `priority:high` doc-drift task.
**Lesson: in an autonomous queue, the maintainer's explicit signals (priority
labels, L3 declarations) must dominate every default heuristic; that is what
"minimal maintainer involvement" means — rare interventions, always honored.**

## 2026-07-19 — Never quote gate counts you did not observe

A gate run piped through `tail -4` kept only the summary; a commit message then
quoted an inferred pytest count. It was almost certainly right (1815 + 2 new
tests) but was not observed — a P9 violation in spirit. Caught and amended before
push. **Lesson: capture gate output fully (the harness `--json` keeps tails per
gate), and quote only numbers visible in the log; "green" is a fine claim when
the count is not at hand.**

## 2026-07-19 — Verify before building: most of the "pilot readiness" goal already existed

A prior-session audit would have been enough: the Northstar pilot, demo script,
website walkthrough, and meta files were already on `main`. The session's real
gaps (Workbench ownership not surfaced, README omission) only appeared by running
the product and comparing UI against CLI (`martenweave owners` 90% coverage vs
ledger "Unassigned" everywhere). **Lesson: run the product as a user and compare
surfaces before writing a task list; CLI truth and UI truth drift silently.**

## 2026-07-19 — The Workbench "Demo mode" paint is a probe race, not a bug

Browser snapshots taken immediately after page load show "Demo mode / API
unavailable" even when the API is healthy — the capabilities probe resolves a
moment later and the UI flips to connected. Two consecutive snapshots (or waiting
for "Local workspace") give the truth. **Lesson: when smoke-testing the Workbench,
wait for the connected marker before asserting anything.** (Recorded as a known
limitation, not fixed.)

## 2026-07-19 — Website numbers must be captured from CLI ground truth, not remembered

The walkthrough's claims (187 objects, 13 warnings, 61 gaps, 71/55 impact counts)
were reconciled by re-running `validate`/`gap-report`/`impact --json` and comparing
each number. They all matched — but the check is what makes the page trustworthy.
**Lesson: every quantitative public claim gets re-verified against command output
in the same session that touches the page.**

## 2026-07-19 — Packaged Workbench assets are a second build artifact that must be committed

`martenweave workbench` serves `frontend/dist` in a dev checkout but
`src/modelops_core/workbench_static` in an installed wheel. A frontend fix that
skips `bash scripts/build_workbench_assets.sh` ships stale assets in the package.
**Lesson: frontend change → rebuild assets → commit both copies in one commit.**

## 2026-07-19 — Deterministic data generators earn their keep

The Northstar CSV/XLSX generator (fixed seed, pinned XLSX zip dates) regenerates
byte-identical files, so `git status` after regeneration is a valid regression
check. **Lesson: any new synthetic fixture must be byte-deterministic and checked
exactly this way.**
