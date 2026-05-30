# CLI Contracts

Stable command contracts grouped by capability. Agents and future UI layers may rely on these JSON shapes.

---

## Command Groups

| Group | File | Commands |
|---|---|---|
| Validation and Index | [cli-contracts/validation-index.md](cli-contracts/validation-index.md) | `init`, `validate`, `build-index`, `health`, `analyze` |
| Search, Query, and Trace | [cli-contracts/search-query-trace.md](cli-contracts/search-query-trace.md) | `search`, `query`, `trace`, `impact` |
| Dataset and Gap Analysis | [cli-contracts/dataset-gaps.md](cli-contracts/dataset-gaps.md) | `profile-dataset`, `infer-model`, `gaps` |
| Proposals and Approval | [cli-contracts/proposals-approval.md](cli-contracts/proposals-approval.md) | `propose-patch`, `proposal *`, `change-request *` |
| Export and Import | [cli-contracts/export-import.md](cli-contracts/export-import.md) | `export-model`, `export-schema`, `import-model-sheet` |
| Reports and Governance | [cli-contracts/reports-governance.md](cli-contracts/reports-governance.md) | `config-guard`, `scorecard`, `gap-report`, `owners`, `decisions`, `audit-log`, `usage-report` |
| System and Server | [cli-contracts/system-server.md](cli-contracts/system-server.md) | `clean`, `diff`, `migrate`, `serve`, `mcp`, `sources` |

---

## Contract Rules

- JSON output is for agents and automation; avoid breaking field names without tests.
- Human table output may evolve, but command exit codes must remain meaningful.
- Validation errors should be structured and actionable.
- Commands must not require AI provider keys unless the command explicitly calls a provider.
- Generated outputs must be written under the configured generated path.

## Testing

CLI changes require focused tests in `tests/test_cli.py` or a command-specific test file, plus the validation ladder in `docs/ai/VALIDATION_LADDER.md`.
