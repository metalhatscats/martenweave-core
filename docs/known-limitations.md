# Known Limitations

Martenweave Core is useful today, but it is still an early backend-first project. These limits are intentional to state plainly before a public release.

## Product Scope

- No production or hosted UI is included. `docs-build` can generate a local static read-only viewer,
  but it is disposable output from the SQLite index, not an editable application.
- No hosted SaaS tenant, login system, or managed workflow engine is included.
- No SAP write-back, browser editing, workflow approvals, or AI auto-mutation path exists in the
  generated viewer.
- SAP migration and MDM examples are starter scenarios, not an official SAP partnership or SAP-certified product claim.
- Generated indexes and generated viewer files are local artifacts, not a shared production database
  service.

## AI and Automation

- The default AI adapter is `NoProviderAdapter`, a deterministic scaffold that makes no provider call.
- Provider-backed proposal generation is optional and still evolving.
- AI output is not canonical truth. It must become a `PatchProposal`, pass deterministic checks, and receive human approval before canonical files change.
- Raw private datasets should not be sent to an external provider by default.

## Model Coverage

- Bundled examples intentionally contain methodology warnings to demonstrate health, scorecard, and gap reporting.
- Some deep design docs describe future import/export capabilities that are not yet implemented as CLI commands.
- Domain packs beyond the included examples need more real-world fixtures and validation rules.

## Integrations

- Google Drive, Google Sheets, GitHub publishing, MCP, and local API paths are optional integration surfaces.
- External write integrations require local credentials and should be tested with synthetic data first.
- Database metadata, JSON Schema/OpenAPI, dbt, graph projection, and OpenLineage docs include roadmap/design content; verify command availability with `modelops --help`.

## Release Operations

- Public release does not imply a PyPI publish unless the maintainer intentionally triggers the release workflow.
- Generated artifacts should be rebuilt locally and normally left uncommitted.
- The project is local-first. Teams embedding it in pipelines own their own repository permissions, retention, and provider credentials.
