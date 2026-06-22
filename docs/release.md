# Release Guide

This document defines how Martenweave Core is versioned, built, and released.

For the complete go/no-go checklist, see [release-checklist.md](release-checklist.md).

## Versioning Policy

Martenweave Core follows [Semantic Versioning 2.0.0](https://semver.org/):

- **MAJOR** — incompatible CLI or API changes, breaking schema changes
- **MINOR** — new features, new object types, new CLI commands
- **PATCH** — bug fixes, validation hardening, documentation corrections

### Where to update the version

1. `pyproject.toml` — `project.version`
2. `src/modelops_core/__version__.py` — `__version__`

Both must match before a release commit.

## Release Checklist

- [ ] All tests pass: `.venv/bin/python -m pytest`
- [ ] Lint passes: `.venv/bin/python -m ruff check .`
- [ ] Format check passes: `.venv/bin/python -m ruff format --check .`
- [ ] JSON smoke passes: `bash scripts/smoke_test.sh`
- [ ] Release smoke passes: `bash scripts/release_smoke.sh`
- [ ] Example models validate and build indexes
- [ ] Version is updated in `pyproject.toml` and `src/modelops_core/__version__.py`
- [ ] `CHANGELOG.md` is updated for this release
- [ ] `docs/release.md` is still accurate
- [ ] Known limitations are current: `docs/known-limitations.md`
- [ ] Open-source docs exist: `LICENSE`, `CONTRIBUTING.md`, `SECURITY.md`, `SUPPORT.md`
- [ ] Local config guard reviewed: `.venv/bin/modelops config-guard --repo . --json`
- [ ] Release config guard passes: `.venv/bin/modelops config-guard --repo . --mode release --json`
- [ ] No secrets or raw sensitive data in commits
- [ ] Package builds locally:
  ```bash
  rm -rf dist/ src/*.egg-info
  .venv/bin/python -m build
  ls -l dist/
  ```
- [ ] Optional extras are documented (see below)

## Automated Release

Push a tag to trigger the release workflow:

```bash
git tag v0.4.0 -m "Release v0.4.0"
git push origin v0.4.0
```

**Tag signing policy:**
- Signed tags (`git tag -s`) are **recommended** for releases.
- Unsigned maintainer tags are **allowed** for v0.x releases when GPG signing is not configured locally.
- Once GPG is set up, switch to signed tags and update this policy:
  ```bash
  gpg --full-generate-key
  git config --global user.signingkey <KEY_ID>
  git config --global tag.gpgSign true
  ```

The [`.github/workflows/release.yml`](../../.github/workflows/release.yml) workflow will:

1. Run tests and lint
2. Build wheel + sdist with `python -m build`
3. Publish to PyPI via [trusted publishing (OIDC)](https://docs.pypi.org/trusted-publishers/)
4. Create a GitHub Release with auto-generated notes

**Requirements:**
- The `release` environment must be configured in the GitHub repository settings.
- The PyPI project must have a trusted publisher entry for this repository and workflow.

## Local Build

```bash
.venv/bin/python -m build
```

This produces:

- `dist/martenweave-core-<version>.tar.gz` — source distribution
- `dist/martenweave-core-<version>-py3-none-any.whl` — wheel

Clean build artifacts between releases:

```bash
rm -rf dist/ src/*.egg-info
```

## Optional Extras

Martenweave Core keeps the base package lightweight. Optional integrations are installed via extras:

| Extra | Install command | Purpose |
|---|---|---|
| `dev` | `pip install -e ".[dev]"` | pytest, ruff, build |
| `google_adk` | `pip install -e ".[google_adk]"` | Google ADK agent provider |
| `mcp` | `pip install -e ".[mcp]"` | MCP server runtime |

Do not add provider-specific packages to the base `dependencies` list.

## Changelog

Keep a `CHANGELOG.md` at the repository root. Follow the [Keep a Changelog](https://keepachangelog.com/) format.

### Entry format

```markdown
## [0.1.1] - 2026-05-25

### Added
- Formula detection in Excel import (#47).

### Fixed
- JSON output wrapping from Rich console (#126).

### Changed
- Updated dev dependencies to include `build`.
```

Categories:

- `Added` — new features
- `Changed` — changes to existing functionality
- `Deprecated` — soon-to-be-removed features
- `Removed` — now-removed features
- `Fixed` — bug fixes
- `Security` — vulnerability fixes
