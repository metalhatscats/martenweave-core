# Public Source Readiness Notes

This document records the minimum public-readiness expectations for Martenweave Core.

## Current State

- License: PolyForm Free Trial License 1.0.0, in `LICENSE`.
- Package metadata: `pyproject.toml` declares README, license, keywords, and classifiers.
- Contribution path: `CONTRIBUTING.md` and GitHub issue templates.
- Security reporting: `SECURITY.md`.
- Support expectations: `SUPPORT.md`.
- CI: Python 3.11 and 3.12 test/lint matrix with example index builds.
- Release workflow: tag-triggered build and publish workflow exists, but maintainers must not trigger it accidentally.

## Public Claim Guardrails

Do not claim:

- SAP certification
- SAP partnership or affiliation
- production SaaS availability
- production UI availability
- customers, case studies, or testimonials that do not exist
- autonomous AI mutation of model truth

Do claim, when verified:

- backend-first CLI/core package
- canonical file source of truth
- deterministic validation
- generated SQLite/JSONL indexes
- search/query/trace/impact workflows
- proposal-first AI governance
- local-first architecture
- source availability for inspection and time-limited evaluation

Do not describe current repository source or future releases as open source. Their commercial-use
restrictions make them source-available. Previously published MIT-licensed versions remain open
source under the terms shipped with those copies.

## Repository Hygiene

Before making the repository public or announcing a release:

```bash
git status --short
.venv/bin/martenweave config-guard --repo . --json
.venv/bin/martenweave config-guard --repo . --mode release --json
.venv/bin/python -m ruff check .
.venv/bin/python -m pytest
bash scripts/release_smoke.sh
```

Check for:

- committed generated artifacts
- private data in examples or fixtures
- secrets in config files
- stale links in README and public docs
- issue templates that match the contribution workflow

## Remaining Public-Readiness Work

Track remaining work as GitHub issues with:

- Goal
- Scope
- Acceptance criteria
- Validation command

Route core/product issues to `metalhatscats/martenweave-core` and website/docs issues to `Martenweave/martenweave.github.io`.
