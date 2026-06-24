# Martenweave — GitHub Publishing Workflow

Version: `0.1-draft`  
Document type: Workflow / integration boundary  
Scope: How Martenweave publishes, reviews, and versions model repositories on GitHub  
Depends on: `docs/integration-architecture.md`  
Status: Draft for implementation

---

## 1. Purpose

This document defines the **GitHub publishing workflow** for Martenweave. It describes how model repositories use Git and GitHub as a **versioning, review, and publishing layer** while preserving the principle that canonical model files are the source of truth.

GitHub is not a runtime database, not a model store, and not a replacement for the local `martenweave build-index` workflow. It is a collaboration layer where teams review model changes through Pull Requests, track issues, and publish generated documentation.

---

## 2. Design principles

### 2.1 GitHub is a versioning and review layer

```text
┌─────────────────────────────────────────────────────────────────────────┐
│                            GitHub                                        │
│                                                                          │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────────────┐ │
│  │ Repository  │    │ Issues      │    │ Pull Requests               │ │
│  │ (canonical  │    │ (gaps,      │    │ (model change review)       │ │
│  │  model,     │    │  decisions, │    │                             │ │
│  │  docs)      │    │  change     │    │                             │ │
│  │             │    │  requests)  │    │                             │ │
│  └─────────────┘    └─────────────┘    └─────────────────────────────┘ │
│  ┌─────────────┐    ┌─────────────┐                                    │
│  │ GitHub      │    │ GitHub      │                                    │
│  │ Pages       │    │ Releases    │                                    │
│  │ (docs site) │    │ (packages)  │                                    │
│  └─────────────┘    └─────────────┘                                    │
└─────────────────────────────────────────────────────────────────────────┘
                                    ▲
                                    │ push, PR, issue
                                    │
┌─────────────────────────────────────────────────────────────────────────┐
│                         Martenweave Repository (local)                  │
│                                                                          │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────────────────────┐   │
│  │  model/ │  │generated│  │  docs/  │  │  modelops.config.yaml   │   │
│  │(source │  │(dispos- │  │(product │  │  (repo config)           │   │
│  │ of truth│  │ able)   │  │  docs)  │  │                         │   │
│  └─────────┘  └─────────┘  └─────────┘  └─────────────────────────┘   │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  martenweave validate && martenweave build-index && martenweave health   │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Model changes are proposal-first

Every change to canonical model files must be preceded by a PatchProposal or ChangeRequest:

```text
Model gap or note
      │
      ▼
PatchProposal  ──►  validation  ──►  human review  ──►  ChangeRequest
      │                                                    │
      │                                                    ▼
      │                                            Canonical file update
      │                                                    │
      │                                                    ▼
      └────────────────────────────────────────────  git commit + PR
```

### 2.3 Generated artifacts are disposable

- `generated/modelops.db`, `generated/*.jsonl`, and `generated/git_bundles/` are rebuilt from canonical files.
- They are excluded from Git by default via `.gitignore`.
- They may be attached to GitHub Releases as binary artifacts, but never committed to the main branch.

### 2.4 Secrets and credentials are never committed

- `.env`, OAuth tokens, API keys, and service account files are excluded from Git.
- Repository-level config (`modelops.config.yaml`) contains only non-sensitive settings.

---

## 3. Supported flows

### 3.1 Initialize a model repo locally

```bash
martenweave init ./my-model
```

**What happens:**

- Creates the standard directory structure (`model/`, `generated/`, `data/samples/`, `docs/`).
- Generates `modelops.config.yaml` with repository defaults.
- User initializes Git: `git init && git add . && git commit -m "Initial model repo"`.

**What belongs in the first commit:**

- `modelops.config.yaml`
- `model/` (with initial domain pack or empty `.gitkeep`)
- `docs/` (with project-specific documentation)
- `data/samples/` (with `.gitignore` for large files)
- `generated/` (with `.gitignore` excluding all contents)
- `.gitignore` (excluding `.env`, `generated/`, `*.db`, large datasets)

### 3.2 Validate and build generated index locally

```bash
martenweave validate --repo ./my-model
martenweave build-index --repo ./my-model --jsonl
```

**What happens:**

- Deterministic validation runs on canonical files.
- SQLite index and JSONL exports are generated in `generated/`.
- These artifacts are not committed to Git.

**CI equivalent:**

```bash
pytest && ruff check .
martenweave validate --repo ./my-model
martenweave build-index --repo ./my-model --jsonl
```

### 3.3 Create a GitHub-ready commit summary

```bash
modelops git-bundle <proposal-id> --repo ./my-model
```

**What happens:**

- Generates a reviewable bundle in `generated/git_bundles/<proposal-id>/`.
- Bundle contains:
  - `README.md` — human-readable summary
  - `PR_BODY.md` — suggested pull request description
  - `COMMIT_MESSAGE.txt` — suggested commit message
  - `bundle.json` — machine-readable metadata
  - `changed_files/` — copies of affected canonical files

**User action:**

```bash
cd ./my-model
git checkout -b model-change-<proposal-id>
# apply approved changes from ChangeRequest
git add model/
git commit -F generated/git_bundles/<proposal-id>/COMMIT_MESSAGE.txt
git push origin model-change-<proposal-id>
# open PR using PR_BODY.md as description
```

### 3.4 Create issue drafts from model gaps or change requests

**Current flow:**

```bash
modelops issue-draft create --from-validation --repo ./my-model
modelops publish-issue generated/issues/<draft-file>.md \
  --repo ./my-model \
  --github-repo metalhatscats/martenweave-core \
  --dry-run
```

**What happens:**

- Generates an issue draft from a model gap, decision, or change request.
- Title and body are pre-filled with model context.
- User reviews and submits via GitHub CLI or web interface.

**Fields in issue body:**

- Affected object IDs
- Validation results
- Impact summary
- Suggested labels: `model-change`, `gap`, `decision`

### 3.5 Publish docs or generated model reports to GitHub Pages

**Future flow:**

```bash
modelops publish-docs --repo ./my-model --target github-pages
```

**What happens:**

- Generates a static documentation site from `docs/` and generated reports.
- Publishes to a separate site repository or `gh-pages` branch.
- The site repo is distinct from the canonical model repository to keep generated artifacts separate.

**Site repository structure:**

```
my-model-docs/
  index.html
  model-reference/
  health-reports/
  lineage-graphs/
  .nojekyll
```

---

## 4. What belongs in Git

### 4.1 Commit to Git

| Category | Examples | Reason |
|---|---|---|
| Canonical model files | `model/DOMAIN-*.md`, `model/ATTR-*.md` | Source of truth |
| Repository config | `modelops.config.yaml` | Shared settings |
| Documentation | `docs/*.md`, `README.md` | Human-readable context |
| Examples | `examples/*/model/` | Reference implementations |
| Config templates | `templates/model_spines/*.yaml` | Reusable scaffolding |
| Tests | `tests/` | Quality assurance |
| Build config | `pyproject.toml`, `.gitignore` | Project setup |

### 4.2 Do not commit

| Category | Examples | Reason |
|---|---|---|
| Generated artifacts | `generated/modelops.db`, `generated/*.jsonl` | Disposable, rebuildable |
| Raw datasets | `data/samples/*.csv`, large Excel files | Size, privacy |
| Secrets | `.env`, `service-account.json`, tokens | Security |
| Local credentials | `~/.config/martenweave/` | User-specific |
| Large exports | `generated/git_bundles/`, `*.zip` | Size, generated |
| IDE files | `.idea/`, `.vscode/` | User-specific |
| Python cache | `__pycache__/`, `.pytest_cache/` | Generated |

### 4.3 Recommended `.gitignore`

```gitignore
# Environment
.env
*.env

# Generated artifacts
generated/
*.db
*.jsonl

# Raw datasets (keep samples small or external)
data/samples/*.csv
data/samples/*.xlsx
!data/samples/.gitkeep

# Secrets
service-account.json
*_credentials.json

# IDE
.idea/
.vscode/

# Python
__pycache__/
*.pyc
.pytest_cache/
.ruff_cache/
.venv/
```

---

## 5. Pull request workflow for model governance

### 5.1 Branch naming

```
model-change-<proposal-id>
gap-fix-<issue-number>
domain-pack-<name>
docs-update-<description>
```

### 5.2 PR checklist

Every model change PR should include:

- [ ] `martenweave validate` passes with zero errors.
- [ ] `martenweave build-index --jsonl` succeeds.
- [ ] `pytest` passes.
- [ ] Affected object IDs are listed in the PR description.
- [ ] Impact analysis is included for changes affecting >5 objects.
- [ ] ChangeRequest ID is referenced, if applicable.

### 5.3 PR template

```markdown
## Model Change

- Proposal ID: <!-- e.g., PROP-20260525-001 -->
- ChangeRequest ID: <!-- e.g., CR-20260525-001 -->

### Affected Objects

<!-- List object IDs -->

### Validation

<!-- Paste `martenweave validate` summary -->

### Impact

<!-- Paste `martenweave impact` output for key objects -->

### Checklist

- [ ] `martenweave validate` passes
- [ ] `martenweave build-index --jsonl` succeeds
- [ ] `pytest` passes
```

### 5.4 Review requirements

| Change size | Reviewers | Requirements |
|---|---|---|
| 1–2 objects | 1 reviewer | Validation pass |
| 3–10 objects | 2 reviewers | Validation + impact analysis |
| 10+ objects | 2+ reviewers + approval gate | Validation + impact + audit log review |
| Domain pack addition | Team lead + domain expert | Full validation + documentation update |

---

## 6. GitHub Actions CI (future)

When the repository includes `.github/workflows/ci.yml`, the following checks run on every PR:

```yaml
name: CI
on: [push, pull_request]
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -e .
      - run: pytest
      - run: ruff check .
      - run: martenweave validate --repo .
      - run: martenweave build-index --repo . --jsonl
```

**Note:** Issue #42 tracks adding this workflow. It is currently blocked by PAT scope limitations in the project's automation account.

---

## 7. Release packaging

### 7.1 Versioned releases

Model repositories may be versioned using Git tags:

```bash
git tag -a v0.1.0 -m "Customer BP model v0.1.0"
git push origin v0.1.0
```

### 7.2 Release artifacts

GitHub Releases may attach:

- `model-export-<version>.xlsx` — Excel roundtrip workbook
- `model-index-<version>.db` — SQLite index snapshot
- `lineage-edges-<version>.jsonl` — Lineage edge export
- `search-documents-<version>.jsonl` — Search document export

These are **generated artifacts** attached for convenience, not committed to the repository.

### 7.3 Portable model packages (future #71)

A portable model package is a zip or tar archive containing:

```
my-model-package/
  model/              # Canonical files
  modelops.config.yaml
  docs/
  generated/          # Optional: included for offline use
  manifest.json       # Package metadata
```

This is distinct from the Git repository and is built via a CLI command.

---

## 8. Security defaults

| Concern | Default |
|---|---|
| Secrets in Git | Blocked by `.gitignore` |
| Generated artifacts in Git | Blocked by `.gitignore` |
| Large files in Git | Blocked; use GitHub Releases or external storage |
| Force pushes to main | Discouraged; use branch protection |
| Direct canonical writes | Require PatchProposal + approval |
| CI access to secrets | Use GitHub Secrets, not hardcoded values |

---

## 9. Related issues

| Issue | Description | Status |
|---|---|---|
| #46 | Integration architecture (parent document) | Completed |
| #52 | GitHub-ready change bundles | Completed |
| #58 | Controlled GitHub write integration | Implementation |
| #71 | Portable model package archive | Design + code |
| #42 | CI workflow for tests, lint, and validation | Blocked (PAT scope) |

---

## 10. Validation

```bash
pytest && ruff check .
```
