"""Tests for data quality and coverage analysis in health report."""

from __future__ import annotations

from pathlib import Path

from modelops_core.index import build_index
from modelops_core.reports.health_report import (
    CoverageGap,
    DataQualityCoverage,
    generate_repository_health,
)


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


def test_attribute_without_validation_rule_gap(tmp_path: Path) -> None:
    db_path = _build_repo(
        tmp_path,
        [
            {"id": "ATTR-1", "type": "Attribute", "status": "active", "name": "A1"},
        ],
    )
    report = generate_repository_health(db_path)
    assert report.data_quality_coverage is not None
    assert report.data_quality_coverage.active_attributes == 1
    assert report.data_quality_coverage.attributes_with_rules == 0

    gaps = [g for g in report.coverage_gaps_list if g.gap_type == "missing_validation_rule"]
    assert len(gaps) == 1
    assert gaps[0].object_id == "ATTR-1"


def test_attribute_with_validation_rule_covered(tmp_path: Path) -> None:
    db_path = _build_repo(
        tmp_path,
        [
            {"id": "ATTR-2", "type": "Attribute", "status": "active", "name": "A2"},
            {
                "id": "VAL-1",
                "type": "ValidationRule",
                "status": "active",
                "name": "V1",
                "attribute": "ATTR-2",
            },
        ],
    )
    report = generate_repository_health(db_path)
    assert report.data_quality_coverage.active_attributes == 1
    assert report.data_quality_coverage.attributes_with_rules == 1
    gaps = [g for g in report.coverage_gaps_list if g.gap_type == "missing_validation_rule"]
    assert len(gaps) == 0


def test_field_endpoint_without_lov_gap(tmp_path: Path) -> None:
    db_path = _build_repo(
        tmp_path,
        [
            {"id": "FEP-1", "type": "FieldEndpoint", "status": "active", "name": "F1"},
        ],
    )
    report = generate_repository_health(db_path)
    assert report.data_quality_coverage.active_field_endpoints == 1
    assert report.data_quality_coverage.endpoints_with_lov == 0
    gaps = [g for g in report.coverage_gaps_list if g.gap_type == "missing_lov"]
    assert len(gaps) == 1


def test_field_endpoint_with_lov_covered(tmp_path: Path) -> None:
    db_path = _build_repo(
        tmp_path,
        [
            {
                "id": "FEP-2",
                "type": "FieldEndpoint",
                "status": "active",
                "name": "F2",
                "value_list": "VLIST-1",
            },
        ],
    )
    report = generate_repository_health(db_path)
    assert report.data_quality_coverage.endpoints_with_lov == 1
    gaps = [g for g in report.coverage_gaps_list if g.gap_type == "missing_lov"]
    assert len(gaps) == 0


def test_mapping_without_value_mapping_gap(tmp_path: Path) -> None:
    db_path = _build_repo(
        tmp_path,
        [
            {"id": "MAP-1", "type": "Mapping", "status": "active", "name": "M1"},
        ],
    )
    report = generate_repository_health(db_path)
    assert report.data_quality_coverage.active_mappings == 1
    assert report.data_quality_coverage.mappings_with_value_mapping == 0
    gaps = [g for g in report.coverage_gaps_list if g.gap_type == "missing_value_mapping"]
    assert len(gaps) == 1


def test_mapping_with_value_mapping_covered(tmp_path: Path) -> None:
    db_path = _build_repo(
        tmp_path,
        [
            {
                "id": "MAP-2",
                "type": "Mapping",
                "status": "active",
                "name": "M2",
                "value_mapping": "VMAP-1",
            },
        ],
    )
    report = generate_repository_health(db_path)
    assert report.data_quality_coverage.mappings_with_value_mapping == 1
    gaps = [g for g in report.coverage_gaps_list if g.gap_type == "missing_value_mapping"]
    assert len(gaps) == 0


def test_active_object_without_owner_gap(tmp_path: Path) -> None:
    db_path = _build_repo(
        tmp_path,
        [
            {"id": "ATTR-3", "type": "Attribute", "status": "active", "name": "A3"},
        ],
    )
    report = generate_repository_health(db_path)
    gaps = [g for g in report.coverage_gaps_list if g.gap_type == "missing_owner"]
    assert len(gaps) == 1
    assert gaps[0].object_id == "ATTR-3"


def test_active_object_with_owner_covered(tmp_path: Path) -> None:
    db_path = _build_repo(
        tmp_path,
        [
            {
                "id": "ATTR-4",
                "type": "Attribute",
                "status": "active",
                "name": "A4",
                "business_owner": "PERSON-1",
            },
        ],
    )
    report = generate_repository_health(db_path)
    gaps = [g for g in report.coverage_gaps_list if g.gap_type == "missing_owner"]
    assert len(gaps) == 0
    assert report.data_quality_coverage.objects_with_owner == 1


def test_data_quality_coverage_percentages() -> None:
    dq = DataQualityCoverage(
        active_attributes=10,
        attributes_with_rules=5,
        active_field_endpoints=10,
        endpoints_with_lov=2,
        active_mappings=10,
        mappings_with_value_mapping=1,
        active_datasets=0,
        datasets_with_profile=0,
        active_objects=10,
        objects_with_owner=7,
    )
    assert dq.attribute_rule_coverage_percent == 50.0
    assert dq.endpoint_lov_coverage_percent == 20.0
    assert dq.mapping_logic_coverage_percent == 10.0
    assert dq.dataset_profile_coverage_percent == 0.0
    assert dq.ownership_coverage_percent == 70.0


def test_coverage_gap_dataclass() -> None:
    gap = CoverageGap(
        object_id="OBJ-1",
        object_type="Attribute",
        object_name="Test",
        gap_type="missing_rule",
        suggested_action="Add a rule.",
    )
    assert gap.object_id == "OBJ-1"
    assert gap.suggested_action == "Add a rule."
