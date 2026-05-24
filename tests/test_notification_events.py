"""Tests for notification event log (issue #31)."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from modelops_core.cli import app
from modelops_core.notifications.event_service import (
    NotificationEvent,
    emit_notification_event,
    filter_notification_events,
    read_notification_events,
)

runner = CliRunner()


def test_emit_and_read_event(tmp_path: Path) -> None:
    event = emit_notification_event(
        repo_root=tmp_path,
        event_type="change_request_approved",
        source_type="ChangeRequest",
        source_id="CR-001",
        recipient_id="alice",
        recipient_role="approver",
        reason="approver of ChangeRequest 'CR-001'",
        affected_objects=["ATTR-1"],
        message_summary="CR-001 approved",
        status="approved",
    )
    assert event.event_id.startswith("NE-")
    assert event.recipient_id == "alice"

    events = read_notification_events(tmp_path)
    assert len(events) == 1
    assert events[0].event_type == "change_request_approved"


def test_filter_events(tmp_path: Path) -> None:
    emit_notification_event(
        repo_root=tmp_path,
        event_type="change_request_approved",
        source_type="ChangeRequest",
        source_id="CR-001",
        recipient_id="alice",
        recipient_role="approver",
        reason="r1",
    )
    emit_notification_event(
        repo_root=tmp_path,
        event_type="change_request_rejected",
        source_type="ChangeRequest",
        source_id="CR-002",
        recipient_id="bob",
        recipient_role="requester",
        reason="r2",
    )

    events = read_notification_events(tmp_path)
    assert len(events) == 2

    filtered = filter_notification_events(events, recipient="alice")
    assert len(filtered) == 1
    assert filtered[0].recipient_id == "alice"

    filtered = filter_notification_events(events, event_type="change_request_rejected")
    assert len(filtered) == 1
    assert filtered[0].source_id == "CR-002"

    filtered = filter_notification_events(events, source_id="CR-001")
    assert len(filtered) == 1


def test_cli_cr_create_emits_event(tmp_path: Path) -> None:
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

    result = runner.invoke(
        app,
        [
            "change-request",
            "create",
            "--id",
            "CR-EVT-001",
            "--title",
            "Event Test",
            "--repo",
            str(tmp_path),
            "--affected-object",
            "ATTR-TEST",
        ],
    )
    assert result.exit_code == 0

    events = read_notification_events(tmp_path)
    assert len(events) >= 1
    alice_events = [e for e in events if e.recipient_id == "alice"]
    assert len(alice_events) == 1
    assert alice_events[0].event_type == "change_request_requested"


def test_cli_cr_approve_emits_event(tmp_path: Path) -> None:
    model_dir = tmp_path / "model"
    model_dir.mkdir()

    cr_dir = model_dir / "change-requests"
    cr_dir.mkdir()
    cr_file = cr_dir / "CR-EVT-002.md"
    cr_file.write_text(
        "---\n"
        "id: CR-EVT-002\n"
        "type: ChangeRequest\n"
        "status: pending\n"
        "name: Event Test\n"
        "requester: bob\n"
        "---\n\n# Test\n"
    )

    result = runner.invoke(
        app,
        [
            "change-request",
            "update-status",
            "CR-EVT-002",
            "approved",
            "--repo",
            str(tmp_path),
        ],
    )
    assert result.exit_code == 0

    events = read_notification_events(tmp_path)
    bob_events = [e for e in events if e.recipient_id == "bob"]
    assert len(bob_events) >= 1
    assert any(e.event_type == "change_request_approved" for e in bob_events)


def test_cli_notifications_list_json(tmp_path: Path) -> None:
    emit_notification_event(
        repo_root=tmp_path,
        event_type="change_request_approved",
        source_type="ChangeRequest",
        source_id="CR-001",
        recipient_id="alice",
        recipient_role="approver",
        reason="r1",
    )

    result = runner.invoke(
        app,
        ["notifications", "list", "--repo", str(tmp_path), "--json"],
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert len(data) == 1
    assert data[0]["recipient_id"] == "alice"


def test_cli_notifications_list_filtered(tmp_path: Path) -> None:
    emit_notification_event(
        repo_root=tmp_path,
        event_type="change_request_approved",
        source_type="ChangeRequest",
        source_id="CR-001",
        recipient_id="alice",
        recipient_role="approver",
        reason="r1",
    )
    emit_notification_event(
        repo_root=tmp_path,
        event_type="change_request_rejected",
        source_type="ChangeRequest",
        source_id="CR-002",
        recipient_id="bob",
        recipient_role="requester",
        reason="r2",
    )

    result = runner.invoke(
        app,
        [
            "notifications",
            "list",
            "--repo",
            str(tmp_path),
            "--recipient",
            "alice",
        ],
    )
    assert result.exit_code == 0
    assert "alice" in result.output
    assert "bob" not in result.output


def test_notification_event_from_dict() -> None:
    data = {
        "event_id": "NE-1",
        "timestamp": "2026-01-01T00:00:00Z",
        "event_type": "test",
        "source_type": "ChangeRequest",
        "source_id": "CR-1",
        "recipient_id": "alice",
        "recipient_role": "owner",
        "reason": "test",
        "affected_objects": ["A", "B"],
        "message_summary": "msg",
        "status": "pending",
    }
    event = NotificationEvent.from_dict(data)
    assert event.event_id == "NE-1"
    assert event.affected_objects == ["A", "B"]
