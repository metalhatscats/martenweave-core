# Deployment Options

Martenweave is local-first. These are the supported deployment modes today.

## Local CLI

- Install via `pip install martenweave-core`
- Run `martenweave` commands against a local repository (`modelops` is a compatibility alias)
- SQLite index, JSONL exports, Markdown canonical files
- No server, no database server, no cloud required

## Local API Server

- FastAPI/uvicorn server on localhost
- Same CLI commands exposed as HTTP endpoints
- Useful for IDE plugins and local integrations

## MCP Server

- Model Context Protocol server for AI assistants
- Exposes read + proposal tools, no direct apply
- Runs locally alongside the model repository

## Local Workbench

- Packaged browser UI served by `martenweave workbench --repo <repo>`
- Connects only to the bound local API and preserves Core approval gates
- No hosted service, authentication/RBAC, or independent canonical storage

## CI / GitHub Action

- CI environment with `martenweave-core` installed
- Runs validate, build-index, analyze, scorecard in CI
- Posts PR comments (see `github-action-design.md`)

## Data Storage

| Mode | Canonical Files | Generated Index | Config |
|---|---|---|---|
| Local CLI | `model/` git-tracked | `generated/` git-ignored | `modelops.config.yaml` |
| API/MCP | same | same | same |

Secrets: only AI provider keys (optional), stored in `.env` or env vars.
