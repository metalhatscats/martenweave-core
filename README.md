# martenweave-core

Backend-first agentic data model registry.

Turns data models into a structured, traceable, validated, AI-ready model knowledge layer. This repository contains the canonical model registry, deterministic validation, generated SQLite index, safe AI patch proposals, and Git-friendly model files.

SAP migration and Master Data Management are the **first domain pack** and proof case, not the product boundary. The core works for generic data models: domains, entities, attributes, relationships, datasets, mappings, rules, evidence, decisions, and change proposals.

**No UI is included.** This is a CLI-driven, backend/core library designed to be embedded in pipelines, IDEs, and agent workflows.

## Core Principles

- **Canonical files are the source of truth.** Markdown + YAML frontmatter objects live in `model/`.
- **Generated index is disposable.** SQLite and JSONL outputs are rebuildable from canonical files.
- **Deterministic validation first.** Every object is validated for IDs, types, references, and domain context rules before indexing.
- **AI must not silently mutate.** AI creates `PatchProposal` objects for human review. Approved changes become `ChangeRequest`s.
- **Local-first.** No cloud dependencies, no SaaS lock-in.

## What Martenweave is / is not

| Is | Is not |
|---|---|
| A backend-first model registry for data modeling, migration, and governance | A SAP-only tool |
| A canonical file store with generated indexes | A database-first MDM platform |
| A validator-gated, proposal-first editing workflow | A workflow engine |
| A local-first CLI and embeddable library | A SaaS platform |
| AI-assisted, with human approval required for changes | An autonomous AI agent that mutates models |

## Quickstart

```bash
# Install
pip install -e .

# Scaffold a new repository
modelops init ./my-model

# Validate canonical files
modelops validate --repo ./my-model

# Build SQLite index + JSONL exports
modelops build-index --repo ./my-model --jsonl

# Health report
modelops health --repo ./my-model

# Impact analysis
modelops impact FEP-S4-KNVV-KDGRP --repo ./my-model

# Propose a patch from a note
modelops propose-patch --from ./note.md --repo ./my-model
```

## Example Model

The `examples/customer_bp_model/` directory contains the first domain pack: a full canonical model slice for SAP Business Partner → Customer:

```
Business Partner -> Customer -> Customer Sales Area -> Customer Group -> KNVV-KDGRP
```

Run validation against it:

```bash
modelops validate --repo examples/customer_bp_model
```

## Architecture

```
modelops.config.yaml        # Repository configuration
model/                      # Canonical Markdown + YAML objects
  DOMAIN-*.md
  ENTITY-*.md
  ATTR-*.md
  FEP-*.md
  MAP-*.md
  ...
generated/                  # Disposable artifacts
  modelops.db               # SQLite index
  search_documents.jsonl    # Search export
  lineage_edges.jsonl       # Lineage export
  audit_events.jsonl        # Audit log
data/samples/               # Sample datasets for profiling
```

## Domain Rules (SAP example)

The first domain pack includes SAP-specific context rules:

- `Attribute` is business meaning.
- `FieldEndpoint` is physical representation.
- `AttributeUsage` links an `Attribute` to a specific business context.
- `Mapping` links source and target `FieldEndpoint`s.
- `KNVV` fields must be in `customer_sales_area` context.
- `KNB1` fields must be in `customer_company_code` context.
- `KNVP` fields must be in `customer_partner_function` context.
- `BUT000` fields must be in `bp_central` context.

Future domain packs can add their own validation rules without changing core concepts.

## Development

```bash
# Run tests
pytest

# Lint
ruff check .
```

## License

MIT
