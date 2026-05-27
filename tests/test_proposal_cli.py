"""Tests for proposal CLI commands."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from modelops_core.cli import app
from modelops_core.patching.patch_model import PatchOperation
from modelops_core.patching.patch_proposal_service import (
    build_patch_proposal,
    transition_patch_proposal_status,
    write_patch_proposal,
)
from modelops_core.repository import parse_file

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
        app,
        [
            "proposal",
            "apply",
            "PP-APP-001",
            "--repo",
            _repo_from_model(temp_model_dir),
            "--apply",
        ],
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
        app,
        [
            "proposal",
            "apply",
            "PP-REJ-001",
            "--repo",
            _repo_from_model(temp_model_dir),
            "--apply",
        ],
    )
    assert result.exit_code == 1
    assert "Only 'accepted'" in result.output


# proposal diff tests ---------------------------------------------------------


def test_proposal_diff_update_object(temp_model_dir: Path) -> None:
    op = PatchOperation(
        op="update_object", object_id="DOMAIN-TEST", target_path="name", after="New Name"
    )
    _create_accepted_proposal(temp_model_dir, "PP-DIFF-001", [op])

    result = runner.invoke(
        app, ["proposal", "diff", "PP-DIFF-001", "--repo", _repo_from_model(temp_model_dir)]
    )
    assert result.exit_code == 0
    assert "update_object" in result.output
    assert "New Name" in result.output


def test_proposal_diff_create_object(temp_model_dir: Path) -> None:
    op = PatchOperation(
        op="create_object",
        object_id="SYS-DIFF",
        object_type="System",
        after={"id": "SYS-DIFF", "type": "System", "status": "draft"},
    )
    _create_accepted_proposal(temp_model_dir, "PP-DIFF-002", [op])

    result = runner.invoke(
        app, ["proposal", "diff", "PP-DIFF-002", "--repo", _repo_from_model(temp_model_dir)]
    )
    assert result.exit_code == 0
    assert "create_object" in result.output
    assert "SYS-DIFF" in result.output


def test_proposal_diff_json(temp_model_dir: Path) -> None:
    op = PatchOperation(
        op="update_object", object_id="DOMAIN-TEST", target_path="name", after="Json Name"
    )
    _create_accepted_proposal(temp_model_dir, "PP-DIFF-003", [op])

    result = runner.invoke(
        app,
        [
            "proposal",
            "diff",
            "PP-DIFF-003",
            "--json",
            "--repo",
            _repo_from_model(temp_model_dir),
        ],
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["proposal_id"] == "PP-DIFF-003"
    assert len(data["diffs"]) == 1
    assert data["diffs"][0]["op"] == "update_object"
    assert data["diffs"][0]["after"] == "Json Name"


def test_proposal_diff_not_found(temp_model_dir: Path) -> None:
    result = runner.invoke(
        app, ["proposal", "diff", "PP-MISSING", "--repo", _repo_from_model(temp_model_dir)]
    )
    assert result.exit_code == 1
    assert "not found" in result.output


# Proposal expiration tests ---------------------------------------------------


def test_proposal_list_stale_filters_expired(temp_model_dir: Path) -> None:
    from datetime import UTC, datetime

    op = PatchOperation(op="update_object", object_id="DOMAIN-TEST", target_path="name", after="X")
    _create_accepted_proposal(temp_model_dir, "PP-EXPIRED-001", [op])
    # Set expires_at to past
    proposal_path = temp_model_dir / "patch-proposals" / "PP-EXPIRED-001.md"
    text = proposal_path.read_text(encoding="utf-8")
    past = datetime(2020, 1, 1, tzinfo=UTC).isoformat()
    text = text.replace(
        "status: accepted", f"status: accepted\nexpires_at: {past}"
    )
    proposal_path.write_text(text, encoding="utf-8")

    # Create a non-expired proposal
    _create_accepted_proposal(temp_model_dir, "PP-FRESH-001", [op])

    result = runner.invoke(
        app, ["proposal", "list", "--stale", "--repo", _repo_from_model(temp_model_dir)]
    )
    assert result.exit_code == 0
    assert "PP-EXPIRED-001" in result.output
    assert "PP-FRESH-001" not in result.output


def test_proposal_show_displays_expiration(temp_model_dir: Path) -> None:
    op = PatchOperation(op="update_object", object_id="DOMAIN-TEST", target_path="name", after="X")
    _create_accepted_proposal(temp_model_dir, "PP-EXP-SHOW-001", [op])
    proposal_path = temp_model_dir / "patch-proposals" / "PP-EXP-SHOW-001.md"
    text = proposal_path.read_text(encoding="utf-8")
    text = text.replace(
        "status: accepted", "status: accepted\nexpires_at: 2025-12-31T23:59:59+00:00"
    )
    proposal_path.write_text(text, encoding="utf-8")

    result = runner.invoke(
        app, ["proposal", "show", "PP-EXP-SHOW-001", "--repo", _repo_from_model(temp_model_dir)]
    )
    assert result.exit_code == 0
    assert "Expires at" in result.output
    assert "2025-12-31" in result.output


def test_proposal_validate_warns_on_expired(temp_model_dir: Path) -> None:
    from datetime import UTC, datetime

    op = PatchOperation(op="update_object", object_id="DOMAIN-TEST", target_path="name", after="X")
    _create_accepted_proposal(temp_model_dir, "PP-EXP-VAL-001", [op])
    proposal_path = temp_model_dir / "patch-proposals" / "PP-EXP-VAL-001.md"
    text = proposal_path.read_text(encoding="utf-8")
    past = datetime(2020, 1, 1, tzinfo=UTC).isoformat()
    text = text.replace(
        "status: accepted", f"status: accepted\nexpires_at: {past}"
    )
    proposal_path.write_text(text, encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "proposal",
            "validate",
            "PP-EXP-VAL-001",
            "--json",
            "--repo",
            _repo_from_model(temp_model_dir),
        ],
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert any(r["code"] == "PATCH_PROPOSAL_EXPIRED" for r in data["results"])


# --json flag tests -----------------------------------------------------------


def test_proposal_list_json_empty(temp_model_dir: Path) -> None:
    result = runner.invoke(
        app, ["proposal", "list", "--json", "--repo", _repo_from_model(temp_model_dir)]
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data == []


def test_proposal_list_json_with_proposals(temp_model_dir: Path) -> None:
    op = PatchOperation(op="update_object", object_id="DOMAIN-TEST", target_path="name", after="X")
    _create_accepted_proposal(temp_model_dir, "PP-JSON-LIST-001", [op])

    result = runner.invoke(
        app, ["proposal", "list", "--json", "--repo", _repo_from_model(temp_model_dir)]
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert len(data) == 1
    assert data[0]["id"] == "PP-JSON-LIST-001"
    assert data[0]["status"] == "accepted"
    assert data[0]["applied"] is False


def test_proposal_show_json(temp_model_dir: Path) -> None:
    op = PatchOperation(op="update_object", object_id="DOMAIN-TEST", target_path="name", after="X")
    _create_accepted_proposal(temp_model_dir, "PP-JSON-SHOW-001", [op])

    result = runner.invoke(
        app,
        [
            "proposal",
            "show",
            "PP-JSON-SHOW-001",
            "--json",
            "--repo",
            _repo_from_model(temp_model_dir),
        ],
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["id"] == "PP-JSON-SHOW-001"
    assert data["status"] == "accepted"
    assert "operations" in data


def test_proposal_validate_json_valid(temp_model_dir: Path) -> None:
    op = PatchOperation(op="update_object", object_id="DOMAIN-TEST", target_path="name", after="X")
    _create_accepted_proposal(temp_model_dir, "PP-JSON-VAL-001", [op])

    result = runner.invoke(
        app,
        [
            "proposal",
            "validate",
            "PP-JSON-VAL-001",
            "--json",
            "--repo",
            _repo_from_model(temp_model_dir),
        ],
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["proposal_id"] == "PP-JSON-VAL-001"
    assert data["error_count"] == 0
    assert "results" in data


def test_proposal_validate_json_invalid(temp_model_dir: Path) -> None:
    proposal = build_patch_proposal("PP-JSON-VAL-002", [])
    write_patch_proposal(proposal, temp_model_dir)

    result = runner.invoke(
        app,
        [
            "proposal",
            "validate",
            "PP-JSON-VAL-002",
            "--json",
            "--repo",
            _repo_from_model(temp_model_dir),
        ],
    )
    assert result.exit_code == 1
    data = json.loads(result.output)
    assert data["proposal_id"] == "PP-JSON-VAL-002"
    assert data["error_count"] > 0
    assert "results" in data


def test_proposal_apply_dry_run_json(temp_model_dir: Path) -> None:
    op = PatchOperation(
        op="create_object",
        object_id="SYS-JSON-DRY",
        object_type="System",
        after={"id": "SYS-JSON-DRY", "type": "System", "status": "draft"},
    )
    _create_accepted_proposal(temp_model_dir, "PP-JSON-DRY-001", [op])

    result = runner.invoke(
        app,
        [
            "proposal",
            "apply",
            "PP-JSON-DRY-001",
            "--repo",
            _repo_from_model(temp_model_dir),
            "--dry-run",
            "--json",
        ],
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["proposal_id"] == "PP-JSON-DRY-001"
    assert data["dry_run"] is True
    assert "would_change" in data
    assert "risk_level" in data


def test_proposal_apply_default_is_dry_run(temp_model_dir: Path) -> None:
    """Default proposal apply should be dry-run without mutating files."""
    op = PatchOperation(
        op="create_object",
        object_id="SYS-DEFAULT-DRY",
        object_type="System",
        after={"id": "SYS-DEFAULT-DRY", "type": "System", "status": "draft"},
    )
    _create_accepted_proposal(temp_model_dir, "PP-DEFAULT-DRY-001", [op])

    result = runner.invoke(
        app,
        [
            "proposal",
            "apply",
            "PP-DEFAULT-DRY-001",
            "--repo",
            _repo_from_model(temp_model_dir),
        ],
    )
    assert result.exit_code == 0
    assert "Dry-run" in result.output
    assert "--apply" in result.output
    # File should NOT exist after default dry-run
    assert not (temp_model_dir / "systems" / "SYS-DEFAULT-DRY.md").exists()


def test_proposal_accept_with_reviewer_notes(temp_model_dir: Path) -> None:
    op = PatchOperation(
        op="update_object", object_id="DOMAIN-TEST", target_path="name", after="New Name"
    )
    proposal = build_patch_proposal("PP-REVIEW-001", [op])
    write_patch_proposal(proposal, temp_model_dir)
    proposal_path = temp_model_dir / "patch-proposals" / "PP-REVIEW-001.md"

    transition_patch_proposal_status(
        proposal_path,
        "accepted",
        reviewer="alice",
        reviewer_notes="Looks good, minor naming change.",
    )

    parsed = parse_file(proposal_path)
    assert parsed.frontmatter is not None
    assert parsed.frontmatter["status"] == "accepted"
    assert parsed.frontmatter["reviewer"] == "alice"
    assert parsed.frontmatter["reviewer_notes"] == "Looks good, minor naming change."
    assert parsed.frontmatter["reviewed_at"] is not None


def test_proposal_reject_with_reason(temp_model_dir: Path) -> None:
    op = PatchOperation(
        op="update_object", object_id="DOMAIN-TEST", target_path="name", after="Bad Name"
    )
    proposal = build_patch_proposal("PP-REJECT-001", [op])
    write_patch_proposal(proposal, temp_model_dir)
    proposal_path = temp_model_dir / "patch-proposals" / "PP-REJECT-001.md"

    transition_patch_proposal_status(
        proposal_path,
        "rejected",
        reviewer="bob",
        rejection_reason="Name does not follow naming conventions.",
    )

    parsed = parse_file(proposal_path)
    assert parsed.frontmatter is not None
    assert parsed.frontmatter["status"] == "rejected"
    assert parsed.frontmatter["reviewer"] == "bob"
    assert parsed.frontmatter["rejection_reason"] == "Name does not follow naming conventions."
    assert parsed.frontmatter["reviewed_at"] is not None


def test_proposal_show_reviewer_metadata(temp_model_dir: Path) -> None:
    op = PatchOperation(
        op="update_object", object_id="DOMAIN-TEST", target_path="name", after="Updated"
    )
    proposal = build_patch_proposal("PP-SHOW-REVIEW-001", [op])
    write_patch_proposal(proposal, temp_model_dir)
    proposal_path = temp_model_dir / "patch-proposals" / "PP-SHOW-REVIEW-001.md"
    transition_patch_proposal_status(
        proposal_path,
        "rejected",
        reviewer="carol",
        reviewer_notes="Needs more context.",
        rejection_reason="Insufficient evidence.",
    )

    result = runner.invoke(
        app, ["proposal", "show", "PP-SHOW-REVIEW-001", "--repo", _repo_from_model(temp_model_dir)]
    )
    assert result.exit_code == 0
    assert "carol" in result.output
    assert "Needs more context." in result.output
    assert "Insufficient evidence." in result.output


def test_proposal_list_shows_reviewer(temp_model_dir: Path) -> None:
    op = PatchOperation(
        op="update_object", object_id="DOMAIN-TEST", target_path="name", after="X"
    )
    proposal = build_patch_proposal("PP-LIST-REVIEW-001", [op])
    write_patch_proposal(proposal, temp_model_dir)
    proposal_path = temp_model_dir / "patch-proposals" / "PP-LIST-REVIEW-001.md"
    transition_patch_proposal_status(proposal_path, "accepted", reviewer="dave")

    result = runner.invoke(app, ["proposal", "list", "--repo", _repo_from_model(temp_model_dir)])
    assert result.exit_code == 0
    assert "PP-LIST-REVIEW-001" in result.output
    assert "dave" in result.output


class TestProposalAcceptRejectCli:
    def test_proposal_accept_cli(self, temp_model_dir: Path) -> None:
        op = PatchOperation(
            op="update_object", object_id="DOMAIN-TEST", target_path="name", after="New Name"
        )
        proposal = build_patch_proposal("PP-ACCEPT-CLI-001", [op])
        write_patch_proposal(proposal, temp_model_dir)

        result = runner.invoke(
            app,
            [
                "proposal",
                "accept",
                "PP-ACCEPT-CLI-001",
                "--repo",
                _repo_from_model(temp_model_dir),
                "--reviewer",
                "alice",
                "--notes",
                "Looks good.",
            ],
        )
        assert result.exit_code == 0
        assert "accepted" in result.output

        proposal_path = temp_model_dir / "patch-proposals" / "PP-ACCEPT-CLI-001.md"
        parsed = parse_file(proposal_path)
        assert parsed.frontmatter is not None
        assert parsed.frontmatter["status"] == "accepted"
        assert parsed.frontmatter["reviewer"] == "alice"
        assert parsed.frontmatter["reviewer_notes"] == "Looks good."
        assert parsed.frontmatter["reviewed_at"] is not None

    def test_proposal_accept_cli_json(self, temp_model_dir: Path) -> None:
        op = PatchOperation(
            op="update_object", object_id="DOMAIN-TEST", target_path="name", after="New Name"
        )
        proposal = build_patch_proposal("PP-ACCEPT-CLI-002", [op])
        write_patch_proposal(proposal, temp_model_dir)

        result = runner.invoke(
            app,
            [
                "proposal",
                "accept",
                "PP-ACCEPT-CLI-002",
                "--repo",
                _repo_from_model(temp_model_dir),
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["proposal_id"] == "PP-ACCEPT-CLI-002"
        assert data["status"] == "accepted"

    def test_proposal_accept_cli_missing(self, temp_model_dir: Path) -> None:
        result = runner.invoke(
            app,
            [
                "proposal",
                "accept",
                "PP-MISSING",
                "--repo",
                _repo_from_model(temp_model_dir),
            ],
        )
        assert result.exit_code == 1
        assert "not found" in result.output

    def test_proposal_reject_cli(self, temp_model_dir: Path) -> None:
        op = PatchOperation(
            op="update_object", object_id="DOMAIN-TEST", target_path="name", after="Bad Name"
        )
        proposal = build_patch_proposal("PP-REJECT-CLI-001", [op])
        write_patch_proposal(proposal, temp_model_dir)

        result = runner.invoke(
            app,
            [
                "proposal",
                "reject",
                "PP-REJECT-CLI-001",
                "--repo",
                _repo_from_model(temp_model_dir),
                "--reviewer",
                "bob",
                "--reason",
                "Naming violation.",
                "--notes",
                "Please fix and resubmit.",
            ],
        )
        assert result.exit_code == 0
        assert "rejected" in result.output

        proposal_path = temp_model_dir / "patch-proposals" / "PP-REJECT-CLI-001.md"
        parsed = parse_file(proposal_path)
        assert parsed.frontmatter is not None
        assert parsed.frontmatter["status"] == "rejected"
        assert parsed.frontmatter["reviewer"] == "bob"
        assert parsed.frontmatter["rejection_reason"] == "Naming violation."
        assert parsed.frontmatter["reviewer_notes"] == "Please fix and resubmit."
        assert parsed.frontmatter["reviewed_at"] is not None

    def test_proposal_reject_cli_json(self, temp_model_dir: Path) -> None:
        op = PatchOperation(
            op="update_object", object_id="DOMAIN-TEST", target_path="name", after="Bad Name"
        )
        proposal = build_patch_proposal("PP-REJECT-CLI-002", [op])
        write_patch_proposal(proposal, temp_model_dir)

        result = runner.invoke(
            app,
            [
                "proposal",
                "reject",
                "PP-REJECT-CLI-002",
                "--repo",
                _repo_from_model(temp_model_dir),
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["proposal_id"] == "PP-REJECT-CLI-002"
        assert data["status"] == "rejected"

    def test_proposal_reject_cli_missing(self, temp_model_dir: Path) -> None:
        result = runner.invoke(
            app,
            [
                "proposal",
                "reject",
                "PP-MISSING",
                "--repo",
                _repo_from_model(temp_model_dir),
            ],
        )
        assert result.exit_code == 1
        assert "not found" in result.output

    # -- Safety / contract tests for state transitions ----------------------

    def test_proposal_accept_already_accepted_is_idempotent(self, temp_model_dir: Path) -> None:
        op = PatchOperation(
            op="update_object", object_id="DOMAIN-TEST", target_path="name", after="New Name"
        )
        _create_accepted_proposal(temp_model_dir, "PP-ACCEPT-IDEM-001", [op])

        result = runner.invoke(
            app,
            [
                "proposal",
                "accept",
                "PP-ACCEPT-IDEM-001",
                "--repo",
                _repo_from_model(temp_model_dir),
                "--reviewer",
                "alice2",
            ],
        )
        assert result.exit_code == 0
        assert "accepted" in result.output

        proposal_path = temp_model_dir / "patch-proposals" / "PP-ACCEPT-IDEM-001.md"
        parsed = parse_file(proposal_path)
        assert parsed.frontmatter is not None
        assert parsed.frontmatter["status"] == "accepted"
        assert parsed.frontmatter["reviewer"] == "alice2"

    def test_proposal_accept_rejected_is_blocked(self, temp_model_dir: Path) -> None:
        op = PatchOperation(
            op="update_object", object_id="DOMAIN-TEST", target_path="name", after="Bad"
        )
        proposal = build_patch_proposal("PP-ACCEPT-BLOCK-001", [op])
        write_patch_proposal(proposal, temp_model_dir)
        proposal_path = temp_model_dir / "patch-proposals" / "PP-ACCEPT-BLOCK-001.md"
        transition_patch_proposal_status(proposal_path, "rejected", reviewer="bob")

        result = runner.invoke(
            app,
            [
                "proposal",
                "accept",
                "PP-ACCEPT-BLOCK-001",
                "--repo",
                _repo_from_model(temp_model_dir),
            ],
        )
        assert result.exit_code == 1
        assert "rejected" in result.output
        assert "recreated" in result.output

    def test_proposal_accept_applied_is_blocked(self, temp_model_dir: Path) -> None:
        op = PatchOperation(
            op="update_object", object_id="DOMAIN-TEST", target_path="name", after="X"
        )
        _create_accepted_proposal(temp_model_dir, "PP-ACCEPT-APP-001", [op])
        proposal_path = temp_model_dir / "patch-proposals" / "PP-ACCEPT-APP-001.md"
        # Mark as applied directly in frontmatter
        text = proposal_path.read_text(encoding="utf-8")
        text = text.replace(
            "status: accepted",
            "status: accepted\napplied_at: 2024-01-01T00:00:00Z",
        )
        proposal_path.write_text(text, encoding="utf-8")

        result = runner.invoke(
            app,
            [
                "proposal",
                "accept",
                "PP-ACCEPT-APP-001",
                "--repo",
                _repo_from_model(temp_model_dir),
            ],
        )
        assert result.exit_code == 1
        assert "already been applied" in result.output

    def test_proposal_reject_already_rejected_is_idempotent(self, temp_model_dir: Path) -> None:
        op = PatchOperation(
            op="update_object", object_id="DOMAIN-TEST", target_path="name", after="Bad"
        )
        proposal = build_patch_proposal("PP-REJECT-IDEM-001", [op])
        write_patch_proposal(proposal, temp_model_dir)
        proposal_path = temp_model_dir / "patch-proposals" / "PP-REJECT-IDEM-001.md"
        transition_patch_proposal_status(proposal_path, "rejected", reviewer="bob")

        result = runner.invoke(
            app,
            [
                "proposal",
                "reject",
                "PP-REJECT-IDEM-001",
                "--repo",
                _repo_from_model(temp_model_dir),
                "--reviewer",
                "bob2",
                "--reason",
                "Still bad.",
            ],
        )
        assert result.exit_code == 0
        assert "rejected" in result.output

        parsed = parse_file(proposal_path)
        assert parsed.frontmatter is not None
        assert parsed.frontmatter["status"] == "rejected"
        assert parsed.frontmatter["reviewer"] == "bob2"
        assert parsed.frontmatter["rejection_reason"] == "Still bad."

    def test_proposal_reject_accepted_is_blocked(self, temp_model_dir: Path) -> None:
        op = PatchOperation(
            op="update_object", object_id="DOMAIN-TEST", target_path="name", after="X"
        )
        _create_accepted_proposal(temp_model_dir, "PP-REJECT-BLOCK-001", [op])

        result = runner.invoke(
            app,
            [
                "proposal",
                "reject",
                "PP-REJECT-BLOCK-001",
                "--repo",
                _repo_from_model(temp_model_dir),
            ],
        )
        assert result.exit_code == 1
        assert "already accepted" in result.output

    def test_proposal_reject_applied_is_blocked(self, temp_model_dir: Path) -> None:
        op = PatchOperation(
            op="update_object", object_id="DOMAIN-TEST", target_path="name", after="X"
        )
        _create_accepted_proposal(temp_model_dir, "PP-REJECT-APP-001", [op])
        proposal_path = temp_model_dir / "patch-proposals" / "PP-REJECT-APP-001.md"
        text = proposal_path.read_text(encoding="utf-8")
        text = text.replace(
            "status: accepted",
            "status: accepted\napplied_at: 2024-01-01T00:00:00Z",
        )
        proposal_path.write_text(text, encoding="utf-8")

        result = runner.invoke(
            app,
            [
                "proposal",
                "reject",
                "PP-REJECT-APP-001",
                "--repo",
                _repo_from_model(temp_model_dir),
            ],
        )
        assert result.exit_code == 1
        assert "already been applied" in result.output

    # -- JSON contract tests for error shapes -------------------------------

    def test_proposal_accept_rejected_json_contract(self, temp_model_dir: Path) -> None:
        op = PatchOperation(
            op="update_object", object_id="DOMAIN-TEST", target_path="name", after="Bad"
        )
        proposal = build_patch_proposal("PP-ACCEPT-JSON-BLOCK-001", [op])
        write_patch_proposal(proposal, temp_model_dir)
        proposal_path = temp_model_dir / "patch-proposals" / "PP-ACCEPT-JSON-BLOCK-001.md"
        transition_patch_proposal_status(proposal_path, "rejected", reviewer="bob")

        result = runner.invoke(
            app,
            [
                "proposal",
                "accept",
                "PP-ACCEPT-JSON-BLOCK-001",
                "--repo",
                _repo_from_model(temp_model_dir),
                "--json",
            ],
        )
        assert result.exit_code == 1
        data = json.loads(result.output)
        assert data["proposal_id"] == "PP-ACCEPT-JSON-BLOCK-001"
        assert data["status"] == "rejected"
        assert "error" in data
        assert "rejected" in data["error"]

    def test_proposal_reject_accepted_json_contract(self, temp_model_dir: Path) -> None:
        op = PatchOperation(
            op="update_object", object_id="DOMAIN-TEST", target_path="name", after="X"
        )
        _create_accepted_proposal(temp_model_dir, "PP-REJECT-JSON-BLOCK-001", [op])

        result = runner.invoke(
            app,
            [
                "proposal",
                "reject",
                "PP-REJECT-JSON-BLOCK-001",
                "--repo",
                _repo_from_model(temp_model_dir),
                "--json",
            ],
        )
        assert result.exit_code == 1
        data = json.loads(result.output)
        assert data["proposal_id"] == "PP-REJECT-JSON-BLOCK-001"
        assert data["status"] == "accepted"
        assert "error" in data
        assert "accepted" in data["error"]

    def test_proposal_accept_applied_json_contract(self, temp_model_dir: Path) -> None:
        op = PatchOperation(
            op="update_object", object_id="DOMAIN-TEST", target_path="name", after="X"
        )
        _create_accepted_proposal(temp_model_dir, "PP-ACCEPT-JSON-APP-001", [op])
        proposal_path = temp_model_dir / "patch-proposals" / "PP-ACCEPT-JSON-APP-001.md"
        text = proposal_path.read_text(encoding="utf-8")
        text = text.replace(
            "status: accepted",
            "status: accepted\napplied_at: 2024-01-01T00:00:00Z",
        )
        proposal_path.write_text(text, encoding="utf-8")

        result = runner.invoke(
            app,
            [
                "proposal",
                "accept",
                "PP-ACCEPT-JSON-APP-001",
                "--repo",
                _repo_from_model(temp_model_dir),
                "--json",
            ],
        )
        assert result.exit_code == 1
        data = json.loads(result.output)
        assert data["proposal_id"] == "PP-ACCEPT-JSON-APP-001"
        assert "error" in data
        assert "applied" in data["error"]

    def test_proposal_reject_applied_json_contract(self, temp_model_dir: Path) -> None:
        op = PatchOperation(
            op="update_object", object_id="DOMAIN-TEST", target_path="name", after="X"
        )
        _create_accepted_proposal(temp_model_dir, "PP-REJECT-JSON-APP-001", [op])
        proposal_path = temp_model_dir / "patch-proposals" / "PP-REJECT-JSON-APP-001.md"
        text = proposal_path.read_text(encoding="utf-8")
        text = text.replace(
            "status: accepted",
            "status: accepted\napplied_at: 2024-01-01T00:00:00Z",
        )
        proposal_path.write_text(text, encoding="utf-8")

        result = runner.invoke(
            app,
            [
                "proposal",
                "reject",
                "PP-REJECT-JSON-APP-001",
                "--repo",
                _repo_from_model(temp_model_dir),
                "--json",
            ],
        )
        assert result.exit_code == 1
        data = json.loads(result.output)
        assert data["proposal_id"] == "PP-REJECT-JSON-APP-001"
        assert "error" in data
        assert "applied" in data["error"]


class TestProposalListStatusFilter:
    def test_proposal_list_status_accepted(self, temp_model_dir: Path) -> None:
        op = PatchOperation(
            op="update_object", object_id="DOMAIN-TEST", target_path="name", after="X"
        )
        _create_accepted_proposal(temp_model_dir, "PP-ACCEPTED-001", [op])

        # Also create a pending proposal
        proposal = build_patch_proposal("PP-PENDING-001", [op])
        write_patch_proposal(proposal, temp_model_dir)

        result = runner.invoke(
            app,
            [
                "proposal",
                "list",
                "--repo",
                _repo_from_model(temp_model_dir),
                "--status",
                "accepted",
            ],
        )
        assert result.exit_code == 0
        assert "PP-ACCEPTED-001" in result.output
        assert "PP-PENDING-001" not in result.output

    def test_proposal_list_status_rejected(self, temp_model_dir: Path) -> None:
        op = PatchOperation(
            op="update_object", object_id="DOMAIN-TEST", target_path="name", after="X"
        )
        proposal = build_patch_proposal("PP-REJECTED-001", [op])
        write_patch_proposal(proposal, temp_model_dir)
        proposal_path = temp_model_dir / "patch-proposals" / "PP-REJECTED-001.md"
        transition_patch_proposal_status(proposal_path, "rejected")

        # Also create an accepted proposal
        _create_accepted_proposal(temp_model_dir, "PP-ACCEPTED-002", [op])

        result = runner.invoke(
            app,
            [
                "proposal",
                "list",
                "--repo",
                _repo_from_model(temp_model_dir),
                "--status",
                "rejected",
            ],
        )
        assert result.exit_code == 0
        assert "PP-REJECTED-001" in result.output
        assert "PP-ACCEPTED-002" not in result.output

    def test_proposal_list_status_json(self, temp_model_dir: Path) -> None:
        op = PatchOperation(
            op="update_object", object_id="DOMAIN-TEST", target_path="name", after="X"
        )
        _create_accepted_proposal(temp_model_dir, "PP-ACCEPTED-003", [op])
        proposal = build_patch_proposal("PP-PENDING-003", [op])
        write_patch_proposal(proposal, temp_model_dir)

        result = runner.invoke(
            app,
            [
                "proposal",
                "list",
                "--repo",
                _repo_from_model(temp_model_dir),
                "--status",
                "accepted",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert len(data) == 1
        assert data[0]["id"] == "PP-ACCEPTED-003"

    def test_proposal_list_status_no_match(self, temp_model_dir: Path) -> None:
        op = PatchOperation(
            op="update_object", object_id="DOMAIN-TEST", target_path="name", after="X"
        )
        _create_accepted_proposal(temp_model_dir, "PP-ACCEPTED-004", [op])

        result = runner.invoke(
            app,
            [
                "proposal",
                "list",
                "--repo",
                _repo_from_model(temp_model_dir),
                "--status",
                "rejected",
            ],
        )
        assert result.exit_code == 0
        assert "PP-ACCEPTED-004" not in result.output
        # Empty table is rendered when no proposals match the filter
        assert "Status" in result.output


class TestProposalListReviewerFilter:
    def test_proposal_list_reviewer_filter(self, temp_model_dir: Path) -> None:
        op = PatchOperation(
            op="update_object", object_id="DOMAIN-TEST", target_path="name", after="X"
        )
        _create_accepted_proposal(temp_model_dir, "PP-ALICE-001", [op])
        proposal_path = temp_model_dir / "patch-proposals" / "PP-ALICE-001.md"
        transition_patch_proposal_status(proposal_path, "accepted", reviewer="alice")

        _create_accepted_proposal(temp_model_dir, "PP-BOB-001", [op])
        proposal_path2 = temp_model_dir / "patch-proposals" / "PP-BOB-001.md"
        transition_patch_proposal_status(proposal_path2, "accepted", reviewer="bob")

        result = runner.invoke(
            app,
            [
                "proposal",
                "list",
                "--repo",
                _repo_from_model(temp_model_dir),
                "--reviewer",
                "alice",
            ],
        )
        assert result.exit_code == 0
        assert "PP-ALICE-001" in result.output
        assert "PP-BOB-001" not in result.output

    def test_proposal_list_reviewer_and_status_combined(self, temp_model_dir: Path) -> None:
        op = PatchOperation(
            op="update_object", object_id="DOMAIN-TEST", target_path="name", after="X"
        )
        _create_accepted_proposal(temp_model_dir, "PP-ALICE-002", [op])
        proposal_path = temp_model_dir / "patch-proposals" / "PP-ALICE-002.md"
        transition_patch_proposal_status(proposal_path, "accepted", reviewer="alice")

        proposal = build_patch_proposal("PP-ALICE-PENDING-002", [op])
        write_patch_proposal(proposal, temp_model_dir)

        result = runner.invoke(
            app,
            [
                "proposal",
                "list",
                "--repo",
                _repo_from_model(temp_model_dir),
                "--reviewer",
                "alice",
                "--status",
                "accepted",
            ],
        )
        assert result.exit_code == 0
        assert "PP-ALICE-002" in result.output
        assert "PP-ALICE-PENDING-002" not in result.output

    def test_proposal_list_reviewer_json(self, temp_model_dir: Path) -> None:
        op = PatchOperation(
            op="update_object", object_id="DOMAIN-TEST", target_path="name", after="X"
        )
        _create_accepted_proposal(temp_model_dir, "PP-ALICE-003", [op])
        proposal_path = temp_model_dir / "patch-proposals" / "PP-ALICE-003.md"
        transition_patch_proposal_status(proposal_path, "accepted", reviewer="alice")

        result = runner.invoke(
            app,
            [
                "proposal",
                "list",
                "--repo",
                _repo_from_model(temp_model_dir),
                "--reviewer",
                "alice",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert len(data) == 1
        assert data[0]["reviewer"] == "alice"
