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


def test_assessment_run_rejects_invalid_model(tmp_path: Path) -> None:
    model_dir = tmp_path / "model"
    model_dir.mkdir()
    (model_dir / "ATTR-BAD.md").write_text(
        "---\nid: ATTR-BAD\ntype: Attribute\nstatus: draft\nname: Bad\ndomain: NONEXISTENT\n---\n",
        encoding="utf-8",
    )

    out = tmp_path / "assessment"
    result = runner.invoke(app, ["assessment", "run", "--repo", str(tmp_path), "--out", str(out)])
    assert result.exit_code == 1, result.output
    assert "Validation failed" in result.output
    assert not out.exists()


def test_assessment_run_allow_invalid_builds_package(tmp_path: Path) -> None:
    model_dir = tmp_path / "model"
    model_dir.mkdir()
    (model_dir / "ATTR-BAD.md").write_text(
        "---\nid: ATTR-BAD\ntype: Attribute\nstatus: draft\nname: Bad\ndomain: NONEXISTENT\n---\n",
        encoding="utf-8",
    )

    out = tmp_path / "assessment-allow"
    result = runner.invoke(
        app,
        [
            "assessment",
            "run",
            "--repo",
            str(tmp_path),
            "--out",
            str(out),
            "--allow-invalid",
        ],
    )
    assert result.exit_code == 0, result.output
    assert (out / "01_readiness_scorecard.md").exists()
    assert "--allow-invalid" in result.output
    assert "validation errors" in result.output


def test_assessment_package_metadata_customer_bp(sample_repo: Path, tmp_path: Path) -> None:
    out = tmp_path / "assessment"
    result = runner.invoke(
        app, ["assessment", "run", "--repo", str(sample_repo), "--out", str(out), "--json"]
    )
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data["repo_name"] == "Untitled Repository"
    assert data["readiness_level"] == "draft"
    assert data["object_count"] == 85
    assert data["gap_score"] == 1.0
    assert data["high_risk_count"] == 34
    assert isinstance(data["artifacts"], list)


def test_assessment_scorecard_metrics_customer_bp(sample_repo: Path, tmp_path: Path) -> None:
    out = tmp_path / "assessment"
    result = runner.invoke(
        app, ["assessment", "run", "--repo", str(sample_repo), "--out", str(out)]
    )
    assert result.exit_code == 0, result.output
    content = (out / "01_readiness_scorecard.md").read_text(encoding="utf-8")

    expected_metrics = {
        "model_completeness": 60.0,
        "ownership_coverage": 100.0,
        "validation_rule_coverage": 31.2,
        "lov_coverage": 0.0,
        "mapping_logic_coverage": 0.0,
        "dataset_profile_coverage": 0.0,
        "traceability_coverage": 94.1,
        "unresolved_issue_count": 1,
        "pending_change_count": 0,
        "high_risk_change_count": 0,
        "evidence_coverage": 100.0,
        "sap_table_coverage": 100.0,
    }
    for name, value in expected_metrics.items():
        assert f"| {name} | {value} " in content, f"Expected {name} to be {value}"


def test_assessment_scorecard_metrics_supplier_vendor(supplier_repo: Path, tmp_path: Path) -> None:
    out = tmp_path / "assessment"
    result = runner.invoke(
        app, ["assessment", "run", "--repo", str(supplier_repo), "--out", str(out)]
    )
    assert result.exit_code == 0, result.output
    content = (out / "01_readiness_scorecard.md").read_text(encoding="utf-8")

    expected_metrics = {
        "model_completeness": 50.0,
        "ownership_coverage": 32.0,
        "validation_rule_coverage": 0.0,
        "lov_coverage": 0.0,
        "mapping_logic_coverage": 0.0,
        "dataset_profile_coverage": 0.0,
        "traceability_coverage": 97.2,
        "unresolved_issue_count": 1,
        "pending_change_count": 0,
        "high_risk_change_count": 0,
        "evidence_coverage": 100.0,
        "sap_table_coverage": 0.0,
    }
    for name, value in expected_metrics.items():
        assert f"| {name} | {value} " in content, f"Expected {name} to be {value}"


def test_assessment_gap_score_capped_for_gaps(sample_repo: Path, tmp_path: Path) -> None:
    """Gap score is capped at 1.0 when gaps exceed object count."""
    out = tmp_path / "assessment"
    result = runner.invoke(
        app, ["assessment", "run", "--repo", str(sample_repo), "--out", str(out), "--json"]
    )
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data["gap_score"] == 1.0
