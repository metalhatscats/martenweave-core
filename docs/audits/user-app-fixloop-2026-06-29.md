# Martenweave User-App Fix-Loop Report — 2026-06-29

> Deep user-testing + fix-loop for `martenweave-core` 0.4.1.
> Surfaces tested: CLI, local API server, generated static viewer.

---

## Summary

This report documents a second pass over the user-facing surfaces of Martenweave.
The goal was to act as a real first-time user, run the full workflow, fix the
observed rough edges, add regression tests, and retest.

**Result:** All six known issues are fixed and retested. The full CLI/API/viewer
flow runs without silent failures or misleading messages. Test suite, linting,
and formatting all pass.

---

## Test Environment

| Item | Value |
|---|---|
| Package | `martenweave-core` 0.4.1 |
| Python | 3.11 |
| Virtual env | `/Users/dzmitryikharlanau/Developments/martenweave/.venv` |
| Test repo | `/tmp/martenweave-fixloop-repo` (copied from `examples/customer_bp_model`) |
| Viewer output | `/tmp/martenweave-fixloop-viewer` |
| Evidence folder | `docs/audits/user-app-fixloop-evidence-2026-06-29/` |

---

## User Flow Tested

```bash
martenweave validate --repo .
martenweave build-index --repo .
martenweave docs-build --repo . --site /tmp/martenweave-fixloop-viewer
martenweave search customer --repo .
martenweave query --repo . --type Attribute
martenweave trace FEP-S4-KNVV-KDGRP --repo .
martenweave impact DOMAIN-CUSTOMER-BP --repo .
martenweave gaps data/samples/customer_sales_area_sample.csv --repo .
martenweave propose-patch --from note.md --repo . --dry-run
martenweave index-fresh --repo .
```

After the CLI flow, the local API server was started and the static viewer was
served with `python -m http.server`. The viewer was exercised in a real browser
on desktop (1280×800) and mobile (390×844) viewports.

---

## Issues Found, Fixed, and Retested

### 1. `propose-patch --dry-run` showed an unclear error for generic notes

**Before:** A generic note with no configured AI provider produced a raw
`AIOutputValidationError: Candidate has no operations.` and the CLI printed that
low-level message.

**Fix:** `build_patch_proposal_from_note` now detects when the default
`NoProviderAdapter` cannot infer operations and returns a human-readable result
instead of raising. The CLI prints the assumption and a concrete next step.

**Files changed:**

- `src/modelops_core/ai/patch_proposal_service.py`
- `src/modelops_core/cli.py`

**After evidence:** `after/propose-patch-generic.txt`

```text
No proposal generated.
  • No AI provider is configured. The deterministic scaffold adapter could not
    infer operations from this note.
  → Set an AI provider (e.g. MARTENWEAVE_AI_PROVIDER=kimi), or include a
    recognized object ID and a concrete change ...
```

---

### 2. `index-fresh` could say "fresh" while still listing "Stale sources"

**Before:** When a canonical file was touched but its content did not change,
the service correctly reported `fresh: true`, but the CLI still printed
`Stale sources: 1 file(s)`, which looked contradictory.

**Fix:** The CLI presentation layer now distinguishes hash-mismatch staleness
from mtime-only drift. When the index is fresh, newer sources are labeled
"Sources newer than index: … (content hash matches; no rebuild needed)".

**Files changed:**

- `src/modelops_core/cli.py`

**After evidence:** `after/index-fresh-mtime.txt`

```text
Index freshness: fresh
  Sources newer than index: 1 file(s) (content hash matches; no rebuild needed)
    model/ATTR-CUST-SALES-CUSTOMER-GROUP.md
```

---

### 3. CLI `trace` and `impact` returned silent empty results for unknown IDs

**Before:** Running `trace` or `impact` on a non-existent object produced an
empty-looking table and exited with code `0`.

**Fix:** Both commands now check `root_object_type`. If the object is missing,
they print `Object not found: <id>` and exit with code `1`. JSON mode returns a
structured `error` field.

**Files changed:**

- `src/modelops_core/cli.py`

**After evidence:** `after/trace-unknown.txt`, `after/impact-unknown.txt`

```text
Object not found: DOES-NOT-EXIST
```

---

### 4. API `/impact/{id}` returned HTTP 200 for unknown objects

**Before:** The impact endpoint returned a 200 response with empty upstream/downstream
arrays when the object did not exist.

**Fix:** The endpoint now raises `HTTPException(status_code=404)` when
`report.root_object_type is None`. The same fix was applied to `/trace/{id}` for
consistency.

**Files changed:**

- `src/modelops_core/api/app.py`

**After evidence:** `after/api-smoke.txt`

```text
{"detail":"Object DOES-NOT-EXIST not found"}
HTTP 404
```

---

### 5. Static viewer lacked basic labels and landmarks

**Before:** The viewer had no `<main>` landmark, the navigation had no
`aria-label`, and the search/filter inputs had no accessible label.

**Fix:** Added `aria-label="Viewer navigation"` to the nav, wrapped content in
`<main class="shell">`, and gave the dashboard filter and object-list search
inputs `id="viewer-search"` plus `aria-label` attributes.

**Files changed:**

- `src/modelops_core/docs/static_doc_generator.py`

**After evidence:**

- `after/viewer-desktop-index.png`
- `after/viewer-desktop-objects.png`
- `after/viewer-mobile-index.png`
- `after/viewer-mobile-objects.png`

---

### 6. Static viewer produced a favicon 404

**Before:** The browser requested `/favicon.ico` and the server logged a 404.

**Fix:** Added an inline SVG favicon via a `data:` URI in the shared page
template.

**Files changed:**

- `src/modelops_core/docs/static_doc_generator.py`

**After evidence:** `after/viewer-console-errors.txt` shows zero console errors.

---

## Test Changes

Regression tests were added or updated for every fix:

| Test file | What changed |
|---|---|
| `tests/test_ai_patch_proposal_service.py` | Updated generic-note test to assert provider-configuration hint; added CLI dry-run test for generic notes. |
| `tests/test_provider_adapter.py` | Unchanged; adapter behavior preserved. |
| `tests/test_trace.py` | Added CLI unknown-ID tests (human and JSON). |
| `tests/test_impact_service.py` | Added CLI unknown-ID tests (human and JSON). |
| `tests/test_api.py` | Added `/impact/{id}` and `/trace/{id}` 404 tests. |
| `tests/test_index_fresh.py` | Added CLI test for fresh index with mtime-only drift. |
| `tests/test_docs_build.py` | Added tests for inline favicon, search-input label, landmark regions; updated link-safety test to ignore `data:` URIs. |

---

## Validation Results

```bash
ruff check .
ruff format --check .
pytest -q
```

- `ruff check .` — passed
- `ruff format --check .` — passed
- `pytest -q` — **1342 passed, 3 skipped, 7 warnings**

Additional smoke checks:

- CLI first-user flow completed end-to-end.
- API server `/health`, `/impact/DOMAIN-CUSTOMER-BP`, `/impact/DOES-NOT-EXIST`,
  `/trace/DOES-NOT-EXIST` behaved as expected.
- Static viewer generated, served, and clicked through on desktop and mobile.
- Browser console showed **0 errors** and no favicon 404.

---

## Remaining Risks / Not Addressed

These are intentionally out of scope for a small fix-loop, but worth noting:

1. **No hosted UI.** The product remains CLI/backend-first; the viewer is a
   read-only local artifact.
2. **AI provider is still a stub by default.** Real `propose-patch` behavior
   requires configuring `MARTENWEAVE_AI_PROVIDER` and credentials.
3. **Mobile navigation wraps.** The viewer nav bar wraps on narrow screens; this
   is acceptable for a generated diagnostic viewer but not a polished mobile app.
4. **Stale-index warnings on read commands are still emitted as text/JSON flags;**
   they do not block execution.
5. **No git commit was made** for this fix-loop; changes are local only.

---

## Evidence

All captured evidence lives in:

```text
docs/audits/user-app-fixloop-evidence-2026-06-29/
├── before/   # baseline screenshots and logs from the first audit pass
└── after/    # post-fix CLI logs, API smoke output, and browser screenshots
```

Key after artifacts:

- `after/validate.txt`, `after/build-index.txt`, `after/docs-build.txt`
- `after/trace-unknown.txt`, `after/impact-unknown.txt`
- `after/propose-patch-generic.txt`, `after/index-fresh-mtime.txt`
- `after/api-smoke.txt`, `after/api-server.log`
- `after/viewer-desktop-index.png`, `after/viewer-desktop-objects.png`,
  `after/viewer-desktop-objects-search.png`
- `after/viewer-mobile-index.png`, `after/viewer-mobile-objects.png`
- `after/viewer-console-errors.txt`

---

## Appendix: Source Files Touched

- `src/modelops_core/cli.py`
- `src/modelops_core/api/app.py`
- `src/modelops_core/ai/patch_proposal_service.py`
- `src/modelops_core/docs/static_doc_generator.py`
- `tests/test_ai_patch_proposal_service.py`
- `tests/test_trace.py`
- `tests/test_impact_service.py`
- `tests/test_api.py`
- `tests/test_index_fresh.py`
- `tests/test_docs_build.py`

No commit was created per the current workflow constraints.
