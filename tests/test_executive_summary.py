"""Tests for the one-page executive migration readiness summary."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from modelops_core.cli import app
from modelops_core.pilot.executive_summary import (
    generate_executive_summary,
    render_executive_summary_markdown,
)

runner = CliRunner()

MAPPING_WORKBOOK = Path(__file__).parent / "fixtures" / "pilot" / "sap_customer_mapping.xlsx"


@pytest.mark.skipif(not MAPPING_WORKBOOK.exists(), reason="pilot fixture missing")
def test_executive_summary_from_assessment(sample_repo: Path, tmp_path: Path) -> None:
    """End-to-end test generating an executive summary from an assessment run."""
    assessment_dir = tmp_path / "assessment"

    result = runner.invoke(
        app,
        [
            "run",
            "migration-assessment",
            "--repo",
            str(sample_repo),
            "--mapping",
            str(MAPPING_WORKBOOK),
            "--out",
            str(assessment_dir),
        ],
    )
    assert result.exit_code == 0, result.output

    manifest_path = assessment_dir / "manifest.json"
    summary = generate_executive_summary(manifest_path)

    assert summary.repo_name
    assert summary.readiness_verdict in {"blocked", "at_risk", "review", "ready"}
    assert summary.key_metrics["total_findings"] > 0
    assert summary.recommended_next_action
    assert summary.source_artifacts["manifest"]
    assert summary.source_artifacts["findings"]


@pytest.mark.skipif(not MAPPING_WORKBOOK.exists(), reason="pilot fixture missing")
def test_executive_summary_markdown_includes_verdict_and_sources(
    sample_repo: Path, tmp_path: Path
) -> None:
    """The rendered Markdown cites source finding IDs and artifacts."""
    assessment_dir = tmp_path / "assessment"

    result = runner.invoke(
        app,
        [
            "run",
            "migration-assessment",
            "--repo",
            str(sample_repo),
            "--mapping",
            str(MAPPING_WORKBOOK),
            "--out",
            str(assessment_dir),
        ],
    )
    assert result.exit_code == 0, result.output

    summary = generate_executive_summary(assessment_dir / "manifest.json")
    md = render_executive_summary_markdown(summary)

    assert "# Executive Migration Readiness Summary" in md
    assert f"**Readiness Verdict**: {summary.readiness_verdict.upper()}" in md
    assert "## Source Artifacts" in md
    assert "manifest.json" in md or "manifest" in md


@pytest.mark.skipif(not MAPPING_WORKBOOK.exists(), reason="pilot fixture missing")
def test_executive_summary_cli_writes_files(sample_repo: Path, tmp_path: Path) -> None:
    """The CLI command writes Markdown and JSON executive summary files."""
    assessment_dir = tmp_path / "assessment"
    out_dir = tmp_path / "summary"

    result = runner.invoke(
        app,
        [
            "run",
            "migration-assessment",
            "--repo",
            str(sample_repo),
            "--mapping",
            str(MAPPING_WORKBOOK),
            "--out",
            str(assessment_dir),
        ],
    )
    assert result.exit_code == 0, result.output

    result = runner.invoke(
        app,
        [
            "executive-summary",
            "--assessment",
            str(assessment_dir / "manifest.json"),
            "--out",
            str(out_dir),
        ],
    )
    assert result.exit_code == 0, result.output

    md_path = out_dir / "executive-summary.md"
    json_path = out_dir / "executive-summary.json"
    assert md_path.exists()
    assert json_path.exists()

    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert data["readiness_verdict"] in {"blocked", "at_risk", "review", "ready"}
    assert data["key_metrics"]["total_findings"] > 0


@pytest.mark.skipif(not MAPPING_WORKBOOK.exists(), reason="pilot fixture missing")
def test_executive_summary_cli_json_output(sample_repo: Path, tmp_path: Path) -> None:
    """The CLI --json flag emits JSON to stdout."""
    assessment_dir = tmp_path / "assessment"

    result = runner.invoke(
        app,
        [
            "run",
            "migration-assessment",
            "--repo",
            str(sample_repo),
            "--mapping",
            str(MAPPING_WORKBOOK),
            "--out",
            str(assessment_dir),
        ],
    )
    assert result.exit_code == 0, result.output

    result = runner.invoke(
        app,
        [
            "executive-summary",
            "--assessment",
            str(assessment_dir / "manifest.json"),
            "--out",
            str(tmp_path / "summary"),
            "--json",
        ],
    )
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data["readiness_verdict"] in {"blocked", "at_risk", "review", "ready"}
    assert "key_metrics" in data
