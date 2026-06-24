# Martenweave — Google Drive and Google Sheets Integration Boundary

Version: `0.1-draft`  
Document type: Integration boundary / design specification  
Scope: How Martenweave interacts with Google Drive and Google Sheets  
Depends on: `docs/integration-architecture.md`  
Status: Draft for implementation

---

## 1. Purpose

This document defines the integration boundary between Martenweave and Google Drive / Google Sheets. It specifies supported flows, metadata contracts, access patterns, and safety rules that ensure Google Drive and Sheets are treated as **input/output channels**, not as canonical model storage.

All principles from `docs/integration-architecture.md` apply:

- Canonical model files in `model/` remain the source of truth.
- Imports from Google Drive/Sheets produce profiles or PatchProposals, never direct canonical mutations.
- Exports to Google Sheets are generated review views, clearly marked as such.
- OAuth credentials are handled outside canonical model files.

---

## 2. Supported flows

```text
┌─────────────────────────────────────────────────────────────────────────┐
│                         Google Drive / Sheets                            │
│                                                                          │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐             │
│  │  XLSX/CSV    │    │  Google      │    │  Google      │             │
│  │  files       │    │  Sheet       │    │  Sheet       │             │
│  │  (import)    │    │  (profile)   │    │  (review)    │             │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘             │
│         │                   │                   │                       │
│         │  fetch_content()  │  fetch_content()  │  write_content()    │
│         ▼                   ▼                   ▼                       │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    GoogleDriveConnector                          │   │
│  │                    GoogleSheetsConnector                         │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│         │                   │                   │                       │
└─────────┼───────────────────┼───────────────────┼───────────────────────┘
          │                   │                   │
          ▼                   ▼                   ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         Martenweave Repository                          │
│                                                                          │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────────────┐│
│  │ Dataset     │    │ PatchProposal│    │  SourceRegistryEntry        ││
│  │ Profile     │    │ (model edit) │    │  (external reference)       ││
│  └─────────────┘    └─────────────┘    └─────────────────────────────┘│
│                                                                          │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────────────┐│
│  │ Export      │    │ Review      │    │  generated/                 ││
│  │ Service     │───►│ Workbook    │───►│  (not canonical)            ││
│  │             │    │ (XLSX/JSON) │    │                             ││
│  └─────────────┘    └─────────────┘    └─────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.1 Import XLSX/CSV files from Drive

**Flow:**

```text
User provides Drive file ID or share link
      │
      ▼
GoogleDriveConnector.fetch_content(file_id)
      │
      ▼
Local temp file  ──►  profile-dataset or import-model-sheet
      │
      ▼
SourceRegistryEntry with external_reference = Drive file ID
```

**Behavior:**

- File is downloaded to a temporary path, processed, then optionally cached in `data/samples/`.
- The source registry records the Drive file ID, MIME type, and revision marker.
- Re-import of the same file uses the revision marker to detect changes.

### 2.2 Profile a Google Sheet as a dataset source

**Flow:**

```text
User provides Sheet ID and range
      │
      ▼
GoogleSheetsConnector.fetch_content(sheet_id)
      │
      ▼
Dataset profiler treats sheet as a CSV-like dataset
      │
      ▼
DatasetProfile  ──►  source_registry.jsonl
```

**Behavior:**

- Sheet is read as a tabular dataset. The first row is treated as headers.
- Column names are normalized (trimmed, lowercased, spaces replaced with underscores).
- Data types are inferred using the same profiler used for local CSV files.
- The source registry stores the Sheet ID, tab name, and cell range.

### 2.3 Export model workbook to Drive

**Flow:**

```text
Canonical model files
      │
      ▼
Export service generates workbook (same structure as Excel roundtrip)
      │
      ▼
GoogleDriveConnector.write_content(file_id or new file)
      │
      ▼
File appears in user's Drive with generated metadata in description
```

**Behavior:**

- The exported workbook follows the same sheet structure as the Excel roundtrip template.
- Stable object IDs are preserved in the `id` column.
- Generated metadata columns (`__source_row__`, `__generated_at__`) are included.
- The Drive file description contains `martenweave-export`, generation timestamp, and repository name.

### 2.4 Publish model review workbook to Google Sheets

**Flow:**

```text
Canonical model files
      │
      ▼
Export service generates workbook data
      │
      ▼
GoogleSheetsConnector.write_content(sheet_id)
      │
      ▼
Sheet is populated with one tab per object category
```

**Behavior:**

- Each object category (Entities, Attributes, FieldEndpoints, etc.) gets its own Sheet tab.
- Header row is frozen.
- Stable object IDs are in column A.
- A hidden or protected `__metadata__` tab contains export timestamp, repository info, and a warning that this is a generated view.

### 2.5 Import edited Sheet as a PatchProposal

**Flow:**

```text
Edited Google Sheet (human review edits)
      │
      ▼
GoogleSheetsConnector.fetch_content(sheet_id)
      │
      ▼
Import service diffs against canonical model
      │
      ▼
PatchProposal  ──►  validation  ──►  human approval  ──►  ChangeRequest
```

**Behavior:**

- Rows with modified values are compared against canonical objects by ID.
- New rows (missing IDs or new IDs) are treated as create operations.
- Deleted rows are treated as delete operations.
- The same safety rules as Excel roundtrip import apply: all changes become a PatchProposal, not direct canonical writes.

---

## 3. Source metadata for Drive/Sheets references

Every Google Drive or Sheets interaction is recorded in the source registry with the following metadata:

### 3.1 Core fields

| Field | Type | Example | Description |
|---|---|---|---|
| `source_id` | `str` | `1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms` | Google file ID or Sheet ID |
| `source_type` | `str` | `google_drive_file` / `google_sheet` | Distinguishes Drive files from Sheets |
| `external_reference` | `str` | `https://drive.google.com/file/d/...` | Human-accessible URL |
| `mime_type` | `str` | `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` | MIME type from Drive metadata |
| `revision_id` | `str` | `1a2b3c...` | Google revision ID for change detection |
| `modified_at` | `str` | `2026-05-20T14:30:00Z` | Last modified time from Google metadata |
| `file_path` | `str \| None` | `data/samples/drive_import_20260520.xlsx` | Local cache path, if cached |
| `file_hash` | `str \| None` | `sha256:abc123...` | SHA-256 of downloaded content |
| `registered_at` | `str` | `2026-05-20T14:35:00Z` | When this entry was created |
| `status` | `str` | `registered` / `imported` / `stale` | Current status |

### 3.2 Sheets-specific fields

| Field | Type | Example | Description |
|---|---|---|---|
| `sheet_tab` | `str` | `Sheet1` | Tab name for Sheet operations |
| `cell_range` | `str` | `A1:Z1000` | Range used for import/export |
| `header_row` | `int` | `1` | Row number containing headers |

### 3.3 Linkage fields

| Field | Type | Description |
|---|---|---|
| `linked_dataset` | `str \| None` | Canonical Dataset object ID, if profiled |
| `linked_proposals` | `list[str]` | PatchProposal IDs generated from this source |
| `linked_export` | `str \| None` | Export operation ID, if this is an export target |

---

## 4. Access and configuration

### 4.1 Credential handling

Google Drive and Sheets integration requires OAuth 2.0 credentials. These are **never** stored in canonical model files or committed to Git.

**Supported config approaches:**

1. **Environment variables** (recommended for CI and local development):
   ```bash
   export GOOGLE_CLIENT_ID="..."
   export GOOGLE_CLIENT_SECRET="..."
   export GOOGLE_REFRESH_TOKEN="..."
   ```

2. **Local config file** (user-managed, Git-ignored):
   ```yaml
   # ~/.config/martenweave/google_credentials.yaml
   client_id: "..."
   client_secret: "..."
   refresh_token: "..."
   ```

3. **Service account JSON** (for server-to-server use):
   ```bash
   export GOOGLE_SERVICE_ACCOUNT_JSON_PATH="/secure/path/to/service-account.json"
   ```

### 4.2 Repository-level config

The repository-level `modelops.config.yaml` may reference integration settings by name, but never contains secrets:

```yaml
integrations:
  google_drive:
    enabled: true
    credentials_source: env  # env | file | service_account
    default_folder_id: "1a2b3c..."  # optional default Drive folder
  google_sheets:
    enabled: true
    credentials_source: env
    default_sheet_id: null
```

### 4.3 Scope requirements

| Flow | Required OAuth Scope |
|---|---|
| Read Drive files | `https://www.googleapis.com/auth/drive.readonly` |
| Write Drive files | `https://www.googleapis.com/auth/drive.file` |
| Read Sheets | `https://www.googleapis.com/auth/spreadsheets.readonly` |
| Write Sheets | `https://www.googleapis.com/auth/spreadsheets` |

---

## 5. Safety rules

### 5.1 Canonical truth

- Google Sheets **must not** be treated as the canonical model store.
- A Sheet may be the source of a PatchProposal, but the proposal must pass validation and human approval before canonical files change.
- The hidden `__metadata__` tab in exported Sheets must contain a clear warning: "This is a generated review view. Do not treat as canonical model truth."

### 5.2 Explicit actions

- All Drive/Sheet interactions are triggered by explicit CLI commands:
  ```bash
  modelops import-drive <file-id> --repo ./my-model
  martenweave export-sheets --repo ./my-model --sheet-id <id>
  modelops profile-sheet <sheet-id> --range A1:Z100
  ```
- No automatic background sync, polling, or two-way replication.

### 5.3 Change detection

- The source registry stores `revision_id` and `modified_at` from Google metadata.
- Re-importing the same source without changes should be a no-op or produce an identical PatchProposal.
- Stale detection is the responsibility of the source refresh service (#72).

### 5.4 Error handling

- Network errors, permission errors, and quota errors are normalized to `ConnectorError`.
- Missing or invalid credentials produce a clear setup message pointing to documentation.
- Partial failures (e.g., some tabs fail) are logged but do not corrupt the source registry.

---

## 6. Connector design

### 6.1 `GoogleDriveConnector`

Implements `ConnectorAdapter` for Google Drive.

**Responsibilities:**

- `list_sources(prefix)` — list files in a Drive folder.
- `fetch_metadata(file_id)` — get Drive file metadata (name, size, MIME type, revision).
- `fetch_content(file_id)` — download file content as bytes.
- `write_content(file_id, content)` — upload or update a Drive file.
- `to_source_entry(file_id)` — build a `SourceEntry` with Drive-specific metadata.

**Path safety:**

- Drive file IDs are opaque strings. No path traversal risk.
- Folder IDs are validated to be valid Drive identifiers.

### 6.2 `GoogleSheetsConnector`

Implements `ConnectorAdapter` for Google Sheets.

**Responsibilities:**

- `list_sources(prefix)` — list Sheets accessible to the user (or in a folder).
- `fetch_metadata(sheet_id)` — get Sheet metadata (title, locale, sheet count).
- `fetch_content(sheet_id)` — read cell values as structured data (CSV-like).
- `write_content(sheet_id, content)` — write cell values to a Sheet.
- `to_source_entry(sheet_id)` — build a `SourceEntry` with Sheets-specific metadata.

**Content format:**

- `fetch_content` returns tabular data as a list of lists (rows of cells).
- `write_content` accepts tabular data and writes it to the specified range.

### 6.3 Optional dependency

Google Drive/Sheets integration is **optional**. The core package does not depend on `google-api-python-client` or `gspread`.

**Installation:**
```bash
pip install modelops_core[google]
# or
pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

**Runtime check:**
```python
try:
    from googleapiclient.discovery import build
except ImportError:
    raise ConnectorError(
        "Google integration requires 'google-api-python-client'. "
        "Install with: pip install modelops_core[google]",
        connector_type="google",
        action="import",
    )
```

---

## 7. Testing strategy

All Google Drive/Sheets integration tests **must** mock external API calls. No live network requests during the test suite.

**Test coverage:**

| Test | Approach |
|---|---|
| `GoogleDriveConnector.list_sources` | Mock `googleapiclient.discovery.build` |
| `GoogleDriveConnector.fetch_content` | Mock `drive.files().get_media()` |
| `GoogleDriveConnector.write_content` | Mock `drive.files().create()` and `.update()` |
| `GoogleSheetsConnector.fetch_content` | Mock `sheets.spreadsheets().values().get()` |
| `GoogleSheetsConnector.write_content` | Mock `sheets.spreadsheets().values().update()` |
| Source registry entry | Verify `to_source_entry()` produces correct `SourceEntry` |
| Missing credentials | Verify clear error message without real auth flow |
| Optional dependency | Test import guard when `googleapiclient` is missing |

---

## 8. Related issues

| Issue | Description | Status |
|---|---|---|
| #46 | Integration architecture (parent document) | Completed |
| #50 | Google Sheets export adapter | Implementation |
| #51 | GitHub publishing workflow | Design doc |
| #56 | Google Drive import adapter | Implementation |
| #57 | Google Sheets import adapter as PatchProposal source | Implementation |
| #58 | Controlled GitHub write integration | Implementation |
| #72 | Source refresh and stale detection | Design + code |

---

## 9. Validation

```bash
pytest && ruff check .
```
