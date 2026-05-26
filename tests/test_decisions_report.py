"""Tests for Decision evidence validation hardening and decisions report (#236)."""

from __future__ import annotations

from pathlib import Path

from modelops_core.index.sqlite_builder import build_index
from modelops_core.reports.decisions_report import (
    DecisionsReport,
    generate_decisions_report,
)
from modelops_core.repository import parse_file
from modelops_core.validation.pipeline import validate_objects
from modelops_core.validation.result import ValidationSeverity


class TestValidateCheckDecisions:
    def test_check_decisions_warns_on_deprecated_evidence(self, tmp_path: Path) -> None:
        model_dir = tmp_path / "model"
        model_dir.mkdir()
        (model_dir / "DEC-001.md").write_text(
            "---\nid: DEC-001\ntype: Decision\nstatus: active\n"
            "name: Test Decision\nevidence: EVIDENCE-001\n"
            "schema_version: '1.0'\n---\n",
            encoding="utf-8",
        )
        (model_dir / "EVIDENCE-001.md").write_text(
            "---\nid: EVIDENCE-001\ntype: Evidence\nstatus: retired\n"
            "name: Old Evidence\nschema_version: '1.0'\n---\n",
            encoding="utf-8",
        )
        parsed = [parse_file(f) for f in model_dir.glob("*.md")]
        summary = validate_objects(parsed, check_decisions=True)
        deprecated = [r for r in summary.results if r.code == "DECISION_DEPRECATED_EVIDENCE"]
        assert len(deprecated) == 1
        assert deprecated[0].severity == ValidationSeverity.WARNING
        assert "EVIDENCE-001" in deprecated[0].message
        assert "retired" in deprecated[0].message

    def test_check_decisions_no_warning_for_active_evidence(self, tmp_path: Path) -> None:
        model_dir = tmp_path / "model"
        model_dir.mkdir()
        (model_dir / "DEC-001.md").write_text(
            "---\nid: DEC-001\ntype: Decision\nstatus: active\n"
            "name: Test Decision\nevidence: EVIDENCE-001\n"
            "schema_version: '1.0'\n---\n",
            encoding="utf-8",
        )
        (model_dir / "EVIDENCE-001.md").write_text(
            "---\nid: EVIDENCE-001\ntype: Evidence\nstatus: active\n"
            "name: Good Evidence\nschema_version: '1.0'\n---\n",
            encoding="utf-8",
        )
        parsed = [parse_file(f) for f in model_dir.glob("*.md")]
        summary = validate_objects(parsed, check_decisions=True)
        deprecated = [r for r in summary.results if r.code == "DECISION_DEPRECATED_EVIDENCE"]
        assert deprecated == []

    def test_check_decisions_false_skips_advanced(self, tmp_path: Path) -> None:
        model_dir = tmp_path / "model"
        model_dir.mkdir()
        (model_dir / "DEC-001.md").write_text(
            "---\nid: DEC-001\ntype: Decision\nstatus: active\n"
            "name: Test Decision\nevidence: EVIDENCE-001\n"
            "schema_version: '1.0'\n---\n",
            encoding="utf-8",
        )
        (model_dir / "EVIDENCE-001.md").write_text(
            "---\nid: EVIDENCE-001\ntype: Evidence\nstatus: retired\n"
            "name: Old Evidence\nschema_version: '1.0'\n---\n",
            encoding="utf-8",
        )
        parsed = [parse_file(f) for f in model_dir.glob("*.md")]
        summary = validate_objects(parsed, check_decisions=False)
        deprecated = [r for r in summary.results if r.code == "DECISION_DEPRECATED_EVIDENCE"]
        assert deprecated == []

    def test_check_decisions_no_evidence_no_error(self, tmp_path: Path) -> None:
        model_dir = tmp_path / "model"
        model_dir.mkdir()
        (model_dir / "DEC-001.md").write_text(
            "---\nid: DEC-001\ntype: Decision\nstatus: active\n"
            "name: Test Decision\nschema_version: '1.0'\n---\n",
            encoding="utf-8",
        )
        parsed = [parse_file(f) for f in model_dir.glob("*.md")]
        summary = validate_objects(parsed, check_decisions=True)
        deprecated = [r for r in summary.results if r.code == "DECISION_DEPRECATED_EVIDENCE"]
        assert deprecated == []


class TestDecisionsReport:
    def test_report_on_example_repo(self, sample_repo: Path) -> None:
        repo_root = sample_repo
        db_path = repo_root / "generated" / "modelops.db"
        report = generate_decisions_report(db_path, repo_root)
        assert isinstance(report, DecisionsReport)
        assert report.total_decisions >= 0

    def test_report_json_serializable(self, sample_repo: Path) -> None:
        import json

        repo_root = sample_repo
        db_path = repo_root / "generated" / "modelops.db"
        report = generate_decisions_report(db_path, repo_root)
        data = {
            "evidence_coverage": [
                {
                    "domain": d.domain,
                    "total_decisions": d.total_decisions,
                    "decisions_with_evidence": d.decisions_with_evidence,
                    "coverage_percent": d.coverage_percent,
                }
                for d in report.evidence_coverage
            ],
            "uncovered_decisions": [
                {
                    "object_id": d.object_id,
                    "object_name": d.object_name,
                    "status": d.status,
                    "domain": d.domain,
                }
                for d in report.uncovered_decisions
            ],
            "deprecated_evidence_decisions": [
                {
                    "object_id": d.object_id,
                    "object_name": d.object_name,
                    "status": d.status,
                    "domain": d.domain,
                }
                for d in report.deprecated_evidence_decisions
            ],
            "category_breakdown": [
                {"category": c.category, "count": c.count}
                for c in report.category_breakdown
            ],
            "total_decisions": report.total_decisions,
            "total_with_evidence": report.total_with_evidence,
            "overall_coverage_percent": report.overall_coverage_percent,
        }
        text = json.dumps(data, indent=2, default=str)
        assert "total_decisions" in text

    def test_empty_repo(self, tmp_path: Path) -> None:
        model_dir = tmp_path / "model"
        model_dir.mkdir()
        generated_dir = tmp_path / "generated"
        generated_dir.mkdir()
        (tmp_path / "modelops.config.yaml").write_text(
            "model_dir: model\ngenerated_dir: generated\n", encoding="utf-8"
        )
        build_index(
            repo_root=tmp_path,
            db_path=generated_dir / "modelops.db",
            allow_invalid=True,
        )
        report = generate_decisions_report(generated_dir / "modelops.db", tmp_path)
        assert report.evidence_coverage == []
        assert report.uncovered_decisions == []
        assert report.deprecated_evidence_decisions == []
        assert report.category_breakdown == []
        assert report.total_decisions == 0
        assert report.total_with_evidence == 0
        assert report.overall_coverage_percent == 0.0

    def test_evidence_coverage_per_domain(self, tmp_path: Path) -> None:
        model_dir = tmp_path / "model"
        model_dir.mkdir()
        generated_dir = tmp_path / "generated"
        generated_dir.mkdir()
        (model_dir / "DEC-001.md").write_text(
            "---\nid: DEC-001\ntype: Decision\nstatus: active\n"
            "name: D1\nevidence: EVIDENCE-001\ndomain: DOMAIN-A\n"
            "schema_version: '1.0'\n---\n",
            encoding="utf-8",
        )
        (model_dir / "DEC-002.md").write_text(
            "---\nid: DEC-002\ntype: Decision\nstatus: active\n"
            "name: D2\ndomain: DOMAIN-A\nschema_version: '1.0'\n---\n",
            encoding="utf-8",
        )
        (model_dir / "DEC-003.md").write_text(
            "---\nid: DEC-003\ntype: Decision\nstatus: active\n"
            "name: D3\nevidence: EVIDENCE-002\ndomain: DOMAIN-B\n"
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
        report = generate_decisions_report(generated_dir / "modelops.db", tmp_path)
        assert report.total_decisions == 3
        assert report.total_with_evidence == 2
        assert report.overall_coverage_percent == 66.7

        domain_a = next(d for d in report.evidence_coverage if d.domain == "DOMAIN-A")
        assert domain_a.total_decisions == 2
        assert domain_a.decisions_with_evidence == 1
        assert domain_a.coverage_percent == 50.0

        domain_b = next(d for d in report.evidence_coverage if d.domain == "DOMAIN-B")
        assert domain_b.total_decisions == 1
        assert domain_b.decisions_with_evidence == 1
        assert domain_b.coverage_percent == 100.0

    def test_uncovered_decisions_listed(self, tmp_path: Path) -> None:
        model_dir = tmp_path / "model"
        model_dir.mkdir()
        generated_dir = tmp_path / "generated"
        generated_dir.mkdir()
        (model_dir / "DEC-001.md").write_text(
            "---\nid: DEC-001\ntype: Decision\nstatus: active\n"
            "name: D1\nevidence: EVIDENCE-001\nschema_version: '1.0'\n---\n",
            encoding="utf-8",
        )
        (model_dir / "DEC-002.md").write_text(
            "---\nid: DEC-002\ntype: Decision\nstatus: active\n"
            "name: D2\nschema_version: '1.0'\n---\n",
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
        report = generate_decisions_report(generated_dir / "modelops.db", tmp_path)
        assert len(report.uncovered_decisions) == 1
        assert report.uncovered_decisions[0].object_id == "DEC-002"

    def test_deprecated_evidence_decisions_listed(self, tmp_path: Path) -> None:
        model_dir = tmp_path / "model"
        model_dir.mkdir()
        generated_dir = tmp_path / "generated"
        generated_dir.mkdir()
        (model_dir / "DEC-001.md").write_text(
            "---\nid: DEC-001\ntype: Decision\nstatus: active\n"
            "name: D1\nevidence: EVIDENCE-001\nschema_version: '1.0'\n---\n",
            encoding="utf-8",
        )
        (model_dir / "EVIDENCE-001.md").write_text(
            "---\nid: EVIDENCE-001\ntype: Evidence\nstatus: retired\n"
            "name: Old Evidence\nschema_version: '1.0'\n---\n",
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
        report = generate_decisions_report(generated_dir / "modelops.db", tmp_path)
        assert len(report.deprecated_evidence_decisions) == 1
        assert report.deprecated_evidence_decisions[0].object_id == "DEC-001"

    def test_category_breakdown(self, tmp_path: Path) -> None:
        model_dir = tmp_path / "model"
        model_dir.mkdir()
        generated_dir = tmp_path / "generated"
        generated_dir.mkdir()
        (model_dir / "DEC-001.md").write_text(
            "---\nid: DEC-001\ntype: Decision\nstatus: active\n"
            "name: D1\ndecision_category: architecture\n"
            "schema_version: '1.0'\n---\n",
            encoding="utf-8",
        )
        (model_dir / "DEC-002.md").write_text(
            "---\nid: DEC-002\ntype: Decision\nstatus: active\n"
            "name: D2\ndecision_category: architecture\n"
            "schema_version: '1.0'\n---\n",
            encoding="utf-8",
        )
        (model_dir / "DEC-003.md").write_text(
            "---\nid: DEC-003\ntype: Decision\nstatus: active\n"
            "name: D3\ndecision_category: data_model\n"
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
        report = generate_decisions_report(generated_dir / "modelops.db", tmp_path)
        breakdown = {c.category: c.count for c in report.category_breakdown}
        assert breakdown.get("architecture") == 2
        assert breakdown.get("data_model") == 1

    def test_category_fallback_to_category_field(self, tmp_path: Path) -> None:
        model_dir = tmp_path / "model"
        model_dir.mkdir()
        generated_dir = tmp_path / "generated"
        generated_dir.mkdir()
        (model_dir / "DEC-001.md").write_text(
            "---\nid: DEC-001\ntype: Decision\nstatus: active\n"
            "name: D1\ncategory: governance\nschema_version: '1.0'\n---\n",
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
        report = generate_decisions_report(generated_dir / "modelops.db", tmp_path)
        assert len(report.category_breakdown) == 1
        assert report.category_breakdown[0].category == "governance"
        assert report.category_breakdown[0].count == 1
