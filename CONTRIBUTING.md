# Contributing to Martenweave Core

Martenweave is a backend-first agentic data model registry. Contributions should preserve the core product boundary:

- Canonical Markdown/YAML model files are the source of truth.
- Generated SQLite/JSONL artifacts are disposable and should not be committed unless a maintainer explicitly asks for it.
- Validation is deterministic and must stay ahead of indexing and reporting.
- AI-generated changes must flow through `PatchProposal` and human approval before canonical files change.
- SAP migration and MDM are starter scenarios, not the only supported domain.

## Good First Contributions

- Reproducible CLI bugs with a failing test.
- Documentation corrections for commands that exist today.
- Validation-rule improvements with focused fixtures.
- Example-model improvements that keep examples small and explainable.
- Domain-pack additions that do not hard-code one domain into core behavior.

## Local Setup

```bash
python -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
```

## Validation Before a PR

Run the smallest relevant test first, then the release checks before asking for review:

```bash
.venv/bin/python -m ruff check .
.venv/bin/python -m ruff format --check .
.venv/bin/python -m pytest
bash scripts/release_smoke.sh
```

For model changes, also run:

```bash
.venv/bin/modelops validate --repo examples/customer_bp_model
.venv/bin/modelops build-index --repo examples/customer_bp_model --jsonl
```

## Pull Request Expectations

- Explain the goal and scope.
- List exact validation commands and results.
- Call out canonical model changes separately from generated artifacts.
- Keep changes small enough to review.
- Do not include secrets, raw client data, local `.env` files, or generated indexes.

## Issue Quality

Useful issues include:

- Goal
- Scope
- Acceptance criteria
- Validation command
- Reproduction steps when reporting a bug

The repository issue templates are structured around that format.

## Contribution Licensing

Martenweave Core is source-available and may also be offered under separate pilot or commercial
agreements. The project may therefore require a contributor agreement before accepting external
code or documentation. A maintainer will confirm the required terms during pull-request review;
submitting a pull request does not by itself guarantee that it can be merged.
