# Validation Commands — Exact Set with Expected Outputs

> The canonical command ladder for factory work, with the outputs verified on
> 2026-07-19 (Core `main` @ 8d96d25). All commands run from the Core repository
> root. If your environment produces different counts, investigate before
> proceeding — drift in these numbers is itself a finding.

## Core gates

```bash
# Lint + format
.venv/bin/ruff check .                          # "All checks passed!"
.venv/bin/ruff format --check src tests         # no diffs reported

# Tests
.venv/bin/python -m pytest -q                   # 1805 passed, 3 skipped (~110 s)

# Package build
.venv/bin/python -m build                       # dist/martenweave_core-0.6.1-{py3-none-any.whl,tar.gz}

# Release smoke (isolated venv wheel install + CLI + demo + frontend tests)
bash scripts/release_smoke.sh                   # "Release smoke checks passed"
```

## Documentation and skill structure

```bash
.venv/bin/python scripts/validate_doc_commands.py   # expected: every documented CLI command is fresh
.venv/bin/python scripts/validate_skills.py         # validates skills/ structure
```

## Northstar regression benchmark

```bash
bash scripts/demo_northstar_pilot.sh            # "Northstar synthetic pilot reproduction passed (11/11 steps)."
```

Key assertions inside (jq): validate `is_valid: true`, 0 errors, 13 warnings;
index 187 objects; gap report total 61; impact counts 71 / 55; readiness fails
with `active_object_missing_owner, high_risk_unapproved_proposal`; propose-patch
without provider refuses to guess; issue draft + git bundle (4 files) created.
Requires `jq` (`command -v jq`).

Deterministic data check:

```bash
cd examples/northstar_mobility_pilot && ../../.venv/bin/python data/generate_synthetic_data.py && cd ../..
git status --short                              # empty = byte-identical regeneration
```

## Workbench

```bash
npm --prefix frontend ci
npm --prefix frontend run build                 # vite build OK
npm --prefix frontend test                      # 55 passed (vitest)
npm --prefix frontend run test:e2e              # 8 passed (Playwright connected spec)
bash scripts/build_workbench_assets.sh          # sync packaged workbench_static after frontend changes
```

Live smoke: `.venv/bin/martenweave workbench --repo examples/northstar_mobility_pilot --no-open`
then open `http://127.0.0.1:8000`; wait for "Local workspace" before asserting
(see LESSONS_LEARNED 2026-07-19 probe race).

## Website (repo: sibling `martenweave.github.io`)

```bash
npm ci && npm run build          # "Site validation passed: 170 HTML files ..."
npm run test:render              # "Rendered site smoke check passed."
npm run test:production          # parity: deployed site == exact main commit
```

## Full clean-checkout proof

```bash
git clone --depth 50 https://github.com/metalhatscats/martenweave-core.git /tmp/mw-clean-verify
cd /tmp/mw-clean-verify && python3.11 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
bash scripts/demo_northstar_pilot.sh            # must pass 11/11 here too
```
