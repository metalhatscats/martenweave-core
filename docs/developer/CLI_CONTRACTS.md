# CLI Contracts

## Stable Commands

Agents and future UI layers may rely on these commands:

```bash
modelops init <path>
modelops validate --repo <repo> [--json]
modelops build-index --repo <repo> [--jsonl]
modelops health --repo <repo> [--json]
modelops analyze --repo <repo> [--json]
modelops search <query> --repo <repo> [--json]
modelops query --repo <repo> [--json]
modelops trace <object-id> --repo <repo> [--json]
modelops impact <object-id> --repo <repo>
modelops profile-dataset <file> --repo <repo> [--json]
modelops infer-model <profile-json> --repo <repo> [--json]
modelops propose-patch --from <note> --repo <repo>
modelops proposal validate <proposal-id> --repo <repo> [--json]
modelops proposal impact <proposal-id> --repo <repo> [--json]
modelops proposal apply <proposal-id> --repo <repo> [--dry-run]
modelops change-request create ...
modelops export-model --repo <repo> --format csv|xlsx --output <path>
modelops config-guard --repo <repo> [--json]
```

## Contract Rules

- JSON output is for agents and automation; avoid breaking field names without tests.
- Human table output may evolve, but command exit codes must remain meaningful.
- Validation errors should be structured and actionable.
- Commands must not require AI provider keys unless the command explicitly calls a provider.
- Generated outputs must be written under the configured generated path.

## Testing

CLI changes require focused tests in `tests/test_cli.py` or a command-specific test file, plus the validation ladder in `docs/ai/VALIDATION_LADDER.md`.
