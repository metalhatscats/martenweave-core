"""Tests for canonical object fixture factories."""

from __future__ import annotations

from modelops_core.repository.parser import ParsedObject
from modelops_core.validation import validate_objects


def _make_obj(source_path: str, frontmatter: dict) -> ParsedObject:
    return ParsedObject(
        source_path=source_path,
        content_hash="abc",
        frontmatter=frontmatter,
        body="",
        parser_error=None,
    )


def test_domain_factory_is_valid(domain_factory) -> None:
    obj = _make_obj("DOMAIN-FACTORY.md", domain_factory())
    summary = validate_objects([obj])
    assert summary.is_valid


def test_attribute_factory_with_domain_is_valid(domain_factory, attribute_factory) -> None:
    objects = [
        _make_obj("DOMAIN-FACTORY.md", domain_factory()),
        _make_obj("ATTR-FACTORY.md", attribute_factory()),
    ]
    summary = validate_objects(objects)
    assert summary.is_valid


def test_entity_context_factory_is_valid(domain_factory, entity_context_factory) -> None:
    objects = [
        _make_obj("DOMAIN-FACTORY.md", domain_factory()),
        _make_obj("ENTITY-CONTEXT-FACTORY.md", entity_context_factory()),
    ]
    summary = validate_objects(objects)
    assert summary.is_valid


def test_field_endpoint_factory_is_valid(
    domain_factory, attribute_factory, field_endpoint_factory
) -> None:
    objects = [
        _make_obj("DOMAIN-FACTORY.md", domain_factory()),
        _make_obj("ATTR-FACTORY.md", attribute_factory()),
        _make_obj("FEP-FACTORY.md", field_endpoint_factory()),
    ]
    summary = validate_objects(objects)
    assert summary.is_valid


def test_mapping_factory_is_valid(
    domain_factory,
    attribute_factory,
    field_endpoint_factory,
    mapping_factory,
) -> None:
    objects = [
        _make_obj("DOMAIN-FACTORY.md", domain_factory()),
        _make_obj("ATTR-FACTORY.md", attribute_factory()),
        _make_obj("FEP-SOURCE-FACTORY.md", field_endpoint_factory(id="FEP-SOURCE-FACTORY")),
        _make_obj("FEP-TARGET-FACTORY.md", field_endpoint_factory(id="FEP-TARGET-FACTORY")),
        _make_obj("MAP-FACTORY.md", mapping_factory()),
    ]
    summary = validate_objects(objects)
    assert summary.is_valid


def test_patch_proposal_factory_is_valid(patch_proposal_factory) -> None:
    obj = _make_obj("PP-FACTORY.md", patch_proposal_factory())
    summary = validate_objects([obj])
    assert summary.is_valid


def test_factories_accept_overrides(domain_factory, attribute_factory) -> None:
    domain = domain_factory(id="DOMAIN-OVERRIDE", name="Override Domain")
    attr = attribute_factory(
        id="ATTR-OVERRIDE",
        name="Override Attribute",
        domain="DOMAIN-OVERRIDE",
    )
    objects = [
        _make_obj("DOMAIN-OVERRIDE.md", domain),
        _make_obj("ATTR-OVERRIDE.md", attr),
    ]
    summary = validate_objects(objects)
    assert summary.is_valid
    assert not any(
        r.object_id == "DOMAIN-OVERRIDE" and r.severity.name == "ERROR" for r in summary.results
    )
