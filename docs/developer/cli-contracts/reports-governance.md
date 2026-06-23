# CLI Contract — Reports and Governance

## Commands

```bash
modelops config-guard --repo <repo> [--mode local|release] [--json]
modelops scorecard --repo <repo> [--json]
modelops gap-report --repo <repo> [--json]
modelops owners --repo <repo> [--json]
modelops decisions list --repo <repo> [--json]
modelops decisions report --repo <repo> [--json]
modelops audit-log --repo <repo> [--json]
modelops usage-report --repo <repo> [--json]
```

## JSON Contracts

### `config-guard --json`

Stable shape: dict of check names to issue lists. Each issue includes `file_status`
when a repository path is available (`tracked`, `untracked`, `ignored`, or `unknown`).
Default `local` mode blocks on ignored local findings; `release` mode reports ignored
local findings but does not make them release-blocking.

### `scorecard --json`

Stable fields: `martenweave_version`, `metrics` (list), `readiness_level`, `object_count`, `gaps` (list), `summary`

### `gap-report --json`

Stable fields: `martenweave_version`, `gaps_by_type` (dict), `total_gap_count`, `gap_score`, `sources_checked` (list)

### `owners --json`

Stable fields: `martenweave_version`, `owners` (list), `orphaned_objects` (list), `coverage_percent`

### `decisions list --json`

Stable shape: list of decision dicts with `id`, `status`, `name`, `domain`

### `decisions report --json`

Stable fields: `martenweave_version`, `evidence_coverage` (list), `uncovered_decisions` (list), `category_breakdown` (list), `total_decisions`, `total_with_evidence`, `overall_coverage_percent`

### `audit-log --json`

Stable shape: list of audit event dicts with `event_id`, `event_type`, `timestamp`, `status`

### `usage-report --json`

Stable fields: `martenweave_version`, `command_summary`, `status_summary`
