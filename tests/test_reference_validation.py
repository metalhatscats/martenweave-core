"""Tests for reference validation."""

from __future__ import annotations

from modelops_core.repository.parser import ParsedObject
from modelops_core.validation import validate_objects


def test_broken_reference() -> None:
    source = ParsedObject(
        source_path="source.md",
        content_hash="abc",
        frontmatter={
            "id": "ATTR-TEST",
            "type": "Attribute",
            "status": "draft",
            "domain": "DOMAIN-MISSING",
        },
        body=None,
        parser_error=None,
    )
    summary = validate_objects([source])
    assert not summary.is_valid
    assert any(r.code == "REFERENCE_BROKEN" for r in summary.results)


def test_reference_type_mismatch() -> None:
    domain = ParsedObject(
        source_path="domain.md",
        content_hash="abc",
        frontmatter={"id": "DOMAIN-TEST", "type": "MasterDataDomain", "status": "draft"},
        body=None,
        parser_error=None,
    )
    attr = ParsedObject(
        source_path="attr.md",
        content_hash="abc",
        frontmatter={
            "id": "ATTR-TEST",
            "type": "Attribute",
            "status": "draft",
            "domain": "ATTR-TEST-WRONG",  # Will be broken, but let's test type mismatch
        },
        body=None,
        parser_error=None,
    )
    # Actually domain points to Attribute which expects MasterDataDomain
    attr2 = ParsedObject(
        source_path="attr2.md",
        content_hash="abc",
        frontmatter={
            "id": "ATTR-TEST2",
            "type": "Attribute",
            "status": "draft",
            "domain": "ATTR-TEST",  # ATTR-TEST is Attribute, not MasterDataDomain
        },
        body=None,
        parser_error=None,
    )
    summary = validate_objects([domain, attr, attr2])
    assert not summary.is_valid
    assert any(r.code == "REFERENCE_TYPE_MISMATCH" for r in summary.results)


def test_duplicate_ids() -> None:
    a = ParsedObject(
        source_path="a.md",
        content_hash="abc",
        frontmatter={"id": "DUP-001", "type": "Attribute", "status": "draft"},
        body=None,
        parser_error=None,
    )
    b = ParsedObject(
        source_path="b.md",
        content_hash="def",
        frontmatter={"id": "DUP-001", "type": "Attribute", "status": "draft"},
        body=None,
        parser_error=None,
    )
    summary = validate_objects([a, b])
    assert not summary.is_valid
    assert any(r.code == "ID_DUPLICATE" for r in summary.results)


# Circular reference tests ----------------------------------------------------


def test_simple_cycle() -> None:
    a = ParsedObject(
        source_path="a.md",
        content_hash="abc",
        frontmatter={
            "id": "A",
            "type": "Attribute",
            "status": "draft",
            "domain": "B",
        },
        body=None,
        parser_error=None,
    )
    b = ParsedObject(
        source_path="b.md",
        content_hash="def",
        frontmatter={
            "id": "B",
            "type": "MasterDataDomain",
            "status": "draft",
            "related_objects": ["A"],
        },
        body=None,
        parser_error=None,
    )
    summary = validate_objects([a, b])
    assert any(r.code == "REFERENCE_CIRCULAR" for r in summary.results)
    cycle_result = next(r for r in summary.results if r.code == "REFERENCE_CIRCULAR")
    assert "A" in cycle_result.related_objects
    assert "B" in cycle_result.related_objects


def test_self_reference() -> None:
    a = ParsedObject(
        source_path="a.md",
        content_hash="abc",
        frontmatter={
            "id": "A",
            "type": "Attribute",
            "status": "draft",
            "domain": "A",
        },
        body=None,
        parser_error=None,
    )
    summary = validate_objects([a])
    assert any(r.code == "REFERENCE_CIRCULAR" for r in summary.results)
    cycle_result = next(r for r in summary.results if r.code == "REFERENCE_CIRCULAR")
    assert cycle_result.related_objects == ["A"]


def test_no_false_positive_on_dag() -> None:
    a = ParsedObject(
        source_path="a.md",
        content_hash="abc",
        frontmatter={
            "id": "A",
            "type": "Attribute",
            "status": "draft",
            "domain": "B",
        },
        body=None,
        parser_error=None,
    )
    b = ParsedObject(
        source_path="b.md",
        content_hash="def",
        frontmatter={
            "id": "B",
            "type": "MasterDataDomain",
            "status": "draft",
        },
        body=None,
        parser_error=None,
    )
    summary = validate_objects([a, b])
    assert not any(r.code == "REFERENCE_CIRCULAR" for r in summary.results)


def test_nested_cycle() -> None:
    a = ParsedObject(
        source_path="a.md",
        content_hash="abc",
        frontmatter={
            "id": "A",
            "type": "Attribute",
            "status": "draft",
            "domain": "B",
        },
        body=None,
        parser_error=None,
    )
    b = ParsedObject(
        source_path="b.md",
        content_hash="def",
        frontmatter={
            "id": "B",
            "type": "MasterDataDomain",
            "status": "draft",
            "related_objects": ["C"],
        },
        body=None,
        parser_error=None,
    )
    c = ParsedObject(
        source_path="c.md",
        content_hash="ghi",
        frontmatter={
            "id": "C",
            "type": "BusinessEntity",
            "status": "draft",
            "domain": "A",
        },
        body=None,
        parser_error=None,
    )
    summary = validate_objects([a, b, c])
    assert any(r.code == "REFERENCE_CIRCULAR" for r in summary.results)
    cycle_result = next(r for r in summary.results if r.code == "REFERENCE_CIRCULAR")
    assert set(cycle_result.related_objects) == {"A", "B", "C"}
