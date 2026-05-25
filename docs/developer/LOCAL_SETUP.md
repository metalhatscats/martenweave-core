# Local Setup

## Python

Martenweave Core requires Python 3.11 or newer. On this workstation, `/usr/bin/python3` is Python 3.9 and will fail on imports such as `StrEnum` and `datetime.UTC`.

Use the existing venv:

```bash
.venv/bin/python --version
.venv/bin/python -m pip install -e '.[dev]'
```

Or create a new one with Python 3.11:

```bash
python3.11 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
```

## Smoke Check

```bash
.venv/bin/modelops --help
.venv/bin/python -m pytest --collect-only -q
.venv/bin/python -m ruff check .
```

## Secrets

Do not commit `.env`. Use `.env.example` for placeholders only. Run:

```bash
.venv/bin/modelops config-guard --repo . --json
```
