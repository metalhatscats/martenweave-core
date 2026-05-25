# Skill: Documentation Discipline — Martenweave

## When to use
Use when adding, updating, or reorganizing docs.

## Inputs
- Behavior, command, architecture, or product boundary being documented.
- Existing docs that may overlap.

## Read first
1. `docs/ai/README.md`
2. `docs/architecture/README.md`
3. `docs/product/README.md`
4. `docs/developer/README.md`

## Do not do
- Do not create duplicate docs with unclear ownership.
- Do not promote UI, SaaS, or one domain as core MVP scope.
- Do not write generic agent advice detached from this repo.
- Do not update docs for behavior that does not exist unless clearly marked planned.

## Procedure
1. Identify the owning doc layer: AI, architecture, product, developer, operations, or examples.
2. Link to existing detail instead of duplicating it.
3. Keep docs short, operational, and command-oriented.
4. Update `AGENTS.md` only for front-door guidance.
5. Run skill validation if skills are touched.
6. Run tests only when docs define executable contracts or commands.

## Validation
```bash
.venv/bin/python scripts/validate_skills.py
```

For command docs, also run the documented command when practical.

## Output format
Return:
- docs changed;
- stale or duplicate docs consolidated;
- commands verified;
- known remaining doc gaps.
