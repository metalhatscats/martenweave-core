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
- [ ] Public-source and licensing docs exist: `LICENSE`, `CONTRIBUTING.md`, `SECURITY.md`, `SUPPORT.md`
- [ ] Local config guard reviewed: `.venv/bin/martenweave config-guard --repo . --json`
- [ ] Release config guard passes: `.venv/bin/martenweave config-guard --repo . --mode release --json`
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
git tag -a vX.Y.Z -m "Release vX.Y.Z"
git push origin vX.Y.Z
```

Do not move or reuse an existing remote tag. If a tag exists from a failed release attempt and
points to the wrong commit, create the next patch version from the intended release commit instead
of force-pushing the old tag.

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
- The tag must point at the exact commit that passed local validation and CI.
- **The Git tag version must match the package version in `pyproject.toml`.** The release
  workflow runs a preflight guard that fails before building if the versions differ.

### Tag / package version matching

The release guard strips a leading `v` from the tag and compares the remainder to
`project.version` in `pyproject.toml`. Examples:

| Tag | `pyproject.toml` version | Result |
|---|---|---|
| `v0.5.0` | `0.5.0` | ✅ passes |
| `0.5.0` | `0.5.0` | ✅ passes |
| `v0.5.0a1` | `0.5.0` | ❌ fails — cannot publish a pre-release tag from a stable package version |
| `v0.5.1` | `0.5.0` | ❌ fails — tag and package versions differ |

To publish a pre-release (e.g. for a dry-run on a real tag), bump the package version
to the same pre-release version first:

```bash
# pyproject.toml: version = "0.5.1a1"
git tag -a v0.5.1a1 -m "Pre-release v0.5.1a1"
git push origin v0.5.1a1
```

This prevents a pre-release tag from accidentally publishing a stable version such as
`0.5.0` to PyPI.

### Dry-run release tests

For local or CI release smoke tests that do **not** intend to publish, do not push a
tag that triggers `.github/workflows/release.yml`. If you must exercise the release
workflow end-to-end, use a dedicated test PyPI instance or ensure `pyproject.toml`
declares a pre-release version that matches the tag. Never run a dry-run against the
production PyPI project with a stable package version.

## Local Build

```bash
.venv/bin/python -m build
```

This produces:

- `dist/martenweave-core-<version>.tar.gz` — source distribution
- `dist/martenweave-core-<version>-py3-none-any.whl` — wheel

## Canonical repository migrations

`martenweave migrate --repo <repo>` is preview-first. It reports each planned schema marker
change without touching canonical files. Use `--apply` only after reviewing the plan:

```bash
.venv/bin/martenweave migrate --repo ./my-model
.venv/bin/martenweave migrate --repo ./my-model --apply
```

The current Core writes only schema versions with an explicit migration path. Future or unknown
versions fail without mutation. On apply, the original canonical files are copied under
`generated/migration-backups/`, writes are atomically replaced, the repository is validated, the
disposable index is rebuilt, and a receipt is written under `generated/migration-receipts/`.
Restore the recorded backup and rebuild the index to roll back a completed migration.

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
