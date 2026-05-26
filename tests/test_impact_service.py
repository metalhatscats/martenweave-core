"""Tests for impact analysis."""

from __future__ import annotations

from pathlib import Path

from modelops_core.impact.impact_report import (
    AffectedObject,
    ImpactReport,
    render_impact_report_markdown,
)
from modelops_core.impact.impact_service import generate_impact_report
from modelops_core.index import build_index


def test_impact_report_found_object(temp_model_dir: Path) -> None:
    repo_root = temp_model_dir.parent
    db_path = repo_root / "generated" / "modelops.db"
    build_index(repo_root=repo_root, db_path=db_path)

    report = generate_impact_report(db_path, "DOMAIN-TEST", max_depth=2)
    assert report.root_object_id == "DOMAIN-TEST"
    # ATTR-TEST references DOMAIN-TEST, so it should appear downstream
    assert any(o.object_id == "ATTR-TEST" for o in report.affected_objects)


def test_impact_report_missing_object(temp_model_dir: Path) -> None:
    repo_root = temp_model_dir.parent
    db_path = repo_root / "generated" / "modelops.db"
    build_index(repo_root=repo_root, db_path=db_path)

    report = generate_impact_report(db_path, "MISSING-ID", max_depth=2)
    assert report.root_object_type is None
    assert report.affected_objects == []


def test_render_markdown_includes_root_object() -> None:
    report = ImpactReport(
        root_object_id="DOMAIN-TEST",
        root_object_type="MasterDataDomain",
        root_object_name="Test Domain",
        affected_objects=[
            AffectedObject(
                object_id="ATTR-TEST",
                object_type="Attribute",
                object_name="Test Attribute",
                direction="downstream",
                depth=1,
            )
        ],
    )
    md = render_impact_report_markdown(report)
    assert "# Impact Report: DOMAIN-TEST" in md
    assert "DOMAIN-TEST" in md
    assert "MasterDataDomain" in md
    assert "Test Domain" in md


def test_render_markdown_includes_affected_objects_table() -> None:
    report = ImpactReport(
        root_object_id="DOMAIN-TEST",
        root_object_type="MasterDataDomain",
        affected_objects=[
            AffectedObject(
                object_id="ATTR-TEST",
                object_type="Attribute",
                object_name="Test Attribute",
                direction="downstream",
                depth=1,
            ),
            AffectedObject(
                object_id="FEP-TEST",
                object_type="FieldEndpoint",
                direction="upstream",
                depth=1,
            ),
        ],
    )
    md = render_impact_report_markdown(report)
    assert "| Object ID | Type | Name | Direction | Depth |" in md
    assert "ATTR-TEST" in md
    assert "FEP-TEST" in md
    assert "downstream" in md
    assert "upstream" in md


def test_render_markdown_no_affected_objects() -> None:
    report = ImpactReport(
        root_object_id="DOMAIN-TEST",
        root_object_type="MasterDataDomain",
        affected_objects=[],
    )
    md = render_impact_report_markdown(report)
    assert "No related objects found" in md


def test_render_markdown_relationship_summary() -> None:
    report = ImpactReport(
        root_object_id="DOMAIN-TEST",
        root_object_type="MasterDataDomain",
        affected_objects=[
            AffectedObject(
                object_id="ATTR-1",
                object_type="Attribute",
                relationship_type="maps_to",
                direction="downstream",
                depth=1,
            ),
            AffectedObject(
                object_id="ATTR-2",
                object_type="Attribute",
                relationship_type="maps_to",
                direction="downstream",
                depth=1,
            ),
            AffectedObject(
                object_id="FEP-1",
                object_type="FieldEndpoint",
                relationship_type="belongs_to",
                direction="upstream",
                depth=1,
            ),
        ],
    )
    md = render_impact_report_markdown(report)
    assert "## Relationship Summary" in md
    assert "maps_to" in md
    assert "belongs_to" in md


def test_render_markdown_downstream_upstream_counts() -> None:
    report = ImpactReport(
        root_object_id="DOMAIN-TEST",
        root_object_type="MasterDataDomain",
        affected_objects=[
            AffectedObject(
                object_id="ATTR-1",
                object_type="Attribute",
                direction="downstream",
                depth=1,
            ),
            AffectedObject(
                object_id="FEP-1",
                object_type="FieldEndpoint",
                direction="upstream",
                depth=1,
            ),
        ],
    )
    md = render_impact_report_markdown(report)
    assert "**Downstream**: 1" in md
    assert "**Upstream**: 1" in md
    assert "**Total affected objects**: 2" in md
