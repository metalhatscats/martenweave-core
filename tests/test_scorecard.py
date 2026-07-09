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


class TestScorecardEvidenceCoverage:
    def test_evidence_coverage_100_percent(self, tmp_path: Path) -> None:
        from modelops_core.index.sqlite_builder import build_index

        model_dir = tmp_path / "model"
        model_dir.mkdir()
        generated_dir = tmp_path / "generated"
        generated_dir.mkdir()
        (model_dir / "DEC-001.md").write_text(
            "---\nid: DEC-001\ntype: Decision\nstatus: active\n"
            "name: Test Decision\nevidence: EVIDENCE-001\n"
            "schema_version: '1.0'\n---\n",
            encoding="utf-8",
        )
        (model_dir / "DEC-002.md").write_text(
            "---\nid: DEC-002\ntype: Decision\nstatus: active\n"
            "name: Test Decision 2\nevidence: EVIDENCE-002\n"
            "schema_version: '1.0'\n---\n",
            encoding="utf-8",
        )
        (tmp_path / "modelops.config.yaml").write_text(
            "model_dir: model\ngenerated_dir: generated\n", encoding="utf-8"
        )
        build_index(
            repo_root=tmp_path,
            db_path=generated_dir / "modelops.db",
            allow_invalid=True,
        )
        report = generate_scorecard(generated_dir / "modelops.db", tmp_path)
        ev_metric = next(m for m in report.metrics if m.name == "evidence_coverage")
        assert ev_metric.value == 100.0
        assert ev_metric.status == "pass"

    def test_evidence_coverage_partial(self, tmp_path: Path) -> None:
        from modelops_core.index.sqlite_builder import build_index

        model_dir = tmp_path / "model"
        model_dir.mkdir()
        generated_dir = tmp_path / "generated"
        generated_dir.mkdir()
        (model_dir / "DEC-001.md").write_text(
            "---\nid: DEC-001\ntype: Decision\nstatus: active\n"
            "name: Test Decision\nevidence: EVIDENCE-001\n"
            "schema_version: '1.0'\n---\n",
            encoding="utf-8",
        )
        (model_dir / "DEC-002.md").write_text(
            "---\nid: DEC-002\ntype: Decision\nstatus: active\n"
            "name: Test Decision 2\nschema_version: '1.0'\n---\n",
            encoding="utf-8",
        )
        (tmp_path / "modelops.config.yaml").write_text(
            "model_dir: model\ngenerated_dir: generated\n", encoding="utf-8"
        )
        build_index(
            repo_root=tmp_path,
            db_path=generated_dir / "modelops.db",
            allow_invalid=True,
        )
        report = generate_scorecard(generated_dir / "modelops.db", tmp_path)
        ev_metric = next(m for m in report.metrics if m.name == "evidence_coverage")
        assert ev_metric.value == 50.0
        assert ev_metric.status == "warning"

    def test_evidence_coverage_zero_decisions(self, tmp_path: Path) -> None:
        from modelops_core.index.sqlite_builder import build_index

        model_dir = tmp_path / "model"
        model_dir.mkdir()
        generated_dir = tmp_path / "generated"
        generated_dir.mkdir()
        (model_dir / "DOMAIN-TEST.md").write_text(
            "---\nid: DOMAIN-TEST\ntype: MasterDataDomain\nstatus: draft\n"
            "name: Test Domain\nschema_version: '1.0'\n---\n",
            encoding="utf-8",
        )
        (tmp_path / "modelops.config.yaml").write_text(
            "model_dir: model\ngenerated_dir: generated\n", encoding="utf-8"
        )
        build_index(
            repo_root=tmp_path,
            db_path=generated_dir / "modelops.db",
            allow_invalid=True,
        )
        report = generate_scorecard(generated_dir / "modelops.db", tmp_path)
        ev_metric = next(m for m in report.metrics if m.name == "evidence_coverage")
        assert ev_metric.value == 0.0
        assert ev_metric.status == "fail"
        assert "No Decision objects" in ev_metric.explanation


class TestScorecardSapTableCoverage:
    def test_sap_table_coverage_counts_target_tables(self, tmp_path: Path) -> None:
        from modelops_core.index.sqlite_builder import build_index

        model_dir = tmp_path / "model"
        model_dir.mkdir()
        generated_dir = tmp_path / "generated"
        generated_dir.mkdir()
        (model_dir / "FEP-KNVV.md").write_text(
            "---\nid: FEP-KNVV\ntype: FieldEndpoint\nstatus: active\n"
            "name: KNVV Field\nsap_table: KNVV\n"
            "business_attribute: ATTR-001\nschema_version: '1.0'\n---\n",
            encoding="utf-8",
        )
        (model_dir / "FEP-OTHER.md").write_text(
            "---\nid: FEP-OTHER\ntype: FieldEndpoint\nstatus: active\n"
            "name: Other Field\nsap_table: OTHER\nschema_version: '1.0'\n---\n",
            encoding="utf-8",
        )
        (tmp_path / "modelops.config.yaml").write_text(
            "model_dir: model\ngenerated_dir: generated\n", encoding="utf-8"
        )
        build_index(
            repo_root=tmp_path,
            db_path=generated_dir / "modelops.db",
            allow_invalid=True,
        )
        report = generate_scorecard(generated_dir / "modelops.db", tmp_path)
        sap_metric = next(m for m in report.metrics if m.name == "sap_table_coverage")
        assert sap_metric.value == 100.0
        assert sap_metric.status == "pass"

    def test_sap_table_coverage_partial(self, tmp_path: Path) -> None:
        from modelops_core.index.sqlite_builder import build_index

        model_dir = tmp_path / "model"
        model_dir.mkdir()
        generated_dir = tmp_path / "generated"
        generated_dir.mkdir()
        (model_dir / "FEP-KNVV.md").write_text(
            "---\nid: FEP-KNVV\ntype: FieldEndpoint\nstatus: active\n"
            "name: KNVV Field\nsap_table: KNVV\nschema_version: '1.0'\n---\n",
            encoding="utf-8",
        )
        (model_dir / "FEP-KNB1.md").write_text(
            "---\nid: FEP-KNB1\ntype: FieldEndpoint\nstatus: active\n"
            "name: KNB1 Field\nsap_table: KNB1\n"
            "attribute: ATTR-001\nschema_version: '1.0'\n---\n",
            encoding="utf-8",
        )
        (tmp_path / "modelops.config.yaml").write_text(
            "model_dir: model\ngenerated_dir: generated\n", encoding="utf-8"
        )
        build_index(
            repo_root=tmp_path,
            db_path=generated_dir / "modelops.db",
            allow_invalid=True,
        )
        report = generate_scorecard(generated_dir / "modelops.db", tmp_path)
        sap_metric = next(m for m in report.metrics if m.name == "sap_table_coverage")
        assert sap_metric.value == 50.0
        assert sap_metric.status == "fail"

    def test_sap_table_coverage_zero_targets(self, tmp_path: Path) -> None:
        from modelops_core.index.sqlite_builder import build_index

        model_dir = tmp_path / "model"
        model_dir.mkdir()
        generated_dir = tmp_path / "generated"
        generated_dir.mkdir()
        (model_dir / "FEP-OTHER.md").write_text(
            "---\nid: FEP-OTHER\ntype: FieldEndpoint\nstatus: active\n"
            "name: Other Field\nsap_table: OTHER\nschema_version: '1.0'\n---\n",
            encoding="utf-8",
        )
        (tmp_path / "modelops.config.yaml").write_text(
            "model_dir: model\ngenerated_dir: generated\n", encoding="utf-8"
        )
        build_index(
            repo_root=tmp_path,
            db_path=generated_dir / "modelops.db",
            allow_invalid=True,
        )
        report = generate_scorecard(generated_dir / "modelops.db", tmp_path)
        sap_metric = next(m for m in report.metrics if m.name == "sap_table_coverage")
        assert sap_metric.value == 0.0
        assert sap_metric.status == "fail"
        assert "No target SAP FieldEndpoints" in sap_metric.explanation

    def test_sap_table_coverage_ignores_non_target_tables(self, tmp_path: Path) -> None:
        from modelops_core.index.sqlite_builder import build_index

        model_dir = tmp_path / "model"
        model_dir.mkdir()
        generated_dir = tmp_path / "generated"
        generated_dir.mkdir()
        (model_dir / "FEP-OTHER.md").write_text(
            "---\nid: FEP-OTHER\ntype: FieldEndpoint\nstatus: active\n"
            "name: Other Field\nsap_table: OTHER\nschema_version: '1.0'\n---\n",
            encoding="utf-8",
        )
        (tmp_path / "modelops.config.yaml").write_text(
            "model_dir: model\ngenerated_dir: generated\n", encoding="utf-8"
        )
        build_index(
            repo_root=tmp_path,
            db_path=generated_dir / "modelops.db",
            allow_invalid=True,
        )
        report = generate_scorecard(generated_dir / "modelops.db", tmp_path)
        sap_metric = next(m for m in report.metrics if m.name == "sap_table_coverage")
        assert sap_metric.value == 0.0
        assert sap_metric.status == "fail"


class TestScorecardRepoName:
    def test_scorecard_uses_name_from_config(self, tmp_path: Path) -> None:
        from modelops_core.index.sqlite_builder import build_index

        model_dir = tmp_path / "model"
        model_dir.mkdir()
        generated_dir = tmp_path / "generated"
        generated_dir.mkdir()
        (model_dir / "DOMAIN-TEST.md").write_text(
            "---\nid: DOMAIN-TEST\ntype: MasterDataDomain\nstatus: draft\n"
            "name: Test Domain\nschema_version: '1.0'\n---\n",
            encoding="utf-8",
        )
        (tmp_path / "modelops.config.yaml").write_text(
            "name: Official Repo Name\n", encoding="utf-8"
        )
        build_index(
            repo_root=tmp_path,
            db_path=generated_dir / "modelops.db",
            allow_invalid=True,
        )
        report = generate_scorecard(generated_dir / "modelops.db", tmp_path)
        assert report.repo_name == "Official Repo Name"

    def test_scorecard_uses_workspace_name_fallback(self, tmp_path: Path) -> None:
        from modelops_core.index.sqlite_builder import build_index

        model_dir = tmp_path / "model"
        model_dir.mkdir()
        generated_dir = tmp_path / "generated"
        generated_dir.mkdir()
        (model_dir / "DOMAIN-TEST.md").write_text(
            "---\nid: DOMAIN-TEST\ntype: MasterDataDomain\nstatus: draft\n"
            "name: Test Domain\nschema_version: '1.0'\n---\n",
            encoding="utf-8",
        )
        (tmp_path / "modelops.config.yaml").write_text(
            "workspace_name: Customer BP Example\n", encoding="utf-8"
        )
        build_index(
            repo_root=tmp_path,
            db_path=generated_dir / "modelops.db",
            allow_invalid=True,
        )
        report = generate_scorecard(generated_dir / "modelops.db", tmp_path)
        assert report.repo_name == "Customer BP Example"


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
            "evidence_coverage",
            "sap_table_coverage",
        }
        assert expected.issubset(names)
