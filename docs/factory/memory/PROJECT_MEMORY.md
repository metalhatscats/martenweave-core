# Project Memory — Current State Index

> Read this first every factory session. It is the map to durable project context.
> Update it whenever the underlying truth changes (same patch as the change).
> Last verified: 2026-07-19 against Core `main` @ 02206ce9 and website @ fddee57.

## Product state

- Core `0.6.1` on `main`; full suite **1823 passed, 3 skipped**; ruff clean;
  wheel builds; `scripts/release_smoke.sh` green (also from a clean clone +
  fresh venv on 2026-07-19).
- Northstar synthetic pilot is the regression benchmark: 187 canonical objects,
  7 domains, 13 intentional warnings, 61 gaps, readiness not ready
  (`active_object_missing_owner`, `high_risk_unapproved_proposal`), impact counts
  71 (shared payment terms) / 55 (shared credit limit). Reproduce:
  `bash scripts/demo_northstar_pilot.sh` (11 self-verifying steps, needs `jq`;
  11/11 verified from a clean clone 2026-07-19).
- Workbench serves the real local API (no static demo data in connected mode);
  ledger surfaces canonical ownership since `8d96d25`. Since `02206ce9`: no demo
  paint while the capabilities probe is pending (#550), ledger fits 1280px
  viewports (#549); 59 vitest + 9 Playwright e2e green.
- Website live at <https://martenweave.github.io>, production-parity tested; the
  Northstar walkthrough numbers match verified CLI output. Public claims
  re-verified 2026-07-19 (`fddee57`): homepage proof block matches real CLI
  output (89 objects, 59/59 ownership, first gap `ATTR-BP-CENTRAL-LEGAL-FORM`);
  stale 0.5.0 claims fixed site-wide; site validator now also covers 7 extra doc
  routes, version claims in living docs + JSON-LD, and Markdown private paths.
  `inbox/` removed from the tree (history-purge decision tracked as a website
  issue).

## Where the truth lives

| Topic | Source |
|---|---|
| Product scope / north star | `docs/factory/NORTH_STAR.md` (+ `docs/product/MVP_SCOPE.md`) |
| Architecture decisions | `docs/architecture/ARCHITECTURE_DECISIONS.md` + boundary docs |
| Agent operating rules (runtime AI) | `docs/ai/` (permission tiers, safety rules, validation ladder) |
| Factory policies | `docs/factory/policies/` |
| Work queue | GitHub issues (`agent-ready` label) — not this file |
| Known limitations | `docs/factory/memory/KNOWN_LIMITATIONS.md` |
| Rejected ideas | `docs/factory/memory/REJECTED_IDEAS.md` |
| Lessons from past work | `docs/factory/memory/LESSONS_LEARNED.md` |
| Exact validation commands | `docs/factory/memory/VALIDATION_COMMANDS.md` |

## Open structural facts agents must respect

- `generated/` in every repo is disposable output — never edit, never commit fixes
  into it; rebuild instead.
- `.github/workflows/` is L3 (maintainer-only) territory.
- The Workbench has two asset copies: `frontend/dist` (dev) and
  `src/modelops_core/workbench_static` (packaged). After any frontend change run
  `bash scripts/build_workbench_assets.sh` and commit the packaged copy.
- `scripts/validate_doc_commands.py` checks every `modelops <cmd>` snippet in
  README/docs against the real CLI — keep doc commands real or mark them
  `<!-- modelops-freshness-ignore -->`.
- `scripts/validate_skills.py` enforces skill structure; new skills must be added
  to its `REQUIRED_SKILLS` list and to `skills/README.md`.
- Both GitHub repos had **zero open issues** when the factory was created
  (2026-07-19); the backlog is seeded by factory audits from then on.

## Current factory build status

Factory build-out completed 2026-07-19 (commits `19730d0`, `13cabe0`, `16168d5`,
`cb29c1a`): north star, policies (autonomy L0–L3, gates G1–G11, preventions
P1–P10), workflows, 7 agent definitions, 5 memory docs, 13 factory skills (24
skills total, all structurally validated), the stdlib `./factory` harness
(audit/plan/run-next/review/validate/release-check, 12 tests), and a live GitHub
backlog seeded from verified audit findings (first issues #546–#554).

Planner conventions (verified by dogfooding): maintainer `priority:*` labels
dominate ranking; classes order correctness → docs-drift → test-ci → ux-clarity;
issues declaring L3 (`(L3` in title or `Autonomy: L3` body line) are listed but
never recommended. Loop runs completed with gate evidence: #553, #546, #554,
#547 (`355440f`), #548 (`6ae5a36`), #552 (`866d453` website repo — factory
guide live at /docs/ai-factory.html, maintainer-approved), #549 + #550
(`02206ce9` — pilot-readiness consistency pass with website `fddee57`;
20/20 factory gates + clean-env Northstar 11/11 + release smoke).
Open: #551 (L3 CI proposal, awaiting maintainer).
