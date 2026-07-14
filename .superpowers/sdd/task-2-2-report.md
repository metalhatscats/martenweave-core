# Task 2.2 + 2.3 Report: Agent-loop CLI, MCP prompt, and self-correction rules

## Summary

Implemented a closed-loop `martenweave agent-loop` command and an MCP `run_agent_loop` prompt that turns a free-text modeling goal into a validated, impact-assessed `PatchProposal` through iterative propose → validate → refine cycles, without ever applying changes automatically.

## What was implemented

### 1. `src/modelops_core/ai/agent_loop.py`

New module containing the core state machine and loop logic:

- `AgentLoopStatus` enum with terminal statuses: `valid_proposal`, `invalid_proposal`, `no_progress`, `high_risk`, `failed`.
- `IterationLogEntry` dataclass recording per-iteration `iteration`, `action`, `proposal_id`, `validation_status`, and `errors`.
- `AgentLoopResult` dataclass with all required fields: `goal`, `iterations`, `final_status`, `proposal_id`, `proposal_path`, `validation_status`, `impact`, `assumptions`, `human_checks`, `log`.
- `_errors_unchanged(prev, current)` helper comparing normalized error tuples `(code, message, object_id)`.
- `_build_refined_note(goal, proposal, previous_errors)` constructing a note that appends validation errors to the original goal.
- `run_agent_loop(repo_root, goal, max_iterations=5, dry_run=False)` implementing the state machine:
  1. Baseline repository validation via `validate_objects`.
  2. Iterative proposal generation via `build_patch_proposal_from_note`.
  3. Validation inspection from `proposal["validation_status"]` and `proposal["validation_results"]`.
  4. Impact analysis via `generate_proposal_impact_report` and `compute_proposal_risk`.
  5. Refinement on validation errors, stopping on max iterations or no progress.
  6. Never calls `apply_patch_proposal`; only writes to `model/patch-proposals/` (and only when not in dry-run mode).
  7. Writes an audit event with `actor="agent-loop"` after every iteration via `AuditEventService`.

### 2. `src/modelops_core/cli.py`

Added `martenweave agent-loop` Typer command:

- Options: `--goal TEXT`, `--repo PATH`, `--max-iterations N`, `--dry-run`, `--json`.
- Calls `run_agent_loop` and renders a Rich table or stable JSON output.
- Exits with code 1 on terminal failure statuses (`invalid_proposal`, `no_progress`, `failed`).

### 3. `src/modelops_core/mcp_server.py`

Added `run_agent_loop(goal: str)` MCP prompt that instructs an agent to use `validate_model`, `propose_model_change`, `proposal_impact`, and `proposal_dry_run` in sequence, with explicit safety rules (no automatic application, max 5 iterations, only write PatchProposal files).

### 4. Tests

- `tests/test_agent_loop.py`: 11 tests covering helpers, valid goal, refinement, max iterations, no progress, high risk, failure, and dry-run behavior.
- `tests/test_cli.py`: 2 tests covering CLI JSON and human output for `agent-loop`.

## TDD RED/GREEN evidence

Focused tests were run iteratively during development:

```bash
pytest tests/test_agent_loop.py tests/test_cli.py -v -k agent_loop
```

Initial RED run (after first implementation):
- 7 failed due to patching `modelops_core.ai.agent_loop.build_patch_proposal_from_note` before the function was imported at module level.

Fix:
- Moved `build_patch_proposal_from_note` import to module level in `agent_loop.py`.

Subsequent RED run:
- `test_agent_loop_max_iterations` failed with `no_progress` instead of `invalid_proposal` because the mock returned identical errors each iteration.

Fix:
- Updated the test to return distinct error messages per iteration.

Final focused run:
- 13 passed, 44 deselected.

Full validation ladder run:

```bash
pytest -q && ruff check .
```

Result:
- 1420 passed, 3 skipped, 7 warnings.
- `All checks passed!`

## Manual end-to-end verification

Invoked the CLI against `examples/customer_bp_model` with the sample goal. The loop produced a valid proposal in one iteration, correctly flagged it as `high_risk` because it touched an active object and affected >5 downstream objects, and wrote the proposal to `model/patch-proposals/`. The manual test artifact was removed afterward.

## Files changed

- `src/modelops_core/ai/agent_loop.py` (new)
- `src/modelops_core/cli.py` (modified)
- `src/modelops_core/mcp_server.py` (modified)
- `tests/test_agent_loop.py` (new)
- `tests/test_cli.py` (modified)

## Self-review findings

- The state machine matches the design spec diagram and terminal statuses.
- Safety boundaries are respected: no `apply_patch_proposal` call, canonical objects outside `patch-proposals/` are not mutated, and `--dry-run` prevents any proposal write.
- Every iteration (including the baseline validation) emits an audit event with actor `agent-loop`.
- JSON output is stable and includes all required fields.
- Ruff linting passes with no issues.
- Imports were kept local where needed to avoid circular dependencies; `build_patch_proposal_from_note` was moved to module level after confirming no circular import risk.

## Issues or concerns

- The `NoProviderAdapter` scaffold returns a proposal that modifies `ATTR-CUST-SALES-CUSTOMER-GROUP` regardless of the exact goal wording, which can cause high-risk results for otherwise simple goals. This is expected behavior for the deterministic scaffold and would improve once a real AI provider is configured.
- No actual `dry_run_patch_proposal` service call is made inside the loop in dry-run mode; the CLI dry-run only suppresses the write. This satisfies the brief requirement to "preview the loop without writing any proposals" but does not surface an operations preview. If a deeper dry-run preview is needed later, it can be added as a non-breaking enhancement.
- The `_build_refined_note` signature follows the brief (`goal, proposal, previous_errors`). The design spec's optional high-risk impact sentence is included only if the proposal dict carries an `impact` key, which the current state machine does not set during refinement (high-risk is a terminal state). This is consistent with the state machine but means that specific sentence is not currently exercised.

## Commits

- `176bf55` feat: agent-loop CLI, MCP prompt, and self-correction rules


---

## Fix pass — Task 2.2 Important findings

### Changes made

1. **Baseline validation blocks the loop** (`src/modelops_core/ai/agent_loop.py`)
   - After `_run_baseline_validation`, if `is_valid` is `False`, `run_agent_loop` immediately returns an `AgentLoopResult` with:
     - `final_status="failed"`
     - `validation_status="invalid"`
     - `iterations=0`
     - `human_checks` containing a clear message with the error count.
   - The existing baseline-validation audit event is still emitted before returning.

2. **Guard `max_iterations < 1`** (`src/modelops_core/ai/agent_loop.py`)
   - Added an upfront check before baseline validation.
   - Returns a failed result with `human_checks` explaining that `max_iterations` must be at least 1.

3. **Terminal impact-transition audit event** (`src/modelops_core/ai/agent_loop.py`)
   - After impact analysis completes and `result.impact` is populated, `_emit_iteration_audit` is called with `action="impact_analysis"`, `validation_status="valid"`, and the final proposal ID.
   - This event is emitted before the `HIGH_RISK` or `VALID_PROPOSAL` return, satisfying the requirement to audit the terminal transition.

### Tests added (`tests/test_agent_loop.py`)

- `test_agent_loop_blocks_on_invalid_baseline` — mocks `_run_baseline_validation` to return an invalid summary; asserts `FAILED`, no proposal generation attempted, and human checks mention baseline failure.
- `test_agent_loop_rejects_zero_max_iterations` — invokes the loop with `max_iterations=0`; asserts `FAILED`, `iterations=0`, and a clear human check.
- `test_agent_loop_emits_terminal_impact_audit` — patches `_emit_iteration_audit`; asserts an `impact_analysis` audit call occurs with the final proposal ID and `validation_status="valid"`.

### Verification

Focused tests:

```bash
/Users/dzmitryikharlanau/Developments/martenweave/.venv/bin/python -m pytest tests/test_agent_loop.py -v
```

Result: **14 passed**.

Full validation ladder:

```bash
/Users/dzmitryikharlanau/Developments/martenweave/.venv/bin/python -m pytest -q && /Users/dzmitryikharlanau/Developments/martenweave/.venv/bin/python -m ruff check .
```

Result: **1423 passed, 3 skipped, 7 warnings**; `All checks passed!`.

### Commit

- `ab54b60` fix(agent-loop): block on invalid baseline, guard max_iterations, emit terminal impact audit

### New concerns

None. All findings from the fix brief are addressed, tests pass, and linting is clean.
