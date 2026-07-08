# Task 5: Verification and example repo validation — Report

## Status

DONE

## Summary

All verification steps passed after fixing two implementation gaps discovered
during the smoke test:

1. The CLI `--semantic` search was only reranking keyword candidates, so objects
   that did not contain the literal query terms were never surfaced. The search
   now scores the full semantic index while still applying the same type/status/
   domain/tag filters.
2. The TF-IDF tokenizer used exact token matching, so "grouping" did not match
   "group". A conservative English stemmer was added, and IDF smoothing was added
   so common terms in small corpora still contribute non-zero weight.

A stale CLI-structure test expectation was also updated to include the existing
`ai-provider` and `agent-loop` top-level commands present in this branch.

## Commits

- `1ebbb27` — fix(semantic-search): full-index semantic search, stemming, IDF smoothing

## Step 1 — Focused tests

Command:

```bash
PYTHONPATH=src /Users/dzmitryikharlanau/Developments/martenweave/.venv/bin/python \
  -m pytest tests/test_semantic_search.py tests/test_query_service.py tests/test_index_builder.py -v
```

Result: **79 passed in 0.41s**

## Step 2 — Full validation ladder

Command:

```bash
PYTHONPATH=src /Users/dzmitryikharlanau/Developments/martenweave/.venv/bin/python -m pytest -q && \
PYTHONPATH=src /Users/dzmitryikharlanau/Developments/martenweave/.venv/bin/python -m ruff check .
```

Result:

- pytest: **1454 passed, 3 skipped, 7 warnings in 53.97s**
- ruff: **All checks passed!**

## Step 3 — Example repo smoke test

Command:

```bash
PYTHON=/Users/dzmitryikharlanau/Developments/martenweave/.venv/bin/python
PYTHONPATH=src $PYTHON -m modelops_core.cli build-index --repo examples/customer_bp_model --jsonl
PYTHONPATH=src $PYTHON -m modelops_core.cli search "customer grouping" \
  --repo examples/customer_bp_model --semantic --json
```

Result:

- Index built: 85 objects, valid.
- Total semantic results: 50
- `ATTR-CUST-SALES-CUSTOMER-GROUP` rank: **10**
- `FEP-S4-KNVV-KDGRP` rank: **11**
- Both expected object IDs appear in the results.

Top 15 results:

```
1.  ATTR-BP-SALES-AREA-PRICE-GROUP
2.  FEP-LEGACY-CUST-GROUP
3.  VLIST-S4-CUST-GROUP
4.  VLIST-LEGACY-CUST-GROUP
5.  MAP-CUST-GROUP-LEGACY-TO-KNVV-KDGRP
6.  USE-BP-SALES-AREA-PRICE-GROUP-S4
7.  USE-CUST-SALES-CUSTOMER-GROUP-S4
8.  VAL-CUST-GROUP-ALLOWED-VALUES
9.  FEP-MIGFILE-CUSTOMER-GROUP
10. ATTR-CUST-SALES-CUSTOMER-GROUP  <-- expected
11. FEP-S4-KNVV-KDGRP               <-- expected
12. VMAP-CUST-GROUP-LEGACY-TO-S4
13. EVI-CH01-A17-ANALYSIS
14. DEC-CH01-A17-CUSTOMER-GROUP
15. MAPSET-CUSTOMER-BP
```

## Deviations / notes

- The smoke-test commands must be run with `PYTHONPATH=src`; otherwise the venv's
  installed `modelops_core` (from the main worktree) is used, which lacks the
  `--semantic` flag on `search`.
- `numpy` acceleration remains deferred, as noted in the task brief.

## Files changed

- `src/modelops_core/index/semantic_search.py` — conservative stemming + IDF smoothing
- `src/modelops_core/index/query_service.py` — `expand_candidate_ids` parameter
- `src/modelops_core/cli.py` — semantic search across full index with filter preservation
- `tests/test_cli_structure.py` — updated expected top-level commands
