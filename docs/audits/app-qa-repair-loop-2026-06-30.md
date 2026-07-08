# Martenweave Frontend QA + Repair Loop

**Date:** 2026-06-30  
**Scope:** `frontend/` prototype (Vite + React + `@xyflow/react`, static demo data)  
**Tester:** QA + repair agent  
**Status:** PASS — core user flows are stable and validation is green.

---

## 1. Tested flows

All flows were exercised both manually and with browser automation (Kimi WebBridge + Playwright MCP).

- App loads cleanly on desktop and mobile.
- Sidebar and mobile hamburger navigation work across all seven routes.
- Home prompt box accepts input and shows the mocked evidence-backed answer.
- Global model search filters by query, object-type tabs, type filters, and status filters.
- Search result sorting (Relevance / Recently updated / Name) works.
- Empty-search state renders and clears.
- Object detail page opens; tabs switch; field count reflects demo data.
- Lineage canvas renders `@xyflow/react` nodes/edges; inspector panel opens/closes.
- Gaps list expands/collapses and links to proposals.
- Proposals list filters by status; proposal review page shows changes, impact, validation, activity.
- Approve / request-changes dialog opens, requires a reason for rejection, and navigates back.
- Responsive layouts are usable at 1440×900, 768×1024, and 375×812.
- Console and network inspected for errors on every route.

---

## 2. Commands run

```bash
# Install frontend dependencies
cd frontend && npm install

# Build the frontend
npm run build

# Python lint + full test suite (from repo root)
.venv/bin/python -m ruff check .
.venv/bin/python -m pytest

# Start a stable production preview server
npm run preview -- --port 4173
```

Browser automation was performed against `http://127.0.0.1:4173` after each rebuild.

---

## 3. Issues found

| Priority | Issue | Route / area |
|---|---|---|
| Medium | `favicon.ico` 404 console error on every load. | All |
| Medium | Browser tab title was generic `"Prototype"`. | All |
| Medium | Object detail showed `"Fields 24"` and `"View all 24"` while the demo `fields` array contains 5 items. | Object |
| Medium | Models search tab counts were hardcoded (`All 52`, `Objects 12`, etc.) and did not match demo data. | Models |
| Medium | Profile dropdown stayed open when clicking outside; no dismissal path. | Topbar |
| Medium | "View all" button in Home › Recent activity was dead (no handler). | Home |
| Medium | Sort dropdown did not sort results; status filter checkboxes did not filter. | Models |
| Low | `npm run dev` background task timed out after the default 600 s window. | Infrastructure |
| Low | Build emits a chunk-size warning (>500 kB) for the single JS bundle. | Build |

No Blocker or High issues were found.

---

## 4. Issues fixed

### 4.7 Topbar search query carry
- **Files:** `frontend/src/App.jsx`
- `useRoute()` now strips `?query` when resolving the current route name.
- `navigate(route, search)` accepts an optional query string and writes `/#/<route>?<search>`.
- Topbar search submit encodes the query as `search=<query>` and navigates to `models`.
- `ModelsScreen` reads `?search=` from the hash on first render and uses it as the initial query, falling back to the demo default `"business partner"`.

### 4.8 Mobile lineage inspector sizing
- **Files:** `frontend/src/styles.css`, `frontend/src/App.jsx`
- Changed the default `panelOpen` state in `LineageScreen` from `true` to `false` so the graph is visible first.
- In the `max-width: 680px` breakpoint, `.lineage-inspector` is now a floating card (`right:12px; bottom:12px; top:auto; width:min(260px,85vw); max-height:70vh; border-radius:14px`) instead of a full-height overlay.

### 4.9 Build chunk-size warning
- **File:** `frontend/vite.config.mjs`
- Added a `vendor` manual chunk containing `react`, `react-dom`, `@xyflow/react`, and `@phosphor-icons/react`.
- The warning is gone and the build now emits two JS chunks (`index` ~235 kB, `vendor` ~314 kB) instead of one >500 kB bundle.

### 4.1 Favicon + page title
- **File:** `frontend/index.html`
- Added `<link rel="icon" type="image/png" href="/martenweave-logo.png" />` using the existing public logo.
- Changed `<title>` to `"Martenweave · Prototype"`.

### 4.2 Object detail field counts
- **File:** `frontend/src/App.jsx`
- Replaced hardcoded `24` with `{fields.length}` in the Fields tab badge and the "View all" link.

### 4.3 Models search tab counts
- **File:** `frontend/src/App.jsx`
- Tab counts now derive from `modelObjects` (All, Objects = Domain|Entity, Fields = Attribute, Mappings = Mapping, Proposals = Proposal).

### 4.4 Profile menu dismissal
- **File:** `frontend/src/App.jsx`
- Added `useRef` + `useEffect` that closes the profile menu on clicks outside `.profile-wrap`.

### 4.5 Dead "View all" button
- **File:** `frontend/src/App.jsx`
- Removed the `action="View all"` prop from the Home › Recent activity rail section.

### 4.6 Functional sort and status filters
- **File:** `frontend/src/App.jsx`
- Implemented `updatedMinutes()` helper and wired the sort dropdown to sort by name or recency.
- Added `selectedStatuses` state and applied it to the memoized result list.
- Status filter counts now compute from `modelObjects`.
- "Clear search" and "Clear all" reset both type and status selections.

---

## 5. Remaining risks / known limitations

These are accepted prototype limitations, not regressions.

- **AI answers** are mocked static responses; real inference would require the backend core (`martenweave` CLI / API).
- **No persistence** — refreshing the browser resets all UI state.
- **Long-running `npm run dev`** can hit the background-task timeout; `npm run preview` is preferred for stable QA/demo.

---

## 6. Validation results

### Backend / Python
```
All checks passed!
1342 passed, 3 skipped, 7 warnings in 61.43s
```

### Frontend build (after follow-up pass)
```
vite v6.4.2 building for production...
✓ 4732 modules transformed.
dist/assets/index-D-g57X43.js   234.52 kB │ gzip: 69.97 kB
dist/assets/vendor-DYF2Wjre.js  314.22 kB │ gzip: 92.02 kB
✓ built in 2.33s
```

### Browser console (after fixes)
- Home: 0 errors
- Models: 0 errors
- Object: 0 errors
- Lineage: 0 errors
- Gaps: 0 errors
- Proposals: 0 errors
- Proposal review: 0 errors
- Mobile home + navigation: 0 errors
- Topbar search → Models: 0 errors
- Mobile lineage inspector (375×812): 0 errors

### Functional checks (automated)
- Navigation between all routes via sidebar and mobile menu: OK
- Search query, tab filters, type filters, status filters, sort: OK
- Empty state + clear: OK
- Object detail tabs + dynamic field count: OK
- Lineage canvas render + node selection: OK
- Gap expand/collapse + proposal link: OK
- Approval dialog open/close/confirm: OK
- Profile menu open/close-on-outside-click: OK
- Topbar search carries query into Models: OK
- Mobile lineage inspector opens as compact floating card: OK

---

## 7. Files changed

- `frontend/index.html`
- `frontend/src/App.jsx`
- `frontend/src/styles.css`
- `frontend/vite.config.mjs`
- `docs/audits/app-qa-repair-loop-2026-06-30.md` (this report)

No git commit was made per project policy; changes are local and ready for review.
