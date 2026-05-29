"""Tests for proposal impact analysis."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from modelops_core.cli import app
from modelops_core.impact.proposal_impact_service import (
    generate_proposal_impact_report,
)
from modelops_core.index import build_index
from modelops_core.repository.parser import ParsedObject

runner = CliRunner()


def _make_obj(source_path: Path, frontmatter: dict) -> ParsedObject:
    return ParsedObject(
        source_path=str(source_path),
        content_hash="abc",
        frontmatter=frontmatter,
        body="",
        parser_error=None,
    )


def test_proposal_impact_for_update_object(tmp_path: Path) -> None:
    model_dir = tmp_path / "model"
    model_dir.mkdir()
    generated_dir = tmp_path / "generated"
    generated_dir.mkdir()

    # Create objects
    (model_dir / "DOMAIN-TEST.md").write_text(
        "---\nid: DOMAIN-TEST\ntype: MasterDataDomain\nstatus: active\nname: Test Domain\n---\n",
        encoding="utf-8",
    )
    (model_dir / "ATTR-TEST.md").write_text(
        "---\n"
        "id: ATTR-TEST\n"
        "type: Attribute\n"
        "status: active\n"
        "name: Test Attribute\n"
        "domain: DOMAIN-TEST\n"
        "---\n",
        encoding="utf-8",
    )

    db_path = generated_dir / "modelops.db"
    build_index(repo_root=tmp_path, db_path=db_path)

    operations = [
        {
            "op": "update_object",
            "object_id": "ATTR-TEST",
            "target_path": "name",
            "after": "New Name",
        }
    ]
    report = generate_proposal_impact_report(db_path, "PP-001", operations, max_depth=2)

    assert report.proposal_id == "PP-001"
    assert len(report.operation_reports) == 1
    assert report.operation_reports[0].object_id == "ATTR-TEST"
    # ATTR-TEST references DOMAIN-TEST, so impact should include DOMAIN-TEST
    affected_ids = {obj.object_id for obj in report.all_affected_objects}
    assert "DOMAIN-TEST" in affected_ids


def test_proposal_impact_for_create_object_synthetic_refs(tmp_path: Path) -> None:
    model_dir = tmp_path / "model"
    model_dir.mkdir()
    generated_dir = tmp_path / "generated"
    generated_dir.mkdir()

    (model_dir / "DOMAIN-TEST.md").write_text(
        "---\nid: DOMAIN-TEST\ntype: MasterDataDomain\nstatus: active\nname: Test Domain\n---\n",
        encoding="utf-8",
    )

    db_path = generated_dir / "modelops.db"
    build_index(repo_root=tmp_path, db_path=db_path)

    operations = [
        {
            "op": "create_object",
            "object_id": "ATTR-NEW",
            "object_type": "Attribute",
            "after": {
                "id": "ATTR-NEW",
                "type": "Attribute",
                "status": "draft",
                "domain": "DOMAIN-TEST",
            },
        }
    ]
    report = generate_proposal_impact_report(db_path, "PP-002", operations, max_depth=2)

    assert report.proposal_id == "PP-002"
    assert len(report.operation_reports) == 1
    synthetic = report.operation_reports[0].synthetic_affected
    assert len(synthetic) == 1
    assert synthetic[0].object_id == "DOMAIN-TEST"
    assert synthetic[0].direction == "downstream"


def test_proposal_impact_high_risk_for_mapping(tmp_path: Path) -> None:
    model_dir = tmp_path / "model"
    model_dir.mkdir()
    generated_dir = tmp_path / "generated"
    generated_dir.mkdir()

    (model_dir / "MAP-001.md").write_text(
        "---\nid: MAP-001\ntype: Mapping\nstatus: active\nname: Test Mapping\n---\n",
        encoding="utf-8",
    )

    db_path = generated_dir / "modelops.db"
    build_index(repo_root=tmp_path, db_path=db_path)

    operations = [
        {"op": "update_object", "object_id": "MAP-001", "target_path": "name", "after": "New"}
    ]
    report = generate_proposal_impact_report(db_path, "PP-003", operations, max_depth=2)
    assert report.high_risk is True


def test_proposal_impact_deduplication(tmp_path: Path) -> None:
    model_dir = tmp_path / "model"
    model_dir.mkdir()
    generated_dir = tmp_path / "generated"
    generated_dir.mkdir()

    (model_dir / "DOMAIN-TEST.md").write_text(
        "---\nid: DOMAIN-TEST\ntype: MasterDataDomain\nstatus: active\nname: Test Domain\n---\n",
        encoding="utf-8",
    )
    (model_dir / "ATTR-A.md").write_text(
        "---\nid: ATTR-A\ntype: Attribute\nstatus: active\nname: A\ndomain: DOMAIN-TEST\n---\n",
        encoding="utf-8",
    )
    (model_dir / "ATTR-B.md").write_text(
        "---\nid: ATTR-B\ntype: Attribute\nstatus: active\nname: B\ndomain: DOMAIN-TEST\n---\n",
        encoding="utf-8",
    )

    db_path = generated_dir / "modelops.db"
    build_index(repo_root=tmp_path, db_path=db_path)

    operations = [
        {"op": "update_object", "object_id": "ATTR-A", "target_path": "name", "after": "A2"},
        {"op": "update_object", "object_id": "ATTR-B", "target_path": "name", "after": "B2"},
    ]
    report = generate_proposal_impact_report(db_path, "PP-004", operations, max_depth=2)

    # Both ATTR-A and ATTR-B reference DOMAIN-TEST, so DOMAIN-TEST should appear only once
    affected = report.all_affected_objects
    domain_objs = [obj for obj in affected if obj.object_id == "DOMAIN-TEST"]
    assert len(domain_objs) == 1


def test_cli_proposal_impact_no_index(tmp_path: Path) -> None:
    model_dir = tmp_path / "model"
    model_dir.mkdir()
    proposals_dir = model_dir / "patch-proposals"
    proposals_dir.mkdir()
    (proposals_dir / "PP-001.md").write_text(
        "---\nid: PP-001\ntype: PatchProposal\nstatus: accepted\noperations: []\n---\n",
        encoding="utf-8",
    )

    result = runner.invoke(app, ["proposal", "impact", "PP-001", "--repo", str(tmp_path)])
    assert result.exit_code == 1
    assert "No index found" in result.output


def test_cli_proposal_impact_not_found(tmp_path: Path) -> None:
    model_dir = tmp_path / "model"
    model_dir.mkdir()
    generated_dir = tmp_path / "generated"
    generated_dir.mkdir()
    db_path = generated_dir / "modelops.db"
    build_index(repo_root=tmp_path, db_path=db_path)

    result = runner.invoke(app, ["proposal", "impact", "PP-999", "--repo", str(tmp_path)])
    assert result.exit_code == 1
    assert "PatchProposal not found" in result.output


def test_cli_proposal_impact_json(tmp_path: Path) -> None:
    model_dir = tmp_path / "model"
    model_dir.mkdir()
    generated_dir = tmp_path / "generated"
    generated_dir.mkdir()

    (model_dir / "DOMAIN-TEST.md").write_text(
        "---\nid: DOMAIN-TEST\ntype: MasterDataDomain\nstatus: active\nname: Test Domain\n---\n",
        encoding="utf-8",
    )

    proposals_dir = model_dir / "patch-proposals"
    proposals_dir.mkdir()
    (proposals_dir / "PP-001.md").write_text(
        "---\n"
        "id: PP-001\n"
        "type: PatchProposal\n"
        "status: accepted\n"
        "operations:\n"
        "  - op: update_object\n"
        "    object_id: DOMAIN-TEST\n"
        "    target_path: name\n"
        "    after: Updated Domain\n"
        "---\n",
        encoding="utf-8",
    )

    db_path = generated_dir / "modelops.db"
    build_index(repo_root=tmp_path, db_path=db_path)

    result = runner.invoke(app, ["proposal", "impact", "PP-001", "--repo", str(tmp_path), "--json"])
    assert result.exit_code == 0
    assert "proposal_id" in result.output
    assert "PP-001" in result.output
    assert "affected_objects" in result.output
