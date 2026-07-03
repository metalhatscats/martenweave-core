# User App Audit — martenweave-core

**Date:** 2026-06-29
**Auditor:** Kimi Code CLI
**Repository:** `metalhatscats/martenweave-core`
**Version audited:** `0.4.1`
**Evidence folder:** [`docs/audits/user-app-audit-evidence-2026-06-29/`](./user-app-audit-evidence-2026-06-29/)

---

## 1. Executive Summary

**App status: PARTIALLY USABLE as a user-facing product.**

martenweave-core is explicitly a **CLI-driven, backend-first core library**. The README and AGENTS.md repeatedly state that *"No hosted or editable product UI is included."* Therefore this audit treats the **CLI, the optional local API server (`serve`), the optional MCP server (`mcp`), and the generated static read-only HTML viewer (`docs-build`)** as the user-facing surfaces.

What is present works for a technical user who reads the docs first:

- The CLI install, validation, indexing, search, query, trace, impact, health, scorecard, dataset profiling, and gap-detection flows all run without crashing.
- The generated static viewer renders correctly on desktop, tablet, and mobile, with working local search and navigation.
- The local API server exposes a small but functional set of read endpoints.
- The test suite is green (`1331 passed, 3 skipped`) and linting passes.

However, a new user will hit friction quickly:

- The `propose-patch` flow returns an empty proposal with the default adapter, with no explanation of how to enable a real AI provider.
- Several CLI outputs are confusing or contradictory (e.g. `index-fresh` says "fresh" while listing "Stale sources").
- Error messages for missing/broken inputs are inconsistent: some commands return clear errors, others silently report zero results.
- The static viewer is read-only by design, so there is no true "create/edit/save" user journey in the browser.
- Accessibility is basic: focus works, but there is no skip link, ARIA landmarks are missing, and the favicon 404s.

**Bottom line:** The product is solid for its stated scope (backend/agent integration surface) but not yet a self-explanatory, standalone user application. The next slice should make the first 15 minutes obvious to a non-expert and tighten the CLI/API error contract.

---

## 2. What Works Well

| Area | Evidence | Notes |
|---|---|---|
| **Installation** | [`cli-logs/01-help.txt`](./user-app-audit-evidence-2026-06-29/cli-logs/01-help.txt) | `pip install -e .` already done; `martenweave --version` returns `0.4.1`. |
| **Validation** | [`cli-logs/02-validate.txt`](./user-app-audit-evidence-2026-06-29/cli-logs/02-validate.txt) | `validate` runs cleanly with 0 errors and clear warning codes/suggested fixes. |
| **Indexing** | [`cli-logs/03-build-index.txt`](./user-app-audit-evidence-2026-06-29/cli-logs/03-build-index.txt) | `build-index --jsonl` produces `modelops.db`, `search_documents.jsonl`, `lineage_edges.jsonl`. |
| **Static viewer generation** | [`cli-logs/04-docs-build.txt`](./user-app-audit-evidence-2026-06-29/cli-logs/04-docs-build.txt) | `docs-build --site` creates a complete static site in one command. |
| **Search / query** | [`cli-logs/05-search.txt`](./user-app-audit-evidence-2026-06-29/cli-logs/05-search.txt), [`06-query.txt`](./user-app-audit-evidence-2026-06-29/cli-logs/06-query.txt) | Keyword search returns scored results; structured query filters by type. |
| **Trace / impact** | [`cli-logs/07-trace.txt`](./user-app-audit-evidence-2026-06-29/cli-logs/07-trace.txt), [`08-impact.txt`](./user-app-audit-evidence-2026-06-29/cli-logs/08-impact.txt) | Both commands run and show related objects. |
| **Health / scorecard / gaps** | [`cli-logs/09-health.txt`](./user-app-audit-evidence-2026-06-29/cli-logs/09-health.txt), [`10-scorecard.txt`](./user-app-audit-evidence-2026-06-29/cli-logs/10-scorecard.txt), [`11-gap-report.txt`](./user-app-audit-evidence-2026-06-29/cli-logs/11-gap-report.txt), [`13-gaps.txt`](./user-app-audit-evidence-2026-06-29/cli-logs/13-gaps.txt) | Dataset profiling and gap detection produce a readable coverage table. |
| **API server** | [`cli-logs/api-server.log`](./user-app-audit-evidence-2026-06-29/cli-logs/api-server.log), `api-*.json` | All tested endpoints returned correct HTTP status codes and JSON. |
| **Static viewer UI** | `screenshots/viewer-desktop-*.png`, `viewer-mobile-*.png`, `viewer-tablet-*.png` | Pages load, search filters instantly, navigation works, responsive layout collapses cleanly. |
| **Test suite** | See "Validation commands run" | `pytest` passes; `ruff check` passes. |

---

## 3. Critical Blockers

None of the tested paths crash, but the following block a smooth first-time user experience:

1. **`propose-patch` produces empty proposals with no guidance.**
   - Command: `martenweave propose-patch --from note.md --repo examples/simple_product_model --dry-run`
   - Output: `Candidate has no operations.`
   - File: [`cli-logs/14-propose-patch-dry-run.txt`](./user-app-audit-evidence-2026-06-29/cli-logs/14-propose-patch-dry-run.txt)
   - Impact: The demo path in `docs/demo-quickstart-flow.md` promises a governance shape, but a new user cannot get a proposal without configuring an AI provider. The CLI does not explain this.

2. **`index-fresh` output is contradictory.**
   - Output starts with `Index freshness: fresh` then lists `Stale sources: 1 file(s)`.
   - File: [`cli-logs/edge-05-stale-index.txt`](./user-app-audit-evidence-2026-06-29/cli-logs/edge-05-stale-index.txt)
   - Impact: Users cannot tell whether they need to rebuild the index.

3. **No interactive create/edit/save journey in the browser.**
   - The static viewer is read-only by design. There are no forms, no edit buttons, no save flow.
   - This is documented, but it means the audit scenarios for "core creation flow" and "edit/update flow" must be performed via CLI file editing, which is not the expected web-app experience.

---

## 4. UX Friction Points

| # | Finding | Severity | Evidence |
|---|---|---|---|
| 1 | `propose-patch` gives no hint that an AI provider must be configured. | High | [`cli-logs/14-propose-patch-dry-run.txt`](./user-app-audit-evidence-2026-06-29/cli-logs/14-propose-patch-dry-run.txt) |
| 2 | `index-fresh` says "fresh" and "Stale sources" in the same report. | Medium | [`cli-logs/edge-05-stale-index.txt`](./user-app-audit-evidence-2026-06-29/cli-logs/edge-05-stale-index.txt) |
| 3 | `impact NONEXISTENT-ID` returns a report with 0 affected objects instead of "object not found". | Medium | [`cli-logs/edge-04-impact-invalid-id.txt`](./user-app-audit-evidence-2026-06-29/cli-logs/edge-04-impact-invalid-id.txt) |
| 4 | `trace invalid-id-format` reports "No related objects found" without validating the ID format. | Low | [`cli-logs/edge-10-invalid-id-format.txt`](./user-app-audit-evidence-2026-06-29/cli-logs/edge-10-invalid-id-format.txt) |
| 5 | `docs-build` error message wraps the path across lines (`No index found at \n/private/... Run \n...`). | Low | [`cli-logs/edge-01-docs-build-no-index.txt`](./user-app-audit-evidence-2026-06-29/cli-logs/edge-01-docs-build-no-index.txt) |
| 6 | `help` text for 60+ commands is dense; there is no `martenweave tutorial` or `martenweave first-run` command. | Low | [`cli-logs/01-help.txt`](./user-app-audit-evidence-2026-06-29/cli-logs/01-help.txt) |
| 7 | Static viewer search has no URL sync, so users cannot share or bookmark a filtered view. | Low | Screenshots |
| 8 | Static viewer object detail pages have no "copy link" or "open in canonical file" action. | Low | Screenshots |

---

## 5. Reliability Issues

| # | Finding | Severity | Evidence |
|---|---|---|---|
| 1 | `index-fresh` contradiction (see above) undermines trust in freshness checks. | Medium | [`cli-logs/edge-05-stale-index.txt`](./user-app-audit-evidence-2026-06-29/cli-logs/edge-05-stale-index.txt) |
| 2 | `impact` on unknown IDs does not fail; it silently returns empty results. This could hide typos in scripts. | Medium | [`cli-logs/edge-04-impact-invalid-id.txt`](./user-app-audit-evidence-2026-06-29/cli-logs/edge-04-impact-invalid-id.txt) |
| 3 | API `/impact/{obj_id}` returns 200 with empty lists for unknown IDs (same silent behavior). | Medium | Manual API test |
| 4 | `build-index` output wraps paths in the middle, which makes log parsing fragile. | Low | [`cli-logs/03-build-index.txt`](./user-app-audit-evidence-2026-06-29/cli-logs/03-build-index.txt) |
| 5 | No retry/timeout configuration is exposed for `serve` or `mcp` commands. | Low | `src/modelops_core/cli.py:4504-4554` |

---

## 6. Console / Network Errors

| Source | Error / Warning | Severity | Notes |
|---|---|---|---|
| Static viewer (all pages) | `Failed to load resource: 404 (File not found) @ http://127.0.0.1:8002/favicon.ico` | Low | Cosmetic; no favicon is shipped. |
| Static viewer | No other console errors or warnings. | — | JS search works without errors. |
| API server | No errors in server log; all endpoints returned expected status codes. | — | [`cli-logs/api-server.log`](./user-app-audit-evidence-2026-06-29/cli-logs/api-server.log) |
| CLI | Deprecation warnings in tests only (`modelops_core.patching.change_request_service` deprecated). | Low | Not visible to end users. |

---

## 7. Mobile / Responsive Issues

| Viewport | Result | Evidence |
|---|---|---|
| Desktop (1280×720) | PASS. Layout is clean, nav visible, cards grid works. | `viewer-desktop-index.png` |
| Tablet (768×1024) | PASS. Grid collapses to fewer columns; nav wraps. | `viewer-tablet-index.png` |
| Mobile (375×667) | PARTIAL. Layout stacks correctly, but tables require horizontal scroll and the search box is full-width and easy to tap. | `viewer-mobile-index.png`, `viewer-mobile-objects.png` |

**Specific issues:**

- Tables on mobile overflow horizontally (acceptable for data-heavy pages, but no sticky column indicator).
- The nav pills wrap and take significant vertical space on very small screens.
- No viewport zoom disabled; good.

---

## 8. Accessibility Issues

| # | Finding | Severity | Evidence |
|---|---|---|---|
| 1 | No `<main>` landmark or `role="main"` on viewer pages. | Medium | `src/modelops_core/docs/static_doc_generator.py` `_write_page` |
| 2 | No skip link for keyboard users. | Medium | Viewer screenshots |
| 3 | Search input has no associated `<label>`; only a `placeholder`. | Medium | `viewer-desktop-objects.png` |
| 4 | Focus outline is visible on links but very subtle on the search box. | Low | `viewer-desktop-focus-state.png` |
| 5 | Color contrast for `.muted` text (`#64748b` on `#ffffff`) is borderline but generally passes WCAG AA for large text. | Low | CSS in `static_doc_generator.py:65` |
| 6 | Tables lack `scope` attributes and captions. | Low | Generated HTML |
| 7 | No `aria-current` on active nav item despite CSS selector existing. | Low | `static_doc_generator.py:102` |

---

## 9. Performance Concerns

| # | Finding | Severity | Evidence |
|---|---|---|---|
| 1 | Static viewer pages are small (~8–12 KB HTML) and fast. No issues. | — | `/tmp/martenweave-viewer-simple/*.html` |
| 2 | Search is local JS filtering; no network round-trip. Fast on 14 objects. | — | Browser testing |
| 3 | API endpoints read the filesystem on every request (`scan_repository` + `parse_file`). This will slow down as model size grows. | Medium | `src/modelops_core/api/app.py:53-74` |
| 4 | `objects.html` embeds all search terms in every row; for 10k+ objects this could bloat page size. | Low | `static_doc_generator.py:699-714` |
| 5 | No caching headers or ETag on API responses. | Low | API testing |

---

## 10. Scenario Matrix

| Scenario | Status | Notes |
|---|---|---|
| 1. First impression: understand app in 30 seconds | PARTIAL | README and docs are clear, but only if the user already knows it is CLI-first. No landing page explains it to a non-technical user. |
| 2. Navigation: reach all important areas | PASS | CLI help lists all commands; viewer has persistent top nav. |
| 3. Core creation flow: create the main object | PARTIAL | `init` scaffolds a repo; creating real objects requires hand-editing Markdown/YAML or running import commands. No guided creation UI. |
| 4. Edit/update flow: change saved data and verify persistence | PARTIAL | Edit canonical `.md` files directly, then `validate` + `build-index`. No browser edit flow. |
| 5. Search/discovery flow | PASS | `search` and `query` CLI commands work; viewer search filters instantly. |
| 6. Detail view flow: open an item and understand context | PASS | Object detail pages show facts, owners, description, body, relationships, mappings. |
| 7. Empty states: pages before data exists | PASS | Empty repo viewer renders with 0 objects and explanatory text. Empty API responses return `[]` or clear messages. |
| 8. Error states: invalid input, missing required fields, failed action | PARTIAL | Missing files return clear errors; invalid IDs often return empty results instead of errors. |
| 9. Responsiveness: desktop, tablet, mobile | PASS / PARTIAL | Desktop/tablet good; mobile tables require scroll. |
| 10. Reliability: refresh, reload, restart backend, data survives | PASS | Static viewer is stateless; canonical files survive; rebuilding index restores everything. |
| 11. Performance: slow pages or heavy payloads | PASS | No visible slowness at this model size. |
| 12. Accessibility basics | PARTIAL | Keyboard focus works, but labels, landmarks, and skip links are missing. |

---

## 11. Click-Count Table for Key Flows

Because the product is CLI-first, "clicks" are measured as command invocations + key interactions.

| Flow | Steps / Clicks | Observations |
|---|---|---|
| Install + first help | 2 (`pip install -e .`, `martenweave --help`) | Straightforward. |
| Validate example model | 1 (`martenweave validate --repo examples/simple_product_model`) | Immediate feedback. |
| Build index | 1 (`martenweave build-index --repo ... --jsonl`) | One command. |
| Generate local viewer | 1 (`martenweave docs-build --repo ... --site ...`) | One command. |
| Open viewer → search → open object | 3 (navigate URL, type search, click object) | Smooth. |
| Dataset profile → gap report | 2 (`profile-dataset`, `gaps`) | Works end-to-end. |
| Create a proposal from a note | 1 (`propose-patch --dry-run`) | **Fails to produce useful output** with default adapter. |
| Trace an object | 1 (`trace ATTR-PRODUCT-NAME`) | Works. |
| Impact analysis | 1 (`impact DOMAIN-PRODUCT`) | Works. |
| Start API server + query health | 2 (`serve`, `curl /health`) | Works. |

---

## 12. Screenshots / Evidence Links

All evidence is in [`docs/audits/user-app-audit-evidence-2026-06-29/`](./user-app-audit-evidence-2026-06-29/).

### CLI logs

- [`cli-logs/01-help.txt`](./user-app-audit-evidence-2026-06-29/cli-logs/01-help.txt)
- [`cli-logs/02-validate.txt`](./user-app-audit-evidence-2026-06-29/cli-logs/02-validate.txt)
- [`cli-logs/03-build-index.txt`](./user-app-audit-evidence-2026-06-29/cli-logs/03-build-index.txt)
- [`cli-logs/04-docs-build.txt`](./user-app-audit-evidence-2026-06-29/cli-logs/04-docs-build.txt)
- [`cli-logs/05-search.txt`](./user-app-audit-evidence-2026-06-29/cli-logs/05-search.txt)
- [`cli-logs/06-query.txt`](./user-app-audit-evidence-2026-06-29/cli-logs/06-query.txt)
- [`cli-logs/07-trace.txt`](./user-app-audit-evidence-2026-06-29/cli-logs/07-trace.txt)
- [`cli-logs/08-impact.txt`](./user-app-audit-evidence-2026-06-29/cli-logs/08-impact.txt)
- [`cli-logs/09-health.txt`](./user-app-audit-evidence-2026-06-29/cli-logs/09-health.txt)
- [`cli-logs/10-scorecard.txt`](./user-app-audit-evidence-2026-06-29/cli-logs/10-scorecard.txt)
- [`cli-logs/11-gap-report.txt`](./user-app-audit-evidence-2026-06-29/cli-logs/11-gap-report.txt)
- [`cli-logs/12-profile-dataset.txt`](./user-app-audit-evidence-2026-06-29/cli-logs/12-profile-dataset.txt)
- [`cli-logs/13-gaps.txt`](./user-app-audit-evidence-2026-06-29/cli-logs/13-gaps.txt)
- [`cli-logs/14-propose-patch-dry-run.txt`](./user-app-audit-evidence-2026-06-29/cli-logs/14-propose-patch-dry-run.txt)
- [`cli-logs/15-init-empty-repo.txt`](./user-app-audit-evidence-2026-06-29/cli-logs/15-init-empty-repo.txt)
- [`cli-logs/16-validate-empty-repo.txt`](./user-app-audit-evidence-2026-06-29/cli-logs/16-validate-empty-repo.txt)

### API logs

- [`cli-logs/api-server.log`](./user-app-audit-evidence-2026-06-29/cli-logs/api-server.log)
- [`cli-logs/api-01-health.json`](./user-app-audit-evidence-2026-06-29/cli-logs/api-01-health.json)
- [`cli-logs/api-02-objects-attribute.json`](./user-app-audit-evidence-2026-06-29/cli-logs/api-02-objects-attribute.json)
- [`cli-logs/api-03-object-detail.json`](./user-app-audit-evidence-2026-06-29/cli-logs/api-03-object-detail.json)
- [`cli-logs/api-04-validate.json`](./user-app-audit-evidence-2026-06-29/cli-logs/api-04-validate.json)
- [`cli-logs/api-05-trace.json`](./user-app-audit-evidence-2026-06-29/cli-logs/api-05-trace.json)
- [`cli-logs/api-06-impact.json`](./user-app-audit-evidence-2026-06-29/cli-logs/api-06-impact.json)
- [`cli-logs/api-07-proposals.json`](./user-app-audit-evidence-2026-06-29/cli-logs/api-07-proposals.json)
- [`cli-logs/api-08-object-not-found.txt`](./user-app-audit-evidence-2026-06-29/cli-logs/api-08-object-not-found.txt)
- [`cli-logs/api-09-empty-repo-trace.txt`](./user-app-audit-evidence-2026-06-29/cli-logs/api-09-empty-repo-trace.txt)
- [`cli-logs/api-10-empty-repo-health.json`](./user-app-audit-evidence-2026-06-29/cli-logs/api-10-empty-repo-health.json)
- [`cli-logs/api-11-empty-repo-objects.json`](./user-app-audit-evidence-2026-06-29/cli-logs/api-11-empty-repo-objects.json)
- [`cli-logs/api-12-export-csv.json`](./user-app-audit-evidence-2026-06-29/cli-logs/api-12-export-csv.json)

### Edge-case logs

- [`cli-logs/edge-01-docs-build-no-index.txt`](./user-app-audit-evidence-2026-06-29/cli-logs/edge-01-docs-build-no-index.txt)
- [`cli-logs/edge-02-build-index-empty.txt`](./user-app-audit-evidence-2026-06-29/cli-logs/edge-02-build-index-empty.txt)
- [`cli-logs/edge-03-search-empty.txt`](./user-app-audit-evidence-2026-06-29/cli-logs/edge-03-search-empty.txt)
- [`cli-logs/edge-04-impact-invalid-id.txt`](./user-app-audit-evidence-2026-06-29/cli-logs/edge-04-impact-invalid-id.txt)
- [`cli-logs/edge-05-stale-index.txt`](./user-app-audit-evidence-2026-06-29/cli-logs/edge-05-stale-index.txt)
- [`cli-logs/edge-06-empty-search.txt`](./user-app-audit-evidence-2026-06-29/cli-logs/edge-06-empty-search.txt)
- [`cli-logs/edge-07-missing-dataset.txt`](./user-app-audit-evidence-2026-06-29/cli-logs/edge-07-missing-dataset.txt)
- [`cli-logs/edge-08-missing-repo.txt`](./user-app-audit-evidence-2026-06-29/cli-logs/edge-08-missing-repo.txt)
- [`cli-logs/edge-09-docs-build-empty.txt`](./user-app-audit-evidence-2026-06-29/cli-logs/edge-09-docs-build-empty.txt)
- [`cli-logs/edge-10-invalid-id-format.txt`](./user-app-audit-evidence-2026-06-29/cli-logs/edge-10-invalid-id-format.txt)
- [`cli-logs/edge-11-long-search.txt`](./user-app-audit-evidence-2026-06-29/cli-logs/edge-11-long-search.txt)
- [`cli-logs/edge-12-nonexistent-type.txt`](./user-app-audit-evidence-2026-06-29/cli-logs/edge-12-nonexistent-type.txt)
- [`cli-logs/mcp-import.txt`](./user-app-audit-evidence-2026-06-29/cli-logs/mcp-import.txt)
- [`cli-logs/mcp-start.txt`](./user-app-audit-evidence-2026-06-29/cli-logs/mcp-start.txt)
- [`cli-logs/viewer-console-errors.log`](./user-app-audit-evidence-2026-06-29/cli-logs/viewer-console-errors.log)

### Screenshots

- [`screenshots/viewer-desktop-index.png`](./user-app-audit-evidence-2026-06-29/screenshots/viewer-desktop-index.png)
- [`screenshots/viewer-desktop-objects.png`](./user-app-audit-evidence-2026-06-29/screenshots/viewer-desktop-objects.png)
- [`screenshots/viewer-desktop-objects-search.png`](./user-app-audit-evidence-2026-06-29/screenshots/viewer-desktop-objects-search.png)
- [`screenshots/viewer-desktop-object-detail.png`](./user-app-audit-evidence-2026-06-29/screenshots/viewer-desktop-object-detail.png)
- [`screenshots/viewer-desktop-gaps.png`](./user-app-audit-evidence-2026-06-29/screenshots/viewer-desktop-gaps.png)
- [`screenshots/viewer-desktop-decisions.png`](./user-app-audit-evidence-2026-06-29/screenshots/viewer-desktop-decisions.png)
- [`screenshots/viewer-desktop-owners.png`](./user-app-audit-evidence-2026-06-29/screenshots/viewer-desktop-owners.png)
- [`screenshots/viewer-desktop-focus-state.png`](./user-app-audit-evidence-2026-06-29/screenshots/viewer-desktop-focus-state.png)
- [`screenshots/viewer-tablet-index.png`](./user-app-audit-evidence-2026-06-29/screenshots/viewer-tablet-index.png)
- [`screenshots/viewer-mobile-index.png`](./user-app-audit-evidence-2026-06-29/screenshots/viewer-mobile-index.png)
- [`screenshots/viewer-mobile-objects.png`](./user-app-audit-evidence-2026-06-29/screenshots/viewer-mobile-objects.png)
- [`screenshots/viewer-empty-index.png`](./user-app-audit-evidence-2026-06-29/screenshots/viewer-empty-index.png)

---

## 13. Top 10 Prioritized Fixes

| Rank | Fix | Priority | Effort | File(s) |
|---|---|---|---|---|
| 1 | Make `propose-patch` explain why the proposal is empty and how to enable/configure an AI provider. | High | Small | `src/modelops_core/ai/patch_proposal_service.py`, `src/modelops_core/cli.py` |
| 2 | Resolve `index-fresh` contradiction: either report "stale" when sources are stale, or rename the section and explain hash-vs-mtime. | High | Small | `src/modelops_core/reports/index_freshness.py`, `src/modelops_core/cli.py` |
| 3 | `impact` and `trace` should validate the object ID exists and return a clear "not found" error with exit code 1. | High | Small | `src/modelops_core/impact/impact_service.py`, `src/modelops_core/trace/trace_service.py`, `src/modelops_core/cli.py` |
| 4 | API `/impact/{obj_id}` should return 404 for unknown objects instead of 200 with empty lists. | Medium | Small | `src/modelops_core/api/app.py:169-206` |
| 5 | Add a favicon to the static viewer to eliminate the 404 console error. | Low | Tiny | `src/modelops_core/docs/static_doc_generator.py` |
| 6 | Improve `docs-build` missing-index error formatting so the path is not split across lines. | Low | Tiny | `src/modelops_core/docs/static_doc_generator.py:269-272` |
| 7 | Add accessible labels/landmarks to viewer: `<main>`, `<label for="search">`, `aria-current`. | Medium | Small | `src/modelops_core/docs/static_doc_generator.py` |
| 8 | Cache API repository scans or load from SQLite index instead of re-parsing all canonical files on every request. | Medium | Medium | `src/modelops_core/api/app.py` |
| 9 | Add a `martenweave doctor` (already exists) first-run hint and link to `docs/first-15-minutes.md` in `--help` output. | Low | Small | `src/modelops_core/cli.py`, `docs/first-15-minutes.md` |
| 10 | Sync viewer search query to URL hash (`?q=...`) so filtered views are shareable. | Low | Small | `src/modelops_core/docs/static_doc_generator.py` `_VIEWER_JS` |

---

## 14. Recommended Next Implementation Slice

**Goal:** Make the first 15 minutes trustworthy for a new user.

1. **Fix the three high-priority CLI confusions above** (`propose-patch` empty-state message, `index-fresh` contradiction, `impact`/`trace` unknown-ID handling). These are small, isolated changes with immediate UX return.
2. **Add one guided onboarding command** — e.g. `martenweave demo --repo examples/simple_product_model` — that runs validate → build-index → docs-build → opens the viewer path, mirroring `docs/first-15-minutes.md`.
3. **Tighten the API error contract** for unknown IDs (404 from `/impact`, `/trace`, `/objects/{id}` already returns 404; align `/impact`).
4. **Ship a favicon and accessible labels** in the static viewer as a quick polish pass.

This slice does not require building a hosted UI; it improves the existing CLI-first surfaces that users already interact with.

---

## 15. Validation Commands Run

```bash
# Lint
.venv/bin/python -m ruff check .
# Result: All checks passed!

# Unit tests
.venv/bin/python -m pytest -q
# Result: 1331 passed, 3 skipped, 7 warnings in 52.36s
```

**Commands were re-run after evidence collection; results identical.**

---

## 16. Notes on Scope

- The product explicitly has **no hosted/editable UI**. Browser testing was performed on the generated static viewer and the local API server only.
- Forms, modals, editable fields, save buttons, and authentication flows do not exist and were not tested because they are not part of the product.
- The MCP server was verified to import and instantiate; full stdio/SSE testing was not performed because `timeout` is unavailable in this macOS environment and the server expects persistent stdio input.
