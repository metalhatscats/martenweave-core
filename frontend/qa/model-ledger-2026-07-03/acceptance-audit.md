# Martenweave workbench acceptance audit

Date: 2026-07-03

## App shell and navigation — passed

- Compact workbench navigation includes Workspace, Models, Lineage, Gaps, Proposals, Reports, and
  Settings.
- Global search, command palette, Import, Export, workspace activity, repository context, and user
  controls are active.
- Existing Martenweave logo is preserved.
- Evidence: `07-ledger-final.png`; `frontend/src/App.jsx`; `frontend/src/workbench.jsx`.

## Import / load workflow — passed

- Source types: canonical files, Excel mappings, dataset extracts, validation reports, and
  tickets/decisions/notes.
- States: source selection, file-access explanation, parsing progress, parsed summary, detected
  objects, detected gaps, deterministic validation, and safe load completion.
- Canonical truth safety is explicit before completion.
- Evidence: `04-import-flow.png`; Vitest sample import flow.

## Export workflow — passed

- Options: model index, gap report, impact report, lineage snapshot, patch proposal, and evidence
  summary.
- States: configuration, format selection, deterministic file naming, generated success, and local
  download.
- Evidence: Vitest export flow; `frontend/src/workbench.jsx`.

## Model object experience — passed

- Shows object identity, canonical ID, domain/type, owner, steward, lifecycle, status, definition,
  fields, validation, dataset coverage, connected systems, relationships, source evidence,
  downstream impact, open gap, and proposal.
- Export and proposal-draft actions are active.
- Evidence: `09-object-detail.png`; Object Detail route browser smoke test.

## Relationships and lineage — passed

- Nine graph nodes cover source systems, transformation, canonical model, downstream systems and
  datasets, governing decision, detected gap, and patch proposal.
- Search, depth, layer filters, selected-node inspector, zoom controls, MiniMap, object navigation,
  related gap navigation, and lineage export are active.
- Legend distinguishes source, transformation, canonical, target, gap, decision, and proposal.
- Evidence: `10-lineage.png`; browser check: nine nodes, seven legend categories, no overflow.

## Gap detection workflow — passed

- Each gap exposes missing knowledge, source/target context, severity, object, owner, evidence,
  recommendation, linked proposal, and next action.
- Filters cover severity, status, object, source, query, and sort.
- States represented in the demo data include In review, Draft, and Needs proposal; proposal
  drafting is active for unlinked gaps.
- Evidence: `11-gaps.png`; Gaps route browser smoke test.

## AI patch proposal review — passed

- Review includes reason, linked gap, risk, validation, changed objects, diff, impact, reviewers,
  notes, activity, approve, and request-changes states.
- Approval explicitly creates a governed change request and does not directly mutate canonical
  files.
- Review state updates visibly after a decision.
- Evidence: `12-proposal-review.png`; Vitest approval flow.

## Keyboard shortcuts — passed

- `/`: global search.
- Cmd/Ctrl + K: command palette.
- G then M/L/P/G: Models, Lineage, Proposals, Gaps.
- E: export current view.
- I: import.
- Escape: close overlays and panels.
- Enter: open selected ledger object.
- Cmd/Ctrl + Enter: open proposal approval review.
- `?`: shortcut help.
- Evidence: implementation in `frontend/src/App.jsx` and `frontend/src/workbench.jsx`; Vitest
  command, focus, selected-row, and G-then-M tests.

## Command palette — passed

- Commands cover object search, import, export, gaps, lineage, proposals, object opening, settings,
  and shortcut help.
- Supports text filtering, pointer selection, Arrow Up/Down, Enter, Escape, and Cmd/Ctrl + K.
- Evidence: `05-command-palette.png`; Vitest arrow-key execution test.

## Functional polish — passed

- No dead primary buttons across all routes.
- Inert field/evidence affordances were converted to non-button rows.
- Empty, loading, error/explanation, review, and success states are present.
- Browser route checks report no horizontal document overflow at 1280 px.
- Narrow check at 650 px reports no horizontal document overflow and uses mobile navigation.
- Browser console contains zero warnings/errors after all main routes and interactive flows.

## Visual fidelity — passed

- Model Ledger hierarchy, density, split workbench, status rail, selected-row drawer, semantic
  colors, Inter typography, and compact navigation match the selected visual target.
- Full comparison: `08-final-comparison.png`.
- Detailed QA: `frontend/design-qa.md` with `final result: passed`.

## Product restraint — passed

- No chatbot-led home, generic analytics dashboard, workflow engine, SAP write-back, or direct AI
  mutation was added.
- The prototype remains focused on canonical model truth, evidence, validation, indexes, gaps,
  lineage, impact, proposals, human review, and exports.

## Validation — passed

- Frontend: 9 Vitest tests passed.
- Frontend production build passed.
- Repository: 1,342 pytest tests passed, 3 skipped.
- Ruff: all checks passed.
- Browser: all nine routes loaded, no horizontal overflow at laptop width, no dead primary buttons,
  and zero console warnings/errors.

## Prototype boundary

Import parsing and export generation use realistic local demo data, as allowed by the brief.
Production file parsing, indexing, and canonical mutation remain owned by the existing backend/CLI
services and governed change-request workflow.
