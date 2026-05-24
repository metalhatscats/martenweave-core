"""Tests for model analysis service."""

from __future__ import annotations

from pathlib import Path

from modelops_core.index import build_index
from modelops_core.reports.analysis_service import generate_analysis_report


def _build_repo(tmp_path: Path, objects: list[dict]) -> Path:
    model_dir = tmp_path / "model"
    model_dir.mkdir(parents=True, exist_ok=True)
    generated_dir = tmp_path / "generated"
    generated_dir.mkdir(parents=True, exist_ok=True)

    for obj in objects:
        obj_id = obj["id"]
        frontmatter_lines = []
        for k, v in obj.items():
            if isinstance(v, list):
                frontmatter_lines.append(f"{k}:")
                for item in v:
                    frontmatter_lines.append(f"  - {item}")
            else:
                frontmatter_lines.append(f"{k}: {v}")
        frontmatter = "\n".join(frontmatter_lines)
        content = f"---\n{frontmatter}\n---\n\n# {obj_id}\n"
        (model_dir / f"{obj_id}.md").write_text(content, encoding="utf-8")

    db_path = generated_dir / "modelops.db"
    build_index(repo_root=tmp_path, db_path=db_path, allow_invalid=True)
    return db_path


def test_orphan_fields_report(tmp_path: Path) -> None:
    db_path = _build_repo(
        tmp_path,
        [
            {
                "id": "FEP-1",
                "type": "FieldEndpoint",
                "status": "active",
                "name": "F1",
            },
            {
                "id": "FEP-2",
                "type": "FieldEndpoint",
                "status": "active",
                "name": "F2",
                "business_attribute": "ATTR-1",
            },
        ],
    )
    report = generate_analysis_report(db_path, tmp_path)
    assert report.orphan_fields is not None
    assert len(report.orphan_fields.field_endpoints_without_attribute) == 1
    assert report.orphan_fields.field_endpoints_without_attribute[0]["object_id"] == "FEP-1"


def test_attributes_without_fields_report(tmp_path: Path) -> None:
    db_path = _build_repo(
        tmp_path,
        [
            {"id": "ATTR-1", "type": "Attribute", "status": "active", "name": "A1"},
            {
                "id": "USE-1",
                "type": "AttributeUsage",
                "status": "active",
                "attribute": "ATTR-1",
            },
            {"id": "ATTR-2", "type": "Attribute", "status": "active", "name": "A2"},
        ],
    )
    report = generate_analysis_report(db_path, tmp_path)
    assert report.attribute_coverage is not None
    attrs = report.attribute_coverage.attributes_without_fields
    assert len(attrs) == 1
    assert attrs[0]["object_id"] == "ATTR-2"


def test_ownership_gaps_report(tmp_path: Path) -> None:
    db_path = _build_repo(
        tmp_path,
        [
            {"id": "ATTR-1", "type": "Attribute", "status": "active", "name": "A1"},
            {
                "id": "ATTR-2",
                "type": "Attribute",
                "status": "active",
                "name": "A2",
                "business_owner": "PERSON-1",
            },
        ],
    )
    report = generate_analysis_report(db_path, tmp_path)
    gaps = [g for g in report.ownership_gaps if g["object_id"] == "ATTR-1"]
    assert len(gaps) == 1
    assert gaps[0]["gap_type"] == "missing_owner"


def test_validation_coverage_report(tmp_path: Path) -> None:
    db_path = _build_repo(
        tmp_path,
        [
            {"id": "ATTR-1", "type": "Attribute", "status": "active", "name": "A1"},
            {
                "id": "VAL-1",
                "type": "ValidationRule",
                "status": "active",
                "name": "V1",
                "attribute": "ATTR-1",
            },
            {"id": "ATTR-2", "type": "Attribute", "status": "active", "name": "A2"},
        ],
    )
    report = generate_analysis_report(db_path, tmp_path)
    gaps = [g for g in report.validation_coverage if g["object_id"] == "ATTR-2"]
    assert len(gaps) == 1


def test_lov_coverage_report(tmp_path: Path) -> None:
    db_path = _build_repo(
        tmp_path,
        [
            {"id": "FEP-1", "type": "FieldEndpoint", "status": "active", "name": "F1"},
            {
                "id": "FEP-2",
                "type": "FieldEndpoint",
                "status": "active",
                "name": "F2",
                "value_list": "VLIST-1",
            },
        ],
    )
    report = generate_analysis_report(db_path, tmp_path)
    gaps = [g for g in report.lov_coverage if g["object_id"] == "FEP-1"]
    assert len(gaps) == 1


def test_mapping_coverage_report(tmp_path: Path) -> None:
    db_path = _build_repo(
        tmp_path,
        [
            {"id": "MAP-1", "type": "Mapping", "status": "active", "name": "M1"},
            {
                "id": "MAP-2",
                "type": "Mapping",
                "status": "active",
                "name": "M2",
                "value_mapping": "VMAP-1",
            },
        ],
    )
    report = generate_analysis_report(db_path, tmp_path)
    gaps = [g for g in report.mapping_coverage if g["object_id"] == "MAP-1"]
    assert len(gaps) == 1


def test_risk_report(tmp_path: Path) -> None:
    db_path = _build_repo(
        tmp_path,
        [
            {
                "id": "ISS-1",
                "type": "Issue",
                "status": "active",
                "name": "I1",
            },
            {
                "id": "RISK-1",
                "type": "Risk",
                "status": "active",
                "name": "R1",
            },
        ],
    )
    report = generate_analysis_report(db_path, tmp_path)
    assert report.risk_report is not None
    assert report.risk_report.issue_count == 1
    assert report.risk_report.risk_count == 1


def test_change_activity_report(tmp_path: Path) -> None:
    db_path = _build_repo(
        tmp_path,
        [
            {"id": "DOMAIN-1", "type": "MasterDataDomain", "status": "active", "name": "D1"},
        ],
    )
    report = generate_analysis_report(db_path, tmp_path)
    assert report.change_activity is not None
    assert report.change_activity.event_count == 0
