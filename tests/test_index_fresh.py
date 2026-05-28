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

        # Wait a tiny bit, then modify a model file's content
        time.sleep(0.1)
        model_path = resolve_model_path(sample_repo)
        for f in model_path.iterdir():
            if f.is_file() and f.suffix == ".md":
                content = f.read_text(encoding="utf-8")
                f.write_text(content + "\n", encoding="utf-8")
                break

        report = check_index_freshness(sample_repo)
        assert report.fresh is False
        assert report.reason == "content hash mismatch"
        assert report.hash_mismatch is True

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

        # Modify multiple files
        time.sleep(0.1)
        model_path = resolve_model_path(sample_repo)
        modified = []
        for f in sorted(model_path.iterdir()):
            if f.is_file() and f.suffix == ".md":
                content = f.read_text(encoding="utf-8")
                f.write_text(content + "\n", encoding="utf-8")
                modified.append(str(f.name))
            if len(modified) >= 3:
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
                content = f.read_text(encoding="utf-8")
                f.write_text(content + "\n", encoding="utf-8")
                break

        result = runner.invoke(
            app, ["index-fresh", "--repo", str(sample_repo), "--json"]
        )
        assert result.exit_code == 0
        data = json.loads(result.output.strip())
        assert data["fresh"] is False
        assert data["hash_mismatch"] is True


class TestIndexFreshnessHash:
    def test_hash_mismatch_detects_content_change(self, tmp_path: Path) -> None:
        """Content changes should be detected even when mtimes are unchanged."""
        from modelops_core.index import build_index

        model_dir = tmp_path / "model"
        model_dir.mkdir()
        gen_dir = tmp_path / "generated"
        gen_dir.mkdir()

        # Create initial canonical file
        obj_path = model_dir / "DOMAIN-TEST.md"
        obj_path.write_text(
            "---\nid: DOMAIN-TEST\ntype: MasterDataDomain\nstatus: draft\nname: Test\n---\n",
            encoding="utf-8",
        )

        db_path = gen_dir / "modelops.db"
        build_index(repo_root=tmp_path, db_path=db_path)

        # Modify content without touching mtime
        original_mtime = obj_path.stat().st_mtime
        obj_path.write_text(
            "---\nid: DOMAIN-TEST\ntype: MasterDataDomain\nstatus: draft\nname: Modified\n---\n",
            encoding="utf-8",
        )
        # Restore original mtime to simulate edge case
        import os
        os.utime(obj_path, (original_mtime, original_mtime))

        report = check_index_freshness(tmp_path)
        assert report.fresh is False
        assert report.hash_mismatch is True
        assert report.reason == "content hash mismatch"
        assert report.stored_source_hash is not None
        assert report.current_source_hash is not None
        assert report.stored_source_hash != report.current_source_hash

    def test_hash_match_ignores_mtime_difference(self, tmp_path: Path) -> None:
        """If content hash matches, index should be fresh even if mtime differs."""
        from modelops_core.index import build_index

        model_dir = tmp_path / "model"
        model_dir.mkdir()
        gen_dir = tmp_path / "generated"
        gen_dir.mkdir()

        obj_path = model_dir / "DOMAIN-TEST.md"
        obj_path.write_text(
            "---\nid: DOMAIN-TEST\ntype: MasterDataDomain\nstatus: draft\nname: Test\n---\n",
            encoding="utf-8",
        )

        db_path = gen_dir / "modelops.db"
        build_index(repo_root=tmp_path, db_path=db_path)

        # Touch the file (change mtime) without changing content
        time.sleep(0.1)
        obj_path.touch()

        report = check_index_freshness(tmp_path)
        assert report.fresh is True
        assert report.hash_mismatch is False
        assert report.reason is None
        assert report.stored_source_hash == report.current_source_hash
        # mtime difference is still reported as diagnostic context
        assert len(report.stale_sources) >= 1

    def test_fallback_to_mtime_when_no_manifest_hash(self, tmp_path: Path) -> None:
        """If manifest has no source_content_hash, fall back to mtime comparison."""
        import sqlite3

        model_dir = tmp_path / "model"
        model_dir.mkdir()
        gen_dir = tmp_path / "generated"
        gen_dir.mkdir()

        obj_path = model_dir / "DOMAIN-TEST.md"
        obj_path.write_text(
            "---\nid: DOMAIN-TEST\ntype: MasterDataDomain\nstatus: draft\nname: Test\n---\n",
            encoding="utf-8",
        )

        db_path = gen_dir / "modelops.db"
        # Create a minimal DB without the manifest hash
        conn = sqlite3.connect(str(db_path))
        conn.execute(
            "CREATE TABLE index_manifest (key TEXT PRIMARY KEY, value TEXT NOT NULL)"
        )
        conn.execute(
            "INSERT INTO index_manifest (key, value) VALUES (?, ?)",
            ("build_timestamp", "2024-01-01T00:00:00Z"),
        )
        conn.commit()
        conn.close()

        # Touch file to make it newer than the DB
        time.sleep(0.1)
        obj_path.touch()

        report = check_index_freshness(tmp_path)
        assert report.fresh is False
        assert report.stored_source_hash is None
        assert report.hash_mismatch is None
        assert report.reason == "stale sources detected"
