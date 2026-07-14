# Task 1.2 Report: Wire prompt registry into adapters

## What was implemented

1. **Added `PromptRegistry.render_for_workflow`** (`src/modelops_core/ai/prompt_registry.py`)
   - Looks up the latest prompt template for a workflow.
   - Returns `(system_prompt, user_prompt)` where the user prompt is rendered from structured inputs.
   - Raises `KeyError` when no template exists so callers can fall back.

2. **Created `propose_patch_v1.yaml`** (`src/modelops_core/ai/prompts/propose_patch_v1.yaml`)
   - `prompt_id: propose_patch`, `version: "1.0.0"`, `workflow: propose-patch`.
   - Defines `system_instructions`, `input_schema`, `output_schema` (mirroring the candidate schema),
     `safety_rules`, and a one-shot `example`.

3. **Refactored adapters** to use the prompt registry via a shared helper
   - Added `build_prompt_messages` in `src/modelops_core/ai/_candidate_common.py`.
   - Converts `AIContextBundle` to the input dict expected by the prompt template.
   - Tries `PromptRegistry.render_for_workflow("propose-patch", ...)` and falls back to the existing
     `_SYSTEM_PROMPT` / `_build_prompt` on `KeyError`.
   - Updated `kimi_adapter.py`, `openai_compatible_adapter.py`, and `ollama_adapter.py` to call
     `build_prompt_messages(context)` and pass the resulting system/user prompts to the provider.

4. **Tests added**
   - `test_prompt_registry.py`: `test_prompt_registry_render_for_workflow`,
     `test_prompt_registry_render_propose_patch`.
   - `test_kimi_adapter.py`: `test_kimi_adapter_uses_registry_prompt`,
     `test_kimi_adapter_fallback_when_registry_missing`, plus a shared `_minimal_valid_response` helper.
   - `test_openai_compatible_adapter.py`: `test_openai_adapter_uses_registry_prompt`,
     `test_openai_adapter_fallback_when_registry_missing`, plus a shared `_minimal_valid_response` helper.
   - `test_ollama_adapter.py`: `test_ollama_adapter_uses_registry_prompt`,
     `test_ollama_adapter_fallback_when_registry_missing`, plus a shared `_minimal_valid_response` helper.
   - Adapter tests mock `modelops_core.ai._candidate_common.PromptRegistry` to avoid filesystem coupling.

## TDD RED/GREEN evidence

- Initial focused run before changes: **53 passed**.
- First iteration with local `PromptRegistry` import inside `build_prompt_messages`: registry adapter tests
  **RED** (`AttributeError: ... does not have the attribute 'PromptRegistry'`).
- Fix: moved `PromptRegistry` import to module level in `_candidate_common.py` so it is patchable.
- Final focused run: **61 passed**.
- Full validation ladder: **1378 passed, 3 skipped**; `ruff check .` reports **All checks passed!**

## Files changed

- `src/modelops_core/ai/prompt_registry.py`
- `src/modelops_core/ai/_candidate_common.py`
- `src/modelops_core/ai/kimi_adapter.py`
- `src/modelops_core/ai/openai_compatible_adapter.py`
- `src/modelops_core/ai/ollama_adapter.py`
- `src/modelops_core/ai/prompts/propose_patch_v1.yaml` (created)
- `tests/test_prompt_registry.py`
- `tests/test_kimi_adapter.py`
- `tests/test_openai_compatible_adapter.py`
- `tests/test_ollama_adapter.py`

## Self-review findings

- The fallback path preserves the original hardcoded behavior exactly.
- No new runtime dependencies were added.
- No real AI provider calls are made in tests.
- All existing tests continue to pass; the change is backward compatible.
- `ruff` passes with no new lint issues.
- The prompt YAML follows the same structure as existing prompts in `src/modelops_core/ai/prompts/`.

## Issues or concerns

- None. The implementation matches the brief and validation is green.
