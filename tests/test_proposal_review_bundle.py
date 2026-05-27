"""Tests for proposal review-bundle CLI command."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from modelops_core.cli import app
from modelops_core.index import build_index
from modelops_core.patching.patch_model import PatchOperation
from modelops_core.patching.patch_proposal_service import (
    build_patch_proposal,
    write_patch_proposal,
)

runner = CliRunner()


def test_review_bundle_json_valid(tmp_path: Path) -> None:
    model_dir = tmp_path / "model"
    model_dir.mkdir()
    proposals_dir = model_dir / "patch-proposals"
    proposals_dir.mkdir()

    op = PatchOperation(op="update_object", object_id="DOMAIN-TEST", target_path="name", after="X")
    proposal = build_patch_proposal("PP-RB-001", [op])
    write_patch_proposal(proposal, model_dir)

    result = runner.invoke(
        app, ["proposal", "review-bundle", "PP-RB-001", "--repo", str(tmp_path), "--json"]
    )
    assert result.exit_code == 0
    data = json.loads(result.output)

    assert data["proposal_id"] == "PP-RB-001"
    assert "martenweave_version" in data

    # Report section
    report = data["report"]
    assert report["id"] == "PP-RB-001"
    assert report["status"] == "pending_review"
    assert report["effective_status"] == "pending_review"
    assert report["operations_count"] == 1
    assert report["risk_level"] is not None

    # Impact section (no index → note present)
    impact = data["impact"]
    assert impact["proposal_id"] == "PP-RB-001"
    assert "note" in impact
    assert "build-index" in impact["note"]

    # Validation section
    validation = data["validation"]
    assert validation["is_safe"] is True
    assert validation["error_count"] == 0
    assert validation["warning_count"] == 0
    assert validation["issues"] == []


def test_review_bundle_json_invalid(tmp_path: Path) -> None:
    model_dir = tmp_path / "model"
    model_dir.mkdir()
    proposals_dir = model_dir / "patch-proposals"
    proposals_dir.mkdir()

    proposal = build_patch_proposal("PP-RB-002", [])
    write_patch_proposal(proposal, model_dir)

    result = runner.invoke(
        app, ["proposal", "review-bundle", "PP-RB-002", "--repo", str(tmp_path), "--json"]
    )
    assert result.exit_code == 0
    data = json.loads(result.output)

    validation = data["validation"]
    assert validation["is_safe"] is False
    assert validation["error_count"] > 0
    assert any(i["code"] == "PATCH_OPERATIONS_EMPTY" for i in validation["issues"])


def test_review_bundle_not_found(tmp_path: Path) -> None:
    model_dir = tmp_path / "model"
    model_dir.mkdir()

    result = runner.invoke(
        app, ["proposal", "review-bundle", "PP-MISSING", "--repo", str(tmp_path), "--json"]
    )
    assert result.exit_code == 1
    data = json.loads(result.output)
    assert data["proposal_id"] == "PP-MISSING"
    assert data["error"] == "PatchProposal not found"


def test_review_bundle_human_readable(tmp_path: Path) -> None:
    model_dir = tmp_path / "model"
    model_dir.mkdir()
    proposals_dir = model_dir / "patch-proposals"
    proposals_dir.mkdir()

    op = PatchOperation(op="update_object", object_id="DOMAIN-TEST", target_path="name", after="X")
    proposal = build_patch_proposal("PP-RB-003", [op])
    write_patch_proposal(proposal, model_dir)

    result = runner.invoke(
        app, ["proposal", "review-bundle", "PP-RB-003", "--repo", str(tmp_path)]
    )
    assert result.exit_code == 0
    assert "Proposal Review Bundle: PP-RB-003" in result.output
    assert "Report" in result.output
    assert "Impact" in result.output
    assert "Validation" in result.output
    assert "Safe" in result.output or "Errors: 0" in result.output


def test_review_bundle_with_index(tmp_path: Path) -> None:
    model_dir = tmp_path / "model"
    model_dir.mkdir()
    generated_dir = tmp_path / "generated"
    generated_dir.mkdir()

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

    proposals_dir = model_dir / "patch-proposals"
    proposals_dir.mkdir()
    (proposals_dir / "PP-RB-004.md").write_text(
        "---\n"
        "id: PP-RB-004\n"
        "type: PatchProposal\n"
        "status: accepted\n"
        "operations:\n"
        "  - op: update_object\n"
        "    object_id: ATTR-TEST\n"
        "    target_path: name\n"
        "    after: Updated Name\n"
        "---\n",
        encoding="utf-8",
    )

    db_path = generated_dir / "modelops.db"
    build_index(repo_root=tmp_path, db_path=db_path)

    result = runner.invoke(
        app, ["proposal", "review-bundle", "PP-RB-004", "--repo", str(tmp_path), "--json"]
    )
    assert result.exit_code == 0
    data = json.loads(result.output)

    impact = data["impact"]
    assert "note" not in impact
    assert len(impact["affected_objects"]) > 0
    affected_ids = {obj["object_id"] for obj in impact["affected_objects"]}
    assert "DOMAIN-TEST" in affected_ids
    assert len(impact["operations"]) == 1
    assert impact["operations"][0]["op"] == "update_object"
