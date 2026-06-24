# Martenweave — Source Refresh and Stale Model Detection

Version: `0.1-draft`  
Document type: Architecture / detection design  
Scope: How to detect when external sources have changed since they were last profiled or imported  
Depends on: `docs/integration-architecture.md`  
Status: Draft for implementation

---

## 1. Purpose

This document defines the **source refresh and stale model detection** design for Martenweave. It describes how the system detects when external sources — local files, Google Drive files, Google Sheets, and future connectors — have changed since they were last profiled or imported, so users can refresh model knowledge intentionally and safely.

Stale detection is **advisory**, not automatic. The system warns users about stale sources; it does not mutate canonical files or generate PatchProposals without explicit user action.

---

## 2. Design principles

### 2.1 Explicit refresh only

- Users must run a command to check for stale sources: `modelops sources refresh-check`.
- No background polling, no automatic re-import, no silent model updates.
- Detected changes produce a report, not a PatchProposal directly.

### 2.2 Source registry is the checkpoint

- The source registry (`generated/source_registry.jsonl`) stores the last known state of each source.
- Freshness comparison uses stored checksums, revision IDs, or modification timestamps.
- If a source is not in the registry, it cannot be checked for staleness.

### 2.3 Proposal-first for all changes

- If a user decides to refresh a stale source, the system generates a new profile or PatchProposal.
- The new proposal goes through the standard validation and approval workflow.
- Canonical files change only after human approval.

---

## 3. Freshness metadata

### 3.1 Stored in source registry

Each `SourceEntry` carries freshness metadata:

| Field | Type | Description |
|---|---|---|
| `source_id` | `str` | Stable identifier |
| `source_type` | `str` | `dataset_profile`, `model_sheet_import`, `google_drive_file`, etc. |
| `file_hash` | `str \| None` | SHA-256 checksum (local files, downloaded Drive files) |
| `revision_id` | `str \| None` | Provider revision marker (Drive, Sheets, GitHub) |
| `modified_at` | `str \| None` | Last modified timestamp from provider |
| `registered_at` | `str` | When this entry was created |
| `last_seen_at` | `str \| None` | When this source was last successfully read |

### 3.2 Connector-specific markers

| Connector | Freshness marker | How to compare |
|---|---|---|
| `LocalFileConnector` | `file_hash` (SHA-256) | Recompute hash, compare |
| `GoogleDriveConnector` | `revision_id` | Fetch Drive metadata, compare revision |
| `GoogleSheetsConnector` | `modified_at` | Fetch Sheets metadata, compare timestamp |
| Future: `GitHubConnector` | `commit_sha` | Fetch latest commit for file path |
| Future: `DatabaseConnector` | `row_count` + `max_modified_at` | Query metadata table |

---

## 4. Stale detection flow

```text
modelops sources refresh-check --repo ./my-model
      │
      ▼
Read source_registry.jsonl
      │
      ▼
For each registered source:
  - Instantiate the appropriate ConnectorAdapter
  - Fetch current metadata
  - Compare current marker against stored marker
      │
      ├──► MATCH → mark "fresh"
      │
      └──► MISMATCH → mark "stale", collect diff info
      │
      ▼
Output stale source report
```

### 4.1 Stale source report

```json
{
  "checked_at": "2026-05-25T14:30:00Z",
  "sources_checked": 5,
  "fresh_count": 3,
  "stale_count": 2,
  "stale_sources": [
    {
      "source_id": "sales_data_2026.csv",
      "source_type": "dataset_profile",
      "status": "stale",
      "stored_hash": "abc123...",
      "current_hash": "def456...",
      "last_seen_at": "2026-05-20T10:00:00Z",
      "suggested_action": "Re-run modelops profile-dataset"
    },
    {
      "source_id": "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms",
      "source_type": "google_sheet",
      "status": "stale",
      "stored_modified_at": "2026-05-20T10:00:00Z",
      "current_modified_at": "2026-05-24T08:30:00Z",
      "suggested_action": "Re-run modelops import-drive or import-sheet"
    }
  ]
}
```

### 4.2 CLI output (human-readable)

```text
$ modelops sources refresh-check --repo ./my-model

Checked 5 sources
  Fresh:  3
  Stale:  2

Stale sources:
  sales_data_2026.csv
    Type: dataset_profile
    Changed: hash mismatch (stored: abc123..., current: def456...)
    Last seen: 2026-05-20
    Action: modelops profile-dataset data/samples/sales_data_2026.csv

  1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms
    Type: google_sheet
    Changed: modified_at moved from 2026-05-20 to 2026-05-24
    Last seen: 2026-05-20
    Action: modelops import-sheet <sheet-id>
```

---

## 5. Impact on model objects

### 5.1 Linking sources to model objects

When a source is imported as a PatchProposal, the proposal's `affected_objects` field links the source to canonical objects. When a source goes stale, the system can report which model objects may be affected:

```json
{
  "stale_source_id": "sales_data_2026.csv",
  "linked_objects": [
    "ATTR-CUST-SALES-CUSTOMER-GROUP",
    "FEP-S4-KNVV-KDGRP",
    "MAP-CUST-GROUP-S4"
  ],
  "suggested_review": "Verify attribute definitions and mappings still match the updated dataset"
}
```

### 5.2 Health report integration (future)

Stale sources can be surfaced in the health report:

```text
$ martenweave health --repo ./my-model

Stale source warnings:
  - sales_data_2026.csv has changed since last profile (5 days ago)
  - Google Sheet 1Bxi... has been modified since last import (1 day ago)
```

---

## 6. Refresh workflow

### 6.1 Check only

```bash
modelops sources refresh-check --repo ./my-model
```

Produces a report. No changes to model files or registry.

### 6.2 Refresh a single source

```bash
modelops sources refresh <source-id> --repo ./my-model
```

**Behavior:**

1. Re-fetch the source content.
2. Generate a new DatasetProfile or PatchProposal.
3. Register a new `SourceEntry` with updated markers.
4. Run validation on the resulting proposal.
5. Present the proposal for human review.

### 6.3 Refresh all stale sources

```bash
modelops sources refresh-all --repo ./my-model
```

**Behavior:**

1. Run `refresh-check` internally.
2. For each stale source, generate a new profile or proposal.
3. Bundle proposals into a single reviewable package.
4. Present the bundle for human review.

---

## 7. Implementation notes

### 7.1 Connector responsibility

Each `ConnectorAdapter` implementation must provide a way to fetch the current freshness marker:

```python
class ConnectorAdapter(Protocol):
    # ... existing methods ...

    def fetch_freshness_marker(self, source_id: str) -> dict[str, Any]:
        """Return a dict with current freshness markers.

        Must include at least one of: file_hash, revision_id, modified_at.
        """
        ...
```

Default implementation: return `modified_at` from `fetch_metadata()`.

### 7.2 Registry comparison logic

```python
def is_stale(stored: SourceEntry, current: dict[str, Any]) -> bool:
    if stored.file_hash and current.get("file_hash"):
        return stored.file_hash != current["file_hash"]
    if stored.revision_id and current.get("revision_id"):
        return stored.revision_id != current["revision_id"]
    if stored.modified_at and current.get("modified_at"):
        return stored.modified_at != current["modified_at"]
    return False  # Cannot determine freshness
```

### 7.3 No connector available

If a source was registered by a connector that is no longer configured (e.g., Google Drive credentials removed), the system reports:

```text
  sales_data_2026.csv
    Status: unknown (cannot check: Google Drive connector not configured)
```

---

## 8. Related issues

| Issue | Description | Status |
|---|---|---|
| #46 | Integration architecture | Completed |
| #49 | Google Drive/Sheets boundary | Completed |
| #54 | Source registry | Completed |
| #55 | Connector adapter interface | Completed |
| #56 | Google Drive import adapter | Implementation |
| #57 | Google Sheets import adapter | Implementation |
| #72 | This document | Design doc |
| #74 | Bulk refactor operations | Design doc |

---

## 9. Validation

```bash
pytest && ruff check .
```
