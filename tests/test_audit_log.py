"""Tests for audit event service and CLI."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from modelops_core.cli import app
from modelops_core.reports.audit_service import (
    AuditEvent,
    AuditEventService,
    create_audit_event,
    filter_audit_events,
)

runner = CliRunner()


def test_create_audit_event() -> None:
    event = create_audit_event(
        event_type="test_event",
        actor="tester",
        status="success",
        command="test cmd",
        proposal_id="PP-001",
        changed_object_ids=["OBJ-1"],
        changed_files=["file.md"],
        validation_status="valid",
        source_evidence_ids=["EV-1"],
    )
    assert event.event_type == "test_event"
    assert event.actor == "tester"
    assert event.proposal_id == "PP-001"
    assert event.changed_object_ids == ["OBJ-1"]
    assert event.command == "test cmd"
    assert event.validation_status == "valid"


def test_audit_event_roundtrip(tmp_path: Path) -> None:
    service = AuditEventService(tmp_path)
    event = create_audit_event(event_type="model_export", status="success")
    event_id = service.emit(event)
    assert event_id.startswith("audit-")

    events = service.read_events()
    assert len(events) == 1
    assert events[0].event_type == "model_export"
    assert events[0].status == "success"


def test_filter_by_event_type() -> None:
    events = [
        create_audit_event(event_type="patch_apply", status="success"),
        create_audit_event(event_type="model_export", status="success"),
        create_audit_event(event_type="patch_apply", status="failed"),
    ]
    filtered = filter_audit_events(events, event_type="patch_apply")
    assert len(filtered) == 2
    assert all(e.event_type == "patch_apply" for e in filtered)


def test_filter_by_proposal_id() -> None:
    events = [
        create_audit_event(event_type="patch_apply", proposal_id="PP-001"),
        create_audit_event(event_type="patch_apply", proposal_id="PP-002"),
    ]
    filtered = filter_audit_events(events, proposal_id="PP-001")
    assert len(filtered) == 1
    assert filtered[0].proposal_id == "PP-001"


def test_filter_by_object_id() -> None:
    events = [
        create_audit_event(
            event_type="patch_apply", changed_object_ids=["OBJ-A", "OBJ-B"]
        ),
        create_audit_event(event_type="patch_apply", changed_object_ids=["OBJ-C"]),
    ]
    filtered = filter_audit_events(events, object_id="OBJ-A")
    assert len(filtered) == 1


def test_filter_by_date_range() -> None:
    events = [
        create_audit_event(event_type="test", status="success"),
    ]
    events[0].timestamp = "2026-05-01T12:00:00Z"
    filtered = filter_audit_events(events, date_from="2026-01-01", date_to="2026-12-31")
    assert len(filtered) == 1
    filtered = filter_audit_events(events, date_from="2027-01-01")
    assert len(filtered) == 0


def test_cli_audit_log_empty(tmp_path: Path) -> None:
    result = runner.invoke(app, ["audit-log", "--repo", str(tmp_path)])
    assert result.exit_code == 0
    assert "No audit events found" in result.output


def test_cli_audit_log_with_events(tmp_path: Path) -> None:
    service = AuditEventService(tmp_path)
    service.emit(create_audit_event(event_type="model_export", command="export-model"))
    service.emit(create_audit_event(event_type="patch_apply", command="proposal apply"))

    result = runner.invoke(app, ["audit-log", "--repo", str(tmp_path)])
    assert result.exit_code == 0
    assert "Audit Log (2 events)" in result.output
    assert "export" in result.output
    assert "patch_apply" in result.output


def test_cli_audit_log_filter_by_type(tmp_path: Path) -> None:
    service = AuditEventService(tmp_path)
    service.emit(create_audit_event(event_type="model_export"))
    service.emit(create_audit_event(event_type="patch_apply"))

    result = runner.invoke(
        app, ["audit-log", "--repo", str(tmp_path), "--event-type", "patch_apply"]
    )
    assert result.exit_code == 0
    assert "patch_apply" in result.output
    assert "model_export" not in result.output


def test_cli_audit_log_json_output(tmp_path: Path) -> None:
    service = AuditEventService(tmp_path)
    service.emit(create_audit_event(event_type="model_export", status="success"))

    result = runner.invoke(app, ["audit-log", "--repo", str(tmp_path), "--json"])
    assert result.exit_code == 0
    assert "model_export" in result.output
    assert "success" in result.output


def test_audit_event_to_dict() -> None:
    event = create_audit_event(event_type="test", status="success")
    d = event.to_dict()
    assert d["event_type"] == "test"
    assert d["status"] == "success"
    assert "event_id" in d
    assert "timestamp" in d


def test_audit_event_from_dict() -> None:
    original = create_audit_event(
        event_type="test",
        status="failed",
        command="cmd",
        proposal_id="PP-1",
        changed_object_ids=["A"],
        changed_files=["f.md"],
        validation_status="invalid",
        source_evidence_ids=["E1"],
    )
    restored = AuditEvent.from_dict(original.to_dict())
    assert restored.event_type == "test"
    assert restored.status == "failed"
    assert restored.command == "cmd"
    assert restored.proposal_id == "PP-1"
    assert restored.changed_object_ids == ["A"]
    assert restored.changed_files == ["f.md"]
    assert restored.validation_status == "invalid"
    assert restored.source_evidence_ids == ["E1"]
