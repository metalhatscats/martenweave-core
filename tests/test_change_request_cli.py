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


class TestChangeRequestApproveRejectCli:
    # -- approve tests ------------------------------------------------------

    def test_cr_approve(self, tmp_path: Path) -> None:
        model_dir = tmp_path / "model"
        model_dir.mkdir()
        repo_root = tmp_path

        runner.invoke(
            app,
            [
                "change-request",
                "create",
                "--id",
                "CR-APPROVE-001",
                "--title",
                "Approve Test",
                "--repo",
                str(repo_root),
            ],
        )

        result = runner.invoke(
            app,
            [
                "change-request",
                "approve",
                "CR-APPROVE-001",
                "--repo",
                str(repo_root),
                "--approver",
                "alice",
            ],
        )
        assert result.exit_code == 0
        assert "approved" in result.output
        assert "alice" in result.output

        result = runner.invoke(
            app,
            [
                "change-request",
                "show",
                "CR-APPROVE-001",
                "--repo",
                str(repo_root),
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["status"] == "approved"
        assert len(data["approvals"]) == 1
        assert data["approvals"][0]["approver"] == "alice"
        assert data["approvals"][0]["decision"] == "approved"

    def test_cr_approve_json(self, tmp_path: Path) -> None:
        model_dir = tmp_path / "model"
        model_dir.mkdir()
        repo_root = tmp_path

        runner.invoke(
            app,
            [
                "change-request",
                "create",
                "--id",
                "CR-APPROVE-JSON-001",
                "--title",
                "Approve JSON",
                "--repo",
                str(repo_root),
            ],
        )

        result = runner.invoke(
            app,
            [
                "change-request",
                "approve",
                "CR-APPROVE-JSON-001",
                "--repo",
                str(repo_root),
                "--approver",
                "bob",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["status"] == "approved"
        assert data["approvals"][0]["approver"] == "bob"
        assert data["approvals"][0]["decision"] == "approved"

    def test_cr_approve_already_approved_is_blocked(self, tmp_path: Path) -> None:
        model_dir = tmp_path / "model"
        model_dir.mkdir()
        repo_root = tmp_path

        runner.invoke(
            app,
            [
                "change-request",
                "create",
                "--id",
                "CR-APPROVE-BLOCK-001",
                "--title",
                "Already Approved",
                "--repo",
                str(repo_root),
            ],
        )

        runner.invoke(
            app,
            [
                "change-request",
                "approve",
                "CR-APPROVE-BLOCK-001",
                "--repo",
                str(repo_root),
                "--approver",
                "alice",
            ],
        )

        result = runner.invoke(
            app,
            [
                "change-request",
                "approve",
                "CR-APPROVE-BLOCK-001",
                "--repo",
                str(repo_root),
                "--approver",
                "bob",
            ],
        )
        assert result.exit_code == 1
        assert "Invalid transition" in result.output
        assert "approved" in result.output

    def test_cr_approve_rejected_is_blocked(self, tmp_path: Path) -> None:
        model_dir = tmp_path / "model"
        model_dir.mkdir()
        repo_root = tmp_path

        runner.invoke(
            app,
            [
                "change-request",
                "create",
                "--id",
                "CR-APPROVE-REJ-001",
                "--title",
                "Rejected CR",
                "--repo",
                str(repo_root),
            ],
        )

        runner.invoke(
            app,
            [
                "change-request",
                "reject",
                "CR-APPROVE-REJ-001",
                "--repo",
                str(repo_root),
                "--approver",
                "bob",
            ],
        )

        result = runner.invoke(
            app,
            [
                "change-request",
                "approve",
                "CR-APPROVE-REJ-001",
                "--repo",
                str(repo_root),
                "--approver",
                "alice",
            ],
        )
        assert result.exit_code == 1
        assert "Invalid transition" in result.output

    def test_cr_approve_implemented_is_blocked(self, tmp_path: Path) -> None:
        model_dir = tmp_path / "model"
        model_dir.mkdir()
        repo_root = tmp_path

        runner.invoke(
            app,
            [
                "change-request",
                "create",
                "--id",
                "CR-APPROVE-IMPL-001",
                "--title",
                "Implemented CR",
                "--repo",
                str(repo_root),
                "--status",
                "implemented",
            ],
        )

        result = runner.invoke(
            app,
            [
                "change-request",
                "approve",
                "CR-APPROVE-IMPL-001",
                "--repo",
                str(repo_root),
                "--approver",
                "alice",
            ],
        )
        assert result.exit_code == 1
        assert "Invalid transition" in result.output

    def test_cr_approve_missing(self, tmp_path: Path) -> None:
        model_dir = tmp_path / "model"
        model_dir.mkdir()
        repo_root = tmp_path

        result = runner.invoke(
            app,
            [
                "change-request",
                "approve",
                "CR-MISSING",
                "--repo",
                str(repo_root),
                "--approver",
                "alice",
            ],
        )
        assert result.exit_code == 1
        assert "not found" in result.output

    # -- reject tests -------------------------------------------------------

    def test_cr_reject(self, tmp_path: Path) -> None:
        model_dir = tmp_path / "model"
        model_dir.mkdir()
        repo_root = tmp_path

        runner.invoke(
            app,
            [
                "change-request",
                "create",
                "--id",
                "CR-REJECT-001",
                "--title",
                "Reject Test",
                "--repo",
                str(repo_root),
            ],
        )

        result = runner.invoke(
            app,
            [
                "change-request",
                "reject",
                "CR-REJECT-001",
                "--repo",
                str(repo_root),
                "--approver",
                "bob",
            ],
        )
        assert result.exit_code == 0
        assert "rejected" in result.output
        assert "bob" in result.output

        result = runner.invoke(
            app,
            [
                "change-request",
                "show",
                "CR-REJECT-001",
                "--repo",
                str(repo_root),
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["status"] == "rejected"
        assert len(data["approvals"]) == 1
        assert data["approvals"][0]["approver"] == "bob"
        assert data["approvals"][0]["decision"] == "rejected"

    def test_cr_reject_with_reason(self, tmp_path: Path) -> None:
        model_dir = tmp_path / "model"
        model_dir.mkdir()
        repo_root = tmp_path

        runner.invoke(
            app,
            [
                "change-request",
                "create",
                "--id",
                "CR-REJECT-REASON-001",
                "--title",
                "Reject With Reason",
                "--repo",
                str(repo_root),
            ],
        )

        result = runner.invoke(
            app,
            [
                "change-request",
                "reject",
                "CR-REJECT-REASON-001",
                "--repo",
                str(repo_root),
                "--approver",
                "carol",
                "--reason",
                "Insufficient evidence.",
            ],
        )
        assert result.exit_code == 0

        result = runner.invoke(
            app,
            [
                "change-request",
                "show",
                "CR-REJECT-REASON-001",
                "--repo",
                str(repo_root),
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["status"] == "rejected"
        assert data["rejection_reason"] == "Insufficient evidence."

    def test_cr_reject_json(self, tmp_path: Path) -> None:
        model_dir = tmp_path / "model"
        model_dir.mkdir()
        repo_root = tmp_path

        runner.invoke(
            app,
            [
                "change-request",
                "create",
                "--id",
                "CR-REJECT-JSON-001",
                "--title",
                "Reject JSON",
                "--repo",
                str(repo_root),
            ],
        )

        result = runner.invoke(
            app,
            [
                "change-request",
                "reject",
                "CR-REJECT-JSON-001",
                "--repo",
                str(repo_root),
                "--approver",
                "dave",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["status"] == "rejected"
        assert data["approvals"][0]["approver"] == "dave"
        assert data["approvals"][0]["decision"] == "rejected"

    def test_cr_reject_already_rejected_is_blocked(self, tmp_path: Path) -> None:
        model_dir = tmp_path / "model"
        model_dir.mkdir()
        repo_root = tmp_path

        runner.invoke(
            app,
            [
                "change-request",
                "create",
                "--id",
                "CR-REJECT-BLOCK-001",
                "--title",
                "Already Rejected",
                "--repo",
                str(repo_root),
            ],
        )

        runner.invoke(
            app,
            [
                "change-request",
                "reject",
                "CR-REJECT-BLOCK-001",
                "--repo",
                str(repo_root),
                "--approver",
                "bob",
            ],
        )

        result = runner.invoke(
            app,
            [
                "change-request",
                "reject",
                "CR-REJECT-BLOCK-001",
                "--repo",
                str(repo_root),
                "--approver",
                "alice",
            ],
        )
        assert result.exit_code == 1
        assert "Invalid transition" in result.output
        assert "rejected" in result.output

    def test_cr_reject_implemented_is_blocked(self, tmp_path: Path) -> None:
        model_dir = tmp_path / "model"
        model_dir.mkdir()
        repo_root = tmp_path

        runner.invoke(
            app,
            [
                "change-request",
                "create",
                "--id",
                "CR-REJECT-IMPL-001",
                "--title",
                "Implemented CR",
                "--repo",
                str(repo_root),
                "--status",
                "implemented",
            ],
        )

        result = runner.invoke(
            app,
            [
                "change-request",
                "reject",
                "CR-REJECT-IMPL-001",
                "--repo",
                str(repo_root),
                "--approver",
                "bob",
            ],
        )
        assert result.exit_code == 1
        assert "Invalid transition" in result.output

    def test_cr_reject_missing(self, tmp_path: Path) -> None:
        model_dir = tmp_path / "model"
        model_dir.mkdir()
        repo_root = tmp_path

        result = runner.invoke(
            app,
            [
                "change-request",
                "reject",
                "CR-MISSING",
                "--repo",
                str(repo_root),
                "--approver",
                "bob",
            ],
        )
        assert result.exit_code == 1
        assert "not found" in result.output

    # -- transition tests: approved → rejected ------------------------------

    def test_cr_reject_approved_is_allowed(self, tmp_path: Path) -> None:
        model_dir = tmp_path / "model"
        model_dir.mkdir()
        repo_root = tmp_path

        runner.invoke(
            app,
            [
                "change-request",
                "create",
                "--id",
                "CR-APPROVED-TO-REJECT-001",
                "--title",
                "Approved Then Rejected",
                "--repo",
                str(repo_root),
            ],
        )

        runner.invoke(
            app,
            [
                "change-request",
                "approve",
                "CR-APPROVED-TO-REJECT-001",
                "--repo",
                str(repo_root),
                "--approver",
                "alice",
            ],
        )

        result = runner.invoke(
            app,
            [
                "change-request",
                "reject",
                "CR-APPROVED-TO-REJECT-001",
                "--repo",
                str(repo_root),
                "--approver",
                "bob",
                "--reason",
                "Reversing decision.",
            ],
        )
        assert result.exit_code == 0
        assert "rejected" in result.output

        result = runner.invoke(
            app,
            [
                "change-request",
                "show",
                "CR-APPROVED-TO-REJECT-001",
                "--repo",
                str(repo_root),
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["status"] == "rejected"
        assert len(data["approvals"]) == 2
        assert data["approvals"][0]["decision"] == "approved"
        assert data["approvals"][1]["decision"] == "rejected"
        assert data["rejection_reason"] == "Reversing decision."
