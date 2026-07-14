# Source-State Classification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan inline. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add explicit `evidence` / `finding` / `proposal` / `canonical` source-state classification to backend schemas, API responses, and tests for issue #517.

**Architecture:** Add a `SourceState` enum and small classification module; enrich FastAPI response payloads without removing fields; add focused tests that assert write boundaries.

**Tech Stack:** Python 3.11, Pydantic 2, FastAPI, pytest, ruff.

## Global Constraints

- Canonical model files in `model/` remain the source of truth.
- AI and imports create proposals; they never silently mutate canonical files.
- All API changes are additive.
- Line length 100; target Python 3.11.
- Tests must assert classification and mutation-safety boundaries.

---

### Task 1: Add SourceState enum to shared schemas

**Files:**
- Modify: `src/modelops_core/schemas/common.py`
- Test: `tests/test_source_classification.py`

**Interfaces:**
- Consumes: nothing new.
- Produces: `SourceState` enum with `EVIDENCE`, `FINDING`, `PROPOSAL`, `CANONICAL`.

- [ ] **Step 1: Write the failing test**

```python
from modelops_core.schemas.common import SourceState


def test_source_state_values() -> None:
    assert SourceState.EVIDENCE == "evidence"
    assert SourceState.FINDING == "finding"
    assert SourceState.PROPOSAL == "proposal"
    assert SourceState.CANONICAL == "canonical"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_source_classification.py::test_source_state_values -v`
Expected: FAIL with `ImportError: cannot import name 'SourceState'`

- [ ] **Step 3: Add the enum**

Add to `src/modelops_core/schemas/common.py` after `ChangeRequestStatus`:

```python
class SourceState(StrEnum):
    """Product-wide source-of-truth classification."""

    EVIDENCE = "evidence"
    FINDING = "finding"
    PROPOSAL = "proposal"
    CANONICAL = "canonical"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_source_classification.py::test_source_state_values -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/modelops_core/schemas/common.py tests/test_source_classification.py
git commit -m "feat(#517): add SourceState enum"
```

---

### Task 2: Add classification utilities

**Files:**
- Create: `src/modelops_core/source_state.py`
- Modify: `src/modelops_core/schemas/__init__.py` (export `SourceState`)
- Test: `tests/test_source_classification.py`

**Interfaces:**
- Consumes: `SourceState`, `ObjectType` registry.
- Produces:
  - `classify_object_type(object_type: str) -> SourceState`
  - `classify_file_path(path: Path) -> SourceState`
  - `classify_artifact(artifact_path: Path | str) -> SourceState`
  - `classify_dataset_gap(gap_code: str) -> SourceState`

- [ ] **Step 1: Write the failing tests**

```python
from pathlib import Path

from modelops_core.source_state import (
    classify_artifact,
    classify_dataset_gap,
    classify_file_path,
    classify_object_type,
)


def test_classify_object_type() -> None:
    assert classify_object_type("PatchProposal") == "proposal"
    assert classify_object_type("ChangeRequest") == "proposal"
    assert classify_object_type("Evidence") == "evidence"
    assert classify_object_type("Attribute") == "canonical"
    assert classify_object_type("FieldEndpoint") == "canonical"


def test_classify_file_path() -> None:
    assert classify_file_path(Path("model/patch-proposals/PP-0001.md")) == "proposal"
    assert classify_file_path(Path("model/evidence/EV-0001.md")) == "evidence"
    assert classify_file_path(Path("model/attributes/ATTR-0001.md")) == "canonical"


def test_classify_artifact() -> None:
    assert classify_artifact("generated/source_registry.jsonl") == "evidence"
    assert classify_artifact("generated/readiness.json") == "finding"
    assert classify_artifact("generated/assessment/scorecard.md") == "finding"
    assert classify_artifact("model/patch-proposals/PP-0001.md") == "proposal"
    assert classify_artifact("generated/modelops.db") == "canonical"


def test_classify_dataset_gap() -> None:
    assert classify_dataset_gap("UNMODELED_DATASET_COLUMN") == "finding"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/test_source_classification.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'modelops_core.source_state'`

- [ ] **Step 3: Implement the classification module**

Create `src/modelops_core/source_state.py`:

```python
"""Deterministic source-state classification utilities."""

from __future__ import annotations

from pathlib import Path

from modelops_core.schemas.common import SourceState


def classify_object_type(object_type: str | None) -> str:
    """Classify a canonical object type into a source state."""
    if not object_type:
        return SourceState.CANONICAL.value
    mapping = {
        "PatchProposal": SourceState.PROPOSAL,
        "ChangeRequest": SourceState.PROPOSAL,
        "Evidence": SourceState.EVIDENCE,
    }
    return mapping.get(object_type, SourceState.CANONICAL).value


def classify_file_path(path: Path) -> str:
    """Classify a canonical file by its path under the model directory."""
    parts = {p.lower() for p in path.parts}
    if "patch-proposals" in parts:
        return SourceState.PROPOSAL.value
    if "change-requests" in parts:
        return SourceState.PROPOSAL.value
    if "evidence" in parts:
        return SourceState.EVIDENCE.value
    return SourceState.CANONICAL.value


def classify_artifact(artifact_path: Path | str) -> str:
    """Classify a generated artifact or file path by name/location."""
    path = Path(artifact_path)
    name = path.name.lower()
    parts = {p.lower() for p in path.parts}

    if name in {"source_registry.jsonl"} or "import-sessions" in parts:
        return SourceState.EVIDENCE.value

    if any(
        token in parts or token in name
        for token in {
            "readiness",
            "gap",
            "assessment",
            "high_risk",
            "impact",
            "validation",
        }
    ):
        return SourceState.FINDING.value

    if "patch-proposals" in parts or "change-requests" in parts:
        return SourceState.PROPOSAL.value

    return SourceState.CANONICAL.value


def classify_dataset_gap(gap_code: str) -> str:
    """Dataset gaps are generated findings, never canonical truth."""
    return SourceState.FINDING.value
```

- [ ] **Step 4: Export SourceState from schemas package**

Modify `src/modelops_core/schemas/__init__.py` to include `SourceState` in its public exports if it exports enums.

- [ ] **Step 5: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_source_classification.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/modelops_core/source_state.py src/modelops_core/schemas/__init__.py tests/test_source_classification.py
git commit -m "feat(#517): add source-state classification utilities"
```

---

### Task 3: Enrich API responses with source_state

**Files:**
- Modify: `src/modelops_core/api/app.py`
- Test: `tests/test_api.py`

**Interfaces:**
- Consumes: `classify_object_type`, `classify_dataset_gap`, `SourceState`.
- Produces: API responses include `source_state` fields.

- [ ] **Step 1: Write the failing test**

```python
from fastapi.testclient import TestClient

from modelops_core.api.app import app

client = TestClient(app)


def test_api_objects_include_source_state(sample_repo: str) -> None:
    response = client.get("/objects", params={"repo": sample_repo})
    assert response.status_code == 200
    data = response.json()
    assert data
    for obj in data:
        assert obj["source_state"] == "canonical"


def test_api_proposals_include_source_state(sample_repo: str) -> None:
    response = client.get("/proposals", params={"repo": sample_repo})
    assert response.status_code == 200
    data = response.json()
    for proposal in data:
        assert proposal["source_state"] == "proposal"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/test_api.py::test_api_objects_include_source_state tests/test_api.py::test_api_proposals_include_source_state -v`
Expected: FAIL with `KeyError: 'source_state'`

- [ ] **Step 3: Enrich API responses**

Modify `src/modelops_core/api/app.py`:

1. Add import at the top:

```python
from modelops_core.source_state import (
    classify_dataset_gap,
    classify_object_type,
)
```

2. In `list_objects`, add to each result:

```python
fm["source_state"] = classify_object_type(str(fm.get("type", "")))
```

3. In `get_object`, add:

```python
result["source_state"] = classify_object_type(str(result.get("type", "")))
```

4. In `list_proposals`, add:

```python
results.append(
    {
        "id": fm.get("id", f.stem),
        "status": fm.get("status", "pending_review"),
        "validation_status": fm.get("validation_status", "pending"),
        "applied_at": fm.get("applied_at"),
        "source_state": SourceState.PROPOSAL.value,
    }
)
```

5. In `get_proposal`, add:

```python
result = dict(fm)
result["source_state"] = SourceState.PROPOSAL.value
return result
```

6. In `validate`, add `source_state` to each result:

```python
{
    "severity": str(r.severity),
    "code": r.code,
    "message": r.message,
    "object_id": r.object_id,
    "suggested_fix": r.suggested_fix,
    "source_state": SourceState.FINDING.value,
}
```

7. In `gaps` and `dataset_readiness`, add `source_state` to each gap dict:

```python
def _gap_to_dict_with_state(gap: ColumnGap) -> dict[str, Any]:
    d = _gap_to_dict(gap)
    d["source_state"] = classify_dataset_gap(gap.gap_code)
    return d
```

Use this helper when serializing `dataset_gaps` and `model_gaps`.

8. In `dataset_readiness`, add `source_state` to `dataset_profile`:

```python
profile_dict = _build_dataset_profile_dict(...)
profile_dict["source_state"] = SourceState.EVIDENCE.value
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_api.py::test_api_objects_include_source_state tests/test_api.py::test_api_proposals_include_source_state -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/modelops_core/api/app.py tests/test_api.py
git commit -m "feat(#517): expose source_state in API responses"
```

---

### Task 4: Add mutation-safety tests

**Files:**
- Test: `tests/test_source_classification.py`

**Interfaces:**
- Consumes: model-sheet import service, gap promotion service, patch apply service.
- Produces: tests proving imports and findings do not write canonical files directly.

- [ ] **Step 1: Write tests**

```python
from pathlib import Path

import pytest

from modelops_core.gaps.gap_detection import DatasetGapReport, promote_gaps_to_proposal
from modelops_core.imports.model_sheet_import_service import import_model_sheet_xlsx
from modelops_core.patching.apply_service import apply_patch_proposal
from modelops_core.repository import scan_repository


def test_import_sheet_returns_proposal_not_canonical(
    sample_repo: str, tmp_path: Path
) -> None:
    # Create a minimal xlsx with one new object
    import openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Attribute"
    ws.append(["id", "type", "name", "status"])
    ws.append(["ATTR-TEST-NEW", "Attribute", "Test", "draft"])
    xlsx = tmp_path / "new_attrs.xlsx"
    wb.save(xlsx)

    model_path = Path(sample_repo) / "model"
    before = set(scan_repository(model_path))
    proposal = import_model_sheet_xlsx(xlsx, model_path)
    after = set(scan_repository(model_path))

    assert proposal["type"] == "PatchProposal"
    assert proposal["source_state"] == "proposal"
    assert before == after


def test_gap_promotion_creates_proposal_not_canonical(sample_repo: str) -> None:
    model_path = Path(sample_repo) / "model"
    before = set(scan_repository(model_path))

    report = DatasetGapReport(dataset_id="TEST")
    path = promote_gaps_to_proposal(report, model_path)

    after = set(scan_repository(model_path))
    assert path.name.startswith("PP-")
    assert "patch-proposals" in str(path)
    # Only the proposal file was added
    assert after - before == {str(path)}
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/test_source_classification.py -v`
Expected: FAIL because `source_state` is not present on the proposal dict returned by import.

- [ ] **Step 3: Enrich returned proposal dicts with source_state**

Modify `_build_proposal` in `src/modelops_core/imports/model_sheet_import_service.py` to add:

```python
proposal["source_state"] = SourceState.PROPOSAL.value
```

Modify `promote_gaps_to_proposal` in `src/modelops_core/gaps/gap_detection.py` to return the path (already does) and ensure the built proposal includes `source_state`. In `build_patch_proposal` in `src/modelops_core/patching/patch_proposal_service.py`, add:

```python
proposal["source_state"] = SourceState.PROPOSAL.value
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_source_classification.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/modelops_core/imports/model_sheet_import_service.py src/modelops_core/gaps/gap_detection.py src/modelops_core/patching/patch_proposal_service.py tests/test_source_classification.py
git commit -m "test(#517): assert evidence/finding write boundaries"
```

---

### Task 5: Update architecture documentation

**Files:**
- Modify: `docs/architecture/AI_PATCH_WORKFLOW.md`

- [ ] **Step 1: Add source-state section**

Append a section:

```markdown
## Source-of-truth states

Martenweave classifies every artifact into one of four states:

- **evidence** — raw imported inputs such as dataset profiles and import sessions.
- **finding** — generated analysis such as gap reports, readiness reports,
  validation results, and assessment artifacts.
- **proposal** — reviewable `PatchProposal` and `ChangeRequest` objects.
- **canonical** — approved objects in `model/` files.

Allowed transitions:

- evidence → finding (analysis reads imported evidence)
- evidence → proposal (import or gap promotion creates a proposal)
- finding → proposal (reviewing a finding may produce a proposal)
- proposal → canonical (only after human review and `apply`)

Only `proposal → canonical` writes to `model/`. Evidence and findings never
mutate canonical files.
```

- [ ] **Step 2: Commit**

```bash
git add docs/architecture/AI_PATCH_WORKFLOW.md
git commit -m "docs(#517): document source-of-truth states and transitions"
```

---

### Task 6: Run full validation

- [ ] **Step 1: Run targeted tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_source_classification.py tests/test_api.py -q
```

Expected: PASS

- [ ] **Step 2: Run issue keyword tests**

Run:

```bash
.venv/bin/python -m pytest tests/ -k "evidence or finding or proposal or canonical or mutation_safety" -q
```

Expected: PASS

- [ ] **Step 3: Lint**

Run:

```bash
.venv/bin/python -m ruff check .
```

Expected: no errors

- [ ] **Step 4: Commit any fixes**

```bash
git commit -a -m "chore(#517): lint fixes"
```

---

## Self-Review

- Spec coverage: every design section maps to a task.
- No placeholders: all code and commands are explicit.
- Type consistency: `SourceState` enum used throughout; classification utilities
  return `str` values for easy JSON serialization.
