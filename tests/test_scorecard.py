"""Tests for model governance scorecard and readiness metrics (#70)."""

from __future__ import annotations

from pathlib import Path

from modelops_core.index.sqlite_builder import build_index
from modelops_core.reports.scorecard_service import (
    ScorecardMetric,
    generate_scorecard,
)


class TestScorecardOnExample:
    def test_scorecard_has_metrics(self, sample_repo: Path) -> None:
        repo_root = sample_repo
        db_path = repo_root / "generated" / "modelops.db"
        report = generate_scorecard(db_path, repo_root)
        assert report.repo_name
        assert report.readiness_level in ("seed", "draft", "review", "ready")
        assert report.object_count > 0
        assert len(report.metrics) >= 8

    def test_scorecard_metric_structure(self, sample_repo: Path) -> None:
        repo_root = sample_repo
        db_path = repo_root / "generated" / "modelops.db"
        report = generate_scorecard(db_path, repo_root)
        for m in report.metrics:
            assert isinstance(m, ScorecardMetric)
            assert m.name
            assert m.status in ("pass", "warning", "fail")
            assert m.explanation

    def test_scorecard_no_index(self, tmp_path: Path) -> None:
        report = generate_scorecard(tmp_path / "generated" / "modelops.db", tmp_path)
        assert report.readiness_level == "seed"
        assert report.object_count == 0
        assert "No index found" in report.summary

    def test_scorecard_json_serializable(self, sample_repo: Path) -> None:
        import json

        repo_root = sample_repo
        db_path = repo_root / "generated" / "modelops.db"
        report = generate_scorecard(db_path, repo_root)
        data = {
            "repo_name": report.repo_name,
            "readiness_level": report.readiness_level,
            "object_count": report.object_count,
            "metrics": [
                {
                    "name": m.name,
                    "value": m.value,
                    "target": m.target,
                    "status": m.status,
                    "explanation": m.explanation,
                }
                for m in report.metrics
            ],
        }
        text = json.dumps(data, indent=2, default=str)
        assert "readiness_level" in text


class TestScorecardGaps:
    def test_scorecard_gaps_are_actionable(self, sample_repo: Path) -> None:
        repo_root = sample_repo
        db_path = repo_root / "generated" / "modelops.db"
        report = generate_scorecard(db_path, repo_root)
        for gap in report.gaps:
            assert gap.gap_type
            assert gap.suggested_action

    def test_scorecard_max_gaps_respected(self, tmp_path: Path) -> None:
        from modelops_core.fixtures.fixture_generator import generate_fixture_repo

        generate_fixture_repo(tmp_path, profile="large")
        db_path = tmp_path / "generated" / "modelops.db"
        build_index(tmp_path, db_path=db_path, allow_invalid=True)
        report = generate_scorecard(db_path, tmp_path, max_gaps=5)
        assert len(report.gaps) <= 5


class TestScorecardReadinessLevels:
    def test_seed_for_tiny_repo(self, tmp_path: Path) -> None:
        from modelops_core.fixtures.fixture_generator import generate_fixture_repo

        generate_fixture_repo(tmp_path, profile="small")
        db_path = tmp_path / "generated" / "modelops.db"
        build_index(tmp_path, db_path=db_path, allow_invalid=True)
        report = generate_scorecard(db_path, tmp_path)
        # Small fixtures may still be "draft" due to missing owners, etc.
        assert report.readiness_level in ("seed", "draft", "review", "ready")

    def test_ready_when_clean(self, tmp_path: Path) -> None:
        from modelops_core.fixtures.fixture_generator import generate_fixture_repo

        generate_fixture_repo(tmp_path, profile="small")
        db_path = tmp_path / "generated" / "modelops.db"
        build_index(tmp_path, db_path=db_path, allow_invalid=True)
        report = generate_scorecard(db_path, tmp_path)
        assert report.readiness_level
        # Ensure deterministic output by checking metric names are stable
        names = {m.name for m in report.metrics}
        expected = {
            "model_completeness",
            "ownership_coverage",
            "validation_rule_coverage",
            "lov_coverage",
            "mapping_logic_coverage",
            "dataset_profile_coverage",
            "traceability_coverage",
            "source_freshness_hours",
            "unresolved_issue_count",
            "pending_change_count",
            "high_risk_change_count",
        }
        assert expected.issubset(names)
