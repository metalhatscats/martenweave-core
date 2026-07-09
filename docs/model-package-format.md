<!-- modelops-freshness-ignore: all -->

# Martenweave — Portable Model Package Format

Version: `0.1-draft`  
Document type: Architecture / packaging specification  
Scope: How to create, inspect, and share a self-contained Martenweave model package  
Depends on: `docs/integration-architecture.md`, `docs/github-publishing-workflow.md`  
Status: Draft for implementation

---

## 1. Purpose

This document defines the **portable model package format** for Martenweave. A model package is a self-contained archive that can be shared with clients, agents, or other tools without requiring a live repository checkout or access to the original Git repository.

Packages are **generated artifacts**, not canonical model storage. They are built from canonical files on demand and are disposable — any package can be rebuilt from the canonical model repository.

---

## 2. Design principles

### 2.1 Safe by default

- Raw datasets, secrets, and local credentials are excluded unless explicitly requested.
- Generated provider traces, temporary files, and IDE artifacts are always excluded.
- The package includes integrity metadata (checksums) so recipients can verify contents.

### 2.2 Inspectable without importing

- A package contains a top-level `manifest.json` with metadata, object counts, and validation summary.
- Recipients can list contents and read the manifest without unpacking the full archive.

### 2.3 Canonical files are still the source of truth

- The package is a snapshot, not a replacement for version control.
- Changes to a package do not flow back to the original repository automatically.
- Re-importing a package produces a PatchProposal, not direct canonical mutation.

---

## 3. Package structure

```text
my-model-package-0.1.0.zip
├── manifest.json              # Package metadata and integrity
├── model/                     # Canonical model files (source of truth)
│   ├── DOMAIN-*.md
│   ├── ATTR-*.md
│   ├── FEP-*.md
│   └── ...
├── config/
│   └── modelops.config.yaml   # Repository configuration (non-sensitive)
├── docs/                      # Product and architecture documentation
│   ├── README.md
│   └── ...
├── generated/                 # Generated index and exports (optional)
│   ├── modelops.db            # SQLite index snapshot
│   ├── search_documents.jsonl
│   ├── lineage_edges.jsonl
│   └── validation_report.json
├── exports/                   # Optional tabular exports
│   ├── model.xlsx
│   └── model.csv/
├── scorecard/                 # Optional scorecard and health reports
│   └── scorecard.json
└── .martenweave-package-ignore  # Package-specific exclusions (like .gitignore)
```

### 3.1 `manifest.json`

```json
{
  "package_format_version": "1.0",
  "created_at": "2026-05-25T14:30:00Z",
  "created_by": "modelops package create",
  "repository_name": "customer-bp-model",
  "package_version": "0.1.0",
  "git_commit": "abc123def456",
  "git_branch": "main",
  "canonical_object_counts": {
    "MasterDataDomain": 1,
    "BusinessEntity": 4,
    "Attribute": 23,
    "FieldEndpoint": 45,
    "Mapping": 12
  },
  "validation_summary": {
    "error_count": 0,
    "warning_count": 2,
    "info_count": 0,
    "is_valid": true
  },
  "includes": {
    "generated": true,
    "exports": false,
    "scorecard": true,
    "docs": true
  },
  "excluded_by_default": [
    "data/samples/",
    ".env",
    "generated/source_registry.jsonl",
    "generated/git_bundles/",
    "*.pyc",
    "__pycache__/"
  ],
  "checksums": {
    "manifest.json": "sha256:...",
    "model/DOMAIN-CUSTOMER-BP.md": "sha256:...",
    "generated/modelops.db": "sha256:..."
  }
}
```

### 3.2 Required contents

| Path | Required | Description |
|---|---|---|
| `manifest.json` | Yes | Package metadata, version, checksums |
| `model/` | Yes | Canonical model files (at least one object) |
| `config/modelops.config.yaml` | Yes | Repository configuration |
| `docs/README.md` | No | Human-readable package description |
| `generated/` | No | SQLite index, JSONL exports, validation report |
| `exports/` | No | XLSX/CSV tabular exports |
| `scorecard/` | No | Scorecard and health reports |

### 3.3 Default exclusions

The following are **excluded by default** and cannot be overridden:

- `.env`, `*.env` — environment variables and secrets
- `service-account.json`, `*_credentials.json` — credential files
- `data/samples/` — raw datasets (unless explicitly included with `--include-datasets`)
- `.git/` — Git internals
- `__pycache__/`, `*.pyc`, `.pytest_cache/` — Python cache
- `.venv/`, `venv/` — virtual environments
- `generated/source_registry.jsonl` — source registry (rebuildable)
- `generated/git_bundles/` — git bundles (rebuildable)
- `.idea/`, `.vscode/` — IDE files
- `.DS_Store` — macOS metadata

---

## 4. CLI design (future)

### 4.1 Create a package

```bash
modelops package create --repo ./my-model --output ./my-model-0.1.0.zip
```

**Options:**

| Flag | Description |
|---|---|
| `--include-generated` | Include `generated/` (default: yes) |
| `--include-exports` | Include `exports/` (default: no) |
| `--include-scorecard` | Include `scorecard/` (default: yes) |
| `--include-docs` | Include `docs/` (default: yes) |
| `--include-datasets` | Include `data/samples/` (default: no) |
| `--version <ver>` | Override package version in manifest |

**Behavior:**

1. Run `martenweave validate` and `martenweave build-index --jsonl`.
2. Collect validation report and object counts.
3. Build `manifest.json` with checksums.
4. Create zip archive with selected contents.
5. Write archive path to stdout.

### 4.2 Inspect a package

```bash
modelops package inspect ./my-model-0.1.0.zip
```

**Output:**

```text
Package: customer-bp-model v0.1.0
Created: 2026-05-25T14:30:00Z
Git: abc123def456 on main
Objects: 85 total (1 Domain, 4 Entities, 23 Attributes, 45 Fields, 12 Mappings)
Validation: 0 errors, 2 warnings
Includes: generated, scorecard, docs
```

**With `--json`:**

```bash
modelops package inspect ./my-model-0.1.0.zip --json
```

Returns the full `manifest.json` content.

### 4.3 Extract a package

```bash
modelops package extract ./my-model-0.1.0.zip --output ./unpacked
```

Extracts the archive to a directory. The unpacked directory is a valid Martenweave repository.

### 4.4 Import a package as PatchProposal (future)

```bash
modelops package import ./my-model-0.1.0.zip --repo ./target-model
```

Diffs the package contents against the target repository and generates a PatchProposal.

---

## 5. Integrity and security

### 5.1 Checksums

- Every file in the package is checksummed with SHA-256.
- The `manifest.json` itself is checksummed and the checksum is stored in the manifest.
- Recipients can verify integrity by recomputing checksums.

### 5.2 Signature (future)

- Packages may be signed with GPG or Sigstore for provenance.
- Signature file: `manifest.json.sig`.
- Verification: `modelops package verify ./my-model-0.1.0.zip`.

### 5.3 Size limits

- Default maximum package size: 100 MB.
- Packages with datasets may exceed this; warn and require `--allow-large`.

---

## 6. Use cases

| Use case | Command | Includes |
|---|---|---|
| Handoff to client | `package create` | model, generated, docs, scorecard |
| Agent review | `package create --include-exports` | + exports |
| Backup snapshot | `package create --include-generated` | + generated |
| CI artifact | `package create --version $CI_COMMIT_TAG` | model, generated |
| Offline review | `package create --include-exports --include-datasets` | + datasets |

---

## 7. Related issues

| Issue | Description | Status |
|---|---|---|
| #46 | Integration architecture | Completed |
| #51 | GitHub publishing workflow | Completed |
| #71 | This document | Design doc |
| #72 | Source refresh and stale detection | Design doc |
| #74 | Bulk refactor operations | Design doc |

---

## 8. Validation

```bash
pytest && ruff check .
```
