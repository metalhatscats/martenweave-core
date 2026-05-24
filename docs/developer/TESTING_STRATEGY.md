# Testing Strategy

## Foundation

The foundation provides runnable or clearly stubbed quality gates. Product behavior tests are added with implementation tasks.

## Backend

Use pytest for:

- frontmatter parsing;
- schema validation;
- stable ID uniqueness;
- reference resolution;
- SAP context validation;
- dataset gap checks;
- PatchProposal safety;
- index generation;
- impact traversal.

## Frontend

Use Vitest for component behavior and Playwright for MVP workflows once screens exist.

## Acceptance Evidence

Every task must record commands run, results, changed files, and remaining gaps in `Result Notes`.
