# Known Limitations

> Verified product limitations. Agents must **not** re-report these as new bugs or
> "fix" them without an L3 decision — they are documented boundaries of the current
> product. Each entry has a source. When a limitation is resolved, remove it here
> in the same patch.

## Product scope limitations (by design)

- **No profiling of production databases / no ETL** — datasets enter as CSV/XLSX
  files only. Source: `docs/governance/DAMA_ALIGNMENT.md` (Limitation notes).
- **No RBAC / authentication / multi-user** — the Workbench and API are local,
  single-user, trust-based surfaces. Source: `docs/architecture/WORKBENCH_BOUNDARY.md`,
  `docs/product/MVP_SCOPE.md` §3.2.
- **No workflow engine** — approvals are gates and statuses, not a BPM engine.
  Source: `docs/architecture/MODEL_REPOSITORY_SPEC.md` §37.
- **No direct SAP integration or write-back** — SAP tables/fields are modeled as
  `FieldEndpoint` metadata, never live connections. Source: `README.md`
  ("What Martenweave is / is not"), MVP_SCOPE §3.2.
- **No real-time SAP lineage / ABAP extraction / graph DB** — lineage is computed
  from canonical references. Source: `docs/architecture/DATA_LINEAGE_AND_IMPACT_MODEL.md` §42.
- **No full DAMA compliance claims** — alignment documentation only.
  Source: MVP_SCOPE §3.2 (12).
- **AI provider is a stub by default** — `NoProviderAdapter` refuses to guess
  (deterministic "no proposal generated"); real proposals require a configured
  provider. This is the no-silent-mutation gate working as intended, not a bug.

## Verified technical limitations (candidates for future L2/L3 work)

- **Owner names resolve in the Workbench ledger but not in CLI reports** — the
  `owners` CLI report still prints raw `PERSON-*` IDs (the Workbench ledger
  resolves display names since `6ae5a36`). Cosmetic; resolve in the report layer
  if users ask. Verified 2026-07-19.
- **Very large models warn above a configurable threshold** — `build-index` is a
  full rebuild by design; huge repos may need a higher limit or a split.
  Source: `README.md` Core Principles.
