"""Tests for lifecycle summary and roadmap metadata (#92)."""

from __future__ import annotations

from pathlib import Path

from modelops_core.reports.analysis_service import generate_analysis_report
from modelops_core.schemas.common import GeneralStatus


class TestGeneralStatus:
    def test_all_lifecycle_values_present(self) -> None:
        values = {s.value for s in GeneralStatus}
        expected = {
            "proposed",
            "draft",
            "active",
            "under_review",
            "deprecated",
            "retired",
            "blocked",
            "planned",
            "implemented",
            "archived",
        }
        assert values == expected


class TestLifecycleSummary:
    def test_empty_repo(self, tmp_path: Path) -> None:
        from modelops_core.fixtures.fixture_generator import generate_fixture_repo
        from modelops_core.index.sqlite_builder import build_index

        generate_fixture_repo(tmp_path, profile="minimal")
        build_index(tmp_path, max_objects=10_000, allow_invalid=True)
        db_path = tmp_path / "generated" / "modelops.db"
        report = generate_analysis_report(db_path, tmp_path)
        assert report.lifecycle_summary is not None
        assert report.lifecycle_summary.active >= 0

    def test_counts_by_status(self, tmp_path: Path) -> None:
        from modelops_core.fixtures.fixture_generator import generate_fixture_repo
        from modelops_core.index.sqlite_builder import build_index

        generate_fixture_repo(tmp_path, profile="small")
        build_index(tmp_path, max_objects=10_000, allow_invalid=True)
        db_path = tmp_path / "generated" / "modelops.db"
        report = generate_analysis_report(db_path, tmp_path)
        ls = report.lifecycle_summary
        assert ls is not None
        total = (
            ls.proposed
            + ls.draft
            + ls.active
            + ls.under_review
            + ls.deprecated
            + ls.retired
            + ls.blocked
            + ls.planned
            + ls.implemented
            + ls.other
        )
        assert total == report.object_count

    def test_roadmap_fields_counted(self, tmp_path: Path) -> None:
        from modelops_core.index.sqlite_builder import build_index

        # Create a minimal model with target_release and roadmap_priority
        repo_dir = tmp_path / "repo"
        repo_dir.mkdir()
        model_dir = repo_dir / "model"
        model_dir.mkdir()
        (repo_dir / "modelops.config.yaml").write_text(
            'name: "Test"\nversion: "1.0.0"\nschema_version: "1.0"\n',
            encoding="utf-8",
        )
        (model_dir / "ATTR-TEST-01.md").write_text(
            "---\n"
            "id: ATTR-TEST-01\n"
            "type: Attribute\n"
            "status: draft\n"
            "name: Test Attribute\n"
            'target_release: "v1.0"\n'
            "roadmap_priority: high\n"
            "---\n\n"
            "# Test\n",
            encoding="utf-8",
        )
        build_index(repo_dir, max_objects=10_000, allow_invalid=True)
        db_path = repo_dir / "generated" / "modelops.db"
        report = generate_analysis_report(db_path, repo_dir)
        ls = report.lifecycle_summary
        assert ls is not None
        assert ls.draft == 1
        assert ls.with_target_release == 1
        assert ls.with_roadmap_priority == 1
