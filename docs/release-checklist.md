# Release Checklist

Use this checklist before a public GitHub release, package publish, or release-candidate handoff. Do not tag or publish until every required item is complete or explicitly waived in release notes.

## Required Verification

```bash
.venv/bin/python -m pip install -e ".[dev]"
.venv/bin/python -m ruff check .
.venv/bin/python -m ruff format --check .
.venv/bin/python -m pytest
bash scripts/smoke_test.sh
bash scripts/release_smoke.sh
.venv/bin/modelops config-guard --repo . --json
.venv/bin/modelops config-guard --repo . --mode release --json
.venv/bin/python -m build
```

## Example Repositories

Each bundled example must validate, build an index, and report a fresh index:

```bash
for repo in \
  examples/simple_product_model \
  examples/customer_bp_model \
  examples/supplier_vendor_model \
  examples/generic_product_model
do
  .venv/bin/modelops validate --repo "$repo"
  .venv/bin/modelops build-index --repo "$repo" --jsonl
  .venv/bin/modelops index-fresh --repo "$repo"
done
```

## Public CLI Smoke Flow

The release smoke script covers:

- `validate`
- `build-index --jsonl`
- `index-fresh`
- `health`
- `scorecard`
- `search`
- `query`
- `trace`
- `impact`
- `gaps --check-model`
- `gap-report`
- `propose-patch --dry-run`

## Release Readiness

- [ ] Version matches in `pyproject.toml` and `src/modelops_core/__version__.py`.
- [ ] `CHANGELOG.md` has a dated entry for the release.
- [ ] `docs/release-notes-first-public-rc.md` is updated or superseded by final release notes.
- [ ] `docs/release-validation-evidence.md` reflects the latest release-candidate validation run.
- [ ] `README.md` quickstart works from a clean clone.
- [ ] `docs/first-15-minutes.md` and `docs/demo-quickstart-flow.md` are accurate.
- [ ] `docs/known-limitations.md` reflects current limits.
- [ ] License/commercial-use wording matches `LICENSE`, `pyproject.toml`, and `docs/licensing-and-commercial-use.md`.
- [ ] `LICENSE`, `CONTRIBUTING.md`, `SECURITY.md`, and `SUPPORT.md` exist.
- [ ] No secrets, private datasets, `.env` files, or generated indexes are staged.
- [ ] Ignored local `.env` findings are reviewed in local mode and do not block release mode.
- [ ] All generated artifacts can be rebuilt from canonical files.
- [ ] Website positioning is updated if product claims changed.

## Hard Stops

Do not release if:

- deterministic validation is broken for bundled examples
- `build-index` cannot produce SQLite and JSONL outputs
- `search`, `trace`, or `impact` are broken on `examples/customer_bp_model`
- AI can mutate canonical files without a proposal/review path
- package metadata points to a missing license
- known failing tests are hidden or skipped without an issue
