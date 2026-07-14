"""Tests for source-state classification across the product."""

from __future__ import annotations

from pathlib import Path

import pytest

from modelops_core.gaps.gap_detection import DatasetGapReport, promote_gaps_to_proposal
from modelops_core.imports.model_sheet_import_service import import_model_sheet_xlsx
from modelops_core.repository import scan_repository
from modelops_core.schemas.common import SourceState
from modelops_core.source_state import (
    classify_artifact,
    classify_dataset_gap,
    classify_file_path,
    classify_object_type,
)


def test_source_state_values() -> None:
    assert SourceState.EVIDENCE == "evidence"
    assert SourceState.FINDING == "finding"
    assert SourceState.PROPOSAL == "proposal"
    assert SourceState.CANONICAL == "canonical"


def test_classify_object_type() -> None:
    assert classify_object_type("PatchProposal") == "proposal"
    assert classify_object_type("ChangeRequest") == "proposal"
    assert classify_object_type("Evidence") == "evidence"
    assert classify_object_type("Attribute") == "canonical"
    assert classify_object_type("FieldEndpoint") == "canonical"
    assert classify_object_type(None) == "canonical"


def test_classify_file_path() -> None:
    assert classify_file_path(Path("model/patch-proposals/PP-0001.md")) == "proposal"
    assert classify_file_path(Path("model/change-requests/CR-0001.md")) == "proposal"
    assert classify_file_path(Path("model/evidence/EV-0001.md")) == "evidence"
    assert classify_file_path(Path("model/attributes/ATTR-0001.md")) == "canonical"


def test_classify_artifact() -> None:
    assert classify_artifact("generated/source_registry.jsonl") == "evidence"
    assert classify_artifact("generated/import-sessions/sessions.jsonl") == "evidence"
    assert classify_artifact("generated/readiness.json") == "finding"
    assert classify_artifact("generated/assessment/scorecard.md") == "finding"
    assert classify_artifact("generated/high_risk_fields.md") == "finding"
    assert classify_artifact("generated/impact/ATTR-0001.md") == "finding"
    assert classify_artifact("generated/validation_report.json") == "finding"
    assert classify_artifact("model/patch-proposals/PP-0001.md") == "proposal"
    assert classify_artifact("model/change-requests/CR-0001.md") == "proposal"
    assert classify_artifact("generated/modelops.db") == "canonical"
    assert classify_artifact("generated/search_documents.jsonl") == "canonical"


def test_classify_dataset_gap() -> None:
    assert classify_dataset_gap("UNMODELED_DATASET_COLUMN") == "finding"
    assert classify_dataset_gap("MISSING_OWNER") == "finding"


def test_import_sheet_returns_proposal_not_canonical(temp_model_dir: Path) -> None:
    pytest.importorskip("openpyxl")
    from openpyxl import Workbook

    model_path = temp_model_dir
    wb = Workbook()
    ws = wb.active
    ws.title = "Attribute"
    ws.append(["id", "type", "name", "status"])
    ws.append(["ATTR-TEST-NEW", "Attribute", "Test", "draft"])
    xlsx = temp_model_dir.parent / "new_attrs.xlsx"
    wb.save(xlsx)
    wb.close()

    before = set(scan_repository(model_path))
    proposal = import_model_sheet_xlsx(xlsx, model_path)
    after = set(scan_repository(model_path))

    assert proposal["type"] == "PatchProposal"
    assert proposal["source_state"] == "proposal"
    assert before == after


def test_gap_promotion_creates_proposal_not_canonical(temp_model_dir: Path) -> None:
    model_path = temp_model_dir
    before = set(scan_repository(model_path))

    report = DatasetGapReport(dataset_id="TEST")
    path = promote_gaps_to_proposal(report, model_path)

    after = set(scan_repository(model_path))
    assert path.name.startswith("PP-")
    assert "patch-proposals" in str(path)
    assert after - before == {str(path)}

    # The written proposal file is classified as a proposal, not canonical.
    assert path.name.endswith(".md")
    from modelops_core.repository import parse_file

    parsed = parse_file(path)
    assert parsed.frontmatter.get("source_state") == "proposal"
