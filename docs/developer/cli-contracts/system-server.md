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

### Frontend integration

The local API enables the workbench to read live data without importing backend internals.

- The frontend defaults to `http://127.0.0.1:8000`. Set `VITE_API_BASE_URL` to point to a different
  local server.
- `modelops serve` configures CORS for local development origins (`http://localhost`,
  `http://127.0.0.1`, and common Vite ports).
- When the API is unreachable, the index is stale, or the contract version is incompatible, the
  workbench shows the connection state and falls back to explicitly labeled demo data.
- All write operations continue to require explicit human approval through the proposal/change-
  request flow; the frontend does not edit canonical files directly.

The Lineage screen consumes two unversioned read endpoints:

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/trace/{id}?direction=&max_depth=` | Upstream/downstream relationship traversal |
| GET | `/impact/{id}` | Upstream/downstream impact summary and total affected count |

Both endpoints require a generated index and return `404` for unknown object IDs. The workbench
falls back to the static demo lineage graph when these endpoints are unavailable.
