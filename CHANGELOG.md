# Changelog

All notable changes to Martenweave Core.

## [0.4.0] — 2026-05-26

### Added

- **MCP server** (#77, #79, #78): Optional FastMCP server exposing Martenweave as safe MCP tools, resources, and prompts. Includes 6 read-only tools, 8 resources, 6 prompts, and 6 write-intent tools flowing through PatchProposal/ChangeRequest workflow.
- **Local application usage telemetry** (#82): Privacy-safe command telemetry writing to `generated/usage_events.jsonl`. `@with_telemetry` decorator instruments 12 CLI commands. Telemetry failures never break workflows.
- **AI usage event logging** (#81): Records metadata about AI provider invocations to `generated/ai_usage_events.jsonl`. Includes token estimation, cost estimation, and `wrap_ai_adapter()` for transparent instrumentation.
- **System lineage model** (#65): Cross-system data flow tracking with `IntegrationFlow`, `DataFlowStep`, `TransformationRule`, `Interface`, `InterfaceEndpoint`, `Application`, and `System` objects.
- **GitHub write integration** (#58): Publish issue drafts and pull requests from PatchProposals and ChangeRequests.
- **Google Drive / Sheets connectors** (#56, #57, #50): Import CSV/XLSX from Google Drive, import Google Sheets as PatchProposals, and export models to Google Sheets.
- **Source registry** (#54): Track imported files and external references with `SourceRegistryService`.
- **Git bundles** (#52): Generate GitHub-ready change bundles from PatchProposals.
- **Excel business-review roundtrip** (#48): Export formatted XLSX workbooks for business review and re-import changes.
- **Static docs build** (#59): Generate static Markdown documentation from the model index.
- **Usage report** (#89): Aggregate audit events into command and status summaries via `usage-report` CLI.
- **Config guard** (#43): Scan repositories for secrets and configuration guardrail issues.
- **Proposal impact analysis** (#47): BFS-based impact analysis for PatchProposal operations.
- **Approval gates and ChangeRequest workflow** (#44, #45): Create, approve, reject, and manage ChangeRequests with risk scoring.
- **Notification events** (#61): Emit and preview notification events for workflow actions.
- **Resource limits** (#62): Enforce max_objects, max_index_objects, and max_proposal_operations.
- **Schema versioning** (#41): Migrate canonical objects to current schema version.
- **Diff command** (#39): Compare two model repositories and show differences.
- **Search and query** (#40): Keyword search and structured queries over the generated index.
- **Product and commercial documentation** (#83–#93): Interview guide, ICP positioning, pilot package, collaboration model, commercial packaging, security checklist, and Data Model Book playbook.

### Changed

- **README** (#169): Expanded command reference to cover all 30+ CLI commands.
- **Docs index** (#171): Added `docs/README.md` as the documentation landing page.

### Fixed

- **Validation JSON output** (#126): `validate --json` now emits parseable JSON.
- **Schema version normalization** (#124): Example canonical objects aligned to schema version 1.0.
- **Release-safe config guard** (#466): Release/smoke mode distinguishes tracked, untracked, and ignored files so ignored local `.env` findings remain visible without blocking clean release scans.
- **Release smoke execution**: Release smoke now uses the installed `modelops` executable consistently in CI and local validation.

---

## [0.0.1] — 2026-05-24

### Added

- Initial scaffold: canonical model format, deterministic validation (Layer 1–3), SQLite index builder, CLI with init/validate/build-index/health/impact/propose-patch.
- SAP domain pack: KNVV, KNB1, KNVP, BUT000 context rules.
- Example models: `customer_bp_model`, `simple_product_model`, `generic_product_model`.
