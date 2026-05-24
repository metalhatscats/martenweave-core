"""Tests for ownership validation and health report."""

from __future__ import annotations

from pathlib import Path

from modelops_core.index import build_index
from modelops_core.repository import ParsedObject
from modelops_core.reports.health_report import generate_repository_health
from modelops_core.validation import validate_objects


def test_ownership_warning_for_missing_owner() -> None:
    obj = ParsedObject(
        source_path="ATTR.md",
        content_hash="x",
        frontmatter={
            "id": "ATTR-TEST",
            "type": "Attribute",
            "status": "active",
            "name": "Test Attribute",
        },
        body=None,
        parser_error=None,
    )
    summary = validate_objects([obj])
    assert any(r.code == "OWNERSHIP_MISSING" for r in summary.results)
    assert all(r.severity == "WARNING" for r in summary.results if r.code == "OWNERSHIP_MISSING")


def test_ownership_no_warning_when_owner_present() -> None:
    obj = ParsedObject(
        source_path="ATTR.md",
        content_hash="x",
        frontmatter={
            "id": "ATTR-TEST",
            "type": "Attribute",
            "status": "active",
            "name": "Test Attribute",
            "business_owner": "PERSON-001",
        },
        body=None,
        parser_error=None,
    )
    summary = validate_objects([obj])
    assert not any(r.code == "OWNERSHIP_MISSING" for r in summary.results)


def test_ownership_no_warning_for_inactive() -> None:
    obj = ParsedObject(
        source_path="ATTR.md",
        content_hash="x",
        frontmatter={
            "id": "ATTR-TEST",
            "type": "Attribute",
            "status": "archived",
            "name": "Test Attribute",
        },
        body=None,
        parser_error=None,
    )
    summary = validate_objects([obj])
    assert not any(r.code == "OWNERSHIP_MISSING" for r in summary.results)


def test_health_report_ownership_coverage(sample_repo: Path) -> None:
    build_index(sample_repo)
    db_path = sample_repo / "generated" / "modelops.db"
    report = generate_repository_health(db_path)
    assert report.ownership_coverage is not None
    assert report.ownership_coverage.total_eligible > 0
    # At least the attribute with data_steward should count
    assert report.ownership_coverage.with_owner > 0
