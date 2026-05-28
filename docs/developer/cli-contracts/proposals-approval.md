# CLI Contract — Proposals and Approval

## Commands

```bash
modelops propose-patch --from <note> --repo <repo>
modelops proposal validate <proposal-id> --repo <repo> [--json]
modelops proposal impact <proposal-id> --repo <repo> [--json]
modelops proposal apply <proposal-id> --repo <repo> --dry-run
modelops proposal apply <proposal-id> --repo <repo> --apply
modelops change-request create ...
```

## JSON Contracts

### `propose-patch --json`

Stable fields: `is_safe`, `proposal`, `assumptions`, `human_checks`

### `proposal impact --json`

Stable fields: `proposal_id`, `high_risk`, `risk_assessment`, `affected_objects`, `operations`

### `change-request create --json`

Stable fields: `id`, `status`, `title`, `path`

### `change-request list --json`

Stable shape: list of CR dicts with `id`, `status`, `title`

### `change-request show --json`

Stable shape: full CR dict

### `change-request update-status --json`

Stable shape: full CR dict with updated `status`
