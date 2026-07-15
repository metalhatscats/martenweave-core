# Release Validation Evidence

## Martenweave Core 0.6.0

Run date: 2026-07-15

Branches:

- Core: `main`
- Site: `main`

Environment:

- Python: 3.11.15
- Martenweave Core: 0.6.0
- `gh` issue check: authenticated GitHub CLI

### Core Validation

| Command | Result | Evidence |
|---|---|---|
| `.venv/bin/martenweave --version` | Passed | `martenweave-core 0.6.0` |
| `.venv/bin/python -m ruff check src tests` | Passed | `All checks passed!` |
| `.venv/bin/python -m ruff format --check .` | Passed | `294 files already formatted` |
| `.venv/bin/python -m pytest` | Passed | `1796 passed, 3 skipped, 7 warnings in 92.93s` |
| `bash scripts/smoke_test.sh` | Passed | `Smoke Test Complete — All JSON contracts stable` |
| `bash scripts/release_smoke.sh` | Passed | `Release smoke checks passed` — all bundled examples validated, indexed, checked fresh, and exercised through search, query, trace, impact, gaps, gap report, proposal dry-run, docs-build, config guard release mode, and frontend tests |
| `.venv/bin/martenweave config-guard --repo . --mode release --json` | Passed | Reported ignored local `.env` and generated frontend findings with `file_status: "ignored"` and exited 0 |
| `.venv/bin/python scripts/validate_doc_commands.py` | Passed | `All documented modelops commands are fresh.` |
| `.venv/bin/python -m build` | Passed | Produced `martenweave_core-0.6.0.tar.gz` and `martenweave_core-0.6.0-py3-none-any.whl`; wheel METADATA reports `Version: 0.6.0` |

### Frontend Validation

| Command | Result | Evidence |
|---|---|---|
| `cd frontend && npm test -- --run` | Passed | `52 passed` |
| `cd frontend && npm run build` | Passed | Production bundle emitted to `frontend/dist/` |
| `cd frontend && npm run test:e2e` | Passed | `8 passed` |

### Website Validation

| Command | Result | Evidence |
|---|---|---|
| `npm run build` | Passed | `35 static HTML routes`; search index generated |
| `npm run validate` | Passed | `33 HTML files, generated doc routes, links, sitemap, and AI discovery files are valid` |
| `npm run test:render` | Passed | `Rendered site smoke check passed.` |

### Package Metadata

- `pyproject.toml` declares `version = "0.6.0"`.
- `src/modelops_core/__version__.py` declares `__version__ = "0.6.0"`.
- Built wheel and sdist filenames include `0.6.0`.
- Wheel METADATA reports `Version: 0.6.0`.

### License Status

- Current supported release and active development use Apache License 2.0.
- Version 0.4.1 was originally distributed under MIT; existing copies retain those terms.

### Tag Safety

- Remote `v0.4.0` and `v0.4.1` tags exist and point to older commits; they are intentionally not reused, moved, deleted, or force-updated.
- `v0.6.0` is the safe Apache-licensed release from the validated `main` commit.

### Release Readiness Decision

The core is release-clean for source/GitHub and PyPI handoff: validation, smoke tests, frontend tests, e2e tests, package build, config-guard release mode, website validation, and documentation command validation have completed.

The only remaining open issue is [#416](https://github.com/metalhatscats/martenweave-core/issues/416), a maintainability refactor to split the CLI monolith into a `commands/` package. It is not a functional release blocker and is tracked for a future release.

---

## Historical: Martenweave Core 0.4.1

Run date: 2026-06-23

Branches:

- Core: `release/v0.4.1`
- Site: `main`

Environment:

- Python: 3.11.15
- Martenweave Core: 0.4.1
- `gh` issue check: authenticated GitHub CLI

### Core Validation

| Command | Result | Evidence |
|---|---|---|
| `.venv/bin/martenweave --version` | Passed | `martenweave-core 0.4.1` |
| `.venv/bin/python -m ruff check .` | Passed | `All checks passed!` |
| `.venv/bin/python -m ruff format --check .` | Passed | `209 files already formatted` |
| `.venv/bin/python -m pytest` | Passed | `1302 passed, 3 skipped, 7 warnings in 63.72s` |
| `bash scripts/smoke_test.sh` | Passed | `Smoke Test Complete — All JSON contracts stable` |
| `bash scripts/release_smoke.sh` | Passed | `Release smoke checks passed` — all bundled examples validated, indexed, checked fresh, and exercised through search, query, trace, impact, gaps, gap report, proposal dry-run, and config guard release mode |
| `.venv/bin/martenweave config-guard --repo . --mode release --json` | Passed | Reported ignored local `.env` `api_key` findings with `file_status: "ignored"` and exited 0 |
| `.venv/bin/python -m build` | Passed | Produced `martenweave_core-0.4.1.tar.gz` and `martenweave_core-0.4.1-py3-none-any.whl`; wheel METADATA reports `Version: 0.4.1` |

## Config Guard

| Command | Result | Evidence |
|---|---|---|
| `.venv/bin/martenweave config-guard --repo . --json` | Failed locally | Detected three potential `api_key` secrets in ignored local `.env` at lines 1, 2, and 4; no `repo_config`, `gitignore`, or `repo_secrets` findings |
| `.venv/bin/martenweave config-guard --repo . --mode release --json` | Passed | Reported the same ignored `.env` findings with `file_status: "ignored"` and exited 0 |

Interpretation: default local mode still reports ignored local `.env` secrets. Release mode can pass
when findings are limited to ignored local-only files, while tracked or untracked repository secret
findings remain release-blocking.

## Package Metadata

- `pyproject.toml` declares `version = "0.4.1"`.
- `src/modelops_core/__version__.py` declares `__version__ = "0.4.1"`.
- Built wheel and sdist filenames include `0.4.1`.
- Wheel METADATA reports `Version: 0.4.1`.

## License Status at the Time of 0.4.1

- Version 0.4.1 was originally distributed under MIT, and existing copies retain those terms.
- This section is historical release evidence, not the current licensing statement.
- The current supported release and active development use Apache License 2.0; see
  `docs/licensing-and-commercial-use.md`.

## Tag Safety

- Remote `v0.4.0` tag exists and points to an older commit; it is intentionally not reused,
  moved, deleted, or force-updated.
- `v0.4.1` is the safe patch release from the validated `main`/`release/v0.4.1` commit.

## Release Readiness Decision

The core is release-clean for source/GitHub and PyPI handoff: validation, smoke tests, package
build, config-guard release mode, trusted publishing, and PyPI publication for `martenweave-core
0.4.1` have completed.

[#411](https://github.com/metalhatscats/martenweave-core/issues/411) was the manual PyPI trusted
publisher setup blocker during the release-candidate phase. It is now resolved and closed.

## Generated Artifacts

Build and smoke commands may create ignored local artifacts under:

- `examples/*/generated/`
- Python cache directories
- `dist/`, `build/`, `src/*.egg-info/`
- Site screenshot/output directories

These are rebuildable artifacts and should not be staged for release commits unless explicitly
intended as public proof assets.
