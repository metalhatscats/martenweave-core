# Factory Policy — Deterministic Quality Gates

> Every factory patch runs the gates below. Gates are **deterministic** — commands
> with pass/fail exit codes — except G1–G3, which are checklist gates executed by
> the responsible agent and verified by the Security & Critical Review agent.
> All commands run from the Core repository root with the repo-local venv
> (`.venv/bin/...`) unless noted. This file is the human-readable contract;
> `factory validate` (see `../README.md`) executes G3–G10, and
> `factory release-check` adds G11.

## Gate map

| # | Gate | Type | Command / evidence |
|---|---|---|---|
| G1 | **Product-scope** | checklist | Change is traceable to `../NORTH_STAR.md` scope; does not add a non-goal (chatbot, workflow engine, SaaS, SAP write-back, auth). Evidence: issue states the north-star link; reviewer confirms. |
| G2 | **Architecture consistency** | checklist | Consistent with `docs/architecture/ARCHITECTURE_DECISIONS.md` and boundary docs (`CANONICAL_MODEL_BOUNDARY.md`, `WORKBENCH_BOUNDARY.md`, `GENERATED_INDEX_BOUNDARY.md`, `INTEGRATION_BOUNDARIES.md`). No new component duplicates an existing service. Evidence: reviewer notes which ADRs/boundaries were checked. |
| G3 | **Security and privacy** | mixed | `.venv/bin/python -m pytest tests/test_secret_guardrails.py -q` plus checklist: no secrets committed, no new network calls, no PII in fixtures, guardrails unchanged or strengthened. |
| G4 | **Schema and compatibility** | command | `.venv/bin/martenweave validate --repo <each example>` for all 8 bundled examples (see `.github/workflows/ci.yml` for the list) — `is_valid: true`, 0 errors. |
| G5 | **Unit and integration tests** | command | `.venv/bin/python -m pytest -q` — full suite green. New behavior ships with tests; coverage floor 70% (CI enforces), 90% on critical paths. |
| G6 | **Ruff and package build** | command | `.venv/bin/ruff check .` and `.venv/bin/ruff format --check src tests`; `.venv/bin/python -m build` succeeds. |
| G7 | **API and MCP contract tests** | command | `.venv/bin/python -m pytest tests/test_api_contract.py tests/test_api.py tests/test_mcp_server.py -q` |
| G8 | **Northstar regression** | command | `bash scripts/demo_northstar_pilot.sh` — all 11 steps pass; canonical model stays valid; intentional problems still surface (61 gaps, 13 warnings, readiness not ready). |
| G9 | **Workbench build and smoke** | command | `npm --prefix frontend ci && npm --prefix frontend run build && npm --prefix frontend test`; for UI-affecting changes also `npm --prefix frontend run test:e2e` and `bash scripts/build_workbench_assets.sh` so packaged assets stay current. |
| G10 | **Documentation and website consistency** | command | `.venv/bin/python scripts/validate_doc_commands.py` and `.venv/bin/python scripts/validate_skills.py`; when website files change: in the website repo `npm ci && npm run build && npm run test:render` and after deploy `npm run test:production`. Website claims must match verified Core behavior (skill: `website-claim-verification`). |
| G11 | **Release readiness** | command | `bash scripts/release_smoke.sh`; plus `.venv/bin/python scripts/release_preflight.py` when a version bump is being prepared. |

## Rules

1. **Gate selection.** Every patch runs G1–G3, G5, G6, G10. G4, G7, G8, G9 run when
   the patch touches their surface (schemas/validation, API/MCP, demo paths, frontend)
   — but `factory validate` always runs the full set so a wrong selection cannot
   hide a regression. G11 runs before any release decision and on `factory release-check`.
2. **Never weaken a gate to pass it.** Deleting a test, lowering coverage, skipping a
   step, or editing fixture data to make a check pass is a policy violation
   (`AGENT_PREVENTIONS.md` P1) and blocks the patch.
3. **Evidence.** The patch description (commit message or PR body) lists the gates
   run and their results: command → pass/fail → counts (e.g. `pytest: 1805 passed`).
4. **Environment.** Use `.venv/bin/...` binaries. Frontend commands need Node/npm;
   the Northstar script needs `jq`. Missing tools are a blocker to report, not to
   work around.
