# Martenweave MCP Server Design

## Goal

Design an MCP (Model Context Protocol) server so external agents — such as Claude, Kimi, or Google ADK — can work with Martenweave models through safe, bounded tools instead of reading and mutating files directly.

## Scope

This document covers:

- MCP server architecture and transport options
- Tool inventory mapped to existing CLI and API contracts
- Read-only vs write-intent tool categories
- Request/response schemas aligned with CLI `--json` contracts
- Context-size limits and response compaction strategies
- Safety boundaries (no direct file mutation)
- Implementation path and dependency strategy

## What is MCP

[MCP](https://modelcontextprotocol.io) is an open protocol that standardizes how applications provide context and tools to LLMs. An MCP server exposes:

- **Tools** — functions the model can call (with structured input/output)
- **Resources** — URI-addressable data the model can read
- **Prompts** — reusable prompt templates

Martenweave exposes its core operations as MCP tools, keeping the canonical model as the source of truth and never allowing agents to mutate Markdown files directly.

## Server Architecture

```
┌─────────────────┐     MCP/JSON-RPC      ┌──────────────────────┐
│  AI Agent/IDE   │  ◄─────────────────►  │  martenweave-mcp     │
│  (Claude, Kimi) │    stdio or SSE       │  (MCP server)        │
└─────────────────┘                       └──────────────────────┘
                                                    │
                       ┌────────────────────────────┼────────────────────────────┐
                       │                            │                            │
                ┌──────▼──────┐            ┌────────▼────────┐          ┌────────▼────────┐
                │   SQLite    │            │   model/        │          │  generated/     │
                │   Index     │            │   canonical     │          │  artifacts      │
                └─────────────┘            │   files         │          └─────────────────┘
                                           └─────────────────┘
```

### Transport Options

| Transport | Use Case | Recommendation |
|---|---|---|
| `stdio` | CLI embedding, local agents, VS Code extensions | **Primary for v0.1** |
| `SSE` (Server-Sent Events) | Remote IDE, web agents | Future |
| `HTTP` | Custom integrations | Future |

The server is implemented as a standalone Python package (`martenweave-mcp`) that depends on `modelops_core` and the official `mcp` Python SDK.

```bash
# Example: run via stdio
npx -y @anthropic/mcp-server@latest  # or equivalent
python -m martenweave_mcp --repo ./my-model --transport stdio
```

## Tool Inventory

### Read-Only Tools (Safe — no side effects)

These tools query the model index or canonical files without modifying anything.

| Tool Name | Maps to CLI / Service | Purpose |
|---|---|---|
| `search_model` | `modelops search --json` | Keyword search across all objects |
| `query_model` | `modelops query --json` | Structured query by type, status, domain |
| `get_object` | `query_service.get_object_by_id` | Fetch full frontmatter for one object |
| `trace_object_tool` | `modelops trace --json` | Upstream/downstream relationship trace |
| `proposal_impact` | `modelops impact --json` | Impact report for a PatchProposal |
| `validate_model` | `modelops validate --json` | Run deterministic validation |
| `health_report` | `modelops health --json` | Repository health and coverage gaps |
| `scorecard` | `modelops scorecard --json` | Governance readiness scorecard |
| `analyze_model` | `modelops analyze --json` | Full model analysis (orphans, coverage, risk) |
| `list_change_requests` | `modelops change-request list --json` | List CRs |
| `show_change_request` | `modelops change-request show --json` | Single CR detail |
| `list_proposals` | `modelops proposal list` | List PatchProposals |
| `show_proposal` | `modelops proposal show` | Single proposal detail |
| `audit_log` | `modelops audit-log --json` | Query audit events |
| `usage_report` | `modelops usage-report --json` | CLI usage and AI call summary |
| `diff_repositories` | `modelops diff --json` | Compare two model repos |
| `list_sources` | `modelops sources --json` | Registered import sources |
| `config_guard` | `modelops config-guard --json` | Guardrail scan results |

### Write-Intent Tools (Require validation, PatchProposal, or approval)

These tools produce proposals, trigger workflows, or create governance objects. None of them write directly to canonical files.

| Tool Name | Maps to CLI / Service | Purpose |
|---|---|---|
| `propose_model_change` | `modelops propose-patch --json` | Create PatchProposal from a note |
| `infer_model` | `modelops infer-model --json` | Generate PatchProposal from dataset profile |
| `profile_dataset` | `modelops profile-dataset --json` | Profile CSV/XLSX and store result |
| `import_model_sheet` | `modelops import-model-sheet --json` | Import spreadsheet as PatchProposal |
| `proposal_dry_run` | `modelops proposal apply --dry-run` | Preview proposal application |
| `create_change_request_tool` | `modelops change-request create --json` | Create a ChangeRequest |
| `update_cr_status` | `modelops change-request update-status` | Update CR status |
| `approve_change_request` | `modelops change-request approve` | Approve a CR |
| `reject_change_request` | `modelops change-request reject` | Reject a CR |
| `build_index` | `modelops build-index` | Rebuild SQLite index |
| `export_model` | `modelops export-model --json` | Export CSV/XLSX |
| `generate_docs` | `modelops docs-build` | Build static Markdown docs |
| `publish_issue` | `modelops publish-issue --json` | Publish issue draft to GitHub |
| `publish_pr` | `modelops publish-pr --json` | Publish PR from proposal bundle |

### AI-Assisted Tools (Provider-dependent)

These tools invoke an AI provider adapter (currently `NoProviderAdapter` stub).

| Tool Name | Maps to Service | Purpose |
|---|---|---|
| `analyze_model_with_ai` | `ai.patch_proposal_service` | AI-assisted gap analysis or suggestion |
| `generate_proposal_from_context` | `ai.patch_proposal_service` | Build PatchProposal from free-text context |

## Tool Schemas

All tool inputs and outputs are JSON-compatible and mirror the CLI `--json` contracts. The server uses the same service layer as the CLI and the local API (`modelops_core.api`).

### `search_model`

**Input:**
```json
{
  "query": "customer group",
  "object_type": "Attribute",
  "status": "active",
  "domain": "DOMAIN-CUSTOMER-BP",
  "limit": 20
}
```

**Output:**
```json
{
  "results": [
    {
      "object_id": "ATTR-CUST-SALES-CUSTOMER-GROUP",
      "object_type": "Attribute",
      "status": "active",
      "name": "Customer Group",
      "title": null,
      "domain": "DOMAIN-CUSTOMER-BP",
      "source_file": "model/ATTR-CUST-SALES-CUSTOMER-GROUP.md",
      "score": 2,
      "matched_fields": ["name", "description"]
    }
  ],
  "total_returned": 1
}
```

### `query_model`

**Input:**
```json
{
  "object_type": "FieldEndpoint",
  "status": "active",
  "domain": "DOMAIN-CUSTOMER-BP",
  "name_like": "KNVV",
  "limit": 50
}
```

**Output:**
```json
{
  "results": [
    {
      "object_id": "FEP-S4-KNVV-KDGRP",
      "object_type": "FieldEndpoint",
      "status": "active",
      "name": "Customer Group (KNVV)",
      "domain": "DOMAIN-CUSTOMER-BP",
      "source_file": "model/FEP-S4-KNVV-KDGRP.md"
    }
  ],
  "total_returned": 1
}
```

### `get_object`

**Input:**
```json
{"object_id": "FEP-S4-KNVV-KDGRP"}
```

**Output:**
```json
{
  "object_id": "FEP-S4-KNVV-KDGRP",
  "type": "FieldEndpoint",
  "status": "active",
  "name": "Customer Group (KNVV)",
  "domain": "DOMAIN-CUSTOMER-BP",
  "entity_context": "ENTITY-CUST-SALES-AREA",
  "endpoint_type": "sap_table_field",
  "sap_table": "KNVV",
  "sap_field": "KDGRP",
  "description": "Sales-area-dependent customer grouping...",
  "source_file": "model/FEP-S4-KNVV-KDGRP.md"
}
```

### `trace_object`

**Input:**
```json
{
  "object_id": "FEP-S4-KNVV-KDGRP",
  "direction": "both",
  "max_depth": 3
}
```

**Output:**
```json
{
  "root_object_id": "FEP-S4-KNVV-KDGRP",
  "root_object_type": "FieldEndpoint",
  "root_object_name": "Customer Group (KNVV)",
  "nodes": [
    {"object_id": "ATTR-CUST-SALES-CUSTOMER-GROUP", "object_type": "Attribute", "depth": 1}
  ],
  "edges": [
    {"from_object_id": "FEP-S4-KNVV-KDGRP", "to_object_id": "ATTR-CUST-SALES-CUSTOMER-GROUP", "relationship_type": "attribute", "direction": "upstream"}
  ]
}
```

### `analyze_impact`

**Input:**
```json
{
  "object_id": "FEP-S4-KNVV-KDGRP",
  "max_depth": 2
}
```

**Output:**
```json
{
  "root_object_id": "FEP-S4-KNVV-KDGRP",
  "root_object_type": "FieldEndpoint",
  "affected_objects": [
    {"object_id": "ATTR-CUST-SALES-CUSTOMER-GROUP", "object_type": "Attribute", "direction": "upstream", "depth": 1}
  ]
}
```

### `validate_model`

**Input:**
```json
{"repo": "/path/to/repo"}
```

**Output:**
```json
{
  "is_valid": true,
  "error_count": 0,
  "warning_count": 2,
  "info_count": 1,
  "results": [
    {"severity": "WARNING", "code": "NAME_MISSING", "object_id": "ENTITY-001", "message": "Name is missing", "suggested_fix": "Add a name field"}
  ]
}
```

### `propose_patch`

**Input:**
```json
{
  "note_text": "Add a new Attribute for Customer Credit Group mapped to KNVV-KDGRP.",
  "repo": "/path/to/repo"
}
```

**Output:**
```json
{
  "proposal_id": "PP-2026-001",
  "operations": [
    {"op": "add", "object_id": "ATTR-CUST-SALES-CREDIT-GROUP", "object_type": "Attribute", "target_path": "model/ATTR-CUST-SALES-CREDIT-GROUP.md"}
  ],
  "is_safe": false,
  "assumptions": ["Assuming KDGRP is the correct SAP field"],
  "human_checks": ["Verify business meaning with domain owner"],
  "validation_status": "invalid",
  "path": "model/patch-proposals/PP-2026-001.md"
}
```

### `proposal_dry_run`

**Input:**
```json
{"proposal_id": "PP-2026-001", "repo": "/path/to/repo"}
```

**Output:**
```json
{
  "proposal_id": "PP-2026-001",
  "would_change": 2,
  "risk_level": "medium",
  "requires_approval": true,
  "operations_preview": [
    {"op": "add", "object_id": "ATTR-CUST-SALES-CREDIT-GROUP", "status": "would_create", "file": "model/ATTR-CUST-SALES-CREDIT-GROUP.md"}
  ]
}
```

### `apply_proposal`

**Input:**
```json
{"proposal_id": "PP-2026-001", "repo": "/path/to/repo", "force": false}
```

**Output:**
```json
{
  "applied": true,
  "changed_files": ["model/ATTR-CUST-SALES-CREDIT-GROUP.md"],
  "audit_event_written": true,
  "index_rebuilt": true
}
```

**Error if approval required:**
```json
{
  "error": "Approval required for PP-2026-001. Risk level: medium. Create an approved ChangeRequest or use force.",
  "requires_approval": true,
  "risk_level": "medium"
}
```

## Context-Size Limits and Response Compaction

AI agents have limited context windows. The MCP server implements tiered response compaction.

### Default Limits

| Parameter | Default | Override |
|---|---|---|
| Max results per query/search | 20 | `limit` input field |
| Max trace nodes | 50 | `max_depth` + truncation |
| Max impact objects | 30 | `max_depth` + truncation |
| Max validation results | 50 | Severities sorted ERROR > WARNING > INFO |
| Max proposal operations preview | 20 | Full list available via `show_proposal` |
| Max audit events | 50 | `limit` input field |

### Compaction Strategies

1. **Truncation** — Return top-N results with a `truncated: true` flag and `total_available` count.
2. **Summary mode** — When `summary: true` is passed, return counts and aggregates instead of full objects.
3. **Field selection** — Default responses include only `object_id`, `object_type`, `name`, `status`. Full frontmatter available via `get_object`.
4. **Relationship deduplication** — Trace/impact edges are deduplicated by `(from, to, type)` before serialization.

### Example: Compacted Search

```json
{
  "results": [
    {"object_id": "ATTR-001", "object_type": "Attribute", "name": "Customer Group", "status": "active"}
  ],
  "total_returned": 1,
  "total_available": 15,
  "truncated": true,
  "suggestion": "Use query_model with object_type=Attribute and domain=DOMAIN-CUSTOMER-BP to narrow results."
}
```

## Safety Boundaries

### No Direct File Mutation

The MCP server **never** exposes tools that:
- Write, edit, or delete Markdown/YAML files in `model/` directly
- Bypass the PatchProposal → validation → approval → apply workflow
- Modify `.github/workflows/`, `.env`, or other sensitive files
- Execute arbitrary shell commands or SQL against the index

### Write-Intent Tool Guardrails

| Tool | Guardrail |
|---|---|
| `propose_model_change` | Always writes to `model/patch-proposals/`, never to `model/` |
| `infer_model` | Generates PatchProposal; human review required before apply |
| `proposal_dry_run` | Read-only preview; no file modifications |
| `proposal_impact` | Read-only analysis; no file modifications |
| `create_change_request_tool` | Creates governance object; does not modify model files |
| `export_model` | Read-only export; does not modify canonical files |

### Audit and Telemetry

Every tool call is logged as an audit event (actor = `mcp_agent`) with:
- `tool_name`, `input_summary` (redacted for privacy)
- `output_summary`, `status`, `latency_ms`
- `error_type` if the call failed

## Resource Exposing

In addition to tools, the MCP server can expose canonical model files as MCP resources:

| Resource URI | Content |
|---|---|
| `modelops://object/{object_id}` | Full frontmatter JSON for an object |
| `modelops://repo/health` | Latest health report (cached) |
| `modelops://repo/validation` | Latest validation summary (cached) |
| `modelops://repo/audit` | Recent audit events (last 100) |

Resources are read-only and do not trigger side effects.

## Prompt Templates

The server can provide reusable prompt templates for common agent workflows:

| Prompt Name | Description |
|---|---|
| `review_proposal` | Guide an agent through reviewing a PatchProposal for safety and correctness |
| `gap_analysis` | Guide an agent through identifying coverage gaps in a domain |
| `impact_assessment` | Guide an agent through assessing the impact of a proposed change |
| `model_onboarding` | Guide an agent through understanding a new model repository |

## Implementation Path

### Phase 1 — Design (this document)

- Tool inventory, schemas, safety boundaries, compaction strategy
- No runtime dependencies added to `modelops_core`

### Phase 2 — Standalone Package (`martenweave-mcp`)

- New package: `packages/martenweave-mcp/` or separate repo
- Dependencies: `modelops_core`, `mcp>=1.0`
- Entry point: `python -m martenweave_mcp`
- Transport: `stdio` first, `SSE` later

### Phase 3 — CLI Integration

- Optional `modelops mcp` subcommand to start the server with the current repo context
- Configurable via `modelops.config.yaml`:
  ```yaml
  mcp:
    enabled: true
    transport: stdio
    max_results: 20
    default_repo: "."
  ```

### Phase 4 — IDE Extensions

- VS Code extension shipping the MCP server
- Cursor / Windsurf / Zed integration via MCP config

## Dependency Strategy

| Dependency | Scope | Version |
|---|---|---|
| `modelops_core` | Required | `>=0.1.0` |
| `mcp` (Python SDK) | Required for `martenweave-mcp` | `>=1.0` |
| `uvicorn` | Optional (for SSE transport) | `>=0.25` |

`modelops_core` itself does **not** depend on `mcp`. The MCP server is an optional consumer of the core library.

## Relationship to CLI, API, and UI

| Interface | Role | MCP Equivalence |
|---|---|---|
| CLI (`modelops`) | Human operator interface | Same services, different transport |
| API (`modelops serve`) | Programmatic HTTP interface | Same services, different transport |
| MCP Server | AI agent interface | Same services, structured tool calls |
| Future UI | Visual browsing and editing | Will consume the same API/index |

All four interfaces share the same service layer. The MCP server is a thin adapter that maps MCP tool calls to existing service functions.

## Example: Agent Workflow via MCP

An AI agent asked to "add a new customer attribute" would use the MCP tools in this sequence:

```
1. search_model(query="customer attribute", object_type="Attribute")
   └─ Discover existing customer attributes

2. get_object(object_id="ATTR-CUST-SALES-CUSTOMER-GROUP")
   └─ Understand the pattern for customer attributes

3. propose_model_change(note="Add Customer Credit Group...")
   └─ Generate PatchProposal for human review

4. proposal_impact(proposal_id="PP-2026-001")
   └─ Assess impact of the proposal

5. (Human reviews and approves via CLI or UI)

6. apply_patch_proposal (via CLI, not exposed as MCP tool)
   └─ Apply the approved proposal
```

At no point does the agent directly edit a Markdown file.

## Future Extensions

| Feature | Description |
|---|---|
| `SSE transport` | HTTP-based transport for remote agents |
| `Sampling` | MCP sampling support for AI-assisted tool chains |
| `Multi-repo` | Server configured with multiple repositories |
| `Streaming` | Stream large trace/impact results in chunks |
| `Tool confirmation` | Require human approval for high-risk tool calls |
| `Graph export` | `graph_export` tool returning nodes/edges JSON for visualization |

## Acceptance Criteria

- [x] The MCP design exposes useful model operations without allowing direct unsafe file mutation.
- [x] Tool inputs and outputs are JSON-compatible and align with CLI `--json` contracts.
- [x] The design can be implemented after command contracts are stable.
- [x] The document explains how MCP complements CLI/API/UI.
- [x] Context-size limits and compaction strategies are defined.
- [x] Audit logging for every MCP tool call is specified.
