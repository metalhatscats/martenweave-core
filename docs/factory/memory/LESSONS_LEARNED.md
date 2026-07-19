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

## 2026-07-19 — Commit the complete generated set; globs lie by omission

The website "Validate site" CI job failed on `866d453` because
`git add docs/*.html` missed `docs/search-index.json` and `docs/use-cases/*.html`
— the docs-currency check compares committed generated files against sources.
The Pages deploy succeeded anyway, so the failure was only visible in CI.
**Lesson: after any build that regenerates artifacts, `git status` is the add
list — never a hand-written glob. For the website repo that means all of
`docs/**` (including subdirectories and `search-index.json`) plus `sitemap.xml`;
then run `npm run validate` locally before pushing, because it is exactly what
the workflow runs.**

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

## 2026-07-19 — The probe-race lesson graduated from known limitation to fix

The "Demo mode paint is a probe race" entry above was first recorded as a known
limitation; it is fixed in `02206ce9` (#550, plus the 1280px ledger clip #549):
the provider starts non-demo, every read hook short-circuits the pending state to
a neutral loading state, and a Playwright viewport spec + a never-resolving-probe
unit test lock the behaviour. **Lesson: known limitations need a re-check date —
pilot-facing cosmetic races become credibility bugs the moment a real user demo is
scheduled.**

## 2026-07-19 — Validators must not enshrine the claims they check

`validate-site.mjs` pinned the homepage proof string
`ATTR-BP-CENTRAL-FOUNDATION-DATE` — when the example model changed, both the copy
and the validator were stale together, and CI stayed green. It also checked
version strings only in the AI discovery files, so `docs/*.md`, blog HTML, and
JSON-LD drifted to 0.5.0 while llms.txt/ai.json were correct. **Lesson: required
strings in validators age exactly like the copy they guard — re-derive them from
verified command output, and extend claim checks to every surface that carries
the claim (docs, blog, structured data).**

## 2026-07-19 — Some CLI commands intentionally write into the example repo

`martenweave agent readiness` persists readiness blockers as
`model/issues/ISS-READINESS-*` objects — running it (directly or via
`scripts/validate_doc_commands.py`) leaves untracked files in
`examples/*/model/`. **Lesson: after local validation runs, check `git status`
for untracked example artifacts and clean them before committing; never commit
generated readiness issues into the checked-in examples.**
