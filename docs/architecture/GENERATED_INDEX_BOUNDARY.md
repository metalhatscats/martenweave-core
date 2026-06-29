# Generated Index Boundary

## Generated Artifacts

Generated artifacts are rebuildable outputs, usually under a repository's `generated/` directory:

- `modelops.db`
- `search_documents.jsonl`
- `lineage_edges.jsonl`
- `audit_events.jsonl`
- generated Markdown docs from `docs-build`
- generated local static viewer files from `docs-build`:
  - `index.html`
  - `objects.html`
  - `objects/<safe-object-id>.html`
  - `gaps.html`
  - `decisions.html`
  - `owners.html`
  - `assets/viewer.css`
  - `assets/viewer.js`
  - `search-index.json`
  - `viewer-manifest.json`
- dataset profiles
- exports and reports

## Rules

- Generated artifacts are never the source of model truth.
- Do not manually edit generated artifacts to fix behavior.
- Rebuild generated artifacts from canonical files.
- Do not commit generated files unless the task explicitly requires fixtures.
- If generated files change during validation, inspect and discard unless intentionally part of the task.
- The local static viewer is read-only generated output. It must not become a hosted UI, login
  surface, editor, SAP write-back path, or AI auto-mutation workflow.
- Viewer pages may warn about stale indexes, but freshness warnings do not make generated artifacts
  canonical.

## Commands

```bash
.venv/bin/martenweave build-index --repo examples/customer_bp_model --jsonl
.venv/bin/martenweave build-index --repo examples/simple_product_model --jsonl
.venv/bin/martenweave docs-build --repo examples/customer_bp_model --site /tmp/martenweave-viewer
```

Index build must fail clearly when canonical files contain blocking validation errors, unless an explicit allow-invalid path is used for diagnostics.

`docs-build` also fails clearly when `modelops.db` is missing. Rebuild the index first, then
regenerate the viewer. Search in the viewer is local and does not require `fetch`, a web server, or
external assets.
