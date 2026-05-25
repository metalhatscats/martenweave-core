# Canonical Model Boundary

## Source Of Truth

Canonical model truth lives in a model repository:

```text
modelops.config.yaml
model/
  *.md
  *.yaml
  *.yml
```

Canonical files contain stable object IDs, types, statuses, references, governance fields, and human-readable descriptions.

## Canonical File Rules

- Every object needs a globally unique stable ID.
- IDs must match `^[A-Z][A-Z0-9]*(-[A-Z0-9]+)*$`.
- References must point to existing objects of expected types.
- Markdown body is explanatory; YAML frontmatter is machine-readable.
- Raw datasets are not canonical model files.
- Generated indexes are not canonical model files.

## AI Boundary

AI may create or modify canonical model content only through reviewable proposals:

```text
PatchProposal -> validation -> human approval -> ChangeRequest -> apply
```

Direct AI mutation of canonical truth is forbidden.

## Agent Maintenance Exception

Agents may edit example canonical files only when the task explicitly asks for repository maintenance, fixtures, or docs-aligned examples. They must run validation afterward and report warnings.
