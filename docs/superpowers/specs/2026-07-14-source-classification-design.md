# Source-State Classification Design

## Context

Issue #517 asks Martenweave to make the boundary between imported evidence,
generated findings, proposed changes, and approved canonical truth explicit
across the product. This protects the core principle that canonical model files
are the source of truth and that AI/imports only create proposals.

## Goals

1. Define four explicit product states: `evidence`, `finding`, `proposal`, and
   `canonical`.
2. Expose the state on API resources and generated artifacts so consumers
   (frontend, reports, CLI) can render it without guessing.
3. Keep the smallest backend-first slice: classification utilities, API
   response enrichment, and tests that assert write boundaries.
4. Do not silently mutate canonical files from evidence or findings.

## Non-goals

- Full UI redesign is out of scope for this slice; frontend PRs for related
  screens are already in flight.
- Adding a new canonical object type is unnecessary; existing `Evidence` and
  `PatchProposal` objects already exist, they just need explicit state labels.
- Rewriting import/gap/assessment logic is not required; we add metadata and
  boundary checks, not new workflows.

## Design

### SourceState enum

Introduce a deterministic enum in `src/modelops_core/schemas/common.py`:

```python
class SourceState(StrEnum):
    EVIDENCE = "evidence"       # Raw imported inputs (datasets, workbooks)
    FINDING = "finding"         # Generated analysis (gaps, readiness reports,
                                # assessment artifacts, validation results)
    PROPOSAL = "proposal"       # Human-reviewable PatchProposals and ChangeRequests
    CANONICAL = "canonical"     # Approved objects in model/ files
```

### Classification utilities

Add `src/modelops_core/source_state.py` with:

- `classify_object_type(object_type: str) -> SourceState` — maps canonical
  object types to states. `PatchProposal` and `ChangeRequest` are proposals,
  `Evidence` is evidence, everything else in `model/` is canonical.
- `classify_file_path(path: Path) -> SourceState` — uses the containing
  subfolder to classify files in `patch-proposals/` as proposal,
  `evidence/` as evidence, and everything else under `model/` as canonical.
- `classify_artifact(artifact_path: Path | str) -> SourceState` — classifies
  generated artifacts by path/filename patterns:
  - `source_registry.jsonl`, dataset profiles, import sessions → evidence
  - `readiness.json`, gap reports, assessment packages, high-risk fields,
    impact reports → finding
  - `patch-proposals/*.md`, change-requests → proposal
  - `modelops.db`, `search_documents.jsonl`, `lineage_edges.jsonl`, canonical
    exports → canonical
- `classify_dataset_gap(gap_code: str) -> SourceState` — always `finding`.

### API enrichment

Extend `src/modelops_core/api/app.py` response payloads:

- `GET /objects` and `GET /objects/{id}`: add `source_state: "canonical"`.
- `GET /proposals` and `GET /proposals/{id}`: add `source_state: "proposal"`.
- `GET /validate`: add `source_state: "finding"` to each result.
- `POST /gaps` and `POST /dataset-readiness`: add `source_state: "finding"`
  to `dataset_gaps` and `model_gaps`; add `source_state: "evidence"` to the
  `dataset_profile`; add `source_state: "proposal"` when
  `promoted_proposal_path` is present.
- `POST /export`: add `source_state: "canonical"` to exported files.

These are additive fields; no existing field is removed or renamed.

### Write-boundary tests

Add `tests/test_source_classification.py` covering:

- Canonical objects returned by the API are classified as `canonical`.
- PatchProposals are classified as `proposal`.
- Dataset gaps and model gaps are classified as `finding`.
- Dataset profiles are classified as `evidence`.
- Importing a model sheet returns a proposal, never a canonical object.
- Gap promotion creates a proposal, not a canonical object.
- Applying an accepted proposal is the only tested path that writes canonical
  files.

### Documentation

Update `docs/architecture/AI_PATCH_WORKFLOW.md` to include the four states and
allowed transitions. Add a short section to `docs/developer/CODE_STYLE.md`
describing when to use `SourceState`.

## Allowed transitions

- `evidence` → `finding` (profiling/gap analysis reads evidence)
- `evidence` → `proposal` (import/gap promotion creates a proposal)
- `finding` → `proposal` (reviewing a finding may produce a proposal)
- `proposal` → `canonical` (only after human review and `apply`)
- `canonical` is terminal; canonical files are only modified by a proposal
  apply operation.

## Risks and mitigations

- Risk: Frontend or CLI consumers may not expect the new field.
  Mitigation: Additive-only API changes; consumers that ignore the field
  continue to work.
- Risk: Classifying by file path is fragile if folder conventions change.
  Mitigation: Use the object type registry as the primary signal and path as
  a fallback; add tests for each classification path.
- Risk: Confusion with existing `source_type` and `source_evidence` fields.
  Mitigation: Name the new concept `source_state`; leave existing fields
  untouched and document the distinction.

## Validation

```bash
.venv/bin/python -m pytest tests/test_source_classification.py tests/test_api.py -q
.venv/bin/python -m pytest tests/ -k "evidence or finding or proposal or canonical or mutation_safety" -q
.venv/bin/python -m ruff check .
```
