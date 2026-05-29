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
    assert any(
        r.code == "TIMESTAMP_MISSING" and r.severity == ValidationSeverity.WARNING
        for r in summary.results
    )


def test_timestamp_missing_warning() -> None:
    from modelops_core.repository.parser import ParsedObject

    obj = ParsedObject(
        source_path="test.md",
        content_hash="abc",
        frontmatter={
            "id": "TEST",
            "type": "Attribute",
            "status": "draft",
            "name": "Test",
        },
        body=None,
        parser_error=None,
    )
    summary = validate_objects([obj])
    assert any(
        r.code == "TIMESTAMP_MISSING" and r.severity == ValidationSeverity.WARNING
        for r in summary.results
    )


def test_timestamp_present_no_warning(tmp_path: Path) -> None:
    path = tmp_path / "valid.md"
    path.write_text(
        "---\n"
        "id: ATTR-VALID\n"
        "type: Attribute\n"
        "status: draft\n"
        "name: Valid\n"
        "created_at: 2024-01-15T10:30:00+00:00\n"
        "---\n",
        encoding="utf-8",
    )
    obj = parse_file(path)
    summary = validate_objects([obj])
    assert summary.is_valid
    assert not any(r.code == "TIMESTAMP_MISSING" for r in summary.results)


# Tag validation tests --------------------------------------------------------


def test_valid_tags_pass() -> None:
    from modelops_core.repository.parser import ParsedObject

    obj = ParsedObject(
        source_path="test.md",
        content_hash="abc",
        frontmatter={
            "id": "TEST",
            "type": "Attribute",
            "status": "draft",
            "name": "Test",
            "tags": ["customer", "sales"],
        },
        body=None,
        parser_error=None,
    )
    summary = validate_objects([obj])
    assert summary.is_valid
    assert not any(r.code.startswith("TAG") for r in summary.results)


def test_tag_with_spaces_warning() -> None:
    from modelops_core.repository.parser import ParsedObject

    obj = ParsedObject(
        source_path="test.md",
        content_hash="abc",
        frontmatter={
            "id": "TEST",
            "type": "Attribute",
            "status": "draft",
            "name": "Test",
            "tags": ["customer group"],
        },
        body=None,
        parser_error=None,
    )
    summary = validate_objects([obj])
    assert any(r.code == "TAG_INVALID_FORMAT" for r in summary.results)


def test_tag_uppercase_warning() -> None:
    from modelops_core.repository.parser import ParsedObject

    obj = ParsedObject(
        source_path="test.md",
        content_hash="abc",
        frontmatter={
            "id": "TEST",
            "type": "Attribute",
            "status": "draft",
            "name": "Test",
            "tags": ["Customer"],
        },
        body=None,
        parser_error=None,
    )
    summary = validate_objects([obj])
    assert any(r.code == "TAG_INVALID_FORMAT" for r in summary.results)


def test_tag_too_long_warning() -> None:
    from modelops_core.repository.parser import ParsedObject

    obj = ParsedObject(
        source_path="test.md",
        content_hash="abc",
        frontmatter={
            "id": "TEST",
            "type": "Attribute",
            "status": "draft",
            "name": "Test",
            "tags": ["a" * 33],
        },
        body=None,
        parser_error=None,
    )
    summary = validate_objects([obj])
    assert any(r.code == "TAG_INVALID_FORMAT" for r in summary.results)


def test_tags_too_many_warning() -> None:
    from modelops_core.repository.parser import ParsedObject

    obj = ParsedObject(
        source_path="test.md",
        content_hash="abc",
        frontmatter={
            "id": "TEST",
            "type": "Attribute",
            "status": "draft",
            "name": "Test",
            "tags": [f"tag{i}" for i in range(11)],
        },
        body=None,
        parser_error=None,
    )
    summary = validate_objects([obj])
    assert any(r.code == "TAGS_TOO_MANY" for r in summary.results)


def test_tags_invalid_type_warning() -> None:
    from modelops_core.repository.parser import ParsedObject

    obj = ParsedObject(
        source_path="test.md",
        content_hash="abc",
        frontmatter={
            "id": "TEST",
            "type": "Attribute",
            "status": "draft",
            "name": "Test",
            "tags": "customer",
        },
        body=None,
        parser_error=None,
    )
    summary = validate_objects([obj])
    assert any(r.code == "TAGS_INVALID_TYPE" for r in summary.results)


# Lifecycle validation tests --------------------------------------------------


def test_deprecated_object_incomplete() -> None:
    from modelops_core.repository.parser import ParsedObject

    obj = ParsedObject(
        source_path="test.md",
        content_hash="abc",
        frontmatter={
            "id": "ATTR-DEP",
            "type": "Attribute",
            "status": "deprecated",
            "name": "Deprecated Attr",
        },
        body=None,
        parser_error=None,
    )
    summary = validate_objects([obj])
    assert any(
        r.code == "DEPRECATED_OBJECT_INCOMPLETE" and r.severity == ValidationSeverity.ERROR
        for r in summary.results
    )


def test_deprecated_object_complete() -> None:
    from modelops_core.repository.parser import ParsedObject

    obj = ParsedObject(
        source_path="test.md",
        content_hash="abc",
        frontmatter={
            "id": "ATTR-DEP",
            "type": "Attribute",
            "status": "deprecated",
            "name": "Deprecated Attr",
            "deprecated_reason": "Replaced by ATTR-NEW",
        },
        body=None,
        parser_error=None,
    )
    summary = validate_objects([obj])
    assert not any(r.code == "DEPRECATED_OBJECT_INCOMPLETE" for r in summary.results)


def test_retired_object_referenced() -> None:
    from modelops_core.repository.parser import ParsedObject

    retired = ParsedObject(
        source_path="retired.md",
        content_hash="abc",
        frontmatter={
            "id": "ATTR-OLD",
            "type": "Attribute",
            "status": "retired",
            "name": "Old",
        },
        body=None,
        parser_error=None,
    )
    active = ParsedObject(
        source_path="active.md",
        content_hash="def",
        frontmatter={
            "id": "ATTR-NEW",
            "type": "Attribute",
            "status": "active",
            "name": "New",
            "domain": "ATTR-OLD",
        },
        body=None,
        parser_error=None,
    )
    summary = validate_objects([retired, active])
    assert any(
        r.code == "RETIRED_OBJECT_REFERENCED" and r.severity == ValidationSeverity.ERROR
        for r in summary.results
    )


def test_retired_object_not_referenced_by_draft() -> None:
    from modelops_core.repository.parser import ParsedObject

    retired = ParsedObject(
        source_path="retired.md",
        content_hash="abc",
        frontmatter={
            "id": "ATTR-OLD",
            "type": "Attribute",
            "status": "retired",
            "name": "Old",
        },
        body=None,
        parser_error=None,
    )
    draft = ParsedObject(
        source_path="draft.md",
        content_hash="def",
        frontmatter={
            "id": "ATTR-NEW",
            "type": "Attribute",
            "status": "draft",
            "name": "New",
            "domain": "ATTR-OLD",
        },
        body=None,
        parser_error=None,
    )
    summary = validate_objects([retired, draft])
    assert any(r.code == "RETIRED_OBJECT_REFERENCED" for r in summary.results)


def test_retired_object_reference_ignored_for_inactive_source() -> None:
    from modelops_core.repository.parser import ParsedObject

    retired = ParsedObject(
        source_path="retired.md",
        content_hash="abc",
        frontmatter={
            "id": "ATTR-OLD",
            "type": "Attribute",
            "status": "retired",
            "name": "Old",
        },
        body=None,
        parser_error=None,
    )
    archived = ParsedObject(
        source_path="archived.md",
        content_hash="def",
        frontmatter={
            "id": "ATTR-NEW",
            "type": "Attribute",
            "status": "archived",
            "name": "New",
            "domain": "ATTR-OLD",
        },
        body=None,
        parser_error=None,
    )
    summary = validate_objects([retired, archived])
    assert not any(r.code == "RETIRED_OBJECT_REFERENCED" for r in summary.results)


def test_invalid_status_transition_retired_to_active() -> None:
    from modelops_core.repository.parser import ParsedObject

    obj = ParsedObject(
        source_path="test.md",
        content_hash="abc",
        frontmatter={
            "id": "ATTR-001",
            "type": "Attribute",
            "status": "active",
            "name": "Test",
            "previous_status": "retired",
        },
        body=None,
        parser_error=None,
    )
    summary = validate_objects([obj])
    assert any(
        r.code == "INVALID_STATUS_TRANSITION" and r.severity == ValidationSeverity.WARNING
        for r in summary.results
    )


def test_invalid_status_transition_archived_to_draft() -> None:
    from modelops_core.repository.parser import ParsedObject

    obj = ParsedObject(
        source_path="test.md",
        content_hash="abc",
        frontmatter={
            "id": "ATTR-001",
            "type": "Attribute",
            "status": "draft",
            "name": "Test",
            "previous_status": "archived",
        },
        body=None,
        parser_error=None,
    )
    summary = validate_objects([obj])
    assert any(r.code == "INVALID_STATUS_TRANSITION" for r in summary.results)


def test_valid_status_transition_no_warning() -> None:
    from modelops_core.repository.parser import ParsedObject

    obj = ParsedObject(
        source_path="test.md",
        content_hash="abc",
        frontmatter={
            "id": "ATTR-001",
            "type": "Attribute",
            "status": "active",
            "name": "Test",
            "previous_status": "draft",
        },
        body=None,
        parser_error=None,
    )
    summary = validate_objects([obj])
    assert not any(r.code == "INVALID_STATUS_TRANSITION" for r in summary.results)


def test_no_previous_status_no_transition_warning() -> None:
    from modelops_core.repository.parser import ParsedObject

    obj = ParsedObject(
        source_path="test.md",
        content_hash="abc",
        frontmatter={
            "id": "ATTR-001",
            "type": "Attribute",
            "status": "active",
            "name": "Test",
        },
        body=None,
        parser_error=None,
    )
    summary = validate_objects([obj])
    assert not any(r.code == "INVALID_STATUS_TRANSITION" for r in summary.results)


def test_invalid_status_for_attribute() -> None:
    from modelops_core.repository.parser import ParsedObject

    obj = ParsedObject(
        source_path="test.md",
        content_hash="abc",
        frontmatter={
            "id": "ATTR-001",
            "type": "Attribute",
            "status": "random_gibberish",
            "name": "Test",
        },
        body=None,
        parser_error=None,
    )
    summary = validate_objects([obj])
    assert not summary.is_valid
    assert any(
        r.code == "STATUS_INVALID" and r.severity == ValidationSeverity.ERROR
        for r in summary.results
    )


def test_invalid_status_for_issue() -> None:
    from modelops_core.repository.parser import ParsedObject

    obj = ParsedObject(
        source_path="test.md",
        content_hash="abc",
        frontmatter={
            "id": "ISS-001",
            "type": "Issue",
            "status": "active",
            "name": "Test",
        },
        body=None,
        parser_error=None,
    )
    summary = validate_objects([obj])
    assert not summary.is_valid
    invalid = [r for r in summary.results if r.code == "STATUS_INVALID"]
    assert len(invalid) == 1
    assert "closed" in invalid[0].message
    assert "open" in invalid[0].message


def test_valid_general_status_passes() -> None:
    from modelops_core.repository.parser import ParsedObject

    for status in ("proposed", "draft", "active", "under_review", "deprecated"):
        obj = ParsedObject(
            source_path="test.md",
            content_hash="abc",
            frontmatter={
                "id": "ATTR-001",
                "type": "Attribute",
                "status": status,
                "name": "Test",
            },
            body=None,
            parser_error=None,
        )
        summary = validate_objects([obj])
        assert not any(r.code == "STATUS_INVALID" for r in summary.results)


def test_empty_status_still_triggers_status_missing() -> None:
    from modelops_core.repository.parser import ParsedObject

    obj = ParsedObject(
        source_path="test.md",
        content_hash="abc",
        frontmatter={
            "id": "ATTR-001",
            "type": "Attribute",
            "status": "",
            "name": "Test",
        },
        body=None,
        parser_error=None,
    )
    summary = validate_objects([obj])
    assert any(r.code == "STATUS_MISSING" for r in summary.results)
    assert not any(r.code == "STATUS_INVALID" for r in summary.results)
