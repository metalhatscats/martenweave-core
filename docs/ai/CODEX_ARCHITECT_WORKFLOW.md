# Codex Architect Workflow

## Purpose

Codex prepares the repository for reliable implementation. It audits architecture, clarifies boundaries, hardens validation, trims stale docs, and makes tasks ready for Kimi.

## Use Codex For

- architecture audits and boundary cleanup;
- validation ladder and CI design;
- docs restructuring and ownership maps;
- focused refactors with limited blast radius;
- issue writing and acceptance criteria;
- checking whether a task is ready for long-loop execution.

## Workflow

1. Inspect the current repo before proposing edits.
2. Identify product, architecture, validation, and agent-readiness gaps.
3. Prefer small structural improvements over broad rewrites.
4. Preserve working code unless a blocker is found.
5. Create agent-ready issues for deferred work.
6. Validate with the same commands Kimi will use.

## Output

Codex closeout should state:

- verdict: AI-ready, partially AI-ready, or not AI-ready;
- main findings;
- files changed;
- validation commands and results;
- issues created or reused;
- recommended next issues for Kimi.
