# Skill: Architecture Decision — Martenweave

## When to use
Use when a task changes core architecture, source-of-truth boundaries, validation authority, object semantics, domain-pack boundaries, dependencies, or external write behavior.

## Inputs
- Proposed architecture change.
- Affected docs, code, examples, and tests.

## Read first
1. `docs/architecture/ARCHITECTURE_DECISIONS.md`
2. `docs/architecture/CORE_DOMAIN_MODEL.md`
3. `docs/architecture/DOMAIN_PACK_BOUNDARY.md`
4. Relevant source and tests.

## Do not do
- Do not make accidental architecture changes inside implementation work.
- Do not move domain-specific behavior into core without a decision.
- Do not add heavy infrastructure without an issue.
- Do not weaken canonical/generated or proposal/approval boundaries.

## Procedure
1. State the decision being made.
2. Identify whether it affects core, domain pack, integration, generated index, or AI workflow.
3. Compare at least two practical options when the decision is non-trivial.
4. Update architecture docs and tests if behavior changes.
5. Create or reference a GitHub architecture decision issue for large changes.

## Validation
```bash
.venv/bin/python -m pytest -v
.venv/bin/python -m ruff check .
```

Add example validation if canonical behavior changes.

## Output format
Return:
- decision summary;
- affected boundary;
- files changed;
- validation result;
- follow-up issue if needed.
