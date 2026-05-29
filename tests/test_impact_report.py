"""Tests for impact report rendering and structure."""

from __future__ import annotations

from modelops_core.impact.impact_report import (
    AffectedObject,
    ImpactReport,
    render_impact_report_markdown,
)


class TestImpactReport:
    def test_empty_affected_objects(self) -> None:
        report = ImpactReport(root_object_id="ATTR-001")
        assert report.grouped_by_type == {}
        assert report.downstream_objects == []
        assert report.upstream_objects == []
        assert report.affected_relationship_classes == {}

    def test_grouped_by_direction_and_type_unknown(self) -> None:
        obj = AffectedObject(
            object_id="FEP-001", object_type="FieldEndpoint", direction=None, depth=1
        )
        report = ImpactReport(root_object_id="ATTR-001", affected_objects=[obj])
        grouped = report.grouped_by_direction_and_type
        assert "unknown" in grouped
        assert "FieldEndpoint" in grouped["unknown"]

    def test_affected_relationship_classes_unknown(self) -> None:
        obj = AffectedObject(
            object_id="FEP-001",
            object_type="FieldEndpoint",
            relationship_class=None,
        )
        report = ImpactReport(root_object_id="ATTR-001", affected_objects=[obj])
        assert report.affected_relationship_classes == {"unknown": 1}

    def test_filter_properties(self) -> None:
        objs = [
            AffectedObject(object_id="MAP-001", object_type="Mapping", direction="downstream"),
            AffectedObject(object_id="VR-001", object_type="ValidationRule", direction="upstream"),
            AffectedObject(object_id="EC-001", object_type="EntityContext", direction="downstream"),
        ]
        report = ImpactReport(root_object_id="ATTR-001", affected_objects=objs)
        assert len(report.affected_mappings) == 1
        assert len(report.affected_rules) == 1
        assert len(report.affected_contexts) == 1
        assert len(report.downstream_objects) == 2
        assert len(report.upstream_objects) == 1

    def test_downstream_upstream_exact_match(self) -> None:
        objs = [
            AffectedObject(object_id="A", object_type="Attribute", direction="downstream"),
            AffectedObject(object_id="B", object_type="Attribute", direction="upstream"),
            AffectedObject(object_id="C", object_type="Attribute", direction=None),
        ]
        report = ImpactReport(root_object_id="ATTR-001", affected_objects=objs)
        assert len(report.downstream_objects) == 1
        assert len(report.upstream_objects) == 1


class TestRenderImpactReportMarkdown:
    def test_empty_report(self) -> None:
        report = ImpactReport(root_object_id="ATTR-001")
        md = render_impact_report_markdown(report)
        assert "# Impact Report: ATTR-001" in md
        assert "No related objects found" in md

    def test_root_name_omitted_when_none(self) -> None:
        report = ImpactReport(root_object_id="ATTR-001")
        md = render_impact_report_markdown(report)
        assert "Name:" not in md

    def test_root_name_included_when_present(self) -> None:
        report = ImpactReport(root_object_id="ATTR-001", root_object_name="Customer Group")
        md = render_impact_report_markdown(report)
        assert "Customer Group" in md

    def test_table_renders_with_dash_for_none_name(self) -> None:
        obj = AffectedObject(
            object_id="FEP-001",
            object_type="FieldEndpoint",
            object_name=None,
            direction="downstream",
        )
        report = ImpactReport(root_object_id="ATTR-001", affected_objects=[obj])
        md = render_impact_report_markdown(report)
        assert "FEP-001" in md
        assert "—" in md

    def test_relationship_classes_section_omitted_when_empty(self) -> None:
        report = ImpactReport(root_object_id="ATTR-001")
        md = render_impact_report_markdown(report)
        assert "Relationship Classes" not in md
