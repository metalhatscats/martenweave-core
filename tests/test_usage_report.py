"""Tests for usage report service and CLI (#89)."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from modelops_core.cli import app
from modelops_core.reports.audit_service import AuditEventService, create_audit_event
from modelops_core.reports.usage_report_service import generate_usage_report

runner = CliRunner()


class TestUsageReportService:
    def test_empty_repo(self, tmp_path: Path) -> None:
        report = generate_usage_report(tmp_path)
        assert report.total_events == 0
        assert report.ai_usage_summary["note"] == (
            "No AI usage recorded. Enable AI provider calls to capture usage."
        )

    def test_aggregates_event_types(self, tmp_path: Path) -> None:
        service = AuditEventService(tmp_path)
        service.emit(create_audit_event(event_type="model_export", command="export-model"))
        service.emit(create_audit_event(event_type="patch_apply", command="proposal apply"))
        service.emit(create_audit_event(event_type="model_export", command="export-model"))

        report = generate_usage_report(tmp_path)
        assert report.total_events == 3
        assert report.event_type_counts["model_export"] == 2
        assert report.event_type_counts["patch_apply"] == 1
        assert report.command_counts["export-model"] == 2
        assert report.command_counts["proposal apply"] == 1

    def test_ai_usage_from_metadata(self, tmp_path: Path) -> None:
        service = AuditEventService(tmp_path)
        service.emit(
            create_audit_event(
                event_type="ai_call",
                command="propose-patch",
                metadata={"tokens": 150},
            )
        )
        report = generate_usage_report(tmp_path)
        assert report.ai_usage_summary["ai_calls"] == 1
        assert report.ai_usage_summary["total_tokens"] == 150


class TestUsageReportCli:
    def test_empty_repo(self, tmp_path: Path) -> None:
        result = runner.invoke(app, ["usage-report", "--repo", str(tmp_path)])
        assert result.exit_code == 0
        assert "Total events: 0" in result.output
        assert "No audit events found" in result.output

    def test_with_events(self, tmp_path: Path) -> None:
        service = AuditEventService(tmp_path)
        service.emit(create_audit_event(event_type="model_export", command="export-model"))
        service.emit(create_audit_event(event_type="patch_apply", command="proposal apply"))

        result = runner.invoke(app, ["usage-report", "--repo", str(tmp_path)])
        assert result.exit_code == 0
        assert "Total events: 2" in result.output
        assert "model_export" in result.output
        assert "patch_apply" in result.output
        assert "export-model" in result.output

    def test_json_output(self, tmp_path: Path) -> None:
        service = AuditEventService(tmp_path)
        service.emit(create_audit_event(event_type="model_export", status="success"))

        result = runner.invoke(app, ["usage-report", "--repo", str(tmp_path), "--json"])
        assert result.exit_code == 0
        assert "total_events" in result.output
        assert "model_export" in result.output
        assert "ai_usage_summary" in result.output
