"""Tests for ChangeRequest CLI commands (issue #29)."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from modelops_core.cli import app

runner = CliRunner()


def test_cr_create_and_list(tmp_path: Path) -> None:
    model_dir = tmp_path / "model"
    model_dir.mkdir()
    repo_root = tmp_path

    result = runner.invoke(
        app,
        [
            "change-request",
            "create",
            "--id",
            "CR-TEST-001",
            "--title",
            "Test Change",
            "--repo",
            str(repo_root),
            "--requester",
            "alice",
            "--reason",
            "Fix mapping",
            "--affected-object",
            "FEP-1",
        ],
    )
    assert result.exit_code == 0
    assert "CR-TEST-001" in result.output

    result = runner.invoke(
        app,
        ["change-request", "list", "--repo", str(repo_root)],
    )
    assert result.exit_code == 0
    assert "CR-TEST-001" in result.output
    assert "pending" in result.output


def test_cr_show(tmp_path: Path) -> None:
    model_dir = tmp_path / "model"
    model_dir.mkdir()
    repo_root = tmp_path

    runner.invoke(
        app,
        [
            "change-request",
            "create",
            "--id",
            "CR-TEST-002",
            "--title",
            "Show Test",
            "--repo",
            str(repo_root),
            "--requester",
            "bob",
            "--priority",
            "high",
        ],
    )

    result = runner.invoke(
        app,
        ["change-request", "show", "CR-TEST-002", "--repo", str(repo_root)],
    )
    assert result.exit_code == 0
    assert "Show Test" in result.output
    assert "bob" in result.output
    assert "high" in result.output


def test_cr_show_json(tmp_path: Path) -> None:
    model_dir = tmp_path / "model"
    model_dir.mkdir()
    repo_root = tmp_path

    runner.invoke(
        app,
        [
            "change-request",
            "create",
            "--id",
            "CR-TEST-003",
            "--title",
            "JSON Test",
            "--repo",
            str(repo_root),
        ],
    )

    result = runner.invoke(
        app,
        ["change-request", "show", "CR-TEST-003", "--repo", str(repo_root), "--json"],
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["id"] == "CR-TEST-003"


def test_cr_update_status_valid_transition(tmp_path: Path) -> None:
    model_dir = tmp_path / "model"
    model_dir.mkdir()
    repo_root = tmp_path

    runner.invoke(
        app,
        [
            "change-request",
            "create",
            "--id",
            "CR-TEST-004",
            "--title",
            "Transition Test",
            "--repo",
            str(repo_root),
        ],
    )

    result = runner.invoke(
        app,
        [
            "change-request",
            "update-status",
            "CR-TEST-004",
            "approved",
            "--repo",
            str(repo_root),
        ],
    )
    assert result.exit_code == 0
    assert "approved" in result.output


def test_cr_update_status_invalid_transition(tmp_path: Path) -> None:
    model_dir = tmp_path / "model"
    model_dir.mkdir()
    repo_root = tmp_path

    runner.invoke(
        app,
        [
            "change-request",
            "create",
            "--id",
            "CR-TEST-005",
            "--title",
            "Invalid Transition",
            "--repo",
            str(repo_root),
            "--status",
            "approved",
        ],
    )

    result = runner.invoke(
        app,
        [
            "change-request",
            "update-status",
            "CR-TEST-005",
            "pending",
            "--repo",
            str(repo_root),
        ],
    )
    assert result.exit_code == 1
    assert "Invalid transition" in result.output


def test_cr_create_invalid_id(tmp_path: Path) -> None:
    model_dir = tmp_path / "model"
    model_dir.mkdir()
    repo_root = tmp_path

    result = runner.invoke(
        app,
        [
            "change-request",
            "create",
            "--id",
            "bad-id",
            "--title",
            "Bad ID",
            "--repo",
            str(repo_root),
        ],
    )
    assert result.exit_code == 1
    assert "Invalid ChangeRequest ID" in result.output


def test_cr_create_invalid_status(tmp_path: Path) -> None:
    model_dir = tmp_path / "model"
    model_dir.mkdir()
    repo_root = tmp_path

    result = runner.invoke(
        app,
        [
            "change-request",
            "create",
            "--id",
            "CR-TEST-006",
            "--title",
            "Bad Status",
            "--repo",
            str(repo_root),
            "--status",
            "unknown",
        ],
    )
    assert result.exit_code == 1
    assert "Invalid status" in result.output


def test_cr_show_not_found(tmp_path: Path) -> None:
    model_dir = tmp_path / "model"
    model_dir.mkdir()
    repo_root = tmp_path

    result = runner.invoke(
        app,
        ["change-request", "show", "CR-MISSING", "--repo", str(repo_root)],
    )
    assert result.exit_code == 1
    assert "not found" in result.output


def test_cr_list_json(tmp_path: Path) -> None:
    model_dir = tmp_path / "model"
    model_dir.mkdir()
    repo_root = tmp_path

    runner.invoke(
        app,
        [
            "change-request",
            "create",
            "--id",
            "CR-TEST-007",
            "--title",
            "List JSON",
            "--repo",
            str(repo_root),
        ],
    )

    result = runner.invoke(
        app,
        ["change-request", "list", "--repo", str(repo_root), "--json"],
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert len(data) == 1
    assert data[0]["id"] == "CR-TEST-007"


def test_cr_links_and_fields(tmp_path: Path) -> None:
    model_dir = tmp_path / "model"
    model_dir.mkdir()
    repo_root = tmp_path

    result = runner.invoke(
        app,
        [
            "change-request",
            "create",
            "--id",
            "CR-TEST-008",
            "--title",
            "Linked CR",
            "--repo",
            str(repo_root),
            "--affected-object",
            "FEP-1",
            "--affected-object",
            "FEP-2",
            "--linked-proposal",
            "PP-001",
            "--related-issue",
            "ISS-001",
            "--related-decision",
            "DEC-001",
            "--approver",
            "alice",
            "--approver",
            "bob",
            "--source-evidence",
            "Workshop notes",
        ],
    )
    assert result.exit_code == 0

    result = runner.invoke(
        app,
        ["change-request", "show", "CR-TEST-008", "--repo", str(repo_root), "--json"],
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["affected_objects"] == ["FEP-1", "FEP-2"]
    assert data["linked_proposals"] == ["PP-001"]
    assert data["related_issues"] == ["ISS-001"]
    assert data["related_decisions"] == ["DEC-001"]
    assert data["approvers"] == ["alice", "bob"]
    assert data["source_evidence"] == "Workshop notes"
