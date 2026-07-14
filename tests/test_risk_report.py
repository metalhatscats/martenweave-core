"""Tests for the standalone risk-report command and service."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from modelops_core.assessment.assessment_service import generate_risk_report
from modelops_core.cli import app

runner = CliRunner()


def test_risk_report_command_creates_markdown(sample_repo: Path, tmp_path: Path) -> None:
    out = tmp_path / "high_risk_fields.md"
    result = runner.invoke(app, ["risk-report", "--repo", str(sample_repo), "--out", str(out)])
    assert result.exit_code == 0, result.output
    assert out.exists()
    content = out.read_text(encoding="utf-8")
    assert "# High Risk Fields" in content
    assert "| Object ID | Type | Name | Severity | Reasons |" in content


def test_risk_report_command_json_output(sample_repo: Path) -> None:
    result = runner.invoke(app, ["risk-report", "--repo", str(sample_repo), "--json"])
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert "risk_items" in data
    assert "repo_name" in data
    assert "generated_at" in data
    for item in data["risk_items"]:
        assert "object_id" in item
        assert "object_name" in item
        assert "object_type" in item
        assert "severity" in item
        assert "reasons" in item
        assert item["severity"] in {"high", "medium", "low"}


def test_risk_report_command_empty_repo(tmp_path: Path) -> None:
    empty_repo = tmp_path / "empty_repo"
    empty_repo.mkdir()
    result = runner.invoke(app, ["risk-report", "--repo", str(empty_repo), "--json"])
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data["risk_items"] == []
    assert data["total_high_risk_items"] == 0


def test_risk_report_service_returns_markdown(sample_repo: Path) -> None:
    content = generate_risk_report(sample_repo)
    assert "# High Risk Fields" in content
    assert "| Object ID | Type | Name | Severity | Reasons |" in content
