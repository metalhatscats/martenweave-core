# Roadmap v0.1

> **Historical.** This document captures the original v0.1 feature list.
> The active pilot-first roadmap is now in `ROADMAP_PILOT.md`.

## Objective

Ship a useful backend-first core that can be validated locally and executed by AI coding agents through small GitHub issues.

## v0.1 Core

1. Repository init and config loading.
2. Canonical file parser and scanner.
3. Object type registry and reference metadata.
4. Deterministic validation pipeline.
5. Generated SQLite/search/lineage index.
6. Query, search, trace, impact, health, and analysis commands.
7. Dataset profiling and simple model inference into `PatchProposal`.
8. PatchProposal validation, impact, dry-run, apply, audit, and ChangeRequest gates.
9. Export to CSV/XLSX.
10. Skills, docs, templates, and validation ladder for agent execution.

## v0.2 Candidates

- stronger CLI JSON contract tests;
- CI workflow for tests, lint, skills, and examples;
- acceptance demo script;
- privacy/sanitization hardening;
- performance budgets;
- integration adapter interfaces.

## Later

- optional UI;
- optional GitHub publishing workflow;
- optional MCP server;
- optional cloud drive and spreadsheet adapters;
- optional graph projection export;
- hosted team workspace.

Later items must not block v0.1.
