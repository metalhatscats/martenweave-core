# Martenweave Workbench Boundary

Version: 0.4.1
Document type: Architecture boundary
Status: Draft for product development

---

## Purpose

This document defines **Martenweave Workbench** as an official product surface and explains how it relates to **Martenweave Core** and the **local API**.

Martenweave Core remains the authoritative backend and canonical model layer. The Workbench is the local, browser-based UI for assessment, investigation, review, reports, and controlled changes. It is not a hosted SaaS platform, a generic chatbot, or a replacement for the CLI-first workflow.

---

## Product surfaces

| Surface | Role | Technology | Deployment |
|---|---|---|---|
| **Martenweave Core** | Canonical model parsing, validation, indexing, gap/lineage/impact analysis, patch proposals, change requests, audit. | Python library / Typer CLI | Local Python package |
| **Local API** | Bound integration surface for the Workbench and agents. Serves core services over HTTP on localhost. | FastAPI | Started via `martenweave serve` |
| **Martenweave Workbench** | Local browser UI for interactive assessment, object inspection, lineage, gaps, proposals, and reports. | React + Vite static build | Served by core or a static file server on localhost |

---

## Responsibilities

### Core (source of truth)

- Parse and validate canonical Markdown/YAML files.
- Build the disposable SQLite index and JSONL exports.
- Run deterministic validators, gap detection, lineage, and impact analysis.
- Generate patch proposals and change requests.
- Apply approved changes to canonical files.
- Write audit events and telemetry.

### Local API (thin adapter)

- Bind to one validated repository at startup.
- Expose read-only and mutation endpoints using core services.
- Enforce workspace boundary, path safety, and capability reporting.
- Never accept arbitrary repository paths from browser requests.
- Require explicit confirmation for mutations.

### Workbench (local UI)

- Visualize repository status, validation results, index freshness, and scorecard.
- Browse and search the object catalog.
- Show object detail, lineage, impact, gaps, and ownership.
- Run assessment workflows and display executive summaries.
- Review patch proposals and change requests.
- Surface reports and read-only viewers.
- Guide the user through the proposal → approval → apply flow.

The Workbench **does not**:

- Store canonical model truth independently of `model/` files.
- Silently mutate canonical files.
- Bypass validation or approval gates.
- Provide hosted multi-tenant access.
- Perform direct SAP write-back.
- Run autonomous AI mutations.

---

## Data flow

```text
User → Workbench (browser)
            ↓
    Local API (localhost)
            ↓
    Martenweave Core services
            ↓
    Canonical files in model/  +  generated/ index
```

All mutations follow the same path as the CLI:

```text
proposal → validation → review → approval → ChangeRequest → apply → canonical files + Git diff
```

---

## Local API security model

The local API is created by binding a single workspace at startup via `init_app(workspace)`. Once bound, the API does not accept repository paths from HTTP requests.

| Control | Implementation |
|---|---|
| Workspace binding | `modelops_core.api.workspace.create_workspace(repo_root)` validates the repository layout and returns a `WorkspaceContext`. |
| Session token | A 32-byte hex token is generated at startup. Mutations require the `X-Martenweave-Session-Token` header. The CLI prints the token when it starts the server. |
| Path safety | User-supplied file paths (e.g., dataset inputs) must resolve inside the workspace roots (`repo_root`, `model/`, `generated/`, `data/`). Traversal, blocked segments (`.git`, `.env`, `.ssh`, `.gnupg`), and symlinks outside the workspace are rejected. |
| Path redaction | Absolute paths are redacted to workspace-relative paths in JSON responses. Paths outside the workspace are replaced with `<outside-workspace>`. |
| Read-only mode | `martenweave serve --read-only` disables all mutation endpoints (POST `/export`, `/gaps`, `/dataset-readiness`, proposal dry-run/apply/validate). |
| CORS | Allowed origins default to `http://localhost` and `http://127.0.0.1`. Use `--allowed-origin` to add others. |
| Capabilities | `GET /capabilities` returns the workspace name, read-only status, mutation allowance, and version so the Workbench can adapt its UI. |

## Capability modes

The Workbench must respect the API capability contract:

- **read-only mode**: All mutation endpoints are disabled. The Workbench shows inspection, reports, and viewers only.
- **review mode**: Proposals and ChangeRequests can be reviewed but not applied without explicit approval.
- **full mode**: The full proposal → approval → apply flow is available, with confirmation prompts and audit logging.

The Workbench must degrade gracefully when the API is unavailable, the index is stale, validation fails, or AI capabilities are disabled.

---

## Boundaries preserved

| Principle | Core | API | Workbench |
|---|---|---|---|
| Canonical truth | Owns `model/` files | Reads/writes through core | Reads/displays only; mutations via core |
| Deterministic validation | Runs validators | Exposes results | Displays errors and gates |
| AI-assisted proposals | Generates PatchProposals | Returns proposal data | Renders for human review |
| Human approval | Records approval in ChangeRequest | Enforces approval gate | Provides approval UI |
| Local-first | No cloud required | Localhost only | Localhost only |
| No SaaS | No tenancy | No tenancy | No tenancy |
| No SAP write-back | No SAP connectors write | No SAP write path | No SAP write path |

---

## References

- `README.md` — product overview and install instructions
- `AGENTS.md` — agent conventions and testing strategy
- `frontend/README.md` — Workbench implementation notes
- `docs/architecture/SYSTEM_ARCHITECTURE.md` — overall system architecture
- `docs/architecture/INTEGRATION_BOUNDARIES.md` — integration rules
- `docs/product/MVP_SCOPE.md` — MVP scope
- `docs/product/ACCEPTANCE_CRITERIA.md` — acceptance criteria
