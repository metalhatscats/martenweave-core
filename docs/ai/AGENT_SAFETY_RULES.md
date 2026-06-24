# Agent Safety Rules

## Allowed

- Edit source code, tests, docs, templates, and skills.
- Run local validation commands.
- Create `PatchProposal` files when the task is explicitly model-change proposal work.
- Create GitHub issues when explicitly requested and `gh` is authenticated.

## Forbidden

- Commit secrets or credentials.
- Read or expose ignored `.env` contents.
- Treat raw datasets as canonical model truth.
- Persist raw sensitive data in canonical files, docs, generated profiles, prompts, or reports.
- Mutate canonical model files as if AI output were already approved.
- Bypass validation to make a build pass.
- Treat generated SQLite or JSONL artifacts as source of truth.
- Hard-code a starter domain into core architecture.
- Add cloud, SaaS, graph, queue, workflow, or external write dependencies without an explicit issue.
- Write directly into external business systems.

## Canonical Model Safety

AI-created model changes must use:

```text
PatchProposal -> validation -> human approval -> ChangeRequest -> apply -> audit
```

Direct edits to canonical example models are allowed only for explicit repository maintenance tasks and must be validated.

## Secret Handling

Run `martenweave config-guard --repo . --json` when touching config, AI providers, generated artifacts, or docs that mention credentials. If it fails because local ignored `.env` contains secrets, report that fact without printing secret values.

### Validation ladder

Include config-guard in agent workflows that modify or validate repositories:

1. Before proposing changes that touch `modelops.config.yaml`, `.env`, or provider settings.
2. Before committing docs that include example credentials or connection strings.
3. Before publishing releases or generated artifacts.

Never print secret values in reports, prompts, or commit messages.
