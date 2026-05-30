# Code Style Guide — Martenweave Core

> Conventions for Python code, tests, and documentation in `modelops_core`.

---

## Language and Tooling

- **Python**: >= 3.11
- **Line length**: 100 characters (`tool.ruff.line-length = 100` in `pyproject.toml`)
- **Linter/formatter**: [ruff](https://docs.astral.sh/ruff/) >= 0.4
- **Lint rules**: E, F, I, UP, B (`tool.ruff.lint.select`)

Run checks before every commit:

```bash
ruff check .
ruff format .
```

---

## Imports

Every module must start with:

```python
from __future__ import annotations
```

Order imports in three blocks, separated by a blank line:

1. **Standard library**
2. **Third-party packages**
3. **Local/project imports**

Example:

```python
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import typer
from pydantic import BaseModel, Field

from modelops_core.config import resolve_generated_path
from modelops_core.validation.result import ValidationResult
```

---

## Type Hints

Use modern syntax. Do **not** import `Optional`, `List`, `Dict`, etc. from `typing`.

| Preferred | Avoid |
|---|---|
| `str \| None` | `Optional[str]` |
| `list[str]` | `List[str]` |
| `dict[str, int]` | `Dict[str, int]` |
| `tuple[str, ...]` | `Tuple[str, ...]` |

Use `Any` only when a value is truly untyped (e.g., parsed JSON).

---

## Docstrings

Use triple double-quoted docstrings for every module, class, and public function.

Keep them concise — one or two sentences are usually enough. Only add parameter lists when the signature is ambiguous.

```python
def export_schemas(type_filter: str | None = None) -> dict[str, Any]:
    """Export JSON Schema for canonical object types.

    Args:
        type_filter: If provided, export only this object type.
            Use ``"all"`` or ``None`` to export every registered type.

    Returns:
        A dict with ``$schema``, ``title``, ``type_count``, and ``schemas`` keys.
    """
```

---

## Naming Conventions

| Kind | Convention | Example |
|---|---|---|
| Modules | `snake_case.py` | `patch_proposal_service.py` |
| Packages | `snake_case` | `modelops_core` |
| Classes | `PascalCase` | `ValidationResult` |
| Functions / variables | `snake_case` | `build_index`, `repo_root` |
| Constants | `UPPER_SNAKE_CASE` | `METHODOLOGY_WARNING_CODES` |
| Private helpers | `_leading_underscore` | `_resolve_repo` |

---

## Error Handling

Raise **domain-specific exceptions** from `modelops_core.errors` instead of generic `ValueError` or `RuntimeError` when the caller is expected to handle the failure distinctly.

```python
from modelops_core.errors import ResourceLimitExceeded

if object_count > max_allowed:
    raise ResourceLimitExceeded(f"Exceeded limit: {object_count} > {max_allowed}")
```

If a standard exception is sufficient (e.g., `FileNotFoundError`), use it directly.

---

## Tests

- **Framework**: pytest
- **Fixtures**: place shared fixtures in `tests/conftest.py`
- **Test files**: `test_<module>.py` or `test_<feature>.py`
- **Test functions**: `test_<behavior>_<condition>`

Example:

```python
def test_apply_update_invalid_status_blocked(sample_repo: Path) -> None:
    """Setting status to an invalid value should block the apply."""
    ...
```

Use type hints in tests when they improve readability, but they are not required.

---

## CLI Commands

New CLI commands live in `src/modelops_core/cli.py` and follow this pattern:

```python
@app.command("export-schema")
@with_telemetry("export-schema")
def export_schema(
    repo: str | None = typer.Option(None, "--repo", help="Path to model repository."),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON."),
) -> None:
    """Short imperative description."""
    repo_root = _resolve_repo(repo)
    ...
```

- Use `typer.Option` for flags and optional arguments.
- Use `typer.Argument` for required positional arguments.
- Add `# noqa: B008` when `typer.Option` is used with `Path` defaults.
- Always support `--json` for agent-facing output.

---

## Generated and Disposable Files

Never edit files under `generated/` manually. They are rebuilt by `modelops build-index`.
Never commit:

- `.env` files
- `__pycache__/` or `.pytest_cache/`
- Local runtime files (e.g., `=4.0` artifacts)
- SQLite databases or JSONL exports in `generated/`

---

## See Also

- [`AGENTS.md`](../../AGENTS.md) — agent-focused project overview and quick reference
- [`TESTING_STRATEGY.md`](TESTING_STRATEGY.md) — test patterns and coverage expectations
- [`CLI_CONTRACTS.md`](CLI_CONTRACTS.md) — stable JSON output contracts
