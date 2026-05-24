"""Tests for notification preview (issue #30)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from modelops_core.cli import app
from modelops_core.notifications.preview_service import preview_notifications

runner = CliRunner()


def test_preview_for_change_request(tmp_path: Path) -> None:
    model_dir = tmp_path / "model"
    model_dir.mkdir()

    # Create an object with owners and watchers
    attr_file = model_dir / "ATTR-TEST.md"
    attr_file.write_text(
        "---\n"
        "id: ATTR-TEST\n"
        "type: Attribute\n"
        "status: active\n"
        "name: Test Attribute\n"
        "business_owner: alice\n"
        "watchers:\n  - bob\n"
        "---\n\n# Test\n"
    )

    # Create a ChangeRequest affecting the object
    cr_dir = model_dir / "change-requests"
    cr_dir.mkdir()
    cr_file = cr_dir / "CR-001.md"
    cr_file.write_text(
        "---\n"
        "id: CR-001\n"
        "type: ChangeRequest\n"
        "status: pending\n"
        "name: Test CR\n"
        "requester: charlie\n"
        "approvers:\n  - dave\n"
        "affected_objects:\n  - ATTR-TEST\n"
        "---\n\n# Test\n"
    )

    entries = preview_notifications(model_path=model_dir, cr_id="CR-001")
    recipients = {e.recipient_id: e.recipient_role for e in entries}

    assert "alice" in recipients
    assert recipients["alice"] == "business_owner"
    assert "bob" in recipients
    assert recipients["bob"] == "watcher"
    assert "charlie" in recipients
    assert recipients["charlie"] == "requester"
    assert "dave" in recipients
    assert recipients["dave"] == "approver"


def test_preview_for_proposal(tmp_path: Path) -> None:
    model_dir = tmp_path / "model"
    model_dir.mkdir()

    fep_file = model_dir / "FEP-TEST.md"
    fep_file.write_text(
        "---\n"
        "id: FEP-TEST\n"
        "type: FieldEndpoint\n"
        "status: active\n"
        "name: Test Field\n"
        "technical_owner: eve\n"
        "---\n\n# Test\n"
    )

    pp_dir = model_dir / "patch-proposals"
    pp_dir.mkdir()
    pp_file = pp_dir / "PP-001.md"
    pp_file.write_text(
        "---\n"
        "id: PP-001\n"
        "type: PatchProposal\n"
        "status: pending_review\n"
        "name: Test PP\n"
        "affected_objects:\n  - FEP-TEST\n"
        "---\n\n# Test\n"
    )

    entries = preview_notifications(model_path=model_dir, proposal_id="PP-001")
    recipients = {e.recipient_id: e.recipient_role for e in entries}

    assert "eve" in recipients
    assert recipients["eve"] == "technical_owner"


def test_preview_deduplicates(tmp_path: Path) -> None:
    model_dir = tmp_path / "model"
    model_dir.mkdir()

    attr_file = model_dir / "ATTR-TEST.md"
    attr_file.write_text(
        "---\n"
        "id: ATTR-TEST\n"
        "type: Attribute\n"
        "status: active\n"
        "name: Test\n"
        "business_owner: alice\n"
        "watchers:\n  - alice\n"
        "---\n\n# Test\n"
    )

    cr_dir = model_dir / "change-requests"
    cr_dir.mkdir()
    cr_file = cr_dir / "CR-001.md"
    cr_file.write_text(
        "---\n"
        "id: CR-001\n"
        "type: ChangeRequest\n"
        "status: pending\n"
        "name: Test CR\n"
        "requester: alice\n"
        "affected_objects:\n  - ATTR-TEST\n"
        "---\n\n# Test\n"
    )

    entries = preview_notifications(model_path=model_dir, cr_id="CR-001")
    alice_entries = [e for e in entries if e.recipient_id == "alice"]
    # alice appears as business_owner and watcher and requester,
    # but deduplication keeps distinct (role, source_object_id) combos
    assert len(alice_entries) == 3


def test_preview_no_cr_or_proposal_raises(tmp_path: Path) -> None:
    model_dir = tmp_path / "model"
    model_dir.mkdir()

    with pytest.raises(ValueError, match="Either cr_id or proposal_id"):
        preview_notifications(model_path=model_dir)


def test_preview_missing_cr_raises(tmp_path: Path) -> None:
    model_dir = tmp_path / "model"
    model_dir.mkdir()

    with pytest.raises(ValueError, match="ChangeRequest not found"):
        preview_notifications(model_path=model_dir, cr_id="CR-MISSING")


def test_cli_preview_json(tmp_path: Path) -> None:
    model_dir = tmp_path / "model"
    model_dir.mkdir()

    attr_file = model_dir / "ATTR-TEST.md"
    attr_file.write_text(
        "---\n"
        "id: ATTR-TEST\n"
        "type: Attribute\n"
        "status: active\n"
        "name: Test\n"
        "business_owner: alice\n"
        "---\n\n# Test\n"
    )

    cr_dir = model_dir / "change-requests"
    cr_dir.mkdir()
    cr_file = cr_dir / "CR-001.md"
    cr_file.write_text(
        "---\n"
        "id: CR-001\n"
        "type: ChangeRequest\n"
        "status: pending\n"
        "name: Test CR\n"
        "affected_objects:\n  - ATTR-TEST\n"
        "---\n\n# Test\n"
    )

    result = runner.invoke(
        app,
        [
            "notifications",
            "preview",
            "--repo",
            str(tmp_path),
            "--change-request",
            "CR-001",
            "--json",
        ],
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert len(data) == 1
    assert data[0]["recipient_id"] == "alice"
    assert data[0]["recipient_role"] == "business_owner"


def test_cli_preview_table(tmp_path: Path) -> None:
    model_dir = tmp_path / "model"
    model_dir.mkdir()

    attr_file = model_dir / "ATTR-TEST.md"
    attr_file.write_text(
        "---\n"
        "id: ATTR-TEST\n"
        "type: Attribute\n"
        "status: active\n"
        "name: Test\n"
        "business_owner: alice\n"
        "---\n\n# Test\n"
    )

    cr_dir = model_dir / "change-requests"
    cr_dir.mkdir()
    cr_file = cr_dir / "CR-001.md"
    cr_file.write_text(
        "---\n"
        "id: CR-001\n"
        "type: ChangeRequest\n"
        "status: pending\n"
        "name: Test CR\n"
        "affected_objects:\n  - ATTR-TEST\n"
        "---\n\n# Test\n"
    )

    result = runner.invoke(
        app,
        [
            "notifications",
            "preview",
            "--repo",
            str(tmp_path),
            "--change-request",
            "CR-001",
        ],
    )
    assert result.exit_code == 0
    assert "alice" in result.output
    assert "business_owner" in result.output
