"""Tests for pilot outcome report generation."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from modelops_core.cli import app

runner = CliRunner()


def _build_assessment_with_reviews(
    tmp_path: Path,
    dispositions: dict[str, str],
) -> Path:
    """Create a fake assessment manifest and finding-reviews file."""
    assessment_dir = tmp_path / "assessment"
    assessment_dir.mkdir()

    findings = []
    for idx, (finding_id, _disposition) in enumerate(dispositions.items()):
        findings.append(
            {
                "id": finding_id,
                "category": "missing_owner" if idx % 2 == 0 else "missing_mapping",
                "severity": "high" if idx % 3 == 0 else "medium",
            }
        )

    (assessment_dir / "findings.json").write_text(
        json.dumps({"finding_count": len(findings), "findings": findings}, indent=2),
        encoding="utf-8",
    )

    reviews = {"reviews": {}, "history": []}
    for finding_id, disposition in dispositions.items():
        reviews["reviews"][finding_id] = {
            "disposition": disposition,
            "reviewer": "Pilot Reviewer",
            "note": "Reviewed.",
            "timestamp": "2026-01-01T00:00:00Z",
        }

    (assessment_dir / "finding-reviews.json").write_text(
        json.dumps(reviews, indent=2), encoding="utf-8"
    )

    (assessment_dir / "manifest.json").write_text(
        json.dumps(
            {
                "martenweave_version": "0.4.1",
                "repo_name": "Test Pilot",
                "repo_path": "/tmp/test-repo",
                "generated_at": "2026-01-01T00:00:00Z",
                "inputs": {},
                "stage_statuses": [
                    {"name": "validation", "status": "success", "message": ""},
                    {"name": "mapping_profile", "status": "success", "message": ""},
                ],
                "generated_artifacts": [],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    return assessment_dir


def test_pilot_outcome_recommends_continue(tmp_path: Path) -> None:
    assessment_dir = _build_assessment_with_reviews(
        tmp_path,
        {
            "f1": "confirmed",
            "f2": "confirmed",
            "f3": "accepted_risk",
            "f4": "false_positive",
        },
    )
    out = tmp_path / "outcome.md"

    result = runner.invoke(
        app,
        [
            "pilot-outcome",
            "--assessment",
            str(assessment_dir / "manifest.json"),
            "--out",
            str(out),
        ],
    )
    assert result.exit_code == 0, result.output
    assert out.exists()
    content = out.read_text(encoding="utf-8")
    assert "continue" in content.lower()


def test_pilot_outcome_recommends_pivot_when_high_false_positive_rate(tmp_path: Path) -> None:
    assessment_dir = _build_assessment_with_reviews(
        tmp_path,
        {
            "f1": "false_positive",
            "f2": "false_positive",
            "f3": "false_positive",
            "f4": "confirmed",
        },
    )
    out = tmp_path / "outcome.md"

    result = runner.invoke(
        app,
        ["pilot-outcome", "--assessment", str(assessment_dir / "manifest.json"), "--out", str(out)],
    )
    assert result.exit_code == 0, result.output
    content = out.read_text(encoding="utf-8")
    assert "pivot" in content.lower()


def test_pilot_outcome_shows_missing_baselines(tmp_path: Path) -> None:
    assessment_dir = _build_assessment_with_reviews(tmp_path, {"f1": "confirmed"})
    out = tmp_path / "outcome.md"

    result = runner.invoke(
        app,
        ["pilot-outcome", "--assessment", str(assessment_dir / "manifest.json"), "--out", str(out)],
    )
    assert result.exit_code == 0, result.output
    content = out.read_text(encoding="utf-8")
    assert "unavailable" in content.lower() or "not provided" in content.lower()


def test_pilot_outcome_json_output_includes_metrics(tmp_path: Path) -> None:
    assessment_dir = _build_assessment_with_reviews(
        tmp_path,
        {
            "f1": "confirmed",
            "f2": "confirmed",
            "f3": "false_positive",
        },
    )
    out_md = tmp_path / "outcome.md"
    out_json = tmp_path / "outcome.json"

    result = runner.invoke(
        app,
        [
            "pilot-outcome",
            "--assessment",
            str(assessment_dir / "manifest.json"),
            "--out",
            str(out_md),
            "--json-out",
            str(out_json),
        ],
    )
    assert result.exit_code == 0, result.output
    data = json.loads(out_json.read_text(encoding="utf-8"))
    assert data["total_findings"] == 3
    assert data["confirmed_findings"] == 2
    assert data["false_positives"] == 1
    assert "false_positive_rate" in data
    assert "recommendation" in data


def test_pilot_outcome_missing_reviews_file_is_not_blocking(tmp_path: Path) -> None:
    assessment_dir = tmp_path / "assessment"
    assessment_dir.mkdir()
    (assessment_dir / "findings.json").write_text(
        json.dumps({"finding_count": 1, "findings": [{"id": "f1", "severity": "high"}]}, indent=2),
        encoding="utf-8",
    )
    (assessment_dir / "manifest.json").write_text(
        json.dumps(
            {
                "martenweave_version": "0.4.1",
                "repo_name": "Test",
                "repo_path": "/tmp/test",
                "generated_at": "2026-01-01T00:00:00Z",
                "inputs": {},
                "stage_statuses": [],
                "generated_artifacts": [],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    out = tmp_path / "outcome.md"

    result = runner.invoke(
        app,
        ["pilot-outcome", "--assessment", str(assessment_dir / "manifest.json"), "--out", str(out)],
    )
    assert result.exit_code == 0, result.output
    content = out.read_text(encoding="utf-8")
    assert "insufficient_evidence" in content.lower() or "no reviews" in content.lower()
