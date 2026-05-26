"""Tests for impact analysis."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from modelops_core.cli import app
from modelops_core.impact.impact_report import (
    AffectedObject,
    ImpactReport,
    render_impact_report_markdown,
)
from modelops_core.impact.impact_service import generate_impact_report
from modelops_core.index import build_index

runner = CliRunner()


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



def test_impact_report_grouped_by_direction_and_type() -> None:
    report = ImpactReport(
        root_object_id="DOMAIN-TEST",
        affected_objects=[
            AffectedObject(
                object_id="ATTR-1",
                object_type="Attribute",
                direction="downstream",
                depth=1,
            ),
            AffectedObject(
                object_id="ATTR-2",
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
    grouped = report.grouped_by_direction_and_type
    assert "downstream" in grouped
    assert "upstream" in grouped
    assert len(grouped["downstream"]["Attribute"]) == 2
    assert len(grouped["upstream"]["FieldEndpoint"]) == 1


def test_impact_report_affected_relationship_classes() -> None:
    report = ImpactReport(
        root_object_id="DOMAIN-TEST",
        affected_objects=[
            AffectedObject(
                object_id="ATTR-1",
                object_type="Attribute",
                relationship_class="semantic",
                direction="downstream",
                depth=1,
            ),
            AffectedObject(
                object_id="FEP-1",
                object_type="FieldEndpoint",
                relationship_class="physical",
                direction="upstream",
                depth=1,
            ),
            AffectedObject(
                object_id="FEP-2",
                object_type="FieldEndpoint",
                relationship_class="semantic",
                direction="upstream",
                depth=1,
            ),
        ],
    )
    assert report.affected_relationship_classes == {"semantic": 2, "physical": 1}


def test_impact_report_affected_mappings_rules_contexts() -> None:
    report = ImpactReport(
        root_object_id="DOMAIN-TEST",
        affected_objects=[
            AffectedObject(
                object_id="MAP-1", object_type="Mapping", direction="downstream", depth=1
            ),
            AffectedObject(
                object_id="VAL-1",
                object_type="ValidationRule",
                direction="downstream",
                depth=1,
            ),
            AffectedObject(
                object_id="CTX-1",
                object_type="EntityContext",
                direction="upstream",
                depth=1,
            ),
            AffectedObject(
                object_id="ATTR-1", object_type="Attribute", direction="downstream", depth=1
            ),
        ],
    )
    assert len(report.affected_mappings) == 1
    assert len(report.affected_rules) == 1
    assert len(report.affected_contexts) == 1


def test_render_markdown_includes_relationship_classes() -> None:
    report = ImpactReport(
        root_object_id="DOMAIN-TEST",
        affected_objects=[
            AffectedObject(
                object_id="ATTR-1",
                object_type="Attribute",
                relationship_class="semantic",
                direction="downstream",
                depth=1,
            ),
        ],
    )
    md = render_impact_report_markdown(report)
    assert "## Relationship Classes" in md
    assert "semantic" in md


def test_render_markdown_includes_grouped_sections() -> None:
    report = ImpactReport(
        root_object_id="DOMAIN-TEST",
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
    assert "## Grouped by Direction and Type" in md
    assert "### Downstream" in md
    assert "### Upstream" in md


class TestImpactCliGrouping:
    def test_impact_group_by_type(self, tmp_path: Path) -> None:
        from modelops_core.index import build_index

        repo_root = tmp_path / "repo"
        model_dir = repo_root / "model"
        model_dir.mkdir(parents=True)
        generated = repo_root / "generated"
        generated.mkdir()

        # Create minimal model
        (model_dir / "DOMAIN-TEST.md").write_text(
            "---\n"
            "id: DOMAIN-TEST\n"
            "type: MasterDataDomain\n"
            "status: active\n"
            "name: Test Domain\n"
            "---\n\n# Test\n",
            encoding="utf-8",
        )
        (model_dir / "ATTR-TEST.md").write_text(
            "---\n"
            "id: ATTR-TEST\n"
            "type: Attribute\n"
            "status: active\n"
            "name: Test Attr\n"
            "domain: DOMAIN-TEST\n"
            "---\n\n# Test\n",
            encoding="utf-8",
        )

        db_path = generated / "modelops.db"
        build_index(repo_root=repo_root, db_path=db_path)

        result = runner.invoke(
            app, ["impact", "DOMAIN-TEST", "--repo", str(repo_root), "--group-by", "type"]
        )
        assert result.exit_code == 0
        assert "Attribute" in result.output

    def test_impact_group_by_direction(self, tmp_path: Path) -> None:
        from modelops_core.index import build_index

        repo_root = tmp_path / "repo"
        model_dir = repo_root / "model"
        model_dir.mkdir(parents=True)
        generated = repo_root / "generated"
        generated.mkdir()

        (model_dir / "DOMAIN-TEST.md").write_text(
            "---\n"
            "id: DOMAIN-TEST\n"
            "type: MasterDataDomain\n"
            "status: active\n"
            "name: Test Domain\n"
            "---\n\n# Test\n",
            encoding="utf-8",
        )
        (model_dir / "ATTR-TEST.md").write_text(
            "---\n"
            "id: ATTR-TEST\n"
            "type: Attribute\n"
            "status: active\n"
            "name: Test Attr\n"
            "domain: DOMAIN-TEST\n"
            "---\n\n# Test\n",
            encoding="utf-8",
        )

        db_path = generated / "modelops.db"
        build_index(repo_root=repo_root, db_path=db_path)

        result = runner.invoke(
            app,
            ["impact", "DOMAIN-TEST", "--repo", str(repo_root), "--group-by", "direction"],
        )
        assert result.exit_code == 0
        assert "Upstream" in result.output

    def test_impact_group_by_relationship_json(self, tmp_path: Path) -> None:
        from modelops_core.index import build_index

        repo_root = tmp_path / "repo"
        model_dir = repo_root / "model"
        model_dir.mkdir(parents=True)
        generated = repo_root / "generated"
        generated.mkdir()

        (model_dir / "DOMAIN-TEST.md").write_text(
            "---\n"
            "id: DOMAIN-TEST\n"
            "type: MasterDataDomain\n"
            "status: active\n"
            "name: Test Domain\n"
            "---\n\n# Test\n",
            encoding="utf-8",
        )
        (model_dir / "ATTR-TEST.md").write_text(
            "---\n"
            "id: ATTR-TEST\n"
            "type: Attribute\n"
            "status: active\n"
            "name: Test Attr\n"
            "domain: DOMAIN-TEST\n"
            "---\n\n# Test\n",
            encoding="utf-8",
        )

        db_path = generated / "modelops.db"
        build_index(repo_root=repo_root, db_path=db_path)

        result = runner.invoke(
            app,
            [
                "impact",
                "DOMAIN-TEST",
                "--repo",
                str(repo_root),
                "--group-by",
                "relationship",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "grouped" in data
