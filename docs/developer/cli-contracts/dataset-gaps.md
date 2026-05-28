# CLI Contract — Dataset and Gap Analysis

## Commands

```bash
modelops profile-dataset <file> --repo <repo> [--json]
modelops infer-model <profile-json> --repo <repo> [--json]
modelops gaps <dataset-file> --repo <repo> [--json]
```

## JSON Contracts

### `profile-dataset --json`

Stable fields: `dataset_id`, `row_count`, `column_count`, `columns`, `status`

### `infer-model --json`

Stable fields: `id`, `type`, `status`, `operations`, `affected_objects`, `validation_status`, `assumptions`, `human_checks`

### `gaps --json`

Stable fields: `dataset_id`, `matches`, `gaps`, `coverage`

`coverage` contains: `total_columns`, `matched_columns`, `unmatched_columns`, `duplicate_columns`, `match_rate`
