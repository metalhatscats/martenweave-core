# Adding CLI Commands

## Files

- `src/modelops_core/cli.py`
- service module under `src/modelops_core/`
- tests under `tests/`
- `docs/developer/CLI_CONTRACTS.md`

## Steps

1. Implement core behavior in a service, not only inside the Typer command.
2. Add the Typer command using existing option patterns.
3. Provide `--repo` where repository context is needed.
4. Provide `--json` for agent-facing structured output when useful.
5. Keep external writes explicit and opt-in.
6. Add tests for success, failure, and JSON output.
7. Update CLI contracts.

## Validation

```bash
.venv/bin/python -m pytest tests/test_cli.py -v
.venv/bin/modelops --help
.venv/bin/python -m ruff check .
```
