# CLI Contract — Search, Query, and Trace

## Commands

```bash
modelops search <query> --repo <repo> [--json]
modelops query --repo <repo> [--json]
modelops trace <object-id> --repo <repo> [--json]
modelops impact <object-id> --repo <repo>
```

## JSON Contracts

### `search --json`

Stable fields: `results` (list), `total_count`

Each result has: `object_id`, `object_type`, `status`, `name`, `title`, `domain`, `source_file`, `score`, `matched_fields`

### `query --json`

Stable fields: `results` (list), `total_count`

Each result has: `object_id`, `object_type`, `status`, `name`, `title`, `domain`, `source_file`

### `trace --json`

Stable fields: `root_object_id`, `root_object_type`, `root_object_name`, `nodes`, `edges`

### `impact`

Stable fields: `root_object_id`, `root_object_type`, `affected_objects`
