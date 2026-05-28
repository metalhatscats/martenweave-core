# CLI Contract — System and Server

## Commands

```bash
modelops clean --repo <repo> --dry-run
modelops diff <base-repo> <head-repo> --json
modelops migrate --repo <repo>
modelops serve --repo <repo> --host <host> --port <port>
modelops mcp --repo <repo>
modelops sources --repo <repo>
```

## JSON Contracts

### `clean --dry-run --json`

Stable fields: `dry_run`, `generated_path`, `removed_count`, `skipped_count`, `removed` (list), `skipped` (list)

### `diff --json`

Stable fields: `has_changes`, `base_count`, `head_count`, `added`, `removed`, `changed`

### `serve` / `mcp`

These commands start long-running servers. Their primary contract is the HTTP/MCP protocol, not CLI JSON output.
