"""Tests for model summary report command."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from modelops_core.cli import app

runner = CliRunner()


class TestModelSummaryReport:
    def test_creates_markdown_report_for_domain(self, sample_repo: Path) -> None:
        out_path = sample_repo / "generated" / "reports" / "customer-bp-summary.md"
        result = runner.invoke(
            app,
            [
                "model-summary",
                "--repo",
                str(sample_repo),
                "--domain",
                "DOMAIN-CUSTOMER-BP",
                "--out",
                str(out_path),
            ],
        )
        assert result.exit_code == 0, result.output
        assert out_path.exists()
        text = out_path.read_text(encoding="utf-8")
        assert "# Model Summary:" in text
        assert "DOMAIN-CUSTOMER-BP" in text
        assert "## Attributes" in text
        assert "## Target fields" in text
        assert "## Validation scope" in text
        assert "`ATTR-" in text
        assert "`FEP-" in text

    def test_json_output_includes_expected_structure(self, sample_repo: Path) -> None:
        result = runner.invoke(
            app,
            [
                "model-summary",
                "--repo",
                str(sample_repo),
                "--domain",
                "DOMAIN-CUSTOMER-BP",
                "--json",
            ],
        )
        assert result.exit_code == 0, result.output
        data = json.loads(result.output)
        assert data["domain_id"] == "DOMAIN-CUSTOMER-BP"
        assert data["object_count"] > 0
        assert "Attribute" in data["type_counts"]
        assert len(data["attributes"]) > 0
        assert "validation_summary" in data
        assert "coverage_gaps" in data
        assert "open_issues" in data
        assert "owners" in data

    def test_no_domain_summarizes_repository(self, sample_repo: Path) -> None:
        result = runner.invoke(
            app,
            [
                "model-summary",
                "--repo",
                str(sample_repo),
                "--json",
            ],
        )
        assert result.exit_code == 0, result.output
        data = json.loads(result.output)
        assert data["domain_id"] is None
        assert data["object_count"] > 0

    def test_requires_index(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        model_dir = repo / "model"
        model_dir.mkdir(parents=True)
        out_path = repo / "summary.md"
        result = runner.invoke(
            app,
            [
                "model-summary",
                "--repo",
                str(repo),
                "--out",
                str(out_path),
            ],
        )
        assert result.exit_code == 1
        assert "build-index" in result.output

    def test_markdown_contains_risks_and_decisions(self, sample_repo: Path) -> None:
        out_path = sample_repo / "generated" / "reports" / "customer-bp-summary-risks.md"
        result = runner.invoke(
            app,
            [
                "model-summary",
                "--repo",
                str(sample_repo),
                "--domain",
                "DOMAIN-CUSTOMER-BP",
                "--out",
                str(out_path),
            ],
        )
        assert result.exit_code == 0, result.output
        text = out_path.read_text(encoding="utf-8")
        assert "## Validation scope" in text
        assert "## Owners" in text
        assert "## Evidence references" in text
        assert "## Source fields" in text
