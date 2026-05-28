# CLI Contract — Validation and Index

## Commands

```bash
modelops init <path>
modelops validate --repo <repo> [--json]
modelops build-index --repo <repo> [--jsonl]
modelops health --repo <repo> [--json]
modelops analyze --repo <repo> [--json]
```

## JSON Contracts

### `validate --json`

Stable fields: `is_valid`, `error_count`, `warning_count`, `info_count`, `summary_by_code`, `results`

Each result in `results` has: `severity`, `code`, `message`, `object_id` (optional), `suggested_fix` (optional).

### `build-index --json`

Stable fields: `martenweave_version`, `repo`, `db_path`, `objects_count`, `valid`, `dry_run`, `jsonl_paths`, `errors`

### `health --json`

Stable fields: `object_count`, `index_fresh`, `coverage_gaps`, `ownership_coverage`, `data_quality_coverage`, `coverage_gaps_list`, `type_counts`

### `analyze --json`

Stable fields: `object_count`, `type_counts`, `orphan_fields`, `attribute_coverage`, `ownership_gaps`, `validation_coverage`, `lov_coverage`, `mapping_coverage`, `risk_report`, `change_activity`, `lifecycle_summary`
