"""Tests for impact analysis."""

from __future__ import annotations

from pathlib import Path

from modelops_core.impact.impact_service import generate_impact_report
from modelops_core.index import build_index


def test_impact_report_found_object(temp_model_dir: Path) -> None:
    repo_root = temp_model_dir.parent
    db_path = repo_root / "generated" / "modelops.db"
    build_index(repo_root=repo_root, db_path=db_path)

    report = generate_impact_report(db_path, "DOMAIN-TEST", max_depth=2)
    assert report.root_object_id == "DOMAIN-TEST"
    # ATTR-TEST references DOMAIN-TEST, so it should appear downstream
    assert any(o.object_id == "ATTR-TEST" for o in report.affected_objects)


def test_impact_report_missing_object(temp_model_dir: Path) -> None:
    repo_root = temp_model_dir.parent
    db_path = repo_root / "generated" / "modelops.db"
    build_index(repo_root=repo_root, db_path=db_path)

    report = generate_impact_report(db_path, "MISSING-ID", max_depth=2)
    assert report.root_object_type is None
    assert report.affected_objects == []
