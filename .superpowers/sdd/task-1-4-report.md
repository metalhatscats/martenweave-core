# Task 1.4: Tighten MCP server AI workflows — Report

## What was implemented

1. **`propose_model_change` now passes repository context and records MCP-specific telemetry**
   - `src/modelops_core/mcp_server.py`: `propose_model_change` calls `build_patch_proposal_from_note(note, repo_root=repo_root, command="mcp-propose-model-change")`.
   - `src/modelops_core/ai/patch_proposal_service.py`: added a `command` parameter (default `"propose-patch"`) and forwarded it to `wrap_ai_adapter` so the telemetry event carries the MCP command name.

2. **`infer_model` exposes `dataset_id` and `domain` hints**
   - `src/modelops_core/mcp_server.py`: `infer_model(profile_path, dataset_id=None, domain=None)`.
   - `src/modelops_core/imports/model_inference_service.py`: added `domain` parameter to `infer_model_from_profile` and threaded it through `_infer_objects_from_sheet` so generated objects use the supplied domain when provided.

3. **All write-intent tools return `assumptions` and `human_checks` arrays**
   - `propose_model_change` already returned them; unchanged.
   - `infer_model` already returned them via the generated proposal; unchanged.
   - `proposal_dry_run`, `proposal_impact`, `create_change_request_tool`, and `export_model` now include explicit `assumptions` and `human_checks` arrays, including on error paths where applicable.

## What was tested

- Added a RED/GREEN TDD cycle:
  1. Wrote `test_propose_model_change_triggers_telemetry` asserting that `generated/ai_usage_events.jsonl` contains an event with `command="mcp-propose-model-change"` and `provider="NoProviderAdapter"`. This failed before implementation (no telemetry file created, command was `"propose-patch"`).
  2. Implemented the source changes; test passes.
- Added/updated tests for all write-intent tools to assert `assumptions` and `human_checks` are present.
- Added tests for `infer_model` with explicit `dataset_id` and `domain` hints, verifying the proposal ID and generated object domains.
- Ran focused suite: `pytest tests/test_mcp_server.py -v` — **47 passed**.
- Ran full validation ladder: `pytest -q && ruff check .` — **1392 passed, 3 skipped; ruff clean**.

## Files changed

- `src/modelops_core/ai/patch_proposal_service.py`
- `src/modelops_core/imports/model_inference_service.py`
- `src/modelops_core/mcp_server.py`
- `tests/test_mcp_server.py`
- `.superpowers/sdd/task-1-4-report.md` (this file)

## Self-review findings

- The `command` parameter addition is backward-compatible: existing CLI callers default to `"propose-patch"`.
- The `domain` parameter addition is backward-compatible: existing callers default to `None`, preserving previous domain inference from `dataset_id`.
- No new runtime dependencies were introduced.
- No real AI provider calls are made in tests; the `NoProviderAdapter` scaffold is used.
- All modified lines respect the project’s 100-character line-length limit.

## Issues or concerns

- None. The implementation stays within the brief and follows existing patterns.


## Task 1.4 Fix Pass — Error-path arrays and export serialization

### What changed

1. **`infer_model` error path now returns required arrays**
   - `src/modelops_core/mcp_server.py`: when `profile_path` does not exist, the tool now returns `{"error": ..., "assumptions": [], "human_checks": []}` and uses `indent=2, default=str` for consistent JSON serialization.

2. **`create_change_request_tool` error path now returns required arrays**
   - `src/modelops_core/mcp_server.py`: the `ValueError` handler now returns `{"error": str(exc), "assumptions": [], "human_checks": []}` with consistent serialization.

3. **Optional cleanup: `export_model` unknown-format serialization**
   - `src/modelops_core/mcp_server.py`: the unknown-format response now serializes with `indent=2, default=str`, matching all other tool outputs.

### Tests updated

- `tests/test_mcp_server.py`:
  - `test_create_change_request_tool_invalid_id` now asserts `assumptions` and `human_checks` are present on the error path.
  - `test_export_model_unknown_format` now asserts `assumptions` and `human_checks` are present.
  - Added `test_infer_model_missing_profile_path` to assert the missing-profile error path includes `assumptions` and `human_checks` arrays.

### Verification

- Focused tests: `pytest tests/test_mcp_server.py -v` — **48 passed**.
- Full validation ladder: `pytest -q && ruff check .` — **1393 passed, 3 skipped; ruff clean**.

### Files changed

- `src/modelops_core/mcp_server.py`
- `tests/test_mcp_server.py`
- `.superpowers/sdd/task-1-4-report.md` (this append)

### Concerns

- None. The fixes are minimal, backward-compatible, and the validation ladder is green.
