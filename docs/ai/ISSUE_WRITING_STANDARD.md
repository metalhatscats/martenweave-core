# Issue Writing Standard

Every agent-ready issue must be small enough to complete in one focused loop.

## Required Sections

```markdown
## Goal
One sentence describing the outcome.

## Scope
Files, behavior, or docs that may change.

## Acceptance criteria
- Observable, testable criteria.

## Validation command
Exact command(s) the agent must run.

## Out of scope
Explicit exclusions.

## Safety notes
Canonical/generated/data/secret/external-write constraints.

## Core/domain-pack impact
State whether the change affects core, a domain pack, examples, or docs only.
```

## Good Issues

- Name the command, module, doc, or example involved.
- Include a validation command.
- State whether generated files may be touched.
- Keep architecture decisions separate from implementation tasks.

## Bad Issues

- "Improve everything."
- "Make AI better."
- "Refactor docs."
- "Add enterprise platform support."

Split broad work into small issues with one measurable outcome each.
