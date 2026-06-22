# Release Validation Evidence

Run date: 2026-06-22

Branches:

- Core: `release/first-public-rc`
- Site: `release/first-public-rc-site`

Environment:

- Python: 3.11.15
- Martenweave Core: 0.4.0
- `jq`: `/usr/bin/jq`

## Core Validation

| Command | Result | Evidence |
|---|---|---|
| `.venv/bin/python -m ruff check .` | Passed | `All checks passed!` |
| `.venv/bin/python -m ruff format --check .` | Passed | `209 files already formatted` |
| `.venv/bin/python -m pytest` | Passed | `1232 passed in 52.99s` |
| `bash scripts/smoke_test.sh` | Passed | 9 CLI commands, 35+ JSON assertions |
| `bash scripts/release_smoke.sh` | Passed | All bundled examples validated, indexed, checked fresh, and exercised through search/query/trace/impact/gaps/proposal dry-run |
| `.venv/bin/python -m build` | Passed | Built `martenweave_core-0.4.0.tar.gz` and `martenweave_core-0.4.0-py3-none-any.whl` |
| `.venv/bin/modelops assessment run --repo examples/customer_bp_model --out /tmp/martenweave-assessment-rc --json` | Passed | Produced scorecard, gap report, high-risk field register, impact reports, recommendations, and XLSX review workbook |
| `bash scripts/demo_v0_3_gap_to_proposal.sh` | Passed | Validated, indexed, profiled dataset, detected gaps, created PatchProposal, showed diff, and verified dry-run review gate |

## Config Guard

| Command | Result | Evidence |
|---|---|---|
| `.venv/bin/modelops config-guard --repo . --json` | Failed locally | Detected potential `api_key` secrets in ignored local `.env` at lines 1, 2, and 4 |
| `.venv/bin/modelops config-guard --repo . --mode release --json` | Completed | Reported the same ignored `.env` findings and no `repo_config`, `gitignore`, or `repo_secrets` findings |

Interpretation: the local `.env` file is ignored and must not be staged. This is environment-only
noise for this working copy, but the release should not be called fully clean until the maintainer
either removes/moves the local `.env` or explicitly accepts this documented local-only finding.

## Public Site Validation

| Command | Result | Evidence |
|---|---|---|
| `npm run build:docs` | Passed | Generated 10 static browser-readable docs routes |
| `npm run validate` | Passed | Checked generated docs, root assets, anchors, required copy, sitemap, AI discovery files, and public docs routes |
| `python3 -m http.server 4174` plus HTTP checks | Passed | `/`, `/docs.html`, `/docs/quickstart.html`, `/docs/product.html`, `/docs/architecture.html`, `/docs/ai-governance.html`, `/llms.txt`, `/llms-full.txt`, `/ai.json`, and `/sitemap.xml` returned HTTP 200 |

Browser-path note: the in-app Browser runtime rejected `http://127.0.0.1:4174/` under its URL
policy and crashed the tab. Static validation and HTTP route checks passed, but desktop/mobile
visual screenshots were not captured in this run. Treat browser screenshot proof as a remaining
release-candidate task unless the Browser policy is adjusted or a maintainer explicitly approves a
separate Playwright fallback run.

## Generated Artifacts

Build and smoke commands created ignored local artifacts under:

- `dist/`
- `src/martenweave_core.egg-info/`
- `examples/*/generated/`
- Python cache directories

These are rebuildable artifacts and should not be staged for the release PR.
