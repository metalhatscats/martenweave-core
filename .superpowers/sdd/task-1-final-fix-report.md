# Phase 1 Final Fix Report

## Findings Addressed

### 1. `_provider_health` masks non-200 HTTP status as `reachable: false` with `error: null`

**Changed:** `src/modelops_core/cli.py`

Restructured `_provider_health` so that a non-200 HTTP response now sets `error` to `"Provider returned HTTP {status}"` instead of returning `error: null`.

### 2. Broad exception catch in health check

**Changed:** `src/modelops_core/cli.py`

Replaced the broad `except Exception` in `_provider_health` with specific handlers for:
- `urllib.error.HTTPError` → `"Provider returned HTTP {code}"`
- `urllib.error.URLError` → `"Provider request failed: {reason}"`
- `TimeoutError` → `"Provider health check timed out"`
- A final narrow `except Exception` that records the exception type/message and redacts any leaked API key by replacing it with `[REDACTED]`.

The API key is now read once into a local `api_key` variable so it can be used for the Authorization header and for redaction.

### 3. Retry-loop control flow is confusing

**Changed:** `src/modelops_core/ai/openai_compatible_adapter.py` and `src/modelops_core/ai/ollama_adapter.py`

In both adapters, the retry loop now uses `break` when retries are exhausted for 5xx errors, making the exhaustion path explicit. The comment was updated from `"fall through to raise below"` (which was misleading because `continue` was used) to `"break out of the loop and raise below"`.

### Optional Minor Cleanups

**Changed:**
- `tests/test_kimi_adapter.py`
- `tests/test_ollama_adapter.py`
- `tests/test_openai_compatible_adapter.py`

Updated imports so `_parse_candidate` is imported from `modelops_core.ai._candidate_common` instead of re-exported from each adapter module.

**Changed:** `src/modelops_core/ai/patch_proposal_service.py`

Added an `Args:` section to the `build_patch_proposal_from_note` docstring documenting all parameters, including `command` and its telemetry purpose.

## Tests Added/Updated

**Added to `tests/test_cli.py`:**
- `test_ai_provider_health_non_200_status`: verifies non-200 responses produce a descriptive error.
- `test_ai_provider_health_http_error`: verifies `HTTPError` handling.
- `test_ai_provider_health_url_error`: verifies `URLError` handling.
- `test_ai_provider_health_timeout`: verifies `TimeoutError` handling.
- `test_ai_provider_health_unexpected_error_redacts_secret`: verifies the fallback `Exception` handler redacts the API key.

## Verification

### Focused tests

```bash
pytest tests/test_cli.py -v -k ai_provider
# 14 passed, 30 deselected

pytest tests/test_openai_compatible_adapter.py tests/test_ollama_adapter.py -v
# 33 passed

pytest tests/test_kimi_adapter.py -v
# 15 passed
```

### Full validation ladder

```bash
pytest -q && ruff check .
# 1407 passed, 3 skipped, 7 warnings
# All checks passed!
```

## Concerns

None. All findings from the brief are addressed, tests are green, and ruff is clean.
