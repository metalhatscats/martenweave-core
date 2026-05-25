"""Tests for git-bundle change bundle generation."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from modelops_core.bundle import create_git_bundle
from modelops_core.cli import app
from modelops_core.patching.patch_model import PatchOperation
from modelops_core.patching.patch_proposal_service import (
    build_patch_proposal,
    write_patch_proposal,
)

runner = CliRunner()


def test_bundle_creates_files(temp_model_dir: Path) -> None:
    op = PatchOperation(
        op="update_object",
        object_id="DOMAIN-TEST",
        target_path="name",
        after="Updated Domain Name",
    )
    proposal = build_patch_proposal("PP-BUNDLE-001", [op], affected_objects=["DOMAIN-TEST"])
    write_patch_proposal(proposal, temp_model_dir)

    repo_root = temp_model_dir.parent
    result = create_git_bundle(repo_root, "PP-BUNDLE-001")

    assert result.bundle_dir.exists()
    assert result.bundle_json_path is not None
    assert result.bundle_json_path.exists()
    assert result.readme_path is not None
    assert result.readme_path.exists()
    assert result.pr_body_path is not None
    assert result.pr_body_path.exists()
    assert result.changed_files_dir is not None
    assert result.changed_files_dir.exists()


def test_bundle_json_has_expected_keys(temp_model_dir: Path) -> None:
    op = PatchOperation(
        op="update_object",
        object_id="DOMAIN-TEST",
        target_path="name",
        after="Updated Domain Name",
    )
    proposal = build_patch_proposal("PP-BUNDLE-002", [op], affected_objects=["DOMAIN-TEST"])
    write_patch_proposal(proposal, temp_model_dir)

    repo_root = temp_model_dir.parent
    result = create_git_bundle(repo_root, "PP-BUNDLE-002")

    data = json.loads(result.bundle_json_path.read_text())
    assert data["proposal_id"] == "PP-BUNDLE-002"
    assert "risk" in data
    assert "impact" in data
    assert "validation" in data
    assert "operations_count" in data
    assert "affected_objects" in data
    assert "copied_files" in data


def test_bundle_copies_changed_files(temp_model_dir: Path) -> None:
    op = PatchOperation(
        op="update_object",
        object_id="DOMAIN-TEST",
        target_path="name",
        after="Updated Domain Name",
    )
    proposal = build_patch_proposal("PP-BUNDLE-003", [op], affected_objects=["DOMAIN-TEST"])
    write_patch_proposal(proposal, temp_model_dir)

    repo_root = temp_model_dir.parent
    result = create_git_bundle(repo_root, "PP-BUNDLE-003")

    copied = list(result.changed_files_dir.iterdir())
    assert len(copied) >= 1
    names = {f.name for f in copied}
    assert "DOMAIN-TEST.md" in names


def test_bundle_commit_message_includes_proposal_id(temp_model_dir: Path) -> None:
    op = PatchOperation(
        op="update_object",
        object_id="DOMAIN-TEST",
        target_path="name",
        after="Updated Domain Name",
    )
    proposal = build_patch_proposal("PP-BUNDLE-004", [op], affected_objects=["DOMAIN-TEST"])
    write_patch_proposal(proposal, temp_model_dir)

    repo_root = temp_model_dir.parent
    result = create_git_bundle(repo_root, "PP-BUNDLE-004")

    commit_path = result.bundle_dir / "COMMIT_MESSAGE.txt"
    assert commit_path.exists()
    assert "PP-BUNDLE-004" in commit_path.read_text()


def test_bundle_raises_on_missing_proposal(temp_model_dir: Path) -> None:
    repo_root = temp_model_dir.parent
    with pytest.raises(ValueError, match="PatchProposal not found"):
        create_git_bundle(repo_root, "PP-MISSING")


def test_cli_git_bundle(temp_model_dir: Path) -> None:
    op = PatchOperation(
        op="update_object",
        object_id="DOMAIN-TEST",
        target_path="name",
        after="Updated Domain Name",
    )
    proposal = build_patch_proposal("PP-BUNDLE-CLI", [op], affected_objects=["DOMAIN-TEST"])
    write_patch_proposal(proposal, temp_model_dir)

    repo = str(temp_model_dir.parent)
    result = runner.invoke(app, ["git-bundle", "PP-BUNDLE-CLI", "--repo", repo])
    assert result.exit_code == 0
    assert "Bundle created" in result.output
    assert "PP-BUNDLE-CLI" in result.output


def test_cli_git_bundle_json(temp_model_dir: Path) -> None:
    op = PatchOperation(
        op="update_object",
        object_id="DOMAIN-TEST",
        target_path="name",
        after="Updated Domain Name",
    )
    proposal = build_patch_proposal("PP-BUNDLE-JSON", [op], affected_objects=["DOMAIN-TEST"])
    write_patch_proposal(proposal, temp_model_dir)

    repo = str(temp_model_dir.parent)
    result = runner.invoke(
        app, ["git-bundle", "PP-BUNDLE-JSON", "--repo", repo, "--json"]
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["proposal_id"] == "PP-BUNDLE-JSON"
    assert "bundle_dir" in data


def test_cli_git_bundle_missing_proposal(temp_model_dir: Path) -> None:
    repo = str(temp_model_dir.parent)
    result = runner.invoke(app, ["git-bundle", "PP-NOPE", "--repo", repo])
    assert result.exit_code == 1
    assert "PatchProposal not found" in result.output
