# CLI Structure

> Staging document for splitting `src/modelops_core/cli.py` into a `commands/` package.

## Status

`cli.py` currently contains all commands in a single flat Typer application. The split is planned to be incremental: each command group below will move into its own module under `src/modelops_core/commands/`, with `cli.py` becoming a thin router that imports and registers sub-apps.

## Command groups

| Module | Commands | Notes |
|---|---|---|
| `commands/init.py` | `init` | Scaffold a new repository. |
| `commands/validate.py` | `validate` | Deterministic validation of canonical files. |
| `commands/index.py` | `build-index`, `index-fresh`, `migrate` | Index build, freshness check, schema migration. |
| `commands/health.py` | `health`, `doctor`, `scorecard`, `analyze`, `gap-report` | Repository health and readiness reports. |
| `commands/impact.py` | `impact`, `trace` | Object-level impact and lineage traversal. |
| `commands/proposal.py` | `proposal *`, `propose-patch` | Patch proposal lifecycle and note-driven creation. |
| `commands/change_request.py` | `change-request *` | Approved change request lifecycle. |
| `commands/export.py` | `export-model`, `export-schema`, `export-sheets`, `git-bundle` | Model export and git bundle generation. |
| `commands/import_.py` | `import-drive`, `import-sheet`, `import-model-sheet`, `profile-dataset`, `infer-model` | Dataset profiling and spreadsheet import. |
| `commands/query.py` | `search`, `query` | Structured and keyword search over the index. |
| `commands/diff.py` | `diff` | Compare two model repositories. |
| `commands/audit.py` | `audit-log` | Append-only audit log queries. |
| `commands/serve.py` | `serve` | Local FastAPI server. |
| `commands/mcp.py` | `mcp` | MCP server for agent integration. |
| `commands/docs.py` | `docs-build` | Static documentation generation. |
| `commands/guardrails.py` | `config-guard` | Secrets and configuration guardrails. |
| `commands/gap.py` | `gaps` | Dataset-to-model gap detection. |
| `commands/notifications.py` | `notifications *` | Notification preview and list. |
| `commands/decisions.py` | `decisions *` | Decision browsing and reporting. |
| `commands/issue_draft.py` | `issue-draft *` | GitHub-ready issue draft generation. |
| `commands/clean.py` | `clean` | Remove generated artifacts. |
| `commands/doctor.py` | `doctor` | Repository diagnostics. |
| `commands/owners.py` | `owners` | Ownership coverage and steward workload. |
| `commands/sources.py` | `sources`, `source-show` | External source registry. |
| `commands/usage_report.py` | `usage-report` | Aggregated usage telemetry. |
| `commands/publish.py` | `publish-issue`, `publish-pr` | Publish drafts to GitHub. |
| `commands/assessment.py` | `assessment run` | Migration readiness assessment package. |

## Constraints for the split

- Do not change command names, signatures, or JSON output contracts.
- Keep `with_telemetry` decorators on every command.
- Keep `console` and shared helpers (e.g., `_resolve_repo`) in a thin common module if needed.
- Run `test_cli_contracts.py` and `test_cli_structure.py` after each moved group.
- No UI changes.

## Acceptance criteria for the full split

- `src/modelops_core/cli.py` is under 500 lines and only registers sub-apps.
- Every command listed in `modelops --help` continues to work.
- All existing tests pass without modification.
