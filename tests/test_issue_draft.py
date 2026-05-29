"""Tests for GitHub issue draft generation (issue #33)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from modelops_core.cli import app
from modelops_core.issue_draft.draft_service import (
    DraftResult,
    create_draft_from_change_request,
    create_draft_from_proposal,
    create_draft_from_validation,
    write_draft,
)

runner = CliRunner()


def test_draft_from_change_request(tmp_path: Path) -> None:
    model_dir = tmp_path / "model"
    model_dir.mkdir()

    (model_dir / "change-requests").mkdir()
    (model_dir / "change-requests" / "CR-001.md").write_text(
        "---\n"
        "id: CR-001\n"
        "type: ChangeRequest\n"
        "status: pending\n"
        "name: Test CR\n"
        "title: Test CR\n"
        "reason: Fix the mapping\n"
        "requested_change: Update mapping rules\n"
        "expected_impact: Low\n"
        "affected_objects:\n  - OBJ-001\n"
        "linked_proposals:\n  - PP-001\n"
        "approvers:\n  - alice\n"
        "requester: bob\n"
        "---\n\n# Test CR\n",
        encoding="utf-8",
    )

    draft = create_draft_from_change_request(model_dir, "CR-001")

    assert isinstance(draft, DraftResult)
    assert "Test CR" in draft.title
    assert "Fix the mapping" in draft.body
    assert "OBJ-001" in draft.body
    assert "PP-001" in draft.body
    assert "alice" in draft.body
    assert "change-request" in draft.labels
    assert "alice" in draft.suggested_assignees
    assert "bob" in draft.suggested_assignees


def test_draft_from_change_request_not_found(tmp_path: Path) -> None:
    model_dir = tmp_path / "model"
    model_dir.mkdir()

    with pytest.raises(ValueError, match="ChangeRequest not found"):
        create_draft_from_change_request(model_dir, "CR-MISSING")


def test_draft_from_proposal(tmp_path: Path) -> None:
    model_dir = tmp_path / "model"
    model_dir.mkdir()
    generated_dir = tmp_path / "generated"
    generated_dir.mkdir()

    (model_dir / "DOMAIN-TEST.md").write_text(
        "---\nid: DOMAIN-TEST\ntype: MasterDataDomain\nstatus: draft\nname: Test\n---\n",
        encoding="utf-8",
    )

    proposals_dir = model_dir / "patch-proposals"
    proposals_dir.mkdir()
    (proposals_dir / "PP-001.md").write_text(
        "---\n"
        "id: PP-001\n"
        "type: PatchProposal\n"
        "status: accepted\n"
        "name: PP-001\n"
        "title: Test Proposal\n"
        "source_evidence: Workshop notes\n"
        "affected_objects:\n  - DOMAIN-TEST\n"
        "operations:\n"
        "  - op: update_object\n"
        "    object_id: DOMAIN-TEST\n"
        "    target_path: name\n"
        "    after: Updated\n"
        "validation_status: valid\n"
        "---\n",
        encoding="utf-8",
    )

    draft = create_draft_from_proposal(model_dir, generated_dir, "PP-001")

    assert isinstance(draft, DraftResult)
    assert "Test Proposal" in draft.title
    assert "Workshop notes" in draft.body
    assert "DOMAIN-TEST" in draft.body
    assert "patch-proposal" in draft.labels


def test_draft_from_proposal_not_found(tmp_path: Path) -> None:
    model_dir = tmp_path / "model"
    model_dir.mkdir()
    generated_dir = tmp_path / "generated"
    generated_dir.mkdir()

    with pytest.raises(ValueError, match="PatchProposal not found"):
        create_draft_from_proposal(model_dir, generated_dir, "PP-MISSING")


def test_draft_from_validation(tmp_path: Path) -> None:
    model_dir = tmp_path / "model"
    model_dir.mkdir()

    (model_dir / "DOMAIN-TEST.md").write_text(
        "---\nid: DOMAIN-TEST\ntype: MasterDataDomain\nstatus: draft\nname: Test\n---\n",
        encoding="utf-8",
    )
    # Duplicate ID to trigger validation error
    (model_dir / "DOMAIN-TEST2.md").write_text(
        "---\nid: DOMAIN-TEST\ntype: MasterDataDomain\nstatus: draft\nname: Test2\n---\n",
        encoding="utf-8",
    )

    draft = create_draft_from_validation(tmp_path)

    assert isinstance(draft, DraftResult)
    assert "Validation" in draft.title
    assert "DUPLICATE_ID" in draft.body or "validation" in draft.body.lower()
    assert "validation" in draft.labels


def test_write_draft(tmp_path: Path) -> None:
    draft = DraftResult(
        title="Test Draft",
        body="## Body\n\nHello",
        source_type="test",
        source_id="T-001",
        labels=["test"],
        suggested_assignees=["alice"],
    )

    path = write_draft(tmp_path, draft)
    content = path.read_text(encoding="utf-8")

    assert "Test Draft" in content
    assert "Body" in content
    assert "test" in content
    assert "alice" in content
    assert path.name == "T-001.md"


def test_cli_draft_from_change_request(tmp_path: Path) -> None:
    model_dir = tmp_path / "model"
    model_dir.mkdir()
    (model_dir / "change-requests").mkdir()
    (model_dir / "change-requests" / "CR-CLI-001.md").write_text(
        "---\n"
        "id: CR-CLI-001\n"
        "type: ChangeRequest\n"
        "status: pending\n"
        "name: CLI Test\n"
        "title: CLI Test\n"
        "reason: Test reason\n"
        "---\n",
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "issue-draft",
            "create",
            "--repo",
            str(tmp_path),
            "--change-request",
            "CR-CLI-001",
        ],
    )
    assert result.exit_code == 0
    assert "Draft written" in result.output


def test_cli_draft_from_proposal(tmp_path: Path) -> None:
    model_dir = tmp_path / "model"
    model_dir.mkdir()
    proposals_dir = model_dir / "patch-proposals"
    proposals_dir.mkdir()
    (proposals_dir / "PP-CLI-001.md").write_text(
        "---\n"
        "id: PP-CLI-001\n"
        "type: PatchProposal\n"
        "status: accepted\n"
        "name: PP-CLI-001\n"
        "title: CLI Proposal\n"
        "operations: []\n"
        "---\n",
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "issue-draft",
            "create",
            "--repo",
            str(tmp_path),
            "--proposal",
            "PP-CLI-001",
        ],
    )
    assert result.exit_code == 0
    assert "Draft written" in result.output


def test_cli_draft_from_validation(tmp_path: Path) -> None:
    model_dir = tmp_path / "model"
    model_dir.mkdir()
    (model_dir / "DOMAIN-TEST.md").write_text(
        "---\nid: DOMAIN-TEST\ntype: MasterDataDomain\nstatus: draft\nname: Test\n---\n",
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "issue-draft",
            "create",
            "--repo",
            str(tmp_path),
            "--from-validation",
        ],
    )
    assert result.exit_code == 0
    assert "Draft written" in result.output


def test_cli_draft_requires_source(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        ["issue-draft", "create", "--repo", str(tmp_path)],
    )
    assert result.exit_code == 1
    assert "Specify one source" in result.output


def test_cli_draft_json_output(tmp_path: Path) -> None:
    model_dir = tmp_path / "model"
    model_dir.mkdir()
    proposals_dir = model_dir / "patch-proposals"
    proposals_dir.mkdir()
    (proposals_dir / "PP-JSON-001.md").write_text(
        "---\n"
        "id: PP-JSON-001\n"
        "type: PatchProposal\n"
        "status: accepted\n"
        "name: PP-JSON-001\n"
        "title: JSON Test\n"
        "operations: []\n"
        "---\n",
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "issue-draft",
            "create",
            "--repo",
            str(tmp_path),
            "--proposal",
            "PP-JSON-001",
            "--json",
        ],
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "title" in data
    assert "body" in data
    assert data["source_id"] == "PP-JSON-001"
