# Martenweave — Integration Architecture

Version: `0.1-draft`  
Document type: Architecture / integration boundary  
Scope: How external systems bring input into and receive exports from a Martenweave model repository  
Status: Draft for product development

---

## 1. Purpose

This document defines the **integration architecture** for Martenweave. It describes how external systems — local files, spreadsheets, cloud storage, Git, and future sources — interact with a model repository without violating the rule that **canonical model files are the source of truth**.

Martenweave is local-first and file-based. Integrations are optional adapters that sit at the repository boundary. They may:

- **Import** external data as profiles, datasets, or PatchProposals.
- **Export** generated views, reports, and workbooks for review or downstream use.
- **Publish** model metadata to versioning or collaboration platforms.

Integrations **must not** silently mutate canonical model files, write directly into `model/`, or treat external storage as the model source of truth.

---

## 2. Integration categories

```text
┌─────────────────────────────────────────────────────────────┐
│                    Martenweave Repository                    │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────────┐   │
│  │  model/ │  │generated│  │  data/  │  │    docs/    │   │
│  │(source │  │(index,  │  │(samples,│  │(markdown   │   │
│  │ of truth│  │ registry│  │ profiles│  │  docs)      │   │
│  └────┬────┘  └────┬────┘  └────┬────┘  └─────────────┘   │
│       │            │            │                           │
│  ┌────┴────────────┴────────────┴─────────────────────┐    │
│  │              Integration Boundary                   │    │
│  │  (adapters, registries, export services, bundles)  │    │
│  └────┬────────────┬────────────┬────────────┬────────┘    │
│       │            │            │            │              │
│   Local Files   Spreadsheets  Cloud/Drive   Git / GitHub  │
│   (CSV, XLSX)   (Excel,       (Google      (repos, PRs,   │
│                 Sheets)        Drive, S3)    Pages)        │
│                                                             │
│   Future: Databases, dbt, OpenAPI, OpenLineage, MCP        │
└─────────────────────────────────────────────────────────────┘
```

### 2.1 Local files

**Role:** First-class input and output channel.

**Import flows:**

- `profile-dataset` — profile a local CSV/Excel file and register it in the source registry.
- `import-model-sheet` — read a structured Excel workbook and produce a PatchProposal.
- Direct file copy into `data/samples/` for manual inspection.

**Export flows:**

- Excel roundtrip workbook to `generated/` for review.
- JSONL exports (`search_documents.jsonl`, `lineage_edges.jsonl`) for downstream tools.
- Git bundles (`generated/git_bundles/`) for manual PR creation.

**Principles:**

- Local files are the default. No credentials or network calls required.
- File hashes (SHA-256) are stored in the source registry for integrity.
- Paths are resolved relative to the repository root.

### 2.2 Spreadsheet roundtrip

**Role:** Human-friendly review and edit surface.

**Supported formats:**

- Excel (`.xlsx`) — full roundtrip via `openpyxl`.
- Google Sheets — explicit export and import via optional adapter (future).

**Flows:**

```text
Canonical model files  --export-->  Excel/Sheets workbook (review view)
                                              |
                                              v (human edits)
Edited workbook  --import-->  PatchProposal  --validate-->  approval --> canonical update
```

**Principles:**

- Export is always a generated view. The workbook is not canonical.
- Import from a spreadsheet always produces a `PatchProposal`, never a direct canonical write.
- Stable object IDs are preserved across export and re-import.
- Generated metadata columns (e.g., `__source_row__`, `__generated_at__`) are ignored on re-import.

### 2.3 Cloud storage (Google Drive, future S3)

**Role:** Optional input and output channel for teams that store source data or review artifacts in cloud storage.

**Supported flows:**

- Import XLSX/CSV files from Google Drive as dataset profiles or PatchProposal sources.
- Export model review workbooks to Google Drive for sharing.
- Future: list, fetch, and write files via `ConnectorAdapter` implementations.

**Principles:**

- Cloud storage is an I/O channel, not a model store.
- OAuth/client credentials are handled via environment variables or local config, never committed.
- Every cloud file interaction is registered in the source registry with an external reference ID.
- The `ConnectorAdapter` protocol is the extension point for new cloud providers.

### 2.4 Git publishing

**Role:** Versioning, review, and publishing layer.

**Supported flows:**

- Local model repository is a Git repository (user-managed).
- `modelops git-bundle <proposal-id>` generates a reviewable change bundle.
- Future: controlled GitHub write integration for issue drafts, PR creation, and Pages publishing.

**Principles:**

- Git tracks canonical files, docs, examples, and config templates.
- Generated artifacts (`generated/`, large exports, raw datasets) are excluded by default via `.gitignore`.
- Secrets and local credentials are never committed.
- Model changes are proposal-first: a PatchProposal or ChangeRequest precedes any canonical file update.
- GitHub is a versioning/review layer, not a runtime database.

### 2.5 Future external sources

Planned adapter categories (not in v0.1):

- **Database metadata** — schema import from PostgreSQL, SAP, etc.
- **dbt / analytics models** — import dbt model definitions and lineage.
- **JSON Schema / OpenAPI** — import schema definitions as canonical objects.
- **OpenLineage** — export system lineage in OpenLineage-compatible format.
- **MCP server** — expose model navigation and safe write-intent tools to AI agents.

---

## 3. Source registry metadata

Every external input is recorded as a `SourceEntry` in `generated/source_registry.jsonl`.

### 3.1 Core fields

| Field | Type | Description |
|---|---|---|
| `source_id` | `str` | Stable identifier for the source (e.g., filename, Drive file ID) |
| `source_type` | `str` | `dataset_profile`, `model_sheet_import`, `google_drive_file`, `local_file`, etc. |
| `file_path` | `str \| None` | Local path, if applicable |
| `file_hash` | `str \| None` | SHA-256 checksum for integrity verification |
| `registered_at` | `str` | ISO-8601 timestamp of registration |
| `status` | `str` | `registered`, `imported`, `stale`, `error`, etc. |
| `metadata` | `dict` | Provider-specific metadata (size, revision, external URL, etc.) |

### 3.2 Optional linkage fields

| Field | Type | Description |
|---|---|---|
| `external_reference` | `str \| None` | Cloud provider file ID, URL, or URI |
| `last_seen_at` | `str \| None` | Timestamp of last successful read |
| `imported_at` | `str \| None` | Timestamp when this source was last imported |
| `profile_id` | `str \| None` | Linked dataset profile ID |
| `linked_dataset` | `str \| None` | Linked canonical Dataset object ID |
| `linked_proposals` | `list[str]` | PatchProposal IDs generated from this source |

### 3.3 Registry behavior

- Append-only JSONL. New entries for the same `source_id` supersede older ones in read-time deduplication.
- Registry is disposable — it can be rebuilt by re-running import and profile commands.
- Registry lives in `generated/` and is excluded from Git.

---

## 4. Safe integration principles

### 4.1 Canonical files remain model truth

No adapter, connector, or external system may write directly into `model/` except through the approved change workflow:

```text
PatchProposal  -->  validation  -->  human approval  -->  ChangeRequest  -->  canonical update
```

### 4.2 Imports generate profiles and PatchProposals

All imports from external systems produce either:

- A `DatasetProfile` (for raw data inspection), or
- A `PatchProposal` (for structured model changes).

Neither is canonical until approved and applied.

### 4.3 Exports are generated views

All exports (Excel, Sheets, JSONL, reports) are derived from canonical files. They are marked as generated, carry timestamps, and are stored in `generated/` or external storage, never in `model/`.

### 4.4 External writes require explicit user action

No automatic background sync. Every write to an external system is triggered by an explicit CLI command (e.g., `modelops export-excel`, future `modelops export-sheets`).

### 4.5 Provider credentials are handled outside canonical model files

- OAuth tokens, API keys, and service account files live in environment variables or local config files (e.g., `.env`).
- They are never stored in canonical model files, `modelops.config.yaml`, or the source registry.
- They are excluded from Git via `.gitignore`.

---

## 5. Adapter extension model

New integrations are added by implementing the `ConnectorAdapter` protocol.

```python
class ConnectorAdapter(Protocol):
    def list_sources(self, prefix: str | None = None) -> list[ConnectorSourceInfo]: ...
    def fetch_metadata(self, source_id: str) -> ConnectorSourceInfo: ...
    def fetch_content(self, source_id: str) -> bytes: ...
    def write_content(self, source_id: str, content: bytes) -> None: ...
    def to_source_entry(self, source_id: str) -> SourceEntry: ...
```

### 5.1 Existing adapters

| Adapter | Status | Purpose |
|---|---|---|
| `LocalFileConnector` | Implemented | Local filesystem read/write with path escaping guards |
| `GoogleSheetsConnector` | Planned (#50, #57) | Export/import Google Sheets workbooks |
| `GoogleDriveConnector` | Planned (#56) | List, fetch, and write Drive files |
| `GitHubConnector` | Planned (#58) | Controlled issue/PR creation |

### 5.2 Adding a new adapter

1. Create a module in `src/modelops_core/connectors/`.
2. Implement the `ConnectorAdapter` protocol.
3. Normalize all errors to `ConnectorError` with `connector_type`, `action`, and `details`.
4. Add tests with mocked external calls.
5. Register the adapter in the source registry via `to_source_entry()`.
6. Add a CLI command or flag for explicit user invocation.
7. Document the adapter in this architecture document and in the adapter's own module docstring.

---

## 6. Data flow diagrams

### 6.1 Import flow

```text
External source
      │
      ▼
ConnectorAdapter.fetch_content()
      │
      ▼
Import service (profile or model-sheet)
      │
      ├──► DatasetProfile  ──► source_registry.jsonl
      │
      └──► PatchProposal  ──► validation  ──► human review  ──► ChangeRequest
```

### 6.2 Export flow

```text
Canonical model files
      │
      ▼
Export service (Excel, Sheets, JSONL)
      │
      ▼
Generated review view
      │
      ├──► generated/  (local)
      │
      └──► ConnectorAdapter.write_content()  (external)
```

### 6.3 Git publishing flow

```text
Canonical model files
      │
      ▼
modelops validate && modelops build-index
      │
      ▼
modelops git-bundle <proposal-id>
      │
      ▼
Git bundle in generated/git_bundles/
      │
      ▼
Manual or future automated PR creation
```

---

## 7. Security and privacy defaults

| Concern | Default |
|---|---|
| Cloud credentials | Environment variables only; never committed |
| Raw datasets | Stored in `data/`; excluded from Git |
| Generated artifacts | Stored in `generated/`; excluded from Git |
| Canonical files | Stored in `model/`; versioned in Git |
| External file hashes | SHA-256; verified on re-import |
| Network calls | Only on explicit CLI command; no background polling |
| AI provider data | No raw dataset sharing with external AI providers |

---

## 8. Related issues and future work

| Issue | Description | Status |
|---|---|---|
| #49 | Google Drive and Google Sheets integration boundary | Design doc |
| #50 | Google Sheets export adapter | Implementation |
| #51 | GitHub publishing workflow | Design doc |
| #56 | Google Drive import adapter | Implementation |
| #57 | Google Sheets import adapter | Implementation |
| #58 | Controlled GitHub write integration | Implementation |
| #63 | Database metadata import design | Future |
| #64 | JSON Schema and OpenAPI import | Future |
| #67 | OpenLineage-compatible export | Future |
| #71 | Portable model package archive | Design + code |
| #72 | Source refresh and stale detection | Design + code |
| #74 | Bulk refactor operations | Design + code |

---

## 9. Validation

This architecture document is validated by:

```bash
pytest && ruff check .
```

All integration implementations must include tests with mocked external calls and must not contact live services during the test suite.
