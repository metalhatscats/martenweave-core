# Agent Context Loading

## First Files

Every agent starts with:

1. `AGENTS.md`
2. `skills/README.md`
3. task-specific skill under `skills/*/SKILL.md`
4. `pyproject.toml`
5. relevant tests under `tests/`

## Load By Task Type

| Task | Read next |
|---|---|
| Object types or references | `src/modelops_core/schemas/common.py`, `src/modelops_core/schemas/registry.py` |
| Validation behavior | `src/modelops_core/validation/pipeline.py`, relevant `tests/test_*validation*.py` |
| CLI command | `src/modelops_core/cli.py`, `docs/developer/CLI_CONTRACTS.md`, `tests/test_cli.py` |
| Index/search/trace/impact | `src/modelops_core/index/`, `src/modelops_core/impact/`, `src/modelops_core/trace/` |
| Patch proposal or approval | `docs/architecture/PATCH_PROPOSAL_AND_APPROVAL_FLOW.md`, `src/modelops_core/patching/`, `src/modelops_core/change_request/` |
| Dataset profiling or gaps | `src/modelops_core/imports/`, `src/modelops_core/gaps/`, `docs/architecture/AI_CONTEXT_AND_EVIDENCE_MODEL.md` |
| Domain pack | `docs/architecture/DOMAIN_PACK_BOUNDARY.md`, `src/modelops_core/domain_packs/`, `tests/test_domain_packs.py` |

## Ignore By Default

- `generated/`
- `.venv/`
- `.pytest_cache/`
- raw datasets unless the task is profiling/import behavior;
- local `.env` files;
- large binary files.

## Context Hygiene

Read summaries and indexes before full files. Use `rg` for targeted searches. Load examples only when they clarify canonical shape. Do not paste raw dataset rows into AI context. Prefer IDs, schemas, command output summaries, and file paths.
