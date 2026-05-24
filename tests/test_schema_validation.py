"""Tests for schema validation pipeline."""

from __future__ import annotations

from pathlib import Path

from modelops_core.repository import parse_file
from modelops_core.validation import validate_objects
from modelops_core.validation.result import ValidationSeverity


def test_valid_object_passes(tmp_path: Path) -> None:
    path = tmp_path / "valid.md"
    path.write_text(
        "---\nid: ATTR-VALID\ntype: Attribute\nstatus: draft\nname: Valid\n---\n",
        encoding="utf-8",
    )
    obj = parse_file(path)
    summary = validate_objects([obj])
    assert summary.is_valid
    assert summary.error_count == 0


def test_missing_id() -> None:
    from modelops_core.repository.parser import ParsedObject

    obj = ParsedObject(
        source_path="test.md",
        content_hash="abc",
        frontmatter={"type": "Attribute", "status": "draft"},
        body=None,
        parser_error=None,
    )
    summary = validate_objects([obj])
    assert not summary.is_valid
    assert any(r.code == "ID_MISSING" for r in summary.results)


def test_invalid_id_format() -> None:
    from modelops_core.repository.parser import ParsedObject

    obj = ParsedObject(
        source_path="test.md",
        content_hash="abc",
        frontmatter={"id": "invalid-id-lower", "type": "Attribute", "status": "draft"},
        body=None,
        parser_error=None,
    )
    summary = validate_objects([obj])
    assert not summary.is_valid
    assert any(r.code == "ID_INVALID_FORMAT" for r in summary.results)


def test_unknown_type() -> None:
    from modelops_core.repository.parser import ParsedObject

    obj = ParsedObject(
        source_path="test.md",
        content_hash="abc",
        frontmatter={"id": "TEST-001", "type": "UnknownType", "status": "draft"},
        body=None,
        parser_error=None,
    )
    summary = validate_objects([obj])
    assert not summary.is_valid
    assert any(r.code == "TYPE_UNKNOWN" for r in summary.results)


def test_missing_status() -> None:
    from modelops_core.repository.parser import ParsedObject

    obj = ParsedObject(
        source_path="test.md",
        content_hash="abc",
        frontmatter={"id": "TEST-001", "type": "Attribute"},
        body=None,
        parser_error=None,
    )
    summary = validate_objects([obj])
    assert not summary.is_valid
    assert any(r.code == "STATUS_MISSING" for r in summary.results)


def test_display_name_missing_warning() -> None:
    from modelops_core.repository.parser import ParsedObject

    obj = ParsedObject(
        source_path="test.md",
        content_hash="abc",
        frontmatter={"id": "TEST-001", "type": "Attribute", "status": "draft"},
        body=None,
        parser_error=None,
    )
    summary = validate_objects([obj])
    assert any(
        r.code == "DISPLAY_NAME_MISSING" and r.severity == ValidationSeverity.WARNING
        for r in summary.results
    )
