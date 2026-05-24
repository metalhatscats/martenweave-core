# Skill: Project Orientation — Martenweave

## When to use
You just opened this repository and need to understand what it is, where things live, and how to navigate safely before making any change.

## Inputs
- None (self-contained onboarding).

## Read first
1. `AGENTS.md` (project root) — full project overview, conventions, and quick reference.
2. `pyproject.toml` — dependencies, test configuration, ruff settings.
3. `src/modelops_core/cli.py` — available CLI commands and their signatures.
4. `src/modelops_core/schemas/common.py` — canonical object types and base schemas.
5. `examples/customer_bp_model/` — a working canonical model slice to copy patterns from.

## Do not do
- Do not assume this is a generic web framework; it is a backend CLI library.
- Do not edit files in `generated/`; they are rebuilt by `modelops build-index`.
- Do not treat sample datasets in `data/` as canonical model truth.

## Procedure
1. Verify Python >=3.11 is active: `python3 --version`
2. Install in editable mode: `pip install -e .`
3. Confirm CLI is available: `modelops --help`
4. Run the full test suite to establish baseline: `pytest`
5. Run lint to establish baseline: `ruff check .`
6. Open `examples/customer_bp_model/model/` and inspect 2–3 `.md` files to learn the canonical file format (YAML frontmatter + Markdown body).

## Validation
- `pytest` passes with no failures.
- `ruff check .` reports no errors.
- `modelops --help` lists commands: `init`, `validate`, `build-index`, `health`, `impact`, `propose-patch`.

## Output format
Return a concise summary:
- What the repo does (1 sentence)
- Technology stack (Python 3.11+, Pydantic, Typer, Rich, SQLite)
- Three most important directories (`src/modelops_core/`, `tests/`, `examples/`)
- One canonical file example path
