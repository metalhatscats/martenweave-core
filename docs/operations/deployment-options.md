# Deployment Options

Martenweave is local-first. These are the supported and planned deployment modes.

## v0.1 — Local CLI

- Install via `pip install modelops_core`
- Run `modelops` commands against local repository
- SQLite index, JSONL exports, Markdown canonical files
- No server, no database server, no cloud required

## v0.2 — Local API Server

- FastAPI/uvicorn server on localhost
- Same CLI commands exposed as HTTP endpoints
- Useful for IDE plugins and local integrations

## v0.2 — MCP Server

- Model Context Protocol server for AI assistants
- Exposes read + proposal tools, no direct apply
- Runs locally alongside the model repository

## v0.3 — One-Screen Workspace

- Local web UI (e.g., Gradio or lightweight frontend)
- Connects to local API or direct Python calls
- Same local-first data model

## CI / GitHub Action

- Docker image with `modelops_core` installed
- Runs validate, build-index, analyze, scorecard in CI
- Posts PR comments (see `github-action-design.md`)

## Later — Team Server

- Optional multi-user server with authentication
- Centralized model repository with git-backed storage
- Not required for individual or small team usage

## Docker

```dockerfile
FROM python:3.11-slim
RUN pip install modelops_core
WORKDIR /repo
ENTRYPOINT ["modelops"]
```

## Data Storage

| Mode | Canonical Files | Generated Index | Config |
|---|---|---|---|
| Local CLI | `model/` git-tracked | `generated/` git-ignored | `modelops.config.yaml` |
| API/MCP | same | same | same |

Secrets: only AI provider keys (optional), stored in `.env` or env vars.
