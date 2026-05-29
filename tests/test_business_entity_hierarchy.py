"""Tests for BusinessObject / Perspective hierarchy support."""

from __future__ import annotations

from modelops_core.repository.parser import ParsedObject
from modelops_core.schemas.registry import get_reference_fields
from modelops_core.validation import validate_objects


def test_parent_entity_reference_field_registered() -> None:
    refs = get_reference_fields("BusinessEntity")
    assert "parent_entity" in refs
    assert refs["parent_entity"].expected_target_type == "BusinessEntity"


def test_valid_parent_entity_hierarchy() -> None:
    domain = ParsedObject(
        source_path="domain.md",
        content_hash="abc",
        frontmatter={
            "id": "DOMAIN-TEST",
            "type": "MasterDataDomain",
            "status": "active",
        },
        body=None,
        parser_error=None,
    )
    parent = ParsedObject(
        source_path="parent.md",
        content_hash="abc",
        frontmatter={
            "id": "ENTITY-PARENT",
            "type": "BusinessEntity",
            "status": "active",
            "domain": "DOMAIN-TEST",
        },
        body=None,
        parser_error=None,
    )
    child = ParsedObject(
        source_path="child.md",
        content_hash="abc",
        frontmatter={
            "id": "ENTITY-CHILD",
            "type": "BusinessEntity",
            "status": "active",
            "domain": "DOMAIN-TEST",
            "parent_entity": "ENTITY-PARENT",
        },
        body=None,
        parser_error=None,
    )
    summary = validate_objects([domain, parent, child])
    assert summary.is_valid


def test_broken_parent_entity_reference() -> None:
    domain = ParsedObject(
        source_path="domain.md",
        content_hash="abc",
        frontmatter={
            "id": "DOMAIN-TEST",
            "type": "MasterDataDomain",
            "status": "active",
        },
        body=None,
        parser_error=None,
    )
    child = ParsedObject(
        source_path="child.md",
        content_hash="abc",
        frontmatter={
            "id": "ENTITY-CHILD",
            "type": "BusinessEntity",
            "status": "active",
            "domain": "DOMAIN-TEST",
            "parent_entity": "ENTITY-MISSING",
        },
        body=None,
        parser_error=None,
    )
    summary = validate_objects([domain, child])
    assert not summary.is_valid
    assert any(
        r.code == "REFERENCE_BROKEN" and r.object_id == "ENTITY-CHILD" for r in summary.results
    )


def test_parent_entity_type_mismatch() -> None:
    domain = ParsedObject(
        source_path="domain.md",
        content_hash="abc",
        frontmatter={
            "id": "DOMAIN-TEST",
            "type": "MasterDataDomain",
            "status": "active",
        },
        body=None,
        parser_error=None,
    )
    attr = ParsedObject(
        source_path="attr.md",
        content_hash="abc",
        frontmatter={
            "id": "ATTR-TEST",
            "type": "Attribute",
            "status": "active",
            "domain": "DOMAIN-TEST",
        },
        body=None,
        parser_error=None,
    )
    child = ParsedObject(
        source_path="child.md",
        content_hash="abc",
        frontmatter={
            "id": "ENTITY-CHILD",
            "type": "BusinessEntity",
            "status": "active",
            "domain": "DOMAIN-TEST",
            "parent_entity": "ATTR-TEST",
        },
        body=None,
        parser_error=None,
    )
    summary = validate_objects([domain, attr, child])
    assert not summary.is_valid
    assert any(
        r.code == "REFERENCE_TYPE_MISMATCH" and r.object_id == "ENTITY-CHILD"
        for r in summary.results
    )
