# Integration Boundaries

## Principle

Integrations bring input into Martenweave and receive exports from Martenweave. They are not the model source of truth.

## Allowed Integration Roles

| Role | Behavior |
|---|---|
| Import | Read files, spreadsheets, metadata, tickets, or docs and create profiles or `PatchProposal`s. |
| Export | Produce CSV, XLSX, JSONL, reports, or packages from canonical/indexed model data. |
| Reference | Store external IDs, URLs, checksums, and timestamps as evidence metadata. |

## Forbidden By Default

- Direct writes into external business systems.
- Treating an external spreadsheet, catalog, or SaaS tool as canonical model truth.
- Background sync that silently changes canonical files.
- Credential storage in canonical files.

## Future Adapters

Local files and spreadsheets come first. Cloud drives, Git publishing, catalogs, MCP, and external systems require explicit issues and must preserve the proposal-first model.
