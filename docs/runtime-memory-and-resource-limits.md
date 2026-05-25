# Runtime Memory Budgets and Resource Limits

Martenweave is designed to run locally on a developer laptop without cloud dependencies. This document defines the v1 resource budgets and explains how to configure, override, and recover from limit violations.

## Memory Model

| Layer | What it is | Persistence | Typical size |
|---|---|---|---|
| **Canonical files** | Markdown + YAML frontmatter objects in `model/` | Git-tracked source of truth | Kilobytes to tens of MB |
| **Generated index** | SQLite DB, JSONL exports in `generated/` | Rebuildable disposable artifacts | Similar to canonical files |
| **Runtime memory** | Parsed objects, relationship graphs, profiles | In-memory only during command execution | Bounded by limits below |
| **Cache** | Dataset profile JSONs, temporary DB files | `generated/` or temp files | Configured per workflow |

Canonical files are the only source of truth. The generated index and runtime memory are rebuilt on demand and must never grow without bound.

## Default Limits

Defaults are chosen for a normal developer laptop (8–16 GB RAM) and a repository with up to a few thousand objects.

| Limit | Default | Config key | Where it applies |
|---|---|---|---|
| Max file size | 50 MB | `max_file_size_bytes` | Dataset profiling (CSV/XLSX) |
| Max profile rows | 500,000 | `max_profile_rows` | Dataset profiling |
| Max profile columns | 1,000 | `max_profile_columns` | Dataset profiling |
| Max trace depth | 5 | `max_trace_depth` | `trace` graph traversal |
| Max index objects | 10,000 | `max_index_objects` | `build-index` |
| Max export objects | 10,000 | `max_export_objects` | `export-model` CSV/XLSX per type |
| Max import rows | 100,000 | `max_import_rows` | `import-model-sheet` per XLSX sheet |
| Max context objects | 50 | `max_context_objects` | AI context bundles |
| Max context relationships | 100 | `max_context_relationships` | AI context bundles |
| Max response size | 10 MB | `max_response_size_bytes` | CLI/API JSON payloads |

## Configuring Limits

Add a `resource_limits` block to `modelops.config.yaml`:

```yaml
name: "My Model Repository"
version: "1.0.0"
schema_version: "1.0"
resource_limits:
  max_file_size_bytes: 104857600        # 100 MB
  max_profile_rows: 1000000
  max_profile_columns: 2000
  max_trace_depth: 8
  max_index_objects: 20000
  max_export_objects: 20000
  max_import_rows: 500000
  max_context_objects: 100
  max_context_relationships: 200
  max_response_size_bytes: 20971520     # 20 MB
```

All keys are optional. Unspecified keys use the defaults above.

## Overriding Limits Safely

- **CLI flags**: Some commands accept direct overrides (e.g. `modelops trace --max-depth 10`). CLI overrides take precedence over config file values.
- **Environment variables**: Not supported for resource limits in v1. Use `modelops.config.yaml`.
- **Programmatic use**: Service functions accept explicit parameters (e.g. `build_index(..., max_objects=20_000)`).

## Graceful Failure Behavior

When a limit is exceeded, Martenweave fails with a clear message and a recovery suggestion:

| Workflow | Behavior |
|---|---|
| `build-index` | Raises `ResourceLimitExceeded` with object count and hint to increase `max_index_objects` or split the repository. |
| `profile-dataset` | Returns a `ProfilingStatus` with `success=False`, `truncated=True`, and a human-readable `reason`. |
| `export-model` | Raises `ResourceLimitExceeded` for the offending object type with a hint to increase `max_export_objects` or filter by type. |
| `import-model-sheet` | Truncates rows at the limit and adds a warning to the generated `PatchProposal`. |
| `trace` | Stops traversal at `max_depth`; returned nodes never exceed the limit. |
| `build-context-bundle` | Compacts objects and relationships, stripping descriptions if needed, and adds warnings to the bundle. |

## Sizing Guidance

| Repository size | Recommended limits |
|---|---|
| Small (< 100 objects) | Defaults are generous; no changes needed. |
| Medium (100–2,000 objects) | Defaults work well. Monitor `build-index` time. |
| Large (2,000–10,000 objects) | Defaults still apply. Consider splitting by domain if build time exceeds 30 seconds. |
| Very large (> 10,000 objects) | Increase `max_index_objects` and `max_export_objects` in config, or split into multiple repositories. |

## Security and Safety Notes

- Limits prevent accidental exhaustion of RAM by malformed or oversized inputs.
- The profiler streams CSV rows and samples XLSX sheets to avoid loading entire files into memory.
- No limit increase should be made without verifying available system memory.
- Generated artifacts are disposable; if a limit blocks an export, you can always retry after adjusting config.
