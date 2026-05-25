# Architecture Decisions

## Current Decisions

| Decision | Status | Consequence |
|---|---|---|
| Canonical files are source of truth | accepted | `model/` Markdown/YAML objects define model truth. |
| Generated indexes are disposable | accepted | SQLite/JSONL outputs are rebuilt from canonical files. |
| Deterministic validation before indexing | accepted | Invalid references/types block healthy indexes by default. |
| AI proposes, humans approve | accepted | AI output becomes `PatchProposal`; approved work becomes `ChangeRequest`. |
| Core is domain-neutral | accepted | SAP and other domains live in optional domain packs/examples. |
| Local-first backend core before UI/platform | accepted | CLI and Python services lead; UI/cloud remain optional later layers. |
| Integrations are input/output channels | accepted | External systems never become source of truth for the model. |

## Decision Process

Use an architecture decision issue when a change:

- changes canonical object semantics;
- changes source-of-truth boundaries;
- adds a dependency category;
- changes validation authority;
- moves domain-specific behavior into core;
- introduces external writes or hosted infrastructure.

Architecture decisions must include the problem, considered options, chosen decision, validation impact, and rollback path.
