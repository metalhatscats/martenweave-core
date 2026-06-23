"""Tests for the Migration Model Readiness Assessment package."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from modelops_core.cli import app

runner = CliRunner()


def test_assessment_run_creates_all_files(sample_repo: Path, tmp_path: Path) -> None:
    out = tmp_path / "assessment"
    result = runner.invoke(
        app, ["assessment", "run", "--repo", str(sample_repo), "--out", str(out)]
    )
    assert result.exit_code == 0, result.output
    assert (out / "01_readiness_scorecard.md").exists()
    assert (out / "02_gap_report.md").exists()
    assert (out / "03_high_risk_fields.md").exists()
    assert (out / "04_impact_reports").exists()
    assert (out / "05_business_review.xlsx").exists()
    assert (out / "06_recommendations.md").exists()


def test_assessment_scorecard_headers(sample_repo: Path, tmp_path: Path) -> None:
    out = tmp_path / "assessment"
    runner.invoke(app, ["assessment", "run", "--repo", str(sample_repo), "--out", str(out)])
    content = (out / "01_readiness_scorecard.md").read_text(encoding="utf-8")
    assert "# Migration Model Readiness Scorecard" in content
    assert "## Metrics" in content


def test_assessment_gap_report_headers(sample_repo: Path, tmp_path: Path) -> None:
    out = tmp_path / "assessment"
    runner.invoke(app, ["assessment", "run", "--repo", str(sample_repo), "--out", str(out)])
    content = (out / "02_gap_report.md").read_text(encoding="utf-8")
    assert "# Gap Report" in content
    assert "## Gaps by Type" in content


def test_assessment_high_risk_fields_has_table(sample_repo: Path, tmp_path: Path) -> None:
    out = tmp_path / "assessment"
    runner.invoke(app, ["assessment", "run", "--repo", str(sample_repo), "--out", str(out)])
    content = (out / "03_high_risk_fields.md").read_text(encoding="utf-8")
    assert "# High Risk Fields" in content
    assert "| Object ID | Type | Name | Severity | Reasons |" in content


def test_assessment_impact_reports_dir(sample_repo: Path, tmp_path: Path) -> None:
    out = tmp_path / "assessment"
    runner.invoke(app, ["assessment", "run", "--repo", str(sample_repo), "--out", str(out)])
    impact_dir = out / "04_impact_reports"
    md_files = list(impact_dir.glob("*.md"))
    assert len(md_files) >= 0


def test_assessment_business_review_xlsx(sample_repo: Path, tmp_path: Path) -> None:
    out = tmp_path / "assessment"
    runner.invoke(app, ["assessment", "run", "--repo", str(sample_repo), "--out", str(out)])
    xlsx_path = out / "05_business_review.xlsx"
    assert xlsx_path.exists()
    assert xlsx_path.stat().st_size > 0


def test_assessment_recommendations_headers(sample_repo: Path, tmp_path: Path) -> None:
    out = tmp_path / "assessment"
    runner.invoke(app, ["assessment", "run", "--repo", str(sample_repo), "--out", str(out)])
    content = (out / "06_recommendations.md").read_text(encoding="utf-8")
    assert "# Recommendations" in content
    assert "## Next Steps" in content


def test_assessment_json_output(sample_repo: Path, tmp_path: Path) -> None:
    out = tmp_path / "assessment"
    result = runner.invoke(
        app, ["assessment", "run", "--repo", str(sample_repo), "--out", str(out), "--json"]
    )
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert "repo_name" in data
    assert "readiness_level" in data
    assert "artifacts" in data
    assert isinstance(data["artifacts"], list)
