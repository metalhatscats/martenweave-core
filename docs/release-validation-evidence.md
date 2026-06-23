# Release Validation Evidence

Run date: 2026-06-23

Branches:

- Core: `main`
- Site: `main`

Environment:

- Python: 3.11.15
- Martenweave Core: 0.4.0
- Site server: `python3 -m http.server 4173`
- `gh` issue check: authenticated GitHub CLI

## Core Validation

| Command | Result | Evidence |
|---|---|---|
| `.venv/bin/python -m ruff check .` | Passed | `All checks passed!` |
| `.venv/bin/python -m ruff format --check .` | Passed | `209 files already formatted` |
| `.venv/bin/python -m pytest` | Passed | `1305 passed, 2 warnings in 47.91s` |
| `bash scripts/release_smoke.sh` | Passed | All bundled examples validated, indexed, checked fresh, and exercised through search, query, trace, impact, gaps, gap report, proposal dry-run, and config guard release mode |

## Config Guard

| Command | Result | Evidence |
|---|---|---|
| `.venv/bin/modelops config-guard --repo . --json` | Failed locally | Detected three potential `api_key` secrets in ignored local `.env` at lines 1, 2, and 4; no `repo_config`, `gitignore`, or `repo_secrets` findings |
| `.venv/bin/modelops config-guard --repo . --mode release --json` | Passed | Reported the same ignored `.env` findings with `file_status: "ignored"` and exited 0 |

Interpretation: default local mode still reports ignored local `.env` secrets. Release mode can pass
when findings are limited to ignored local-only files, while tracked or untracked repository secret
findings remain release-blocking.

## Public Site Validation

| Command | Result | Evidence |
|---|---|---|
| `npm run build:docs` | Passed | `Generated docs: 11 static HTML routes.` |
| `npm run validate` | Passed | `Generated docs are current: 11 routes checked.` and `Site validation passed: 13 HTML files, generated doc routes, links, sitemap, and AI discovery files are valid.` |
| `python3 -m http.server 4173` plus `curl -I http://localhost:4173/` | Passed | HTTP `200 OK`, `Content-type: text/html`, `Content-Length: 31672` |
| `curl -I http://localhost:4173/docs.html` | Passed | HTTP `200 OK`, `Content-type: text/html`, `Content-Length: 7745` |
| `curl -I http://localhost:4173/docs/quickstart.html` | Passed | HTTP `200 OK`, `Content-type: text/html`, `Content-Length: 6120` |

## License Status

- Current license: MIT in `LICENSE`.
- Package metadata: `pyproject.toml` declares `license = "MIT"`.
- MIT permits commercial use when the license notice is preserved.
- Current release-candidate recommendation: keep the core MIT and monetize optional paid pilots,
  facilitation, support, templates, and future products.
- Future dual-license or source-available non-commercial strategy: requires owner decision.

## Release Readiness Decision

The core and public site are release-candidate clean for a source/GitHub handoff: validation,
generated static docs, public links, founder/contact path, and licensing language are current.

Do not publish to PyPI until
[#411](https://github.com/metalhatscats/martenweave-core/issues/411) is closed. The issue is still
open and tracks missing PyPI trusted publisher configuration.

## Generated Artifacts

Build and smoke commands may create ignored local artifacts under:

- `examples/*/generated/`
- Python cache directories
- Site screenshot/output directories

These are rebuildable artifacts and should not be staged for release commits unless explicitly
intended as public proof assets.
