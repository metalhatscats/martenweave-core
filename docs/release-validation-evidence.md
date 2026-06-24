# Release Validation Evidence

Run date: 2026-06-23

Branches:

- Core: `release/v0.4.1`
- Site: `main`

Environment:

- Python: 3.11.15
- Martenweave Core: 0.4.1
- `gh` issue check: authenticated GitHub CLI

## Core Validation

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

## License Status

- Current license: MIT in `LICENSE`.
- Package metadata: `pyproject.toml` declares `license = "MIT"`.
- MIT permits commercial use when the license notice is preserved.
- Current release-candidate recommendation: keep the core MIT and monetize optional paid pilots,
  facilitation, support, templates, and future products.
- Future dual-license or source-available non-commercial strategy: requires owner decision.

## Tag Safety

- Remote `v0.4.0` tag exists and points to an older commit; it is intentionally not reused,
  moved, deleted, or force-updated.
- `v0.4.1` is the safe patch release from the validated `main`/`release/v0.4.1` commit.

## Release Readiness Decision

The core is release-candidate clean for a source/GitHub handoff: validation, smoke tests, package
build, and config-guard release mode all pass locally.

**Do not publish to PyPI until
[#411](https://github.com/metalhatscats/martenweave-core/issues/411) is closed.** The issue remains
open because the PyPI project trusted publisher entry must be configured manually. Do not push the
`v0.4.1` tag while #411 is open; pushing the tag would trigger `.github/workflows/release.yml` and
fail at the PyPI publish step.

## Generated Artifacts

Build and smoke commands may create ignored local artifacts under:

- `examples/*/generated/`
- Python cache directories
- `dist/`, `build/`, `src/*.egg-info/`
- Site screenshot/output directories

These are rebuildable artifacts and should not be staged for release commits unless explicitly
intended as public proof assets.
