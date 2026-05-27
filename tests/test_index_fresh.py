"""Tests for index freshness check command and service."""

from __future__ import annotations

import json
import time
from pathlib import Path

from typer.testing import CliRunner

from modelops_core.cli import app
from modelops_core.config import resolve_generated_path, resolve_model_path
from modelops_core.reports.index_freshness import check_index_freshness

runner = CliRunner()


class TestIndexFreshnessService:
    def test_no_index(self, sample_repo: Path) -> None:
        # Ensure no index exists
        db_path = resolve_generated_path(sample_repo) / "modelops.db"
        if db_path.exists():
            db_path.unlink()
        report = check_index_freshness(sample_repo)
        assert report.fresh is False
        assert report.reason == "no index"
        assert report.db_mtime is None

    def test_fresh_index(self, sample_repo: Path) -> None:
        # Build index first
        result = runner.invoke(app, ["build-index", "--repo", str(sample_repo)])
        assert result.exit_code == 0

        report = check_index_freshness(sample_repo)
        assert report.fresh is True
        assert report.reason is None
        assert report.db_mtime is not None
        assert report.newest_source_mtime is not None
        assert report.stale_sources == []

    def test_stale_index(self, sample_repo: Path) -> None:
        # Build index first
        result = runner.invoke(app, ["build-index", "--repo", str(sample_repo)])
        assert result.exit_code == 0

        # Wait a tiny bit, then touch a model file
        time.sleep(0.1)
        model_path = resolve_model_path(sample_repo)
        for f in model_path.iterdir():
            if f.is_file() and f.suffix == ".md":
                f.touch()
                break

        report = check_index_freshness(sample_repo)
        assert report.fresh is False
        assert report.reason == "stale sources detected"
        assert len(report.stale_sources) >= 1

    def test_empty_repo(self, tmp_path: Path) -> None:
        repo = tmp_path / "empty-repo"
        repo.mkdir()
        model_dir = repo / "model"
        model_dir.mkdir()
        gen_dir = repo / "generated"
        gen_dir.mkdir()
        # Create empty DB
        (gen_dir / "modelops.db").write_text("")

        report = check_index_freshness(repo)
        assert report.fresh is True
        assert report.reason == "no canonical files"

    def test_deterministic_sorting(self, sample_repo: Path) -> None:
        # Build index first
        result = runner.invoke(app, ["build-index", "--repo", str(sample_repo)])
        assert result.exit_code == 0

        # Touch multiple files
        time.sleep(0.1)
        model_path = resolve_model_path(sample_repo)
        touched = []
        for f in sorted(model_path.iterdir()):
            if f.is_file() and f.suffix == ".md":
                f.touch()
                touched.append(str(f.name))
            if len(touched) >= 3:
                break

        report = check_index_freshness(sample_repo)
        assert report.fresh is False
        # stale_sources should be sorted
        assert report.stale_sources == sorted(report.stale_sources)


class TestIndexFreshCLI:
    def test_cli_json_no_index(self, sample_repo: Path) -> None:
        db_path = resolve_generated_path(sample_repo) / "modelops.db"
        if db_path.exists():
            db_path.unlink()
        result = runner.invoke(
            app, ["index-fresh", "--repo", str(sample_repo), "--json"]
        )
        assert result.exit_code == 0
        data = json.loads(result.output.strip())
        assert "fresh" in data
        assert data["fresh"] is False
        assert "db_path" in data
        assert "newest_source_mtime" in data
        assert "reason" in data
        assert "stale_sources" in data
        assert data["reason"] == "no index"

    def test_cli_json_fresh(self, sample_repo: Path) -> None:
        runner.invoke(app, ["build-index", "--repo", str(sample_repo)])
        result = runner.invoke(
            app, ["index-fresh", "--repo", str(sample_repo), "--json"]
        )
        assert result.exit_code == 0
        data = json.loads(result.output.strip())
        assert data["fresh"] is True
        assert data["reason"] is None
        assert data["stale_sources"] == []
        assert "martenweave_version" in data

    def test_cli_human_readable_no_index(self, sample_repo: Path) -> None:
        db_path = resolve_generated_path(sample_repo) / "modelops.db"
        if db_path.exists():
            db_path.unlink()
        result = runner.invoke(app, ["index-fresh", "--repo", str(sample_repo)])
        assert result.exit_code == 0
        assert "Index freshness:" in result.output
        assert "stale" in result.output.lower()
        assert "no index" in result.output.lower()

    def test_cli_human_readable_fresh(self, sample_repo: Path) -> None:
        runner.invoke(app, ["build-index", "--repo", str(sample_repo)])
        result = runner.invoke(app, ["index-fresh", "--repo", str(sample_repo)])
        assert result.exit_code == 0
        assert "Index freshness:" in result.output
        assert "fresh" in result.output.lower()

    def test_cli_json_stale(self, sample_repo: Path) -> None:
        runner.invoke(app, ["build-index", "--repo", str(sample_repo)])
        time.sleep(0.1)
        model_path = resolve_model_path(sample_repo)
        for f in model_path.iterdir():
            if f.is_file() and f.suffix == ".md":
                f.touch()
                break

        result = runner.invoke(
            app, ["index-fresh", "--repo", str(sample_repo), "--json"]
        )
        assert result.exit_code == 0
        data = json.loads(result.output.strip())
        assert data["fresh"] is False
        assert len(data["stale_sources"]) >= 1
