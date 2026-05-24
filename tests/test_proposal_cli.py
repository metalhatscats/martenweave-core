"""Tests for proposal CLI commands."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from modelops_core.cli import app
from modelops_core.patching.patch_model import PatchOperation
from modelops_core.patching.patch_proposal_service import (
    build_patch_proposal,
    transition_patch_proposal_status,
    write_patch_proposal,
)

runner = CliRunner()


def _create_accepted_proposal(temp_model_dir: Path, proposal_id: str, operations: list) -> None:
    proposal = build_patch_proposal(proposal_id, operations)
    write_patch_proposal(proposal, temp_model_dir)
    proposal_path = temp_model_dir / "patch-proposals" / f"{proposal_id}.md"
    transition_patch_proposal_status(proposal_path, "accepted")


def _repo_from_model(model_dir: Path) -> str:
    return str(model_dir.parent)


def test_proposal_list_empty(temp_model_dir: Path) -> None:
    result = runner.invoke(app, ["proposal", "list", "--repo", _repo_from_model(temp_model_dir)])
    assert result.exit_code == 0
    assert "No PatchProposals found" in result.output or "No patch-proposals" in result.output


def test_proposal_list_with_proposals(temp_model_dir: Path) -> None:
    op = PatchOperation(op="update_object", object_id="DOMAIN-TEST", target_path="name", after="X")
    _create_accepted_proposal(temp_model_dir, "PP-LIST-001", [op])

    result = runner.invoke(app, ["proposal", "list", "--repo", _repo_from_model(temp_model_dir)])
    assert result.exit_code == 0
    assert "PP-LIST-001" in result.output
    assert "accepted" in result.output


def test_proposal_show(temp_model_dir: Path) -> None:
    op = PatchOperation(op="update_object", object_id="DOMAIN-TEST", target_path="name", after="X")
    _create_accepted_proposal(temp_model_dir, "PP-SHOW-001", [op])

    result = runner.invoke(
        app, ["proposal", "show", "PP-SHOW-001", "--repo", _repo_from_model(temp_model_dir)]
    )
    assert result.exit_code == 0
    assert "PP-SHOW-001" in result.output
    assert "update_object" in result.output


def test_proposal_validate_valid(temp_model_dir: Path) -> None:
    op = PatchOperation(op="update_object", object_id="DOMAIN-TEST", target_path="name", after="X")
    _create_accepted_proposal(temp_model_dir, "PP-VAL-001", [op])

    result = runner.invoke(
        app, ["proposal", "validate", "PP-VAL-001", "--repo", _repo_from_model(temp_model_dir)]
    )
    assert result.exit_code == 0
    assert "Errors: 0" in result.output


def test_proposal_validate_invalid(temp_model_dir: Path) -> None:
    # Empty operations = invalid
    proposal = build_patch_proposal("PP-VAL-002", [])
    write_patch_proposal(proposal, temp_model_dir)

    result = runner.invoke(
        app, ["proposal", "validate", "PP-VAL-002", "--repo", _repo_from_model(temp_model_dir)]
    )
    assert result.exit_code == 1
    assert "PATCH_OPERATIONS_EM" in result.output


def test_proposal_apply_dry_run(temp_model_dir: Path) -> None:
    op = PatchOperation(
        op="create_object",
        object_id="SYS-DRY",
        object_type="System",
        after={"id": "SYS-DRY", "type": "System", "status": "draft"},
    )
    _create_accepted_proposal(temp_model_dir, "PP-DRY-001", [op])

    result = runner.invoke(
        app,
        [
            "proposal",
            "apply",
            "PP-DRY-001",
            "--repo",
            _repo_from_model(temp_model_dir),
            "--dry-run",
        ],
    )
    assert result.exit_code == 0
    assert "Dry-run" in result.output
    assert "would_create" in result.output
    # File should NOT exist after dry-run
    assert not (temp_model_dir / "systems" / "SYS-DRY.md").exists()


def test_proposal_apply_create_object(temp_model_dir: Path) -> None:
    op = PatchOperation(
        op="create_object",
        object_id="SYS-NEW-CLI",
        object_type="System",
        after={"id": "SYS-NEW-CLI", "type": "System", "status": "draft"},
    )
    _create_accepted_proposal(temp_model_dir, "PP-APP-001", [op])

    result = runner.invoke(
        app, ["proposal", "apply", "PP-APP-001", "--repo", _repo_from_model(temp_model_dir)]
    )
    assert result.exit_code == 0
    assert "Applied PP-APP-001" in result.output
    assert (temp_model_dir / "systems" / "SYS-NEW-CLI.md").exists()


def test_proposal_apply_rejects_unaccepted(temp_model_dir: Path) -> None:
    op = PatchOperation(op="update_object", object_id="DOMAIN-TEST", target_path="name", after="X")
    proposal = build_patch_proposal("PP-REJ-001", [op])
    write_patch_proposal(proposal, temp_model_dir)
    # Leave status as pending_review

    result = runner.invoke(
        app, ["proposal", "apply", "PP-REJ-001", "--repo", _repo_from_model(temp_model_dir)]
    )
    assert result.exit_code == 1
    assert "Only 'accepted'" in result.output
