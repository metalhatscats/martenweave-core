# Generated Index Boundary

## Generated Artifacts

Generated artifacts are rebuildable outputs, usually under a repository's `generated/` directory:

- `modelops.db`
- `search_documents.jsonl`
- `lineage_edges.jsonl`
- `audit_events.jsonl`
- dataset profiles
- exports and reports

## Rules

- Generated artifacts are never the source of model truth.
- Do not manually edit generated artifacts to fix behavior.
- Rebuild generated artifacts from canonical files.
- Do not commit generated files unless the task explicitly requires fixtures.
- If generated files change during validation, inspect and discard unless intentionally part of the task.

## Commands

```bash
.venv/bin/martenweave build-index --repo examples/customer_bp_model --jsonl
.venv/bin/martenweave build-index --repo examples/simple_product_model --jsonl
```

Index build must fail clearly when canonical files contain blocking validation errors, unless an explicit allow-invalid path is used for diagnostics.
