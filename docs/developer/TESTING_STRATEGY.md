# Testing Strategy

## Philosophy

Martenweave Core is a backend-first, validator-gated model registry. Tests exist to prove that deterministic validation, indexing, patching, and reporting behave correctly for both machine-generated and human-authored canonical objects. Product behavior tests are added with implementation tasks; every change that affects validation, indexing, CLI output, or patch safety must include tests.

## Test framework

- Use **pytest** for all Python tests.
- Target Python 3.11 and 3.12 in CI.
- Run the full suite with:

  ```bash
  python -m pytest
  ```

- Run a targeted module with:

  ```bash
  python -m pytest tests/test_reference_validation.py -q
  ```

## Test levels

| Level | Purpose | Examples |
|---|---|---|
| Unit | Pure functions and small services | `test_schema_validation.py`, `test_patch_proposal_validation.py` |
| Integration | Services that read/write files or SQLite | `test_index_builder.py`, `test_assessment_package.py` |
| CLI contract | CLI commands produce the documented JSON/markdown outputs | `test_cli_contracts.py` |
| End-to-end | Full workflows across propose → validate → apply | `test_e2e_proposal_full_lifecycle.py` |

Use the fewest level needed to prove the behavior. Prefer unit tests for validation rules; prefer integration tests for index and report output.

## Coverage target

- **Overall floor:** 70%.
- **Critical paths:** 90%.
- Critical paths include:
  - `src/modelops_core/validation/pipeline.py`
  - `src/modelops_core/patching/` (apply, validate, proposal service)
  - `src/modelops_core/index/sqlite_builder.py`
  - `src/modelops_core/change_request/service.py`

Do not chase coverage by testing trivial getters or generated CLI help text. Coverage is a guardrail, not a goal.

## Mocking policy

- **Mock external APIs only.** Network calls to AI providers, Google Drive, GitHub, and telemetry endpoints must be mocked or use stub adapters.
- **Do not mock core validation.** Tests for `validate_objects`, patch validators, and SAP context rules should exercise the real code with real or fixture objects.
- **Do not mock the SQLite index** when testing index building, reports, or impact analysis. Use temporary paths and the `build_index` helper.
- Use `monkeypatch` or pytest fixtures to inject stubs for external services such as `NoProviderAdapter`.

## Fixtures

Shared fixtures live in `tests/conftest.py`:

- `sample_repo` — a temporary copy of `examples/customer_bp_model` with a fresh SQLite index.
- `supplier_repo` — a temporary copy of `examples/supplier_vendor_model` with a fresh SQLite index.
- `temp_model_dir` — a minimal temporary model with a `DOMAIN-TEST` and `ATTR-TEST` object.

Use these fixtures for integration and assessment tests. For unit tests that only need parsed frontmatter, build `ParsedObject` instances directly to keep tests fast and isolated.

When adding a new object type or validation rule, add a minimal fixture or factory only if multiple tests need the same canonical shape.

## Contract tests

Any new CLI command, subcommand, or JSON output must be covered in `tests/test_cli_contracts.py`. Contract tests verify that:

- The command exits with code `0` for valid input.
- JSON output contains the documented keys and value types.
- Markdown reports contain expected headings and tables.
- Error commands exit non-zero and surface actionable messages.

If a command changes its output schema, update the contract test and the relevant documentation together.

## Adding tests for validation rules

Validation rules live in `src/modelops_core/validation/pipeline.py` and domain packs such as `src/modelops_core/domain_packs/sap.py`.

When adding or modifying a rule:

1. Add a positive test proving the rule does not fire for valid objects.
2. Add a negative test proving the rule fires with the expected `code` and `severity` for invalid objects.
3. If the rule is type-specific, test against the correct object type and realistic frontmatter.
4. If the rule is cross-object (references, ValueList codes, retired lifecycle), include all related objects in the input list so `_build_registry` can resolve references.

Use `ValidationSeverity.ERROR` / `ValidationSeverity.WARNING` assertions rather than brittle message strings.

## Patch and change-request safety tests

Patch proposals and change requests are the only AI-assisted write path. Tests must prove:

- `validate_patch_proposal` catches malformed or unsafe operations.
- `apply_patch_proposal` rolls back on failure.
- Before-state guards reject stale applies.
- Approved proposals create `ChangeRequest` objects, not direct canonical edits.

See `tests/test_patch_proposal_validation.py`, `tests/test_patch_apply.py`, and `tests/test_change_request_service.py` for patterns.

## Running lint and format checks

Before committing, run:

```bash
python -m ruff check .
python -m ruff format --check src tests
```

Fix any reported issues with:

```bash
python -m ruff check . --fix
python -m ruff format src tests
```

## Example models as test data

The `examples/` directory contains real canonical models. Do not edit them to make a test pass. If a test needs a specific invalid state, construct it in a temporary directory or via `ParsedObject` fixtures.

## Acceptance evidence

Every task must record in result notes:

- Commands run.
- Pass/fail counts.
- Changed files.
- Any remaining gaps or follow-up issues.
