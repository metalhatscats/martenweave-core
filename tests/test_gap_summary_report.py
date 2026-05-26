"""Tests for the consolidated gap summary report command."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from modelops_core.cli import app
from modelops_core.index.sqlite_builder import build_index
from modelops_core.reports.gap_summary import generate_gap_summary_report

runner = CliRunner()


def _init_repo(tmp_path: Path) -> Path:
    """Create a minimal temp repo with config, model, generated dirs."""
    model_dir = tmp_path / "model"
    model_dir.mkdir()
    generated_dir = tmp_path / "generated"
    generated_dir.mkdir()

    (model_dir / "DOMAIN-TEST.md").write_text(
        "---\nid: DOMAIN-TEST\ntype: MasterDataDomain\nstatus: draft\n"
        "name: Test Domain\nschema_version: '1.0'\n---\n",
        encoding="utf-8",
    )
    (model_dir / "ATTR-TEST.md").write_text(
        "---\nid: ATTR-TEST\ntype: Attribute\nstatus: draft\n"
        "name: Test Attribute\ndomain: DOMAIN-TEST\n"
        "schema_version: '1.0'\n---\n",
        encoding="utf-8",
    )

    (tmp_path / "modelops.config.yaml").write_text(
        "model_dir: model\ngenerated_dir: generated\n", encoding="utf-8"
    )

    build_index(repo_root=tmp_path, db_path=generated_dir / "modelops.db")
    return tmp_path


def test_gap_report_zero_gaps(tmp_path: Path) -> None:
    # Empty repo with no objects should report zero gaps
    model_dir = tmp_path / "model"
    model_dir.mkdir()
    generated_dir = tmp_path / "generated"
    generated_dir.mkdir()
    (tmp_path / "modelops.config.yaml").write_text(
        "model_dir: model\ngenerated_dir: generated\n", encoding="utf-8"
    )
    build_index(repo_root=tmp_path, db_path=generated_dir / "modelops.db")
    result = runner.invoke(app, ["gap-report", "--repo", str(tmp_path), "--json"])
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert "gaps_by_type" in data
    assert data["total_gap_count"] == 0
    assert data["gap_score"] == 0.0
    assert data["top_objects"] == []


def test_gap_report_no_index(tmp_path: Path) -> None:
    (tmp_path / "modelops.config.yaml").write_text(
        "model_dir: model\ngenerated_dir: generated\n", encoding="utf-8"
    )
    result = runner.invoke(app, ["gap-report", "--repo", str(tmp_path)])
    assert result.exit_code == 1
    assert "No index found" in result.output


def test_gap_report_json_contract(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    result = runner.invoke(app, ["gap-report", "--repo", str(repo), "--json"])
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert "gaps_by_type" in data
    assert "total_gap_count" in data
    assert "gap_score" in data
    assert "top_objects" in data
    assert "total_objects" in data
    assert "sources_checked" in data
    assert isinstance(data["gaps_by_type"], dict)


def test_gap_report_missing_owner_detected(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    # ATTR-TEST has no owner, so it should appear as a gap
    result = runner.invoke(app, ["gap-report", "--repo", str(repo), "--json"])
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data["total_gap_count"] > 0
    gap_types = list(data["gaps_by_type"].keys())
    assert any("owner" in gt.lower() for gt in gap_types)


def test_gap_report_deterministic_samples(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    result1 = runner.invoke(app, ["gap-report", "--repo", str(repo), "--json"])
    result2 = runner.invoke(app, ["gap-report", "--repo", str(repo), "--json"])
    assert result1.output == result2.output


def test_gap_report_human_output(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    result = runner.invoke(app, ["gap-report", "--repo", str(repo)])
    assert result.exit_code == 0, result.output
    assert "Gap Summary Report" in result.output
    assert "Total objects" in result.output


def test_gap_report_does_not_mutate_files(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    attr_path = repo / "model" / "ATTR-TEST.md"
    mtime_before = attr_path.stat().st_mtime
    result = runner.invoke(app, ["gap-report", "--repo", str(repo), "--json"])
    assert result.exit_code == 0, result.output
    mtime_after = attr_path.stat().st_mtime
    assert mtime_before == mtime_after


def test_gap_report_service_directly(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    db_path = repo / "generated" / "modelops.db"
    report = generate_gap_summary_report(db_path, repo)
    assert report.total_objects >= 2
    assert isinstance(report.gaps_by_type, dict)
    assert isinstance(report.gap_score, float)
    assert 0.0 <= report.gap_score <= 1.0


def test_gap_report_deduplicates_per_type(tmp_path: Path) -> None:
    """Same object should only appear once per gap type."""
    repo = _init_repo(tmp_path)
    db_path = repo / "generated" / "modelops.db"
    report = generate_gap_summary_report(db_path, repo)
    for summary in report.gaps_by_type.values():
        assert len(summary.sample_object_ids) == len(set(summary.sample_object_ids))
