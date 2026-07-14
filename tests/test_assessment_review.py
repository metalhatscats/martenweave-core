"""Tests for the assessment-review disposition workflow."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from modelops_core.cli import app

runner = CliRunner()

MAPPING_WORKBOOK = Path(__file__).parent / "fixtures" / "pilot" / "sap_customer_mapping.xlsx"


@pytest.mark.skipif(not MAPPING_WORKBOOK.exists(), reason="pilot fixture missing")
def test_assessment_review_lifecycle(sample_repo: Path, tmp_path: Path) -> None:
    """End-to-end test for reviewing findings from an assessment."""
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
    assert (assessment_dir / "findings.json").exists()

    findings = json.loads((assessment_dir / "findings.json").read_text(encoding="utf-8"))
    assert findings["findings"]
    first_finding = findings["findings"][0]
    finding_id = first_finding["id"]

    # Record a disposition for the first finding.
    result = runner.invoke(
        app,
        [
            "assessment-review",
            "set",
            "--assessment",
            str(assessment_dir / "manifest.json"),
            "--finding-id",
            finding_id,
            "--disposition",
            "confirmed",
            "--reviewer",
            "Pilot Reviewer",
            "--note",
            "Confirmed against the mapping workbook.",
        ],
    )
    assert result.exit_code == 0, result.output
    reviews_path = assessment_dir / "finding-reviews.json"
    assert reviews_path.exists()

    reviews = json.loads(reviews_path.read_text(encoding="utf-8"))
    assert reviews["reviews"][finding_id]["disposition"] == "confirmed"
    assert reviews["reviews"][finding_id]["reviewer"] == "Pilot Reviewer"

    # Update the same finding; latest state should be preserved.
    result = runner.invoke(
        app,
        [
            "assessment-review",
            "set",
            "--assessment",
            str(assessment_dir / "manifest.json"),
            "--finding-id",
            finding_id,
            "--disposition",
            "false_positive",
            "--reviewer",
            "Pilot Reviewer",
            "--note",
            "Re-classified after closer inspection.",
        ],
    )
    assert result.exit_code == 0, result.output
    reviews = json.loads(reviews_path.read_text(encoding="utf-8"))
    assert reviews["reviews"][finding_id]["disposition"] == "false_positive"

    # Summarize reviews.
    result = runner.invoke(
        app,
        [
            "assessment-review",
            "summary",
            "--assessment",
            str(assessment_dir / "manifest.json"),
        ],
    )
    assert result.exit_code == 0, result.output
    assert "false_positive" in result.output

    # Promote a confirmed finding to a PatchProposal.
    second_finding = findings["findings"][1]
    result = runner.invoke(
        app,
        [
            "assessment-review",
            "set",
            "--assessment",
            str(assessment_dir / "manifest.json"),
            "--finding-id",
            second_finding["id"],
            "--disposition",
            "confirmed",
            "--reviewer",
            "Pilot Reviewer",
            "--note",
            "Needs follow-up.",
        ],
    )
    assert result.exit_code == 0, result.output

    result = runner.invoke(
        app,
        [
            "assessment-review",
            "promote",
            "--assessment",
            str(assessment_dir / "manifest.json"),
            "--finding-id",
            second_finding["id"],
            "--repo",
            str(sample_repo),
        ],
    )
    assert result.exit_code == 0, result.output
    assert (sample_repo / "model" / "patch-proposals").exists()
    proposals = list((sample_repo / "model" / "patch-proposals").glob("*.md"))
    assert proposals
