# Local Static Viewer

`martenweave docs-build` generates a local, static, read-only viewer from the SQLite index.
It is a disposable generated artifact, not a hosted product UI.

## Build

Build the index first:

```bash
.venv/bin/martenweave build-index --repo examples/customer_bp_model --jsonl
```

Then generate the Markdown docs and HTML viewer:

```bash
.venv/bin/martenweave docs-build \
  --repo examples/customer_bp_model \
  --site /tmp/martenweave-viewer
```

`--site` is an alias for the existing `--output` option, so older commands still work:

```bash
.venv/bin/martenweave docs-build \
  --repo examples/customer_bp_model \
  --output generated/docs_site
```

## Generated pages

The output includes:

- `index.html` — dashboard with repository metadata, type counts, validation counts, freshness,
  and quick search
- `objects.html` — searchable object list
- `objects/<safe-object-id>.html` — one detail page per indexed object
- `gaps.html` — deterministic model gaps, validation findings, ownership/coverage signals, and
  canonical Issues
- `decisions.html` — Decisions, evidence references, and evidence coverage
- `owners.html` — ownership coverage, owner workload, and missing-owner objects
- `assets/viewer.css` and `assets/viewer.js`
- `search-index.json`
- `viewer-manifest.json`

Search is local and filters embedded rows, so the viewer works from `file://` as well as from a
local HTTP server.

## Boundaries

- Canonical Markdown + YAML files in `model/` remain authoritative.
- `modelops.db`, generated Markdown, generated HTML, and JSON viewer artifacts are rebuildable.
- The viewer is static and read-only: it has no login, hosted service, editing workflow, SAP
  write-back, telemetry, external fonts/CDNs, or AI auto-mutation path.
- Stale indexes still generate, but the pages and manifest show a prominent stale-index warning.
- Missing indexes fail clearly; run `martenweave build-index` first.

## Local preview

Open the files directly or serve the folder locally:

```bash
cd /tmp/martenweave-viewer
python3 -m http.server 8000
```

Then open <http://127.0.0.1:8000/>.
