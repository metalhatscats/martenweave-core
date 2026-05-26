"""Tests for the clean command and build-index dry-run mode."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from modelops_core.cli import app

runner = CliRunner()


def test_clean_dry_run_lists_files(sample_repo: Path) -> None:
    """Dry-run should list generated files without deleting them."""
    result = runner.invoke(app, ["clean", "--repo", str(sample_repo), "--dry-run"])
    assert result.exit_code == 0
    assert "Dry-run" in result.output


def test_clean_dry_run_json(sample_repo: Path) -> None:
    """Dry-run with --json should return parseable JSON."""
    result = runner.invoke(
        app, ["clean", "--repo", str(sample_repo), "--dry-run", "--json"]
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["dry_run"] is True
    assert "generated_path" in data
    assert "removed_count" in data
    assert "skipped_count" in data


def test_clean_removes_generated_files(tmp_path: Path) -> None:
    """Clean should remove .jsonl and .db files in generated/."""
    repo = tmp_path / "repo"
    repo.mkdir()
    generated = repo / "generated"
    generated.mkdir()

    # Create some generated artifacts
    (generated / "modelops.db").write_text("db", encoding="utf-8")
    (generated / "search_documents.jsonl").write_text("jsonl", encoding="utf-8")
    (generated / "lineage_edges.jsonl").write_text("jsonl", encoding="utf-8")
    (generated / "modelops.db.tmp").write_text("tmp", encoding="utf-8")

    profile_dir = generated / "dataset_profiles"
    profile_dir.mkdir()
    (profile_dir / "sample.json").write_text("profile", encoding="utf-8")

    result = runner.invoke(app, ["clean", "--repo", str(repo)])
    assert result.exit_code == 0
    assert "Cleaned" in result.output
    assert not (generated / "modelops.db").exists()
    assert not (generated / "search_documents.jsonl").exists()
    assert not (generated / "lineage_edges.jsonl").exists()
    assert not (generated / "modelops.db.tmp").exists()
    assert not (profile_dir / "sample.json").exists()


def test_clean_json_output(tmp_path: Path) -> None:
    """Clean --json should report removed files."""
    repo = tmp_path / "repo"
    repo.mkdir()
    generated = repo / "generated"
    generated.mkdir()
    (generated / "modelops.db").write_text("db", encoding="utf-8")

    result = runner.invoke(app, ["clean", "--repo", str(repo), "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["dry_run"] is False
    assert data["removed_count"] >= 1
    assert any("modelops.db" in p for p in data["removed"])


def test_clean_safety_refuses_outside_repo(tmp_path: Path) -> None:
    """Clean must refuse if generated/ resolves outside repo root."""
    repo = tmp_path / "repo"
    repo.mkdir()
    # Create a symlink or config that points generated outside repo
    config = repo / "modelops.config.yaml"
    config.write_text(
        "name: test\ngenerated_path: ../outside_generated\n",
        encoding="utf-8",
    )
    outside = tmp_path / "outside_generated"
    outside.mkdir()

    result = runner.invoke(app, ["clean", "--repo", str(repo)])
    assert result.exit_code == 1
    assert "Refusing to clean" in result.output


def test_clean_no_generated_dir(tmp_path: Path) -> None:
    """Clean should succeed when generated directory does not exist."""
    repo = tmp_path / "repo"
    repo.mkdir()
    result = runner.invoke(app, ["clean", "--repo", str(repo)])
    assert result.exit_code == 0


def test_build_index_dry_run_does_not_write_db(sample_repo: Path) -> None:
    """build-index --dry-run must not create or modify the database."""
    db_path = sample_repo / "generated" / "modelops.db"
    # Remove existing DB if present to be certain
    if db_path.exists():
        db_path.unlink()

    result = runner.invoke(
        app, ["build-index", "--repo", str(sample_repo), "--dry-run"]
    )
    assert result.exit_code == 0
    assert "Dry-run" in result.output
    assert not db_path.exists()


def test_build_index_dry_run_with_jsonl(sample_repo: Path) -> None:
    """build-index --dry-run --jsonl must not write JSONL exports."""
    gen = sample_repo / "generated"
    search_jsonl = gen / "search_documents.jsonl"
    lineage_jsonl = gen / "lineage_edges.jsonl"
    if search_jsonl.exists():
        search_jsonl.unlink()
    if lineage_jsonl.exists():
        lineage_jsonl.unlink()

    result = runner.invoke(
        app, ["build-index", "--repo", str(sample_repo), "--dry-run", "--jsonl"]
    )
    assert result.exit_code == 0
    assert not search_jsonl.exists()
    assert not lineage_jsonl.exists()


def test_build_index_dry_run_reports_validation(sample_repo: Path) -> None:
    """build-index --dry-run should still report validation results."""
    result = runner.invoke(
        app, ["build-index", "--repo", str(sample_repo), "--dry-run"]
    )
    assert result.exit_code == 0
    assert "Valid:" in result.output
