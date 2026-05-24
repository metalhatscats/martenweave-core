# Martenweave Skills Index

This directory contains operational skills for AI coding agents working on the Martenweave backend-first, CLI-driven, canonical-model-registry codebase.

## Core Rule

**AI proposes, validators verify, humans approve.**

The AI agent may suggest changes, run deterministic validators, and produce reviewable artifacts (PatchProposals). It must never silently mutate canonical files. Humans approve changes, which then become ChangeRequests.

## Skill Quick Reference

| Scenario | Skill to use |
|---|---|
| Onboarding to the repo, first time setup | [`project-orientation`](project-orientation/SKILL.md) |
| Picking up a GitHub issue, implementing, testing, PRing | [`github-issue-loop`](github-issue-loop/SKILL.md) |
| Verifying canonical files, schemas, references, SAP rules | [`validation`](validation/SKILL.md) |
| Preventing source-of-truth drift, cleaning up processes, ending a session cleanly | [`memory-and-process-hygiene`](memory-and-process-hygiene/SKILL.md) |
| Adding or modifying canonical objects (domains, attributes, endpoints, mappings) | [`model-registry-core`](model-registry-core/SKILL.md) |
| Profiling a CSV dataset and finding column gaps against the model | [`dataset-gap-analysis`](dataset-gap-analysis/SKILL.md) |
| Understanding dependencies before deleting or changing an object | [`impact-analysis`](impact-analysis/SKILL.md) |
| AI proposing a model change for human review and approval | [`patch-proposal`](patch-proposal/SKILL.md) |

## Recommended GitHub Issue Loop

1. **Orient** — Use `project-orientation` if this is your first session.
2. **Plan** — Read the issue, relevant tests, and `AGENTS.md`.
3. **Branch & Reproduce** — Create a feature branch. Write a failing test for bugs, or an expectation test for features.
4. **Implement** — Make the smallest viable change. Follow code style (line length 100, Python 3.11+).
5. **Validate** — Run `pytest -v`, `ruff check .`, and `modelops validate` if canonical files changed.
6. **Impact check** — If modifying an existing object, run `modelops impact <ID>`.
7. **Hygiene** — Use `memory-and-process-hygiene` to check processes, memory, and `git status` before committing.
8. **Propose** — If the change is AI-initiated model knowledge, create a `PatchProposal` and wait for human approval.
9. **Submit** — Push and open a PR with test evidence and issue linkage.

## Validation

Run the structural validation script before relying on the skills layer:

```bash
python3 scripts/validate_skills.py
```

This checks that every skill directory exists, contains a `SKILL.md`, and has all required sections.
