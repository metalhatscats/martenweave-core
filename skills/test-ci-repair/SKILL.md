# Skill: Test and CI Repair — Martenweave

## When to use
A pytest run or a CI job (`test-and-lint`, `frontend-build`) is failing and you must diagnose and fix it without weakening any check (P1).

## Inputs
- The failing command or CI log (job name, step, Python version from the matrix)
- Current branch and the diff that introduced the failure
- Optional: a maintainer waiver, if one exists, recorded in the issue

## Read first
1. The complete failure output — assertion diff, traceback, failing step — before touching anything.
2. `docs/developer/TESTING_STRATEGY.md` — test levels, coverage floors, mocking policy.
3. `.github/workflows/ci.yml` — the exact commands each job runs (read-only; see P8).
4. `docs/factory/policies/AGENT_PREVENTIONS.md` (P1) and `docs/factory/policies/QUALITY_GATES.md` (G5, G6, G9).

## Do not do
- Do not delete, skip, or quarantine tests; no `skip`/`xfail` to silence a failure (P1).
- Do not loosen assertions, lower coverage floors, or edit fixtures/examples to make a check pass (P1).
- Do not edit `.github/workflows/` — protected path (P8), L3: propose the change in the issue, never apply.
- Do not fix the assertion when the code is wrong; fix the cause.
- Do not claim done while any gate is red; a failing test blocks until fixed or the maintainer explicitly waives it.

## Procedure
1. **Reproduce locally first**, using the exact command from the CI log:
   ```bash
   .venv/bin/python -m pytest -q                                  # full suite (G5)
   .venv/bin/python -m pytest tests/test_x.py::test_y -q          # single failing test
   ```
2. **Read the failure.** Identify the layer: unit, integration, CLI contract, or e2e (see TESTING_STRATEGY.md). Trace the assertion back to the code under test before editing.
3. **Classify the break**:
   - Product bug → fix the implementation; the failing test stays and must pass unchanged or strengthened.
   - Test bug (test asserts wrong behavior) → correct the test to assert the right behavior; never weaker.
   - Intended behavior change → update test, contract test (`tests/test_cli_contracts.py`), and docs in the same patch.
4. **CI-specific failures**: the `test-and-lint` matrix runs Python 3.11 and 3.12 — reproduce under the failing interpreter version, not just your local one. The `frontend-build` job reproduces with:
   ```bash
   npm --prefix frontend ci && npm --prefix frontend run build && npm --prefix frontend test
   ```
   Other CI steps with local equivalents: `ruff check src tests`, `ruff format --check src tests`, `bash scripts/release_smoke.sh`, `.venv/bin/python scripts/validate_doc_commands.py`.
5. **Coverage failures**: CI enforces `--cov-fail-under=70`; critical paths (`validation/pipeline.py`, `patching/`, `index/sqlite_builder.py`, `change_request/service.py`) target 90% per TESTING_STRATEGY.md. A coverage drop means missing tests for new code — write the tests. Never lower the floor or pad coverage with trivial getters.
6. **Environment-only failures** (missing tool, network): report the environment gap in the issue and retry once after fixing it; do not skip the gate (see `docs/factory/WORKFLOWS.md` recovery rules).
7. Re-run the full gate set after the fix:
   ```bash
   .venv/bin/python -m pytest --cov=modelops_core --cov-report=term-missing --cov-fail-under=70
   .venv/bin/ruff check .
   ```

## Validation
- `.venv/bin/python -m pytest -q` passes with no new skips.
- The exact CI command that failed now exits 0, under the same Python/Node version as CI.
- Coverage stays at or above the floor that failed; no assertion was weakened in the diff.
- `factory review` diff check shows no P1/P8 violation.

## Output format
Return:
- Root cause (one paragraph: what broke and why)
- Classification (product bug / test bug / intended change / environment)
- Files changed, with the failing test name(s)
- Commands run with exact pass/fail counts (e.g. `pytest: 1805 passed`)
- Waiver status (`none`, or maintainer waiver reference)
