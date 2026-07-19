# Project Memory — Current State Index

> Read this first every factory session. It is the map to durable project context.
> Update it whenever the underlying truth changes (same patch as the change).
> Last verified: 2026-07-19 against Core `main` @ 8d96d25 and website @ 4c6d922.

## Product state

- Core `0.6.1` on `main`; full suite **1805 passed, 3 skipped**; ruff clean;
  wheel builds; `scripts/release_smoke.sh` green.
- Northstar synthetic pilot is the regression benchmark: 187 canonical objects,
  7 domains, 13 intentional warnings, 61 gaps, readiness not ready
  (`active_object_missing_owner`, `high_risk_unapproved_proposal`), impact counts
  71 (shared payment terms) / 55 (shared credit limit). Reproduce:
  `bash scripts/demo_northstar_pilot.sh` (11 self-verifying steps, needs `jq`).
- Workbench serves the real local API (no static demo data in connected mode);
  ledger surfaces canonical ownership since `8d96d25`.
- Website live at <https://martenweave.github.io>, production-parity tested; the
  Northstar walkthrough numbers match verified CLI output.

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

Factory skeleton created 2026-07-19: north star, policies (autonomy, gates,
preventions), workflows, this memory layer. Agent definitions, 13 skills, the
`./factory` harness, and the seeded backlog follow in the same build-out; check
`docs/factory/README.md` layout against disk before assuming a file exists.
