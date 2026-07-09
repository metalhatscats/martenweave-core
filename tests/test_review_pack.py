"""Tests for the business review pack command."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from modelops_core.assessment.assessment_service import generate_review_pack
from modelops_core.cli import app

runner = CliRunner()


def test_review_pack_command_creates_all_files(sample_repo: Path, tmp_path: Path) -> None:
    out = tmp_path / "review-pack"
    result = runner.invoke(
        app, ["review-pack", "create", "--repo", str(sample_repo), "--out", str(out)]
    )
    assert result.exit_code == 0, result.output
    assert (out / "summary.md").exists()
    assert (out / "missing_owners.md").exists()
    assert (out / "fields_needing_decision.md").exists()
    assert (out / "high_risk_mappings.md").exists()
    assert (out / "signoff_checklist.md").exists()
    assert (out / "business_review.xlsx").exists()


def test_review_pack_summary_headers(sample_repo: Path, tmp_path: Path) -> None:
    out = tmp_path / "review-pack"
    runner.invoke(app, ["review-pack", "create", "--repo", str(sample_repo), "--out", str(out)])
    content = (out / "summary.md").read_text(encoding="utf-8")
    assert "# Business Review Pack" in content or "# Review Pack Summary" in content


def test_review_pack_missing_owners_has_table(sample_repo: Path, tmp_path: Path) -> None:
    out = tmp_path / "review-pack"
    runner.invoke(app, ["review-pack", "create", "--repo", str(sample_repo), "--out", str(out)])
    content = (out / "missing_owners.md").read_text(encoding="utf-8")
    assert "# Missing Owners" in content
    assert "| Object ID | Type | Name |" in content


def test_review_pack_fields_needing_decision_has_table(sample_repo: Path, tmp_path: Path) -> None:
    out = tmp_path / "review-pack"
    runner.invoke(app, ["review-pack", "create", "--repo", str(sample_repo), "--out", str(out)])
    content = (out / "fields_needing_decision.md").read_text(encoding="utf-8")
    assert "# Fields Needing Decision" in content
    assert "| Object ID | Type | Name | Reason |" in content


def test_review_pack_high_risk_mappings_has_table(sample_repo: Path, tmp_path: Path) -> None:
    out = tmp_path / "review-pack"
    runner.invoke(app, ["review-pack", "create", "--repo", str(sample_repo), "--out", str(out)])
    content = (out / "high_risk_mappings.md").read_text(encoding="utf-8")
    assert "# High Risk Mappings" in content
    assert "| Object ID | Name | Severity | Reasons |" in content


def test_review_pack_signoff_checklist_has_checkboxes(sample_repo: Path, tmp_path: Path) -> None:
    out = tmp_path / "review-pack"
    runner.invoke(app, ["review-pack", "create", "--repo", str(sample_repo), "--out", str(out)])
    content = (out / "signoff_checklist.md").read_text(encoding="utf-8")
    assert "# Sign-off Checklist" in content
    assert "- [ ]" in content


def test_review_pack_json_output(sample_repo: Path, tmp_path: Path) -> None:
    out = tmp_path / "review-pack"
    result = runner.invoke(
        app, ["review-pack", "create", "--repo", str(sample_repo), "--out", str(out), "--json"]
    )
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert "repo_name" in data
    assert "generated_at" in data
    assert "artifacts" in data
    assert len(data["artifacts"]) == 6


def test_review_pack_service_returns_paths(sample_repo: Path, tmp_path: Path) -> None:
    out = tmp_path / "review-pack"
    artifacts = generate_review_pack(sample_repo, out)
    names = {a.path.name for a in artifacts}
    expected = {
        "summary.md",
        "missing_owners.md",
        "fields_needing_decision.md",
        "high_risk_mappings.md",
        "signoff_checklist.md",
        "business_review.xlsx",
    }
    assert names == expected
