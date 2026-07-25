# Project Memory — Current State Index

> Read this first every factory session. It is the map to durable project context.
> Update it whenever the underlying truth changes (same patch as the change).
> Last verified: 2026-07-25 against Core `main` @ 65af01c and website @ fddee57.

## Product state

- Core `0.6.2` on `main`; full suite **1900 passed, 3 skipped**; ruff clean;
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
Loop runs #571–#582 completed 2026-07-24, landed 2026-07-25 (`4736cc1` code +
tests, `65af01c` docs): schema import emits MessageType/SchemaNode lineage and
request/response message links with source-registry provenance; `domain-pack`
build/validate/diff CLI; governed workbook suggestion artifacts + protected
review roundtrip in pilot preflight/bootstrap/migration-assessment. Note: the
issues were closed on GitHub a day before the code was committed — land code
first in future loops.
Open: #551 (L3 CI proposal, awaiting maintainer). Website repo:
Martenweave/martenweave.github.io#9 implemented as PR #10 (branch
`docs/schema-domain-pack-workbook-sync-9`, commit `eaa2475`; build-docs,
validate-site, and core-version-copy all green at Core 0.6.2) — awaiting
maintainer merge per the #552 publication precedent. #9 was seeded 2026-07-25
after a green `factory audit` (14/14 PASS) and Northstar 11/11 re-verification
at `ed2e284`; `agent-ready` + `priority:medium` labels now exist in the
website repo. Core #583 (agent-ready, docs-drift, priority:low): sync
`CORE_DOMAIN_MODEL.md` object groups with the 36-type `ObjectType` enum —
verified missing `Application`, `DataFlowStep`, `IntegrationFlow`,
`InterfaceEndpoint`, `MessageType`, `SAPObject`, `SchemaNode`,
`TransformationRule`; completed and closed 2026-07-25 in `796f938`
(code pushed before close, evidence comment posted). Queue: #551 (L3,
maintainer) + website PR #10 (maintainer merge) remain human-gated.
Core #584 (agent-ready, ux-clarity, priority:low): Workbench
`typeToLabel`/`objectTypeToTone` in `frontend/src/api.jsx` lack cases for
`Interface`/`InterfaceEndpoint`/`MessageType`/`SchemaNode` — verified
fallback-only rendering; completed and closed 2026-07-25 in `d42cfcd`
(62 vitest + 9 Playwright e2e green, packaged assets rebuilt).
Format gate fixed (`9461cf1` + lesson: ruff check ≠ format gate);
`release-check` fully green at `205b1ee`. Seeded #585 (agent-ready, docs:
reconcile lineage doc §10 with 44 implemented registry edge labels — 32
verified missing) — completed and closed 2026-07-25 in `50cfb61` (§10
reconciled, new interface/message/flow family, §9 example fixed); and #586
(release evidence pack, L3 maintainer checklist) — **corrected 2026-07-25:
v0.6.2 is already tagged on origin (→ 3e2aa0d) with dist/ artifacts; the
pending release is 0.7.0** covering b769b8a..20436c3 (schema-import family,
domain-pack CLI, workbook suggestions, #583-#585 docs, format fix).
Clean-clone + fresh-venv `release_smoke.sh` green at `20436c3` (evidence
comment on #586). CHANGELOG `[Unreleased]` completed for the whole landing
(`0373f48`); P7 still bars agent version-bump commits — maintainer steps are
now decide number → bump → retitle section → tag → publish. Memory previously said Core 0.6.1 — the bump to 0.6.2 shipped in
`3e2aa0d`; website @ `fdaa395` before PR #10.
