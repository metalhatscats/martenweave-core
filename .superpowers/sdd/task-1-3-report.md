# Task 1.3 Report: Harden AI context builder

## What was implemented

Modified `src/modelops_core/ai/context_builder.py` to satisfy the task brief:

1. **Single `trace_object` call per seed**  
   The previous implementation called `trace_object` twice per seed (once to collect related nodes, once to collect edges). The new implementation makes one call per seed ID, collects related node IDs and relationship refs from the same `TraceResult`, then fetches any missing related objects. This is in `build_context_bundle` lines ~312–330.

2. **Validation-error-weighted compaction**  
   `_compact_objects` now accepts an optional `validation_summary` parameter. The sort key is `(-validation_error_count, type_priority, 0)` so objects with more validation errors rise to the top, followed by the existing type priority. The error counts are derived from the validation summary details.

3. **Redacted source metadata**  
   Added `_fetch_redacted_sources(db_path, object_ids)`. When `redaction_policy != "summary_only"`, the bundle includes redacted metadata (`source_id`, `dataset_id`, `column_count`, `row_count`, `inferred_types`) for linked dataset-profile sources. It reads `generated/source_registry.jsonl` next to the database and never includes raw sample values.

4. **Oversized bundle fallback unchanged but verified**  
   The existing summary-only fallback remains; a new test confirms it returns truncated objects with only `object_id`, `object_type`, and `name` and drops relationship refs.

## Tests added

Created `tests/test_ai_context_builder.py` with:

- `TestSingleTracePerSeed`
  - `test_trace_object_called_once_per_seed`: asserts `trace_object` is called exactly once per seed and nodes/edges come from that call.
  - `test_nodes_and_edges_from_single_trace`: asserts one seed trace yields both nodes and edges.
- `TestCompactObjectsPriority`
  - `test_validation_errors_priority`: object with validation error sorts before same-type objects without errors.
  - `test_same_type_priority_without_errors`: baseline behavior unchanged.
- `TestIncludedSourcesRedacted`
  - `test_includes_redacted_source_metadata`: source metadata present, raw samples absent.
  - `test_summary_only_excludes_sources`: `summary_only` policy yields empty `included_sources`.
- `TestOversizedBundleSummaryFallback`
  - `test_returns_summary_only_when_over_budget`: confirms fallback warning and truncated output.
- `TestContextBundle`
  - `test_bundle_metadata` and `test_empty_bundle_when_db_missing` sanity checks.

## TDD RED/GREEN evidence

Initial focused run (RED):

```
5 failed, 4 passed
- trace_object called 4 times instead of 2
- trace_object called 2 times instead of 1
- _compact_objects did not accept validation_summary
- included_sources was empty for redacted policy
```

After implementation (GREEN):

```
35 passed in 0.19s
```

Full validation ladder (GREEN):

```
1387 passed, 3 skipped, 7 warnings in 50.54s
All checks passed!  (ruff)
```

## Files changed

- `src/modelops_core/ai/context_builder.py` — implementation
- `tests/test_ai_context_builder.py` — new tests

## Self-review findings

- The trace refactor eliminates redundant DB/Graph traversal and is a minimal, focused change.
- Validation priority now actually influences object ordering; previous code returned `(type_priority, 0)` for every object.
- Source metadata is intentionally redacted: only counts and inferred types are exposed, never sample values.
- The heuristic for source linkage is lightweight: it matches `source_id` to included object IDs and falls back to all `dataset_profile` entries in the registry. This could be tightened further by reading object frontmatter for explicit `dataset_id` references if the data model evolves.
- All new code follows the project's 100-character line length and Python 3.11 conventions.

## Issues or concerns

None blocking. The source linkage heuristic is broader than a strict object-to-source reference graph, but it matches the brief's allowance for a "lightweight heuristic such as sources referenced in source_registry" and preserves privacy by never emitting raw samples.

## Commits

- `bc0dd5c` Task 1.3: Harden AI context builder
