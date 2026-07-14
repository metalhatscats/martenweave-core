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

### Versioned API contract (`/api/v1`)

`modelops serve` exposes a stable `v1` namespace alongside the existing unversioned endpoints.
Clients should discover capabilities before rendering actions.

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/api/v1/capabilities` | API version, workspace health, and capability list |
| GET | `/api/v1/search` | Paginated keyword search over the generated index |
| GET | `/api/v1/objects/{id}` | Canonical object detail and relationships |

`GET /api/v1/capabilities` returns:

- `version` — Martenweave package version.
- `api_version` — API contract version (`v1`).
- `repository`, `indexed`, `canonical_files` — workspace health.
- `read_only` — whether mutation endpoints are disabled.
- `read` — list of read operations with `name`, `method`, `href`, `description`.
- `mutations` — list of mutation operations with the same shape.

`GET /api/v1/search` accepts `q` (required), `type`, `status`, `domain`, `tags`, `limit`, and
`offset`, and returns `total_count` and a `results` array. Search returns structured errors when the
index is missing.

`GET /api/v1/objects/{id}` returns the canonical object's frontmatter under `object` and its
outgoing relationships under `relationships`. It returns `404` for unknown IDs and structured errors
for a missing index.
